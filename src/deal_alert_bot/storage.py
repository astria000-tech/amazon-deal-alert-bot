"""SQLite storage for alert history and duplicate prevention."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from .models import Deal, ScoreResult


class AlertStorage:
    """Persist alert history in SQLite."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS alerts (
                    deal_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    category TEXT NOT NULL,
                    source TEXT NOT NULL,
                    url TEXT NOT NULL,
                    score INTEGER NOT NULL,
                    reasons TEXT NOT NULL,
                    notified_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def has_alerted(self, deal_id: str) -> bool:
        """Return True if a deal_id has already been alerted."""

        with self._connect() as connection:
            cursor = connection.execute(
                "SELECT 1 FROM alerts WHERE deal_id = ? LIMIT 1", (deal_id,)
            )
            return cursor.fetchone() is not None

    def record_alert(self, deal: Deal, score_result: ScoreResult) -> None:
        """Record an alert after a notification or console fallback was emitted."""

        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO alerts (
                    deal_id, title, category, source, url, score, reasons
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    deal.deal_id,
                    deal.title,
                    deal.category,
                    deal.source,
                    deal.url,
                    score_result.score,
                    " | ".join(score_result.reasons),
                ),
            )
