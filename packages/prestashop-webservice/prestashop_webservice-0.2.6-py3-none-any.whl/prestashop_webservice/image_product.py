from prestashop_webservice.base_model import BaseModel
from prestashop_webservice.models import ImageProductData


class ImageProduct(BaseModel):
    """Complex queries for images/products endpoint."""

    _data_class = ImageProductData

    def get_by_product(self, product_id: str) -> list[ImageProductData]:
        """Get images for a product."""
        return self._query(f"images/products/{product_id}", None, "image")
