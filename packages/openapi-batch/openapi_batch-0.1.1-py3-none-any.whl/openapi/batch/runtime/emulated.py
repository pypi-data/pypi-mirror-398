# src/openapi/batch/runtime/emulated.py
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

from ..models import ItemState, JobStatus
from ..retry import RetryPolicy
from ..store import SQLiteStore
from ..providers.base import ProviderError, BaseProvider
from ..logging_utils import log


@dataclass(frozen=True)
class EmulatedOptions:
    concurrency: int = 50
    claim_batch: int = 200
    poll_interval_s: float = 0.2


async def run_emulated_job(
    *,
    store: SQLiteStore,
    provider: BaseProvider,
    job_id: str,
    retry: RetryPolicy,
    decode: Optional[Callable[[Any], Any]] = None,
    options: EmulatedOptions = EmulatedOptions(),
) -> None:
    store.set_job_status(job_id, JobStatus.RUNNING)
    sem = asyncio.Semaphore(max(1, options.concurrency))

    async def handle_one(item: Dict[str, Any]) -> None:
        item_id = item["item_id"]
        async with sem:
            attempt = store.bump_attempts(job_id, item_id)
            try:
                raw = await provider.call_one(input=item["input"], meta=item.get("meta") or {})
                val = decode(raw) if decode else raw
                store.mark_ok(job_id, item_id, {"value": val, "raw": raw})
            except ProviderError as e:
                if retry.should_retry(attempt=attempt, error_type=e.error_type, retryable=e.retryable):
                    store.mark_err(
                        job_id,
                        item_id,
                        {"error_type": e.error_type, "message": e.message, "retryable": True, "raw": e.raw},
                        state=ItemState.PENDING,
                    )
                    await asyncio.to_thread(retry.sleep, attempt)
                else:
                    store.mark_err(
                        job_id,
                        item_id,
                        {"error_type": e.error_type, "message": e.message, "retryable": False, "raw": e.raw},
                        state=ItemState.DEAD,
                    )
            except Exception as e:
                store.mark_err(
                    job_id,
                    item_id,
                    {"error_type": "exception", "message": str(e), "retryable": False, "raw": None},
                    state=ItemState.DEAD,
                )

    tasks: set[asyncio.Task] = set()
    last_log = 0.0

    while True:
        tasks = {t for t in tasks if not t.done()}

        capacity = max(0, options.concurrency - len(tasks))
        if capacity > 0:
            claimed = store.claim_pending(job_id, limit=min(options.claim_batch, capacity))
            for it in claimed:
                tasks.add(asyncio.create_task(handle_one(it)))

        prog = store.get_progress(job_id)

        now = asyncio.get_event_loop().time()
        if now - last_log > 2.0:
            log(
                "emulated.progress",
                job_id=job_id,
                pending=prog.pending,
                sent=prog.sent,
                ok=prog.ok,
                dead=prog.dead,
                total=prog.total,
                inflight=len(tasks),
            )
            last_log = now

        if prog.pending == 0 and len(tasks) == 0:
            break

        await asyncio.sleep(options.poll_interval_s)

    prog = store.get_progress(job_id)
    if prog.ok == prog.total and prog.total > 0:
        store.set_job_status(job_id, JobStatus.COMPLETED)
    elif prog.ok > 0:
        store.set_job_status(job_id, JobStatus.PARTIAL)
    else:
        store.set_job_status(job_id, JobStatus.FAILED)

    log(
        "emulated.done",
        job_id=job_id,
        ok=prog.ok,
        dead=prog.dead,
        total=prog.total,
    )
