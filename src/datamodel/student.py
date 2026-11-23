"""Student entity model with field validation and dict serialization."""

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

__all__ = ["Student"]

REQUIRED_STUDENT_FIELDS: tuple[str, ...] = (
    "student_id",
    "name",
    "department",
    "credit_limit",
    "enrolled_courses",
    "enrolled_activities",
)
STR_STUDENT_FIELDS: frozenset[str] = frozenset({"student_id", "name", "department"})
LIST_STUDENT_FIELDS: frozenset[str] = frozenset({"enrolled_courses", "enrolled_activities"})


def _validate_student_field(field_name: str, value: object) -> list[str]:
    if field_name in STR_STUDENT_FIELDS:
        return [] if is_non_blank_str(value) else [f"{field_name} 必須為非空字串"]
    if field_name == "credit_limit":
        return [] if is_plain_int(value, minimum=1) else ["credit_limit 必須為大於 0 的整數"]
    if field_name in LIST_STUDENT_FIELDS:
        return validate_str_list(value, field_name)
    return []


@dataclass
class Student:
    """Represents a student and their enrolled courses and activities."""

    student_id: str
    name: str
    department: str
    credit_limit: int
    enrolled_courses: list[str]
    enrolled_activities: list[str]

    def __post_init__(self) -> None:
        errors: list[str] = []
        for field_name in REQUIRED_STUDENT_FIELDS:
            errors.extend(_validate_student_field(field_name, getattr(self, field_name)))

        if errors:
            raise ValidationError(errors)

        self.enrolled_courses = list(self.enrolled_courses)
        self.enrolled_activities = list(self.enrolled_activities)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Student:
        """Create a validated Student instance from a mapping."""
        if not isinstance(data, Mapping):
            raise ValidationError("學生資料必須為 Mapping 物件")

        errors = collect_missing_fields(data, REQUIRED_STUDENT_FIELDS)
        for field_name in REQUIRED_STUDENT_FIELDS:
            if field_name in data:
                errors.extend(_validate_student_field(field_name, data[field_name]))

        if errors:
            raise ValidationError(errors)

        return cls(
            student_id=data["student_id"],
            name=data["name"],
            department=data["department"],
            credit_limit=data["credit_limit"],
            enrolled_courses=list(data["enrolled_courses"]),
            enrolled_activities=list(data["enrolled_activities"]),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize the student into a JSON-compatible dictionary."""
        return {
            "student_id": self.student_id,
            "name": self.name,
            "department": self.department,
            "credit_limit": self.credit_limit,
            "enrolled_courses": list(self.enrolled_courses),
            "enrolled_activities": list(self.enrolled_activities),
        }
