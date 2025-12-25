from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple

from havij.application.ports import DayLogRepository, ProductCatalog
from havij.domain.model.meal import DayLog, MealEntry
from havij.domain.model.nutrients import Nutrients
from havij.domain.rules import validate_barcode, validate_grams

class MealService:
    def __init__(self, repo: DayLogRepository, catalog: ProductCatalog):
        self._repo = repo
        self._catalog = catalog

    def add_entry(self, day: date, barcode: str, grams: float, when: Optional[datetime] = None) -> MealEntry:
        validate_barcode(barcode)
        validate_grams(grams)
        when = when or datetime.now()

        product = self._catalog.get_by_barcode(barcode)
        nutrients = product.nutrients_for_grams(grams)

        entry = MealEntry(
            entry_id=str(uuid.uuid4()),
            timestamp=when,
            barcode=barcode,
            product_name=product.name,
            grams=grams,
            nutrients=nutrients,
        )

        log = self._repo.load_day(day)
        log.add_entry(entry)
        self._repo.save_day(log)
        return entry

    def remove_entry(self, day: date, entry_id: str) -> bool:
        log = self._repo.load_day(day)
        removed = log.remove_entry(entry_id)
        if removed:
            self._repo.save_day(log)
        return removed

    def get_day_log(self, day: date) -> DayLog:
        return self._repo.load_day(day)

    def get_day_totals(self, day: date) -> Nutrients:
        return self.get_day_log(day).total_nutrients()

    def get_last_days_totals(self, end_day: date, days: int = 7) -> List[Tuple[date, Nutrients]]:
        if days <= 0:
            raise ValueError("days must be > 0")
        result: List[Tuple[date, Nutrients]] = []
        for i in range(days-1, -1, -1):
            d = end_day - timedelta(days=i)
            result.append((d, self.get_day_totals(d)))
        return result
