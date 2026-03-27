"""Unit tests for rag.text_preprocessing."""

from rag.text_preprocessing import (
    remove_headers_footers,
    remove_page_numbers,
    fix_hyphenation,
    merge_wrapped_lines,
    clean_text,
    clean_pages,
    count_tokens,
    _sanitize_control_chars,
)


# ── remove_headers_footers ────────────────────────────────────

def test_remove_headers_footers_strips_repeating_lines():
    pages = [
        "HEADER LINE\nContent page 1\nFOOTER LINE",
        "HEADER LINE\nContent page 2\nFOOTER LINE",
        "HEADER LINE\nContent page 3\nFOOTER LINE",
    ]
    result = remove_headers_footers(pages, threshold=0.5)
    for page in result:
        assert "HEADER LINE" not in page
        assert "FOOTER LINE" not in page
        assert "Content page" in page


def test_remove_headers_footers_keeps_non_repeating():
    pages = [
        "Unique header\nContent 1\nUnique footer",
        "Different header\nContent 2\nDifferent footer",
        "Another header\nContent 3\nAnother footer",
    ]
    result = remove_headers_footers(pages, threshold=0.5)
    # None of the headers/footers repeat enough to be stripped
    assert "Unique header" in result[0]


def test_remove_headers_footers_needs_min_pages():
    pages = ["Page1\nBody", "Page2\nBody"]
    result = remove_headers_footers(pages)
    assert result == pages  # < 3 pages, returns as-is


# ── remove_page_numbers ───────────────────────────────────────

def test_remove_page_numbers():
    text = "Some text\n  42  \nMore text\n1234\nEnd"
    result = remove_page_numbers(text)
    assert "42" not in result
    assert "1234" not in result
    assert "Some text" in result
    assert "More text" in result


def test_remove_page_numbers_keeps_inline_numbers():
    text = "Chapter 42 is about testing"
    result = remove_page_numbers(text)
    assert result == text  # inline numbers are not removed


# ── fix_hyphenation ───────────────────────────────────────────

def test_fix_hyphenation_rejoins_split_words():
    text = "anes-\nthesia is impor-\ntant"
    result = fix_hyphenation(text)
    assert "anesthesia" in result
    assert "important" in result


def test_fix_hyphenation_keeps_normal_hyphens():
    text = "well-known fact\npre-existing condition"
    result = fix_hyphenation(text)
    assert "well-known" in result  # no newline after hyphen


# ── merge_wrapped_lines ───────────────────────────────────────

def test_merge_wrapped_lines_joins_mid_sentence():
    text = "This is a sentence that\ncontinues on the next line"
    result = merge_wrapped_lines(text)
    assert "that continues" in result


def test_merge_wrapped_lines_preserves_sentence_endings():
    text = "End of sentence.\nStart of new sentence"
    result = merge_wrapped_lines(text)
    assert ".\n" in result or ".\nStart" in result


def test_merge_wrapped_lines_preserves_uppercase_starts():
    text = "End of paragraph\nNew Paragraph starts here"
    result = merge_wrapped_lines(text)
    # Uppercase start means new paragraph, should NOT merge
    assert "\n" in result


# ── _sanitize_control_chars ───────────────────────────────────

def test_sanitize_removes_nul():
    text = "hello\x00world"
    assert _sanitize_control_chars(text) == "helloworld"


def test_sanitize_removes_control_chars():
    text = "hello\x01\x02\x03world"
    result = _sanitize_control_chars(text)
    assert "\x01" not in result
    assert "hello" in result
    assert "world" in result


def test_sanitize_preserves_normal_whitespace():
    text = "hello\n\tworld\r\n"
    result = _sanitize_control_chars(text)
    assert "\n" in result
    assert "\t" in result


# ── clean_text (orchestrator) ─────────────────────────────────

def test_clean_text_applies_all_steps():
    text = "anes-\nthesia\n  123  \nhello\x00world"
    result = clean_text(text)
    assert "anesthesia" in result
    assert "123" not in result  # page number removed
    assert "\x00" not in result


def test_clean_text_strips_whitespace():
    result = clean_text("  some text  ")
    assert result == "some text"


# ── clean_pages ───────────────────────────────────────────────

def test_clean_pages_removes_headers_and_cleans():
    pages = [
        "HEADER\nContent with anes-\nthesia\nFOOTER",
        "HEADER\nMore content\nFOOTER",
        "HEADER\nFinal content\nFOOTER",
    ]
    result = clean_pages(pages)
    assert len(result) == 3
    for page in result:
        assert "HEADER" not in page
        assert "FOOTER" not in page
    assert "anesthesia" in result[0]


# ── count_tokens ──────────────────────────────────────────────

def test_count_tokens_returns_int():
    result = count_tokens("Hello world, this is a test")
    assert isinstance(result, int)
    assert result > 0


def test_count_tokens_empty_string():
    assert count_tokens("") == 0


def test_count_tokens_longer_text_has_more_tokens():
    short = count_tokens("hello")
    long = count_tokens("hello world this is a longer sentence with more tokens")
    assert long > short
