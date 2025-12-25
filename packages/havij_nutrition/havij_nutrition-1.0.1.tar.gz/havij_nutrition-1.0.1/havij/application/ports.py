from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import List, Optional, Protocol

from havij.domain.model.product import Product
from havij.domain.model.meal import DayLog

class ProductCatalog(Protocol):
    def get_by_barcode(self, barcode: str) -> Product: ...

class DayLogRepository(Protocol):
    def load_day(self, day: date) -> DayLog: ...
    def save_day(self, log: DayLog) -> None: ...
