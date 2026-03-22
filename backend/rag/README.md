# RAG Pipeline

Hierarchy-aware document ingestion, chunking, embedding, and search
using PostgreSQL + pgvector.

## Quick start

From the `backend/` directory:

```bash
# Ingest a PDF
python rag/ragtool.py upload ~/path/to/book.pdf \
  --title "My Textbook" \
  --user-id SYSTEM \
  --detector general

# Search
python rag/ragtool.py search "query text" --user-id SYSTEM --top-k 5

# Inspect a chunk
python rag/ragtool.py show-chunk <chunk-uuid>

# View ingestion status
python rag/ragtool.py status

# Re-run pipeline for a document
python rag/ragtool.py reprocess <document-uuid> --detector medical
```

## Detector presets

| Preset    | Use for                                      |
|-----------|----------------------------------------------|
| `general` | Generic PDFs, CS/math textbooks, markdown    |
| `medical` | Anesthesia/medical textbooks (roman numerals, CLINICAL MOMENT, references) |

## File overview

| File                   | Purpose                                      |
|------------------------|----------------------------------------------|
| `models.py`            | SQLAlchemy models (RagDocument, RagNode, RagChunk, IngestionRun) |
| `extraction.py`        | PDF/DOCX/TXT text extraction                 |
| `text_preprocessing.py`| Text cleaning (headers, hyphenation, tokens) |
| `embedder.py`          | Embedder protocol + Local/OpenAI implementations |
| `hierarchy_builder.py` | Heading detection + document tree building   |
| `chunker.py`           | Hierarchy-aware chunk splitting/merging      |
| `pipeline.py`          | End-to-end ingestion + pgvector search       |
| `ragtool.py`           | CLI entry point                              |

## Environment variables

| Variable          | Default                  | Description              |
|-------------------|--------------------------|--------------------------|
| `DATABASE_URL`    | (required)               | PostgreSQL connection    |
| `EMBEDDING_MODEL` | `BAAI/bge-small-en-v1.5` | sentence-transformers model or `text-embedding-*` for OpenAI |
| `EMBEDDING_DIM`   | `384`                    | Vector dimension (must match model) |
