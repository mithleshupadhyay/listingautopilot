"""add image assets and editable designs

Revision ID: 0002_assets_designs
Revises: 0001_initial_project_persistence
Create Date: 2026-05-04 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0002_assets_designs"
down_revision = "0001_initial_project_persistence"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "image_assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("asset_type", sa.String(length=64), nullable=False),
        sa.Column("file_name", sa.String(length=512), nullable=False),
        sa.Column("content_type", sa.String(length=128), nullable=False),
        sa.Column("storage_path", sa.Text(), nullable=True),
        sa.Column("public_url", sa.Text(), nullable=True),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("asset_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("customer_id", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
    )
    op.create_index("ix_image_assets_asset_type", "image_assets", ["asset_type"], unique=False)
    op.create_index("ix_image_assets_customer_id", "image_assets", ["customer_id"], unique=False)
    op.create_index("ix_image_assets_customer_type", "image_assets", ["customer_id", "asset_type"], unique=False)
    op.create_index("ix_image_assets_is_deleted", "image_assets", ["is_deleted"], unique=False)
    op.create_index("ix_image_assets_project_id", "image_assets", ["project_id"], unique=False)
    op.create_index("ix_image_assets_project_type", "image_assets", ["project_id", "asset_type"], unique=False)
    op.create_index("ix_image_assets_provider", "image_assets", ["provider"], unique=False)

    op.create_table(
        "editable_designs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("design_type", sa.String(length=64), nullable=False),
        sa.Column("version", sa.String(length=32), nullable=False),
        sa.Column("canvas_width", sa.Integer(), nullable=False),
        sa.Column("canvas_height", sa.Integer(), nullable=False),
        sa.Column("design_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("preview_asset_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("customer_id", sa.String(length=64), nullable=False),
        sa.Column("created_by", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["preview_asset_id"], ["image_assets.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id"),
    )
    op.create_index("ix_editable_designs_created_by", "editable_designs", ["created_by"], unique=False)
    op.create_index("ix_editable_designs_customer_id", "editable_designs", ["customer_id"], unique=False)
    op.create_index("ix_editable_designs_customer_status", "editable_designs", ["customer_id", "status"], unique=False)
    op.create_index("ix_editable_designs_design_type", "editable_designs", ["design_type"], unique=False)
    op.create_index("ix_editable_designs_is_deleted", "editable_designs", ["is_deleted"], unique=False)
    op.create_index("ix_editable_designs_name", "editable_designs", ["name"], unique=False)
    op.create_index("ix_editable_designs_preview_asset_id", "editable_designs", ["preview_asset_id"], unique=False)
    op.create_index("ix_editable_designs_project_id", "editable_designs", ["project_id"], unique=False)
    op.create_index("ix_editable_designs_project_type", "editable_designs", ["project_id", "design_type"], unique=False)
    op.create_index("ix_editable_designs_status", "editable_designs", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_editable_designs_status", table_name="editable_designs")
    op.drop_index("ix_editable_designs_project_type", table_name="editable_designs")
    op.drop_index("ix_editable_designs_project_id", table_name="editable_designs")
    op.drop_index("ix_editable_designs_preview_asset_id", table_name="editable_designs")
    op.drop_index("ix_editable_designs_name", table_name="editable_designs")
    op.drop_index("ix_editable_designs_is_deleted", table_name="editable_designs")
    op.drop_index("ix_editable_designs_design_type", table_name="editable_designs")
    op.drop_index("ix_editable_designs_customer_status", table_name="editable_designs")
    op.drop_index("ix_editable_designs_customer_id", table_name="editable_designs")
    op.drop_index("ix_editable_designs_created_by", table_name="editable_designs")
    op.drop_table("editable_designs")

    op.drop_index("ix_image_assets_provider", table_name="image_assets")
    op.drop_index("ix_image_assets_project_type", table_name="image_assets")
    op.drop_index("ix_image_assets_project_id", table_name="image_assets")
    op.drop_index("ix_image_assets_is_deleted", table_name="image_assets")
    op.drop_index("ix_image_assets_customer_type", table_name="image_assets")
    op.drop_index("ix_image_assets_customer_id", table_name="image_assets")
    op.drop_index("ix_image_assets_asset_type", table_name="image_assets")
    op.drop_table("image_assets")
