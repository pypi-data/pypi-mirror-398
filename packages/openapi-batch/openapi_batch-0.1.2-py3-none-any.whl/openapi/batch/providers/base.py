from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Protocol, Optional, Iterable


@dataclass(frozen=True)
class ProviderCaps:
    native_batch: bool = False


class ProviderError(Exception):
    def __init__(self, error_type: str, message: str, retryable: bool, raw: Any | None = None):
        super().__init__(message)
        self.error_type = error_type
        self.message = message
        self.retryable = retryable
        self.raw = raw


class BaseProvider(Protocol):
    name: str

    def caps(self) -> ProviderCaps: ...

    async def call_one(self, *, input: Dict[str, Any], meta: Dict[str, Any]) -> Any: ...
    # Optional native batch API (only implemented by some providers)

    def native_batch_supported(self) -> bool:
        return self.caps().native_batch

    def native_batch_create(
        self,
        *,
        job_id: str,
        endpoint: str,
        completion_window: str,
        requests: Iterable[Dict[str, Any]],
        metadata: Optional[Dict[str, str]] = None,
    ) -> str:
        """Return provider batch id."""
        raise NotImplementedError

    def native_batch_retrieve(self, *, batch_id: str) -> Dict[str, Any]:
        raise NotImplementedError

    def native_file_content_text(self, *, file_id: str) -> str:
        raise NotImplementedError
