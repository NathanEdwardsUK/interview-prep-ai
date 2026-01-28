"""Add story_structures table

Revision ID: 003_story_structures
Revises: 002_answer_time
Create Date: 2025-01-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "003_story_structures"
down_revision: Union[str, None] = "002_answer_time"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "story_structures",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("structure_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.clerk_user_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_story_structures_id"), "story_structures", ["id"], unique=False)
    op.create_index(op.f("ix_story_structures_question_id"), "story_structures", ["question_id"], unique=False)
    op.create_index(op.f("ix_story_structures_user_id"), "story_structures", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_story_structures_user_id"), table_name="story_structures")
    op.drop_index(op.f("ix_story_structures_question_id"), table_name="story_structures")
    op.drop_index(op.f("ix_story_structures_id"), table_name="story_structures")
    op.drop_table("story_structures")
