"""drop_vector_index_entries_table

Revision ID: 8cee2836eb0f
Revises: e2f3a4b5c6d7
Create Date: 2026-03-27 11:20:11.825249

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8cee2836eb0f'
down_revision: Union[str, None] = 'e2f3a4b5c6d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table('vector_index_entries')


def downgrade() -> None:
    op.create_table(
        'vector_index_entries',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('content_hash', sa.String(64), unique=True),
        sa.Column('embedding', sa.JSON(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('token_count', sa.Integer(), server_default='0'),
        sa.Column('chunk_index', sa.Integer(), server_default='0'),
        sa.Column('source_type', sa.String(50), nullable=False),
        sa.Column('source_id', sa.Integer()),
        sa.Column('vector_metadata', sa.JSON()),
        sa.Column('embedding_model', sa.String(), server_default='text-embedding-3-small'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('last_accessed', sa.DateTime()),
        sa.Column('access_count', sa.Integer(), server_default='0'),
        sa.Column('relevance_score', sa.Numeric()),
    )
