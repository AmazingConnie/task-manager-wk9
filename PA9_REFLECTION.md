# PA 9 Questions

## 1. What was the root cause of BUG-17, and which files were involved? Why would fixing only the stats count have been the wrong fix?
The root cause was that the program was treating tasks that were marked "done" differently from tasks that were marked "completed" in services/tasks.py. Fixing only the stats count would have been the wrong fix as it would not solve the underlying bug, but rather conceal it. This would have made it difficult 

## 2. Did a Drill test fail after your fix? If so, why was updating that test the right call here, when "do not modify the tests" was the rule in Drill?
A drill test named "test_each_allowed_status_is_accepted" did fail after my fix. This is because the pytest set it was a part of used all status values including TaskStatus.DONE. The test compared the updated status of each task and compared with the equivalent status. Since services/tasks.py was modified to convert all TaskStatus.DONE tasks to TaskStatus.COMPLETED tasks, the test broke as TaskStatus.COMPLETED did not match TaskStatus.DONE. Updating the test by removing TaskStatus.DONE from the pytest set was the right call here as the program no longer tested for TaskStatus.DONE.

Also "test_status_becomes_completed" was fixed since it was designed to fail using the xfail parameter. When the bug was fixed, there was no need the mark the test as an intentional fail so I removed the xfail.

## 3. What should happen to tasks already stored in a real database with the old status value? Your fix does not have to handle it, but describe what you would do.
I would use a data migration script that would loop through the database looking for tasks with the old status value and replace them with them with the new status value. Afterwards, the script would print how many tasks with the old status value it had replaced with the new status value. Claude even generated this script during the session, but said that it was not necessary for the project. The generated script can be found in scripts/done_to_complete.py.

## 4. In B3, what did the hook report, and what did Claude do with it? How is that different from you running the tests after Claude finishes?
The hook reported that there was an unused import in services/tasks.py named import os. Since linting reports issues regarding code style and unused libraries, the hook blocked Claude from running the tests afterwards since the linting issues were not fixed. This is different from a developer running the tests after Claude finishes as the user is not forced to fix the linting problems beforehand. This causes the developer to ignore any unused libraries or indent issues in their code.

## 5. Why did you write characterization tests (C2) before refactoring? What would the hook have told you during C3 without them?
I wrote characterization tests before refactoring so that the behavior of the code before refactoring would match the behavior of the code after refactoring. Withoit characterization tests, the hook would have told me that there were linting issues with the refactored code and that the status counts were repetitive.

## Oneline Output
24eae84 (HEAD -> main) chore: add /quality command
ed7f369 refactor(stats): count statuses in one pass
fc8625c test: pin task_summary behavior before refactor
b310bd3 chore: run lint and tests after every edit
4d21bdb fix(tasks): store completed status when completing a task
bb44024 test: reproduce BUG-17
24916ad (origin/main) Changes to README and DRILL
1a85a6a feat(tasks): add case-insensitive task search
cbaabef test: add failing tests for task search
0daaf75 docs: add week 9 drill reflection changes
0549d9c test: add unit tests for task service
52a226e chore: week 9 starter code

## Quality Table (View in Raw Format)
┌───────────────┬────────────────────────────────────┬─────────────┐
│     Step      │              Command               │   Result    │
├───────────────┼────────────────────────────────────┼─────────────┤
│ 1. Format     │ ruff format --check .              │ PASS        │
│ check         │                                    │             │
├───────────────┼────────────────────────────────────┼─────────────┤
│ 2. Lint       │ ruff check .                       │ PASS        │
├───────────────┼────────────────────────────────────┼─────────────┤
│ 3. Tests +    │ pytest -q --cov=app                │ PASS (148   │
│ coverage      │ --cov-report=term-missing          │ passed)     │
├───────────────┼────────────────────────────────────┼─────────────┤
│ Total         │                                    │ 97%         │
│ coverage      │                                    │             │
└───────────────┴────────────────────────────────────┴─────────────┘
