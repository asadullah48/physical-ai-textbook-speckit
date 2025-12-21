"""Add user_progress and module_progress tables

Revision ID: 0003
Revises: 0002
Create Date: 2024-12-19

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create user_progress table
    op.create_table(
        "user_progress",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("content_type", sa.String(20), nullable=False),
        sa.Column("content_id", sa.String(100), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="not_started"),
        sa.Column("progress_percent", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("scroll_position", sa.Float(), nullable=True),
        sa.Column("reading_time_seconds", sa.Integer(), nullable=False, server_default="0"),
        # Exercise-specific fields
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("best_score", sa.Float(), nullable=True),
        sa.Column("last_answer", sa.Text(), nullable=True),
        # Timestamps
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "last_accessed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        # Constraints
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "content_id", name="uq_user_content"),
        sa.CheckConstraint(
            "progress_percent >= 0 AND progress_percent <= 100",
            name="ck_user_progress_percent",
        ),
        sa.CheckConstraint(
            "scroll_position IS NULL OR (scroll_position >= 0 AND scroll_position <= 1)",
            name="ck_user_progress_scroll",
        ),
        sa.CheckConstraint(
            "best_score IS NULL OR (best_score >= 0 AND best_score <= 100)",
            name="ck_user_progress_score",
        ),
    )

    # Create indexes for user_progress table
    op.create_index("ix_user_progress_user_id", "user_progress", ["user_id"])
    op.create_index(
        "ix_progress_user_type", "user_progress", ["user_id", "content_type"]
    )
    op.create_index(
        "ix_progress_user_recent", "user_progress", ["user_id", "last_accessed_at"]
    )

    # Create module_progress table
    op.create_table(
        "module_progress",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("module_id", sa.String(50), nullable=False),
        sa.Column("total_chapters", sa.Integer(), nullable=False),
        sa.Column("completed_chapters", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_exercises", sa.Integer(), nullable=False),
        sa.Column("completed_exercises", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("overall_progress", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("first_accessed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_accessed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        # Constraints
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "module_id", name="uq_user_module"),
    )

    # Create indexes for module_progress table
    op.create_index("ix_module_progress_user", "module_progress", ["user_id"])


def downgrade() -> None:
    # Drop module_progress table and indexes
    op.drop_index("ix_module_progress_user", table_name="module_progress")
    op.drop_table("module_progress")

    # Drop user_progress table and indexes
    op.drop_index("ix_progress_user_recent", table_name="user_progress")
    op.drop_index("ix_progress_user_type", table_name="user_progress")
    op.drop_index("ix_user_progress_user_id", table_name="user_progress")
    op.drop_table("user_progress")
