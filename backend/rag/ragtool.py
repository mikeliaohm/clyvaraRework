#!/usr/bin/env python
"""CLI for RAG ingestion, search, and inspection.

Usage (from backend/):
    python rag/ragtool.py upload mybook.pdf --title "My Book" --user-id SYSTEM
    python rag/ragtool.py search "anesthesia" --user-id SYSTEM
    python rag/ragtool.py show-chunk <chunk-id>
    python rag/ragtool.py status
    python rag/ragtool.py reprocess <document-id>
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import click

# Ensure the backend directory is on sys.path so imports work when invoked
# as `python rag/ragtool.py` from the backend/ directory.
_backend_dir = str(Path(__file__).resolve().parent.parent)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from dotenv import load_dotenv
load_dotenv()

from database import get_session_local, Material
from rag.embedder import get_embedder
from rag.hierarchy_builder import get_detector
from rag.pipeline import ingest_document, search_chunks, get_chunk_with_context
from models.rag import RagDocument, IngestionRun


@click.group()
def cli():
    """RAG pipeline CLI — upload, search, inspect."""
    pass


# ---------------------------------------------------------------------------
# upload
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("--title", required=True, help="Document title")
@click.option("--user-id", required=True, help='Owner user ID (use "SYSTEM" for shared docs)')
@click.option("--detector", default="general", type=click.Choice(["general", "medical"]),
              help="Heading detection preset")
@click.option("--embed-model", default=None, help="Embedding model name (default from EMBEDDING_MODEL env)")
def upload(file: str, title: str, user_id: str, detector: str, embed_model: str | None):
    """Ingest a file into the RAG pipeline."""
    file_path = str(Path(file).resolve())
    file_type = Path(file).suffix.lstrip(".").lower()

    if file_type not in ("pdf", "docx", "doc", "txt"):
        click.echo(f"Error: unsupported file type '.{file_type}'", err=True)
        raise SystemExit(1)

    file_size = os.path.getsize(file_path)

    Session = get_session_local()
    db = Session()

    try:
        # Create a materials row (the pipeline requires one)
        mat = Material(
            user_id=user_id,
            title=title,
            file_type=file_type,
            file_path=file_path,
            file_size=file_size,
            status="uploaded",
        )
        db.add(mat)
        db.flush()

        click.echo(f"Created material id={mat.id} for user_id={user_id}")

        embedder = get_embedder(embed_model)
        heading_detector = get_detector(detector)

        click.echo(f"Using embedder: {embedder.model_name} (dim={embedder.dimension})")
        click.echo(f"Using detector: {detector}")
        click.echo("Running ingestion pipeline...")

        doc = ingest_document(mat.id, db, embedder, heading_detector)

        click.echo(f"Done! RagDocument id={doc.id}, status={doc.status}")

    except Exception as exc:
        click.echo(f"Error: {exc}", err=True)
        db.rollback()
        raise SystemExit(1)
    finally:
        db.close()


# ---------------------------------------------------------------------------
# search
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("query")
@click.option("--user-id", required=True, help="User ID to scope results")
@click.option("--top-k", default=5, type=int, help="Number of results")
@click.option("--embed-model", default=None, help="Embedding model name")
def search(query: str, user_id: str, top_k: int, embed_model: str | None):
    """Search for chunks matching a query."""
    embedder = get_embedder(embed_model)

    Session = get_session_local()
    db = Session()

    try:
        results = search_chunks(query, user_id, db, embedder, top_k=top_k)

        if not results:
            click.echo("No results found.")
            return

        for i, row in enumerate(results, 1):
            score = row.get("score", 0)
            click.echo(f"\n--- Result {i} (score: {score:.4f}) ---")
            click.echo(f"Document: {row.get('document_title', '?')}")
            click.echo(f"Path:     {row.get('heading_path', '?')}")
            click.echo(f"Pages:    {row.get('page_start', '?')}-{row.get('page_end', '?')}")
            click.echo(f"Tokens:   {row.get('token_count', '?')}")
            click.echo(f"Kind:     {row.get('chunk_kind', '?')}")
            click.echo(f"\n{row.get('content', '')[:500]}")

    finally:
        db.close()


# ---------------------------------------------------------------------------
# show-chunk
# ---------------------------------------------------------------------------

@cli.command("show-chunk")
@click.argument("chunk_id")
def show_chunk(chunk_id: str):
    """Show a chunk with its context (neighbours + node info)."""
    Session = get_session_local()
    db = Session()

    try:
        result = get_chunk_with_context(chunk_id, db)
        if result is None:
            click.echo(f"Chunk {chunk_id} not found.", err=True)
            raise SystemExit(1)

        chunk = result["chunk"]
        node = result["node"]

        click.echo(f"=== Chunk {chunk['id']} ===")
        click.echo(f"Path:       {chunk['heading_path']}")
        click.echo(f"Kind:       {chunk['chunk_kind']}")
        click.echo(f"Index:      {chunk['chunk_index']}")
        click.echo(f"Pages:      {chunk['page_start']}-{chunk['page_end']}")
        click.echo(f"Tokens:     {chunk['token_count']}")
        click.echo(f"Node type:  {node.get('node_type', '?')}")
        click.echo(f"Node depth: {node.get('depth', '?')}")
        click.echo(f"\n--- Content ---\n{chunk['content']}")

        if result["prev_content"]:
            click.echo(f"\n--- Prev chunk (excerpt) ---\n{result['prev_content'][:200]}")
        if result["next_content"]:
            click.echo(f"\n--- Next chunk (excerpt) ---\n{result['next_content'][:200]}")

    finally:
        db.close()


# ---------------------------------------------------------------------------
# status
# ---------------------------------------------------------------------------

@cli.command()
@click.option("--document-id", default=None, help="Filter by document ID")
def status(document_id: str | None):
    """Show ingestion run status."""
    from sqlalchemy import select

    Session = get_session_local()
    db = Session()

    try:
        query = select(RagDocument).order_by(RagDocument.created_at.desc()).limit(20)
        if document_id:
            query = select(RagDocument).where(RagDocument.id == document_id)

        docs = db.execute(query).scalars().all()

        if not docs:
            click.echo("No documents found.")
            return

        for doc in docs:
            click.echo(f"\n=== {doc.title} ===")
            click.echo(f"  ID:     {doc.id}")
            click.echo(f"  Status: {doc.status}")
            click.echo(f"  Pages:  {doc.page_count}")

            runs = db.execute(
                select(IngestionRun)
                .where(IngestionRun.document_id == doc.id)
                .order_by(IngestionRun.created_at)
            ).scalars().all()

            for run in runs:
                elapsed = ""
                if run.finished_at and run.created_at:
                    elapsed = f" ({(run.finished_at - run.created_at).total_seconds():.1f}s)"
                click.echo(f"  [{run.stage}] {run.status}{elapsed}  {run.message or ''}")

    finally:
        db.close()


# ---------------------------------------------------------------------------
# reprocess
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("document_id")
@click.option("--detector", default="general", type=click.Choice(["general", "medical"]))
@click.option("--embed-model", default=None)
def reprocess(document_id: str, detector: str, embed_model: str | None):
    """Re-run the ingestion pipeline for an existing document."""
    from sqlalchemy import select, delete

    Session = get_session_local()
    db = Session()

    try:
        doc = db.execute(
            select(RagDocument).where(RagDocument.id == document_id)
        ).scalar_one_or_none()

        if doc is None:
            click.echo(f"Document {document_id} not found.", err=True)
            raise SystemExit(1)

        material_id = doc.material_id

        # Delete old data
        click.echo(f"Deleting old data for document {document_id}...")
        db.execute(delete(IngestionRun).where(IngestionRun.document_id == document_id))
        # Chunks and nodes cascade from rag_documents
        db.delete(doc)
        db.flush()

        embedder = get_embedder(embed_model)
        heading_detector = get_detector(detector)

        click.echo("Re-running pipeline...")
        new_doc = ingest_document(material_id, db, embedder, heading_detector)
        click.echo(f"Done! New document id={new_doc.id}, status={new_doc.status}")

    except Exception as exc:
        click.echo(f"Error: {exc}", err=True)
        db.rollback()
        raise SystemExit(1)
    finally:
        db.close()


if __name__ == "__main__":
    cli()
