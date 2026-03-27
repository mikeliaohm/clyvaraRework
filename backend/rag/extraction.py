"""Text extraction from PDF, DOCX, and TXT files.

This module contains the low-level extraction functions used by both
the RAG pipeline and the existing routers.
"""

import io

import PyPDF2
from docx import Document
from fastapi import HTTPException

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
