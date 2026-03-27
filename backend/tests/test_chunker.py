"""Unit tests for rag.chunker."""

from rag.chunker import (
    split_if_needed,
    merge_small_chunks,
    build_embedding_input,
    ChunkData,
    _split_by_paragraphs,
    _split_by_sentences,
    HARD_MAX,
    TARGET_MAX,
    TARGET_MIN,
)
from rag.text_preprocessing import count_tokens


# ── _split_by_paragraphs ─────────────────────────────────────

def test_split_by_paragraphs_on_blank_lines():
    text = "Para one\n\nPara two\n\nPara three"
    result = _split_by_paragraphs(text)
    assert len(result) == 3
    assert result[0] == "Para one"
    assert result[1] == "Para two"


def test_split_by_paragraphs_strips_empty():
    text = "\n\n\nOnly content\n\n\n"
    result = _split_by_paragraphs(text)
    assert len(result) == 1
    assert result[0] == "Only content"


# ── _split_by_sentences ───────────────────────────────────────

def test_split_by_sentences():
    text = "First sentence. Second sentence! Third sentence?"
    result = _split_by_sentences(text)
    assert len(result) == 3
    assert "First sentence." in result[0]


# ── split_if_needed ───────────────────────────────────────────

def test_split_if_needed_short_text_no_split():
    text = "This is a short text."
    result = split_if_needed(text)
    assert len(result) == 1
    assert result[0] == text


def test_split_if_needed_long_text_splits():
    # Create text with paragraphs that exceed HARD_MAX tokens
    paras = [" ".join(["word"] * 400) for _ in range(5)]
    text = "\n\n".join(paras)
    result = split_if_needed(text)
    assert len(result) > 1
    for piece in result:
        assert count_tokens(piece) <= HARD_MAX + 50  # small tolerance


def test_split_if_needed_respects_paragraph_boundaries():
    para1 = " ".join(["alpha"] * 400)
    para2 = " ".join(["beta"] * 400)
    para3 = " ".join(["gamma"] * 400)
    text = f"{para1}\n\n{para2}\n\n{para3}"
    result = split_if_needed(text)
    assert len(result) >= 2
    # Each piece should contain whole paragraphs (not mid-word splits)
    assert "alpha" in result[0]


# ── merge_small_chunks ────────────────────────────────────────

def test_merge_small_chunks_merges_adjacent():
    c1 = ChunkData(node_id="n1", chunk_kind="semantic", content="Hello", content_display="Hello", token_count=1)
    c2 = ChunkData(node_id="n1", chunk_kind="semantic", content="World", content_display="World", token_count=1)
    result = merge_small_chunks([c1, c2], min_tokens=10, max_merged=100)
    assert len(result) == 1
    assert "Hello" in result[0].content
    assert "World" in result[0].content


def test_merge_small_chunks_different_nodes_no_merge():
    c1 = ChunkData(node_id="n1", chunk_kind="semantic", content="Hello", content_display="Hello", token_count=1)
    c2 = ChunkData(node_id="n2", chunk_kind="semantic", content="World", content_display="World", token_count=1)
    result = merge_small_chunks([c1, c2], min_tokens=10, max_merged=100)
    assert len(result) == 2


def test_merge_small_chunks_preserves_clinical_moments():
    c1 = ChunkData(node_id="n1", chunk_kind="clinical_moment", content="Case", content_display="Case", token_count=1)
    c2 = ChunkData(node_id="n1", chunk_kind="semantic", content="Text", content_display="Text", token_count=1)
    result = merge_small_chunks([c1, c2], min_tokens=10, max_merged=100)
    assert len(result) == 2  # clinical_moment never merges


def test_merge_small_chunks_respects_max_size():
    c1 = ChunkData(node_id="n1", chunk_kind="semantic", content="A", content_display="A", token_count=500)
    c2 = ChunkData(node_id="n1", chunk_kind="semantic", content="B", content_display="B", token_count=500)
    result = merge_small_chunks([c1, c2], min_tokens=10, max_merged=600)
    assert len(result) == 2  # 500+500 > 600, won't merge


def test_merge_small_chunks_empty_list():
    assert merge_small_chunks([]) == []


# ── build_embedding_input ─────────────────────────────────────

def test_build_embedding_input_includes_title():
    chunk = ChunkData(heading_path="Ch1 > Sec A", content="Body text")
    result = build_embedding_input(chunk, title="My Document")
    assert "Title: My Document" in result
    assert "Path: Ch1 > Sec A" in result
    assert "Body text" in result


def test_build_embedding_input_no_title():
    chunk = ChunkData(heading_path="Section", content="Content")
    result = build_embedding_input(chunk)
    assert "Title:" not in result
    assert "Path: Section" in result
    assert "Content" in result


def test_build_embedding_input_clinical_moment():
    chunk = ChunkData(
        heading_path="Path",
        content="Clinical case",
        chunk_kind="clinical_moment",
    )
    result = build_embedding_input(chunk, title="Doc")
    assert "Type: clinical_moment" in result
