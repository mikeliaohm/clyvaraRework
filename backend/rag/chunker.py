"""Hierarchy-aware chunking engine.

Traverses a tree of NodeData objects and produces RagChunk-compatible
data containers.  Respects the chunking policy from the RAG architecture:

  - Target: 250-600 tokens
  - Soft max: 800 tokens
  - Hard max: 1000 tokens
  - Overlap: 40-80 tokens (same parent only)
  - Clinical moments -> standalone chunk
  - References -> excluded from embedding
  - Never merge across section boundaries
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from typing import Optional

from rag.hierarchy_builder import NodeData
from rag.text_preprocessing import count_tokens


# ---------------------------------------------------------------------------
# Chunk size policy
# ---------------------------------------------------------------------------

TARGET_MIN = 250
TARGET_MAX = 600
SOFT_MAX = 800
HARD_MAX = 1000
OVERLAP_TOKENS = 60


# ---------------------------------------------------------------------------
# Chunk data container
# ---------------------------------------------------------------------------

@dataclass
class ChunkData:
    """Lightweight chunk before DB persistence."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str = ""
    node_id: str = ""

    chunk_index: int = 0
    chunk_kind: str = "semantic"   # semantic | clinical_moment | overlap

    heading_path: str = ""
    page_start: Optional[int] = None
    page_end: Optional[int] = None

    token_count: int = 0
    content: str = ""
    content_for_embedding: str = ""

    embedding_model: str = ""

    prev_chunk_id: Optional[str] = None
    next_chunk_id: Optional[str] = None


# ---------------------------------------------------------------------------
# Splitting helpers
# ---------------------------------------------------------------------------

def _split_by_paragraphs(text: str) -> list[str]:
    """Split text on blank-line boundaries."""
    paragraphs = re.split(r"\n\s*\n", text)
    return [p.strip() for p in paragraphs if p.strip()]


def _split_by_sentences(text: str) -> list[str]:
    """Simple sentence splitter (period/question/exclamation followed by space)."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if s.strip()]


def _group_segments(segments: list[str], target: int, hard_max: int) -> list[str]:
    """Greedily group segments into chunks that stay under *hard_max* tokens,
    aiming for around *target* tokens each."""
    groups: list[str] = []
    current: list[str] = []
    current_tokens = 0

    for seg in segments:
        seg_tokens = count_tokens(seg)
        if current and current_tokens + seg_tokens > hard_max:
            groups.append("\n\n".join(current))
            current = [seg]
            current_tokens = seg_tokens
        else:
            current.append(seg)
            current_tokens += seg_tokens

    if current:
        groups.append("\n\n".join(current))

    return groups


def split_if_needed(text: str, target: int = TARGET_MAX, hard_max: int = HARD_MAX) -> list[str]:
    """Split *text* into pieces that fit within *hard_max* tokens.

    Strategy (in order):
      1. Split by paragraphs
      2. If any paragraph still exceeds hard_max, split by sentences
    """
    tokens = count_tokens(text)
    if tokens <= hard_max:
        return [text]

    paragraphs = _split_by_paragraphs(text)

    # If any single paragraph is too large, break it into sentences
    expanded: list[str] = []
    for para in paragraphs:
        if count_tokens(para) > hard_max:
            expanded.extend(_split_by_sentences(para))
        else:
            expanded.append(para)

    return _group_segments(expanded, target, hard_max)


# ---------------------------------------------------------------------------
# Merging helper
# ---------------------------------------------------------------------------

def merge_small_chunks(
    chunks: list[ChunkData],
    min_tokens: int = TARGET_MIN,
    max_merged: int = TARGET_MAX,
) -> list[ChunkData]:
    """Merge adjacent small chunks that share the same parent node.

    Rules:
      - Only merge if both are "semantic" kind
      - Only merge if combined token count <= max_merged
      - Never merge clinical_moment chunks
    """
    if not chunks:
        return chunks

    merged: list[ChunkData] = [chunks[0]]

    for chunk in chunks[1:]:
        prev = merged[-1]
        can_merge = (
            prev.chunk_kind == "semantic"
            and chunk.chunk_kind == "semantic"
            and prev.node_id == chunk.node_id
            and prev.token_count + chunk.token_count <= max_merged
        )
        if can_merge:
            prev.content = prev.content + "\n\n" + chunk.content
            prev.token_count = count_tokens(prev.content)
            prev.page_end = chunk.page_end or prev.page_end
        else:
            merged.append(chunk)

    return merged


# ---------------------------------------------------------------------------
# Embedding input formatter
# ---------------------------------------------------------------------------

def build_embedding_input(chunk: ChunkData, title: str = "") -> str:
    """Build the text that will be embedded (includes heading context)."""
    parts: list[str] = []
    if title:
        parts.append(f"Title: {title}")
    if chunk.heading_path:
        parts.append(f"Path: {chunk.heading_path}")
    if chunk.chunk_kind == "clinical_moment":
        parts.append("Type: clinical_moment")
    parts.append("")
    parts.append(chunk.content)
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def chunk_document(
    nodes: list[NodeData],
    document_id: str,
    embedding_model: str,
    title: str = "",
) -> list[ChunkData]:
    """Produce chunks from a hierarchy tree.

    Args:
        nodes: flat list of NodeData (as returned by build_hierarchy)
        document_id: UUID of the RagDocument
        embedding_model: model name to record on each chunk
        title: document title (used in embedding input)

    Returns:
        Ordered list of ChunkData ready for persistence.
    """
    # Build a lookup from id -> NodeData
    node_map = {n.id: n for n in nodes}

    chunks: list[ChunkData] = []

    for node in nodes:
        if node.node_type == "root":
            continue

        text = (node.cleaned_text or node.raw_text or "").strip()
        if not text:
            continue

        # References are excluded from embedding
        if node.node_type == "reference":
            continue

        # Clinical moments -> standalone chunk
        if node.node_type == "clinical_moment":
            cd = ChunkData(
                document_id=document_id,
                node_id=node.id,
                chunk_kind="clinical_moment",
                heading_path=node.heading_path,
                page_start=node.page_start,
                page_end=node.page_end,
                token_count=count_tokens(text),
                content=text,
                embedding_model=embedding_model,
            )
            cd.content_for_embedding = build_embedding_input(cd, title)
            chunks.append(cd)
            continue

        # Regular node -- split if needed
        pieces = split_if_needed(text)

        for piece in pieces:
            cd = ChunkData(
                document_id=document_id,
                node_id=node.id,
                chunk_kind="semantic",
                heading_path=node.heading_path,
                page_start=node.page_start,
                page_end=node.page_end,
                token_count=count_tokens(piece),
                content=piece,
                embedding_model=embedding_model,
            )
            cd.content_for_embedding = build_embedding_input(cd, title)
            chunks.append(cd)

    # Merge adjacent small chunks (same parent)
    chunks = merge_small_chunks(chunks)

    # Assign sequential chunk_index and link prev/next
    for i, chunk in enumerate(chunks):
        chunk.chunk_index = i
        if i > 0:
            chunk.prev_chunk_id = chunks[i - 1].id
            chunks[i - 1].next_chunk_id = chunk.id

    return chunks
