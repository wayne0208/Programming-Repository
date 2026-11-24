"""Tests for the Classroom entity and seed classroom records."""

import importlib.resources
import json
from types import MappingProxyType
from typing import Any

import pytest

from datamodel.classroom import Classroom
from datamodel.errors import ValidationError


def test_classroom_valid_construction() -> None:
    room = Classroom(room_id="06206", capacity=45, equipment=["投影機", "白板"])

    assert room.room_id == "06206"
    assert room.capacity == 45
    assert room.equipment == ["投影機", "白板"]


def test_classroom_allows_empty_equipment_and_minimum_capacity() -> None:
    room = Classroom(room_id="A101", capacity=1, equipment=[])

    assert room.room_id == "A101"
    assert room.capacity == 1
    assert room.equipment == []


@pytest.mark.parametrize("bad_room_id", ["", "   ", "\t\n", None, 6206, ["06206"]])
def test_classroom_rejects_invalid_room_id(bad_room_id: Any) -> None:
    with pytest.raises(ValidationError) as exc_info:
        Classroom(room_id=bad_room_id, capacity=30, equipment=["投影機"])

    assert exc_info.value.errors
    assert any("room_id" in msg for msg in exc_info.value.errors)


@pytest.mark.parametrize("bad_capacity", [0, -1, -100, True, False, 45.0, "45", None])
def test_classroom_rejects_invalid_capacity(bad_capacity: Any) -> None:
    with pytest.raises(ValidationError) as exc_info:
        Classroom(room_id="06206", capacity=bad_capacity, equipment=["投影機"])

    assert exc_info.value.errors
    assert any("capacity" in msg for msg in exc_info.value.errors)


@pytest.mark.parametrize(
    "bad_equipment",
    [
        "投影機",
        ("投影機",),
        {"投影機"},
        None,
        123,
        [123],
        [None],
        [True],
        [""],
        ["   "],
        ["投影機", "投影機"],
        ["投影機", "白板", "投影機"],
        [["投影機"], ["投影機"]],
    ],
)
def test_classroom_rejects_invalid_equipment(bad_equipment: Any) -> None:
    with pytest.raises(ValidationError) as exc_info:
        Classroom(room_id="06206", capacity=45, equipment=bad_equipment)

    assert exc_info.value.errors
    assert any("equipment" in msg for msg in exc_info.value.errors)


@pytest.mark.parametrize(
    ("bad_room_id", "bad_capacity", "bad_equipment"),
    [
        ("", 0, "not-a-list"),
        ("   ", True, ["", "投影機", "投影機"]),
        (None, -5, [["unhashable"], "   "]),
    ],
)
def test_classroom_collects_all_validation_errors_in_single_exception(
    bad_room_id: Any,
    bad_capacity: Any,
    bad_equipment: Any,
) -> None:
    with pytest.raises(ValidationError) as exc_info:
        Classroom(room_id=bad_room_id, capacity=bad_capacity, equipment=bad_equipment)

    errors = exc_info.value.errors
    assert len(errors) >= 3
    assert any("room_id" in msg for msg in errors)
    assert any("capacity" in msg for msg in errors)
    assert any("equipment" in msg for msg in errors)


def test_classroom_from_dict_and_to_dict_round_trip() -> None:
    raw = {
        "room_id": "03303",
        "capacity": 30,
        "equipment": ["投影機", "白板", "電腦"],
    }

    room_from_dict = Classroom.from_dict(raw)
    room_from_mapping = Classroom.from_dict(MappingProxyType(raw))

    assert room_from_dict == Classroom(room_id="03303", capacity=30, equipment=["投影機", "白板", "電腦"])
    assert room_from_mapping == room_from_dict

    exported = room_from_dict.to_dict()
    assert exported == raw

    round_tripped = Classroom.from_dict(json.loads(json.dumps(exported, ensure_ascii=False)))
    assert round_tripped == room_from_dict


