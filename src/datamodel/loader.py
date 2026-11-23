"""Fault-tolerant seed data loader using importlib.resources."""

import importlib.resources
import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, TypeVar

from datamodel.activity import Activity
from datamodel.classroom import Classroom
from datamodel.course import Course
from datamodel.errors import ValidationError
from datamodel.student import Student

__all__ = ["SeedData", "load_seed_data"]

ENTITY_T = TypeVar("ENTITY_T")


@dataclass
class SeedData:
    """Container holding freshly loaded collections of seed entities keyed by ID."""

    courses: dict[str, Course]
    students: dict[str, Student]
    classrooms: dict[str, Classroom]
    activities: dict[str, Activity]


def _load_entity_file(
    filename: str,
    from_dict: Callable[[Mapping[str, Any]], ENTITY_T],
    get_id: Callable[[ENTITY_T], str],
    warnings: list[str],
) -> dict[str, ENTITY_T]:
    try:
        seed_file = importlib.resources.files("datamodel").joinpath("seed", filename)
        raw_text = seed_file.read_text(encoding="utf-8")
    except OSError as exc:
        warnings.append(f"無法讀取模擬資料檔案 {filename}: {exc}")
        return {}
    except UnicodeDecodeError as exc:
        warnings.append(f"模擬資料檔案 {filename} UTF-8 解碼失敗: {exc}")
        return {}

    try:
        raw_records = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        warnings.append(f"模擬資料檔案 {filename} JSON 解析失敗: {exc}")
        return {}

    if not isinstance(raw_records, list):
        warnings.append(f"模擬資料檔案 {filename} 頂層必須為 JSON 陣列 (list)")
        return {}

    entities: dict[str, ENTITY_T] = {}
    for index, record in enumerate(raw_records):
        try:
            entity = from_dict(record)
        except ValidationError as exc:
            warnings.append(f"{filename}[{index}] 資料驗證失敗: {exc}")
            continue

        entity_id = get_id(entity)
        if entity_id in entities:
            warnings.append(f"{filename}[{index}] 重複的 ID '{entity_id}'，已保留第一筆並略過此筆")
            continue

        entities[entity_id] = entity

    return entities


def load_seed_data() -> tuple[SeedData, list[str]]:
    """Load all built-in seed JSON files into fresh SeedData collections with warnings."""
    warnings: list[str] = []
    courses = _load_entity_file("courses.json", Course.from_dict, lambda c: c.code, warnings)
    students = _load_entity_file("students.json", Student.from_dict, lambda s: s.student_id, warnings)
    classrooms = _load_entity_file("classrooms.json", Classroom.from_dict, lambda r: r.room_id, warnings)
    activities = _load_entity_file("activities.json", Activity.from_dict, lambda a: a.activity_id, warnings)
    return (
        SeedData(
            courses=courses,
            students=students,
            classrooms=classrooms,
            activities=activities,
        ),
        warnings,
    )
