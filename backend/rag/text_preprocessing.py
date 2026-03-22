"""Text cleaning pipeline for RAG ingestion.

Designed to run on per-page text extracted from PDFs before hierarchy
detection and chunking.
"""

from __future__ import annotations

import re
from collections import Counter

import tiktoken


# ---------------------------------------------------------------------------
# Individual cleaning steps
# ---------------------------------------------------------------------------

def remove_headers_footers(page_texts: list[str], threshold: float = 0.5) -> list[str]:
    """Strip repeating first/last lines that appear on many pages (headers/footers).

    A line is treated as a header/footer if it appears on at least
    *threshold* fraction of all pages.
    """
    if len(page_texts) < 3:
        return page_texts

    min_count = max(2, int(len(page_texts) * threshold))

    first_lines: Counter[str] = Counter()
    last_lines: Counter[str] = Counter()

    for page in page_texts:
        lines = page.strip().splitlines()
        if lines:
            first_lines[lines[0].strip()] += 1
            last_lines[lines[-1].strip()] += 1

    header_lines = {line for line, cnt in first_lines.items() if cnt >= min_count}
    footer_lines = {line for line, cnt in last_lines.items() if cnt >= min_count}

    cleaned: list[str] = []
    for page in page_texts:
        lines = page.strip().splitlines()
        if lines and lines[0].strip() in header_lines:
            lines = lines[1:]
        if lines and lines[-1].strip() in footer_lines:
            lines = lines[:-1]
        cleaned.append("\n".join(lines))

    return cleaned


def remove_page_numbers(text: str) -> str:
    """Remove standalone page numbers (lines that are just a number)."""
    return re.sub(r"(?m)^\s*\d{1,4}\s*$", "", text)


def fix_hyphenation(text: str) -> str:
    """Rejoin words split across lines by a hyphen.

    Example: "anes-\\nthesia" → "anesthesia"
    """
    return re.sub(r"(\w)-\n(\w)", r"\1\2", text)


def merge_wrapped_lines(text: str) -> str:
    """Merge lines that are mid-sentence (lowercase continuation).

    Only merges when the previous line does NOT end with sentence-ending
    punctuation and the next line starts with a lowercase letter.
    """
    return re.sub(r"([^.!?:;\n])\n([a-z])", r"\1 \2", text)


def _sanitize_control_chars(text: str) -> str:
    """Remove NUL and other control bytes that PostgreSQL rejects."""
    text = text.replace("\x00", "")
    return re.sub(r"[\x01-\x08\x0b\x0c\x0e-\x1f]", " ", text)


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def clean_text(text: str) -> str:
    """Apply the full cleaning pipeline to a single text string."""
    text = _sanitize_control_chars(text)
    text = remove_page_numbers(text)
    text = fix_hyphenation(text)
    text = merge_wrapped_lines(text)
    return text.strip()


def clean_pages(page_texts: list[str]) -> list[str]:
    """Apply the full pipeline to a list of per-page strings.

    Headers/footers are removed first (needs cross-page analysis), then
    each page is individually cleaned.
    """
    pages = remove_headers_footers(page_texts)
    return [clean_text(p) for p in pages]


# ---------------------------------------------------------------------------
# Token counting
# ---------------------------------------------------------------------------

_encoder: tiktoken.Encoding | None = None


def count_tokens(text: str, model: str = "cl100k_base") -> int:
    """Return the number of tokens in *text* using the given tiktoken model."""
    global _encoder
    if _encoder is None:
        _encoder = tiktoken.get_encoding(model)
    return len(_encoder.encode(text))
