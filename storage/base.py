"""
NeuroSpeak-AI — Abstract Session Repository
=============================================
All storage backends implement this interface.
Swap SQLite → PostgreSQL by changing ``DATABASE_URL`` in ``.env``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from storage.models import SessionRecord


class SessionRepository(ABC):
    """Abstract CRUD interface for session persistence."""

    @abstractmethod
    def save(self, record: SessionRecord) -> SessionRecord:
        """Persist a new session record. Returns the saved record (with id)."""

    @abstractmethod
    def get_all(self, limit: int = 100, offset: int = 0) -> list[SessionRecord]:
        """Return all sessions, most recent first."""

    @abstractmethod
    def get_by_id(self, session_id: str) -> SessionRecord | None:
        """Return a single session by its UUID, or None if not found."""

    @abstractmethod
    def delete(self, session_id: str) -> bool:
        """Delete a session by UUID. Returns True if deleted, False if not found."""

    @abstractmethod
    def count(self) -> int:
        """Return the total number of stored sessions."""

    def dispose(self) -> None:
        """Release any underlying database connections / file handles.

        Override in backends that hold persistent connections (e.g. SQLite,
        PostgreSQL) so callers (tests, CLI tools) can cleanly free resources.
        The default implementation is a no-op.
        """
