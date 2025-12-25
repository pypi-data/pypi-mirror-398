from __future__ import annotations

import sqlite3
from datetime import date, datetime
from typing import List

from havij.domain.model.meal import DayLog, MealEntry
from havij.domain.model.nutrients import Nutrients

class SqliteDayLogRepository:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def load_day(self, day: date) -> DayLog:
        day_str = day.isoformat()
        rows = self._conn.execute(
            "SELECT * FROM meal_entries WHERE day = ? ORDER BY ts ASC",
            (day_str,),
        ).fetchall()

        entries: List[MealEntry] = []
        for r in rows:
            entries.append(
                MealEntry(
                    entry_id=r["entry_id"],
                    timestamp=datetime.fromisoformat(r["ts"]),
                    barcode=r["barcode"],
                    product_name=r["product_name"],
                    grams=float(r["grams"]),
                    nutrients=Nutrients(
                        kcal=float(r["kcal"]),
                        protein_g=float(r["protein_g"]),
                        carbs_g=float(r["carbs_g"]),
                        fat_g=float(r["fat_g"]),
                    ),
                )
            )
        return DayLog(day=day, entries=entries)

    def save_day(self, log: DayLog) -> None:
        # Simple approach: delete day and re-insert (ok for small local app)
        day_str = log.day.isoformat()
        self._conn.execute("DELETE FROM meal_entries WHERE day = ?", (day_str,))
        for e in log.entries:
            self._conn.execute(
                """
                INSERT INTO meal_entries(entry_id, day, ts, barcode, product_name, grams, kcal, protein_g, carbs_g, fat_g)
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    e.entry_id,
                    day_str,
                    e.timestamp.isoformat(),
                    e.barcode,
                    e.product_name,
                    float(e.grams),
                    float(e.nutrients.kcal),
                    float(e.nutrients.protein_g),
                    float(e.nutrients.carbs_g),
                    float(e.nutrients.fat_g),
                ),
            )
        self._conn.commit()