@pytest.mark.parametrize("bad_payload", [None, ["06206", 45, []], "06206", 123])
def test_classroom_from_dict_rejects_non_mapping(bad_payload: Any) -> None:
    with pytest.raises(ValidationError) as exc_info:
        Classroom.from_dict(bad_payload)

    assert exc_info.value.errors


@pytest.mark.parametrize("missing_key", ["room_id", "capacity", "equipment"])
def test_classroom_from_dict_rejects_missing_single_key(missing_key: str) -> None:
    payload: dict[str, Any] = {
        "room_id": "06206",
        "capacity": 45,
        "equipment": ["投影機"],
    }
    del payload[missing_key]

    with pytest.raises(ValidationError) as exc_info:
        Classroom.from_dict(payload)

    assert exc_info.value.errors
    assert any(missing_key in msg for msg in exc_info.value.errors)


def test_classroom_from_dict_reports_all_missing_keys_and_invalid_present_fields() -> None:
    with pytest.raises(ValidationError) as empty_exc:
        Classroom.from_dict({})

    assert len(empty_exc.value.errors) == 3
    for key in ("room_id", "capacity", "equipment"):
        assert any(key in msg for msg in empty_exc.value.errors)

    with pytest.raises(ValidationError) as partial_exc:
        Classroom.from_dict({"room_id": "", "capacity": False})

    errors = partial_exc.value.errors
    assert any("equipment" in msg for msg in errors)
    assert any("room_id" in msg for msg in errors)
    assert any("capacity" in msg for msg in errors)


def test_classroom_from_dict_rejects_invalid_values() -> None:
    with pytest.raises(ValidationError) as exc_info:
        Classroom.from_dict({"room_id": " ", "capacity": True, "equipment": ["投影機", "投影機"]})

    errors = exc_info.value.errors
    assert len(errors) >= 3
    assert any("room_id" in msg for msg in errors)
    assert any("capacity" in msg for msg in errors)
    assert any("equipment" in msg for msg in errors)


def test_classroom_defensive_copy_isolates_equipment_list() -> None:
    ctor_list = ["投影機"]
    room_ctor = Classroom(room_id="06206", capacity=45, equipment=ctor_list)
    ctor_list.append("白板")
    assert room_ctor.equipment == ["投影機"]

    dict_list = ["投影機", "白板"]
    raw_dict = {"room_id": "03303", "capacity": 30, "equipment": dict_list}
    room_from_dict = Classroom.from_dict(raw_dict)
    dict_list.append("音響")
    assert room_from_dict.equipment == ["投影機", "白板"]

    exported = room_from_dict.to_dict()
    exported["equipment"].append("麥克風")
    assert room_from_dict.equipment == ["投影機", "白板"]


def test_seed_classrooms_json_loads_all_five_legacy_classrooms() -> None:
    seed_file = importlib.resources.files("datamodel").joinpath("seed", "classrooms.json")
    raw_text = seed_file.read_text(encoding="utf-8")
    raw_records = json.loads(raw_text)

    assert isinstance(raw_records, list)
    assert len(raw_records) == 5

    classrooms = [Classroom.from_dict(record) for record in raw_records]
    by_id = {room.room_id: room for room in classrooms}

    assert list(by_id.keys()) == ["06206", "03303", "06302", "02303", "00101"]
    assert by_id["06206"] == Classroom("06206", 45, ["投影機", "白板", "電腦", "麥克風", "音響"])
    assert by_id["03303"] == Classroom("03303", 30, ["投影機", "白板", "電腦"])
    assert by_id["06302"] == Classroom("06302", 40, ["投影機", "白板", "麥克風", "音響"])
    assert by_id["02303"] == Classroom("02303", 40, ["投影機", "白板", "音響"])
    assert by_id["00101"] == Classroom("00101", 50, ["音響", "麥克風", "體育器材"])

    assert [room.to_dict() for room in classrooms] == raw_records
