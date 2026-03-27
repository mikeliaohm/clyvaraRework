"""Unit tests for rag.hierarchy_builder."""

from rag.hierarchy_builder import (
    GeneralDetector,
    MedicalTextbookDetector,
    build_hierarchy,
    NodeData,
)


# ── GeneralDetector ───────────────────────────────────────────

class TestGeneralDetector:
    detector = GeneralDetector()

    def test_markdown_h1(self):
        match = self.detector.detect_heading("# Introduction")
        assert match is not None
        assert match.node_type == "chapter"
        assert match.heading_text == "Introduction"

    def test_markdown_h2(self):
        match = self.detector.detect_heading("## Methods")
        assert match is not None
        assert match.node_type == "section"

    def test_markdown_h3(self):
        match = self.detector.detect_heading("### Sub-method")
        assert match is not None
        assert match.node_type == "subsection"

    def test_numbered_heading(self):
        match = self.detector.detect_heading("1. Introduction to Anesthesia")
        assert match is not None
        assert match.ordinal_label == "1"
        assert "Introduction" in match.heading_text

    def test_numbered_heading_nested(self):
        match = self.detector.detect_heading("1.2. Subsection Title")
        assert match is not None
        assert match.ordinal_label == "1.2"

    def test_all_caps_heading(self):
        match = self.detector.detect_heading("INTRODUCTION")
        assert match is not None
        assert match.node_type == "section"
        assert "introduction" in match.heading_text.lower()

    def test_all_caps_too_short(self):
        match = self.detector.detect_heading("HI")
        assert match is None  # less than 5 chars

    def test_regular_text_no_match(self):
        match = self.detector.detect_heading("This is just regular body text.")
        assert match is None

    def test_empty_line_no_match(self):
        match = self.detector.detect_heading("")
        assert match is None


# ── MedicalTextbookDetector ───────────────────────────────────

class TestMedicalTextbookDetector:
    detector = MedicalTextbookDetector()

    def test_clinical_moment(self):
        match = self.detector.detect_heading("CLINICAL MOMENT: Pain Management")
        assert match is not None
        assert match.node_type == "clinical_moment"

    def test_references_section(self):
        match = self.detector.detect_heading("REFERENCES")
        assert match is not None
        assert match.node_type == "reference"

    def test_suggested_readings(self):
        match = self.detector.detect_heading("SUGGESTED READINGS")
        assert match is not None
        assert match.node_type == "reference"

    def test_chapter_heading(self):
        match = self.detector.detect_heading("CHAPTER 3: Pharmacology")
        assert match is not None
        assert match.node_type == "chapter"
        assert "3" in match.ordinal_label

    def test_roman_numeral_section(self):
        match = self.detector.detect_heading("II. Cardiovascular System")
        assert match is not None
        assert match.ordinal_label == "II"

    def test_letter_subsection(self):
        match = self.detector.detect_heading("A. First Point")
        assert match is not None
        assert match.ordinal_label == "A"

    def test_falls_through_to_general(self):
        match = self.detector.detect_heading("# Overview")
        assert match is not None
        assert match.node_type == "chapter"

    def test_regular_text_no_match(self):
        match = self.detector.detect_heading("The patient presented with symptoms.")
        assert match is None


# ── build_hierarchy ───────────────────────────────────────────

class TestBuildHierarchy:
    detector = GeneralDetector()

    def test_simple_hierarchy(self):
        pages = [
            "# Chapter 1\nSome intro text\n## Section A\nSection text\n## Section B\nMore text"
        ]
        nodes = build_hierarchy(pages, "doc-1", self.detector)

        assert len(nodes) >= 4  # root + chapter + 2 sections
        root = nodes[0]
        assert root.node_type == "root"

        chapter = [n for n in nodes if n.node_type == "chapter"]
        assert len(chapter) == 1
        assert "Chapter 1" in chapter[0].heading_text

        sections = [n for n in nodes if n.node_type == "section"]
        assert len(sections) == 2

    def test_root_captures_text_without_headings(self):
        pages = ["Just plain text\nwith no headings at all"]
        nodes = build_hierarchy(pages, "doc-2", self.detector)

        assert len(nodes) == 1
        root = nodes[0]
        assert root.node_type == "root"
        assert "Just plain text" in root.raw_text

    def test_text_accumulates_on_nodes(self):
        pages = ["# Heading\nBody line 1\nBody line 2"]
        nodes = build_hierarchy(pages, "doc-3", self.detector)

        heading_node = [n for n in nodes if n.node_type == "chapter"][0]
        assert "Body line 1" in heading_node.raw_text
        assert "Body line 2" in heading_node.raw_text

    def test_parent_child_relationships(self):
        pages = ["# Parent\n## Child\nText"]
        nodes = build_hierarchy(pages, "doc-4", self.detector)

        parent = [n for n in nodes if n.heading_text == "Parent"][0]
        child = [n for n in nodes if n.heading_text == "Child"][0]
        assert child.parent_id == parent.id

    def test_heading_path_built_correctly(self):
        pages = ["# Chapter\n## Section\nText"]
        nodes = build_hierarchy(pages, "doc-5", self.detector)

        section = [n for n in nodes if n.heading_text == "Section"][0]
        assert "Chapter" in section.heading_path
        assert "Section" in section.heading_path

    def test_page_numbers_assigned(self):
        pages = [
            "# Page One Content",
            "## Page Two Content",
        ]
        nodes = build_hierarchy(pages, "doc-6", self.detector)

        # All nodes should have page_start and page_end
        for node in nodes:
            assert node.page_start is not None
            assert node.page_end is not None

    def test_markdown_parallel_accumulation(self):
        pages = ["# Heading\nPlain body text"]
        markdowns = ["# **Heading**\n**Bold** body text"]
        nodes = build_hierarchy(pages, "doc-7", self.detector, page_markdowns=markdowns)

        heading_node = [n for n in nodes if n.node_type == "chapter"][0]
        assert heading_node.raw_text  # plain text accumulated
        assert heading_node.raw_markdown  # markdown accumulated
        assert "**Bold**" in heading_node.raw_markdown or "Bold" in heading_node.raw_markdown

    def test_no_markdown_when_not_provided(self):
        pages = ["# Heading\nText"]
        nodes = build_hierarchy(pages, "doc-8", self.detector)

        for node in nodes:
            assert node.raw_markdown == ""

    def test_multi_page_document(self):
        pages = [
            "# Chapter 1\nContent on page 1",
            "## Section 1.1\nContent on page 2",
            "# Chapter 2\nContent on page 3",
        ]
        nodes = build_hierarchy(pages, "doc-9", self.detector)

        chapters = [n for n in nodes if n.node_type == "chapter"]
        assert len(chapters) == 2
        sections = [n for n in nodes if n.node_type == "section"]
        assert len(sections) == 1
