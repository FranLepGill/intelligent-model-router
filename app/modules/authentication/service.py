from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.models.entities import ApiKey, Client, ClientStatus


def hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def generate_api_key() -> tuple[str, str, str]:
    """Return (raw_key, key_prefix, key_hash)."""
    settings = get_settings()
    raw = f"{settings.api_key_prefix}{secrets.token_urlsafe(32)}"
    prefix = raw[:12]
    return raw, prefix, hash_api_key(raw)


async def authenticate_api_key(session: AsyncSession, raw_key: str | None) -> Client:
    if not raw_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Provide X-API-Key header.",
        )

    key_hash = hash_api_key(raw_key)
    result = await session.execute(
        select(ApiKey)
        .options(selectinload(ApiKey.client))
        .where(ApiKey.key_hash == key_hash)
    )
    api_key = result.scalar_one_or_none()
    if api_key is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")

    if api_key.revoked_at is not None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key revoked")

    if api_key.expires_at is not None and api_key.expires_at < datetime.now(UTC):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key expired")

    client = api_key.client
    if client.status != ClientStatus.active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Client is not active")

    return client
