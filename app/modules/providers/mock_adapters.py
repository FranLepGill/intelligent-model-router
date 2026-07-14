from __future__ import annotations

import asyncio
import hashlib
import re
import time
from typing import Any

from app.modules.providers.base import ProviderAdapter, ProviderResponse

CATEGORY_PATTERNS: list[tuple[str, str]] = [
    (r"contrase[nñ]a|password|clave", "password_problem"),
    (r"dos veces|duplicad|cobraron.*misma|double.?charg", "duplicate_charge"),
    (r"reembolso|devolver|refund", "refund_problem"),
    (r"bloquead|suspended|locked", "account_blocked"),
]


def classify_support(text: str) -> dict[str, Any]:
    lowered = text.lower()
    for pattern, category in CATEGORY_PATTERNS:
        if re.search(pattern, lowered):
            priority = "high" if category in {"duplicate_charge", "account_blocked"} else "medium"
            return {
                "category": category,
                "priority": priority,
                "suggested_response": _suggestion(category),
            }
    return {
        "category": "general_question",
        "priority": "low",
        "suggested_response": "Un agente revisará tu consulta y te responderá a la brevedad.",
    }


def _suggestion(category: str) -> str:
    return {
        "password_problem": "Podés restablecer tu contraseña desde el enlace 'Olvidé mi contraseña'.",
        "duplicate_charge": "Revisaremos el cobro duplicado y te confirmaremos el resultado.",
        "refund_problem": "Iniciaremos la gestión del reembolso con el equipo de facturación.",
        "account_blocked": "Verificaremos el estado de tu cuenta y los pasos para desbloquearla.",
    }.get(category, "Gracias por contactarnos. Estamos revisando tu caso.")


def estimate_tokens(text: str) -> int:
    return max(1, len(text.split()))


class MockProviderAAdapter(ProviderAdapter):
    """Economical mock model (provider-a). Occasionally returns invalid JSON on complex prompts."""

    provider_id = "provider-a"

    async def complete(
        self,
        *,
        model_id: str,
        prompt: str,
        task_type: str,
        output_format: str = "json",
        language: str = "es",
    ) -> ProviderResponse:
        started = time.perf_counter()
        await asyncio.sleep(0.05)

        # Deterministic failure for forced demo scenarios
        if "FORCE_PROVIDER_A_DOWN" in prompt:
            return ProviderResponse(
                content={},
                input_tokens=estimate_tokens(prompt),
                output_tokens=0,
                latency_ms=int((time.perf_counter() - started) * 1000),
                error_type="provider_unavailable",
                error_message="Simulated provider-a outage",
            )

        # Small model fails structured output on long/complex prompts
        complexity = len(prompt) > 180 or "contrato" in prompt.lower() or "compar" in prompt.lower()
        if model_id == "model-small" and ("FORCE_INVALID_JSON" in prompt or complexity):
            latency = int((time.perf_counter() - started) * 1000)
            return ProviderResponse(
                content="respuesta no estructurada del modelo economico",
                input_tokens=estimate_tokens(prompt),
                output_tokens=12,
                latency_ms=latency,
                raw={"model": model_id},
            )

        payload = classify_support(prompt)
        payload["model_note"] = "provider-a"
        latency = int((time.perf_counter() - started) * 1000) + (80 if model_id == "model-small" else 250)
        out = payload if output_format == "json" else str(payload)
        return ProviderResponse(
            content=out,
            input_tokens=estimate_tokens(prompt),
            output_tokens=estimate_tokens(str(payload)),
            latency_ms=latency,
            raw={"model": model_id, "provider": self.provider_id},
        )


class MockProviderBAdapter(ProviderAdapter):
    """Stronger mock model (provider-b)."""

    provider_id = "provider-b"

    async def complete(
        self,
        *,
        model_id: str,
        prompt: str,
        task_type: str,
        output_format: str = "json",
        language: str = "es",
    ) -> ProviderResponse:
        started = time.perf_counter()
        await asyncio.sleep(0.12)

        if "FORCE_PROVIDER_B_DOWN" in prompt:
            return ProviderResponse(
                content={},
                input_tokens=estimate_tokens(prompt),
                output_tokens=0,
                latency_ms=int((time.perf_counter() - started) * 1000),
                error_type="timeout",
                error_message="Simulated provider-b timeout",
            )

        payload = classify_support(prompt)
        # Slightly smarter: attach confidence hash for demos
        digest = hashlib.sha1(prompt.encode()).hexdigest()[:8]
        payload["confidence"] = 0.93
        payload["analysis_id"] = digest
        payload["model_note"] = "provider-b"
        latency = int((time.perf_counter() - started) * 1000) + 400
        out = payload if output_format == "json" else str(payload)
        return ProviderResponse(
            content=out,
            input_tokens=estimate_tokens(prompt),
            output_tokens=estimate_tokens(str(payload)) + 20,
            latency_ms=latency,
            raw={"model": model_id, "provider": self.provider_id},
        )
