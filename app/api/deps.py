from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.entities import Client
from app.modules.authentication.service import authenticate_api_key


async def get_current_client(
    session: Annotated[AsyncSession, Depends(get_db)],
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> Client:
    return await authenticate_api_key(session, x_api_key)
