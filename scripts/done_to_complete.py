"""One-off data migration for BUG-17: rewrite legacy "done" statuses to "completed".

Usage (uses DATABASE_URL, or sqlite:///tasks.db by default):

    python scripts/migrate_done_to_completed.py

Safe to run more than once; later runs update zero rows.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models import Task, TaskStatus  # noqa: E402


def main():
    """Update every task with the legacy DONE status to COMPLETED and report the count."""
    app = create_app()
    with app.app_context():
        updated = Task.query.filter_by(status=TaskStatus.DONE).update(
            {"status": TaskStatus.COMPLETED}, synchronize_session=False
        )
        db.session.commit()
        print(f"Updated {updated} task(s) from '{TaskStatus.DONE}' to '{TaskStatus.COMPLETED}'.")


if __name__ == "__main__":
    main()