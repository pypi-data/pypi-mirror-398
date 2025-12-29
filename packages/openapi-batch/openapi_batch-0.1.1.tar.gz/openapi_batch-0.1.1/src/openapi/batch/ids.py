from __future__ import annotations

import hashlib
import json
from typing import Any, Dict


def stable_id(payload: Dict[str, Any], namespace: str = "") -> str:
    normalized = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    h = hashlib.sha256((namespace + "\n" + normalized).encode("utf-8")).hexdigest()
    return f"item:{h[:24]}"
