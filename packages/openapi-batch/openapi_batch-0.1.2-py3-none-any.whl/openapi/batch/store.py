from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

from .models import ItemState, JobStatus


@dataclass(frozen=True)
class Progress:
    total: int
    pending: int
    sent: int
    ok: int
    err: int
    retrying: int
    dead: int


class SQLiteStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init(self) -> None:
        with self._conn() as c:
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs(
                  job_id TEXT PRIMARY KEY,
                  created_at REAL NOT NULL,
                  updated_at REAL NOT NULL,
                  status TEXT NOT NULL,
                  provider TEXT NOT NULL,
                  mode TEXT NOT NULL,
                  provider_job_ref TEXT,
                  tags_json TEXT
                )
                """
            )
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS items(
                  job_id TEXT NOT NULL,
                  item_id TEXT NOT NULL,
                  state TEXT NOT NULL,
                  attempts INTEGER NOT NULL,
                  input_json TEXT NOT NULL,
                  meta_json TEXT,
                  result_json TEXT,
                  error_json TEXT,
                  updated_at REAL NOT NULL,
                  PRIMARY KEY(job_id, item_id)
                )
                """
            )
            c.execute("CREATE INDEX IF NOT EXISTS idx_items_job_state ON items(job_id, state)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_items_job_attempts ON items(job_id, attempts)")

    # ----------------------------
    # Jobs
    # ----------------------------
    def create_job(
        self,
        job_id: str,
        provider: str,
        mode: str,
        tags: Optional[Dict[str, Any]] = None,
        provider_job_ref: Optional[str] = None,
    ) -> None:
        now = time.time()
        with self._conn() as c:
            c.execute(
                """
                INSERT INTO jobs(job_id, created_at, updated_at, status, provider, mode, provider_job_ref, tags_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (job_id, now, now, JobStatus.CREATED.value, provider, mode, provider_job_ref, json.dumps(tags or {})),
            )

    def set_job_status(self, job_id: str, status: JobStatus) -> None:
        now = time.time()
        with self._conn() as c:
            c.execute("UPDATE jobs SET status=?, updated_at=? WHERE job_id=?", (status.value, now, job_id))

    def set_provider_job_ref(self, job_id: str, provider_job_ref: str) -> None:
        now = time.time()
        with self._conn() as c:
            c.execute(
                "UPDATE jobs SET provider_job_ref=?, updated_at=? WHERE job_id=?",
                (provider_job_ref, now, job_id),
            )

    def set_job_mode(self, job_id: str, mode: str) -> None:
        now = time.time()
        with self._conn() as c:
            c.execute("UPDATE jobs SET mode=?, updated_at=? WHERE job_id=?", (mode, now, job_id))

    def get_job(self, job_id: str) -> Dict[str, Any]:
        with self._conn() as c:
            row = c.execute("SELECT * FROM jobs WHERE job_id=?", (job_id,)).fetchone()
            if not row:
                raise KeyError(f"job not found: {job_id}")
            d = dict(row)
            d["tags"] = json.loads(d["tags_json"] or "{}")
            return d

    # ----------------------------
    # Items
    # ----------------------------
    def add_items(self, job_id: str, items: Iterable[Dict[str, Any]]) -> None:
        now = time.time()
        with self._conn() as c:
            for it in items:
                c.execute(
                    """
                    INSERT OR REPLACE INTO items(job_id, item_id, state, attempts, input_json, meta_json, result_json, error_json, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, NULL, NULL, ?)
                    """,
                    (
                        job_id,
                        it["item_id"],
                        ItemState.PENDING.value,
                        0,
                        json.dumps(it["input"]),
                        json.dumps(it.get("meta") or {}),
                        now,
                    ),
                )

    def list_items(self, job_id: str) -> List[Dict[str, Any]]:
        with self._conn() as c:
            rows = c.execute("SELECT * FROM items WHERE job_id=?", (job_id,)).fetchall()
        return [self._row_to_item_dict(r) for r in rows]

    def get_progress(self, job_id: str) -> Progress:
        with self._conn() as c:
            total = c.execute("SELECT COUNT(*) AS n FROM items WHERE job_id=?", (job_id,)).fetchone()["n"]
            counts: Dict[str, int] = {}
            for st in ItemState:
                n = c.execute(
                    "SELECT COUNT(*) AS n FROM items WHERE job_id=? AND state=?",
                    (job_id, st.value),
                ).fetchone()["n"]
                counts[st.value] = int(n)
        return Progress(
            total=int(total),
            pending=counts.get(ItemState.PENDING.value, 0),
            sent=counts.get(ItemState.SENT.value, 0),
            ok=counts.get(ItemState.OK.value, 0),
            err=counts.get(ItemState.ERR.value, 0),
            retrying=counts.get(ItemState.RETRYING.value, 0),
            dead=counts.get(ItemState.DEAD.value, 0),
        )

    def claim_pending(self, job_id: str, limit: int) -> List[Dict[str, Any]]:
        """
        Atomically claim up to `limit` pending items by moving them PENDING->SENT.

        Uses BEGIN IMMEDIATE to ensure only one worker claims at a time.
        """
        now = time.time()
        with self._conn() as c:
            c.execute("BEGIN IMMEDIATE")
            rows = c.execute(
                """
                SELECT item_id, input_json, meta_json, attempts
                FROM items
                WHERE job_id=? AND state=?
                LIMIT ?
                """,
                (job_id, ItemState.PENDING.value, limit),
            ).fetchall()

            item_ids = [r["item_id"] for r in rows]
            for item_id in item_ids:
                c.execute(
                    "UPDATE items SET state=?, updated_at=? WHERE job_id=? AND item_id=?",
                    (ItemState.SENT.value, now, job_id, item_id),
                )

        out: List[Dict[str, Any]] = []
        for r in rows:
            out.append(
                {
                    "item_id": r["item_id"],
                    "input": json.loads(r["input_json"]),
                    "meta": json.loads(r["meta_json"] or "{}"),
                    "attempts": int(r["attempts"]),
                }
            )
        return out

    def bump_attempts(self, job_id: str, item_id: str) -> int:
        now = time.time()
        with self._conn() as c:
            row = c.execute(
                "SELECT attempts FROM items WHERE job_id=? AND item_id=?",
                (job_id, item_id),
            ).fetchone()
            if not row:
                raise KeyError(f"item not found: {job_id}/{item_id}")
            attempts = int(row["attempts"]) + 1
            c.execute(
                "UPDATE items SET attempts=?, updated_at=? WHERE job_id=? AND item_id=?",
                (attempts, now, job_id, item_id),
            )
        return attempts

    def mark_ok(self, job_id: str, item_id: str, result: Dict[str, Any]) -> None:
        now = time.time()
        with self._conn() as c:
            c.execute(
                """
                UPDATE items
                SET state=?, result_json=?, error_json=NULL, updated_at=?
                WHERE job_id=? AND item_id=?
                """,
                (ItemState.OK.value, json.dumps(result), now, job_id, item_id),
            )

    def mark_err(self, job_id: str, item_id: str, error: Dict[str, Any], *, state: ItemState) -> None:
        now = time.time()
        with self._conn() as c:
            c.execute(
                """
                UPDATE items
                SET state=?, error_json=?, result_json=NULL, updated_at=?
                WHERE job_id=? AND item_id=?
                """,
                (state.value, json.dumps(error), now, job_id, item_id),
            )

    def requeue_failed(self, job_id: str, *, include_dead: bool = True) -> int:
        """
        Move ERR (and optionally DEAD) back to PENDING.
        """
        now = time.time()
        from_states = [ItemState.ERR.value] + ([ItemState.DEAD.value] if include_dead else [])
        with self._conn() as c:
            q = "UPDATE items SET state=?, updated_at=? WHERE job_id=? AND state IN ({})".format(
                ",".join("?" for _ in from_states)
            )
            cur = c.execute(q, (ItemState.PENDING.value, now, job_id, *from_states))
            return int(cur.rowcount or 0)

    # ----------------------------
    # Internal helpers
    # ----------------------------
    def _row_to_item_dict(self, r: sqlite3.Row) -> Dict[str, Any]:
        return {
            "job_id": r["job_id"],
            "item_id": r["item_id"],
            "state": r["state"],
            "attempts": int(r["attempts"]),
            "input": json.loads(r["input_json"]),
            "meta": json.loads(r["meta_json"] or "{}"),
            "result": json.loads(r["result_json"]) if r["result_json"] else None,
            "error": json.loads(r["error_json"]) if r["error_json"] else None,
            "updated_at": float(r["updated_at"]),
        }
