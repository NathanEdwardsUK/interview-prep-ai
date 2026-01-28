"""Add answer_time_seconds to question_attempts

Revision ID: 002_answer_time
Revises: 001_initial
Create Date: 2025-01-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002_answer_time"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "question_attempts",
        sa.Column("answer_time_seconds", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("question_attempts", "answer_time_seconds")
