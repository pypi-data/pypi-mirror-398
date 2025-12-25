from __future__ import annotations

from havij.application.ports import ProductCatalog
from havij.domain.model.product import Product
from havij.domain.rules import validate_barcode

class ProductService:
    def __init__(self, catalog: ProductCatalog):
        self._catalog = catalog

    def lookup_product(self, barcode: str) -> Product:
        validate_barcode(barcode)
        return self._catalog.get_by_barcode(barcode)
