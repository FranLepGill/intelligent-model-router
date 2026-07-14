from typing import Any

from pydantic import BaseModel, Field


class ClientProfileResponse(BaseModel):
    id: str
    name: str
    status: str
    daily_budget_usd: float
    requests_per_minute: int
    created_at: str | None = None
    policies: list[dict[str, Any]] = Field(default_factory=list)
    api_key_prefixes: list[str] = Field(default_factory=list)


class DashboardMetrics(BaseModel):
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_cost_usd: float
    average_latency_ms: float
    most_used_model: str | None = None
    provider_error_counts: dict[str, int] = Field(default_factory=dict)
    model_usage: dict[str, int] = Field(default_factory=dict)
    fallback_rate: float = 0.0
    recent_requests: list[dict[str, Any]] = Field(default_factory=list)
