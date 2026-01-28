"""Add last_plan_refinement_date to users

Revision ID: 004_refinement_date
Revises: 003_story_structures
Create Date: 2025-01-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "004_refinement_date"
down_revision: Union[str, None] = "003_story_structures"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("last_plan_refinement_date", sa.Date(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "last_plan_refinement_date")
