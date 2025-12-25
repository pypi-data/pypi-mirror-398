from __future__ import annotations

def validate_grams(grams: float) -> None:
    if grams <= 0:
        raise ValueError("grams must be > 0")

def validate_barcode(barcode: str) -> None:
    b = barcode.strip()
    if not b:
        raise ValueError("barcode must be non-empty")
    if not b.isdigit():
        # OpenFoodFacts barcodes are numeric (EAN/UPC). Keep validation simple.
        raise ValueError("barcode must contain only digits")
