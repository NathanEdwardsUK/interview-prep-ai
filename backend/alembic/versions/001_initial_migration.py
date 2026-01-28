"""Initial migration

Revision ID: 001_initial
Revises: 
Create Date: 2025-01-28 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('clerk_user_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('current_applying_role', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('clerk_user_id')
    )
    op.create_index(op.f('ix_users_clerk_user_id'), 'users', ['clerk_user_id'], unique=False)
    
    # Create plan_topics table
    op.create_table(
        'plan_topics',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('planned_daily_study_time', sa.Integer(), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False),
        sa.Column('expected_outcome', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.clerk_user_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_plan_topics_id'), 'plan_topics', ['id'], unique=False)
    op.create_index(op.f('ix_plan_topics_user_id'), 'plan_topics', ['user_id'], unique=False)
    
    # Create topic_progress table
    op.create_table(
        'topic_progress',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('topic_id', sa.Integer(), nullable=False),
        sa.Column('strength_rating', sa.Integer(), nullable=True),
        sa.Column('total_time_spent', sa.Integer(), nullable=True, server_default='0'),
        sa.ForeignKeyConstraint(['topic_id'], ['plan_topics.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.clerk_user_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_topic_progress_id'), 'topic_progress', ['id'], unique=False)
    op.create_index(op.f('ix_topic_progress_user_id'), 'topic_progress', ['user_id'], unique=False)
    op.create_index(op.f('ix_topic_progress_topic_id'), 'topic_progress', ['topic_id'], unique=False)
    
    # Create raw_user_context table
    op.create_table(
        'raw_user_context',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('context_text', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.clerk_user_id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_raw_user_context_id'), 'raw_user_context', ['id'], unique=False)
    op.create_index(op.f('ix_raw_user_context_user_id'), 'raw_user_context', ['user_id'], unique=True)
    
    # Create study_sessions table
    op.create_table(
        'study_sessions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('topic_id', sa.Integer(), nullable=False),
        sa.Column('planned_duration', sa.Integer(), nullable=False),
        sa.Column('start_time', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_interaction_time', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['topic_id'], ['plan_topics.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.clerk_user_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_study_sessions_id'), 'study_sessions', ['id'], unique=False)
    op.create_index(op.f('ix_study_sessions_user_id'), 'study_sessions', ['user_id'], unique=False)
    op.create_index(op.f('ix_study_sessions_topic_id'), 'study_sessions', ['topic_id'], unique=False)
    
    # Create questions table
    op.create_table(
        'questions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('topic_id', sa.Integer(), nullable=False),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('answer_anchors', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['topic_id'], ['plan_topics.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_questions_id'), 'questions', ['id'], unique=False)
    op.create_index(op.f('ix_questions_topic_id'), 'questions', ['topic_id'], unique=False)
    
    # Create question_attempts table
    op.create_table(
        'question_attempts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.Column('study_session_id', sa.Integer(), nullable=False),
        sa.Column('raw_answer', sa.Text(), nullable=False),
        sa.Column('score_rating', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ),
        sa.ForeignKeyConstraint(['study_session_id'], ['study_sessions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_question_attempts_id'), 'question_attempts', ['id'], unique=False)
    op.create_index(op.f('ix_question_attempts_question_id'), 'question_attempts', ['question_id'], unique=False)
    op.create_index(op.f('ix_question_attempts_study_session_id'), 'question_attempts', ['study_session_id'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index(op.f('ix_question_attempts_study_session_id'), table_name='question_attempts')
    op.drop_index(op.f('ix_question_attempts_question_id'), table_name='question_attempts')
    op.drop_index(op.f('ix_question_attempts_id'), table_name='question_attempts')
    op.drop_table('question_attempts')
    
    op.drop_index(op.f('ix_questions_topic_id'), table_name='questions')
    op.drop_index(op.f('ix_questions_id'), table_name='questions')
    op.drop_table('questions')
    
    op.drop_index(op.f('ix_study_sessions_topic_id'), table_name='study_sessions')
    op.drop_index(op.f('ix_study_sessions_user_id'), table_name='study_sessions')
    op.drop_index(op.f('ix_study_sessions_id'), table_name='study_sessions')
    op.drop_table('study_sessions')
    
    op.drop_index(op.f('ix_raw_user_context_user_id'), table_name='raw_user_context')
    op.drop_index(op.f('ix_raw_user_context_id'), table_name='raw_user_context')
    op.drop_table('raw_user_context')
    
    op.drop_index(op.f('ix_topic_progress_topic_id'), table_name='topic_progress')
    op.drop_index(op.f('ix_topic_progress_user_id'), table_name='topic_progress')
    op.drop_index(op.f('ix_topic_progress_id'), table_name='topic_progress')
    op.drop_table('topic_progress')
    
    op.drop_index(op.f('ix_plan_topics_user_id'), table_name='plan_topics')
    op.drop_index(op.f('ix_plan_topics_id'), table_name='plan_topics')
    op.drop_table('plan_topics')
    
    op.drop_index(op.f('ix_users_clerk_user_id'), table_name='users')
    op.drop_table('users')
