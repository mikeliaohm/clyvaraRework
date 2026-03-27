"""Admin-only API endpoints.

Provides user management, system material management,
and RAG search testing for admin users.
"""

import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from config import SYSTEM_USER_ID
from database import get_db, Material, User, Role, UserRole
from deps import get_current_user, _enforce_admin_access
from rag.embedder import get_embedder
from rag.pipeline import search_chunks, get_chunk_with_context
from models.rag import RagDocument, RagNode, RagChunk

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ── Schemas ──────────────────────────────────────────────────

class UserListItem(BaseModel):
    id: int
    email: str
    username: str | None = None
    full_name: str | None = None
    specialty: str | None = None
    is_active: bool
    roles: list[str] = []
    created_at: str | None = None


class RagSearchRequest(BaseModel):
    query: str
    top_k: int = 5


class RagSearchResult(BaseModel):
    chunk_id: str
    content: str
    heading_path: str | None = None
    chunk_kind: str | None = None
    page_start: int | None = None
    page_end: int | None = None
    token_count: int | None = None
    document_title: str | None = None
    document_id: str | None = None
    score: float | None = None


# ── User list ────────────────────────────────────────────────

@router.get("/users")
def list_users(
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _enforce_admin_access(db, current_user, x_admin_key)

    users = db.query(User).order_by(User.created_at.desc()).all()
    result = []
    for u in users:
        role_names = [
            row[0]
            for row in db.query(Role.name)
            .join(UserRole, UserRole.role_id == Role.id)
            .filter(UserRole.user_id == u.id)
            .all()
        ]
        result.append(UserListItem(
            id=u.id,
            email=u.email,
            username=u.username,
            full_name=u.full_name,
            specialty=u.specialty,
            is_active=u.is_active,
            roles=role_names,
            created_at=u.created_at.isoformat() if u.created_at else None,
        ))
    return {"users": [r.model_dump() for r in result]}


# ── System materials ─────────────────────────────────────────

@router.get("/system-materials")
def list_system_materials(
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _enforce_admin_access(db, current_user, x_admin_key)

    materials = (
        db.query(Material)
        .filter(Material.user_id == SYSTEM_USER_ID)
        .order_by(Material.uploaded_at.desc())
        .all()
    )
    return {
        "materials": [
            {
                "id": m.id,
                "title": m.title,
                "file_type": m.file_type,
                "file_size": m.file_size,
                "status": m.status,
                "processing_progress": m.processing_progress,
                "processing_error": m.processing_error,
                "chunk_count": m.chunk_count,
                "total_tokens": m.total_tokens,
                "uploaded_at": m.uploaded_at.isoformat() if m.uploaded_at else None,
                "processed_at": m.processed_at.isoformat() if m.processed_at else None,
            }
            for m in materials
        ]
    }


# ── Delete system material ───────────────────────────────────

@router.delete("/system-materials/{material_id}")
def delete_system_material(
    material_id: int,
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _enforce_admin_access(db, current_user, x_admin_key)

    from material_cache import invalidate_cache

    material = db.query(Material).filter(
        Material.id == material_id,
        Material.user_id == SYSTEM_USER_ID,
    ).first()
    if not material:
        raise HTTPException(status_code=404, detail="System material not found")

    invalidate_cache(material_id)

    # Clean up RAG pipeline data
    rag_doc = db.query(RagDocument).filter(RagDocument.material_id == material_id).first()
    if rag_doc:
        db.query(RagChunk).filter(RagChunk.document_id == rag_doc.id).delete()
        db.query(RagNode).filter(RagNode.document_id == rag_doc.id).delete()
        db.delete(rag_doc)

    db.delete(material)
    db.commit()
    return {"success": True, "message": "System material deleted"}


# ── Reprocess system material ────────────────────────────────

@router.post("/system-materials/{material_id}/reprocess")
def reprocess_system_material(
    material_id: int,
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Re-run the RAG pipeline for a system material (clears old data first)."""
    import threading
    _enforce_admin_access(db, current_user, x_admin_key)

    material = db.query(Material).filter(
        Material.id == material_id,
        Material.user_id == SYSTEM_USER_ID,
    ).first()
    if not material:
        raise HTTPException(status_code=404, detail="System material not found")

    # Clean old RAG data
    rag_doc = db.query(RagDocument).filter(RagDocument.material_id == material_id).first()
    if rag_doc:
        from models.rag import IngestionRun
        db.query(RagChunk).filter(RagChunk.document_id == rag_doc.id).delete()
        db.query(RagNode).filter(RagNode.document_id == rag_doc.id).delete()
        db.query(IngestionRun).filter(IngestionRun.document_id == rag_doc.id).delete()
        db.delete(rag_doc)

    material.status = "processing"
    material.processing_progress = 0
    material.chunk_count = 0
    db.commit()

    # Run pipeline in background
    from routers.materials import _run_rag_pipeline
    threading.Thread(target=_run_rag_pipeline, args=(material.id,), daemon=True).start()

    return {"success": True, "message": f"Reprocessing '{material.title}' in background."}


# ── System material detail & download ────────────────────────

@router.get("/system-materials/{material_id}/detail")
def get_system_material_detail(
    material_id: int,
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get full system material detail including extracted text."""
    _enforce_admin_access(db, current_user, x_admin_key)

    from material_cache import get_cached_text, cache_text

    material = db.query(Material).filter(
        Material.id == material_id,
        Material.user_id == SYSTEM_USER_ID,
    ).first()
    if not material:
        raise HTTPException(status_code=404, detail="System material not found")

    cached = get_cached_text(material.id)
    extracted_text = cached if cached is not None else material.extracted_text
    if cached is None and extracted_text:
        cache_text(material.id, extracted_text)

    return {
        "id": material.id,
        "title": material.title,
        "file_type": material.file_type,
        "file_size": material.file_size,
        "has_file": material.file_path is not None,
        "status": material.status,
        "chunk_count": material.chunk_count,
        "extracted_text": extracted_text,
        "uploaded_at": material.uploaded_at.isoformat() if material.uploaded_at else None,
    }


@router.get("/system-materials/{material_id}/download")
def download_system_material(
    material_id: int,
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Download the original file for a system material."""
    _enforce_admin_access(db, current_user, x_admin_key)

    material = db.query(Material).filter(
        Material.id == material_id,
        Material.user_id == SYSTEM_USER_ID,
    ).first()
    if not material:
        raise HTTPException(status_code=404, detail="System material not found")
    if not material.file_path:
        raise HTTPException(status_code=404, detail="Original file not available")
    if material.file_path.startswith("s3://"):
        raise HTTPException(status_code=501, detail="S3 download not yet implemented")

    file_path = Path(material.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")

    content_types = {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "doc": "application/msword",
        "txt": "text/plain",
    }
    return FileResponse(
        path=file_path,
        filename=material.title,
        media_type=content_types.get(material.file_type, "application/octet-stream"),
    )


# ── RAG search test ──────────────────────────────────────────

@router.post("/rag-search")
def admin_rag_search(
    body: RagSearchRequest,
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Test the new pgvector RAG pipeline. Searches system-wide documents."""
    _enforce_admin_access(db, current_user, x_admin_key)

    t0 = time.perf_counter()
    embedder = get_embedder()
    t_embedder = time.perf_counter()

    results = search_chunks(
        query=body.query,
        user_id=SYSTEM_USER_ID,
        db=db,
        embedder=embedder,
        top_k=body.top_k,
    )
    t_search = time.perf_counter()

    return {
        "query": body.query,
        "timing_ms": {
            "total": round((t_search - t0) * 1000, 1),
            "embedder": round((t_embedder - t0) * 1000, 1),
            "search": round((t_search - t_embedder) * 1000, 1),
        },
        "results": [
            {
                "chunk_id": str(r.get("chunk_id", "")),
                "content": r.get("content", ""),
                "content_display": r.get("content_display") or r.get("content", ""),
                "heading_path": r.get("heading_path"),
                "chunk_kind": r.get("chunk_kind"),
                "page_start": r.get("page_start"),
                "page_end": r.get("page_end"),
                "token_count": r.get("token_count"),
                "document_title": r.get("document_title"),
                "document_id": str(r.get("document_id", "")),
                "score": round(float(r.get("score", 0)), 4),
            }
            for r in results
        ],
        "total_results": len(results),
    }


# ── Document tree (hierarchy + chunks) ───────────────────────

@router.get("/documents/{material_id}/tree")
def get_document_tree(
    material_id: int,
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the document hierarchy tree with chunk info for visualization."""
    _enforce_admin_access(db, current_user, x_admin_key)

    rag_doc = db.query(RagDocument).filter(RagDocument.material_id == material_id).first()
    if not rag_doc:
        raise HTTPException(status_code=404, detail="No RAG document found for this material")

    doc_id = str(rag_doc.id)

    nodes = (
        db.query(RagNode)
        .filter(RagNode.document_id == doc_id)
        .order_by(RagNode.depth, RagNode.child_index)
        .all()
    )

    chunks = (
        db.query(RagChunk)
        .filter(RagChunk.document_id == doc_id)
        .order_by(RagChunk.chunk_index)
        .all()
    )

    # Group chunks by node
    chunks_by_node: dict[str, list] = {}
    for c in chunks:
        nid = str(c.node_id)
        chunks_by_node.setdefault(nid, []).append({
            "id": str(c.id),
            "chunk_index": c.chunk_index,
            "chunk_kind": c.chunk_kind,
            "heading_path": c.heading_path,
            "page_start": c.page_start,
            "page_end": c.page_end,
            "token_count": c.token_count,
            "content_preview": (c.content or "")[:200],
            "has_markdown": bool(c.content_display),
        })

    # Build node list with children references
    node_list = []
    for n in nodes:
        nid = str(n.id)
        node_list.append({
            "id": nid,
            "parent_id": str(n.parent_id) if n.parent_id else None,
            "node_type": n.node_type,
            "ordinal_label": n.ordinal_label,
            "heading_text": n.heading_text,
            "heading_path": n.heading_path,
            "depth": n.depth,
            "page_start": n.page_start,
            "page_end": n.page_end,
            "token_count": n.token_count,
            "chunks": chunks_by_node.get(nid, []),
        })

    return {
        "document_id": doc_id,
        "title": rag_doc.title,
        "page_count": rag_doc.page_count,
        "status": rag_doc.status,
        "total_nodes": len(nodes),
        "total_chunks": len(chunks),
        "nodes": node_list,
    }


# ── Chunk detail ─────────────────────────────────────────────

@router.get("/chunks/{chunk_id}")
def get_chunk_detail(
    chunk_id: str,
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return full chunk content with context (prev/next chunks)."""
    _enforce_admin_access(db, current_user, x_admin_key)

    result = get_chunk_with_context(chunk_id, db)
    if result is None:
        raise HTTPException(status_code=404, detail="Chunk not found")

    return result
