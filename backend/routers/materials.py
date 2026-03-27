import os
import threading
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from config import openai_client, s3_client, S3_BUCKET_NAME, SYSTEM_USER_ID
from database import get_db, Material
from deps import get_current_user, _enforce_admin_access
from material_cache import cache_text, get_cached_text, invalidate_cache
from rag.extraction import extract_text_from_file

router = APIRouter(tags=["materials"])

ALLOWED_TYPES = ["pdf", "docx", "doc", "txt"]

LOCAL_UPLOAD_DIR = Path(os.getenv("LOCAL_UPLOAD_DIR", Path(__file__).resolve().parent.parent / "uploads"))


def _get_extension(filename: str) -> str:
    return filename.split(".")[-1].lower() if "." in filename else ""


def _store_file(file_content: bytes, s3_key: str, content_type: str) -> Optional[str]:
    """Store file to S3 if available, otherwise fall back to local filesystem."""
    if s3_client:
        try:
            s3_client.put_object(
                Bucket=S3_BUCKET_NAME,
                Key=s3_key,
                Body=file_content,
                ContentType=content_type or "application/octet-stream",
            )
            return f"s3://{S3_BUCKET_NAME}/{s3_key}"
        except Exception as e:
            print(f"S3 upload failed, falling back to local: {e}")

    # Local filesystem fallback
    local_path = LOCAL_UPLOAD_DIR / s3_key
    local_path.parent.mkdir(parents=True, exist_ok=True)
    local_path.write_bytes(file_content)
    return str(local_path)


def _run_rag_pipeline(material_id: int) -> None:
    """Run the new RAG pipeline for a material in a background thread."""
    from database import get_session_local
    from rag.embedder import get_embedder
    from rag.pipeline import ingest_document
    from rag.hierarchy_builder import GeneralDetector

    bg_db = get_session_local()()
    try:
        embedder = get_embedder()
        detector = GeneralDetector()
        ingest_document(material_id, bg_db, embedder, detector)

        bg_material = bg_db.query(Material).filter(Material.id == material_id).first()
        if bg_material:
            bg_material.status = "processed"
            bg_material.processing_progress = 100
            bg_material.processed_at = func.now()
            bg_db.commit()
            print(f"✓ RAG pipeline complete for material {material_id}")
    except Exception as e:
        try:
            m = bg_db.query(Material).filter(Material.id == material_id).first()
            if m:
                m.status = "failed"
                m.processing_error = str(e)
                bg_db.commit()
        except Exception:
            pass
        print(f"✗ RAG pipeline error for material {material_id}: {e}")
    finally:
        bg_db.close()


# ── User file upload ──────────────────────────────────────────

@router.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    file_extension = _get_extension(file.filename)
    if file_extension not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed: {', '.join(ALLOWED_TYPES)}")

    try:
        file_content = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")

    file_id = str(uuid4())
    s3_key = f"uploads/{current_user['user_id']}/{file_id}_{file.filename}"
    file_path = _store_file(file_content, s3_key, file.content_type or "")

    # Extract text for display in the dashboard
    try:
        extracted_text = extract_text_from_file(file_content, file_extension)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")

    material = Material(
        user_id=current_user["user_id"],
        title=file.filename,
        file_type=file_extension,
        file_path=file_path,
        file_size=len(file_content),
        extracted_text=extracted_text,
        status="processing",
        processing_progress=0,
    )
    db.add(material)
    db.commit()
    db.refresh(material)

    cache_text(material.id, extracted_text)

    # Run the new RAG pipeline in background
    threading.Thread(target=_run_rag_pipeline, args=(material.id,), daemon=True).start()

    return {
        "success": True,
        "material_id": material.id,
        "file_name": file.filename,
        "file_type": file_extension,
        "text_length": len(extracted_text),
        "file_path": file_path,
        "status": "processing",
        "message": "File uploaded. Processing with RAG pipeline in background.",
    }


# ── Admin system-material upload ─────────────────────────────

