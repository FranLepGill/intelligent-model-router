from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class InferenceRequestCreate(BaseModel):
    task_type: str = Field(..., min_length=1, max_length=64, examples=["customer_support"])
    input: str = Field(..., min_length=1, max_length=100_000)
    language: str = Field(default="es", max_length=16)
    priority: Literal["low", "normal", "high"] = "normal"
    max_cost_usd: float | None = Field(default=None, ge=0)
    max_latency_ms: int | None = Field(default=None, ge=100)
    minimum_quality: float | None = Field(default=None, ge=0, le=1)
    contains_sensitive_data: bool = False
    output_format: Literal["json", "text"] = "json"

    @field_validator("input")
    @classmethod
    def strip_input(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("input cannot be empty")
        return cleaned


class RoutingInfo(BaseModel):
    selected_model: str
    provider: str
    attempts: int
    fallback_used: bool
    reason: dict[str, Any] | None = None


class UsageInfo(BaseModel):
    input_tokens: int
    output_tokens: int
    latency_ms: int
    estimated_cost_usd: float


class InferenceResponse(BaseModel):
    request_id: str
    status: str
    output: dict[str, Any] | None = None
    routing: RoutingInfo | None = None
    usage: UsageInfo | None = None
    error: str | None = None


class InferenceListItem(BaseModel):
    request_id: str
    task_type: str
    status: str
    selected_model: str | None = None
    estimated_cost_usd: float | None = None
    latency_ms: int | None = None
    requested_at: str
