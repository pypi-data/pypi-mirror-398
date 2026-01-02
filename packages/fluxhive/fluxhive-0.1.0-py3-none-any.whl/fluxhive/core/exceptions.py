"""Common exception types for FlowHive agent."""

from __future__ import annotations

from typing import Optional


class TaskExecutionError(RuntimeError):
    """Wrapper for subprocess failures."""

    def __init__(self, message: str, return_code: Optional[int] = None) -> None:
        super().__init__(message)
        self.return_code = return_code


__all__ = ["TaskExecutionError"]


