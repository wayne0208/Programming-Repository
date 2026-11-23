"""Unit tests for Course entity validation, serialization, and seed courses JSON."""

import json
from pathlib import Path
from types import MappingProxyType
from typing import Any

import pytest

from datamodel.constants import COURSE_CATEGORIES, DAYS, PERIODS
from datamodel.course import Course
from datamodel.errors import ScheduleError, ValidationError

SEED_COURSES_PATH = Path(__file__).resolve().parents[2] / "src" / "datamodel" / "seed" / "courses.json"


def _make_valid_course_payload(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "code": "CS101",
        "name": "計算機程式",
        "credits": 3,
        "category": "必修",
        "teacher": "王小明",
        "capacity": 40,
        "enrolled": 35,
        "room": "06206",
        "slots": ["1-1", "1-2"],
    }
    payload.update(overrides)
    return payload


def _make_valid_course(**overrides: Any) -> Course:
    return Course(**_make_valid_course_payload(**overrides))


def test_course_valid_construction_and_boundary_values() -> None:
    course = Course(
        code="CS999",
        name="進階專題",
        credits=1,
        category="選修",
        teacher="林老師",
        capacity=1,
        enrolled=0,
        room="03303",
        slots=["1-1", "7-c"],
    )

    assert course.code == "CS999"
    assert course.name == "進階專題"
    assert course.credits == 1
    assert course.category == "選修"
    assert course.teacher == "林老師"
    assert course.capacity == 1
    assert course.enrolled == 0
    assert course.room == "03303"
    assert course.slots == ["1-1", "7-c"]


def test_course_allows_enrolled_greater_than_capacity() -> None:
    course = _make_valid_course(capacity=30, enrolled=35)

    assert course.capacity == 30
    assert course.enrolled == 35


@pytest.mark.parametrize("category", COURSE_CATEGORIES)
def test_course_accepts_all_domain_categories(category: str) -> None:
    course = _make_valid_course(category=category)
    assert course.category == category


@pytest.mark.parametrize("day", list(DAYS))
@pytest.mark.parametrize("period", list(PERIODS))
def test_course_accepts_all_valid_day_and_period_slots(day: str, period: str) -> None:
    slot = f"{day}-{period}"
    course = _make_valid_course(slots=[slot])
    assert course.slots == [slot]


def test_course_defensive_copies_slots_on_init_from_dict_and_to_dict() -> None:
    init_slots = ["1-1", "2-2"]
    course = _make_valid_course(slots=init_slots)
    init_slots.append("3-3")
    assert course.slots == ["1-1", "2-2"]

    payload = _make_valid_course_payload(slots=["4-5"])
    from_dict_course = Course.from_dict(payload)
    payload["slots"].append("4-6")
    assert from_dict_course.slots == ["4-5"]

    exported = from_dict_course.to_dict()
    exported["slots"].append("5-1")
    assert from_dict_course.slots == ["4-5"]


def test_course_to_dict_and_from_dict_round_trip_json() -> None:
    course = _make_valid_course(slots=["2-8", "2-9", "2-a"])
    exported = course.to_dict()

    assert exported == {
        "code": "CS101",
        "name": "計算機程式",
        "credits": 3,
        "category": "必修",
        "teacher": "王小明",
        "capacity": 40,
        "enrolled": 35,
        "room": "06206",
        "slots": ["2-8", "2-9", "2-a"],
    }

    round_tripped = Course.from_dict(json.loads(json.dumps(exported, ensure_ascii=False)))
    assert round_tripped == course


def test_course_from_dict_accepts_non_dict_mapping() -> None:
    mapping = MappingProxyType(_make_valid_course_payload())
    course = Course.from_dict(mapping)
    assert course.code == "CS101"
    assert course.slots == ["1-1", "1-2"]


def test_course_post_init_collects_all_field_errors_in_single_validation_error() -> None:
    with pytest.raises(ValidationError) as exc_info:
        Course(
            code="   ",
            name="",
            credits=0,
            category="通識",
            teacher="\t",
            capacity=0,
            enrolled=-1,
            room="",
            slots=[],
        )

    err = exc_info.value
    assert isinstance(err, ScheduleError)
    combined = " | ".join(err.errors)
    assert len(err.errors) >= 9
    for field_name in ("code", "name", "credits", "category", "teacher", "capacity", "enrolled", "room", "slots"):
        assert field_name in combined


@pytest.mark.parametrize("field", ["code", "name", "teacher", "room"])
@pytest.mark.parametrize("bad_value", ["", "   ", "\n\t", None, 123])
def test_course_rejects_blank_or_non_string_text_fields(field: str, bad_value: Any) -> None:
    with pytest.raises(ValidationError) as exc_info:
        _make_valid_course(**{field: bad_value})

    assert any(field in msg for msg in exc_info.value.errors)


@pytest.mark.parametrize("bad_category", ["", "   ", " 必修 ", "通識", "必選", None, 1])
def test_course_rejects_invalid_category(bad_category: Any) -> None:
    with pytest.raises(ValidationError) as exc_info:
        _make_valid_course(category=bad_category)

    assert any("category" in msg for msg in exc_info.value.errors)


