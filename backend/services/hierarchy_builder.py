"""Detect document structure and build a hierarchy tree of RagNode objects.

Two detector presets are provided:
  - GeneralDetector:          markdown headings, numbered headings, ALL-CAPS
  - MedicalTextbookDetector:  extends General with roman-numeral sections,
                              letter subsections, CLINICAL MOMENT markers,
                              and REFERENCES / SUGGESTED READINGS exclusions
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from typing import Optional, Protocol, runtime_checkable

from services.text_preprocessing import count_tokens


# ---------------------------------------------------------------------------
# Data container (mirrors RagNode columns, but not an ORM object yet)
# ---------------------------------------------------------------------------

@dataclass
class NodeData:
    """Lightweight representation of a hierarchy node before DB persistence."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str = ""
    parent_id: Optional[str] = None

    node_type: str = "root"          # chapter | section | subsection | item | clinical_moment | reference | root
    ordinal_label: str = ""          # "I", "A", "3", etc.
    heading_text: str = ""
    heading_path: str = ""           # e.g. "Chapter 1 > Section I > A"

    depth: int = 0
    page_start: Optional[int] = None
    page_end: Optional[int] = None

    raw_text: str = ""
    cleaned_text: str = ""
    token_count: int = 0

    child_index: int = 0
    children: list["NodeData"] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Heading detection result
# ---------------------------------------------------------------------------

@dataclass
class HeadingMatch:
    node_type: str
    ordinal_label: str
    heading_text: str
    depth: int               # determines nesting level (lower = higher in tree)


# ---------------------------------------------------------------------------
# Detector protocol
# ---------------------------------------------------------------------------

@runtime_checkable
class HeadingDetector(Protocol):
    def detect_heading(self, line: str) -> Optional[HeadingMatch]:
        """Return a HeadingMatch if the line is a heading, else None."""
        ...


# ---------------------------------------------------------------------------
# General detector
# ---------------------------------------------------------------------------

# Precompiled patterns
_MD_HEADING = re.compile(r"^(#{1,4})\s+(.+)")
_NUMBERED_HEADING = re.compile(r"^(\d+(?:\.\d+)*)\.\s+(.+)")
_ALL_CAPS_HEADING = re.compile(r"^([A-Z][A-Z\s]{4,})$")


class GeneralDetector:
    """Detects markdown-style headings, numbered headings, and ALL-CAPS lines."""

    def detect_heading(self, line: str) -> Optional[HeadingMatch]:
        stripped = line.strip()
        if not stripped:
            return None

        # Markdown headings: # Title, ## Section, etc.
        m = _MD_HEADING.match(stripped)
        if m:
            level = len(m.group(1))
            types = {1: "chapter", 2: "section", 3: "subsection", 4: "item"}
            return HeadingMatch(
                node_type=types.get(level, "item"),
                ordinal_label="",
                heading_text=m.group(2).strip(),
                depth=level,
            )

        # Numbered headings: 1. Title, 1.1. Title
        m = _NUMBERED_HEADING.match(stripped)
        if m:
            parts = m.group(1).split(".")
            depth = len(parts)
            types = {1: "chapter", 2: "section", 3: "subsection"}
            return HeadingMatch(
                node_type=types.get(depth, "item"),
                ordinal_label=m.group(1),
                heading_text=m.group(2).strip(),
                depth=depth,
            )

        # ALL-CAPS lines (at least 5 chars, starts with letter)
        m = _ALL_CAPS_HEADING.match(stripped)
        if m and len(stripped) >= 5:
            return HeadingMatch(
                node_type="section",
                ordinal_label="",
                heading_text=stripped.title(),
                depth=2,
            )

        return None


# ---------------------------------------------------------------------------
# Medical-textbook detector
# ---------------------------------------------------------------------------

_CHAPTER = re.compile(r"^(?:CHAPTER|Chapter)\s+(\d+|[IVXLC]+)[.:]\s*(.*)", re.IGNORECASE)
_ROMAN_SECTION = re.compile(r"^([IVXLC]+)\.\s+(.+)")
_LETTER_SUBSECTION = re.compile(r"^([A-Z])\.\s+(.+)")
_NUMBERED_ITEM = re.compile(r"^(\d+)\.\s+(.+)")
_CLINICAL_MOMENT = re.compile(r"CLINICAL\s+MOMENT", re.IGNORECASE)
_REFERENCES = re.compile(r"^(?:REFERENCES?|SUGGESTED\s+READINGS?|BIBLIOGRAPHY)", re.IGNORECASE)


