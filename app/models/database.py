"""
SQLite database storage with Write-Ahead Logging (WAL) and CRDT-lite Last-Writer-Wins
for the Disaster Relief Coordination platform.
"""

import sqlite3
import json
import time
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path
from app.config import DB_PATH, config
from app.models.schemas import Volunteer, Need, AssignmentProposal, Slot

class Database:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        # Enable Write-Ahead Logging for concurrency and durability
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS volunteers (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                skills TEXT NOT NULL,
                languages TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                start_time REAL NOT NULL,
                end_time REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'available',
                assigned_slot_id TEXT,
                assigned_need_id TEXT,
                hlc_timestamp INTEGER NOT NULL,
                node_id TEXT NOT NULL,
                updated_at REAL NOT NULL
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS needs (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                required_language TEXT NOT NULL,
                start_time REAL NOT NULL,
                end_time REAL NOT NULL,
                required_head_count INTEGER NOT NULL,
                urgency INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'open',
                filled_slots INTEGER NOT NULL DEFAULT 0,
                hlc_timestamp INTEGER NOT NULL,
                node_id TEXT NOT NULL,
                updated_at REAL NOT NULL
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS assignments (
                assignment_id TEXT PRIMARY KEY,
                volunteer_id TEXT NOT NULL,
                volunteer_name TEXT NOT NULL,
                need_id TEXT NOT NULL,
                slot_id TEXT NOT NULL,
                category TEXT NOT NULL,
                score REAL NOT NULL,
                feasibility INTEGER NOT NULL DEFAULT 1,
                breakdown TEXT,
                status TEXT NOT NULL DEFAULT 'proposed',
                hlc_timestamp INTEGER NOT NULL,
                node_id TEXT NOT NULL,
                created_at REAL NOT NULL
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS crdt_counters (
                counter_key TEXT NOT NULL,
                node_id TEXT NOT NULL,
                value INTEGER NOT NULL DEFAULT 0,
                hlc_timestamp INTEGER NOT NULL,
                PRIMARY KEY (counter_key, node_id)
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS sync_log (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_type TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                action TEXT NOT NULL,
                hlc_timestamp INTEGER NOT NULL,
                payload TEXT NOT NULL,
                node_id TEXT NOT NULL
            );
            """)
            conn.commit()

    # --- Volunteer Operations ---

    def upsert_volunteer(self, vol: Volunteer) -> bool:
        """Upsert volunteer with Last-Writer-Wins based on hlc_timestamp."""
        now = time.time()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT hlc_timestamp FROM volunteers WHERE id = ?", (vol.id,))
            row = cursor.fetchone()
            if row and row["hlc_timestamp"] >= vol.hlc_timestamp:
                return False  # Older or equal update ignored under LWW

            cursor.execute("""
            INSERT INTO volunteers (
                id, name, skills, languages, latitude, longitude,
                start_time, end_time, status, assigned_slot_id, assigned_need_id,
                hlc_timestamp, node_id, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                skills = excluded.skills,
                languages = excluded.languages,
                latitude = excluded.latitude,
                longitude = excluded.longitude,
                start_time = excluded.start_time,
                end_time = excluded.end_time,
                status = excluded.status,
                assigned_slot_id = excluded.assigned_slot_id,
                assigned_need_id = excluded.assigned_need_id,
                hlc_timestamp = excluded.hlc_timestamp,
                node_id = excluded.node_id,
                updated_at = excluded.updated_at;
            """, (
                vol.id, vol.name, json.dumps(vol.skills), json.dumps(vol.languages),
                vol.latitude, vol.longitude, vol.start_time, vol.end_time,
                vol.status, vol.assigned_slot_id, vol.assigned_need_id,
                vol.hlc_timestamp, vol.node_id, now
            ))

            cursor.execute("""
            INSERT INTO sync_log (entity_type, entity_id, action, hlc_timestamp, payload, node_id)
            VALUES (?, ?, ?, ?, ?, ?);
            """, ("volunteer", vol.id, "upsert", vol.hlc_timestamp, vol.model_dump_json(), vol.node_id))
            conn.commit()
            return True

    def get_volunteer(self, vol_id: str) -> Optional[Volunteer]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM volunteers WHERE id = ?", (vol_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_volunteer(row)

    def list_volunteers(self, status: Optional[str] = None) -> List[Volunteer]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if status:
                cursor.execute("SELECT * FROM volunteers WHERE status = ?", (status,))
            else:
                cursor.execute("SELECT * FROM volunteers ORDER BY id ASC")
            rows = cursor.fetchall()
            return [self._row_to_volunteer(r) for r in rows]

    def _row_to_volunteer(self, row: sqlite3.Row) -> Volunteer:
        return Volunteer(
            id=row["id"],
            name=row["name"],
            skills=json.loads(row["skills"]),
            languages=json.loads(row["languages"]),
            latitude=row["latitude"],
            longitude=row["longitude"],
            start_time=row["start_time"],
            end_time=row["end_time"],
            status=row["status"],
            assigned_slot_id=row["assigned_slot_id"],
            assigned_need_id=row["assigned_need_id"],
            hlc_timestamp=row["hlc_timestamp"],
            node_id=row["node_id"]
        )

    # --- Need Operations ---

    def upsert_need(self, need: Need) -> bool:
        """Upsert need with Last-Writer-Wins based on hlc_timestamp."""
        now = time.time()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT hlc_timestamp FROM needs WHERE id = ?", (need.id,))
            row = cursor.fetchone()
            if row and row["hlc_timestamp"] >= need.hlc_timestamp:
                return False

            cursor.execute("""
            INSERT INTO needs (
                id, title, category, latitude, longitude, required_language,
                start_time, end_time, required_head_count, urgency,
                status, filled_slots, hlc_timestamp, node_id, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                title = excluded.title,
                category = excluded.category,
                latitude = excluded.latitude,
                longitude = excluded.longitude,
                required_language = excluded.required_language,
                start_time = excluded.start_time,
                end_time = excluded.end_time,
                required_head_count = excluded.required_head_count,
                urgency = excluded.urgency,
                status = excluded.status,
                filled_slots = excluded.filled_slots,
                hlc_timestamp = excluded.hlc_timestamp,
                node_id = excluded.node_id,
                updated_at = excluded.updated_at;
            """, (
                need.id, need.title, need.category, need.latitude, need.longitude,
                need.required_language, need.start_time, need.end_time,
                need.required_head_count, need.urgency, need.status,
                need.filled_slots, need.hlc_timestamp, need.node_id, now
            ))

            cursor.execute("""
            INSERT INTO sync_log (entity_type, entity_id, action, hlc_timestamp, payload, node_id)
            VALUES (?, ?, ?, ?, ?, ?);
            """, ("need", need.id, "upsert", need.hlc_timestamp, need.model_dump_json(), need.node_id))
            conn.commit()
            return True

    def get_need(self, need_id: str) -> Optional[Need]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM needs WHERE id = ?", (need_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_need(row)

    def list_needs(self, status: Optional[str] = None) -> List[Need]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if status:
                cursor.execute("SELECT * FROM needs WHERE status = ? ORDER BY urgency DESC", (status,))
            else:
                cursor.execute("SELECT * FROM needs ORDER BY urgency DESC, id ASC")
            rows = cursor.fetchall()
            return [self._row_to_need(r) for r in rows]

    def _row_to_need(self, row: sqlite3.Row) -> Need:
        return Need(
            id=row["id"],
            title=row["title"],
            category=row["category"],
            latitude=row["latitude"],
            longitude=row["longitude"],
            required_language=row["required_language"],
            start_time=row["start_time"],
            end_time=row["end_time"],
            required_head_count=row["required_head_count"],
            urgency=row["urgency"],
            status=row["status"],
            filled_slots=row["filled_slots"],
            hlc_timestamp=row["hlc_timestamp"],
            node_id=row["node_id"]
        )

    # --- Assignment Operations ---

    def save_assignment(self, assignment: AssignmentProposal, node_id: str = "camp-node-01", hlc: int = 0):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO assignments (
                assignment_id, volunteer_id, volunteer_name, need_id, slot_id,
                category, score, feasibility, breakdown, status, hlc_timestamp, node_id, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(assignment_id) DO UPDATE SET
                status = excluded.status,
                score = excluded.score,
                hlc_timestamp = excluded.hlc_timestamp;
            """, (
                assignment.assignment_id, assignment.volunteer_id, assignment.volunteer_name,
                assignment.need_id, assignment.slot_id, assignment.category,
                assignment.score, 1 if assignment.feasibility else 0,
                assignment.breakdown.model_dump_json() if assignment.breakdown else None,
                assignment.status, hlc, node_id, time.time()
            ))

            cursor.execute("""
            INSERT INTO sync_log (entity_type, entity_id, action, hlc_timestamp, payload, node_id)
            VALUES (?, ?, ?, ?, ?, ?);
            """, ("assignment", assignment.assignment_id, "save", hlc, assignment.model_dump_json(), node_id))
            conn.commit()

    def list_assignments(self, status: Optional[str] = None) -> List[AssignmentProposal]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if status:
                cursor.execute("SELECT * FROM assignments WHERE status = ?", (status,))
            else:
                cursor.execute("SELECT * FROM assignments")
            rows = cursor.fetchall()
            assignments = []
            for r in rows:
                breakdown = None
                if r["breakdown"]:
                    try:
                        breakdown = json.loads(r["breakdown"])
                    except Exception:
                        pass
                assignments.append(AssignmentProposal(
                    assignment_id=r["assignment_id"],
                    volunteer_id=r["volunteer_id"],
                    volunteer_name=r["volunteer_name"],
                    need_id=r["need_id"],
                    slot_id=r["slot_id"],
                    category=r["category"],
                    score=r["score"],
                    feasibility=bool(r["feasibility"]),
                    breakdown=breakdown,
                    status=r["status"]
                ))
            return assignments

    def confirm_assignment(self, assignment_id: str, hlc: int = 0) -> bool:
        """Lock and confirm assignment, update volunteer to 'assigned', update need filled_slots."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM assignments WHERE assignment_id = ?", (assignment_id,))
            assign_row = cursor.fetchone()
            if not assign_row:
                return False

            vol_id = assign_row["volunteer_id"]
            need_id = assign_row["need_id"]
            slot_id = assign_row["slot_id"]

            cursor.execute("UPDATE assignments SET status = 'confirmed', hlc_timestamp = ? WHERE assignment_id = ?", (hlc, assignment_id))
            cursor.execute("UPDATE volunteers SET status = 'assigned', assigned_slot_id = ?, assigned_need_id = ?, hlc_timestamp = ? WHERE id = ?", (slot_id, need_id, hlc, vol_id))

            # Update need filled slots count
            cursor.execute("SELECT required_head_count, filled_slots FROM needs WHERE id = ?", (need_id,))
            need_row = cursor.fetchone()
            if need_row:
                new_filled = need_row["filled_slots"] + 1
                new_status = "filled" if new_filled >= need_row["required_head_count"] else "partially_filled"
                cursor.execute("UPDATE needs SET filled_slots = ?, status = ?, hlc_timestamp = ? WHERE id = ?", (new_filled, new_status, hlc, need_id))

            # Increment grow-only counter for filled slots
            cursor.execute("""
            INSERT INTO crdt_counters (counter_key, node_id, value, hlc_timestamp)
            VALUES (?, ?, 1, ?)
            ON CONFLICT(counter_key, node_id) DO UPDATE SET
                value = crdt_counters.value + 1,
                hlc_timestamp = excluded.hlc_timestamp;
            """, (f"filled_slots_{need_id}", config.node_id, hlc))

            cursor.execute("""
            INSERT INTO sync_log (entity_type, entity_id, action, hlc_timestamp, payload, node_id)
            VALUES (?, ?, ?, ?, ?, ?);
            """, ("assignment", assignment_id, "confirm", hlc, json.dumps({"status": "confirmed", "volunteer_id": vol_id, "need_id": need_id}), config.node_id))
            conn.commit()
            return True

    def clear_all(self):
        """Reset database tables (used for testing and simulations)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM volunteers;")
            cursor.execute("DELETE FROM needs;")
            cursor.execute("DELETE FROM assignments;")
            cursor.execute("DELETE FROM crdt_counters;")
            cursor.execute("DELETE FROM sync_log;")
            conn.commit()

    def get_sync_deltas(self, from_hlc: int) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sync_log WHERE hlc_timestamp > ? ORDER BY hlc_timestamp ASC", (from_hlc,))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

db = Database()
