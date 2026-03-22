# RAG Chunking and Embedding Architecture

## Overview

Hierarchy-aware RAG pipeline that parses documents, detects structure,
produces semantically coherent chunks, generates embeddings locally, and
stores everything in PostgreSQL with pgvector for native similarity search.

The system runs **alongside** the existing `materials` / `vector_index_entries`
tables without breaking current functionality.

---

## Entity Relationships

A **RagDocument** is the RAG representation of an uploaded file. It links
back to a `materials` row (which owns the file and the `user_id`). When a
document is ingested the pipeline parses its structure into a tree of
**RagNodes** — each node is a structural element like a chapter, section,
subsection, or clinical moment. The leaf text of those nodes is then split
(and merged where appropriate) into **RagChunks**, which are the units of
retrieval. Each chunk carries its own pgvector embedding and a
`heading_path` breadcrumb so search results always show where the chunk
lives in the document. Chunks are also linked into a doubly-linked list
(`prev_chunk_id` / `next_chunk_id`) for easy context expansion.
**IngestionRuns** log each pipeline stage for observability.

```
  materials          rag_documents        rag_nodes
  +------------+     +---------------+    +-------------+
  | id (PK)    |<-+  | id (PK, UUID) |<-+ | id (PK)     |
  | user_id    |  +--| material_id   |  +-| document_id |
  | file_path  |     | title         |  | | parent_id --+--> self (tree)
  | file_type  |     | checksum      |  | | node_type   |
  +------------+     | status        |  | | heading_path|
                      | page_count    |  | | depth       |
       1:N            +-------+-------+  | +-------------+
                              |          |
              +---------------+-----+    |
              |               |     |    |
              v               v     v    |
        rag_chunks    ingestion_runs |   |
        +-------------+ +-----------+|   |
        | id (PK)     | | id (PK)   ||   |
        | document_id | | doc_id    ||   |
        | node_id ----+-+           ||   |
        | chunk_index | | stage     |+---+
        | content     | | status    |
        | embedding   | | message   |
        | heading_path| +-----------+
        | prev/next_id|
        +-------------+
```

---

## Scope

**In scope:**

- PDF/DOCX/TXT parsing with per-page text extraction
- Hierarchy detection (pluggable: general + medical-textbook presets)
- Hierarchy-aware chunking with semantic coherence
- Local embeddings (BGE via sentence-transformers) with pluggable interface
- pgvector storage and native cosine-distance search
- CLI tools for upload, search, and inspection
- Per-stage ingestion tracking via `ingestion_runs`

**Out of scope (future work):**

- Question generation
- Reranking / advanced retrieval strategies
- Frontend API endpoints for ingestion
- Migration of existing `vector_index_entries` data
- Deprecation of old JSON-embedding search path

---

## High-Level Architecture

```
 PDF file
   |
   v
 1. PDF Parser (PyPDF2)
   |  extract per-page text
   v
 2. Text Preprocessor
   |  remove headers/footers, fix hyphenation,
   |  merge wrapped lines, remove page numbers
   v
 3. Hierarchy Builder (pluggable HeadingDetector)
   |  detect chapters, sections, subsections, items,
   |  clinical moments, references
   |  build parent-child tree of RagNode objects
   v
 4. Chunker
   |  traverse tree, apply chunk size policy,
   |  split/merge respecting hierarchy boundaries,
   |  format content_for_embedding with heading context
   v
 5. Embedder (pluggable: LocalEmbedder / OpenAIEmbedder)
   |  batch-embed chunk texts into vectors
   v
 6. PostgreSQL + pgvector
      store hierarchy + chunks + embeddings
      cosine-distance search via <=> operator
```

---

## Chunking Strategy

### Hard Boundaries

Always split on:
- New chapter
- New roman numeral section (I., II., III.)
- New letter subsection (A., B., C.)
- Numbered items (1., 2., 3.) when large
- `CLINICAL MOMENT`
- `REFERENCE`, `SUGGESTED READINGS` (excluded from embedding)

### Chunk Size Policy

| Parameter   | Value       |
|-------------|-------------|
| Target min  | 250 tokens  |
| Target max  | 600 tokens  |
| Soft max    | 800 tokens  |
| Hard max    | 1000 tokens |
| Overlap     | 60 tokens (same parent only) |

### Merge Rules

- Merge only if: same parent node, same semantic type, both chunks are small
- Never merge across section boundaries
- Never merge clinical moments into other chunks

