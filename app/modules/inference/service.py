from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.models.entities import (
    AIModel,
    AttemptStatus,
    Client,
    InferenceAttempt,
    InferenceRequest,
    RequestStatus,
    RoutingPolicy,
)
from app.modules.providers.registry import get_provider_adapter
from app.modules.routing.engine import RoutingEngine
from app.modules.routing.features import extract_features
from app.modules.validation.response import ResponseValidator
from app.schemas.inference import (
    InferenceRequestCreate,
    InferenceResponse,
    RoutingInfo,
    UsageInfo,
)


class InferenceService:
    def __init__(self) -> None:
        self.router = RoutingEngine()
        self.validator = ResponseValidator()
        self.settings = get_settings()

    async def create_inference(
        self,
        session: AsyncSession,
        client: Client,
        payload: InferenceRequestCreate,
        idempotency_key: str | None = None,
    ) -> InferenceResponse:
        if idempotency_key:
            existing = await self._get_by_idempotency(session, client.id, idempotency_key)
            if existing is not None:
                return self._to_response(existing)

        if len(payload.input) > self.settings.max_input_chars:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Input exceeds maximum allowed size",
            )

        features = extract_features(payload)
        request_id = f"req_{uuid.uuid4().hex[:12]}"

        request = InferenceRequest(
            id=request_id,
            client_id=client.id,
            task_type=payload.task_type,
            input_text=payload.input,
            language=payload.language,
            priority=payload.priority,
            status=RequestStatus.running,
            maximum_cost_usd=payload.max_cost_usd,
            minimum_quality=payload.minimum_quality,
            maximum_latency_ms=payload.max_latency_ms,
            contains_sensitive_data=payload.contains_sensitive_data,
            output_format=payload.output_format,
            idempotency_key=idempotency_key,
            features=features,
        )
        session.add(request)
        await session.flush()

        policy = await self._get_policy(session, client.id, payload.task_type)
        models = await self._list_models(session)
        max_attempts = policy.maximum_attempts if policy else 3
        allow_fallback = policy.allow_fallback if policy else True

        attempted: set[str] = set()
        last_error: str | None = None
        total_latency = 0
        total_input_tokens = 0
        total_output_tokens = 0
        total_cost = 0.0
        selected_model_id: str | None = None
        selected_provider: str | None = None
        decision_reason: dict[str, Any] = {}

        for attempt_number in range(1, max_attempts + 1):
            # First attempt: default model (acceptance criteria). Later: full scoring + escalate.
            prefer_default = attempt_number == 1 and not attempted
            decision = self.router.select(
                models=models,
                features=features,
                policy=policy,
                exclude_model_ids=attempted,
                prefer_default=prefer_default,
            )
            decision_reason = decision.reason
            model = decision.selected_model
            if model is None:
                last_error = "No compatible model available"
                break

            selected_model_id = model.id
            selected_provider = model.provider_id
            attempted.add(model.id)

            adapter = get_provider_adapter(model.provider_id)
            provider_result = await adapter.complete(
                model_id=model.id,
                prompt=payload.input,
                task_type=payload.task_type,
                output_format=payload.output_format,
                language=payload.language,
            )

            cost = self._cost(model, provider_result.input_tokens, provider_result.output_tokens)
            total_latency += provider_result.latency_ms
            total_input_tokens += provider_result.input_tokens
            total_output_tokens += provider_result.output_tokens
            total_cost += cost

            if not provider_result.ok:
                session.add(
                    InferenceAttempt(
                        request_id=request_id,
                        model_id=model.id,
                        provider_id=model.provider_id,
                        attempt_number=attempt_number,
                        status=AttemptStatus.failed,
                        latency_ms=provider_result.latency_ms,
                        input_tokens=provider_result.input_tokens,
                        output_tokens=provider_result.output_tokens,
                        estimated_cost_usd=cost,
                        error_type=provider_result.error_type,
                        error_message=provider_result.error_message,
                        raw_response=provider_result.raw,
                    )
                )
                last_error = provider_result.error_message or provider_result.error_type
                if not allow_fallback:
                    break
                continue

            validation = self.validator.validate(
                provider_result.content,
                output_format=payload.output_format,
                task_type=payload.task_type,
            )
            if not validation.ok:
                session.add(
                    InferenceAttempt(
                        request_id=request_id,
                        model_id=model.id,
                        provider_id=model.provider_id,
                        attempt_number=attempt_number,
                        status=AttemptStatus.invalid_response,
                        latency_ms=provider_result.latency_ms,
                        input_tokens=provider_result.input_tokens,
                        output_tokens=provider_result.output_tokens,
                        estimated_cost_usd=cost,
                        error_type="invalid_response",
                        error_message=";".join(validation.errors),
                        raw_response={
                            "content": provider_result.content
                            if isinstance(provider_result.content, dict)
                            else {"text": str(provider_result.content)}
                        },
                    )
                )
                last_error = ";".join(validation.errors)
                if not allow_fallback:
                    break
                continue

            session.add(
                InferenceAttempt(
                    request_id=request_id,
                    model_id=model.id,
                    provider_id=model.provider_id,
                    attempt_number=attempt_number,
                    status=AttemptStatus.success,
                    latency_ms=provider_result.latency_ms,
                    input_tokens=provider_result.input_tokens,
                    output_tokens=provider_result.output_tokens,
                    estimated_cost_usd=cost,
                    raw_response={"content": validation.normalized},
                )
            )

            request.status = RequestStatus.completed
            request.output = validation.normalized
            request.routing_decision = {
                **decision_reason,
                "attempts": attempt_number,
                "fallback_used": attempt_number > 1,
                "selected_model": model.id,
                "provider": model.provider_id,
            }
            request.usage = {
                "input_tokens": total_input_tokens,
                "output_tokens": total_output_tokens,
                "latency_ms": total_latency,
                "estimated_cost_usd": round(total_cost, 8),
            }
            request.completed_at = datetime.now(UTC)
            await session.commit()
            await session.refresh(request)
            return self._to_response(request)

        request.status = RequestStatus.failed
        request.error_message = last_error or "Inference failed"
        request.routing_decision = {
            **decision_reason,
            "attempts": len(attempted),
            "fallback_used": len(attempted) > 1,
            "selected_model": selected_model_id,
            "provider": selected_provider,
        }
        request.usage = {
            "input_tokens": total_input_tokens,
            "output_tokens": total_output_tokens,
            "latency_ms": total_latency,
            "estimated_cost_usd": round(total_cost, 8),
        }
        request.completed_at = datetime.now(UTC)
        await session.commit()
        await session.refresh(request)
        return self._to_response(request)

    async def get_request(
        self, session: AsyncSession, client: Client, request_id: str
    ) -> InferenceResponse:
        result = await session.execute(
            select(InferenceRequest)
            .options(selectinload(InferenceRequest.attempts))
            .where(InferenceRequest.id == request_id, InferenceRequest.client_id == client.id)
        )
        request = result.scalar_one_or_none()
        if request is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
        return self._to_response(request)

    async def list_requests(
        self, session: AsyncSession, client: Client, limit: int = 50
    ) -> list[InferenceRequest]:
        result = await session.execute(
            select(InferenceRequest)
            .where(InferenceRequest.client_id == client.id)
            .order_by(InferenceRequest.requested_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def _get_by_idempotency(
        self, session: AsyncSession, client_id: Any, idempotency_key: str
    ) -> InferenceRequest | None:
        result = await session.execute(
            select(InferenceRequest)
            .options(selectinload(InferenceRequest.attempts))
            .where(
                InferenceRequest.client_id == client_id,
                InferenceRequest.idempotency_key == idempotency_key,
            )
        )
        return result.scalar_one_or_none()

    async def _get_policy(
        self, session: AsyncSession, client_id: Any, task_type: str
    ) -> RoutingPolicy | None:
        result = await session.execute(
            select(RoutingPolicy).where(
                RoutingPolicy.client_id == client_id,
                RoutingPolicy.task_type == task_type,
            )
        )
        return result.scalar_one_or_none()

    async def _list_models(self, session: AsyncSession) -> list[AIModel]:
        result = await session.execute(select(AIModel).where(AIModel.enabled.is_(True)))
        return list(result.scalars().all())

    def _cost(self, model: AIModel, input_tokens: int, output_tokens: int) -> float:
        in_cost = (input_tokens / 1_000_000) * model.input_cost_per_million_tokens
        out_cost = (output_tokens / 1_000_000) * model.output_cost_per_million_tokens
        return round(in_cost + out_cost, 8)

    def _to_response(self, request: InferenceRequest) -> InferenceResponse:
        routing = None
        if request.routing_decision:
            routing = RoutingInfo(
                selected_model=str(request.routing_decision.get("selected_model") or ""),
                provider=str(request.routing_decision.get("provider") or ""),
                attempts=int(request.routing_decision.get("attempts") or 0),
                fallback_used=bool(request.routing_decision.get("fallback_used")),
                reason=request.routing_decision,
            )
        usage = None
        if request.usage:
            usage = UsageInfo(
                input_tokens=int(request.usage.get("input_tokens") or 0),
                output_tokens=int(request.usage.get("output_tokens") or 0),
                latency_ms=int(request.usage.get("latency_ms") or 0),
                estimated_cost_usd=float(request.usage.get("estimated_cost_usd") or 0),
            )
        return InferenceResponse(
            request_id=request.id,
            status=request.status.value if hasattr(request.status, "value") else str(request.status),
            output=request.output,
            routing=routing,
            usage=usage,
            error=request.error_message,
        )
