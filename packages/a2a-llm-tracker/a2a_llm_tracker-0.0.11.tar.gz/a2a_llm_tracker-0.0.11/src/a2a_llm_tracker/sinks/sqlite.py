from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .base import Sink
from ..events import UsageEvent


class SQLiteSink(Sink):
    def __init__(self, path: str = "usage.db") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(str(self.path))

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS usage_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts TEXT,
                    provider TEXT,
                    model TEXT,
                    token_breakdown_json TEXT,
                    input_cost_usd REAL,
                    output_cost_usd REAL,
                    cost_usd REAL,
                    accuracy TEXT,
                    request_id TEXT,
                    latency_ms INTEGER,
                    status TEXT,
                    error_type TEXT,
                    error_message TEXT,
                    agent_id TEXT,
                    user_id TEXT,
                    session_id TEXT,
                    trace_id TEXT,
                    metadata_json TEXT
                )
                """
            )
            conn.commit()

    def write(self, event: UsageEvent) -> None:
        # Serialize token breakdown to JSON
        token_breakdown_json = "[]"
        try:
            breakdown_list = [b.to_dict() for b in event.token_breakdown]
            token_breakdown_json = json.dumps(breakdown_list, ensure_ascii=False)
        except Exception:
            token_breakdown_json = "[]"

        # Serialize metadata to JSON
        metadata_json = "{}"
        try:
            metadata_json = json.dumps(event.metadata, ensure_ascii=False)
        except Exception:
            metadata_json = "{}"

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO usage_events (
                    ts, provider, model,
                    token_breakdown_json,
                    input_cost_usd, output_cost_usd, cost_usd,
                    accuracy, request_id, latency_ms,
                    status, error_type, error_message,
                    agent_id, user_id, session_id, trace_id,
                    metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.ts.isoformat(),
                    event.provider,
                    event.model,
                    token_breakdown_json,
                    event.input_cost_usd,
                    event.output_cost_usd,
                    event.cost_usd,
                    event.accuracy,
                    event.request_id,
                    event.latency_ms,
                    event.status,
                    event.error_type,
                    event.error_message,
                    event.agent_id,
                    event.user_id,
                    event.session_id,
                    event.trace_id,
                    metadata_json,
                ),
            )
            conn.commit()
