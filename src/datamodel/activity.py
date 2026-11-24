"""Activity data model, slot calculation, and serialization."""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import date, datetime, time
from typing import Any, TypeVar

from datamodel._validation import (
    collect_missing_fields,
    is_non_blank_str,
    is_plain_int,
    validate_str_list,
)
from datamodel.constants import PERIOD_TIMES, PERIODS
from datamodel.errors import ValidationError

__all__ = ["Activity"]

PARSED_T = TypeVar("PARSED_T")
REQUIRED_ACTIVITY_FIELDS: tuple[str, ...] = (
    "activity_id",
    "name",
    "date",
    "start_time",
    "end_time",
    "category",
    "capacity",
    "registered",
    "required_equipment",
    "room",
)
STR_ACTIVITY_FIELDS: frozenset[str] = frozenset({"activity_id", "name", "category"})
INT_ACTIVITY_FIELD_MINIMUMS: dict[str, int] = {
    "capacity": 1,
    "registered": 0,
}
ISO_DATE_RE: re.Pattern[str] = re.compile(r"\d{4}-\d{2}-\d{2}")
ISO_TIME_RE: re.Pattern[str] = re.compile(r"\d{2}:\d{2}(?::\d{2}(?:\.\d{1,6})?)?")


def _is_naive_date(value: object) -> bool:
    return isinstance(value, date) and not isinstance(value, datetime)


def _is_naive_time(value: object) -> bool:
    return isinstance(value, time) and value.tzinfo is None


def _parse_iso_value(
    value: object,
    pattern: re.Pattern[str],
    parser: Callable[[str], PARSED_T],
    format_msg: str,
    invalid_msg: str,
) -> tuple[PARSED_T | None, str | None]:
    if not isinstance(value, str) or pattern.fullmatch(value) is None:
        return None, format_msg
    try:
        return parser(value), None
    except ValueError:
        return None, invalid_msg


def _validate_non_time_activity_field(field_name: str, value: object) -> list[str]:
    if field_name in STR_ACTIVITY_FIELDS:
        return [] if is_non_blank_str(value) else [f"{field_name} 必須為非空字串"]
    if field_name == "date":
        return [] if _is_naive_date(value) else ["date 必須為 datetime.date 型別（不可為 datetime）"]
    if field_name in INT_ACTIVITY_FIELD_MINIMUMS:
        minimum = INT_ACTIVITY_FIELD_MINIMUMS[field_name]
        return [] if is_plain_int(value, minimum=minimum) else [f"{field_name} 必須為大於或等於 {minimum} 的整數"]
    if field_name == "required_equipment":
        return validate_str_list(value, "required_equipment")
    if field_name == "room":
        if value is not None and not is_non_blank_str(value):
            return ["room 必須為 None 或非空字串"]
    return []


def _validate_time_range(
    start_value: object,
    end_value: object,
    *,
    check_start: bool,
    check_end: bool,
) -> list[str]:
    errors: list[str] = []
    start_valid = check_start and _is_naive_time(start_value)
    end_valid = check_end and _is_naive_time(end_value)

    if check_start and not start_valid:
        errors.append("start_time 必須為不含時區的 datetime.time 型別")
    if check_end and not end_valid:
        errors.append("end_time 必須為不含時區的 datetime.time 型別")
    if start_valid and end_valid and end_value <= start_value:  # type: ignore[operator]
        errors.append("end_time 必須晚於 start_time")
    return errors


@dataclass
class Activity:
    """Represent a scheduled campus activity with date, time range, and slot projection."""

    activity_id: str
    name: str
    date: date
    start_time: time
    end_time: time
    category: str
    capacity: int
    registered: int
    required_equipment: list[str]
    room: str | None

    def __post_init__(self) -> None:
        errors: list[str] = []
        for field_name in REQUIRED_ACTIVITY_FIELDS:
            if field_name not in {"start_time", "end_time"}:
                errors.extend(_validate_non_time_activity_field(field_name, getattr(self, field_name)))

        errors.extend(_validate_time_range(self.start_time, self.end_time, check_start=True, check_end=True))

        if errors:
            raise ValidationError(errors)

        self.required_equipment = list(self.required_equipment)

    @property
    def slots(self) -> list[str]:
        """Return covered '<weekday>-<period>' slots via open-interval overlap with PERIOD_TIMES."""
        weekday = str(self.date.isoweekday())
        covered: list[str] = []
        for period in PERIODS:
            p_start, p_end = PERIOD_TIMES[period]
            if max(self.start_time, p_start) < min(self.end_time, p_end):
                covered.append(f"{weekday}-{period}")
        return covered

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Activity:
        """Deserialize an Activity from a mapping, raising ValidationError on invalid input."""
        if not isinstance(data, Mapping):
            raise ValidationError("活動資料必須為 Mapping 型別")

        errors = collect_missing_fields(data, REQUIRED_ACTIVITY_FIELDS)
        parsed_times: dict[str, time] = {}
        parsed_date: date | None = None

        for field_name in REQUIRED_ACTIVITY_FIELDS:
            if field_name not in data:
                continue
            raw_value = data[field_name]
            if field_name == "date":
                parsed_date, date_err = _parse_iso_value(
                    raw_value,
                    ISO_DATE_RE,
                    date.fromisoformat,
                    "date 必須為 YYYY-MM-DD 格式的 ISO 字串",
                    "date 不是有效的日期",
                )
                if date_err is not None:
                    errors.append(date_err)
            elif field_name in {"start_time", "end_time"}:
                parsed_t, time_err = _parse_iso_value(
                    raw_value,
                    ISO_TIME_RE,
                    time.fromisoformat,
                    f"{field_name} 必須為 HH:MM 或 HH:MM:SS 格式的 ISO 字串",
                    f"{field_name} 不是有效的時間",
                )
                if time_err is not None:
                    errors.append(time_err)
                elif parsed_t is not None:
                    parsed_times[field_name] = parsed_t
            else:
                errors.extend(_validate_non_time_activity_field(field_name, raw_value))

        errors.extend(
            _validate_time_range(
                parsed_times.get("start_time"),
                parsed_times.get("end_time"),
                check_start="start_time" in parsed_times,
                check_end="end_time" in parsed_times,
            )
        )

        if errors:
            raise ValidationError(errors)

        assert parsed_date is not None
        return cls(
            activity_id=data["activity_id"],
            name=data["name"],
            date=parsed_date,
            start_time=parsed_times["start_time"],
            end_time=parsed_times["end_time"],
            category=data["category"],
            capacity=data["capacity"],
            registered=data["registered"],
            required_equipment=list(data["required_equipment"]),
            room=data["room"],
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize this Activity into a JSON-compatible dictionary."""
        return {
            "activity_id": self.activity_id,
            "name": self.name,
            "date": self.date.isoformat(),
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "category": self.category,
            "capacity": self.capacity,
            "registered": self.registered,
            "required_equipment": list(self.required_equipment),
            "room": self.room,
        }
