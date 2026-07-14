from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_client
from app.db import get_db
from app.models.entities import AIModel, Client
from app.schemas.models import AIModelCreate, AIModelResponse, AIModelUpdate

router = APIRouter()


@router.get("/models", response_model=list[AIModelResponse])
async def list_models(
    session: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Client, Depends(get_current_client)],
) -> list[AIModel]:
    result = await session.execute(select(AIModel).order_by(AIModel.id))
    return list(result.scalars().all())


@router.post("/models", response_model=AIModelResponse, status_code=status.HTTP_201_CREATED)
async def create_model(
    payload: AIModelCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Client, Depends(get_current_client)],
) -> AIModel:
    existing = await session.get(AIModel, payload.id)
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Model already exists")

    if payload.is_default:
        await session.execute(update(AIModel).values(is_default=False))

    model = AIModel(**payload.model_dump())
    session.add(model)
    await session.commit()
    await session.refresh(model)
    return model


@router.patch("/models/{model_id}", response_model=AIModelResponse)
async def update_model(
    model_id: str,
    payload: AIModelUpdate,
    session: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Client, Depends(get_current_client)],
) -> AIModel:
    model = await session.get(AIModel, model_id)
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")

    data = payload.model_dump(exclude_unset=True)
    if data.get("is_default"):
        await session.execute(update(AIModel).values(is_default=False))

    for key, value in data.items():
        setattr(model, key, value)

    await session.commit()
    await session.refresh(model)
    return model
