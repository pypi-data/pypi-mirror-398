from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Protocol


@dataclass(frozen=True)
class AdapterCaps:
    native_batch: bool = False


class AdapterError(Exception):
    def __init__(self, error_type: str, message: str, retryable: bool, raw: Any | None = None):
        super().__init__(message)
        self.error_type = error_type
        self.message = message
        self.retryable = retryable
        self.raw = raw


class BaseAdapter(Protocol):
    """
    Provider adapter interface.

    MVP: emulated mode only. Native batch can be added later with additional methods.
    """

    name: str

    def caps(self) -> AdapterCaps: ...

    async def call_one(self, *, input: Dict[str, Any], meta: Dict[str, Any]) -> Any:
        """
        Execute a single item request. Return provider response (any JSON-like object).
        Raise AdapterError with retry classification on failures.
        """
        ...
