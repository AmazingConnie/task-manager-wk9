## A1 Prompt
Write a regression test for this bug report in tests/test_bug17.py,
using the client fixture:

BUG-17: Completed tasks don't count as completed
Steps:
1. POST /tasks with {"title": "Write report"} -> id 1
2. POST /tasks with {"title": "Buy milk"} -> id 2
3. POST /tasks/1/complete
4. GET /stats
5. GET /tasks?status=completed
Expected: step 4 shows completed: 1 and completion_rate: 50.0;
step 5 returns task 1.
Actual: step 4 shows completed: 0 and completion_rate: 0.0;
step 5 returns [].

The test must follow the steps and assert the Expected results.
Do not fix anything yet. Run the test and show me that it fails.

## A2 Prompt
The test in tests/test_bug17.py fails: 
client = <FlaskClient <Flask 'app'>>

    def test_bug17_completed_task_counts_in_stats_and_status_filter(client):
        """A completed task is counted by /stats and returned by ?status=completed."""
        # Step 1
        resp = client.post("/tasks", json={"title": "Write report"})
        assert resp.status_code == 201
        first_id = resp.get_json()["id"]
        assert first_id == 1
    
        # Step 2
        resp = client.post("/tasks", json={"title": "Buy milk"})
        assert resp.status_code == 201
        assert resp.get_json()["id"] == 2
    
        # Step 3
        resp = client.post(f"/tasks/{first_id}/complete")
        assert resp.status_code == 200
    
        # Step 4
        resp = client.get("/stats")
        assert resp.status_code == 200
        stats = resp.get_json()
>       assert stats["completed"] == 1
E       assert 0 == 1

tests/test_bug17.py:25: AssertionError

Trace the path from POST /tasks/<id>/complete to GET /stats and to
GET /tasks?status=completed. Explain the root cause and list every file
involved. Then propose a fix and its side effects, including what happens
to tasks already stored with the old value.
Do not change any files yet.

## B3 Prompt
Hook reported that the linting tool found an unused import. Because the hook runs ruff check. and pytest after every edit, the hook rejected the edit. This action also blocked pytest from running.