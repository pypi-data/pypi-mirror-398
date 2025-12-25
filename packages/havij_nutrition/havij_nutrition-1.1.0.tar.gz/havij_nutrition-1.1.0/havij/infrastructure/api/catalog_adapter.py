from __future__ import annotations

from havij.application.ports import ProductCatalog
from havij.domain.model.product import Product
from havij.infrastructure.api.openfoodfacts_client import OpenFoodFactsClient

class OpenFoodFactsCatalog(ProductCatalog):
    def __init__(self, client: OpenFoodFactsClient):
        self._client = client

    def get_by_barcode(self, barcode: str) -> Product:
        return self._client.get_product_by_barcode(barcode)
