import io
from typing import List

import PyPDF2
from docx import Document
from fastapi import HTTPException

from config import openai_client


def extract_pages_from_pdf(file_content: bytes) -> list[str]:
    """Return a list of per-page text strings extracted from a PDF."""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
        return [page.extract_text() or "" for page in pdf_reader.pages]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error extracting PDF pages: {str(e)}")


def extract_text_from_pdf(file_content: bytes) -> str:
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error extracting PDF text: {str(e)}")


def extract_text_from_docx(file_content: bytes) -> str:
    try:
        doc = Document(io.BytesIO(file_content))
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text.strip()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error extracting DOCX text: {str(e)}")


def _sanitize_text(text: str) -> str:
    """Remove NUL and other control bytes that PostgreSQL text columns reject."""
    import re
    text = text.replace("\x00", "")
    text = re.sub(r"[\x01-\x08\x0b\x0c\x0e-\x1f]", " ", text)
    return text


def extract_text_from_file(file_content: bytes, file_type: str) -> str:
    if file_type.lower() == "pdf":
        raw = extract_text_from_pdf(file_content)
    elif file_type.lower() in ["docx", "doc"]:
        raw = extract_text_from_docx(file_content)
    elif file_type.lower() == "txt":
        raw = file_content.decode("utf-8")
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_type}")
    return _sanitize_text(raw)


def generate_embeddings(text: str) -> List[float]:
    if not openai_client:
        raise HTTPException(status_code=503, detail="OpenAI client not configured")

    try:
        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text,
        )
        return response.data[0].embedding
    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "invalid_api_key" in error_msg.lower():
            raise HTTPException(
                status_code=500,
                detail="Error generating embeddings: Invalid OpenAI API key.",
            )
        elif "403" in error_msg or "forbidden" in error_msg.lower():
            raise HTTPException(
                status_code=500,
                detail="Error generating embeddings: API key access denied (403).",
            )
        elif "429" in error_msg or "rate limit" in error_msg.lower():
            raise HTTPException(
                status_code=500,
                detail="Error generating embeddings: Rate limit exceeded.",
            )
        else:
            raise HTTPException(
                status_code=500, detail=f"Error generating embeddings: {error_msg}"
            )


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunks.append(" ".join(words[i : i + chunk_size]))
    return chunks
