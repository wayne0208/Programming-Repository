"""Tests for datamodel domain constants and exception hierarchy."""

from collections.abc import Sequence
from datetime import date, datetime, time, timedelta

import pytest

from datamodel.constants import COURSE_CATEGORIES, DAYS, PERIOD_TIMES, PERIODS
from datamodel.errors import DuplicateIdError, NotFoundError, ScheduleError, ValidationError


def test_days_covers_monday_through_sunday() -> None:
    assert isinstance(DAYS, str)
    assert DAYS == "1234567"
    assert len(DAYS) == 7


def test_periods_covers_twelve_canonical_codes() -> None:
    assert isinstance(PERIODS, str)
    assert PERIODS == "123456789abc"
    assert len(PERIODS) == 12


def test_course_categories_values() -> None:
    assert isinstance(COURSE_CATEGORIES, tuple)
    assert COURSE_CATEGORIES == ("必修", "選修")


def test_period_times_matches_explicit_schedule() -> None:
    expected: dict[str, tuple[time, time]] = {
        "1": (time(8, 10), time(9, 0)),
        "2": (time(9, 10), time(10, 0)),
        "3": (time(10, 10), time(11, 0)),
        "4": (time(11, 10), time(12, 0)),
        "5": (time(12, 10), time(13, 0)),
        "6": (time(13, 10), time(14, 0)),
        "7": (time(14, 10), time(15, 0)),
        "8": (time(15, 10), time(16, 0)),
        "9": (time(16, 10), time(17, 0)),
        "a": (time(17, 10), time(18, 0)),
        "b": (time(18, 10), time(19, 0)),
        "c": (time(19, 10), time(20, 0)),
    }

    assert PERIOD_TIMES == expected
    assert list(PERIOD_TIMES.keys()) == list(PERIODS)


def test_period_times_intervals_are_ordered_50_minutes_with_breaks() -> None:
    anchor = date(2026, 1, 1)
    previous_end: time | None = None

    for period in PERIODS:
        start, end = PERIOD_TIMES[period]
        assert start < end
        duration = datetime.combine(anchor, end) - datetime.combine(anchor, start)
        assert duration == timedelta(minutes=50)
        if previous_end is not None:
            assert previous_end < start
        previous_end = end


def test_exception_hierarchy_structure() -> None:
    assert issubclass(ScheduleError, Exception)
    assert issubclass(ValidationError, ScheduleError)
    assert issubclass(NotFoundError, ScheduleError)
    assert issubclass(DuplicateIdError, ScheduleError)

    assert not issubclass(NotFoundError, ValidationError)
    assert not issubclass(DuplicateIdError, ValidationError)
    assert not issubclass(NotFoundError, DuplicateIdError)


def test_validation_error_normalizes_single_string() -> None:
    err = ValidationError("學分必須為正整數")

    assert isinstance(err, ScheduleError)
    assert err.errors == ["學分必須為正整數"]
    assert "學分必須為正整數" in str(err)


def test_validation_error_normalizes_sequence_and_makes_defensive_copy() -> None:
    raw_list = ["課程代號不可為空", "學分必須大於 0"]
    err_from_list = ValidationError(raw_list)
    raw_list.append("後續新增不應影響")

    assert err_from_list.errors == ["課程代號不可為空", "學分必須大於 0"]
    assert "課程代號不可為空" in str(err_from_list)
    assert "學分必須大於 0" in str(err_from_list)

    err_from_tuple = ValidationError(("錯誤一", "錯誤二"))
    assert isinstance(err_from_tuple.errors, list)
    assert err_from_tuple.errors == ["錯誤一", "錯誤二"]
    assert "錯誤一" in str(err_from_tuple)
    assert "錯誤二" in str(err_from_tuple)


@pytest.mark.parametrize("empty_input", ["", "   ", [], (), ["", "   "]])
def test_validation_error_empty_input_defaults_to_fallback(empty_input: str | Sequence[str]) -> None:
    err = ValidationError(empty_input)

    assert err.errors == ["驗證失敗"]
    assert "驗證失敗" in str(err)


def test_validation_error_filters_blank_entries_from_mixed_sequence() -> None:
    err = ValidationError(["", "欄位格式錯誤", "   "])

    assert err.errors == ["欄位格式錯誤"]
    assert "欄位格式錯誤" in str(err)


@pytest.mark.parametrize(
    ("exc_cls", "message"),
    [
        (NotFoundError, "找不到課程 CS101"),
        (DuplicateIdError, "課程代號重複: CS101"),
    ],
)
def test_other_schedule_errors_preserve_message_and_catch_as_base(
    exc_cls: type[ScheduleError],
    message: str,
) -> None:
    with pytest.raises(ScheduleError) as exc_info:
        raise exc_cls(message)

    assert isinstance(exc_info.value, exc_cls)
    assert message in str(exc_info.value)
