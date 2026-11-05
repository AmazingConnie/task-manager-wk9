# Setup


# Part A
A2.  app/services/tasks.py
Before prompt: Coverage: 45%, Missing: 18, 24, 29-31, 37-42, 60-63, 70, 72, 78-94, 99-102, 107-109
After prompt: Coverage: 100%, Missing: N/A

A4. 
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

# Part B
B1. 

Write pytest tests for a new feature from this spec: 

| Rule  | Behavior  |
| ------ | -------- |
| Whitespace | Leading and trailing spaces in the query are ignored |
| Order | Newest first (highest id first) |
| Empty query | Empty, whitespace-only or missing query raises ValidationError; the route returns 400 with "query" in the error |
| Special characters |  % and _ in the query match literally: "50%" must not match "500" |

Put them in tests/test_search.py. Import the module
(from app.services import tasks as svc) and call svc.search_tasks,
so each test fails on its own. Cover every rule, including a route test.
Do NOT implement the feature. Tests only.


# Reflection
1. What was the coverage of app/services/tasks.py at baseline and at the end? Which lines were
hardest to cover, and why?
The baseline was 100%. The lines that were the hardest to cover were probably the lines that had to do with handling dates since they required that date objects were being passed in instead of regular strings.
2. For the three tests you reviewed in A4: does each check what the code does or what it should
do? Did any test pin behavior you believe is wrong? What evidence did you use?
Each checks what the codes does or what it should do?
3. Why commit the failing tests (B3) before implementing? Describe what could go wrong if you
skipped that commit.
Committing the failing tests helps to ensure that Claude doesn't skip or rewrite the tests when you ask it to generate code for the failing tests.
4. In B2, did any test pass early or fail for the wrong reason? What did you change?
One of the tests for updating tasks had a bug for it. I did not change the code because this drill requires you not to change the existing application code.
5. If you had not been watching the session, how would you prove that Claude did not edit the
tests in B4?
You could prove it by using the /diff command to see if it edited the tests or not.

# Final Outputs
1. Output:
(.venv) rmallu@RohanLaptop:~/COMP5300/Week9/task-manager-wk9$ git log --oneline
1a85a6a (HEAD -> main) feat(tasks): add case-insensitive task search
cbaabef test: add failing tests for task search
0daaf75 (origin/main) docs: add week 9 drill reflection changes
0549d9c test: add unit tests for task service
52a226e chore: week 9 starter code

2. Final Test Output:
======================================= test session starts ========================================
platform linux -- Python 3.10.12, pytest-9.2.0, pluggy-1.7.0
rootdir: /home/rmallu/COMP5300/Week9/task-manager-wk9
configfile: pyproject.toml
testpaths: tests
plugins: cov-7.1.0
collected 128 items                                                                                

tests/test_search.py ...................                                                     [ 14%]
tests/test_smoke.py ...                                                                      [ 17%]
tests/test_tasks_service.py ................................................................ [ 67%]
...............................x..........                                                   [100%]

========================================== tests coverage ==========================================
_________________________ coverage: platform linux, python 3.10.12-final-0 _________________________

Name                       Stmts   Miss  Cover   Missing
--------------------------------------------------------
app/__init__.py               19      0   100%
app/errors.py                 14      0   100%
app/extensions.py              2      0   100%
app/models.py                 19      0   100%
app/routes/__init__.py         0      0   100%
app/routes/stats.py            6      1    83%   12
app/routes/tasks.py           32      6    81%   39, 44-45, 50, 55-56
app/services/__init__.py       0      0   100%
app/services/stats.py         28     25    11%   10-41
app/services/tasks.py         79      0   100%
--------------------------------------------------------
TOTAL                        199     32    84%
================================== 127 passed, 1 xfailed in 7.95s ==================================