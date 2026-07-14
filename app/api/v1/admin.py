from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_client
from app.db import get_db
from app.models.entities import Client, InferenceRequest, RequestStatus
from app.schemas.admin import ClientProfileResponse, DashboardMetrics

router = APIRouter()


@router.get("/me", response_model=ClientProfileResponse)
async def get_me(
    session: Annotated[AsyncSession, Depends(get_db)],
    client: Annotated[Client, Depends(get_current_client)],
) -> ClientProfileResponse:
    result = await session.execute(
        select(Client)
        .options(selectinload(Client.policies), selectinload(Client.api_keys))
        .where(Client.id == client.id)
    )
    loaded = result.scalar_one()
    return ClientProfileResponse(
        id=str(loaded.id),
        name=loaded.name,
        status=loaded.status.value if hasattr(loaded.status, "value") else str(loaded.status),
        daily_budget_usd=loaded.daily_budget_usd,
        requests_per_minute=loaded.requests_per_minute,
        created_at=loaded.created_at.isoformat() if loaded.created_at else None,
        policies=[
            {
                "task_type": p.task_type,
                "strategy": p.strategy.value if hasattr(p.strategy, "value") else str(p.strategy),
                "minimum_quality": p.minimum_quality,
                "maximum_cost_usd": p.maximum_cost_usd,
                "maximum_latency_ms": p.maximum_latency_ms,
                "maximum_attempts": p.maximum_attempts,
                "allow_fallback": p.allow_fallback,
            }
            for p in loaded.policies
        ],
        api_key_prefixes=[k.key_prefix for k in loaded.api_keys if k.revoked_at is None],
    )


@router.get("/admin/metrics", response_model=DashboardMetrics)
async def get_dashboard_metrics(
    session: Annotated[AsyncSession, Depends(get_db)],
    client: Annotated[Client, Depends(get_current_client)],
) -> DashboardMetrics:
    result = await session.execute(
        select(InferenceRequest)
        .where(InferenceRequest.client_id == client.id)
        .order_by(InferenceRequest.requested_at.desc())
        .limit(500)
    )
    rows = list(result.scalars().all())

    total = len(rows)
    successful = sum(1 for r in rows if r.status == RequestStatus.completed)
    failed = sum(1 for r in rows if r.status == RequestStatus.failed)
    costs = [float((r.usage or {}).get("estimated_cost_usd") or 0) for r in rows]
    latencies = [float((r.usage or {}).get("latency_ms") or 0) for r in rows if r.usage]

    model_usage: dict[str, int] = {}
    provider_errors: dict[str, int] = {}
    fallbacks = 0
    for r in rows:
        decision = r.routing_decision or {}
        model = decision.get("selected_model")
        if model:
            model_usage[str(model)] = model_usage.get(str(model), 0) + 1
        if decision.get("fallback_used"):
            fallbacks += 1
        if r.status == RequestStatus.failed:
            provider = str(decision.get("provider") or "unknown")
            provider_errors[provider] = provider_errors.get(provider, 0) + 1

    most_used = None
    if model_usage:
        most_used = max(model_usage.items(), key=lambda item: item[1])[0]

    recent: list[dict[str, Any]] = [
        {
            "request_id": r.id,
            "task_type": r.task_type,
            "status": r.status.value if hasattr(r.status, "value") else str(r.status),
            "selected_model": (r.routing_decision or {}).get("selected_model"),
            "provider": (r.routing_decision or {}).get("provider"),
            "estimated_cost_usd": (r.usage or {}).get("estimated_cost_usd"),
            "latency_ms": (r.usage or {}).get("latency_ms"),
            "fallback_used": bool((r.routing_decision or {}).get("fallback_used")),
            "requested_at": r.requested_at.isoformat() if r.requested_at else None,
        }
        for r in rows[:10]
    ]

    return DashboardMetrics(
        total_requests=total,
        successful_requests=successful,
        failed_requests=failed,
        total_cost_usd=round(sum(costs), 8),
        average_latency_ms=round(sum(latencies) / len(latencies), 2) if latencies else 0.0,
        most_used_model=most_used,
        provider_error_counts=provider_errors,
        model_usage=model_usage,
        fallback_rate=round(fallbacks / total, 4) if total else 0.0,
        recent_requests=recent,
    )
