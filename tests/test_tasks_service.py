"""Unit tests for the public functions in app/services/tasks.py."""

from datetime import date

import pytest

from app.errors import NotFoundError, ValidationError
from app.extensions import db
from app.models import PRIORITIES, Task, TaskStatus
from app.services.tasks import (
    MAX_TITLE_LENGTH,
    complete_task,
    create_task,
    delete_task,
    get_task,
    list_tasks,
    update_task,
)

pytestmark = pytest.mark.usefixtures("app")

MISSING_ID = 9999
BLANK_TITLES = [None, "", "   ", "\t\n "]
BAD_PRIORITIES = [None, "", "   ", "urgent", "HIGH"]
BAD_STATUSES = ["", "   ", "archived", "TODO"]
BAD_DUE_DATES = ["not-a-date", "   ", "2026-13-01", "2026-02-30", "01/02/2026", 20260101]

TITLE_REQUIRED = "title is required"
TITLE_TOO_LONG = f"title must be at most {MAX_TITLE_LENGTH} characters"
PRIORITY_INVALID = "priority must be one of low, medium, high"
STATUS_INVALID = "status must be one of todo, in_progress, completed, done"
DUE_DATE_INVALID = "due_date must be a date in YYYY-MM-DD format"


def reload(task_id):
    """Return the task as stored in the database, ignoring unflushed session state."""
    db.session.expire_all()
    return db.session.get(Task, task_id)


class TestCreateTask:
    def test_title_only_uses_defaults(self):
        task = create_task("Write report")

        assert task.id is not None
        assert task.title == "Write report"
        assert task.description == ""
        assert task.priority == "medium"
        assert task.status == TaskStatus.TODO
        assert task.due_date is None
        assert task.created_at is not None

    def test_all_fields_are_persisted(self):
        task_id = create_task(
            "Write report", description="Quarterly", priority="high", due_date="2026-12-31"
        ).id

        stored = reload(task_id)
        assert stored.title == "Write report"
        assert stored.description == "Quarterly"
        assert stored.priority == "high"
        assert stored.due_date == date(2026, 12, 31)

    def test_title_is_stripped(self):
        assert create_task("  Write report \n").title == "Write report"

    def test_non_string_title_is_converted(self):
        assert create_task(123).title == "123"

    def test_title_at_limit_is_accepted(self):
        title = "x" * MAX_TITLE_LENGTH
        assert create_task(title).title == title

    def test_limit_applies_after_stripping(self):
        title = "x" * MAX_TITLE_LENGTH
        assert create_task(f"  {title}  ").title == title

    def test_title_over_limit_is_rejected(self):
        with pytest.raises(ValidationError) as exc:
            create_task("x" * (MAX_TITLE_LENGTH + 1))
        assert exc.value.message == TITLE_TOO_LONG

    @pytest.mark.parametrize("title", BLANK_TITLES)
    def test_blank_title_is_rejected(self, title):
        with pytest.raises(ValidationError) as exc:
            create_task(title)
        assert exc.value.message == TITLE_REQUIRED

    def test_description_is_stripped(self):
        assert create_task("t", description="  details  ").description == "details"

    @pytest.mark.parametrize("description", [None, "", "   "])
    def test_blank_description_becomes_empty_string(self, description):
        assert create_task("t", description=description).description == ""

    @pytest.mark.parametrize("priority", PRIORITIES)
    def test_each_allowed_priority_is_accepted(self, priority):
        assert create_task("t", priority=priority).priority == priority

    @pytest.mark.parametrize("priority", BAD_PRIORITIES)
    def test_invalid_priority_is_rejected(self, priority):
        with pytest.raises(ValidationError) as exc:
            create_task("t", priority=priority)
        assert exc.value.message == PRIORITY_INVALID

    def test_due_date_accepts_date_object(self):
        assert create_task("t", due_date=date(2026, 12, 31)).due_date == date(2026, 12, 31)

    @pytest.mark.parametrize("due_date", [None, ""])
    def test_blank_due_date_becomes_none(self, due_date):
        assert create_task("t", due_date=due_date).due_date is None

    @pytest.mark.parametrize("due_date", BAD_DUE_DATES)
    def test_invalid_due_date_is_rejected(self, due_date):
        with pytest.raises(ValidationError) as exc:
            create_task("t", due_date=due_date)
        assert exc.value.message == DUE_DATE_INVALID

    @pytest.mark.parametrize(
        "kwargs",
        [
            {"title": None},
            {"title": "t", "priority": "urgent"},
            {"title": "t", "due_date": "not-a-date"},
        ],
    )
    def test_rejected_task_is_not_saved(self, kwargs):
        with pytest.raises(ValidationError):
            create_task(**kwargs)
        assert list_tasks() == []


class TestGetTask:
    def test_returns_the_matching_task(self):
        create_task("first")
        second = create_task("second")

        assert get_task(second.id) is second

    def test_missing_id_raises_not_found(self):
        with pytest.raises(NotFoundError) as exc:
            get_task(MISSING_ID)
        assert exc.value.message == f"task {MISSING_ID} not found"

    @pytest.mark.filterwarnings("ignore:fully NULL primary key")
    def test_none_id_raises_not_found(self):
        with pytest.raises(NotFoundError) as exc:
            get_task(None)
        assert exc.value.message == "task None not found"


