from __future__ import annotations

from typing import Any


def score_case(
    *,
    expected: dict[str, Any],
    obtained: dict[str, Any] | None,
    valid_output: bool,
) -> tuple[float, bool]:
    """Return (score 0..1, correct) for customer_support classification."""
    if not valid_output or not isinstance(obtained, dict):
        return 0.0, False

    expected_category = expected.get("category")
    obtained_category = obtained.get("category")
    category_ok = expected_category == obtained_category

    expected_priority = expected.get("priority")
    obtained_priority = obtained.get("priority")
    priority_ok = expected_priority is None or expected_priority == obtained_priority

    if category_ok and priority_ok:
        return 1.0, True
    if category_ok:
        return 0.75, True
    return 0.0, False
