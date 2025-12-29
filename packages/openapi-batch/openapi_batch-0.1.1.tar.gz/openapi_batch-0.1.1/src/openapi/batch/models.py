from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Generic, Optional, TypeVar, Union

T = TypeVar("T")


class JobStatus(str, Enum):
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    CANCELED = "CANCELED"


class ItemState(str, Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    OK = "OK"
    ERR = "ERR"
    RETRYING = "RETRYING"
    DEAD = "DEAD"


@dataclass(frozen=True)
class BatchItem:
    item_id: str
    input: Dict[str, Any]
    meta: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class ResultOk(Generic[T]):
    item_id: str
    value: T
    raw: Any | None = None


@dataclass(frozen=True)
class ResultErr:
    item_id: str
    error_type: str
    message: str
    retryable: bool
    raw: Any | None = None


ItemResult = Union[ResultOk[T], ResultErr]
