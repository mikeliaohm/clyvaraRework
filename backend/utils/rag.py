"""Backward-compatibility shim — re-exports from rag.extraction.

Existing routers (materials, chat, care_plans, learning_plans) import from
here.  New code should import from rag.extraction directly.
"""

from rag.extraction import (  # noqa: F401
    extract_pages_from_pdf,
    extract_text_from_pdf,
    extract_text_from_docx,
    extract_text_from_file,
    generate_embeddings,
    chunk_text,
)
