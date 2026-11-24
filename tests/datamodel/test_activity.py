"""Tests for the Activity entity, slots calculation, serialization, and seed data."""

import json
from datetime import date, datetime, time, timezone
from pathlib import Path
from types import MappingProxyType
from typing import Any

import pytest

from datamodel.activity import Activity
from datamodel.errors import ValidationError

ACTIVITIES_SEED_PATH = Path(__file__).resolve().parents[2] / "src" / "datamodel" / "seed" / "activities.json"


def _make_valid_kwargs(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "activity_id": "A01",
        "name": "火舞社表演",
        "date": date(2026, 10, 13),
        "start_time": time(14, 10),
        "end_time": time(15, 0),
        "category": "表演",
        "capacity": 10,
        "registered": 30,
        "required_equipment": ["音響"],
        "room": "02303",
    }
    base.update(overrides)
    return base


def _make_valid_dict(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "activity_id": "A01",
        "name": "火舞社表演",
        "date": "2026-10-13",
        "start_time": "14:10",
        "end_time": "15:00",
        "category": "表演",
        "capacity": 10,
        "registered": 30,
        "required_equipment": ["音響"],
        "room": "02303",
    }
    base.update(overrides)
    return base


def test_activity_valid_construction_and_allowed_edge_states() -> None:
    activity = Activity(**_make_valid_kwargs())

    assert activity.activity_id == "A01"
    assert activity.name == "火舞社表演"
    assert activity.date == date(2026, 10, 13)
    assert activity.start_time == time(14, 10)
    assert activity.end_time == time(15, 0)
    assert activity.category == "表演"
    assert activity.capacity == 10
    assert activity.registered == 30  # registered > capacity must be allowed
    assert activity.required_equipment == ["音響"]
    assert activity.room == "02303"

    outdoor = Activity(**_make_valid_kwargs(room=None, required_equipment=[], registered=0, capacity=1))
    assert outdoor.room is None
    assert outdoor.required_equipment == []
    assert outdoor.registered == 0
    assert outdoor.capacity == 1


def test_activity_slots_is_read_only() -> None:
    activity = Activity(**_make_valid_kwargs())

    with pytest.raises(AttributeError):
        activity.slots = ["2-7"]  # type: ignore[misc]


@pytest.mark.parametrize(
    ("activity_date", "start_time", "end_time", "expected_slots"),
    [
        # Single period exact match (Tuesday 2026-10-13, period 7: 14:10-15:00)
        (date(2026, 10, 13), time(14, 10), time(15, 0), ["2-7"]),
        # Multi-period exact span across Saturday periods 6 and 7 (13:10-15:00)
        (date(2026, 11, 14), time(13, 10), time(15, 0), ["6-6", "6-7"]),
        # Multi-period including letter periods 9 and a (Monday 2026-10-19)
        (date(2026, 10, 19), time(16, 10), time(18, 0), ["1-9", "1-a"]),
        # Multi-period including b and c (Sunday 2026-11-22)
        (date(2026, 11, 22), time(18, 10), time(20, 0), ["7-b", "7-c"]),
        # Partial overlap spanning break between periods 1 (08:10-09:00) and 2 (09:10-10:00)
        (date(2026, 10, 12), time(8, 30), time(9, 20), ["1-1", "1-2"]),
        # Partial overlap just 1 minute into period 1
        (date(2026, 10, 12), time(8, 0), time(8, 11), ["1-1"]),
        # Partial overlap just 1 minute before end of period c
        (date(2026, 10, 12), time(19, 59), time(21, 0), ["1-c"]),
        # Touching boundary at end of period 1 (09:00) and start of period 2 (09:10)
        (date(2026, 10, 12), time(8, 10), time(9, 10), ["1-1"]),
        (date(2026, 10, 12), time(9, 0), time(10, 0), ["1-2"]),
        # Touching before first period or after last period
        (date(2026, 10, 12), time(7, 0), time(8, 10), []),
        (date(2026, 10, 12), time(20, 0), time(21, 0), []),
        # Strictly inside break between periods
        (date(2026, 10, 12), time(9, 0), time(9, 10), []),
        (date(2026, 10, 12), time(9, 2), time(9, 8), []),
    ],
)
def test_activity_slots_calculation(
    activity_date: date,
    start_time: time,
    end_time: time,
    expected_slots: list[str],
) -> None:
    activity = Activity(**_make_valid_kwargs(date=activity_date, start_time=start_time, end_time=end_time))

    assert activity.slots == expected_slots


def test_activity_slots_returns_independent_list() -> None:
    activity = Activity(**_make_valid_kwargs())
    slots = activity.slots
    slots.append("9-z")

    assert activity.slots == ["2-7"]


