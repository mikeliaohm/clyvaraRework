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
from database import get_db, Material, VectorIndexEntry
from deps import get_current_user, _enforce_admin_access
from material_cache import cache_text, get_cached_text, invalidate_cache, invalidate_vector_cache
from utils.rag import chunk_text, extract_text_from_file, generate_embeddings

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
        status="processing",
        processing_progress=0,
    )
    db.add(material)
    db.commit()
    db.refresh(material)

    try:
        chunks = chunk_text(extracted_text)
        for i, chunk in enumerate(chunks):
            try:
                embedding = generate_embeddings(chunk)
                db.add(VectorIndexEntry(
                    user_id=current_user["user_id"],
                    content_hash=f"{file_id}_{i}",
                    embedding=embedding,
                    content=chunk,
                    token_count=len(chunk.split()),
                    chunk_index=i,
                    source_type="material",
                    source_id=material.id,
                    embedding_model="text-embedding-3-small",
                    vector_metadata={
                        "file_name": file.filename,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "file_type": file_extension,
                        "file_size": len(file_content),
                    },
                ))
            except Exception as e:
                print(f"Error creating embedding for chunk {i}: {e}")
                continue

        db.commit()
        material.status = "processed"
        material.processing_progress = 100
        material.chunk_count = len(chunks)
        material.total_tokens = sum(len(c.split()) for c in chunks)
        material.extracted_text = extracted_text
        material.processed_at = func.now()
        db.commit()
        cache_text(material.id, extracted_text)

        return {
            "success": True,
            "material_id": material.id,
            "file_name": file.filename,
            "file_type": file_extension,
            "chunks_created": len(chunks),
            "text_length": len(extracted_text),
            "file_path": file_path,
            "message": f"File processed successfully. Created {len(chunks)} chunks for RAG.",
        }
    except Exception as e:
        material.status = "failed"
        material.processing_error = str(e)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Error processing file for RAG: {str(e)}")


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
        status="processing",
        processing_progress=0,
    )
    db.add(material)
    db.commit()
    db.refresh(material)

    def process_material_background():
        from database import get_session_local
        background_db = get_session_local()()
        try:
            bg_material = background_db.query(Material).filter(Material.id == material.id).first()
            if not bg_material:
                return

            chunks = chunk_text(extracted_text)
            total_chunks = len(chunks)
            successful_chunks = 0

            for i, chunk in enumerate(chunks):
                try:
                    bg_material.processing_progress = int((i / total_chunks) * 100)
                    background_db.commit()

                    embedding = generate_embeddings(chunk)
                    background_db.add(VectorIndexEntry(
                        user_id=SYSTEM_USER_ID,
                        content_hash=f"{file_id}_{i}",
                        embedding=embedding,
                        content=chunk,
                        token_count=len(chunk.split()),
                        chunk_index=i,
                        source_type="material",
                        source_id=bg_material.id,
                        embedding_model="text-embedding-3-small",
                        vector_metadata={
                            "file_name": file.filename,
                            "chunk_index": i,
                            "total_chunks": total_chunks,
                            "file_type": file_extension,
                            "file_size": len(file_content),
                            "is_system": True,
                        },
                    ))
                    successful_chunks += 1
                    if (i + 1) % 10 == 0:
                        background_db.commit()
                except Exception as e:
                    print(f"Error creating embedding for chunk {i}: {e}")
                    continue

            background_db.commit()
            bg_material.status = "processed"
            bg_material.processing_progress = 100
            bg_material.chunk_count = successful_chunks
            bg_material.total_tokens = sum(len(c.split()) for c in chunks)
            bg_material.extracted_text = extracted_text
            bg_material.processed_at = func.now()
            background_db.commit()
            cache_text(bg_material.id, extracted_text)
            print(f"✓ Successfully processed system material: {file.filename} ({successful_chunks} chunks)")
        except Exception as e:
            try:
                m = background_db.query(Material).filter(Material.id == material.id).first()
                if m:
                    m.status = "failed"
                    m.processing_error = str(e)
                    background_db.commit()
            except Exception:
                pass
            print(f"✗ Error processing system material {file.filename}: {e}")
        finally:
            background_db.close()

    threading.Thread(target=process_material_background, daemon=True).start()

    return {
        "success": True,
        "material_id": material.id,
        "file_name": file.filename,
        "file_type": file_extension,
        "file_size": len(file_content),
        "file_path": file_path,
        "status": "processing",
        "message": "System material uploaded. Processing in background.",
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
    invalidate_vector_cache(material_id)

    db.query(VectorIndexEntry).filter(
        VectorIndexEntry.source_id == material_id,
        VectorIndexEntry.source_type == "material",
    ).delete()

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


# ── Search ────────────────────────────────────────────────────

@router.get("/api/search")
def search_materials(
    query: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 5,
):
    if not openai_client:
        raise HTTPException(status_code=503, detail="OpenAI client not configured")

    try:
        query_embedding = generate_embeddings(query)

        user_materials = db.query(Material).filter(
            or_(Material.user_id == current_user["user_id"], Material.user_id == SYSTEM_USER_ID),
            Material.status == "processed",
        ).all()

        material_ids = [m.id for m in user_materials]
        if not material_ids:
            return {"results": [], "message": "No processed materials found"}

        vector_entries = db.query(VectorIndexEntry).filter(
            VectorIndexEntry.source_id.in_(material_ids),
            VectorIndexEntry.source_type == "material",
            or_(
                VectorIndexEntry.user_id == current_user["user_id"],
                VectorIndexEntry.user_id == SYSTEM_USER_ID,
            ),
        ).all()

        results = sorted(
            [
                {
                    "content": e.content,
                    "similarity": sum(a * b for a, b in zip(query_embedding, e.embedding)),
                    "metadata": e.vector_metadata,
                    "source_id": e.source_id,
                    "is_system": e.user_id == SYSTEM_USER_ID,
                }
                for e in vector_entries
            ],
            key=lambda x: x["similarity"],
            reverse=True,
        )

        return {"results": results[:limit], "query": query, "total_found": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")
