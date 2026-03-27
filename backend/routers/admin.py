"""Admin-only API endpoints.

Provides user management, system material management,
and RAG search testing for admin users.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from config import SYSTEM_USER_ID
from database import get_db, Material, User, Role, UserRole
from deps import get_current_user, _enforce_admin_access
from rag.embedder import get_embedder
from rag.pipeline import search_chunks

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

    from database import VectorIndexEntry
    from material_cache import invalidate_cache, invalidate_vector_cache

    material = db.query(Material).filter(
        Material.id == material_id,
        Material.user_id == SYSTEM_USER_ID,
    ).first()
    if not material:
        raise HTTPException(status_code=404, detail="System material not found")

    invalidate_cache(material_id)
    invalidate_vector_cache(material_id)

    db.query(VectorIndexEntry).filter(
        VectorIndexEntry.source_id == material_id,
        VectorIndexEntry.source_type == "material",
    ).delete()

    db.delete(material)
    db.commit()
    return {"success": True, "message": "System material deleted"}


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

    embedder = get_embedder()
    results = search_chunks(
        query=body.query,
        user_id=SYSTEM_USER_ID,
        db=db,
        embedder=embedder,
        top_k=body.top_k,
    )

    return {
        "query": body.query,
        "results": [
            {
                "chunk_id": str(r.get("chunk_id", "")),
                "content": r.get("content", ""),
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
