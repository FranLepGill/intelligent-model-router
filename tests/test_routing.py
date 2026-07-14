from app.models.entities import AIModel, RoutingPolicy, RoutingStrategy
from app.modules.routing.engine import RoutingEngine


def _model(**kwargs) -> AIModel:
    defaults = dict(
        id="m",
        provider_id="provider-a",
        name="M",
        version="1",
        enabled=True,
        is_default=False,
        input_cost_per_million_tokens=1.0,
        output_cost_per_million_tokens=2.0,
        average_latency_ms=800,
        context_window=128000,
        supports_vision=False,
        supports_documents=False,
        supports_structured_output=True,
        sensitive_data_allowed=False,
        languages=["es"],
        quality_by_task={"customer_support": 0.9},
        availability_pct=99.0,
        max_rpm=60,
        privacy_level="standard",
    )
    defaults.update(kwargs)
    return AIModel(**defaults)


def test_router_prefers_cheaper_when_quality_is_enough():
    engine = RoutingEngine()
    small = _model(
        id="model-small",
        input_cost_per_million_tokens=0.2,
        output_cost_per_million_tokens=0.8,
        quality_by_task={"customer_support": 0.9},
        average_latency_ms=600,
    )
    large = _model(
        id="model-medium",
        provider_id="provider-b",
        input_cost_per_million_tokens=5.0,
        output_cost_per_million_tokens=15.0,
        quality_by_task={"customer_support": 0.97},
        average_latency_ms=1400,
        sensitive_data_allowed=True,
    )
    policy = RoutingPolicy(
        task_type="customer_support",
        strategy=RoutingStrategy.cheapest,
        minimum_quality=0.85,
        maximum_cost_usd=1.0,
        maximum_latency_ms=5000,
        maximum_attempts=3,
        allow_fallback=True,
    )
    decision = engine.select(
        models=[small, large],
        features={
            "task_type": "customer_support",
            "estimated_tokens": 40,
            "contains_sensitive_data": False,
            "is_complex": False,
            "minimum_quality": 0.85,
        },
        policy=policy,
    )
    assert decision.selected_model is not None
    assert decision.selected_model.id == "model-small"


def test_sensitive_data_filters_unauthorized_models():
    engine = RoutingEngine()
    small = _model(id="model-small", sensitive_data_allowed=False)
    medium = _model(
        id="model-medium",
        provider_id="provider-b",
        sensitive_data_allowed=True,
        quality_by_task={"customer_support": 0.95},
    )
    decision = engine.select(
        models=[small, medium],
        features={
            "task_type": "customer_support",
            "estimated_tokens": 40,
            "contains_sensitive_data": True,
            "is_complex": False,
            "minimum_quality": 0.85,
        },
        policy=None,
    )
    assert decision.selected_model is not None
    assert decision.selected_model.id == "model-medium"
    assert decision.discarded_models["model-small"] == "sensitive_data_not_allowed"
