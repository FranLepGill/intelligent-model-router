from __future__ import annotations

from typing import Any

from app.schemas.inference import InferenceRequestCreate


def estimate_tokens(text: str) -> int:
    # Deterministic approximation (~4 chars/token)
    return max(1, len(text) // 4)


def extract_features(payload: InferenceRequestCreate) -> dict[str, Any]:
    text = payload.input
    return {
        "estimated_tokens": estimate_tokens(text),
        "text_length": len(text),
        "language": payload.language,
        "has_attachments": False,
        "file_type": None,
        "requires_vision": False,
        "output_format": payload.output_format,
        "priority": payload.priority,
        "contains_sensitive_data": payload.contains_sensitive_data,
        "max_cost_usd": payload.max_cost_usd,
        "max_latency_ms": payload.max_latency_ms,
        "minimum_quality": payload.minimum_quality,
        "task_type": payload.task_type,
        "is_complex": len(text) > 180
        or any(k in text.lower() for k in ("contrato", "compar", "analy", "analí")),
    }
