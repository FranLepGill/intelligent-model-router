"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-07-14

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    client_status = sa.Enum("active", "suspended", "inactive", name="client_status")
    provider_status = sa.Enum("active", "degraded", "unavailable", name="provider_status")
    request_status = sa.Enum(
        "pending", "running", "completed", "failed", "escalated", name="request_status"
    )
    attempt_status = sa.Enum(
        "success", "failed", "timeout", "invalid_response", name="attempt_status"
    )
    routing_strategy = sa.Enum(
        "cheapest", "fastest", "quality_first", "balanced", name="routing_strategy"
    )

    client_status.create(op.get_bind(), checkfirst=True)
    provider_status.create(op.get_bind(), checkfirst=True)
    request_status.create(op.get_bind(), checkfirst=True)
    attempt_status.create(op.get_bind(), checkfirst=True)
    routing_strategy.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "clients",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column("status", client_status, nullable=False),
        sa.Column("daily_budget_usd", sa.Float(), nullable=False, server_default="20"),
        sa.Column("requests_per_minute", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "api_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clients.id")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("key_prefix", sa.String(16), nullable=False),
        sa.Column("key_hash", sa.String(255), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "model_providers",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("status", provider_status, nullable=False),
        sa.Column("configuration", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "ai_models",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("provider_id", sa.String(64), sa.ForeignKey("model_providers.id")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("version", sa.String(64), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("input_cost_per_million_tokens", sa.Float(), nullable=False),
        sa.Column("output_cost_per_million_tokens", sa.Float(), nullable=False),
        sa.Column("average_latency_ms", sa.Integer(), nullable=False),
        sa.Column("context_window", sa.Integer(), nullable=False),
        sa.Column("supports_vision", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("supports_documents", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "supports_structured_output", sa.Boolean(), nullable=False, server_default="true"
        ),
        sa.Column(
            "sensitive_data_allowed", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column("languages", postgresql.JSONB(), nullable=False, server_default='["es","en"]'),
        sa.Column("quality_by_task", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("availability_pct", sa.Float(), nullable=False, server_default="99"),
        sa.Column("max_rpm", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("privacy_level", sa.String(32), nullable=False, server_default="standard"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "routing_policies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clients.id")),
        sa.Column("task_type", sa.String(64), nullable=False),
        sa.Column("strategy", routing_strategy, nullable=False),
        sa.Column("minimum_quality", sa.Float(), nullable=False),
        sa.Column("maximum_cost_usd", sa.Float(), nullable=False),
        sa.Column("maximum_latency_ms", sa.Integer(), nullable=False),
        sa.Column("maximum_attempts", sa.Integer(), nullable=False),
        sa.Column("allow_fallback", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("client_id", "task_type", name="uq_client_task_policy"),
    )

    op.create_table(
        "inference_requests",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clients.id")),
        sa.Column("task_type", sa.String(64), nullable=False),
        sa.Column("input_text", sa.Text(), nullable=False),
        sa.Column("language", sa.String(16), nullable=False),
        sa.Column("priority", sa.String(32), nullable=False),
        sa.Column("status", request_status, nullable=False),
        sa.Column("maximum_cost_usd", sa.Float(), nullable=True),
        sa.Column("minimum_quality", sa.Float(), nullable=True),
        sa.Column("maximum_latency_ms", sa.Integer(), nullable=True),
        sa.Column(
            "contains_sensitive_data", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column("output_format", sa.String(32), nullable=False),
        sa.Column("idempotency_key", sa.String(128), nullable=True),
        sa.Column("features", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("routing_decision", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("output", postgresql.JSONB(), nullable=True),
        sa.Column("usage", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("requested_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("client_id", "idempotency_key", name="uq_client_idempotency"),
    )

    op.create_table(
        "inference_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("request_id", sa.String(64), sa.ForeignKey("inference_requests.id")),
        sa.Column("model_id", sa.String(64), sa.ForeignKey("ai_models.id")),
        sa.Column("provider_id", sa.String(64), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("status", attempt_status, nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False),
        sa.Column("output_tokens", sa.Integer(), nullable=False),
        sa.Column("estimated_cost_usd", sa.Float(), nullable=False),
        sa.Column("error_type", sa.String(64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("raw_response", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("inference_attempts")
    op.drop_table("inference_requests")
    op.drop_table("routing_policies")
    op.drop_table("ai_models")
    op.drop_table("model_providers")
    op.drop_table("api_keys")
    op.drop_table("clients")

    sa.Enum(name="routing_strategy").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="attempt_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="request_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="provider_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="client_status").drop(op.get_bind(), checkfirst=True)
