"""readiness roadmap and reports

Revision ID: e7a1c9d44b02
Revises: b8d4f0a61c27
Create Date: 2026-10-02 15:40:00.000000

"""

import sqlalchemy as sa
from alembic import op

revision = "e7a1c9d44b02"
down_revision = "b8d4f0a61c27"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("student_profiles", sa.Column("target_companies", sa.String(length=240), nullable=True))
    op.create_table(
        "readiness_history",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("readiness_percentage", sa.Numeric(5, 2), nullable=False),
        sa.Column("top_factors", sa.JSON(), nullable=False),
        sa.Column("inputs", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_readiness_history_student_id", "readiness_history", ["student_id"])
    op.create_table(
        "roadmap_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("topic", sa.String(length=160), nullable=False),
        sa.Column("subtopic", sa.String(length=240), nullable=False),
        sa.Column("resource_title", sa.String(length=240), nullable=False),
        sa.Column("resource_link", sa.String(length=500), nullable=False),
        sa.Column("focus", sa.String(length=40), nullable=False),
        sa.Column("is_complete", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_roadmap_items_student_id", "roadmap_items", ["student_id"])
    op.create_table(
        "reports",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("pdf_path", sa.Text(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_reports_student_id", "reports", ["student_id"])


def downgrade():
    op.drop_index("ix_reports_student_id", table_name="reports")
    op.drop_table("reports")
    op.drop_index("ix_roadmap_items_student_id", table_name="roadmap_items")
    op.drop_table("roadmap_items")
    op.drop_index("ix_readiness_history_student_id", table_name="readiness_history")
    op.drop_table("readiness_history")
    op.drop_column("student_profiles", "target_companies")
