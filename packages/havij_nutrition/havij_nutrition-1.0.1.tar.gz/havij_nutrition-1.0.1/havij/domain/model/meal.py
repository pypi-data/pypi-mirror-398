from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Iterable, List, Optional

from .nutrients import Nutrients
from .product import Product

@dataclass(frozen=True, slots=True)
class MealEntry:
    entry_id: str
    timestamp: datetime
    barcode: str
    product_name: str
    grams: float
    nutrients: Nutrients

@dataclass
class DayLog:
    day: date
    entries: List[MealEntry]

    def add_entry(self, entry: MealEntry) -> None:
        if entry.grams <= 0:
            raise ValueError("Entry grams must be > 0")
        self.entries.append(entry)

    def remove_entry(self, entry_id: str) -> bool:
        before = len(self.entries)
        self.entries = [e for e in self.entries if e.entry_id != entry_id]
        return len(self.entries) != before

    def total_nutrients(self) -> Nutrients:
        total = Nutrients.zero()
        for e in self.entries:
            total = total + e.nutrients
        return total
