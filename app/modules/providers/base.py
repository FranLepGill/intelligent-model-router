from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProviderResponse:
    content: dict[str, Any] | str
    input_tokens: int
    output_tokens: int
    latency_ms: int
    raw: dict[str, Any] = field(default_factory=dict)
    error_type: str | None = None
    error_message: str | None = None

    @property
    def ok(self) -> bool:
        return self.error_type is None


class ProviderAdapter(ABC):
    provider_id: str

    @abstractmethod
    async def complete(
        self,
        *,
        model_id: str,
        prompt: str,
        task_type: str,
        output_format: str = "json",
        language: str = "es",
    ) -> ProviderResponse:
        raise NotImplementedError
