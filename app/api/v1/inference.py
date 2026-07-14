from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_client
from app.db import get_db
from app.models.entities import Client
from app.modules.inference.service import InferenceService
from app.schemas.inference import InferenceListItem, InferenceRequestCreate, InferenceResponse

router = APIRouter()
service = InferenceService()


@router.post("/inference", response_model=InferenceResponse)
async def create_inference(
    payload: InferenceRequestCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
    client: Annotated[Client, Depends(get_current_client)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> InferenceResponse:
    return await service.create_inference(
        session, client, payload, idempotency_key=idempotency_key
    )


@router.get("/requests/{request_id}", response_model=InferenceResponse)
async def get_request(
    request_id: str,
    session: Annotated[AsyncSession, Depends(get_db)],
    client: Annotated[Client, Depends(get_current_client)],
) -> InferenceResponse:
    return await service.get_request(session, client, request_id)


@router.get("/requests", response_model=list[InferenceListItem])
async def list_requests(
    session: Annotated[AsyncSession, Depends(get_db)],
    client: Annotated[Client, Depends(get_current_client)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[InferenceListItem]:
    rows = await service.list_requests(session, client, limit=limit)
    items: list[InferenceListItem] = []
    for row in rows:
        items.append(
            InferenceListItem(
                request_id=row.id,
                task_type=row.task_type,
                status=row.status.value if hasattr(row.status, "value") else str(row.status),
                selected_model=(row.routing_decision or {}).get("selected_model"),
                estimated_cost_usd=(row.usage or {}).get("estimated_cost_usd"),
                latency_ms=(row.usage or {}).get("latency_ms"),
                requested_at=row.requested_at.isoformat() if row.requested_at else "",
            )
        )
    return items
