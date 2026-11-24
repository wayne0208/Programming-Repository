"""Integration tests for datamodel package exports and load_seed_data()."""

import importlib
import importlib.resources
import json
from dataclasses import is_dataclass
from pathlib import Path
from typing import Any

import pytest

from datamodel import (
    COURSE_CATEGORIES,
    DAYS,
    PERIOD_TIMES,
    PERIODS,
    Activity,
    Classroom,
    Course,
    DuplicateIdError,
    NotFoundError,
    ScheduleError,
    SeedData,
    Student,
    ValidationError,
    load_seed_data,
)

EXPECTED_PUBLIC_SYMBOLS: set[str] = {
    "Course",
    "Student",
    "Classroom",
    "Activity",
    "SeedData",
    "load_seed_data",
    "DAYS",
    "PERIODS",
    "PERIOD_TIMES",
    "COURSE_CATEGORIES",
    "ScheduleError",
    "ValidationError",
    "NotFoundError",
    "DuplicateIdError",
}


def _sample_course(code: str = "CS101", name: str = "資料結構") -> dict[str, Any]:
    return {
        "code": code,
        "name": name,
        "credits": 3,
        "category": "必修",
        "teacher": "王老師",
        "capacity": 40,
        "enrolled": 25,
        "room": "06206",
        "slots": ["1-1", "1-2"],
    }


def _sample_student(student_id: str = "S001", name: str = "林小美") -> dict[str, Any]:
    return {
        "student_id": student_id,
        "name": name,
        "department": "資工一",
        "credit_limit": 25,
        "enrolled_courses": ["CS101"],
        "enrolled_activities": [],
    }


def _sample_classroom(room_id: str = "06206") -> dict[str, Any]:
    return {
        "room_id": room_id,
        "capacity": 45,
        "equipment": ["投影機", "白板"],
    }


def _sample_activity(activity_id: str = "A01", name: str = "專題講座") -> dict[str, Any]:
    return {
        "activity_id": activity_id,
        "name": name,
        "date": "2026-10-15",
        "start_time": "10:10",
        "end_time": "12:00",
        "category": "講座",
        "capacity": 50,
        "registered": 20,
        "required_equipment": ["投影機"],
        "room": "06206",
    }


def _prepare_seed_dir(
    root: Path,
    *,
    courses: list[Any] | None = None,
    students: list[Any] | None = None,
    classrooms: list[Any] | None = None,
    activities: list[Any] | None = None,
) -> Path:
    seed_dir = root / "seed"
    seed_dir.mkdir(parents=True, exist_ok=True)
    datasets = {
        "courses.json": [_sample_course()] if courses is None else courses,
        "students.json": [_sample_student()] if students is None else students,
        "classrooms.json": [_sample_classroom()] if classrooms is None else classrooms,
        "activities.json": [_sample_activity()] if activities is None else activities,
    }
    for filename, payload in datasets.items():
        (seed_dir / filename).write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return seed_dir


def test_package_exports_all_fourteen_public_symbols() -> None:
    pkg = importlib.import_module("datamodel")

    assert hasattr(pkg, "__all__")
    assert len(pkg.__all__) == 14
    assert set(pkg.__all__) == EXPECTED_PUBLIC_SYMBOLS

    imported_symbols = {
        "Course": Course,
        "Student": Student,
        "Classroom": Classroom,
        "Activity": Activity,
        "SeedData": SeedData,
        "load_seed_data": load_seed_data,
        "DAYS": DAYS,
        "PERIODS": PERIODS,
        "PERIOD_TIMES": PERIOD_TIMES,
        "COURSE_CATEGORIES": COURSE_CATEGORIES,
        "ScheduleError": ScheduleError,
        "ValidationError": ValidationError,
        "NotFoundError": NotFoundError,
        "DuplicateIdError": DuplicateIdError,
    }
    for name, obj in imported_symbols.items():
        assert getattr(pkg, name) is obj

    assert is_dataclass(SeedData)
    assert issubclass(ValidationError, ScheduleError)
    assert issubclass(NotFoundError, ScheduleError)
    assert issubclass(DuplicateIdError, ScheduleError)


