from __future__ import annotations

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import (
    AIModel,
    ApiKey,
    Client,
    ClientStatus,
    ModelProvider,
    ProviderStatus,
    RoutingPolicy,
    RoutingStrategy,
)
from app.modules.authentication.service import generate_api_key

logger = structlog.get_logger()

# Stable demo key so local docs stay simple.
DEMO_RAW_API_KEY = "imr_demo_key_change_me_in_production_abc123"


async def seed_demo_data(session: AsyncSession) -> None:
    existing = await session.execute(select(Client).where(Client.name == "demo-customer-support"))
    if existing.scalar_one_or_none() is not None:
        logger.info("seed.skipped", reason="demo client already exists")
        return

    client = Client(
        name="demo-customer-support",
        status=ClientStatus.active,
        daily_budget_usd=20.0,
        requests_per_minute=100,
    )
    session.add(client)
    await session.flush()

    _, prefix, key_hash = generate_api_key()
    # Override with deterministic demo key for local development.
    from app.modules.authentication.service import hash_api_key

    key_hash = hash_api_key(DEMO_RAW_API_KEY)
    prefix = DEMO_RAW_API_KEY[:12]
    session.add(
        ApiKey(
            client_id=client.id,
            name="demo-key",
            key_prefix=prefix,
            key_hash=key_hash,
        )
    )

    session.add_all(
        [
            ModelProvider(
                id="provider-a",
                name="Provider A (economical)",
                status=ProviderStatus.active,
                configuration={"adapter": "mock"},
            ),
            ModelProvider(
                id="provider-b",
                name="Provider B (advanced)",
                status=ProviderStatus.active,
                configuration={"adapter": "mock"},
            ),
        ]
    )

    session.add_all(
        [
            AIModel(
                id="model-small",
                provider_id="provider-a",
                name="Small Economical",
                version="1.0",
                enabled=True,
                is_default=True,
                input_cost_per_million_tokens=0.20,
                output_cost_per_million_tokens=0.80,
                average_latency_ms=650,
                context_window=128000,
                supports_structured_output=True,
                sensitive_data_allowed=False,
                quality_by_task={"customer_support": 0.88, "general": 0.80},
                privacy_level="standard",
            ),
            AIModel(
                id="model-medium",
                provider_id="provider-b",
                name="Medium Advanced",
                version="1.0",
                enabled=True,
                is_default=False,
                input_cost_per_million_tokens=2.50,
                output_cost_per_million_tokens=10.0,
                average_latency_ms=1200,
                context_window=200000,
                supports_documents=True,
                supports_structured_output=True,
                sensitive_data_allowed=True,
                quality_by_task={"customer_support": 0.96, "legal_analysis": 0.94, "general": 0.93},
                privacy_level="strict",
            ),
        ]
    )

    session.add(
        RoutingPolicy(
            client_id=client.id,
            task_type="customer_support",
            strategy=RoutingStrategy.balanced,
            minimum_quality=0.85,
            maximum_cost_usd=0.05,
            maximum_latency_ms=5000,
            maximum_attempts=3,
            allow_fallback=True,
        )
    )

    await session.commit()
    logger.info(
        "seed.completed",
        client=client.name,
        demo_api_key=DEMO_RAW_API_KEY,
        models=["model-small", "model-medium"],
    )
