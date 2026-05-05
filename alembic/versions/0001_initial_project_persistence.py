"""initial project persistence

Revision ID: 0001_initial_project_persistence
Revises:
Create Date: 2026-05-04 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0001_initial_project_persistence"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("brand_name", sa.String(length=256), nullable=True),
        sa.Column("product_name", sa.String(length=256), nullable=True),
        sa.Column("category", sa.String(length=256), nullable=True),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("request_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("response_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("score_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("customer_id", sa.String(length=64), nullable=False),
        sa.Column("created_by", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
    )
    op.create_index("ix_projects_brand_name", "projects", ["brand_name"], unique=False)
    op.create_index("ix_projects_category", "projects", ["category"], unique=False)
    op.create_index("ix_projects_created_by", "projects", ["created_by"], unique=False)
    op.create_index("ix_projects_customer_deleted", "projects", ["customer_id", "is_deleted"], unique=False)
    op.create_index("ix_projects_customer_id", "projects", ["customer_id"], unique=False)
    op.create_index("ix_projects_customer_status", "projects", ["customer_id", "status"], unique=False)
    op.create_index("ix_projects_customer_updated", "projects", ["customer_id", "updated_at"], unique=False)
    op.create_index("ix_projects_is_deleted", "projects", ["is_deleted"], unique=False)
    op.create_index("ix_projects_name", "projects", ["name"], unique=False)
    op.create_index("ix_projects_product_name", "projects", ["product_name"], unique=False)
    op.create_index("ix_projects_status", "projects", ["status"], unique=False)

    op.create_table(
        "uploaded_assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("file_name", sa.String(length=512), nullable=False),
        sa.Column("content_type", sa.String(length=128), nullable=False),
        sa.Column("storage_url", sa.Text(), nullable=True),
        sa.Column("asset_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("customer_id", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
    )
    op.create_index("ix_uploaded_assets_customer_id", "uploaded_assets", ["customer_id"], unique=False)
    op.create_index("ix_uploaded_assets_is_deleted", "uploaded_assets", ["is_deleted"], unique=False)
    op.create_index("ix_uploaded_assets_project_id", "uploaded_assets", ["project_id"], unique=False)

    op.create_table(
        "generation_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("progress_percent", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("job_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("customer_id", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
    )
    op.create_index("ix_generation_jobs_customer_id", "generation_jobs", ["customer_id"], unique=False)
    op.create_index("ix_generation_jobs_is_deleted", "generation_jobs", ["is_deleted"], unique=False)
    op.create_index("ix_generation_jobs_project_id", "generation_jobs", ["project_id"], unique=False)
    op.create_index("ix_generation_jobs_status", "generation_jobs", ["status"], unique=False)

    op.create_table(
        "provider_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider_type", sa.String(length=64), nullable=False),
        sa.Column("model", sa.String(length=256), nullable=True),
        sa.Column("mode", sa.String(length=64), nullable=False),
        sa.Column("latency_ms", sa.String(length=32), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("provider_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("customer_id", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
    )
    op.create_index("ix_provider_runs_customer_id", "provider_runs", ["customer_id"], unique=False)
    op.create_index("ix_provider_runs_mode", "provider_runs", ["mode"], unique=False)
    op.create_index("ix_provider_runs_project_id", "provider_runs", ["project_id"], unique=False)
    op.create_index("ix_provider_runs_provider_type", "provider_runs", ["provider_type"], unique=False)
    op.create_index("ix_provider_runs_success", "provider_runs", ["success"], unique=False)

    op.create_table(
        "creative_packs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("customer_id", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
    )
    op.create_index("ix_creative_packs_customer_id", "creative_packs", ["customer_id"], unique=False)
    op.create_index("ix_creative_packs_is_deleted", "creative_packs", ["is_deleted"], unique=False)
    op.create_index("ix_creative_packs_project_id", "creative_packs", ["project_id"], unique=False)

    op.create_table(
        "design_specs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("customer_id", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
    )
    op.create_index("ix_design_specs_customer_id", "design_specs", ["customer_id"], unique=False)
    op.create_index("ix_design_specs_is_deleted", "design_specs", ["is_deleted"], unique=False)
    op.create_index("ix_design_specs_project_id", "design_specs", ["project_id"], unique=False)

    op.create_table(
        "export_artifacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("export_type", sa.String(length=64), nullable=False),
        sa.Column("data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("customer_id", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
    )
    op.create_index("ix_export_artifacts_customer_id", "export_artifacts", ["customer_id"], unique=False)
    op.create_index("ix_export_artifacts_export_type", "export_artifacts", ["export_type"], unique=False)
    op.create_index("ix_export_artifacts_is_deleted", "export_artifacts", ["is_deleted"], unique=False)
    op.create_index("ix_export_artifacts_project_id", "export_artifacts", ["project_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_export_artifacts_project_id", table_name="export_artifacts")
    op.drop_index("ix_export_artifacts_is_deleted", table_name="export_artifacts")
    op.drop_index("ix_export_artifacts_export_type", table_name="export_artifacts")
    op.drop_index("ix_export_artifacts_customer_id", table_name="export_artifacts")
    op.drop_table("export_artifacts")

    op.drop_index("ix_design_specs_project_id", table_name="design_specs")
    op.drop_index("ix_design_specs_is_deleted", table_name="design_specs")
    op.drop_index("ix_design_specs_customer_id", table_name="design_specs")
    op.drop_table("design_specs")

    op.drop_index("ix_creative_packs_project_id", table_name="creative_packs")
    op.drop_index("ix_creative_packs_is_deleted", table_name="creative_packs")
    op.drop_index("ix_creative_packs_customer_id", table_name="creative_packs")
    op.drop_table("creative_packs")

    op.drop_index("ix_provider_runs_success", table_name="provider_runs")
    op.drop_index("ix_provider_runs_provider_type", table_name="provider_runs")
    op.drop_index("ix_provider_runs_project_id", table_name="provider_runs")
    op.drop_index("ix_provider_runs_mode", table_name="provider_runs")
    op.drop_index("ix_provider_runs_customer_id", table_name="provider_runs")
    op.drop_table("provider_runs")

    op.drop_index("ix_generation_jobs_status", table_name="generation_jobs")
    op.drop_index("ix_generation_jobs_project_id", table_name="generation_jobs")
    op.drop_index("ix_generation_jobs_is_deleted", table_name="generation_jobs")
    op.drop_index("ix_generation_jobs_customer_id", table_name="generation_jobs")
    op.drop_table("generation_jobs")

    op.drop_index("ix_uploaded_assets_project_id", table_name="uploaded_assets")
    op.drop_index("ix_uploaded_assets_is_deleted", table_name="uploaded_assets")
    op.drop_index("ix_uploaded_assets_customer_id", table_name="uploaded_assets")
    op.drop_table("uploaded_assets")

    op.drop_index("ix_projects_status", table_name="projects")
    op.drop_index("ix_projects_product_name", table_name="projects")
    op.drop_index("ix_projects_name", table_name="projects")
    op.drop_index("ix_projects_is_deleted", table_name="projects")
    op.drop_index("ix_projects_customer_updated", table_name="projects")
    op.drop_index("ix_projects_customer_status", table_name="projects")
    op.drop_index("ix_projects_customer_id", table_name="projects")
    op.drop_index("ix_projects_customer_deleted", table_name="projects")
    op.drop_index("ix_projects_created_by", table_name="projects")
    op.drop_index("ix_projects_category", table_name="projects")
    op.drop_index("ix_projects_brand_name", table_name="projects")
    op.drop_table("projects")
