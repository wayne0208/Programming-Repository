"""Unified exception hierarchy for the datamodel package."""

from collections.abc import Sequence

__all__ = [
    "DuplicateIdError",
    "NotFoundError",
    "ScheduleError",
    "ValidationError",
]


class ScheduleError(Exception):
    """Base exception for all scheduling and datamodel errors."""


class ValidationError(ScheduleError):
    """Exception raised when one or more entity field validations fail."""

    def __init__(self, errors: str | Sequence[str]) -> None:
        if isinstance(errors, str):
            normalized = [errors] if errors.strip() else []
        else:
            normalized = [msg for msg in errors if msg.strip()]

        if not normalized:
            normalized = ["驗證失敗"]

        self.errors: list[str] = normalized
        super().__init__("; ".join(self.errors))


class NotFoundError(ScheduleError):
    """Exception raised when a requested entity cannot be found."""


class DuplicateIdError(ScheduleError):
    """Exception raised when attempting to insert a duplicate entity ID."""
