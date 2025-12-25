from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterator, Optional

def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn

def init_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS meal_entries (
            entry_id TEXT PRIMARY KEY,
            day TEXT NOT NULL,
            ts TEXT NOT NULL,
            barcode TEXT NOT NULL,
            product_name TEXT NOT NULL,
            grams REAL NOT NULL,
            kcal REAL NOT NULL,
            protein_g REAL NOT NULL,
            carbs_g REAL NOT NULL,
            fat_g REAL NOT NULL
        );
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_meal_entries_day ON meal_entries(day);")
    conn.commit()
