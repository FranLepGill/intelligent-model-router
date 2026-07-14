from typing import Any

from pydantic import BaseModel, Field


class AIModelCreate(BaseModel):
    id: str = Field(..., min_length=1, max_length=64)
    provider_id: str
    name: str
    version: str = "1.0"
    enabled: bool = True
    is_default: bool = False
    input_cost_per_million_tokens: float = Field(..., ge=0)
    output_cost_per_million_tokens: float = Field(..., ge=0)
    average_latency_ms: int = Field(default=1000, ge=1)
    context_window: int = Field(default=128000, ge=1)
    supports_vision: bool = False
    supports_documents: bool = False
    supports_structured_output: bool = True
    sensitive_data_allowed: bool = False
    languages: list[str] = Field(default_factory=lambda: ["es", "en"])
    quality_by_task: dict[str, float] = Field(default_factory=dict)
    availability_pct: float = 99.0
    max_rpm: int = 60
    privacy_level: str = "standard"


class AIModelUpdate(BaseModel):
    name: str | None = None
    enabled: bool | None = None
    is_default: bool | None = None
    input_cost_per_million_tokens: float | None = None
    output_cost_per_million_tokens: float | None = None
    average_latency_ms: int | None = None
    quality_by_task: dict[str, float] | None = None
    sensitive_data_allowed: bool | None = None


class AIModelResponse(BaseModel):
    id: str
    provider_id: str
    name: str
    version: str
    enabled: bool
    is_default: bool
    input_cost_per_million_tokens: float
    output_cost_per_million_tokens: float
    average_latency_ms: int
    context_window: int
    supports_vision: bool
    supports_documents: bool
    supports_structured_output: bool
    sensitive_data_allowed: bool
    languages: list[Any]
    quality_by_task: dict[str, Any]
    availability_pct: float
    privacy_level: str

    model_config = {"from_attributes": True}
