# `openapi-batch`

A small Python library that makes **batch LLM requests** reliable and easy across providers.

It handles:

* async submission (non-blocking by default)
* retries and partial failures
* durable progress tracking (SQLite)
* provider differences (OpenAI, Gemini, others)
* callbacks when results are ready

You submit items → you get a job handle → results arrive later.

---

## Install

```bash
pip install openapi-batch
```

Optional provider extras:

```bash
pip install openapi-batch[openai]
pip install openapi-batch[gemini]
pip install openapi-batch[openai,gemini]
```

---

## Quick example

### Async batch with callback (recommended)

```python
from openapi.batch import BatchClient

def on_done(job):
    print("status:", job.status())
    print(job.results_dict())

client = BatchClient(
    provider="openai",
    api_key="...",
    default_model="gpt-4o-mini",
)

job = client.map(
    mode="native",   # native | emulated | auto
    items=[
        {"item_id": "a", "input": {"prompt": "Return OK"}},
        {"item_id": "b", "input": {"prompt": "Return YES"}},
    ],
    on_complete=on_done,
)

print("submitted:", job.job_id)
```

Submission returns immediately.
Processing happens in the background.

---

### Blocking usage (for scripts/tests)

```python
job = client.map(items=items, async_submit=False)
job.wait()

results = job.results_dict()
```

---

## Concepts (brief)

### Job

A batch execution with a stable `job_id`.
Stored durably in SQLite.

### Item

One logical request. Identified by `item_id`.
If you don’t provide one, a deterministic ID is generated.

### Modes

* **emulated** – concurrency-controlled requests (works everywhere)
* **native** – provider batch APIs (OpenAI, Gemini)
* **auto** – native if available, otherwise emulated

### Results

Always mapped back by `item_id`.

```python
{
  "a": ResultOk(...),
  "b": ResultErr(...)
}
```

Partial success is normal and expected.

---

## Providers

Currently supported:

* OpenAI
* Gemini
* Local echo (testing)

Providers are internal adapters.
You do **not** need to build a gateway.

---

## Persistence

Each job is stored in SQLite:

* survives process restarts
* supports retries
* allows progress inspection

```python
job.progress()
job.status()
```

---

## Logging

Enable lightweight progress logs:

```bash
export OPENAPI_BATCH_LOG=1
```

You’ll see submission, polling, heartbeats, and completion.

---

## Testing

### Unit tests (fast)

* local_echo provider
* no network

### Integration tests (real APIs)

```bash
export OPENAI_API_KEY=...
export GEMINI_API_KEY=...

pytest -m integration
```

Integration tests are opt-in and may incur cost.

---

## What this library does *not* try to do

* It does not abstract prompts
* It does not hide provider semantics
* It does not invent new APIs

It focuses only on **batch execution, reliability, and DX**.

---

## License

MIT