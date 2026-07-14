from typing import Any

from pydantic import BaseModel, Field


class EvaluationCaseResponse(BaseModel):
    id: str
    case_key: str
    input: str
    expected_output: dict[str, Any]
    difficulty: str
    language: str
    tags: list[Any]

    model_config = {"from_attributes": True}


class EvaluationDatasetResponse(BaseModel):
    id: str
    name: str
    task_type: str
    version: str
    description: str | None = None
    case_count: int = 0


class EvaluationDatasetDetailResponse(EvaluationDatasetResponse):
    cases: list[EvaluationCaseResponse] = Field(default_factory=list)


class EvaluationRunRequest(BaseModel):
    dataset_id: str = Field(default="customer-support-v1")
    model_ids: list[str] | None = None
    update_model_quality: bool = True


class ModelEvaluationMetrics(BaseModel):
    task_type: str
    cases: int
    accuracy: float
    average_score: float
    valid_json_rate: float
    error_rate: float
    average_latency_ms: float
    average_cost_usd: float
    total_cost_usd: float
    quality_by_difficulty: dict[str, float] = Field(default_factory=dict)
    quality_by_language: dict[str, float] = Field(default_factory=dict)


class EvaluationRunResponse(BaseModel):
    evaluation_id: str
    dataset_id: str
    status: str
    model_ids: list[str]
    update_model_quality: bool
    summary: dict[str, Any]
    started_at: str | None = None
    completed_at: str | None = None
    error_message: str | None = None
    result_count: int = 0


class EvaluationResultItem(BaseModel):
    case_key: str
    model_id: str
    score: float
    correct: bool
    valid_output: bool
    difficulty: str
    language: str
    latency_ms: int
    estimated_cost_usd: float
    obtained_category: str | None = None
    expected_category: str | None = None
    error_type: str | None = None
