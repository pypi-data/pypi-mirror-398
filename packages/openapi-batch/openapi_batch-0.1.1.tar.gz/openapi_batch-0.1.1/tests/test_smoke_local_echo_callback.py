# tests/test_smoke_local_echo_callback.py
import threading

from openapi.batch import BatchClient, JobStatus


def test_smoke_local_echo_with_callback(tmp_path):
    db = str(tmp_path / "batches.db")
    client = BatchClient(provider="local_echo", db_path=db)

    items = [
        {"item_id": "a", "input": {"x": 1}},
        {"item_id": "b", "input": {"x": 2}},
    ]

    done = threading.Event()
    seen = {}

    def on_complete(job):
        seen["status"] = job.status()
        seen["results"] = job.results_dict()
        done.set()

    job = client.map(
        items=items,
        concurrency=10,
        on_complete=on_complete,  # 👈 callback
    )

    # Wait for callback
    assert done.wait(5), "callback was not invoked"

    assert seen["status"] in {JobStatus.COMPLETED, JobStatus.PARTIAL}

    res = seen["results"]
    assert res["a"].value["output"]["echo"]["x"] == 1
    assert res["b"].value["output"]["echo"]["x"] == 2
