from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx

from .base import AdapterCaps, AdapterError


@dataclass
class HTTPJSONAdapter:
    """
    Generic adapter that POSTs JSON to your gateway endpoint.

    Request body:
      {"input": <dict>, "meta": <dict>}
    Response:
      any JSON

    This is the cleanest way to support "any provider" in practice:
    standardize provider differences behind your gateway.
    """

    endpoint: str
    headers: Optional[Dict[str, str]] = None
    timeout_s: float = 60.0

    name: str = "http_json"

    def caps(self) -> AdapterCaps:
        return AdapterCaps(native_batch=False)

    async def call_one(self, *, input: Dict[str, Any], meta: Dict[str, Any]) -> Any:
        try:
            async with httpx.AsyncClient(timeout=self.timeout_s) as client:
                r = await client.post(
                    self.endpoint,
                    json={"input": input, "meta": meta},
                    headers=self.headers or {},
                )
        except httpx.TimeoutException as e:
            raise AdapterError("timeout", str(e), True) from e
        except httpx.RequestError as e:
            raise AdapterError("network", str(e), True) from e

        if r.status_code == 429:
            raise AdapterError("rate_limit", f"HTTP 429: {r.text[:500]}", True, raw=r.text)
        if 500 <= r.status_code <= 599:
            raise AdapterError("provider_5xx", f"HTTP {r.status_code}: {r.text[:500]}", True, raw=r.text)
        if r.status_code >= 400:
            raise AdapterError("bad_request", f"HTTP {r.status_code}: {r.text[:500]}", False, raw=r.text)

        try:
            return r.json()
        except Exception as e:
            raise AdapterError("decode", f"Invalid JSON response: {e}", False, raw=r.text) from e
