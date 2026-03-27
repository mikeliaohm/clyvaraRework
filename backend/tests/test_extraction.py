"""Unit tests for rag.extraction — markdown conversion and font analysis."""

import pytest
from unittest.mock import MagicMock, patch
from rag.extraction import _compute_body_font_size, _sanitize_text


# ── _sanitize_text ────────────────────────────────────────────

def test_sanitize_text_removes_null_bytes():
    assert _sanitize_text("hello\x00world") == "helloworld"


def test_sanitize_text_removes_control_chars():
    result = _sanitize_text("test\x01\x02\x03value")
    assert "\x01" not in result
    assert "test" in result
    assert "value" in result


def test_sanitize_text_preserves_newlines_tabs():
    text = "line1\nline2\ttab"
    assert "\n" in _sanitize_text(text)
    assert "\t" in _sanitize_text(text)


# ── _compute_body_font_size ───────────────────────────────────

def _make_mock_doc(page_spans_list):
    """Create a mock fitz.Document with given spans per page.

    page_spans_list: list of lists of dicts with 'text' and 'size'
    """
    doc = MagicMock()
    pages = []
    for page_spans in page_spans_list:
        page = MagicMock()
        blocks = [{
            "type": 0,
            "lines": [{
                "spans": [{"text": s["text"], "size": s["size"], "font": "Arial", "flags": 0}
                          for s in page_spans]
            }]
        }]
        page.get_text.return_value = {"blocks": blocks}
        pages.append(page)
    doc.__iter__ = lambda self: iter(pages)
    return doc


def test_compute_body_font_size_returns_mode():
    doc = _make_mock_doc([
        [
            {"text": "Body text here", "size": 12.0},
            {"text": "More body text", "size": 12.0},
            {"text": "Heading", "size": 18.0},
        ],
    ])
    result = _compute_body_font_size(doc)
    assert result == 12.0  # mode is 12.0


def test_compute_body_font_size_empty_doc():
    doc = _make_mock_doc([])
    result = _compute_body_font_size(doc)
    assert result == 12.0  # default fallback


def test_compute_body_font_size_skips_short_text():
    doc = _make_mock_doc([
        [
            {"text": "ab", "size": 6.0},  # too short, skipped
            {"text": "Normal paragraph text", "size": 11.0},
            {"text": "Another normal line", "size": 11.0},
        ],
    ])
    result = _compute_body_font_size(doc)
    assert result == 11.0


def test_compute_body_font_size_multiple_pages():
    doc = _make_mock_doc([
        [{"text": "Page 1 text", "size": 10.0}],
        [{"text": "Page 2 text", "size": 10.0}],
        [{"text": "Page 3 heading", "size": 14.0}],
    ])
    result = _compute_body_font_size(doc)
    assert result == 10.0  # mode is 10.0
