"""add processing_time_seconds to materials

Revision ID: d49b50adb850
Revises: 371bd8a5f18a
Create Date: 2026-03-27 16:05:08.568587

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'd49b50adb850'
down_revision: Union[str, None] = '371bd8a5f18a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('materials', sa.Column('processing_time_seconds', sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column('materials', 'processing_time_seconds')
