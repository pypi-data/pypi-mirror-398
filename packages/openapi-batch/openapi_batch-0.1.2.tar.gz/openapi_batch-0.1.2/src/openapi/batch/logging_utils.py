# src/openapi/batch/logging_utils.py
from __future__ import annotations

import os
import sys
import time
from typing import Any


def _enabled() -> bool:
    v = os.environ.get("OPENAPI_BATCH_LOG", "").strip().lower()
    return v not in {"", "0", "false", "no"}


def log(msg: str, **kv: Any) -> None:
    """
    Minimal stderr logger, enabled when OPENAPI_BATCH_LOG=1.
    """
    if not _enabled():
        return
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    extra = ""
    if kv:
        extra = " " + " ".join(f"{k}={repr(v)}" for k, v in kv.items())
    sys.stderr.write(f"[openapi-batch] {ts} {msg}{extra}\n")
    sys.stderr.flush()
