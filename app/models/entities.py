from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class ClientStatus(str, enum.Enum):
    active = "active"
    suspended = "suspended"
    inactive = "inactive"


class ProviderStatus(str, enum.Enum):
    active = "active"
    degraded = "degraded"
    unavailable = "unavailable"


class RequestStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    escalated = "escalated"


class AttemptStatus(str, enum.Enum):
    success = "success"
    failed = "failed"
    timeout = "timeout"
    invalid_response = "invalid_response"


class RoutingStrategy(str, enum.Enum):
    cheapest = "cheapest"
    fastest = "fastest"
    quality_first = "quality_first"
    balanced = "balanced"


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    status: Mapped[ClientStatus] = mapped_column(
        Enum(ClientStatus, name="client_status"), default=ClientStatus.active
    )
    daily_budget_usd: Mapped[float] = mapped_column(Float, default=20.0)
    requests_per_minute: Mapped[int] = mapped_column(Integer, default=100)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    api_keys: Mapped[list[ApiKey]] = relationship(back_populates="client")
    policies: Mapped[list[RoutingPolicy]] = relationship(back_populates="client")
    requests: Mapped[list[InferenceRequest]] = relationship(back_populates="client")


class ApiKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clients.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    key_prefix: Mapped[str] = mapped_column(String(16), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    client: Mapped[Client] = relationship(back_populates="api_keys")


class ModelProvider(Base):
    __tablename__ = "model_providers"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[ProviderStatus] = mapped_column(
        Enum(ProviderStatus, name="provider_status"), default=ProviderStatus.active
    )
    configuration: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    models: Mapped[list[AIModel]] = relationship(back_populates="provider")


class AIModel(Base):
    __tablename__ = "ai_models"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    provider_id: Mapped[str] = mapped_column(ForeignKey("model_providers.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(64), default="1.0")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    input_cost_per_million_tokens: Mapped[float] = mapped_column(Float, nullable=False)
    output_cost_per_million_tokens: Mapped[float] = mapped_column(Float, nullable=False)
    average_latency_ms: Mapped[int] = mapped_column(Integer, default=1000)
    context_window: Mapped[int] = mapped_column(Integer, default=128000)
    supports_vision: Mapped[bool] = mapped_column(Boolean, default=False)
    supports_documents: Mapped[bool] = mapped_column(Boolean, default=False)
    supports_structured_output: Mapped[bool] = mapped_column(Boolean, default=True)
    sensitive_data_allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    languages: Mapped[list[Any]] = mapped_column(JSONB, default=lambda: ["es", "en"])
    quality_by_task: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    availability_pct: Mapped[float] = mapped_column(Float, default=99.0)
    max_rpm: Mapped[int] = mapped_column(Integer, default=60)
    privacy_level: Mapped[str] = mapped_column(String(32), default="standard")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    provider: Mapped[ModelProvider] = relationship(back_populates="models")


class RoutingPolicy(Base):
    __tablename__ = "routing_policies"
    __table_args__ = (UniqueConstraint("client_id", "task_type", name="uq_client_task_policy"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clients.id"), nullable=False)
    task_type: Mapped[str] = mapped_column(String(64), nullable=False)
    strategy: Mapped[RoutingStrategy] = mapped_column(
        Enum(RoutingStrategy, name="routing_strategy"), default=RoutingStrategy.balanced
    )
    minimum_quality: Mapped[float] = mapped_column(Float, default=0.85)
    maximum_cost_usd: Mapped[float] = mapped_column(Float, default=0.05)
    maximum_latency_ms: Mapped[int] = mapped_column(Integer, default=5000)
    maximum_attempts: Mapped[int] = mapped_column(Integer, default=3)
    allow_fallback: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    client: Mapped[Client] = relationship(back_populates="policies")


class InferenceRequest(Base):
    __tablename__ = "inference_requests"
    __table_args__ = (
        UniqueConstraint("client_id", "idempotency_key", name="uq_client_idempotency"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    client_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clients.id"), nullable=False)
    task_type: Mapped[str] = mapped_column(String(64), nullable=False)
    input_text: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(16), default="es")
    priority: Mapped[str] = mapped_column(String(32), default="normal")
    status: Mapped[RequestStatus] = mapped_column(
        Enum(RequestStatus, name="request_status"), default=RequestStatus.pending
    )
    maximum_cost_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    minimum_quality: Mapped[float | None] = mapped_column(Float, nullable=True)
    maximum_latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    contains_sensitive_data: Mapped[bool] = mapped_column(Boolean, default=False)
    output_format: Mapped[str] = mapped_column(String(32), default="json")
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    features: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    routing_decision: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    output: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    usage: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    client: Mapped[Client] = relationship(back_populates="requests")
    attempts: Mapped[list[InferenceAttempt]] = relationship(
        back_populates="request", order_by="InferenceAttempt.attempt_number"
    )


class InferenceAttempt(Base):
    __tablename__ = "inference_attempts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id: Mapped[str] = mapped_column(ForeignKey("inference_requests.id"), nullable=False)
    model_id: Mapped[str] = mapped_column(ForeignKey("ai_models.id"), nullable=False)
    provider_id: Mapped[str] = mapped_column(String(64), nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[AttemptStatus] = mapped_column(Enum(AttemptStatus, name="attempt_status"))
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    estimated_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    error_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_response: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    request: Mapped[InferenceRequest] = relationship(back_populates="attempts")
