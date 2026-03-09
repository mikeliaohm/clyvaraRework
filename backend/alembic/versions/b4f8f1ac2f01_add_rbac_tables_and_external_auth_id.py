"""add rbac tables and external auth mapping

Revision ID: b4f8f1ac2f01
Revises: 5d3a712b3ced
Create Date: 2026-03-09 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b4f8f1ac2f01'
down_revision: Union[str, None] = '5d3a712b3ced'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('external_auth_id', sa.String(), nullable=True), schema='main')
    op.create_unique_constraint('uq_users_external_auth_id', 'users', ['external_auth_id'], schema='main')

    op.create_table(
        'roles',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        schema='main'
    )

    op.create_table(
        'user_roles',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['role_id'], ['main.roles.id']),
        sa.ForeignKeyConstraint(['user_id'], ['main.users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'role_id', name='uq_user_roles_user_role'),
        schema='main'
    )

    op.execute(
        sa.text(
            """
            INSERT INTO main.roles (name, description)
            VALUES
                ('user', 'Default authenticated user role'),
                ('admin', 'Administrator role for privileged operations')
            ON CONFLICT (name) DO NOTHING
            """
        )
    )


def downgrade() -> None:
    op.drop_table('user_roles', schema='main')
    op.drop_table('roles', schema='main')
    op.drop_constraint('uq_users_external_auth_id', 'users', schema='main', type_='unique')
    op.drop_column('users', 'external_auth_id', schema='main')