@pytest.mark.parametrize(
    ("field", "invalid_value"),
    [
        ("activity_id", ""),
        ("activity_id", "   "),
        ("activity_id", 101),
        ("activity_id", None),
        ("name", ""),
        ("name", "\t\n"),
        ("name", 123),
        ("name", None),
        ("category", ""),
        ("category", "   "),
        ("category", 1),
        ("category", None),
        ("room", ""),
        ("room", "   "),
        ("room", 2303),
        ("room", True),
        ("date", datetime(2026, 10, 13, 14, 10)),
        ("date", "2026-10-13"),
        ("date", None),
        ("start_time", "14:10"),
        ("start_time", None),
        ("start_time", time(14, 10, tzinfo=timezone.utc)),
        ("end_time", "15:00"),
        ("end_time", None),
        ("end_time", time(15, 0, tzinfo=timezone.utc)),
        ("capacity", 0),
        ("capacity", -5),
        ("capacity", True),
        ("capacity", False),
        ("capacity", "10"),
        ("capacity", 10.5),
        ("registered", -1),
        ("registered", True),
        ("registered", False),
        ("registered", "30"),
        ("registered", 3.5),
        ("required_equipment", ("音響",)),
        ("required_equipment", {"音響"}),
        ("required_equipment", "音響"),
        ("required_equipment", None),
        ("required_equipment", [123]),
        ("required_equipment", ["音響", None]),
        ("required_equipment", [""]),
        ("required_equipment", ["音響", "   "]),
        ("required_equipment", ["音響", "音響"]),
    ],
)
def test_activity_rejects_invalid_single_field(field: str, invalid_value: Any) -> None:
    with pytest.raises(ValidationError) as exc_info:
        Activity(**_make_valid_kwargs(**{field: invalid_value}))

    assert len(exc_info.value.errors) >= 1


@pytest.mark.parametrize(
    ("start_time", "end_time"),
    [
        (time(14, 10), time(14, 10)),
        (time(15, 0), time(14, 10)),
    ],
)
def test_activity_rejects_non_increasing_time_range(start_time: time, end_time: time) -> None:
    with pytest.raises(ValidationError) as exc_info:
        Activity(**_make_valid_kwargs(start_time=start_time, end_time=end_time))

    assert len(exc_info.value.errors) == 1


def test_activity_post_init_collects_all_validation_errors_at_once() -> None:
    with pytest.raises(ValidationError) as exc_info:
        Activity(
            activity_id=" ",
            name="",
            date=datetime(2026, 10, 13, 14, 10),
            start_time=time(15, 0),
            end_time=time(14, 0),
            category="  ",
            capacity=0,
            registered=-1,
            required_equipment=["音響", "音響", ""],
            room=" ",
        )

    errors = exc_info.value.errors
    assert len(errors) >= 8


def test_activity_post_init_handles_invalid_time_types_alongside_other_errors() -> None:
    with pytest.raises(ValidationError) as exc_info:
        Activity(
            activity_id="",
            name="Valid",
            date=date(2026, 10, 13),
            start_time="14:10",  # type: ignore[arg-type]
            end_time=time(15, 0),
            category="",
            capacity=True,
            registered=-2,
            required_equipment=[],
            room=None,
        )

    assert len(exc_info.value.errors) >= 5


def test_activity_to_dict_and_from_dict_round_trip() -> None:
    activity = Activity(**_make_valid_kwargs())
    serialized = activity.to_dict()

    assert serialized == {
        "activity_id": "A01",
        "name": "火舞社表演",
        "date": "2026-10-13",
        "start_time": "14:10:00",
        "end_time": "15:00:00",
        "category": "表演",
        "capacity": 10,
        "registered": 30,
        "required_equipment": ["音響"],
        "room": "02303",
    }
    json_text = json.dumps(serialized, ensure_ascii=False)
    assert isinstance(json_text, str)

    restored = Activity.from_dict(serialized)
    assert restored == activity


def test_activity_from_dict_accepts_hh_mm_and_mapping_proxy_and_none_room() -> None:
    payload = MappingProxyType(_make_valid_dict(room=None, required_equipment=[]))
    activity = Activity.from_dict(payload)

    assert activity.room is None
    assert activity.required_equipment == []
    assert activity.start_time == time(14, 10)
    assert activity.end_time == time(15, 0)
    assert Activity.from_dict(activity.to_dict()) == activity


def test_activity_defensive_copy_for_required_equipment() -> None:
    direct_eq = ["音響"]
    direct = Activity(**_make_valid_kwargs(required_equipment=direct_eq))
    direct_eq.append("投影機")
    assert direct.required_equipment == ["音響"]

    dict_eq = ["白板"]
    from_dict_act = Activity.from_dict(_make_valid_dict(required_equipment=dict_eq))
    dict_eq.append("電腦")
    assert from_dict_act.required_equipment == ["白板"]

    exported = from_dict_act.to_dict()
    exported["required_equipment"].append("麥克風")
    assert from_dict_act.required_equipment == ["白板"]


