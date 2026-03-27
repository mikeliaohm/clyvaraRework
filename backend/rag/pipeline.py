"""End-to-end RAG ingestion pipeline and search.

Core service layer — callable from both CLI and API endpoints.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import select, text as sa_text
from sqlalchemy.orm import Session

from models.rag import IngestionRun, RagChunk, RagDocument, RagNode
from database import Material
from rag.embedder import Embedder
from rag.hierarchy_builder import HeadingDetector, NodeData, build_hierarchy
from rag.chunker import ChunkData, chunk_document
from rag.text_preprocessing import clean_pages, count_tokens
from rag.extraction import extract_pages_from_pdf, extract_text_from_docx


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _log_stage(
    db: Session,
    document_id: str,
    stage: str,
    status: str,
    message: str = "",
) -> IngestionRun:
    run = IngestionRun(
        document_id=document_id,
        stage=stage,
        status=status,
        message=message,
        finished_at=datetime.now(timezone.utc) if status in ("done", "failed") else None,
    )
    db.add(run)
    db.flush()
    return run


def _update_doc_status(db: Session, doc: RagDocument, status: str) -> None:
    doc.status = status
    db.flush()


# ---------------------------------------------------------------------------
# Ingestion
# ---------------------------------------------------------------------------

def ingest_document(
    material_id: int,
    db: Session,
    embedder: Embedder,
    detector: HeadingDetector,
) -> RagDocument:
    """Run the full ingestion pipeline for a material.

    Stages:
      1. Extract   - read file, get per-page text
      2. Preprocess - clean text
      3. Hierarchy  - build node tree, persist rag_nodes
      4. Chunk      - produce chunks, persist rag_chunks (no embeddings yet)
      5. Embed      - batch-embed, update rag_chunks.embedding

    Returns the RagDocument (status = 'ready' on success, 'failed' on error).
    """
    # Load the material row
    material = db.get(Material, material_id)
    if material is None:
        raise ValueError(f"Material {material_id} not found")

    # Read the file
    file_path = material.file_path
    if not file_path or not Path(file_path).exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    file_content = Path(file_path).read_bytes()
    checksum = hashlib.sha256(file_content).hexdigest()

    # Create the RagDocument
    doc = RagDocument(
        material_id=material.id,
        title=material.title,
        source_path=file_path,
        checksum_sha256=checksum,
        status="extracting",
    )
    db.add(doc)
    db.flush()  # get doc.id

    doc_id = str(doc.id)

    try:
        # -- Stage 1: Extract ---------------------------------------
        _log_stage(db, doc_id, "extract", "running")
        _update_doc_status(db, doc, "extracting")

        file_type = (material.file_type or "").lower()
        if file_type == "pdf":
            page_texts = extract_pages_from_pdf(file_content)
        elif file_type in ("docx", "doc"):
            raw = extract_text_from_docx(file_content)
            page_texts = [raw]  # docx has no page concept
        elif file_type == "txt":
            page_texts = [file_content.decode("utf-8")]
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

        doc.page_count = len(page_texts)
        _log_stage(db, doc_id, "extract", "done", f"{len(page_texts)} pages")

        # -- Stage 2: Preprocess ------------------------------------
        _log_stage(db, doc_id, "preprocess", "running")
        _update_doc_status(db, doc, "building_hierarchy")

        cleaned_pages = clean_pages(page_texts)

        _log_stage(db, doc_id, "preprocess", "done")

        # -- Stage 3: Hierarchy -------------------------------------
        _log_stage(db, doc_id, "hierarchy", "running")

        node_datas = build_hierarchy(cleaned_pages, doc_id, detector)

        # Apply cleaned text to each node
        for nd in node_datas:
            nd.cleaned_text = nd.raw_text  # already cleaned by clean_pages

        # Persist nodes
        node_map: dict[str, RagNode] = {}
        for nd in node_datas:
            db_node = RagNode(
                id=nd.id,
                document_id=doc_id,
                parent_id=nd.parent_id,
                node_type=nd.node_type,
                ordinal_label=nd.ordinal_label,
                heading_text=nd.heading_text,
                heading_path=nd.heading_path,
                depth=nd.depth,
                page_start=nd.page_start,
                page_end=nd.page_end,
                raw_text=nd.raw_text,
                cleaned_text=nd.cleaned_text,
                token_count=nd.token_count,
                child_index=nd.child_index,
            )
            db.add(db_node)
            node_map[nd.id] = db_node

        db.flush()
        _log_stage(db, doc_id, "hierarchy", "done", f"{len(node_datas)} nodes")

        # -- Stage 4: Chunk -----------------------------------------
        _log_stage(db, doc_id, "chunk", "running")
        _update_doc_status(db, doc, "chunking")

        chunk_datas = chunk_document(
            node_datas,
            doc_id,
            embedding_model=embedder.model_name,
            title=material.title,
        )

        # Persist chunks (without embeddings or linked-list pointers —
        # those are set in a second pass to avoid FK violations)
        db_chunks: list[RagChunk] = []
        for cd in chunk_datas:
            db_chunk = RagChunk(
                id=cd.id,
                document_id=doc_id,
                node_id=cd.node_id,
                chunk_index=cd.chunk_index,
                chunk_kind=cd.chunk_kind,
                heading_path=cd.heading_path,
                page_start=cd.page_start,
                page_end=cd.page_end,
                token_count=cd.token_count,
                content=cd.content,
                content_for_embedding=cd.content_for_embedding,
                embedding_model=cd.embedding_model,
            )
            db.add(db_chunk)
            db_chunks.append(db_chunk)

        db.flush()

        # Second pass: set prev/next linked-list pointers now that all rows exist
        for cd, db_chunk in zip(chunk_datas, db_chunks):
            if cd.prev_chunk_id:
                db_chunk.prev_chunk_id = cd.prev_chunk_id
            if cd.next_chunk_id:
                db_chunk.next_chunk_id = cd.next_chunk_id
        db.flush()

        _log_stage(db, doc_id, "chunk", "done", f"{len(chunk_datas)} chunks")

        # -- Stage 5: Embed -----------------------------------------
        _log_stage(db, doc_id, "embed", "running")
        _update_doc_status(db, doc, "embedding")

        texts_to_embed = [cd.content_for_embedding for cd in chunk_datas]

        # Batch embed (sentence-transformers handles batching internally)
        BATCH_SIZE = 64
        all_embeddings: list[list[float]] = []
        for i in range(0, len(texts_to_embed), BATCH_SIZE):
            batch = texts_to_embed[i : i + BATCH_SIZE]
            all_embeddings.extend(embedder.embed_texts(batch))

        for db_chunk, embedding in zip(db_chunks, all_embeddings):
            db_chunk.embedding = embedding

        db.flush()
        _log_stage(db, doc_id, "embed", "done", f"{len(all_embeddings)} embeddings")

        # -- Done ---------------------------------------------------
        _update_doc_status(db, doc, "ready")
        db.commit()
        return doc

    except Exception as exc:
        db.rollback()
        # Try to mark as failed (in a fresh transaction)
        try:
            doc.status = "failed"
            _log_stage(db, doc_id, "error", "failed", str(exc))
            db.commit()
        except Exception:
            db.rollback()
        raise


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

def search_chunks(
    query: str,
    user_id: str,
    db: Session,
    embedder: Embedder,
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """Embed *query* and return the top-k most similar chunks.

    Results are scoped to the user's own documents plus system-wide
    documents (materials.user_id = 'SYSTEM').
    """
    query_vec = embedder.embed_query(query)

    sql = sa_text("""
        SELECT
            c.id            AS chunk_id,
            c.content       AS content,
            c.heading_path  AS heading_path,
            c.chunk_kind    AS chunk_kind,
            c.page_start    AS page_start,
            c.page_end      AS page_end,
            c.token_count   AS token_count,
            d.title         AS document_title,
            d.id            AS document_id,
            1 - (c.embedding <=> :query_vec) AS score
        FROM rag_chunks c
        JOIN rag_documents d ON c.document_id = d.id
        JOIN materials m ON d.material_id = m.id
        WHERE m.user_id IN (:user_id, 'SYSTEM')
          AND c.embedding IS NOT NULL
        ORDER BY c.embedding <=> :query_vec
        LIMIT :top_k
    """)

    rows = db.execute(
        sql,
        {"query_vec": str(query_vec), "user_id": user_id, "top_k": top_k},
    ).mappings().all()

    return [dict(row) for row in rows]


# ---------------------------------------------------------------------------
# Chunk context
# ---------------------------------------------------------------------------

def get_chunk_with_context(chunk_id: str, db: Session) -> dict[str, Any] | None:
    """Return a chunk together with its prev/next neighbours and node info."""
    chunk = db.execute(
        select(RagChunk).where(RagChunk.id == chunk_id)
    ).scalar_one_or_none()

    if chunk is None:
        return None

    node = db.execute(
        select(RagNode).where(RagNode.id == chunk.node_id)
    ).scalar_one_or_none()

    prev_chunk = None
    next_chunk = None
    if chunk.prev_chunk_id:
        prev_chunk = db.execute(
            select(RagChunk).where(RagChunk.id == chunk.prev_chunk_id)
        ).scalar_one_or_none()
    if chunk.next_chunk_id:
        next_chunk = db.execute(
            select(RagChunk).where(RagChunk.id == chunk.next_chunk_id)
        ).scalar_one_or_none()

    return {
        "chunk": {
            "id": str(chunk.id),
            "content": chunk.content,
            "heading_path": chunk.heading_path,
            "chunk_kind": chunk.chunk_kind,
            "token_count": chunk.token_count,
            "page_start": chunk.page_start,
            "page_end": chunk.page_end,
            "chunk_index": chunk.chunk_index,
        },
        "node": {
            "id": str(node.id) if node else None,
            "node_type": node.node_type if node else None,
            "heading_text": node.heading_text if node else None,
            "depth": node.depth if node else None,
        },
        "prev_chunk_id": str(chunk.prev_chunk_id) if chunk.prev_chunk_id else None,
        "next_chunk_id": str(chunk.next_chunk_id) if chunk.next_chunk_id else None,
        "prev_content": prev_chunk.content if prev_chunk else None,
        "next_content": next_chunk.content if next_chunk else None,
    }
