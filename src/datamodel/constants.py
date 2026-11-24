"""Domain constants for schedule days, periods, times, and course categories."""

from datetime import time

__all__ = [
    "COURSE_CATEGORIES",
    "DAYS",
    "PERIODS",
    "PERIOD_TIMES",
]

DAYS: str = "1234567"

PERIODS: str = "123456789abc"

COURSE_CATEGORIES: tuple[str, ...] = ("必修", "選修")

PERIOD_TIMES: dict[str, tuple[time, time]] = {
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
