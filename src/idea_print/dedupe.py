"""SQLite-based idempotency store for request deduplication."""

import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Generator


class DedupeStore:
    """SQLite store for tracking processed request IDs."""

    def __init__(self, db_path: str | Path, ttl_seconds: int = 86400):
        """
        Initialize the dedupe store.

        Args:
            db_path: Path to SQLite database file
            ttl_seconds: Time-to-live for entries (default 24 hours)
        """
        self.db_path = Path(db_path)
        self.ttl_seconds = ttl_seconds
        self._init_db()

    def _init_db(self) -> None:
        """Initialize the database schema."""
        with self._connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS processed_requests (
                    request_id TEXT PRIMARY KEY,
                    processed_at INTEGER NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_processed_at
                ON processed_requests(processed_at)
                """
            )

    @contextmanager
    def _connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Get a database connection."""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def is_duplicate(self, request_id: str) -> bool:
        """
        Check if a request ID has already been processed.

        Args:
            request_id: Unique request identifier

        Returns:
            True if the request has been processed before
        """
        with self._connection() as conn:
            cursor = conn.execute(
                "SELECT 1 FROM processed_requests WHERE request_id = ?",
                (request_id,),
            )
            return cursor.fetchone() is not None

    def mark_processed(self, request_id: str) -> None:
        """
        Mark a request ID as processed.

        Args:
            request_id: Unique request identifier
        """
        now = int(time.time())
        with self._connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO processed_requests (request_id, processed_at)
                VALUES (?, ?)
                """,
                (request_id, now),
            )

    def cleanup_expired(self) -> int:
        """
        Remove expired entries from the store.

        Returns:
            Number of entries removed
        """
        cutoff = int(time.time()) - self.ttl_seconds
        with self._connection() as conn:
            cursor = conn.execute(
                "DELETE FROM processed_requests WHERE processed_at < ?",
                (cutoff,),
            )
            return cursor.rowcount

    def check_and_mark(self, request_id: str) -> bool:
        """
        Atomically check if duplicate and mark as processed.

        Args:
            request_id: Unique request identifier

        Returns:
            True if this is a NEW request (not a duplicate)
        """
        now = int(time.time())
        with self._connection() as conn:
            # Try to insert; if it already exists, this will fail
            try:
                conn.execute(
                    """
                    INSERT INTO processed_requests (request_id, processed_at)
                    VALUES (?, ?)
                    """,
                    (request_id, now),
                )
                return True  # New request
            except sqlite3.IntegrityError:
                return False  # Duplicate