class MedicalTextbookDetector(GeneralDetector):
    """Extends GeneralDetector with medical-textbook–specific patterns.

    Priority order (checked first → last):
      1. CLINICAL MOMENT markers
      2. REFERENCES / SUGGESTED READINGS
      3. Chapter headings
      4. Roman-numeral sections (I., II., III.)
      5. Letter subsections (A., B., C.)
      6. Numbered items (1., 2., 3.)
      7. Fall through to GeneralDetector
    """

    def detect_heading(self, line: str) -> Optional[HeadingMatch]:
        stripped = line.strip()
        if not stripped:
            return None

        # Clinical moment (standalone marker)
        if _CLINICAL_MOMENT.search(stripped):
            return HeadingMatch(
                node_type="clinical_moment",
                ordinal_label="",
                heading_text="Clinical Moment",
                depth=4,
            )

        # References / suggested readings
        if _REFERENCES.match(stripped):
            return HeadingMatch(
                node_type="reference",
                ordinal_label="",
                heading_text=stripped.title(),
                depth=2,
            )

        # Chapter heading
        m = _CHAPTER.match(stripped)
        if m:
            return HeadingMatch(
                node_type="chapter",
                ordinal_label=m.group(1),
                heading_text=m.group(2).strip() or f"Chapter {m.group(1)}",
                depth=1,
            )

        # Roman-numeral section
        m = _ROMAN_SECTION.match(stripped)
        if m:
            return HeadingMatch(
                node_type="section",
                ordinal_label=m.group(1),
                heading_text=m.group(2).strip(),
                depth=2,
            )

        # Letter subsection
        m = _LETTER_SUBSECTION.match(stripped)
        if m:
            return HeadingMatch(
                node_type="subsection",
                ordinal_label=m.group(1),
                heading_text=m.group(2).strip(),
                depth=3,
            )

        # Numbered item
        m = _NUMBERED_ITEM.match(stripped)
        if m:
            return HeadingMatch(
                node_type="item",
                ordinal_label=m.group(1),
                heading_text=m.group(2).strip(),
                depth=4,
            )

        # Fall through to general patterns
        return super().detect_heading(line)


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def get_detector(preset: str = "general") -> HeadingDetector:
    """Return a HeadingDetector by preset name."""
    detectors = {
        "general": GeneralDetector,
        "medical": MedicalTextbookDetector,
    }
    cls = detectors.get(preset)
    if cls is None:
        raise ValueError(f"Unknown detector preset: {preset!r}. Choose from {list(detectors)}")
    return cls()


# ---------------------------------------------------------------------------
# Tree builder
# ---------------------------------------------------------------------------

def build_hierarchy(
    page_texts: list[str],
    document_id: str,
    detector: HeadingDetector,
) -> list[NodeData]:
    """Scan page texts line-by-line and return a flat list of NodeData.

    The returned list is ordered depth-first.  Parent–child relationships
    are expressed via ``parent_id``.
    """
    root = NodeData(
        document_id=document_id,
        node_type="root",
        heading_text="Document Root",
        heading_path="",
        depth=0,
    )

    # Stack tracks the current nesting: stack[-1] is the active parent.
    stack: list[NodeData] = [root]
    all_nodes: list[NodeData] = [root]

    current_lines: list[str] = []
    current_page: int = 0

    def _flush_text(target: NodeData) -> None:
        """Append accumulated lines to the target node."""
        if current_lines:
            text = "\n".join(current_lines)
            target.raw_text += ("\n" if target.raw_text else "") + text
            target.token_count = count_tokens(target.raw_text)
            current_lines.clear()

    for page_idx, page_text in enumerate(page_texts):
        for line in page_text.splitlines():
            match = detector.detect_heading(line)

            if match is None:
                current_lines.append(line)
                continue

            # Flush accumulated text to the current deepest node
            _flush_text(stack[-1])

            # Pop stack until we find a parent at a shallower depth
            while len(stack) > 1 and stack[-1].depth >= match.depth:
                stack.pop()

            parent = stack[-1]

            # Build heading path
            parent_path = parent.heading_path
            label = match.ordinal_label
            heading = match.heading_text
            path_segment = f"{label}. {heading}" if label else heading
            heading_path = f"{parent_path} > {path_segment}" if parent_path else path_segment

            node = NodeData(
                document_id=document_id,
                parent_id=parent.id,
                node_type=match.node_type,
                ordinal_label=match.ordinal_label,
                heading_text=match.heading_text,
                heading_path=heading_path,
                depth=match.depth,
                page_start=page_idx + 1,   # 1-indexed
                child_index=len(parent.children),
            )

            parent.children.append(node)
            stack.append(node)
            all_nodes.append(node)
            current_page = page_idx

    # Flush any remaining text
    _flush_text(stack[-1])

    # Back-fill page_end: each node ends where the next sibling (or parent's
    # next sibling) starts, or at the last page.
    last_page = len(page_texts)
    for node in reversed(all_nodes):
        if node.page_end is None:
            node.page_end = last_page
        if node.page_start is None:
            node.page_start = 1

    return all_nodes
