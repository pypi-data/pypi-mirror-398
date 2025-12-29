from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AuthError(RuntimeError):
    message: str
    status_code: int | None = None
    error: str | None = None
    error_description: str | None = None
    details: dict[str, Any] | None = None

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.message
