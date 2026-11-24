"""Classroom data entity with field validation and dictionary serialization."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from datamodel._validation import (
    collect_missing_fields,
    is_non_blank_str,
    is_plain_int,
    validate_str_list,
)
from datamodel.errors import ValidationError

__all__ = ["Classroom"]

REQUIRED_CLASSROOM_FIELDS: tuple[str, ...] = ("room_id", "capacity", "equipment")


def _validate_classroom_field(field_name: str, value: object) -> list[str]:
    if field_name == "room_id":
        return [] if is_non_blank_str(value) else ["room_id 必須為非空字串"]
    if field_name == "capacity":
        return [] if is_plain_int(value, minimum=1) else ["capacity 必須為大於等於 1 的整數（不可為布林值）"]
    if field_name == "equipment":
        return validate_str_list(value, "equipment")
    return []


@dataclass
class Classroom:
    """Represents a physical classroom with seating capacity and equipment."""

    room_id: str
    capacity: int
    equipment: list[str]

    def __post_init__(self) -> None:
        errors: list[str] = []
        for field_name in REQUIRED_CLASSROOM_FIELDS:
            errors.extend(_validate_classroom_field(field_name, getattr(self, field_name)))

        if errors:
            raise ValidationError(errors)

        self.equipment = list(self.equipment)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Classroom:
        """Create a validated Classroom instance from a mapping."""
        if not isinstance(data, Mapping):
            raise ValidationError(["Classroom 資料必須為 Mapping 格式"])

        errors = collect_missing_fields(data, REQUIRED_CLASSROOM_FIELDS)
        for field_name in REQUIRED_CLASSROOM_FIELDS:
            if field_name in data:
                errors.extend(_validate_classroom_field(field_name, data[field_name]))

        if errors:
            raise ValidationError(errors)

        return cls(
            room_id=data["room_id"],
            capacity=data["capacity"],
            equipment=list(data["equipment"]),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize the classroom to a JSON-compatible dictionary."""
        return {
            "room_id": self.room_id,
            "capacity": self.capacity,
            "equipment": list(self.equipment),
        }
