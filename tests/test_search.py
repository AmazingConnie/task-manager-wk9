"""Tests for task search, written from the spec before the feature exists."""

import pytest

from app.errors import ValidationError
from app.services import tasks as svc

SEARCH_URL = "/tasks/search"
BLANK_QUERIES = ["", "   ", "\t\n "]


def titles(tasks):
    """Return the titles of the given tasks, in order."""
    return [task.title for task in tasks]


@pytest.mark.usefixtures("app")
class TestSearchTasksWhitespace:
    @pytest.mark.parametrize("query", ["  report", "report  ", "  report  "])
    def test_leading_and_trailing_spaces_are_ignored(self, query):
        svc.create_task("report")
        svc.create_task("other")

        assert titles(svc.search_tasks(query)) == ["report"]


@pytest.mark.usefixtures("app")
class TestSearchTasksOrder:
    def test_results_are_newest_first(self):
        ids = [svc.create_task("report").id for _ in range(3)]

        results = svc.search_tasks("report")

        assert [task.id for task in results] == sorted(ids, reverse=True)

    def test_non_matching_tasks_do_not_affect_order(self):
        oldest = svc.create_task("report").id
        svc.create_task("other")
        newest = svc.create_task("report").id

        assert [task.id for task in svc.search_tasks("report")] == [newest, oldest]


@pytest.mark.usefixtures("app")
class TestSearchTasksEmptyQuery:
    @pytest.mark.parametrize("query", BLANK_QUERIES)
    def test_blank_query_raises_validation_error(self, query):
        svc.create_task("report")

        with pytest.raises(ValidationError):
            svc.search_tasks(query)

    def test_none_query_raises_validation_error(self):
        svc.create_task("report")

        with pytest.raises(ValidationError):
            svc.search_tasks(None)


@pytest.mark.usefixtures("app")
class TestSearchTasksSpecialCharacters:
    def test_percent_does_not_match_other_characters(self):
        svc.create_task("500")
        svc.create_task("50%")

        assert titles(svc.search_tasks("50%")) == ["50%"]

    def test_percent_alone_does_not_match_everything(self):
        svc.create_task("report")

        assert svc.search_tasks("%") == []

    def test_underscore_does_not_match_a_single_character(self):
        svc.create_task("abc")
        svc.create_task("a_c")

        assert titles(svc.search_tasks("a_c")) == ["a_c"]

    def test_underscore_alone_does_not_match_everything(self):
        svc.create_task("report")

        assert svc.search_tasks("_") == []


class TestSearchRoute:
    def test_returns_matches_as_json_newest_first(self, client):
        oldest = client.post("/tasks", json={"title": "report"}).get_json()["id"]
        client.post("/tasks", json={"title": "other"})
        newest = client.post("/tasks", json={"title": "report"}).get_json()["id"]

        response = client.get(SEARCH_URL, query_string={"query": "  report  "})

        assert response.status_code == 200
        assert [task["id"] for task in response.get_json()] == [newest, oldest]

    def test_special_characters_match_literally(self, client):
        client.post("/tasks", json={"title": "500"})
        client.post("/tasks", json={"title": "50%"})

        response = client.get(SEARCH_URL, query_string={"query": "50%"})

        assert response.status_code == 200
        assert [task["title"] for task in response.get_json()] == ["50%"]

    def test_missing_query_returns_400(self, client):
        response = client.get(SEARCH_URL)

        assert response.status_code == 400
        assert "query" in response.get_json()["error"]

    @pytest.mark.parametrize("query", BLANK_QUERIES)
    def test_blank_query_returns_400(self, client, query):
        response = client.get(SEARCH_URL, query_string={"query": query})

        assert response.status_code == 400
        assert "query" in response.get_json()["error"]
