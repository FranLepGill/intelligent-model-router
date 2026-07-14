from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ValidationResult:
    ok: bool
    errors: list[str] = field(default_factory=list)
    normalized: dict[str, Any] | None = None


class ResponseValidator:
    REQUIRED_SUPPORT_FIELDS = {"category", "priority", "suggested_response"}

    def validate(self, content: Any, *, output_format: str, task_type: str) -> ValidationResult:
        if content is None:
            return ValidationResult(ok=False, errors=["empty_response"])

        if output_format == "json":
            if not isinstance(content, dict):
                return ValidationResult(ok=False, errors=["invalid_json_structure"])
            if not content:
                return ValidationResult(ok=False, errors=["empty_json"])

            errors: list[str] = []
            if task_type == "customer_support":
                missing = self.REQUIRED_SUPPORT_FIELDS - set(content.keys())
                if missing:
                    errors.append(f"missing_fields:{','.join(sorted(missing))}")
                category = content.get("category")
                if isinstance(category, str) and not category.strip():
                    errors.append("empty_category")

            if errors:
                return ValidationResult(ok=False, errors=errors)
            return ValidationResult(ok=True, normalized=content)

        # text
        if not str(content).strip():
            return ValidationResult(ok=False, errors=["empty_text"])
        return ValidationResult(ok=True, normalized={"text": str(content)})
