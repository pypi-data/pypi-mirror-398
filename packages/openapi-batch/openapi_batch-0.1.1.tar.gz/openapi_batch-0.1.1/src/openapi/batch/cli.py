from __future__ import annotations

import argparse
import json
import os
from typing import List, Optional

from .client import BatchClient
from .export import export_jsonl


def _load_items_jsonl(path: str) -> list[dict]:
    items = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))
    return items


def cmd_run(args: argparse.Namespace) -> None:
    client = BatchClient(
        provider=args.provider,
        api_key=args.api_key,
        default_model=args.model,
        base_url=args.base_url,
        timeout_s=args.timeout,
        db_path=args.db,
        openai_endpoint=args.openai_endpoint,
        openai_completion_window=args.openai_completion_window,
        openai_poll_interval_s=args.openai_poll_interval_s,
        gemini_poll_interval_s=args.gemini_poll_interval_s,
    )

    items = _load_items_jsonl(args.items)
    job = client.map(items=items, tags={"cli": True}, concurrency=args.concurrency, mode=args.mode)

    info = job.info()
    prog = job.progress()
    print(json.dumps({"job_id": job.job_id, "status": info["status"], "progress": prog.__dict__}, indent=2))


def cmd_status(args: argparse.Namespace) -> None:
    from .store import SQLiteStore

    store = SQLiteStore(args.db)
    job = store.get_job(args.job)
    prog = store.get_progress(args.job)
    print(json.dumps({"job": job, "progress": prog.__dict__}, indent=2))


def cmd_export(args: argparse.Namespace) -> None:
    from .store import SQLiteStore

    store = SQLiteStore(args.db)
    n = export_jsonl(store=store, job_id=args.job, out_path=args.out, only=args.only)
    print(json.dumps({"exported": n, "out": args.out}, indent=2))


def cmd_retry(args: argparse.Namespace) -> None:
    client = BatchClient(
        provider=args.provider,
        api_key=args.api_key,
        default_model=args.model,
        base_url=args.base_url,
        timeout_s=args.timeout,
        db_path=args.db,
        openai_endpoint=args.openai_endpoint,
        openai_completion_window=args.openai_completion_window,
        openai_poll_interval_s=args.openai_poll_interval_s,
        gemini_poll_interval_s=args.gemini_poll_interval_s,
    )

    job = client.retry_failed(job_id=args.job, concurrency=args.concurrency)
    info = job.info()
    prog = job.progress()
    print(json.dumps({"job_id": job.job_id, "status": info["status"], "progress": prog.__dict__}, indent=2))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="openapi-batch")
    sub = p.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run", help="Run a batch job from items.jsonl")
    run.add_argument("--provider", choices=["openai", "gemini", "local_echo"], required=True)
    run.add_argument("--db", required=True, help="Path to SQLite db file")
    run.add_argument("--items", required=True, help="Path to items.jsonl")
    run.add_argument("--concurrency", type=int, default=50)
    run.add_argument("--mode", choices=["emulated", "auto", "native"], default="emulated")

    run.add_argument("--api-key", default=None, help="Provider API key (or env OPENAI_API_KEY/GEMINI_API_KEY)")
    run.add_argument("--model", default=None, help="Default model (used if item.input.model missing)")
    run.add_argument("--base-url", default=None, help="Provider base URL (OpenAI only; optional)")
    run.add_argument("--timeout", type=float, default=60.0)

    run.add_argument("--openai-endpoint", default="/v1/chat/completions")
    run.add_argument("--openai-completion-window", default="24h")
    run.add_argument("--openai-poll-interval-s", type=float, default=5.0)
    run.add_argument("--gemini-poll-interval-s", type=float, default=5.0)

    run.set_defaults(func=cmd_run)

    st = sub.add_parser("status", help="Show job status + progress")
    st.add_argument("--db", required=True)
    st.add_argument("--job", required=True)
    st.set_defaults(func=cmd_status)

    ex = sub.add_parser("export", help="Export items/results/errors to JSONL")
    ex.add_argument("--db", required=True)
    ex.add_argument("--job", required=True)
    ex.add_argument("--out", required=True)
    ex.add_argument("--only", choices=["all", "ok", "err"], default="all")
    ex.set_defaults(func=cmd_export)

    ry = sub.add_parser("retry", help="Retry failed items for an existing job")
    ry.add_argument("--provider", choices=["openai", "gemini", "local_echo"], required=True)
    ry.add_argument("--db", required=True)
    ry.add_argument("--job", required=True)
    ry.add_argument("--concurrency", type=int, default=50)

    ry.add_argument("--api-key", default=None)
    ry.add_argument("--model", default=None)
    ry.add_argument("--base-url", default=None)
    ry.add_argument("--timeout", type=float, default=60.0)

    ry.add_argument("--openai-endpoint", default="/v1/chat/completions")
    ry.add_argument("--openai-completion-window", default="24h")
    ry.add_argument("--openai-poll-interval-s", type=float, default=5.0)
    ry.add_argument("--gemini-poll-interval-s", type=float, default=5.0)

    ry.set_defaults(func=cmd_retry)

    return p


def main() -> None:
    p = build_parser()
    args = p.parse_args()
    args.func(args)
