# tests/test_smoke_local_echo.py
from openapi.batch import BatchClient, JobStatus


def test_smoke_local_echo(tmp_path):
    db = str(tmp_path / "batches.db")
    client = BatchClient(provider="local_echo", db_path=db)

    items = [
        {"item_id": "a", "input": {"x": 1}, "meta": {"k": "v"}},
        {"item_id": "b", "input": {"x": 2}},
    ]

    # async by default now
    job = client.map(items=items, concurrency=10)

    # Explicitly wait for completion
    status = job.wait(timeout_s=10)
    assert status in {JobStatus.COMPLETED, JobStatus.PARTIAL}

    res = job.results_dict()

    assert res["a"].value["output"]["echo"]["x"] == 1
    assert res["b"].value["output"]["echo"]["x"] == 2
