from __future__ import annotations

from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class Nutrients:
    """Macronutrients and calories.

    All values are expressed per serving (not per 100g).
    """
    kcal: float
    protein_g: float
    carbs_g: float
    fat_g: float

    def __add__(self, other: "Nutrients") -> "Nutrients":
        return Nutrients(
            kcal=self.kcal + other.kcal,
            protein_g=self.protein_g + other.protein_g,
            carbs_g=self.carbs_g + other.carbs_g,
            fat_g=self.fat_g + other.fat_g,
        )

    def scale(self, factor: float) -> "Nutrients":
        return Nutrients(
            kcal=self.kcal * factor,
            protein_g=self.protein_g * factor,
            carbs_g=self.carbs_g * factor,
            fat_g=self.fat_g * factor,
        )

    @staticmethod
    def zero() -> "Nutrients":
        return Nutrients(0.0, 0.0, 0.0, 0.0)
