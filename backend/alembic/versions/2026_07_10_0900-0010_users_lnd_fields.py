"""add L&D-portal fields to users (password_hash, department, job_title, phone, status)
and make google_sub nullable so local-auth users can exist.

Revision ID: 0010_users_lnd_fields
Revises: 0009_activity_completions
Create Date: 2026-07-10 09:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0010_users_lnd_fields"
down_revision: Union[str, None] = "0009_activity_completions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ---- New optional profile / auth columns ----
    op.add_column(
        "users",
        sa.Column("password_hash", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("department", sa.String(length=120), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("job_title", sa.String(length=120), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("phone", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column(
            "status",
            sa.String(length=16),
            nullable=False,
            server_default="active",
        ),
    )

    # Helpful indexes for filtering the admin user list.
    op.create_index("ix_users_department", "users", ["department"])
    op.create_index("ix_users_status", "users", ["status"])

    # ---- Relax google_sub to nullable ----
    # Local-password users have no Google identity, so google_sub must
    # allow NULL. The UNIQUE constraint still guarantees uniqueness for
    # populated values (MySQL allows multiple NULLs in a UNIQUE index).
    op.alter_column(
        "users",
        "google_sub",
        existing_type=sa.String(length=64),
        nullable=True,
    )


def downgrade() -> None:
    # Re-tighten google_sub (will fail if any local-only users exist).
    op.alter_column(
        "users",
        "google_sub",
        existing_type=sa.String(length=64),
        nullable=False,
    )
    op.drop_index("ix_users_status", table_name="users")
    op.drop_index("ix_users_department", table_name="users")
    op.drop_column("users", "status")
    op.drop_column("users", "phone")
    op.drop_column("users", "job_title")
    op.drop_column("users", "department")
    op.drop_column("users", "password_hash")
