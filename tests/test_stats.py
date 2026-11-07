"""Characterization tests for task_summary in app/services/stats.py and the GET /stats route."""

from datetime import date, timedelta

import pytest

import app.services.stats as stats_module
from app.models import TaskStatus
from app.services.stats import task_summary
from app.services.tasks import complete_task, create_task, update_task

pytestmark = pytest.mark.usefixtures("app")

TODAY = date(2026, 6, 15)
YESTERDAY = TODAY - timedelta(days=1)
TOMORROW = TODAY + timedelta(days=1)

EMPTY_SUMMARY = {
    "total": 0,
    "todo": 0,
    "in_progress": 0,
    "completed": 0,
    "overdue": 0,
    "completion_rate": 0.0,
}


def make_task(status=TaskStatus.TODO, due_date=None):
    """Create a task with the given status and due date, and return it."""
    task = create_task("t", due_date=due_date)
    if status == TaskStatus.COMPLETED:
        complete_task(task.id)
    elif status != TaskStatus.TODO:
        update_task(task.id, status=status)
    return task


class TestEmptyDatabase:
    def test_all_counts_are_zero_and_rate_is_zero(self):
        assert task_summary(today=TODAY) == EMPTY_SUMMARY


class TestStatusCounts:
    def test_counts_each_status(self):
        make_task(TaskStatus.TODO)
        make_task(TaskStatus.TODO)
        make_task(TaskStatus.TODO)
        make_task(TaskStatus.IN_PROGRESS)
        make_task(TaskStatus.IN_PROGRESS)
        make_task(TaskStatus.COMPLETED)

        summary = task_summary(today=TODAY)

        assert summary["total"] == 6
        assert summary["todo"] == 3
        assert summary["in_progress"] == 2
        assert summary["completed"] == 1

    @pytest.mark.parametrize(
        ("status", "key"),
        [
            (TaskStatus.TODO, "todo"),
            (TaskStatus.IN_PROGRESS, "in_progress"),
            (TaskStatus.COMPLETED, "completed"),
        ],
    )
    def test_single_task_is_counted_only_in_its_own_status(self, status, key):
        make_task(status)

        summary = task_summary(today=TODAY)

        assert summary["total"] == 1
        for other in ("todo", "in_progress", "completed"):
            assert summary[other] == (1 if other == key else 0)


class TestCompletionRate:
    def test_one_of_three_completed_rounds_to_one_decimal(self):
        make_task(TaskStatus.COMPLETED)
        make_task(TaskStatus.TODO)
        make_task(TaskStatus.IN_PROGRESS)

        assert task_summary(today=TODAY)["completion_rate"] == 33.3

    def test_all_completed_is_one_hundred(self):
        make_task(TaskStatus.COMPLETED)
        make_task(TaskStatus.COMPLETED)

        assert task_summary(today=TODAY)["completion_rate"] == 100.0

    def test_none_completed_is_zero(self):
        make_task(TaskStatus.TODO)

        assert task_summary(today=TODAY)["completion_rate"] == 0.0


class TestOverdue:
    def test_due_yesterday_is_overdue(self):
        make_task(due_date=YESTERDAY)

        assert task_summary(today=TODAY)["overdue"] == 1

    def test_due_today_is_not_overdue(self):
        make_task(due_date=TODAY)

        assert task_summary(today=TODAY)["overdue"] == 0

    def test_due_tomorrow_is_not_overdue(self):
        make_task(due_date=TOMORROW)

        assert task_summary(today=TODAY)["overdue"] == 0

    def test_no_due_date_is_not_overdue(self):
        make_task(due_date=None)

        assert task_summary(today=TODAY)["overdue"] == 0

    def test_completed_past_due_task_is_not_overdue(self):
        make_task(TaskStatus.COMPLETED, due_date=YESTERDAY)

        assert task_summary(today=TODAY)["overdue"] == 0

    def test_in_progress_past_due_task_is_overdue(self):
        make_task(TaskStatus.IN_PROGRESS, due_date=YESTERDAY)

        assert task_summary(today=TODAY)["overdue"] == 1

    def test_counts_only_the_overdue_tasks_in_a_mix(self):
        make_task(due_date=YESTERDAY)
        make_task(due_date=TODAY)
        make_task(due_date=TOMORROW)
        make_task(due_date=None)
        make_task(TaskStatus.COMPLETED, due_date=YESTERDAY)

        summary = task_summary(today=TODAY)

        assert summary["total"] == 5
        assert summary["overdue"] == 1


class TestDefaultToday:
    def test_uses_date_today_when_today_is_not_given(self, monkeypatch):
        class FixedDate(date):
            @classmethod
            def today(cls):
                return cls(TODAY.year, TODAY.month, TODAY.day)

        monkeypatch.setattr(stats_module, "date", FixedDate)
        make_task(due_date=YESTERDAY)
        make_task(due_date=TODAY)

        assert task_summary()["overdue"] == 1


class TestStatsRoute:
    def test_empty_database_returns_zero_summary(self, client):
        response = client.get("/stats")

        assert response.status_code == 200
        assert response.get_json() == EMPTY_SUMMARY

    def test_returns_summary_for_stored_tasks(self, client):
        client.post("/tasks", json={"title": "a", "due_date": "2000-01-01"})
        client.post("/tasks", json={"title": "b"})
        done_id = client.post("/tasks", json={"title": "c"}).get_json()["id"]
        client.post(f"/tasks/{done_id}/complete")

        response = client.get("/stats")

        assert response.status_code == 200
        assert response.get_json() == {
            "total": 3,
            "todo": 2,
            "in_progress": 0,
            "completed": 1,
            "overdue": 1,
            "completion_rate": 33.3,
        }