### Split Rules

If too large:
1. Split by paragraph boundaries
2. Split by sentence windows (last resort)

### Special Handling

- `CLINICAL MOMENT` = standalone chunk (chunk_kind = "clinical_moment")
- References = excluded from embedding search entirely

---

## Text Preprocessing

Applied via `services/text_preprocessing.py`:

1. Remove repeating headers/footers (cross-page frequency analysis)
2. Remove standalone page numbers
3. Fix hyphenation (rejoin hyphenated line breaks)
4. Merge wrapped lines (lowercase continuation)
5. Sanitize control characters for PostgreSQL

---

## Database Schema

### rag_documents

```sql
create table rag_documents (
  id              uuid primary key default gen_random_uuid(),
  material_id     int not null references materials(id) on delete cascade,
  title           text not null,
  source_path     text not null,
  checksum_sha256 varchar(64) not null unique,
  page_count      int,
  status          varchar(30) not null default 'uploaded',
  created_at      timestamptz default now()
);
```

### rag_nodes (Hierarchy Tree)

```sql
create table rag_nodes (
  id            uuid primary key default gen_random_uuid(),
  document_id   uuid not null references rag_documents(id) on delete cascade,
  parent_id     uuid references rag_nodes(id) on delete cascade,
  node_type     varchar(30) not null,
  ordinal_label text,
  heading_text  text,
  heading_path  text not null,
  depth         int not null,
  page_start    int,
  page_end      int,
  raw_text      text,
  cleaned_text  text,
  token_count   int,
  child_index   int not null default 0,
  created_at    timestamptz default now()
);
create index ix_rag_nodes_document_id on rag_nodes(document_id);
```

### rag_chunks

```sql
create extension if not exists vector;

create table rag_chunks (
  id                    uuid primary key default gen_random_uuid(),
  document_id           uuid not null references rag_documents(id) on delete cascade,
  node_id               uuid not null references rag_nodes(id) on delete cascade,
  chunk_index           int not null,
  chunk_kind            varchar(30) not null,
  heading_path          text not null,
  page_start            int,
  page_end              int,
  token_count           int not null,
  content               text not null,
  content_for_embedding text not null,
  embedding             vector,
  embedding_model       text not null,
  prev_chunk_id         uuid references rag_chunks(id),
  next_chunk_id         uuid references rag_chunks(id),
  created_at            timestamptz default now()
);
create index ix_rag_chunks_document_id on rag_chunks(document_id);
create index ix_rag_chunks_node_id on rag_chunks(node_id);
```

### ingestion_runs

```sql
create table ingestion_runs (
  id          uuid primary key default gen_random_uuid(),
  document_id uuid not null references rag_documents(id) on delete cascade,
  stage       varchar(50) not null,
  status      varchar(20) not null,
  message     text,
  created_at  timestamptz default now(),
  finished_at timestamptz
);
```

---

## Embedding Strategy

### Interface (services/embedder.py)

```python
class Embedder(Protocol):
    model_name: str
    dimension: int
    def embed_texts(self, texts: list[str]) -> list[list[float]]: ...
    def embed_query(self, text: str) -> list[float]: ...
```

### Implementations

| Class          | Model                     | Dimensions | Source         |
|----------------|---------------------------|------------|----------------|
| LocalEmbedder  | BAAI/bge-small-en-v1.5    | 384        | sentence-transformers |
| LocalEmbedder  | BAAI/bge-base-en-v1.5     | 768        | sentence-transformers |
| OpenAIEmbedder | text-embedding-3-small    | 1536       | OpenAI API (stub) |

Default: `BAAI/bge-small-en-v1.5` (configurable via `EMBEDDING_MODEL` env var).

Factory: `get_embedder(model_name)` — names starting with `text-embedding-`
route to OpenAI; everything else to sentence-transformers.

### Embedding Input Format

```
Title: <book title>
Path: <Chapter 1 > Section I > Subsection A>
Type: <clinical_moment>  (only for clinical moments)

<chunk content>
```

---

## Heading Detection (services/hierarchy_builder.py)

### GeneralDetector

- Markdown headings: `# Title`, `## Section`, `### Subsection`
- Numbered headings: `1. Title`, `1.1. Title`
- ALL-CAPS lines (5+ characters)

### MedicalTextbookDetector (extends GeneralDetector)

Priority order (checked first to last):

