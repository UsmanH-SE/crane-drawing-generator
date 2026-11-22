import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Database file location
DB_PATH = Path(__file__).parent / "cranes.db"


def get_db_connection() -> sqlite3.Connection:
    """Create and return a database connection with dict-like row access."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create the designs table if it does not already exist."""
    with get_db_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS designs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                span_m REAL NOT NULL,
                capacity_t REAL NOT NULL,
                lift_height_m REAL NOT NULL,
                girder_height_mm INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )
        conn.commit()


def create_design(
    name: str,
    span_m: float,
    capacity_t: float,
    lift_height_m: float,
    girder_height_mm: int,
) -> Dict[str, Any]:
    """Insert a new design record and return it."""
    now = datetime.now(timezone.utc).isoformat()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO designs (
                name, span_m, capacity_t, lift_height_m, girder_height_mm, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (name, span_m, capacity_t, lift_height_m, girder_height_mm, now, now),
        )
        conn.commit()
        design_id = cursor.lastrowid

    return get_design_by_id(design_id)  # type: ignore[return-value]


def get_all_designs() -> List[Dict[str, Any]]:
    """Return all designs ordered newest first."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, name, span_m, capacity_t, lift_height_m, girder_height_mm, created_at, updated_at
            FROM designs
            ORDER BY datetime(created_at) DESC, id DESC;
            """
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_design_by_id(design_id: int) -> Optional[Dict[str, Any]]:
    """Return a single design by its ID or None if not found."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, name, span_m, capacity_t, lift_height_m, girder_height_mm, created_at, updated_at
            FROM designs
            WHERE id = ?;
            """,
            (design_id,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def update_design(
    design_id: int,
    name: str,
    span_m: float,
    capacity_t: float,
    lift_height_m: float,
    girder_height_mm: int,
) -> Optional[Dict[str, Any]]:
    """Update an existing design record and return the updated design, or None if not found."""
    existing = get_design_by_id(design_id)
    if not existing:
        return None

    now = datetime.now(timezone.utc).isoformat()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE designs
            SET name = ?,
                span_m = ?,
                capacity_t = ?,
                lift_height_m = ?,
                girder_height_mm = ?,
                updated_at = ?
            WHERE id = ?;
            """,
            (name, span_m, capacity_t, lift_height_m, girder_height_mm, now, design_id),
        )
        conn.commit()

    return get_design_by_id(design_id)
