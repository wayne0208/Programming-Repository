"""Internal shared validation helpers for datamodel entities."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

__all__ = [
    "collect_missing_fields",
    "is_non_blank_str",
    "is_plain_int",
    "validate_str_list",
]


def is_non_blank_str(value: object) -> bool:
    """Return True when value is a str containing at least one non-whitespace character."""
    return isinstance(value, str) and value.strip() != ""


def is_plain_int(value: object, *, minimum: int = 0) -> bool:
    """Return True when value is an int (excluding bool) >= minimum."""
    return isinstance(value, int) and not isinstance(value, bool) and value >= minimum


def validate_str_list(value: object, field_name: str) -> list[str]:
    """Validate that value is a list of unique, non-blank strings."""
    if not isinstance(value, list):
        return [f"{field_name} 必須為 list[str]"]

    seen: set[str] = set()
    has_invalid_item = False
    duplicates: list[str] = []

    for item in value:
        if not is_non_blank_str(item):
            has_invalid_item = True
        elif item in seen:
            if item not in duplicates:
                duplicates.append(item)
        else:
            seen.add(item)

    errors: list[str] = []
    if has_invalid_item:
        errors.append(f"{field_name} 的所有元素必須為非空字串")
    if duplicates:
        errors.append(f"{field_name} 不可包含重複項目: {', '.join(duplicates)}")
    return errors


def collect_missing_fields(data: Mapping[str, Any], required_fields: tuple[str, ...]) -> list[str]:
    """Return missing required field error messages in field declaration order."""
    return [f"缺少必要欄位: {field}" for field in required_fields if field not in data]
