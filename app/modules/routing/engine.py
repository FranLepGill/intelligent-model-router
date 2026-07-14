from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.config import get_settings
from app.models.entities import AIModel, RoutingPolicy, RoutingStrategy


@dataclass
class RoutingDecision:
    selected_model: AIModel | None
    reason: dict[str, Any] = field(default_factory=dict)
    discarded_models: dict[str, str] = field(default_factory=dict)


class RoutingEngine:
    """Deterministic router based on cost, latency, quality and constraints."""

    def __init__(
        self,
        *,
        quality_weight: float = 1.0,
        cost_weight: float = 0.6,
        latency_weight: float = 0.3,
        reliability_weight: float = 0.4,
    ) -> None:
        self.quality_weight = quality_weight
        self.cost_weight = cost_weight
        self.latency_weight = latency_weight
        self.reliability_weight = reliability_weight

    def select(
        self,
        *,
        models: list[AIModel],
        features: dict[str, Any],
        policy: RoutingPolicy | None,
        exclude_model_ids: set[str] | None = None,
        prefer_default: bool = False,
    ) -> RoutingDecision:
        settings = get_settings()
        exclude_model_ids = exclude_model_ids or set()
        discarded: dict[str, str] = {}
        candidates: list[AIModel] = []

        min_quality = (
            features.get("minimum_quality")
            if features.get("minimum_quality") is not None
            else (policy.minimum_quality if policy else 0.7)
        )
        max_cost = (
            features.get("max_cost_usd")
            if features.get("max_cost_usd") is not None
            else (policy.maximum_cost_usd if policy else None)
        )
        max_latency = (
            features.get("max_latency_ms")
            if features.get("max_latency_ms") is not None
            else (policy.maximum_latency_ms if policy else None)
        )
        strategy = policy.strategy if policy else RoutingStrategy.balanced
        estimated_tokens = int(features.get("estimated_tokens") or 64)

        for model in models:
            if model.id in exclude_model_ids:
                discarded[model.id] = "already_attempted"
                continue
            if not model.enabled:
                discarded[model.id] = "disabled"
                continue
            if features.get("contains_sensitive_data") and not model.sensitive_data_allowed:
                discarded[model.id] = "sensitive_data_not_allowed"
                continue
            if features.get("requires_vision") and not model.supports_vision:
                discarded[model.id] = "vision_not_supported"
                continue
            if estimated_tokens > model.context_window:
                discarded[model.id] = "context_window_exceeded"
                continue
            if max_latency is not None and model.average_latency_ms > max_latency:
                discarded[model.id] = "latency_above_maximum"
                continue

            expected_quality = self._expected_quality(model, features.get("task_type", "general"))
            estimated_cost = self._estimate_cost(model, estimated_tokens)
            if max_cost is not None and estimated_cost > max_cost:
                discarded[model.id] = "cost_above_maximum"
                continue
            if expected_quality < float(min_quality) and features.get("is_complex"):
                # Keep cheap models for complex tasks only if quality is close enough
                if expected_quality + 0.05 < float(min_quality):
                    discarded[model.id] = "quality_below_minimum"
                    continue

            candidates.append(model)

        if prefer_default and not exclude_model_ids:
            default = next((m for m in candidates if m.is_default), None)
            if default is None:
                default = next((m for m in models if m.id == settings.default_model_id and m.enabled), None)
            if default is not None and default.id not in discarded:
                return RoutingDecision(
                    selected_model=default,
                    discarded_models=discarded,
                    reason={
                        "strategy": "default_model",
                        "selected_model": default.id,
                        "required_quality": min_quality,
                        "expected_quality": self._expected_quality(
                            default, features.get("task_type", "general")
                        ),
                        "estimated_cost": self._estimate_cost(default, estimated_tokens),
                        "estimated_latency_ms": default.average_latency_ms,
                        "discarded_models": discarded,
                    },
                )

        if not candidates:
            return RoutingDecision(
                selected_model=None,
                discarded_models=discarded,
                reason={"error": "no_compatible_models", "discarded_models": discarded},
            )

        scored: list[tuple[float, AIModel, dict[str, Any]]] = []
        for model in candidates:
            expected_quality = self._expected_quality(model, features.get("task_type", "general"))
            estimated_cost = self._estimate_cost(model, estimated_tokens)
            reliability = model.availability_pct / 100.0
            score = self._score(strategy, expected_quality, estimated_cost, model.average_latency_ms, reliability)
            scored.append(
                (
                    score,
                    model,
                    {
                        "expected_quality": expected_quality,
                        "estimated_cost": estimated_cost,
                        "estimated_latency_ms": model.average_latency_ms,
                        "reliability": reliability,
                        "score": score,
                    },
                )
            )

        scored.sort(key=lambda item: item[0], reverse=True)
        best_score, best_model, metrics = scored[0]
        return RoutingDecision(
            selected_model=best_model,
            discarded_models=discarded,
            reason={
                "strategy": strategy.value if isinstance(strategy, RoutingStrategy) else strategy,
                "required_quality": min_quality,
                "selected_model": best_model.id,
                "score": best_score,
                **metrics,
                "discarded_models": discarded,
            },
        )

    def _expected_quality(self, model: AIModel, task_type: str) -> float:
        qualities = model.quality_by_task or {}
        if task_type in qualities:
            return float(qualities[task_type])
        if "general" in qualities:
            return float(qualities["general"])
        return 0.75

    def _estimate_cost(self, model: AIModel, input_tokens: int, output_tokens: int = 128) -> float:
        in_cost = (input_tokens / 1_000_000) * model.input_cost_per_million_tokens
        out_cost = (output_tokens / 1_000_000) * model.output_cost_per_million_tokens
        return round(in_cost + out_cost, 8)

    def _score(
        self,
        strategy: RoutingStrategy | str,
        quality: float,
        cost: float,
        latency_ms: int,
        reliability: float,
    ) -> float:
        if strategy == RoutingStrategy.cheapest:
            return -cost * 100 + quality
        if strategy == RoutingStrategy.fastest:
            return -latency_ms / 1000 + quality
        if strategy == RoutingStrategy.quality_first:
            return quality * 10 - cost - latency_ms / 10_000
        # balanced
        return (
            quality * self.quality_weight
            - cost * self.cost_weight * 100
            - (latency_ms / 1000) * self.latency_weight
            + reliability * self.reliability_weight
        )
