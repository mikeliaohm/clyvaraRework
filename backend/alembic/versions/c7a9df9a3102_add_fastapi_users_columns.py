"""add fastapi-users compatibility columns

Revision ID: c7a9df9a3102
Revises: b4f8f1ac2f01
Create Date: 2026-03-09 00:00:01.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c7a9df9a3102'
down_revision: Union[str, None] = 'b4f8f1ac2f01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        schema='main'
    )
    op.add_column(
        'users',
        sa.Column('is_superuser', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        schema='main'
    )
    op.add_column(
        'users',
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        schema='main'
    )


def downgrade() -> None:
    op.drop_column('users', 'is_verified', schema='main')
    op.drop_column('users', 'is_superuser', schema='main')
    op.drop_column('users', 'is_active', schema='main')
