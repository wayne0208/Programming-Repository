"""Course dataclass entity with multi-error field validation and JSON serialization."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from datamodel._validation import (
    collect_missing_fields,
    is_non_blank_str,
    is_plain_int,
)
from datamodel.constants import COURSE_CATEGORIES, DAYS, PERIODS
from datamodel.errors import ValidationError

__all__ = ["Course"]

REQUIRED_COURSE_FIELDS: tuple[str, ...] = (
    "code",
    "name",
    "credits",
    "category",
    "teacher",
    "capacity",
    "enrolled",
    "room",
    "slots",
)
STR_COURSE_FIELDS: frozenset[str] = frozenset({"code", "name", "teacher", "room"})
INT_COURSE_FIELD_MINIMUMS: dict[str, int] = {
    "credits": 1,
    "capacity": 1,
    "enrolled": 0,
}


def _is_valid_slot(slot: object) -> bool:
    return isinstance(slot, str) and len(slot) == 3 and slot[0] in DAYS and slot[1] == "-" and slot[2] in PERIODS


def _validate_slots(slots: object) -> list[str]:
    if not isinstance(slots, list):
        return ["slots 必須為 list[str]"]
    if not slots:
        return ["slots 不可為空清單"]

    errors: list[str] = []
    seen: set[str] = set()
    reported_duplicates: set[str] = set()
    for index, slot in enumerate(slots):
        if not _is_valid_slot(slot):
            errors.append(f"slots[{index}] 格式無效: {slot!r}，須為 '<day>-<period>'")
            continue
        if slot in seen:
            if slot not in reported_duplicates:
                errors.append(f"slots 不可包含重複時段: {slot!r}")
                reported_duplicates.add(slot)
        else:
            seen.add(slot)
    return errors


def _validate_course_field(field_name: str, value: object) -> list[str]:
    if field_name in STR_COURSE_FIELDS:
        return [] if is_non_blank_str(value) else [f"{field_name} 必須為非空字串"]
    if field_name == "category":
        if not is_non_blank_str(value):
            return ["category 必須為非空字串"]
        if value not in COURSE_CATEGORIES:
            return [f"category 必須為 {COURSE_CATEGORIES} 之一，收到: {value!r}"]
        return []
    if field_name in INT_COURSE_FIELD_MINIMUMS:
        minimum = INT_COURSE_FIELD_MINIMUMS[field_name]
        if not is_plain_int(value, minimum=minimum):
            return [f"{field_name} 必須為大於等於 {minimum} 的整數（不可為 bool）"]
        return []
    if field_name == "slots":
        return _validate_slots(value)
    return []


@dataclass
class Course:
    """Course entity representing a scheduled curriculum offering."""

    code: str
    name: str
    credits: int
    category: str
    teacher: str
    capacity: int
    enrolled: int
    room: str
    slots: list[str]

    def __post_init__(self) -> None:
        errors: list[str] = []
        for field_name in REQUIRED_COURSE_FIELDS:
            errors.extend(_validate_course_field(field_name, getattr(self, field_name)))

        if errors:
            raise ValidationError(errors)

        self.slots = list(self.slots)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Course:
        """Create a validated Course instance from a mapping."""
        if not isinstance(data, Mapping):
            raise ValidationError("Course 資料必須為 Mapping 型別")

        errors = collect_missing_fields(data, REQUIRED_COURSE_FIELDS)
        for field_name in REQUIRED_COURSE_FIELDS:
            if field_name in data:
                errors.extend(_validate_course_field(field_name, data[field_name]))

        if errors:
            raise ValidationError(errors)

        return cls(
            code=data["code"],
            name=data["name"],
            credits=data["credits"],
            category=data["category"],
            teacher=data["teacher"],
            capacity=data["capacity"],
            enrolled=data["enrolled"],
            room=data["room"],
            slots=list(data["slots"]),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize this Course into a JSON-compatible dictionary."""
        return {
            "code": self.code,
            "name": self.name,
            "credits": self.credits,
            "category": self.category,
            "teacher": self.teacher,
            "capacity": self.capacity,
            "enrolled": self.enrolled,
            "room": self.room,
            "slots": list(self.slots),
        }
