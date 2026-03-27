"""Text extraction from PDF, DOCX, and TXT files.

Uses PyMuPDF (fitz) for PDF extraction with font metadata,
producing both plain text (for embedding) and markdown (for display).
"""

import io
import re
import statistics
from dataclasses import dataclass

import fitz  # PyMuPDF
from docx import Document
from fastapi import HTTPException


@dataclass
class PageExtraction:
    """Dual-format extraction result for a single page."""
    plain_text: str
    markdown_text: str


# ---------------------------------------------------------------------------
# PDF extraction (PyMuPDF)
# ---------------------------------------------------------------------------

def _spans_to_markdown(page: fitz.Page, body_size: float) -> str:
    """Convert a page's text blocks into markdown using font metadata.

    Args:
        page: a PyMuPDF page object
        body_size: the most common font size in the document (used as baseline)
    """
    blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]
    md_lines: list[str] = []

    for block in blocks:
        if block.get("type") != 0:  # skip image blocks
            continue

        block_lines: list[str] = []
        for line in block.get("lines", []):
            line_parts: list[str] = []
            line_is_heading = False
            line_size = 0

            for span in line.get("spans", []):
                text = span.get("text", "")
                if not text:
                    continue

                size = span.get("size", body_size)
                flags = span.get("flags", 0)
                is_bold = bool(flags & 16) or "bold" in span.get("font", "").lower()
                is_italic = bool(flags & 2) or "italic" in span.get("font", "").lower()

                line_size = max(line_size, size)

                # Apply inline formatting
                formatted = text
                if is_bold and is_italic:
                    formatted = f"***{text.strip()}*** " if text.strip() else text
                elif is_bold:
                    formatted = f"**{text.strip()}** " if text.strip() else text
                elif is_italic:
                    formatted = f"*{text.strip()}* " if text.strip() else text

                line_parts.append(formatted)

            if not line_parts:
                continue

            joined = "".join(line_parts).rstrip()

            # Detect headings by font size relative to body text
            if line_size > 0 and body_size > 0:
                ratio = line_size / body_size
                if ratio >= 1.6 and joined.strip():
                    joined = f"# {joined.strip()}"
                    line_is_heading = True
                elif ratio >= 1.25 and joined.strip():
                    joined = f"## {joined.strip()}"
                    line_is_heading = True

            block_lines.append(joined)

        if block_lines:
            md_lines.append("\n".join(block_lines))

    return "\n\n".join(md_lines)


def _compute_body_font_size(doc: fitz.Document) -> float:
    """Find the most common (mode) font size in the document."""
    sizes: list[float] = []
    for page in doc:
        blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]
        for block in blocks:
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = span.get("text", "").strip()
                    if text and len(text) > 2:  # skip tiny fragments
                        sizes.append(round(span.get("size", 0), 1))

    if not sizes:
        return 12.0

    # Use mode (most common size) as baseline for body text
    try:
        return statistics.mode(sizes)
    except statistics.StatisticsError:
        return statistics.median(sizes)


def extract_pages_from_pdf(file_content: bytes) -> list[str]:
    """Return a list of per-page plain text strings extracted from a PDF."""
    try:
        doc = fitz.open(stream=file_content, filetype="pdf")
        pages = [page.get_text() or "" for page in doc]
        doc.close()
        return pages
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error extracting PDF pages: {str(e)}")


def extract_pages_with_markdown(file_content: bytes) -> list[PageExtraction]:
    """Extract per-page plain text AND markdown-formatted text from a PDF.

    Returns a list of PageExtraction(plain_text, markdown_text).
    """
    try:
        doc = fitz.open(stream=file_content, filetype="pdf")
        body_size = _compute_body_font_size(doc)

        results: list[PageExtraction] = []
        for page in doc:
            plain = page.get_text() or ""
            markdown = _spans_to_markdown(page, body_size)
            results.append(PageExtraction(plain_text=plain, markdown_text=markdown))

        doc.close()
        return results
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error extracting PDF: {str(e)}")


def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract all text from a PDF as a single plain string."""
    try:
        doc = fitz.open(stream=file_content, filetype="pdf")
        text = ""
        for page in doc:
            text += (page.get_text() or "") + "\n"
        doc.close()
        return text.strip()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error extracting PDF text: {str(e)}")


# ---------------------------------------------------------------------------
# DOCX / TXT extraction (unchanged)
# ---------------------------------------------------------------------------

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
    text = text.replace("\x00", "")
    return re.sub(r"[\x01-\x08\x0b\x0c\x0e-\x1f]", " ", text)


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
