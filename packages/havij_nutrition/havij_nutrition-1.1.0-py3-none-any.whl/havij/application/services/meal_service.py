from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta
from typing import List, Optional, Tuple

from havij.application.ports import DayLogRepository, ProductCatalog
from havij.domain.model.meal import DayLog, MealEntry
from havij.domain.model.nutrients import Nutrients
from havij.domain.rules import validate_grams

class MealService:
    def __init__(self, repo: DayLogRepository, catalog: ProductCatalog | None = None):
        self._repo = repo

    def add_entry(
        self,
        user_id: str,
        day: date,
        product_name: str,
        grams: float,
        nutrients_per_100g: Nutrients,
        when: Optional[datetime] = None,
        barcode: str = "",
    ) -> MealEntry:
        validate_grams(grams)
        when = when or datetime.now()

        nutrients = nutrients_per_100g.scale(grams / 100.0)

        entry = MealEntry(
            entry_id=str(uuid.uuid4()),
            timestamp=when,
            barcode=barcode,
            product_name=product_name,
            grams=grams,
            nutrients=nutrients,
        )

        log = self._repo.load_day(day, user_id)
        log.add_entry(entry)
        self._repo.save_day(log, user_id)
        return entry

    def remove_entry(self, user_id: str, day: date, entry_id: str) -> bool:
        log = self._repo.load_day(day, user_id)
        removed = log.remove_entry(entry_id)
        if removed:
            self._repo.save_day(log, user_id)
        return removed

    def get_day_log(self, user_id: str, day: date) -> DayLog:
        return self._repo.load_day(day, user_id)

    def get_day_totals(self, user_id: str, day: date) -> Nutrients:
        return self.get_day_log(user_id, day).total_nutrients()

    def get_last_days_totals(self, user_id: str, end_day: date, days: int = 7) -> List[Tuple[date, Nutrients]]:
        if days <= 0:
            raise ValueError("days must be > 0")
        result: List[Tuple[date, Nutrients]] = []
        for i in range(days-1, -1, -1):
            d = end_day - timedelta(days=i)
            result.append((d, self.get_day_totals(user_id, d)))
        return result

    def assign_unowned_entries(self, user_id: str) -> int:
        return self._repo.assign_unowned_entries(user_id)