def test_load_seed_data_default_dataset_loads_expected_counts_and_records() -> None:
    seed, warnings = load_seed_data()

    assert warnings == []
    assert isinstance(seed, SeedData)

    assert len(seed.courses) == 20
    assert all(isinstance(code, str) and isinstance(course, Course) for code, course in seed.courses.items())
    assert all(course.code == code for code, course in seed.courses.items())

    assert len(seed.students) == 15
    assert all(isinstance(sid, str) and isinstance(student, Student) for sid, student in seed.students.items())
    assert all(student.student_id == sid for sid, student in seed.students.items())
    assert seed.students["1150108"].enrolled_activities == ["A06"]

    assert len(seed.classrooms) == 5
    assert all(isinstance(rid, str) and isinstance(room, Classroom) for rid, room in seed.classrooms.items())
    assert all(room.room_id == rid for rid, room in seed.classrooms.items())

    assert len(seed.activities) == 10
    assert all(isinstance(aid, str) and isinstance(activity, Activity) for aid, activity in seed.activities.items())
    assert all(activity.activity_id == aid for aid, activity in seed.activities.items())


def test_load_seed_data_returns_independent_copies_each_call() -> None:
    first, first_warnings = load_seed_data()
    second, second_warnings = load_seed_data()

    assert first_warnings == []
    assert second_warnings == []
    assert first is not second
    assert first.courses is not second.courses
    assert first.students is not second.students
    assert first.classrooms is not second.classrooms
    assert first.activities is not second.activities

    first.courses["CS001"].slots.append("7-c")
    del first.courses["CS002"]
    first.students["1150108"].enrolled_activities.append("A01")
    first.classrooms["06206"].equipment.append("雷射筆")
    first.activities["A01"].required_equipment.append("攝影機")

    assert "CS002" in second.courses
    assert "7-c" not in second.courses["CS001"].slots
    assert second.students["1150108"].enrolled_activities == ["A06"]
    assert "雷射筆" not in second.classrooms["06206"].equipment
    assert "攝影機" not in second.activities["A01"].required_equipment

    third, third_warnings = load_seed_data()
    assert third_warnings == []
    assert len(third.courses) == 20
    assert third.students["1150108"].enrolled_activities == ["A06"]


