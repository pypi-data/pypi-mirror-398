from typing import cast

from prestashop_webservice.base_model import BaseModel
from prestashop_webservice.models import ProductData
from prestashop_webservice.params import Params


class Product(BaseModel):
    """Complex queries for products endpoint."""

    _data_class = ProductData

    def get_by_id(self, product_id: str) -> ProductData:
        """Get product by ID."""
        return cast(ProductData, self._query(f"products/{product_id}", None, "product"))

    def get_by_category(self, category_id: str, limit: int = 50) -> list[ProductData]:
        """Get products by category."""
        params = Params(
            filter={"id_category_default": category_id},
            display=["id", "name", "reference", "price", "id_category_default"],
            limit=limit,
        )
        return cast(list[ProductData], self._query("products", params, "products"))

    def get_by_reference(self, reference: str) -> ProductData | None:
        """Get product by reference."""
        params = Params(
            filter={"reference": reference},
            display=["id", "reference", "name", "price"],
        )
        products = cast(list[ProductData], self._query("products", params, "products"))
        return products[0] if products else None

    def get_active(self, limit: int = 100) -> list[ProductData]:
        """Get active products."""
        params = Params(
            filter={"active": "1"},
            display=["id", "name", "reference", "active"],
            limit=limit,
        )
        return cast(list[ProductData], self._query("products", params, "products"))

    def get_image_url(self, product_id: str) -> str:
        """Get the default image URL for a product."""
        product = self.get_by_id(product_id)
        img_id = str(product.id_default_image or "").strip()
        slug = str(product.link_rewrite or "").strip()

        if not (img_id and slug):
            return ""

        base_url = self.client.base_url
        return f"{base_url}/{img_id}-large_default/{slug}.jpg"
