from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from .base import ProviderCaps


@dataclass
class LocalEchoProvider:
    name: str = "local_echo"

    def caps(self) -> ProviderCaps:
        return ProviderCaps(native_batch=False)

    async def call_one(self, *, input: Dict[str, Any], meta: Dict[str, Any]) -> Any:
        return {"output": {"echo": input, "meta": meta}}