def test_load_seed_data_skips_malformed_records_with_warnings_and_loads_valid_ones(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    invalid_course = _sample_course(code="BAD1")
    invalid_course["credits"] = 0
    invalid_course["slots"] = ["9-z"]

    _prepare_seed_dir(
        tmp_path,
        courses=[
            _sample_course(code="CS101", name="資料結構"),
            invalid_course,
            _sample_course(code="CS102", name="演算法"),
        ],
        students=["not-a-dict", _sample_student(student_id="S001")],
    )
    monkeypatch.setattr(importlib.resources, "files", lambda pkg: tmp_path)

    seed, warnings = load_seed_data()

    assert list(seed.courses.keys()) == ["CS101", "CS102"]
    assert list(seed.students.keys()) == ["S001"]
    assert list(seed.classrooms.keys()) == ["06206"]
    assert list(seed.activities.keys()) == ["A01"]

    assert len(warnings) == 2
    assert "courses.json" in warnings[0]
    assert "1" in warnings[0]
    assert "credits" in warnings[0]
    assert "slots" in warnings[0]
    assert "students.json" in warnings[1]
    assert "0" in warnings[1]


def test_load_seed_data_keeps_first_valid_record_on_duplicate_id(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    invalid_first_student = _sample_student(student_id="S001", name="")
    _prepare_seed_dir(
        tmp_path,
        courses=[
            _sample_course(code="CS101", name="演算法（第一筆）"),
            _sample_course(code="CS101", name="演算法（重複筆）"),
            _sample_course(code="CS102", name="作業系統"),
        ],
        students=[
            invalid_first_student,
            _sample_student(student_id="S001", name="王大明（合法第一筆）"),
            _sample_student(student_id="S001", name="王大明（重複筆）"),
        ],
        classrooms=[
            _sample_classroom(room_id="06206"),
            {"room_id": "06206", "capacity": 99, "equipment": []},
        ],
        activities=[
            _sample_activity(activity_id="A01", name="第一場活動"),
            _sample_activity(activity_id="A01", name="重複活動"),
        ],
    )
    monkeypatch.setattr(importlib.resources, "files", lambda pkg: tmp_path)

    seed, warnings = load_seed_data()

    assert list(seed.courses.keys()) == ["CS101", "CS102"]
    assert seed.courses["CS101"].name == "演算法（第一筆）"
    assert seed.courses["CS102"].name == "作業系統"

    assert list(seed.students.keys()) == ["S001"]
    assert seed.students["S001"].name == "王大明（合法第一筆）"

    assert list(seed.classrooms.keys()) == ["06206"]
    assert seed.classrooms["06206"].capacity == 45

    assert list(seed.activities.keys()) == ["A01"]
    assert seed.activities["A01"].name == "第一場活動"

    assert len(warnings) == 5
    assert "courses.json" in warnings[0] and "1" in warnings[0] and "CS101" in warnings[0]
    assert "students.json" in warnings[1] and "0" in warnings[1]
    assert "students.json" in warnings[2] and "2" in warnings[2] and "S001" in warnings[2]
    assert "classrooms.json" in warnings[3] and "1" in warnings[3] and "06206" in warnings[3]
    assert "activities.json" in warnings[4] and "1" in warnings[4] and "A01" in warnings[4]


def test_load_seed_data_skips_corrupted_json_file_while_loading_others(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seed_dir = _prepare_seed_dir(tmp_path)
    (seed_dir / "activities.json").write_text("{corrupted-json", encoding="utf-8")
    monkeypatch.setattr(importlib.resources, "files", lambda pkg: tmp_path)

    seed, warnings = load_seed_data()

    assert seed.activities == {}
    assert list(seed.courses.keys()) == ["CS101"]
    assert list(seed.students.keys()) == ["S001"]
    assert list(seed.classrooms.keys()) == ["06206"]

    assert len(warnings) == 1
    assert "activities.json" in warnings[0]


def test_load_seed_data_skips_invalid_utf8_file_with_warning(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seed_dir = _prepare_seed_dir(tmp_path)
    (seed_dir / "classrooms.json").write_bytes(b"\xff\xfe\x80")
    monkeypatch.setattr(importlib.resources, "files", lambda pkg: tmp_path)

    seed, warnings = load_seed_data()

    assert seed.classrooms == {}
    assert list(seed.courses.keys()) == ["CS101"]
    assert list(seed.students.keys()) == ["S001"]
    assert list(seed.activities.keys()) == ["A01"]

    assert len(warnings) == 1
    assert "classrooms.json" in warnings[0]


@pytest.mark.parametrize("non_array_payload", [{"room_id": "06206"}, "not-a-list", 123, None, True])
def test_load_seed_data_skips_non_array_json_root_with_warning(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    non_array_payload: Any,
) -> None:
    seed_dir = _prepare_seed_dir(tmp_path)
    (seed_dir / "classrooms.json").write_text(
        json.dumps(non_array_payload, ensure_ascii=False),
        encoding="utf-8",
    )
    monkeypatch.setattr(importlib.resources, "files", lambda pkg: tmp_path)

    seed, warnings = load_seed_data()

    assert seed.classrooms == {}
    assert list(seed.courses.keys()) == ["CS101"]
    assert list(seed.students.keys()) == ["S001"]
    assert list(seed.activities.keys()) == ["A01"]

    assert len(warnings) == 1
    assert "classrooms.json" in warnings[0]


def test_load_seed_data_skips_missing_and_unreadable_json_files_with_warnings(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seed_dir = _prepare_seed_dir(tmp_path)
    (seed_dir / "courses.json").unlink()
    (seed_dir / "students.json").unlink()
    (seed_dir / "students.json").mkdir()
    monkeypatch.setattr(importlib.resources, "files", lambda pkg: tmp_path)

    seed, warnings = load_seed_data()

    assert seed.courses == {}
    assert seed.students == {}
    assert list(seed.classrooms.keys()) == ["06206"]
    assert list(seed.activities.keys()) == ["A01"]

    assert len(warnings) == 2
    assert any("courses.json" in msg for msg in warnings)
    assert any("students.json" in msg for msg in warnings)


def test_load_seed_data_handles_empty_json_arrays_without_warnings(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _prepare_seed_dir(tmp_path, courses=[], students=[], classrooms=[], activities=[])
    monkeypatch.setattr(importlib.resources, "files", lambda pkg: tmp_path)

    seed, warnings = load_seed_data()

    assert warnings == []
    assert seed == SeedData(courses={}, students={}, classrooms={}, activities={})
