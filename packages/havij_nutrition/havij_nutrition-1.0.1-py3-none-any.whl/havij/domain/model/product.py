from __future__ import annotations

from dataclasses import dataclass
from .nutrients import Nutrients

@dataclass(frozen=True, slots=True)
class Product:
    barcode: str
    name: str
    nutrients_per_100g: Nutrients

    def nutrients_for_grams(self, grams: float) -> Nutrients:
        if grams <= 0:
            raise ValueError("Quantity in grams must be > 0")
        factor = grams / 100.0
        return self.nutrients_per_100g.scale(factor)