@pytest.mark.parametrize("bad_container", [None, [], "not-a-mapping", 42])
def test_activity_from_dict_rejects_non_mapping(bad_container: Any) -> None:
    with pytest.raises(ValidationError) as exc_info:
        Activity.from_dict(bad_container)

    assert len(exc_info.value.errors) >= 1


@pytest.mark.parametrize(
    "missing_key",
    [
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
    ],
)
def test_activity_from_dict_rejects_missing_required_key(missing_key: str) -> None:
    payload = _make_valid_dict()
    del payload[missing_key]

    with pytest.raises(ValidationError) as exc_info:
        Activity.from_dict(payload)

    assert len(exc_info.value.errors) >= 1


@pytest.mark.parametrize(
    "bad_date",
    [
        "2026-10-13T14:10:00",
        "20261013",
        "2026-1-5",
        "2026-W41-2",
        "2026-02-30",
        "10/13",
        "",
        date(2026, 10, 13),
        123,
        None,
    ],
)
def test_activity_from_dict_rejects_invalid_date(bad_date: Any) -> None:
    with pytest.raises(ValidationError) as exc_info:
        Activity.from_dict(_make_valid_dict(date=bad_date))

    assert len(exc_info.value.errors) >= 1


@pytest.mark.parametrize(
    "bad_time",
    [
        "1410",
        "8:10",
        "25:00",
        "14:60",
        "14:10+08:00",
        "14:10:00Z",
        "T14:10:00",
        "invalid",
        "",
        time(14, 10),
        1410,
        None,
    ],
)
def test_activity_from_dict_rejects_invalid_start_or_end_time(bad_time: Any) -> None:
    with pytest.raises(ValidationError):
        Activity.from_dict(_make_valid_dict(start_time=bad_time))

    with pytest.raises(ValidationError):
        Activity.from_dict(_make_valid_dict(end_time=bad_time))


def test_activity_from_dict_collects_multiple_errors_across_missing_parse_and_fields() -> None:
    payload: dict[str, Any] = {
        "activity_id": "",
        "name": "   ",
        "date": "2026-10-13T10:00:00",
        "start_time": "invalid",
        "end_time": "15:00",
        "category": "",
        "capacity": 0,
        "registered": -1,
        "required_equipment": ["音響", "音響"],
        # missing "room"
    }

    with pytest.raises(ValidationError) as exc_info:
        Activity.from_dict(payload)

    assert len(exc_info.value.errors) >= 8


def test_seed_activities_json_loads_all_ten_legacy_activities() -> None:
    assert ACTIVITIES_SEED_PATH.is_file()
    raw_records = json.loads(ACTIVITIES_SEED_PATH.read_text(encoding="utf-8"))
    assert isinstance(raw_records, list)
    assert len(raw_records) == 10

    activities = [Activity.from_dict(record) for record in raw_records]
    by_id = {act.activity_id: act for act in activities}
    assert list(by_id.keys()) == [f"A{i:02d}" for i in range(1, 11)]

    expected_legacy = {
        "A01": ("火舞社表演", date(2026, 10, 13), time(14, 10), time(15, 0), 30, 10, "02303"),
        "A02": ("自主學Python", date(2026, 10, 22), time(11, 10), time(12, 0), 40, 15, "06206"),
        "A03": ("技藝競賽培養", date(2026, 11, 2), time(12, 10), time(13, 0), 30, 10, "03303"),
        "A04": ("慈濟社活動", date(2026, 11, 14), time(13, 10), time(15, 0), 40, 20, "06206"),
        "A05": ("弓道社社課", date(2026, 11, 22), time(10, 10), time(12, 0), 40, 20, "06206"),
        "A06": ("口技社", date(2026, 10, 19), time(16, 10), time(18, 0), 45, 15, "06206"),
        "A07": ("熱舞表演", date(2026, 10, 23), time(16, 10), time(17, 0), 50, 30, "00101"),
        "A08": ("排球冠亞軍賽", date(2026, 10, 17), time(10, 10), time(12, 0), 50, 24, "00101"),
        "A09": ("網球競賽", date(2026, 10, 9), time(17, 10), time(19, 0), 50, 20, "00101"),
        "A10": ("直笛表演", date(2026, 10, 21), time(10, 10), time(11, 0), 40, 15, "06302"),
    }

    for act_id, (name, act_date, start, end, registered, capacity, room) in expected_legacy.items():
        act = by_id[act_id]
        assert act.name == name
        assert act.date == act_date
        assert act.start_time == start
        assert act.end_time == end
        assert act.registered == registered
        assert act.capacity == capacity
        assert act.room == room
        assert act.category.strip() != ""
        assert len(act.required_equipment) >= 1

    assert by_id["A01"].slots == ["2-7"]
    assert by_id["A04"].slots == ["6-6", "6-7"]
    assert by_id["A09"].slots == ["5-a", "5-b"]