@pytest.mark.parametrize("bad_credits", [0, -1, True, False, 3.0, "3", None])
def test_course_rejects_invalid_credits(bad_credits: Any) -> None:
    with pytest.raises(ValidationError) as exc_info:
        _make_valid_course(credits=bad_credits)

    assert any("credits" in msg for msg in exc_info.value.errors)


@pytest.mark.parametrize("bad_capacity", [0, -5, True, False, 40.0, "40", None])
def test_course_rejects_invalid_capacity(bad_capacity: Any) -> None:
    with pytest.raises(ValidationError) as exc_info:
        _make_valid_course(capacity=bad_capacity)

    assert any("capacity" in msg for msg in exc_info.value.errors)


@pytest.mark.parametrize("bad_enrolled", [-1, -10, True, False, 10.0, "10", None])
def test_course_rejects_invalid_enrolled(bad_enrolled: Any) -> None:
    with pytest.raises(ValidationError) as exc_info:
        _make_valid_course(enrolled=bad_enrolled)

    assert any("enrolled" in msg for msg in exc_info.value.errors)


@pytest.mark.parametrize(
    "bad_slots",
    [
        None,
        "1-1",
        ("1-1",),
        {"1-1"},
        123,
        [],
        ["1-1", "1-1"],
        ["1-1", "2-2", "1-1"],
        [123],
        [None],
        [["1-1"]],
        [{"slot": "1-1"}],
        [""],
        ["   "],
        ["11"],
        ["1--1"],
        [" 1-1"],
        ["1-1 "],
        ["1_1"],
        ["1:1"],
        ["1-10"],
        ["0-1"],
        ["8-1"],
        ["a-1"],
        ["1-0"],
        ["1-d"],
        ["1-A"],
        ["1- "],
    ],
)
def test_course_rejects_invalid_slots(bad_slots: Any) -> None:
    with pytest.raises(ValidationError) as exc_info:
        _make_valid_course(slots=bad_slots)

    assert any("slots" in msg for msg in exc_info.value.errors)


@pytest.mark.parametrize("non_mapping", [None, [], ["CS001"], "CS001", 123, True])
def test_course_from_dict_rejects_non_mapping(non_mapping: Any) -> None:
    with pytest.raises(ValidationError) as exc_info:
        Course.from_dict(non_mapping)

    assert exc_info.value.errors


@pytest.mark.parametrize(
    "missing_field",
    ["code", "name", "credits", "category", "teacher", "capacity", "enrolled", "room", "slots"],
)
def test_course_from_dict_rejects_missing_single_field(missing_field: str) -> None:
    payload = _make_valid_course_payload()
    del payload[missing_field]

    with pytest.raises(ValidationError) as exc_info:
        Course.from_dict(payload)

    assert any(missing_field in msg for msg in exc_info.value.errors)


def test_course_from_dict_rejects_empty_dict_and_reports_all_missing_fields() -> None:
    with pytest.raises(ValidationError) as exc_info:
        Course.from_dict({})

    combined = " | ".join(exc_info.value.errors)
    for field_name in ("code", "name", "credits", "category", "teacher", "capacity", "enrolled", "room", "slots"):
        assert field_name in combined


@pytest.mark.parametrize("bad_slots", ["1-1", 123, ("1-1",)])
def test_course_from_dict_rejects_non_list_slots_without_converting_or_crashing(bad_slots: Any) -> None:
    payload = _make_valid_course_payload(slots=bad_slots)

    with pytest.raises(ValidationError) as exc_info:
        Course.from_dict(payload)

    assert any("slots" in msg for msg in exc_info.value.errors)


def test_seed_courses_json_loads_all_twenty_legacy_courses_cleanly() -> None:
    assert SEED_COURSES_PATH.is_file()

    raw_data = json.loads(SEED_COURSES_PATH.read_text(encoding="utf-8"))
    assert isinstance(raw_data, list)
    assert len(raw_data) == 20

    courses = [Course.from_dict(item) for item in raw_data]
    codes = [course.code for course in courses]
    assert codes == [f"CS{idx:03d}" for idx in range(1, 21)]
    assert len(set(codes)) == 20

    by_code = {course.code: course for course in courses}
    assert by_code["CS001"].to_dict() == {
        "code": "CS001",
        "name": "程式設計",
        "credits": 3,
        "category": "必修",
        "teacher": "郭大爺",
        "capacity": 45,
        "enrolled": 40,
        "room": "06206",
        "slots": ["2-8", "2-9", "2-a"],
    }
    assert by_code["CS002"].enrolled == 0
    assert by_code["CS013"].name == "體育(1)"
    assert by_code["CS013"].slots == ["5-b", "5-c"]
    assert by_code["CS014"].capacity == 50
    assert by_code["CS014"].enrolled == 50
    assert by_code["CS020"].name == "親密關係"
    assert by_code["CS020"].slots == ["4-a", "4-b"]

    for raw_item, course in zip(raw_data, courses, strict=True):
        assert course.to_dict() == raw_item
