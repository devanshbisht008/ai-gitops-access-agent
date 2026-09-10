"""Persistent SQLite repository for recording all access ticket requests and outcomes as unique table rows."""

import json
import os
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from src.core.models import ProvisioningReport

DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "config", "tickets.db")

class TicketStoreRepository:
    """Database repository for persisting and querying ticket request rows."""

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = os.path.abspath(db_path)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Initializes ticket_requests table schema if not present."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ticket_requests (
                    ticket_id TEXT PRIMARY KEY,
                    consumer TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    source_environment TEXT NOT NULL,
                    target_environment TEXT NOT NULL,
                    access_type TEXT NOT NULL,
                    access_scope TEXT NOT NULL,
                    requested_by TEXT NOT NULL,
                    business_justification TEXT,
                    tables TEXT,
                    is_ml_use_case INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL,
                    pr_url TEXT,
                    validation_errors TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.commit()

    def save_ticket(self, report: ProvisioningReport) -> Dict[str, Any]:
        """
        Saves or updates a ProvisioningReport as a unique row in ticket_requests table.
        Returns the saved database record as a dictionary.
        """
        norm = report.normalized_request
        val = report.validation_result
        exist = report.existing_access_result
        actions = report.action_taken or {}

        # Determine Ticket Status
        if not val.is_valid:
            status = "REJECTED"
        elif exist and exist.access_exists:
            status = "EXISTS_ACTIVE"
        elif "Pull request" in actions or "Feature branch created" in actions:
            status = "PROVISIONED"
        else:
            status = "PENDING"

        pr_url = actions.get("Pull request", "")
        validation_errors = json.dumps(val.errors) if val and val.errors else "[]"
        tables_json = json.dumps(norm.tables) if norm and norm.tables else "[]"
        now_iso = datetime.now(timezone.utc).isoformat()

        row_data = {
            "ticket_id": report.request_id,
            "consumer": norm.consumer,
            "provider": norm.provider,
            "source_environment": norm.source_environment,
            "target_environment": norm.target_environment,
            "access_type": norm.access_type,
            "access_scope": norm.access_scope,
            "requested_by": norm.requested_by,
            "business_justification": norm.business_justification,
            "tables": tables_json,
            "is_ml_use_case": 1 if norm.is_ml_use_case else 0,
            "status": status,
            "pr_url": pr_url,
            "validation_errors": validation_errors,
            "updated_at": now_iso,
        }

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO ticket_requests (
                    ticket_id, consumer, provider, source_environment, target_environment,
                    access_type, access_scope, requested_by, business_justification,
                    tables, is_ml_use_case, status, pr_url, validation_errors,
                    created_at, updated_at
                ) VALUES (
                    :ticket_id, :consumer, :provider, :source_environment, :target_environment,
                    :access_type, :access_scope, :requested_by, :business_justification,
                    :tables, :is_ml_use_case, :status, :pr_url, :validation_errors,
                    :created_at, :updated_at
                )
                ON CONFLICT(ticket_id) DO UPDATE SET
                    consumer=excluded.consumer,
                    provider=excluded.provider,
                    source_environment=excluded.source_environment,
                    target_environment=excluded.target_environment,
                    access_type=excluded.access_type,
                    access_scope=excluded.access_scope,
                    requested_by=excluded.requested_by,
                    business_justification=excluded.business_justification,
                    tables=excluded.tables,
                    is_ml_use_case=excluded.is_ml_use_case,
                    status=excluded.status,
                    pr_url=excluded.pr_url,
                    validation_errors=excluded.validation_errors,
                    updated_at=excluded.updated_at
            """, {**row_data, "created_at": now_iso})
            conn.commit()

        return row_data

    def get_all_tickets(self) -> List[Dict[str, Any]]:
        """Retrieves all ticket rows from the database ordered by creation date descending."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM ticket_requests ORDER BY rowid DESC")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_ticket(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single ticket row by ticket_id."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM ticket_requests WHERE ticket_id = ?", (ticket_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_latest_ticket_id(self) -> Optional[str]:
        """Returns the ticket_id of the most recently inserted row."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT ticket_id FROM ticket_requests ORDER BY rowid DESC LIMIT 1")
            row = cursor.fetchone()
            return row["ticket_id"] if row else None

    def clear_tickets(self) -> None:
        """Clears all records from ticket_requests table."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM ticket_requests")
            conn.commit()
