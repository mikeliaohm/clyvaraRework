"""make username and full_name nullable for optional registration fields

Revision ID: a1b2c3d4e5f6
Revises: c7a9df9a3102
Create Date: 2026-03-09 00:00:02.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'c7a9df9a3102'
branch_labels: Union[Sequence[str], None] = None
depends_on: Union[Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('users', 'username', nullable=True, schema='main')
    op.alter_column('users', 'full_name', nullable=True, schema='main')


def downgrade() -> None:
    # Restore NOT NULL — will fail if any rows have NULL values.
    op.alter_column('users', 'username', nullable=False, schema='main')
    op.alter_column('users', 'full_name', nullable=False, schema='main')
