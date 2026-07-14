from __future__ import annotations

from fastapi import HTTPException, status

from app.config import get_settings
from app.modules.providers.base import ProviderAdapter
from app.modules.providers.mock_adapters import MockProviderAAdapter, MockProviderBAdapter

_adapters: dict[str, ProviderAdapter] | None = None


def _build_adapters() -> dict[str, ProviderAdapter]:
    settings = get_settings()
    # Phase 1: mock adapters by default. Real HTTP adapters can replace these later.
    if settings.use_mock_providers or not settings.provider_a_api_key:
        return {
            "provider-a": MockProviderAAdapter(),
            "provider-b": MockProviderBAdapter(),
        }
    return {
        "provider-a": MockProviderAAdapter(),
        "provider-b": MockProviderBAdapter(),
    }


def get_provider_adapter(provider_id: str) -> ProviderAdapter:
    global _adapters
    if _adapters is None:
        _adapters = _build_adapters()
    adapter = _adapters.get(provider_id)
    if adapter is None:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"No adapter registered for provider '{provider_id}'",
        )
    return adapter
