"""consolidate all tables into public schema and drop unused tables

Moves active tables from main and user_data schemas into public.
Drops all unused tables and the now-empty schemas.

Revision ID: d1e2f3a4b5c6
Revises: a1b2c3d4e5f6
Create Date: 2026-03-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd1e2f3a4b5c6'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. Move active tables from main schema to public
    # ------------------------------------------------------------------
    main_tables = [
        'users', 'roles', 'user_roles', 'profiles',
        'materials', 'learning_plans', 'learning_plan_progress',
        'care_plans', 'courses', 'topics', 'learning_modules',
        'tests', 'flashcards',
    ]
    for table in main_tables:
        op.execute(sa.text(
            f"ALTER TABLE IF EXISTS main.{table} SET SCHEMA public"
        ))

    # ------------------------------------------------------------------
    # 2. Move active tables from user_data schema to public
    # ------------------------------------------------------------------
    user_data_tables = ['chat_messages', 'user_interactions', 'user_session']
    for table in user_data_tables:
        op.execute(sa.text(
            f"ALTER TABLE IF EXISTS user_data.{table} SET SCHEMA public"
        ))

    # ------------------------------------------------------------------
    # 3. Update foreign key references (main.users -> users, etc.)
    #    Drop and re-create FK constraints on user_roles
    # ------------------------------------------------------------------
    op.drop_constraint('user_roles_user_id_fkey', 'user_roles', type_='foreignkey')
    op.drop_constraint('user_roles_role_id_fkey', 'user_roles', type_='foreignkey')
    op.create_foreign_key('user_roles_user_id_fkey', 'user_roles', 'users', ['user_id'], ['id'])
    op.create_foreign_key('user_roles_role_id_fkey', 'user_roles', 'roles', ['role_id'], ['id'])

    # ------------------------------------------------------------------
    # 4. Drop all unused tables from dashboard schema
    # ------------------------------------------------------------------
    dashboard_tables = [
        'user_widgets', 'analytics_data', 'user_preferences',
        'widgets', 'dashboard_layouts',
    ]
    for table in dashboard_tables:
        op.execute(sa.text(f"DROP TABLE IF EXISTS dashboard.{table} CASCADE"))

    # ------------------------------------------------------------------
    # 5. Drop unused tables that were already in public
    # ------------------------------------------------------------------
    unused_public_tables = [
        'sessions', 'waitlist', 'course_items', 'plan_courses',
        'test_results', 'study_activity', 'weekly_insights',
        'board_exam_topics', 'content_generation',
        'anesthesia_care_plans', 'biometric_data',
        'learning_preferences', 'study_plans', 'proactive_quizzes',
        'vark_content', 'behavioral_analysis', 'agent_notifications',
        'library_content', 'visual_guides', 'biometric_devices',
        'oauth_states', 'oauth_tokens', 'academic_study_plans',
        'password_resets', 'contact_messages', 'artifacts',
        'notification_queue', 'agent_execution_logs',
        'rag_retrieval_logs', 'federation_updates',
        'mastery_scores', 'modality_preferences', 'agent_states',
    ]
    for table in unused_public_tables:
        op.execute(sa.text(f"DROP TABLE IF EXISTS public.{table} CASCADE"))

    # Also drop unused tables that might still be in main (courses, topics, etc.
    # that were moved but are unused — they'll stay in public for now since
    # the models were removed, future autogenerate will clean them up)

    # ------------------------------------------------------------------
    # 6. Drop empty schemas
    # ------------------------------------------------------------------
    op.execute(sa.text("DROP SCHEMA IF EXISTS main CASCADE"))
    op.execute(sa.text("DROP SCHEMA IF EXISTS user_data CASCADE"))
    op.execute(sa.text("DROP SCHEMA IF EXISTS dashboard CASCADE"))


def downgrade() -> None:
    # Re-create schemas
    op.execute(sa.text("CREATE SCHEMA IF NOT EXISTS main"))
    op.execute(sa.text("CREATE SCHEMA IF NOT EXISTS user_data"))
    op.execute(sa.text("CREATE SCHEMA IF NOT EXISTS dashboard"))

    # Move tables back to main
    main_tables = [
        'users', 'roles', 'user_roles', 'profiles',
        'materials', 'learning_plans', 'learning_plan_progress',
        'care_plans', 'courses', 'topics', 'learning_modules',
        'tests', 'flashcards',
    ]
    for table in main_tables:
        op.execute(sa.text(
            f"ALTER TABLE IF EXISTS public.{table} SET SCHEMA main"
        ))

    # Move tables back to user_data
    user_data_tables = ['chat_messages', 'user_interactions', 'user_session']
    for table in user_data_tables:
        op.execute(sa.text(
            f"ALTER TABLE IF EXISTS public.{table} SET SCHEMA user_data"
        ))

    # Restore FK references to main schema
    op.drop_constraint('user_roles_user_id_fkey', 'user_roles', schema='main', type_='foreignkey')
    op.drop_constraint('user_roles_role_id_fkey', 'user_roles', schema='main', type_='foreignkey')
    op.create_foreign_key('user_roles_user_id_fkey', 'user_roles', 'users',
                          ['user_id'], ['id'], source_schema='main', referent_schema='main')
    op.create_foreign_key('user_roles_role_id_fkey', 'user_roles', 'roles',
                          ['role_id'], ['id'], source_schema='main', referent_schema='main')

    # Note: dropped tables (unused) are NOT recreated in downgrade.
    # Re-run the initial migration if they are needed again.
