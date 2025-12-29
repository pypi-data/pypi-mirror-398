from __future__ import annotations

import json
from .store import SQLiteStore


def export_jsonl(*, store: SQLiteStore, job_id: str, out_path: str, only: str = "all") -> int:
    items = store.list_items(job_id)
    n = 0
    with open(out_path, "w", encoding="utf-8") as f:
        for it in items:
            is_ok = it["result"] is not None
            is_err = it["error"] is not None
            if only == "ok" and not is_ok:
                continue
            if only == "err" and not is_err:
                continue

            row = {
                "job_id": it["job_id"],
                "item_id": it["item_id"],
                "state": it["state"],
                "attempts": it["attempts"],
                "input": it["input"],
                "meta": it["meta"],
                "result": it["result"],
                "error": it["error"],
                "updated_at": it["updated_at"],
            }
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            n += 1
    return n
