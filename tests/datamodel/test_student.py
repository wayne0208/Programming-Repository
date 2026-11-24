"""Tests for Student entity validation, serialization, and seed data."""

import json
from importlib.resources import files
from types import MappingProxyType
from typing import Any

import pytest

from datamodel.errors import ValidationError
from datamodel.student import Student


def _make_valid_student_dict(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "student_id": "1150101",
        "name": "王曉明",
        "department": "資工一",
        "credit_limit": 25,
        "enrolled_courses": ["CS008", "CS004"],
        "enrolled_activities": ["A06"],
    }
    data.update(overrides)
    return data


@pytest.mark.parametrize("student_id", ["1150101", "S001", "grad-2026-01"])
def test_student_accepts_valid_data_without_id_prefix_restriction(student_id: str) -> None:
    student = Student(
        student_id=student_id,
        name="王曉明",
        department="資工一",
        credit_limit=25,
        enrolled_courses=[],
        enrolled_activities=[],
    )

    assert student.student_id == student_id
    assert student.name == "王曉明"
    assert student.department == "資工一"
    assert student.credit_limit == 25
    assert student.enrolled_courses == []
    assert student.enrolled_activities == []


def test_student_defensively_copies_lists_on_init() -> None:
    courses = ["CS001", "CS002"]
    activities = ["A01"]
    student = Student(
        student_id="1150101",
        name="王曉明",
        department="資工一",
        credit_limit=25,
        enrolled_courses=courses,
        enrolled_activities=activities,
    )

    courses.append("CS999")
    activities.append("A99")

    assert student.enrolled_courses == ["CS001", "CS002"]
    assert student.enrolled_activities == ["A01"]


@pytest.mark.parametrize("field_name", ["student_id", "name", "department"])
@pytest.mark.parametrize("bad_value", ["", "   ", "\t\n", 123, None, ["text"]])
def test_student_rejects_invalid_text_fields(field_name: str, bad_value: Any) -> None:
    payload = _make_valid_student_dict(**{field_name: bad_value})

    with pytest.raises(ValidationError) as exc_info:
        Student(**payload)

    assert any(field_name in msg for msg in exc_info.value.errors)


@pytest.mark.parametrize("bad_credit", [True, False, 0, -1, -25, 25.0, "25", None])
def test_student_rejects_invalid_credit_limit(bad_credit: Any) -> None:
    payload = _make_valid_student_dict(credit_limit=bad_credit)

    with pytest.raises(ValidationError) as exc_info:
        Student(**payload)

    assert any("credit_limit" in msg for msg in exc_info.value.errors)


@pytest.mark.parametrize("field_name", ["enrolled_courses", "enrolled_activities"])
@pytest.mark.parametrize(
    "bad_list",
    [
        "CS001",
        ("CS001",),
        {"CS001"},
        None,
        123,
        [""],
        ["   "],
        ["CS001", ""],
        ["CS001", 123],
        ["CS001", ["nested"]],
        ["CS001", "CS001"],
    ],
)
def test_student_rejects_invalid_enrolled_lists(field_name: str, bad_list: Any) -> None:
    payload = _make_valid_student_dict(**{field_name: bad_list})

    with pytest.raises(ValidationError) as exc_info:
        Student(**payload)

    assert any(field_name in msg for msg in exc_info.value.errors)


def test_student_collects_all_field_errors_at_once() -> None:
    with pytest.raises(ValidationError) as exc_info:
        Student(
            student_id="",
            name="   ",
            department=None,  # type: ignore[arg-type]
            credit_limit=True,
            enrolled_courses=["CS001", "CS001"],
            enrolled_activities=[123],  # type: ignore[list-item]
        )

    errors = exc_info.value.errors
    assert len(errors) >= 6
    for field_name in (
        "student_id",
        "name",
        "department",
        "credit_limit",
        "enrolled_courses",
        "enrolled_activities",
    ):
        assert any(field_name in msg for msg in errors)


def test_student_collects_both_invalid_element_and_duplicate_in_same_list() -> None:
    payload = _make_valid_student_dict(enrolled_courses=["", "CS001", "CS001"])

    with pytest.raises(ValidationError) as exc_info:
        Student(**payload)

    assert len(exc_info.value.errors) == 2


def test_student_allows_same_code_across_courses_and_activities_lists() -> None:
    student = Student(**_make_valid_student_dict(enrolled_courses=["X01"], enrolled_activities=["X01"]))

    assert student.enrolled_courses == ["X01"]
    assert student.enrolled_activities == ["X01"]


def test_student_from_dict_and_to_dict_round_trip() -> None:
    raw_mapping = MappingProxyType(_make_valid_student_dict())
    student = Student.from_dict(raw_mapping)

    serialized = student.to_dict()
    assert serialized == {
        "student_id": "1150101",
        "name": "王曉明",
        "department": "資工一",
        "credit_limit": 25,
        "enrolled_courses": ["CS008", "CS004"],
        "enrolled_activities": ["A06"],
    }

    round_tripped = Student.from_dict(json.loads(json.dumps(serialized, ensure_ascii=False)))
    assert round_tripped == student