class TestListTasks:
    def test_empty_database_returns_empty_list(self):
        assert list_tasks() == []

    def test_returns_all_tasks_oldest_first(self):
        tasks = [create_task(title) for title in ("c", "a", "b")]

        assert list_tasks() == tasks

    def test_filters_by_status(self):
        todo = create_task("todo")
        started = create_task("started")
        update_task(started.id, status=TaskStatus.IN_PROGRESS)

        assert list_tasks(status=TaskStatus.TODO) == [todo]
        assert list_tasks(status=TaskStatus.IN_PROGRESS) == [started]

    def test_filters_by_priority(self):
        low = create_task("low", priority="low")
        create_task("high", priority="high")

        assert list_tasks(priority="low") == [low]

    def test_combines_status_and_priority_filters(self):
        match = create_task("match", priority="high")
        create_task("wrong priority", priority="low")
        wrong_status = create_task("wrong status", priority="high")
        update_task(wrong_status.id, status=TaskStatus.COMPLETED)

        assert list_tasks(status=TaskStatus.TODO, priority="high") == [match]

    def test_valid_filter_with_no_matches_returns_empty_list(self):
        create_task("t", priority="low")

        assert list_tasks(priority="high") == []
        assert list_tasks(status=TaskStatus.COMPLETED) == []

    @pytest.mark.parametrize("status", BAD_STATUSES)
    def test_invalid_status_filter_is_rejected(self, status):
        with pytest.raises(ValidationError) as exc:
            list_tasks(status=status)
        assert exc.value.message == STATUS_INVALID

    @pytest.mark.parametrize("priority", [p for p in BAD_PRIORITIES if p is not None])
    def test_invalid_priority_filter_is_rejected(self, priority):
        with pytest.raises(ValidationError) as exc:
            list_tasks(priority=priority)
        assert exc.value.message == PRIORITY_INVALID


class TestUpdateTask:
    def test_updates_every_field_and_persists(self):
        task_id = create_task("old").id

        returned = update_task(
            task_id,
            title="new",
            description="details",
            priority="high",
            due_date="2026-12-31",
            status=TaskStatus.IN_PROGRESS,
        )

        assert returned.id == task_id
        stored = reload(task_id)
        assert stored.title == "new"
        assert stored.description == "details"
        assert stored.priority == "high"
        assert stored.due_date == date(2026, 12, 31)
        assert stored.status == TaskStatus.IN_PROGRESS

    def test_only_given_fields_change(self):
        task_id = create_task("old", description="keep", priority="low", due_date="2026-12-31").id

        update_task(task_id, title="new")

        stored = reload(task_id)
        assert stored.title == "new"
        assert stored.description == "keep"
        assert stored.priority == "low"
        assert stored.due_date == date(2026, 12, 31)
        assert stored.status == TaskStatus.TODO

    def test_no_fields_leaves_task_unchanged(self):
        task_id = create_task("old").id

        assert update_task(task_id).title == "old"

    def test_title_is_stripped(self):
        assert update_task(create_task("old").id, title="  new  ").title == "new"

    def test_title_at_limit_is_accepted(self):
        title = "x" * MAX_TITLE_LENGTH
        assert update_task(create_task("old").id, title=title).title == title

    def test_title_over_limit_is_rejected(self):
        task_id = create_task("old").id
        with pytest.raises(ValidationError) as exc:
            update_task(task_id, title="x" * (MAX_TITLE_LENGTH + 1))
        assert exc.value.message == TITLE_TOO_LONG

    @pytest.mark.parametrize("title", BLANK_TITLES)
    def test_blank_title_is_rejected(self, title):
        task_id = create_task("old").id
        with pytest.raises(ValidationError) as exc:
            update_task(task_id, title=title)
        assert exc.value.message == TITLE_REQUIRED

    def test_description_is_stripped(self):
        assert update_task(create_task("t").id, description="  new ").description == "new"

    @pytest.mark.parametrize("description", [None, "", "   "])
    def test_blank_description_clears_it(self, description):
        task_id = create_task("t", description="old").id

        assert update_task(task_id, description=description).description == ""

    @pytest.mark.parametrize("priority", BAD_PRIORITIES)
    def test_invalid_priority_is_rejected(self, priority):
        task_id = create_task("t").id
        with pytest.raises(ValidationError) as exc:
            update_task(task_id, priority=priority)
        assert exc.value.message == PRIORITY_INVALID

    @pytest.mark.parametrize(
        "status", [TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.COMPLETED]
    )
    def test_each_allowed_status_is_accepted(self, status):
        assert update_task(create_task("t").id, status=status).status == status

    def test_legacy_done_status_is_stored_as_completed(self):
        task_id = create_task("t").id

        assert update_task(task_id, status=TaskStatus.DONE).status == TaskStatus.COMPLETED
        assert reload(task_id).status == TaskStatus.COMPLETED

    def test_legacy_done_status_filter_matches_completed_tasks(self):
        task = create_task("t")
        complete_task(task.id)

        assert list_tasks(status=TaskStatus.DONE) == [task]

    @pytest.mark.parametrize("status", [None, *BAD_STATUSES])
    def test_invalid_status_is_rejected(self, status):
        task_id = create_task("t").id
        with pytest.raises(ValidationError) as exc:
            update_task(task_id, status=status)
        assert exc.value.message == STATUS_INVALID

    def test_due_date_accepts_date_object(self):
        task_id = create_task("t").id

        assert update_task(task_id, due_date=date(2026, 12, 31)).due_date == date(2026, 12, 31)

    @pytest.mark.parametrize("due_date", [None, ""])
    def test_blank_due_date_clears_it(self, due_date):
        task_id = create_task("t", due_date="2026-12-31").id

        assert update_task(task_id, due_date=due_date).due_date is None

    @pytest.mark.parametrize("due_date", BAD_DUE_DATES)
    def test_invalid_due_date_is_rejected(self, due_date):
        task_id = create_task("t").id
        with pytest.raises(ValidationError) as exc:
            update_task(task_id, due_date=due_date)
        assert exc.value.message == DUE_DATE_INVALID

    def test_unknown_field_is_rejected(self):
        task_id = create_task("t").id
        with pytest.raises(ValidationError) as exc:
            update_task(task_id, owner="me")
        assert exc.value.message == "cannot update field(s): owner"

    def test_multiple_unknown_fields_are_listed_sorted(self):
        task_id = create_task("t").id
        with pytest.raises(ValidationError) as exc:
            update_task(task_id, zeta=1, id=2)
        assert exc.value.message == "cannot update field(s): id, zeta"

    def test_unknown_field_is_reported_before_missing_task(self):
        with pytest.raises(ValidationError):
            update_task(MISSING_ID, owner="me")

    def test_missing_id_raises_not_found(self):
        with pytest.raises(NotFoundError) as exc:
            update_task(MISSING_ID, title="new")
        assert exc.value.message == f"task {MISSING_ID} not found"

    @pytest.mark.filterwarnings("ignore:fully NULL primary key")
    def test_none_id_raises_not_found(self):
        with pytest.raises(NotFoundError):
            update_task(None, title="new")

    def test_failed_update_commits_nothing(self):
        task_id = create_task("old").id

        with pytest.raises(ValidationError):
            update_task(task_id, title="new", priority="urgent")

        db.session.rollback()
        assert reload(task_id).title == "old"


