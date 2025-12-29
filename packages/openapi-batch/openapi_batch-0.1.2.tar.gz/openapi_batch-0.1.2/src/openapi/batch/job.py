from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, Callable

from .models import JobStatus, ResultErr, ResultOk
from .store import SQLiteStore, Progress


OnComplete = Callable[["JobHandle"], None]


@dataclass(frozen=True)
class JobHandle:
    job_id: str
    store: SQLiteStore

    def info(self) -> Dict[str, Any]:
        return self.store.get_job(self.job_id)

    def status(self) -> JobStatus:
        return JobStatus(self.info()["status"])

    def progress(self) -> Progress:
        return self.store.get_progress(self.job_id)

    def results_dict(self) -> Dict[str, ResultOk[Any] | ResultErr]:
        out: Dict[str, ResultOk[Any] | ResultErr] = {}
        for it in self.store.list_items(self.job_id):
            if it["result"] is not None:
                out[it["item_id"]] = ResultOk(
                    item_id=it["item_id"],
                    value=it["result"]["value"],
                    raw=it["result"].get("raw"),
                )
            elif it["error"] is not None:
                e = it["error"]
                out[it["item_id"]] = ResultErr(
                    item_id=it["item_id"],
                    error_type=e.get("error_type", "unknown"),
                    message=e.get("message", ""),
                    retryable=bool(e.get("retryable", False)),
                    raw=e.get("raw"),
                )
        return out

    def wait(self, *, poll_s: float = 0.5, timeout_s: Optional[float] = None) -> JobStatus:
        start = time.time()
        while True:
            st = self.status()
            if st in {JobStatus.COMPLETED, JobStatus.PARTIAL, JobStatus.FAILED, JobStatus.CANCELED}:
                return st
            if timeout_s is not None and (time.time() - start) > timeout_s:
                return st
            time.sleep(poll_s)

    def on_complete(
        self,
        callback: OnComplete,
        *,
        poll_s: float = 0.5,
        timeout_s: Optional[float] = None,
        daemon: bool = True,
    ) -> None:
        """
        Register a callback that will be invoked once the job becomes terminal.

        This does NOT require holding onto BatchClient, and is useful if you only have job_id/store.
        """

        def watcher() -> None:
            self.wait(poll_s=poll_s, timeout_s=timeout_s)
            callback(self)

        t = threading.Thread(target=watcher, name=f"openapi-batch-wait-{self.job_id}", daemon=daemon)
        t.start()
