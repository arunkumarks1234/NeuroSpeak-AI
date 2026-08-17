"""
NeuroSpeak-AI — SQLite Session Repository
==========================================
Implements ``SessionRepository`` using SQLAlchemy with a SQLite backend.
Zero-config for local use; swap the DATABASE_URL to PostgreSQL for production.

Tables are created automatically on first connection.
"""

from __future__ import annotations

from sqlalchemy import create_engine, desc
from sqlalchemy.orm import Session, sessionmaker

from config import config
from storage.base import SessionRepository
from storage.models import Base, SessionRecord, SessionRecordORM
from utils.logger import get_logger

logger = get_logger(__name__)


class SQLiteSessionRepository(SessionRepository):
    """
    SQLite-backed session repository using SQLAlchemy Core + ORM.

    Usage::

        repo = SQLiteSessionRepository()
        repo.save(record)
        sessions = repo.get_all(limit=20)
    """

    def __init__(self, database_url: str | None = None) -> None:
        url = database_url or config.database_url
        # Ensure data directory exists (SQLite needs its parent dir)
        import re  # noqa: PLC0415
        path_match = re.search(r"sqlite:///(.+)", url)
        if path_match:
            from pathlib import Path  # noqa: PLC0415
            db_path = Path(path_match.group(1))
            db_path.parent.mkdir(parents=True, exist_ok=True)

        self._engine = create_engine(
            url,
            connect_args={"check_same_thread": False},  # SQLite multi-thread safe
            echo=False,
        )
        Base.metadata.create_all(self._engine)
        self._SessionMaker = sessionmaker(bind=self._engine, expire_on_commit=False)

        logger.info("SQLiteSessionRepository initialised | url=%s", url)

    def _session(self) -> Session:
        return self._SessionMaker()

    def save(self, record: SessionRecord) -> SessionRecord:
        """Persist a session record to SQLite."""
        orm_obj = record.to_orm()
        with self._session() as sess:
            sess.add(orm_obj)
            sess.commit()
            logger.debug("Session saved: id=%s severity=%s", record.id[:8], record.severity_level)
        return record

    def get_all(self, limit: int = 100, offset: int = 0) -> list[SessionRecord]:
        """Return sessions ordered by timestamp descending."""
        with self._session() as sess:
            rows = (
                sess.query(SessionRecordORM)
                .order_by(desc(SessionRecordORM.timestamp))
                .limit(limit)
                .offset(offset)
                .all()
            )
        return [SessionRecord.from_orm(row) for row in rows]

    def get_by_id(self, session_id: str) -> SessionRecord | None:
        """Retrieve a session by UUID."""
        with self._session() as sess:
            row = sess.get(SessionRecordORM, session_id)
        if row is None:
            return None
        return SessionRecord.from_orm(row)

    def delete(self, session_id: str) -> bool:
        """Delete a session. Returns True if found and deleted."""
        with self._session() as sess:
            row = sess.get(SessionRecordORM, session_id)
            if row is None:
                return False
            sess.delete(row)
            sess.commit()
            logger.debug("Session deleted: id=%s", session_id[:8])
        return True

    def count(self) -> int:
        """Total number of stored sessions."""
        with self._session() as sess:
            return sess.query(SessionRecordORM).count()
