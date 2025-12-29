from __future__ import annotations

import asyncio
import os
import threading
import time
import uuid
from typing import Any, Callable, Dict, Iterable, List, Optional, Literal

from .callbacks import CallbackRunner, NativeProgress, OnComplete, OnItem, OnProgress
from .ids import stable_id
from .job import JobHandle
from .logging_utils import log
from .models import BatchItem, ItemState, JobStatus, ResultErr, ResultOk
from .providers.registry import ProviderConfig, make_provider
from .retry import RetryPolicy
from .runtime.emulated import EmulatedOptions, run_emulated_job
from .store import SQLiteStore


class BatchClient:
    def __init__(
        self,
        *,
        provider: str,
        api_key: Optional[str] = None,
        default_model: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout_s: float = 60.0,
        db_path: str = "./batches.db",
        default_retry: Optional[RetryPolicy] = None,
        openai_endpoint: str = "/v1/chat/completions",
        openai_completion_window: str = "24h",
        openai_poll_interval_s: float = 5.0,
        gemini_poll_interval_s: float = 5.0,
        native_poll_heartbeat_s: float = 30.0,
    ):
        self.provider_name = provider
        self.api_key = api_key or self._env_key(provider)
        self.default_model = default_model
        self.base_url = base_url
        self.timeout_s = timeout_s

        self.openai_endpoint = openai_endpoint
        self.openai_completion_window = openai_completion_window
        self.openai_poll_interval_s = openai_poll_interval_s

        self.gemini_poll_interval_s = gemini_poll_interval_s
        self.native_poll_heartbeat_s = native_poll_heartbeat_s

        self.store = SQLiteStore(db_path)
        self.default_retry = default_retry or RetryPolicy.default()

        self._provider = make_provider(
            ProviderConfig(
                provider=provider,
                api_key=self.api_key,
                default_model=default_model,
                base_url=base_url,
                timeout_s=timeout_s,
            )
        )

    @staticmethod
    def _env_key(provider: str) -> Optional[str]:
        p = (provider or "").lower().strip()
        if p == "openai":
            return os.environ.get("OPENAI_API_KEY")
        if p == "gemini":
            return os.environ.get("GEMINI_API_KEY")
        return None

    def new_job_id(self) -> str:
        return f"job_{uuid.uuid4().hex[:16]}"

    def map(
        self,
        *,
        items: Iterable[Dict[str, Any] | BatchItem],
        job_id: Optional[str] = None,
        tags: Optional[Dict[str, Any]] = None,
        mode: str = "emulated",  # emulated|auto|native
        decode: Optional[Callable[[Any], Any]] = None,
        retry: Optional[RetryPolicy] = None,
        concurrency: int = 50,
        async_submit: bool = True,
        on_complete: Optional[OnComplete] = None,
        on_progress: Optional[OnProgress] = None,
        on_item: Optional[OnItem] = None,
        # NEW:
        callback_executor: Literal["inline", "thread"] = "inline",
        callback_workers: int = 4,
    ) -> JobHandle:
        job_id = job_id or self.new_job_id()
        retry = retry or self.default_retry

        if mode not in {"emulated", "auto", "native"}:
            raise ValueError("mode must be one of: emulated|auto|native")

        self.store.create_job(job_id=job_id, provider=self.provider_name, mode=mode, tags=tags)

        normalized: List[Dict[str, Any]] = []
        for it in items:
            if isinstance(it, BatchItem):
                item_id = it.item_id
                inp = it.input
                meta = it.meta or {}
            else:
                inp = dict(it.get("input") or {})
                meta = dict(it.get("meta") or {})
                item_id = it.get("item_id") or stable_id({"input": inp, "meta": meta}, namespace=job_id)
            normalized.append({"item_id": item_id, "input": inp, "meta": meta})

        self.store.add_items(job_id, normalized)

        handle = JobHandle(job_id=job_id, store=self.store)

        cb_runner = CallbackRunner(mode=callback_executor, max_workers=callback_workers)

        # Wrap callbacks to run through executor
        def _on_progress(job: JobHandle, progress: Any) -> None:
            if on_progress:
                try:
                    cb_runner.submit(on_progress, job, progress)
                except Exception as e:
                    log("callback.on_progress.exception", job_id=job_id, error=str(e))

        def _on_item(job: JobHandle, item_id: str, result: Any) -> None:
            if on_item:
                try:
                    cb_runner.submit(on_item, job, item_id, result)
                except Exception as e:
                    log("callback.on_item.exception", job_id=job_id, item_id=item_id, error=str(e))

        def _on_complete(job: JobHandle) -> None:
            if on_complete:
                try:
                    cb_runner.submit(on_complete, job)
                except Exception as e:
                    log("callback.on_complete.exception", job_id=job_id, error=str(e))

        def runner() -> None:
            try:
                self._execute_job(
                    job_id=job_id,
                    mode=mode,
                    items=normalized,
                    decode=decode,
                    retry=retry,
                    concurrency=concurrency,
                    on_progress=_on_progress if on_progress else None,
                    on_item=_on_item if on_item else None,
                )
            except Exception as e:
                log("job.runner.exception", job_id=job_id, error=str(e))
                try:
                    self.store.set_job_status(job_id, JobStatus.FAILED)
                except Exception:
                    pass
            finally:
                # complete callback always runs last
                if on_complete:
                    try:
                        _on_complete(handle)
                    except Exception:
                        pass
                # shutdown callback runner (non-blocking)
                cb_runner.shutdown()

        if async_submit:
            t = threading.Thread(target=runner, name=f"openapi-batch-{job_id}", daemon=True)
            t.start()
            log(
                "job.submitted.async",
                job_id=job_id,
                mode=mode,
                provider=self.provider_name,
                callback_executor=callback_executor,
                callback_workers=callback_workers,
            )
            return handle

        runner()
        return handle

    def _execute_job(
        self,
        *,
        job_id: str,
        mode: str,
        items: List[Dict[str, Any]],
        decode: Optional[Callable[[Any], Any]],
        retry: RetryPolicy,
        concurrency: int,
        on_progress: Optional[OnProgress],
        on_item: Optional[OnItem],
    ) -> None:
        chosen = mode
        if mode == "auto":
            chosen = "native" if getattr(self._provider, "native_batch_supported", lambda: False)() else "emulated"

        if chosen == "native":
            p = self.provider_name.lower().strip()
            if p == "openai":
                self._run_openai_native_batch(job_id=job_id, items=items, decode=decode, on_progress=on_progress, on_item=on_item)
                return
            if p == "gemini":
                self._run_gemini_native_batch(job_id=job_id, items=items, decode=decode, on_progress=on_progress, on_item=on_item)
                return

        self.store.set_job_mode(job_id, "emulated")
        asyncio.run(
            run_emulated_job(
                store=self.store,
                provider=self._provider,
                job_id=job_id,
                retry=retry,
                decode=decode,
                options=EmulatedOptions(concurrency=concurrency),
                on_item=on_item,
                on_progress=on_progress,
            )
        )

    # ----------------------------
    # OpenAI native (only callback emissions changed)
    # ----------------------------
    def _run_openai_native_batch(
        self,
        *,
        job_id: str,
        items: List[Dict[str, Any]],
        decode: Optional[Callable[[Any], Any]] = None,
        on_progress: Optional[OnProgress] = None,
        on_item: Optional[OnItem] = None,
    ) -> None:
        from .providers.openai_provider import OpenAIProvider, _to_chat_body

        if not isinstance(self._provider, OpenAIProvider):
            raise RuntimeError("native openai batch requires OpenAIProvider")

        handle = JobHandle(job_id=job_id, store=self.store)

        self.store.set_job_status(job_id, JobStatus.RUNNING)
        self.store.set_job_mode(job_id, "native")

        default_model = self.default_model or ""
        log("openai.native.submit.start", job_id=job_id, endpoint=self.openai_endpoint)

        req_lines: List[Dict[str, Any]] = []
        for it in items:
            item_id = it["item_id"]
            inp = it["input"] or {}
            model_for_item = inp.get("model") or default_model
            body = _to_chat_body(inp, default_model=model_for_item)
            req_lines.append({"custom_id": item_id, "method": "POST", "url": self.openai_endpoint, "body": body})
            self.store.bump_attempts(job_id, item_id)

        batch_id = self._provider.native_batch_create(
            job_id=job_id,
            endpoint=self.openai_endpoint,
            completion_window=self.openai_completion_window,
            requests=req_lines,
            metadata={"job_id": job_id},
        )
        self.store.set_provider_job_ref(job_id, batch_id)
        log("openai.native.submit.done", job_id=job_id, batch_id=batch_id)

        terminal_statuses = {"completed", "failed", "expired", "cancelled"}
        last_status = None
        last_counts = None
        last_heartbeat = 0.0
        started = time.time()

        while True:
            b = self._provider.native_batch_retrieve(batch_id=batch_id)
            st = (b.get("status") or "").lower()
            counts = b.get("request_counts") or {}
            key_counts = (counts.get("total"), counts.get("completed"), counts.get("failed"))

            elapsed = int(time.time() - started)
            now = time.time()

            if st != last_status or key_counts != last_counts:
                log("openai.native.poll", job_id=job_id, batch_id=batch_id, status=st, elapsed_s=elapsed, **counts)
                last_status = st
                last_counts = key_counts
                if on_progress:
                    on_progress(
                        handle,
                        NativeProgress(
                            provider="openai",
                            job_id=job_id,
                            status=st,
                            total=counts.get("total"),
                            completed=counts.get("completed"),
                            failed=counts.get("failed"),
                            elapsed_s=elapsed,
                            provider_job_ref=batch_id,
                        ),
                    )

            if on_progress and (now - last_heartbeat >= self.native_poll_heartbeat_s):
                on_progress(
                    handle,
                    NativeProgress(
                        provider="openai",
                        job_id=job_id,
                        status=st,
                        total=counts.get("total"),
                        completed=counts.get("completed"),
                        failed=counts.get("failed"),
                        elapsed_s=elapsed,
                        provider_job_ref=batch_id,
                    ),
                )
                last_heartbeat = now

            if st in terminal_statuses:
                batch_obj = b
                break

            time.sleep(self.openai_poll_interval_s)

        status = (batch_obj.get("status") or "").lower()
        output_file_id = batch_obj.get("output_file_id")
        error_file_id = batch_obj.get("error_file_id")

        output_map: Dict[str, Dict[str, Any]] = {}
        error_map: Dict[str, Dict[str, Any]] = {}

        if output_file_id:
            out_text = self._provider.native_file_content_text(file_id=output_file_id)
            output_map = OpenAIProvider.parse_output_jsonl(out_text)

        if error_file_id:
            err_text = self._provider.native_file_content_text(file_id=error_file_id)
            error_map = OpenAIProvider.parse_output_jsonl(err_text)

        for it in items:
            item_id = it["item_id"]

            if item_id in output_map:
                line = output_map[item_id]
                resp = (line.get("response") or {})
                body = resp.get("body")

                output_text = ""
                try:
                    choices = (body or {}).get("choices") or []
                    if choices:
                        output_text = choices[0]["message"]["content"]
                except Exception:
                    output_text = ""

                value: Any = {"output": output_text, "response": resp, "batch_line": line}
                if decode:
                    try:
                        value = decode(value)
                    except Exception:
                        pass

                self.store.mark_ok(job_id, item_id, {"value": value, "raw": line})
                if on_item:
                    on_item(handle, item_id, ResultOk(item_id=item_id, value=value, raw=line))
                continue

            if item_id in error_map:
                line = error_map[item_id]
                err = line.get("error") or {"message": "batch_error"}
                msg = err.get("message") if isinstance(err, dict) else str(err)

                err_obj = {"error_type": "batch_error", "message": msg, "retryable": False, "raw": line}
                self.store.mark_err(job_id, item_id, err_obj, state=ItemState.DEAD)
                if on_item:
                    on_item(handle, item_id, ResultErr(item_id=item_id, error_type="batch_error", message=msg, retryable=False, raw=line))
                continue

            err_obj = {
                "error_type": "batch_missing",
                "message": f"Not present in output/error files (batch status={status})",
                "retryable": False,
                "raw": {"batch_id": batch_id, "status": status},
            }
            self.store.mark_err(job_id, item_id, err_obj, state=ItemState.DEAD)
            if on_item:
                on_item(handle, item_id, ResultErr(item_id=item_id, error_type="batch_missing", message=err_obj["message"], retryable=False, raw=err_obj["raw"]))

        prog = self.store.get_progress(job_id)
        if prog.ok == prog.total and prog.total > 0:
            self.store.set_job_status(job_id, JobStatus.COMPLETED)
        elif prog.ok > 0:
            self.store.set_job_status(job_id, JobStatus.PARTIAL)
        else:
            self.store.set_job_status(job_id, JobStatus.FAILED)

        if on_progress:
            on_progress(handle, self.store.get_progress(job_id))

        log("openai.native.done", job_id=job_id, batch_id=batch_id, ok=prog.ok, dead=prog.dead, total=prog.total)

    # ----------------------------
    # Gemini native (only callback emissions changed)
    # ----------------------------
    def _run_gemini_native_batch(
        self,
        *,
        job_id: str,
        items: List[Dict[str, Any]],
        decode: Optional[Callable[[Any], Any]] = None,
        on_progress: Optional[OnProgress] = None,
        on_item: Optional[OnItem] = None,
    ) -> None:
        from .providers.gemini_provider import GeminiProvider, _to_generate_content_request

        if not isinstance(self._provider, GeminiProvider):
            raise RuntimeError("native gemini batch requires GeminiProvider")

        handle = JobHandle(job_id=job_id, store=self.store)

        self.store.set_job_status(job_id, JobStatus.RUNNING)
        self.store.set_job_mode(job_id, "native")

        req_lines: List[Dict[str, Any]] = []
        batch_model = self.default_model

        item_models = []
        for it in items:
            inp = it["input"] or {}
            if "model" in inp:
                item_models.append(inp["model"])
        if item_models and len(set(item_models)) == 1:
            batch_model = item_models[0]

        if not batch_model:
            raise RuntimeError("Gemini native batch requires default_model or consistent input.model across items.")

        for it in items:
            item_id = it["item_id"]
            inp = it["input"] or {}
            req = _to_generate_content_request(inp, default_model=batch_model)
            req_lines.append({"key": item_id, "request": req})
            self.store.bump_attempts(job_id, item_id)

        batch_name = self._provider.native_batch_create(
            job_id=job_id,
            endpoint="",
            completion_window="",
            requests=req_lines,
            metadata={"job_id": job_id, "model": batch_model, "display_name": f"openapi-batch-{job_id}"},
        )
        self.store.set_provider_job_ref(job_id, batch_name)

        terminal = {"JOB_STATE_SUCCEEDED", "JOB_STATE_FAILED", "JOB_STATE_CANCELLED", "JOB_STATE_EXPIRED", "JOB_STATE_PAUSED"}
        last_state = None
        last_heartbeat = 0.0
        started = time.time()

        batch_obj: Dict[str, Any] | None = None
        while True:
            b = self._provider.native_batch_retrieve(batch_id=batch_name)
            state = (b.get("state") or {}).get("name") if isinstance(b.get("state"), dict) else None
            if not state:
                state = str(b.get("state") or "")

            elapsed = int(time.time() - started)
            now = time.time()
            stats = b.get("batch_stats")

            if state != last_state:
                last_state = state
                if on_progress:
                    on_progress(
                        handle,
                        NativeProgress(
                            provider="gemini",
                            job_id=job_id,
                            status=state,
                            elapsed_s=elapsed,
                            provider_job_ref=batch_name,
                            extra={"batch_stats": stats} if stats else None,
                        ),
                    )

            if on_progress and (now - last_heartbeat >= self.native_poll_heartbeat_s):
                on_progress(
                    handle,
                    NativeProgress(
                        provider="gemini",
                        job_id=job_id,
                        status=state,
                        elapsed_s=elapsed,
                        provider_job_ref=batch_name,
                        extra={"batch_stats": stats} if stats else None,
                    ),
                )
                last_heartbeat = now

            if state in terminal:
                batch_obj = b
                break

            time.sleep(self.gemini_poll_interval_s)

        dest = (batch_obj or {}).get("dest") or {}
        result_file = dest.get("file_name") or dest.get("fileName")

        if not result_file:
            for it in items:
                item_id = it["item_id"]
                err_obj = {
                    "error_type": "batch_missing_dest",
                    "message": f"Batch finished but dest.file_name missing. state={batch_obj.get('state')}",
                    "retryable": False,
                    "raw": batch_obj,
                }
                self.store.mark_err(job_id, item_id, err_obj, state=ItemState.DEAD)
                if on_item:
                    on_item(handle, item_id, ResultErr(item_id=item_id, error_type="batch_missing_dest", message=err_obj["message"], retryable=False, raw=batch_obj))
            self.store.set_job_status(job_id, JobStatus.FAILED)
            if on_progress:
                on_progress(handle, self.store.get_progress(job_id))
            return

        text = self._provider.native_file_content_text(file_id=result_file)
        out_map = GeminiProvider.parse_result_jsonl(text)

        for it in items:
            item_id = it["item_id"]
            line = out_map.get(item_id)
            if not line:
                err_obj = {"error_type": "batch_missing", "message": "Missing key in output file.", "retryable": False, "raw": None}
                self.store.mark_err(job_id, item_id, err_obj, state=ItemState.DEAD)
                if on_item:
                    on_item(handle, item_id, ResultErr(item_id=item_id, error_type="batch_missing", message=err_obj["message"], retryable=False, raw=None))
                continue

            if "error" in line and line["error"]:
                msg = str(line["error"])
                err_obj = {"error_type": "batch_error", "message": msg, "retryable": False, "raw": line}
                self.store.mark_err(job_id, item_id, err_obj, state=ItemState.DEAD)
                if on_item:
                    on_item(handle, item_id, ResultErr(item_id=item_id, error_type="batch_error", message=msg, retryable=False, raw=line))
                continue

            resp = line.get("response") or line.get("result") or line.get("generateContentResponse")
            if not isinstance(resp, dict):
                resp = line if ("candidates" in line or "text" in line) else {}

            output_text = GeminiProvider.extract_text_from_generate_content_response(resp)

            value: Any = {"output": output_text, "response": resp, "batch_line": line}
            if decode:
                try:
                    value = decode(value)
                except Exception:
                    pass

            self.store.mark_ok(job_id, item_id, {"value": value, "raw": line})
            if on_item:
                on_item(handle, item_id, ResultOk(item_id=item_id, value=value, raw=line))

        prog = self.store.get_progress(job_id)
        if prog.ok == prog.total and prog.total > 0:
            self.store.set_job_status(job_id, JobStatus.COMPLETED)
        elif prog.ok > 0:
            self.store.set_job_status(job_id, JobStatus.PARTIAL)
        else:
            self.store.set_job_status(job_id, JobStatus.FAILED)

        if on_progress:
            on_progress(handle, self.store.get_progress(job_id))
