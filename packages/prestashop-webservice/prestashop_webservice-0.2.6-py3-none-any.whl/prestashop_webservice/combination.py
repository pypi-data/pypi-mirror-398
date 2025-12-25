from typing import cast

from cachetools import TTLCache, cached

from prestashop_webservice.base_model import BaseModel
from prestashop_webservice.models import CombinationData
from prestashop_webservice.params import Params


class Combination(BaseModel):
    """Complex queries for combinations endpoint."""

    _data_class = CombinationData

    @cached(cache=TTLCache(maxsize=1000, ttl=604800))
    def get_by_id(self, combination_id: str) -> CombinationData:
        """Get combination by ID."""
        return cast(
            CombinationData, self._query(f"combinations/{combination_id}", None, "combination")
        )

    @cached(cache=TTLCache(maxsize=1000, ttl=604800))
    def get_by_product(self, product_id: str) -> list[CombinationData]:
        """Get combinations for a product."""
        params = Params(
            filter={"id_product": product_id},
            display=["id", "id_product", "reference", "ean13", "price", "weight", "default_on"],
        )
        return cast(list[CombinationData], self._query("combinations", params, "combinations"))