class TestCompleteTask:
    def test_status_becomes_completed(self):
        task_id = create_task("t").id

        complete_task(task_id)

        assert reload(task_id).status == TaskStatus.COMPLETED

    def test_returns_the_task_with_status_changed_and_persisted(self):
        task_id = create_task("t").id

        returned = complete_task(task_id)

        assert returned.id == task_id
        assert reload(task_id).status != TaskStatus.TODO

    def test_other_fields_and_tasks_are_untouched(self):
        task_id = create_task("t", description="d", priority="high", due_date="2026-12-31").id
        other_id = create_task("other").id

        complete_task(task_id)

        stored = reload(task_id)
        assert stored.title == "t"
        assert stored.description == "d"
        assert stored.priority == "high"
        assert stored.due_date == date(2026, 12, 31)
        assert reload(other_id).status == TaskStatus.TODO

    def test_completing_twice_keeps_the_same_status(self):
        task_id = create_task("t").id
        first_status = complete_task(task_id).status

        assert complete_task(task_id).status == first_status

    def test_missing_id_raises_not_found(self):
        with pytest.raises(NotFoundError) as exc:
            complete_task(MISSING_ID)
        assert exc.value.message == f"task {MISSING_ID} not found"

    @pytest.mark.filterwarnings("ignore:fully NULL primary key")
    def test_none_id_raises_not_found(self):
        with pytest.raises(NotFoundError):
            complete_task(None)


class TestDeleteTask:
    def test_removes_the_task(self):
        task_id = create_task("t").id

        assert delete_task(task_id) is None

        with pytest.raises(NotFoundError):
            get_task(task_id)

    def test_other_tasks_remain(self):
        doomed = create_task("doomed")
        kept = create_task("kept")

        delete_task(doomed.id)

        assert list_tasks() == [kept]

    def test_missing_id_raises_not_found(self):
        with pytest.raises(NotFoundError) as exc:
            delete_task(MISSING_ID)
        assert exc.value.message == f"task {MISSING_ID} not found"

    def test_deleting_twice_raises_not_found(self):
        task_id = create_task("t").id
        delete_task(task_id)

        with pytest.raises(NotFoundError):
            delete_task(task_id)

    @pytest.mark.filterwarnings("ignore:fully NULL primary key")
    def test_none_id_raises_not_found(self):
        with pytest.raises(NotFoundError):
            delete_task(None)