@router.post("/api/admin/upload-system-material")
async def upload_system_material(
    file: UploadFile = File(...),
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _enforce_admin_access(db, current_user, x_admin_key)

    file_extension = _get_extension(file.filename)
    if file_extension not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed: {', '.join(ALLOWED_TYPES)}")

    try:
        file_content = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")

    file_id = str(uuid4())
    s3_key = f"system-materials/{file_id}_{file.filename}"
    file_path = _store_file(file_content, s3_key, file.content_type or "")

    # Extract text for display
    try:
        extracted_text = extract_text_from_file(file_content, file_extension)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")

    existing = db.query(Material).filter(
        Material.user_id == SYSTEM_USER_ID,
        Material.title == file.filename,
        Material.status == "processed",
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"System material '{file.filename}' already exists")

    material = Material(
        user_id=SYSTEM_USER_ID,
        title=file.filename,
        file_type=file_extension,
        file_path=file_path,
        file_size=len(file_content),
        extracted_text=extracted_text,
        status="processing",
        processing_progress=0,
    )
    db.add(material)
    db.commit()
    db.refresh(material)

    cache_text(material.id, extracted_text)

    # Run the new RAG pipeline in background
    threading.Thread(target=_run_rag_pipeline, args=(material.id,), daemon=True).start()

    return {
        "success": True,
        "material_id": material.id,
        "file_name": file.filename,
        "file_type": file_extension,
        "file_size": len(file_content),
        "file_path": file_path,
        "status": "processing",
        "message": "System material uploaded. Processing with RAG pipeline in background.",
    }


# ── Materials list & delete ───────────────────────────────────

def _material_metadata(m: Material) -> dict:
    """Return lightweight metadata dict (no extracted text)."""
    return {
        "id": m.id,
        "title": m.title,
        "file_type": m.file_type,
        "file_size": m.file_size,
        "has_file": m.file_path is not None,
        "status": m.status,
        "processing_progress": m.processing_progress,
        "processing_error": m.processing_error,
        "chunk_count": m.chunk_count,
        "total_tokens": m.total_tokens,
        "embedding_model": m.embedding_model,
        "uploaded_at": m.uploaded_at.isoformat(),
        "processed_at": m.processed_at.isoformat() if m.processed_at else None,
        "last_accessed": m.last_accessed.isoformat() if m.last_accessed else None,
    }


@router.get("/api/materials")
def get_user_materials(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all materials for the current user (metadata only, no text content)."""
    materials = (
        db.query(Material)
        .filter(Material.user_id == current_user["user_id"])
        .order_by(Material.uploaded_at.desc())
        .all()
    )
    return {"materials": [_material_metadata(m) for m in materials]}


@router.get("/api/materials/{material_id}")
def get_material_detail(
    material_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get full material detail including extracted text."""
    material = db.query(Material).filter(
        Material.id == material_id,
        Material.user_id == current_user["user_id"],
    ).first()

    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    cached = get_cached_text(material.id)
    extracted_text = cached if cached is not None else material.extracted_text
    if cached is None and extracted_text:
        cache_text(material.id, extracted_text)

    result = _material_metadata(material)
    result["extracted_text"] = extracted_text
    return result


@router.delete("/api/materials/{material_id}")
def delete_material(
    material_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    material = db.query(Material).filter(
        Material.id == material_id,
        Material.user_id == current_user["user_id"],
    ).first()

    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    invalidate_cache(material_id)

    # Clean up RAG pipeline data
    from models.rag import RagDocument, RagChunk, RagNode
    rag_doc = db.query(RagDocument).filter(RagDocument.material_id == material_id).first()
    if rag_doc:
        db.query(RagChunk).filter(RagChunk.document_id == rag_doc.id).delete()
        db.query(RagNode).filter(RagNode.document_id == rag_doc.id).delete()
        db.delete(rag_doc)

    db.delete(material)
    db.commit()
    return {"success": True, "message": "Material deleted successfully"}


@router.get("/api/materials/{material_id}/download")
def download_material(
    material_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    material = db.query(Material).filter(
        Material.id == material_id,
        Material.user_id == current_user["user_id"],
    ).first()

    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    if not material.file_path:
        raise HTTPException(status_code=404, detail="Original file not available")

    # S3 files would need a presigned URL — for now, only local files are served
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
    media_type = content_types.get(material.file_type, "application/octet-stream")

    return FileResponse(
        path=file_path,
        filename=material.title,
        media_type=media_type,
    )


# ── Search (uses new RAG pipeline) ────────────────────────────

@router.get("/api/search")
def search_materials(
    query: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 5,
):
    from rag.embedder import get_embedder
    from rag.pipeline import search_chunks

    try:
        embedder = get_embedder()
        results = search_chunks(
            query=query,
            user_id=current_user["user_id"],
            db=db,
            embedder=embedder,
            top_k=limit,
        )
        return {"results": results, "query": query, "total_found": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")