def test_student_from_dict_and_to_dict_defensive_copies() -> None:
    source_courses = ["CS001"]
    source_activities = ["A01"]
    raw = _make_valid_student_dict(
        enrolled_courses=source_courses,
        enrolled_activities=source_activities,
    )

    student = Student.from_dict(raw)
    source_courses.append("CS002")
    source_activities.append("A02")

    assert student.enrolled_courses == ["CS001"]
    assert student.enrolled_activities == ["A01"]

    exported = student.to_dict()
    exported["enrolled_courses"].append("CS003")
    exported["enrolled_activities"].append("A03")

    assert student.enrolled_courses == ["CS001"]
    assert student.enrolled_activities == ["A01"]


@pytest.mark.parametrize("bad_input", [None, [], ["1150101"], "json", 42])
def test_student_from_dict_rejects_non_mapping(bad_input: Any) -> None:
    with pytest.raises(ValidationError):
        Student.from_dict(bad_input)


def test_student_from_dict_rejects_empty_mapping_reporting_all_missing_fields() -> None:
    with pytest.raises(ValidationError) as exc_info:
        Student.from_dict({})

    errors = exc_info.value.errors
    for field_name in (
        "student_id",
        "name",
        "department",
        "credit_limit",
        "enrolled_courses",
        "enrolled_activities",
    ):
        assert any(field_name in msg for msg in errors)


@pytest.mark.parametrize(
    "missing_key",
    ["student_id", "name", "department", "credit_limit", "enrolled_courses", "enrolled_activities"],
)
def test_student_from_dict_rejects_single_missing_key(missing_key: str) -> None:
    payload = _make_valid_student_dict()
    del payload[missing_key]

    with pytest.raises(ValidationError) as exc_info:
        Student.from_dict(payload)

    assert any(missing_key in msg for msg in exc_info.value.errors)


def test_student_from_dict_rejects_invalid_values_and_collects_errors() -> None:
    payload = _make_valid_student_dict(student_id="", credit_limit=False, enrolled_activities="A06")

    with pytest.raises(ValidationError) as exc_info:
        Student.from_dict(payload)

    errors = exc_info.value.errors
    assert len(errors) >= 3
    assert any("student_id" in msg for msg in errors)
    assert any("credit_limit" in msg for msg in errors)
    assert any("enrolled_activities" in msg for msg in errors)


def test_seed_students_json_loads_all_15_students_cleanly() -> None:
    raw_text = files("datamodel").joinpath("seed", "students.json").read_text(encoding="utf-8")
    raw_records = json.loads(raw_text)

    assert isinstance(raw_records, list)
    assert len(raw_records) == 15

    students = [Student.from_dict(record) for record in raw_records]
    by_id = {student.student_id: student for student in students}

    assert [student.student_id for student in students] == [
        "1150101",
        "1150102",
        "1150103",
        "1150104",
        "1150105",
        "1150106",
        "1150107",
        "1150108",
        "1150109",
        "1150110",
        "1140120",
        "1140131",
        "1140146",
        "1130116",
        "1130124",
    ]
    assert len(by_id) == 15

    expected_curriculum3_courses = ["CS008", "CS004", "CS007", "CS006", "CS001", "CS005", "CS003", "CS013"]
    assert by_id["1150101"].name == "王曉明"
    assert by_id["1150101"].department == "資工一"
    assert by_id["1150101"].credit_limit == 25
    assert by_id["1150101"].enrolled_courses == expected_curriculum3_courses
    assert by_id["1150101"].enrolled_activities == []

    assert by_id["1150108"].name == "月島螢"
    assert by_id["1150108"].department == "資工一"
    assert by_id["1150108"].credit_limit == 25
    assert by_id["1150108"].enrolled_courses == expected_curriculum3_courses
    assert by_id["1150108"].enrolled_activities == ["A06"]

    assert by_id["1130124"].name == "芙莉蓮"
    assert by_id["1130124"].department == "資工三"
    assert by_id["1130124"].enrolled_courses == ["CS007", "CS019"]
    assert by_id["1130124"].enrolled_activities == []

    for student in students:
        assert all(code.startswith("CS") for code in student.enrolled_courses)
        assert all(not code.startswith("CS") for code in student.enrolled_activities)

    # Verify independent lists across students sharing the same legacy curriculum
    by_id["1150101"].enrolled_courses.append("CS999")
    assert "CS999" not in by_id["1150102"].enrolled_courses
    assert "CS999" not in by_id["1150109"].enrolled_courses

    # Verify round-trip matches raw seed JSON
    by_id["1150101"].enrolled_courses.pop()
    assert [student.to_dict() for student in students] == raw_records