1. `CLINICAL MOMENT` markers
2. `REFERENCES` / `SUGGESTED READINGS`
3. Chapter headings: `Chapter 1:`, `CHAPTER IV.`
4. Roman numeral sections: `I.`, `II.`, `III.`
5. Letter subsections: `A.`, `B.`, `C.`
6. Numbered items: `1.`, `2.`, `3.`
7. General patterns (fallthrough)

Factory: `get_detector("general" | "medical")`

---

## Ingestion Pipeline (services/rag_pipeline.py)

### Stages

| # | Stage      | Persists              | Status set on doc    |
|---|------------|-----------------------|----------------------|
| 1 | Extract    | (reads file)          | extracting           |
| 2 | Preprocess | (in-memory cleaning)  | building_hierarchy   |
| 3 | Hierarchy  | rag_nodes             | building_hierarchy   |
| 4 | Chunk      | rag_chunks (no embed) | chunking             |
| 5 | Embed      | rag_chunks.embedding  | embedding -> ready   |

Each stage logs a row to `ingestion_runs` with timing.
On failure: status = "failed", error logged to ingestion_runs.

### Entry point

```python
ingest_document(material_id, db, embedder, detector) -> RagDocument
```

Requires an existing `materials` row. Ownership derived via `materials.user_id`.

---

## CLI Tool (cli/ragtool.py)

Run from `backend/`:

```bash
# Ingest a PDF (creates material + runs pipeline)
python -m cli.ragtool upload book.pdf \
  --title "Nurse Anesthesia" \
  --user-id SYSTEM \
  --detector medical

# Search
python -m cli.ragtool search "malignant hyperthermia" \
  --user-id SYSTEM \
  --top-k 5

# Inspect a chunk
python -m cli.ragtool show-chunk <chunk-uuid>

# View ingestion status
python -m cli.ragtool status

# Re-run pipeline for a document
python -m cli.ragtool reprocess <document-uuid> --detector medical
```

---

## Retrieval Query

```sql
select c.id, c.heading_path, c.content,
       1 - (c.embedding <=> :query_vec) as score
from rag_chunks c
join rag_documents d on c.document_id = d.id
join materials m on d.material_id = m.id
where m.user_id in (:user_id, 'SYSTEM')
  and c.embedding is not null
order by c.embedding <=> :query_vec
limit :top_k;
```

---

## File Map

```
backend/
  models/
    __init__.py                 # registers RAG models on Base.metadata
    rag.py                      # RagDocument, RagNode, RagChunk, IngestionRun

  services/
    __init__.py
    embedder.py                 # Embedder protocol, LocalEmbedder, OpenAIEmbedder
    text_preprocessing.py       # clean_pages(), count_tokens()
    hierarchy_builder.py        # GeneralDetector, MedicalTextbookDetector, build_hierarchy()
    chunker.py                  # chunk_document(), split/merge helpers
    rag_pipeline.py             # ingest_document(), search_chunks(), get_chunk_with_context()

  cli/
    __init__.py
    ragtool.py                  # click CLI: upload, search, show-chunk, status, reprocess

  utils/
    rag.py                      # extract_pages_from_pdf() (+ existing functions)

  alembic/versions/
    e2f3a4b5c6d7_add_rag_tables_and_pgvector.py
```

---

## Dependencies

| Package              | Version | Purpose                          |
|----------------------|---------|----------------------------------|
| pgvector             | 0.3.6   | SQLAlchemy pgvector integration  |
| sentence-transformers| 4.1.0   | Local BGE embeddings             |
| tiktoken             | 0.9.0   | Accurate token counting          |
| PyPDF2               | 3.0.1   | PDF text extraction (existing)   |
| python-docx          | 1.1.0   | DOCX text extraction (existing)  |
| click                | 8.3.0   | CLI framework (existing)         |

---

## What to Avoid

- Fixed-size chunking without hierarchy awareness
- Chunking by page boundaries
- Storing only embeddings without text
- Adding an external vector DB (pgvector is sufficient)
- Duplicating user_id on rag_documents (derive from materials FK)

---

## Future Work

- Wire `search_chunks()` into `routers/chat.py` for frontend RAG
- Add API endpoint `POST /api/materials/{id}/ingest` for frontend-triggered ingestion
- Migrate existing `vector_index_entries` data to `rag_chunks`
- Deprecate old JSON-embedding search path
- HNSW index on `rag_chunks.embedding` (add after initial data population)
- Reranking, question generation, advanced retrieval strategies
