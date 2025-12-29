# openapi-batch

`openapi-batch` is a small Python library for running batches of LLM requests reliably.

It provides:
- **Async submission by default** (you don’t block while the batch runs)
- **Durable state** in SQLite (track progress, resume inspection)
- **Retries + partial failure handling**
- **Native batch support** where providers offer it (OpenAI, Gemini)
- **Provider adapters** (no gateway required)
- **Callbacks** for progress, per-item completion, and job completion

---

## Install

```bash
pip install openapi-batch
````

Provider extras:

```bash
pip install openapi-batch[openai]
pip install openapi-batch[gemini]
pip install openapi-batch[openai,gemini]
```

---

## Quick start

### Async batch with callbacks (recommended)

```python
from openapi.batch import BatchClient

def on_progress(job, p):
    # p is store.Progress for emulated jobs, NativeProgress for native polling
    print("progress:", p)

def on_item(job, item_id, result):
    print("item:", item_id, result)

def on_complete(job):
    print("done:", job.status())

client = BatchClient(
    provider="openai",
    api_key="...",
    default_model="gpt-4o-mini",
)

job = client.map(
    mode="native",  # native | emulated | auto
    items=[
        {"item_id": "a", "input": {"prompt": "Return OK"}},
        {"item_id": "b", "input": {"prompt": "Return YES"}},
    ],
    on_progress=on_progress,
    on_item=on_item,
    on_complete=on_complete,
)

print("submitted:", job.job_id)
```

The call returns immediately. Processing happens in the background.

---

### Run callbacks in a thread pool

If your callbacks do I/O (write to DB, publish to queue, HTTP calls), run them in a thread pool:

```python
job = client.map(
    items=items,
    on_progress=on_progress,
    on_item=on_item,
    on_complete=on_complete,
    callback_executor="thread",
    callback_workers=8,
)
```

---

### Blocking mode (useful for scripts/tests)

```python
job = client.map(items=items, async_submit=False)
job.wait()

results = job.results_dict()
print(results)
```

---

## Concepts

### Job

A batch execution with a stable `job_id`. Stored in SQLite.

```python
job.status()
job.progress()
job.info()
```

### Item

One request in the batch, identified by `item_id`. If you don’t provide it, a deterministic ID is generated.

### Result mapping

Results are returned as a dict keyed by `item_id`.

```python
results = job.results_dict()
ok = results["a"]      # ResultOk
err = results["b"]     # ResultErr
```

---

## Modes

* **emulated**: concurrency-controlled requests (works for any provider adapter)
* **native**: provider batch APIs (OpenAI, Gemini)
* **auto**: uses native if available, otherwise emulated

---

## Logging

Enable lightweight progress logs:

```bash
export OPENAPI_BATCH_LOG=1
```

---

## Providers

Currently included:

* OpenAI
* Gemini
* local_echo (tests)

No gateway required — pass the provider to `BatchClient`.

---

## Testing

Unit tests:

```bash
pytest
```

Integration tests (real APIs, opt-in, may incur cost):

```bash
export OPENAI_API_KEY=...
export GEMINI_API_KEY=...
pytest -m integration
```

---

## What this library does not try to do

* Prompt abstraction
* Workflow orchestration
* Hiding provider semantics

It focuses only on batch execution, durability, and developer experience.

---

## License

MIT