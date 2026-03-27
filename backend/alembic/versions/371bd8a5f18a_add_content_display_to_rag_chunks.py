"""add content_display to rag_chunks

Revision ID: 371bd8a5f18a
Revises: 8cee2836eb0f
Create Date: 2026-03-27 13:39:04.455196

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '371bd8a5f18a'
down_revision: Union[str, None] = '8cee2836eb0f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('rag_chunks', sa.Column('content_display', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('rag_chunks', 'content_display')
