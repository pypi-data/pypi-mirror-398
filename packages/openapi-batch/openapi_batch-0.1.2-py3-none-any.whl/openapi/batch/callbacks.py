from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Optional, Protocol, Literal
from concurrent.futures import ThreadPoolExecutor


class JobHandleLike(Protocol):
    job_id: str

    def progress(self) -> Any: ...
    def status(self) -> Any: ...
    def results_dict(self) -> Any: ...


@dataclass(frozen=True)
class NativeProgress:
    """
    Progress object for native batch providers during polling.

    For emulated jobs, you'll typically receive store.Progress.
    """
    provider: str
    job_id: str
    status: str
    total: int | None = None
    completed: int | None = None
    failed: int | None = None
    elapsed_s: int | None = None
    provider_job_ref: str | None = None
    extra: dict[str, Any] | None = None


# Callback types
OnComplete = Callable[[JobHandleLike], None]
OnProgress = Callable[[JobHandleLike, Any], None]  # store.Progress | NativeProgress | dict
OnItem = Callable[[JobHandleLike, str, Any], None]  # ResultOk|ResultErr or raw dict


CallbackExecutorMode = Literal["inline", "thread"]


class CallbackRunner:
    """
    Runs callbacks either inline or in a thread pool.

    - inline: execute immediately in caller thread
    - thread: submit to ThreadPoolExecutor (fire-and-forget)
    """

    def __init__(self, mode: CallbackExecutorMode = "inline", max_workers: int = 4):
        self.mode = mode
        self.max_workers = max_workers
        self._pool: ThreadPoolExecutor | None = None
        if self.mode == "thread":
            self._pool = ThreadPoolExecutor(max_workers=max(1, int(max_workers)), thread_name_prefix="openapi-batch-cb")

    def submit(self, fn: Optional[Callable[..., Any]], *args: Any, **kwargs: Any) -> None:
        if fn is None:
            return

        if self.mode == "inline" or self._pool is None:
            try:
                fn(*args, **kwargs)
            except Exception:
                # swallow
                return
            return

        # thread pool
        def _run() -> None:
            try:
                fn(*args, **kwargs)
            except Exception:
                return

        try:
            self._pool.submit(_run)
        except Exception:
            # If the executor is shutting down or unavailable, fallback inline best-effort.
            try:
                fn(*args, **kwargs)
            except Exception:
                return

    def shutdown(self) -> None:
        if self._pool is not None:
            try:
                self._pool.shutdown(wait=False, cancel_futures=False)
            except Exception:
                pass
            self._pool = None
