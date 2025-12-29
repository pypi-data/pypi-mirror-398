from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from .base import AdapterCaps


@dataclass
class LocalEchoAdapter:
    name: str = "local_echo"

    def caps(self) -> AdapterCaps:
        return AdapterCaps(native_batch=False)

    async def call_one(self, *, input: Dict[str, Any], meta: Dict[str, Any]) -> Any:
        return {"echo": input, "meta": meta}
