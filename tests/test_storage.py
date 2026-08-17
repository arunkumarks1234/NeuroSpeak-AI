from __future__ import annotations

import tempfile
from pathlib import Path

from storage.models import SessionRecord
from storage.sqlite_repository import SQLiteSessionRepository


def test_sqlite_repository_crud():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        repo = SQLiteSessionRepository(f"sqlite:///{db_path}")

        try:
            # Create
            record = SessionRecord(
                source="test",
                duration_seconds=5.0,
                raw_transcript="raw",
                shield_transcript="shield",
                final_transcript="final",
            )
            repo.save(record)

            assert repo.count() == 1

            # Read
            fetched = repo.get_by_id(record.id)
            assert fetched is not None
            assert fetched.id == record.id
            assert fetched.duration_seconds == 5.0

            # Read all
            all_recs = repo.get_all()
            assert len(all_recs) == 1

            # Delete
            assert repo.delete(record.id) is True
            assert repo.count() == 0
        finally:
            # Release the SQLite file handle so Windows can delete the temp dir.
            repo.dispose() # Ensure all connections are closed
            repo = None    # Explicitly dereference to aid garbage collection
