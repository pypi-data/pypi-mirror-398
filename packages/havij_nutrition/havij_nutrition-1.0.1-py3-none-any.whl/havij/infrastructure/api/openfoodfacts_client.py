from __future__ import annotations

import requests
from typing import Any, Dict

from havij.domain.model.nutrients import Nutrients
from havij.domain.model.product import Product

class OpenFoodFactsError(RuntimeError):
    pass

class OpenFoodFactsClient:
    """Very small client for Open Food Facts API v2."""

    BASE_URL = "https://world.openfoodfacts.net/api/v2"

    def __init__(self, timeout_s: float = 10.0):
        self._timeout_s = timeout_s
        self._session = requests.Session()
        self._session.headers.update({
            "Accept": "application/json",
        })

    def get_product_by_barcode(self, barcode: str) -> Product:
        url = f"{self.BASE_URL}/product/{barcode}"
        r = self._session.get(url, timeout=self._timeout_s)
        if r.status_code == 404:
            raise OpenFoodFactsError(f"Product not found for barcode={barcode}")
        if r.status_code >= 400:
            raise OpenFoodFactsError(f"API error {r.status_code}: {r.text[:200]}")

        data = r.json()
        product = data.get("product")
        if not isinstance(product, dict):
            raise OpenFoodFactsError("Unexpected API response: missing 'product'")

        name = (product.get("product_name") or product.get("product_name_en") or "").strip()
        if not name:
            name = f"Product {barcode}"

        nutr = product.get("nutriments") or {}
        nutrients_100g = _parse_nutrients_per_100g(nutr)

        return Product(barcode=barcode, name=name, nutrients_per_100g=nutrients_100g)

def _num(x: Any) -> float:
    try:
        if x is None:
            return 0.0
        return float(x)
    except Exception:
        return 0.0

def _parse_nutrients_per_100g(nutriments: Dict[str, Any]) -> Nutrients:
    # Common keys in OFF:
    # - energy-kcal_100g
    # - proteins_100g
    # - carbohydrates_100g
    # - fat_100g
    kcal = _num(nutriments.get("energy-kcal_100g") or nutriments.get("energy-kcal"))
    protein = _num(nutriments.get("proteins_100g"))
    carbs = _num(nutriments.get("carbohydrates_100g"))
    fat = _num(nutriments.get("fat_100g"))
    return Nutrients(kcal=kcal, protein_g=protein, carbs_g=carbs, fat_g=fat)
