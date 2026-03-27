"""SQLAlchemy models for the RAG pipeline.

Tables: rag_documents, rag_nodes, rag_chunks, ingestion_runs.
These sit alongside the existing materials / vector_index_entries tables.
"""

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, Index,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from database import Base


# ---------------------------------------------------------------------------
# RagDocument — one processed document, linked to a materials row
# ---------------------------------------------------------------------------

class RagDocument(Base):
    __tablename__ = "rag_documents"

    id = Column(UUID, primary_key=True, server_default=text("gen_random_uuid()"))
    material_id = Column(Integer, ForeignKey("materials.id", ondelete="CASCADE"), nullable=False)

    title = Column(String, nullable=False)
    source_path = Column(String, nullable=False)
    checksum_sha256 = Column(String(64), nullable=False, unique=True)

    page_count = Column(Integer)
    status = Column(
        String(30), nullable=False, default="uploaded",
        server_default=text("'uploaded'"),
    )

    created_at = Column(DateTime, server_default=func.now())


# ---------------------------------------------------------------------------
# RagNode — hierarchy tree (chapter → section → subsection → …)
# ---------------------------------------------------------------------------

class RagNode(Base):
    __tablename__ = "rag_nodes"

    id = Column(UUID, primary_key=True, server_default=text("gen_random_uuid()"))
    document_id = Column(
        UUID, ForeignKey("rag_documents.id", ondelete="CASCADE"), nullable=False,
    )
    parent_id = Column(UUID, ForeignKey("rag_nodes.id", ondelete="CASCADE"))

    node_type = Column(String(30), nullable=False)
    ordinal_label = Column(String)
    heading_text = Column(String)
    heading_path = Column(String, nullable=False)

    depth = Column(Integer, nullable=False)
    page_start = Column(Integer)
    page_end = Column(Integer)

    raw_text = Column(Text)
    cleaned_text = Column(Text)
    token_count = Column(Integer)

    child_index = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("ix_rag_nodes_document_id", "document_id"),
    )


# ---------------------------------------------------------------------------
# RagChunk — the unit of retrieval, with a pgvector embedding
# ---------------------------------------------------------------------------

class RagChunk(Base):
    __tablename__ = "rag_chunks"

    id = Column(UUID, primary_key=True, server_default=text("gen_random_uuid()"))
    document_id = Column(
        UUID, ForeignKey("rag_documents.id", ondelete="CASCADE"), nullable=False,
    )
    node_id = Column(
        UUID, ForeignKey("rag_nodes.id", ondelete="CASCADE"), nullable=False,
    )

    chunk_index = Column(Integer, nullable=False)
    chunk_kind = Column(String(30), nullable=False)

    heading_path = Column(String, nullable=False)
    page_start = Column(Integer)
    page_end = Column(Integer)

    token_count = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    content_display = Column(Text, nullable=True)  # markdown-formatted for frontend display
    content_for_embedding = Column(Text, nullable=False)

    embedding = Column(Vector())  # dimension set at insert time
    embedding_model = Column(String, nullable=False)

    prev_chunk_id = Column(UUID, ForeignKey("rag_chunks.id", ondelete="SET NULL"))
    next_chunk_id = Column(UUID, ForeignKey("rag_chunks.id", ondelete="SET NULL"))

    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("ix_rag_chunks_document_id", "document_id"),
        Index("ix_rag_chunks_node_id", "node_id"),
    )


# ---------------------------------------------------------------------------
# IngestionRun — per-stage progress tracking
# ---------------------------------------------------------------------------

class IngestionRun(Base):
    __tablename__ = "ingestion_runs"

    id = Column(UUID, primary_key=True, server_default=text("gen_random_uuid()"))
    document_id = Column(
        UUID, ForeignKey("rag_documents.id", ondelete="CASCADE"), nullable=False,
    )

    stage = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False)
    message = Column(Text)

    created_at = Column(DateTime, server_default=func.now())
    finished_at = Column(DateTime)
