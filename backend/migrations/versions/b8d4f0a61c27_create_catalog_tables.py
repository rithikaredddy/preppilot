"""create catalog tables

Revision ID: b8d4f0a61c27
Revises: c4e8a1b27d90
Create Date: 2026-09-30 12:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

revision = "b8d4f0a61c27"
down_revision = "c4e8a1b27d90"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "companies",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("overview", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_table(
        "company_questions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("category", sa.String(length=16), nullable=False),
        sa.Column("topic", sa.String(length=80), nullable=False),
        sa.Column("difficulty", sa.String(length=16), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("preparation_tip", sa.Text(), nullable=False),
        sa.Column("source", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "category IN ('hr', 'technical', 'coding')", name="ck_company_questions_category"
        ),
        sa.CheckConstraint(
            "source IN ('curated', 'ai_generated')", name="ck_company_questions_source"
        ),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_company_questions_company_id", "company_questions", ["company_id"])
    op.create_table(
        "coding_problems",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=True),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("difficulty", sa.String(length=16), nullable=False),
        sa.Column("topic", sa.String(length=80), nullable=False),
        sa.Column("starter_code", sa.JSON(), nullable=False),
        sa.Column("time_limit_ms", sa.Integer(), nullable=False),
        sa.Column("memory_limit_kb", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("source IN ('curated', 'ai_generated')", name="ck_coding_problems_source"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "coding_test_cases",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("problem_id", sa.Uuid(), nullable=False),
        sa.Column("stdin", sa.Text(), nullable=False),
        sa.Column("expected_stdout", sa.Text(), nullable=False),
        sa.Column("is_hidden", sa.Boolean(), nullable=False),
        sa.Column("weight", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["problem_id"], ["coding_problems.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_coding_test_cases_problem_id", "coding_test_cases", ["problem_id"])
    op.create_table(
        "coding_submissions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("problem_id", sa.Uuid(), nullable=False),
        sa.Column("language", sa.String(length=16), nullable=False),
        sa.Column("source_code", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("passed_count", sa.Integer(), nullable=False),
        sa.Column("total_count", sa.Integer(), nullable=False),
        sa.Column("score", sa.Numeric(5, 2), nullable=False),
        sa.Column("execution_time_ms", sa.Integer(), nullable=True),
        sa.Column("memory_kb", sa.Integer(), nullable=True),
        sa.Column("ai_review", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["problem_id"], ["coding_problems.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_coding_submissions_problem_id", "coding_submissions", ["problem_id"])
    op.create_index("ix_coding_submissions_student_id", "coding_submissions", ["student_id"])
    op.create_table(
        "coding_submission_results",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("submission_id", sa.Uuid(), nullable=False),
        sa.Column("test_case_id", sa.Uuid(), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("time_ms", sa.Integer(), nullable=True),
        sa.Column("memory_kb", sa.Integer(), nullable=True),
        sa.Column("stdout", sa.Text(), nullable=True),
        sa.Column("stderr", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.ForeignKeyConstraint(["submission_id"], ["coding_submissions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["test_case_id"], ["coding_test_cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_coding_submission_results_submission_id",
        "coding_submission_results",
        ["submission_id"],
    )
    op.create_table(
        "communication_analyses",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=True),
        sa.Column("turn_id", sa.Uuid(), nullable=True),
        sa.Column("audio_path", sa.String(length=500), nullable=False),
        sa.Column("transcript", sa.Text(), nullable=False),
        sa.Column("duration_seconds", sa.Numeric(8, 2), nullable=False),
        sa.Column("words_per_minute", sa.Numeric(6, 1), nullable=False),
        sa.Column("filler_count", sa.Integer(), nullable=False),
        sa.Column("filler_words", sa.JSON(), nullable=False),
        sa.Column("pause_count", sa.Integer(), nullable=True),
        sa.Column("clarity_feedback", sa.Text(), nullable=False),
        sa.Column("communication_score", sa.Numeric(5, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["interview_sessions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["turn_id"], ["interview_turns.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_communication_analyses_student_id", "communication_analyses", ["student_id"])


def downgrade():
    op.drop_index("ix_communication_analyses_student_id", table_name="communication_analyses")
    op.drop_table("communication_analyses")
    op.drop_index("ix_coding_submission_results_submission_id", table_name="coding_submission_results")
    op.drop_table("coding_submission_results")
    op.drop_index("ix_coding_submissions_student_id", table_name="coding_submissions")
    op.drop_index("ix_coding_submissions_problem_id", table_name="coding_submissions")
    op.drop_table("coding_submissions")
    op.drop_index("ix_coding_test_cases_problem_id", table_name="coding_test_cases")
    op.drop_table("coding_test_cases")
    op.drop_table("coding_problems")
    op.drop_index("ix_company_questions_company_id", table_name="company_questions")
    op.drop_table("company_questions")
    op.drop_table("companies")
