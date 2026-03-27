"""add RAG tables and pgvector extension

Revision ID: e2f3a4b5c6d7
Revises: d1e2f3a4b5c6
Create Date: 2026-03-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = 'e2f3a4b5c6d7'
down_revision: Union[str, None] = 'd1e2f3a4b5c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    op.create_table(
        'rag_documents',
        sa.Column('id', sa.dialects.postgresql.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('material_id', sa.Integer(), sa.ForeignKey('materials.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('source_path', sa.String(), nullable=False),
        sa.Column('checksum_sha256', sa.String(64), nullable=False, unique=True),
        sa.Column('page_count', sa.Integer()),
        sa.Column('status', sa.String(30), nullable=False, server_default=sa.text("'uploaded'")),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'rag_nodes',
        sa.Column('id', sa.dialects.postgresql.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('document_id', sa.dialects.postgresql.UUID(), sa.ForeignKey('rag_documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('parent_id', sa.dialects.postgresql.UUID(), sa.ForeignKey('rag_nodes.id', ondelete='CASCADE')),
        sa.Column('node_type', sa.String(30), nullable=False),
        sa.Column('ordinal_label', sa.String()),
        sa.Column('heading_text', sa.String()),
        sa.Column('heading_path', sa.String(), nullable=False),
        sa.Column('depth', sa.Integer(), nullable=False),
        sa.Column('page_start', sa.Integer()),
        sa.Column('page_end', sa.Integer()),
        sa.Column('raw_text', sa.Text()),
        sa.Column('cleaned_text', sa.Text()),
        sa.Column('token_count', sa.Integer()),
        sa.Column('child_index', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_rag_nodes_document_id', 'rag_nodes', ['document_id'])

    op.create_table(
        'rag_chunks',
        sa.Column('id', sa.dialects.postgresql.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('document_id', sa.dialects.postgresql.UUID(), sa.ForeignKey('rag_documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('node_id', sa.dialects.postgresql.UUID(), sa.ForeignKey('rag_nodes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('chunk_kind', sa.String(30), nullable=False),
        sa.Column('heading_path', sa.String(), nullable=False),
        sa.Column('page_start', sa.Integer()),
        sa.Column('page_end', sa.Integer()),
        sa.Column('token_count', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('content_for_embedding', sa.Text(), nullable=False),
        sa.Column('embedding', Vector(), nullable=True),
        sa.Column('embedding_model', sa.String(), nullable=False),
        sa.Column('prev_chunk_id', sa.dialects.postgresql.UUID(), sa.ForeignKey('rag_chunks.id', ondelete='SET NULL')),
        sa.Column('next_chunk_id', sa.dialects.postgresql.UUID(), sa.ForeignKey('rag_chunks.id', ondelete='SET NULL')),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_rag_chunks_document_id', 'rag_chunks', ['document_id'])
    op.create_index('ix_rag_chunks_node_id', 'rag_chunks', ['node_id'])

    op.create_table(
        'ingestion_runs',
        sa.Column('id', sa.dialects.postgresql.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('document_id', sa.dialects.postgresql.UUID(), sa.ForeignKey('rag_documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('stage', sa.String(50), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('message', sa.Text()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('finished_at', sa.DateTime()),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('ingestion_runs')
    op.drop_table('rag_chunks')
    op.drop_table('rag_nodes')
    op.drop_table('rag_documents')
    op.execute('DROP EXTENSION IF EXISTS vector')
