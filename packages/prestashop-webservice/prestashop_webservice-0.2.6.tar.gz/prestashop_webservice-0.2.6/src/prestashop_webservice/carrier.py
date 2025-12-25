from typing import cast

from prestashop_webservice.base_model import BaseModel
from prestashop_webservice.models import CarrierData
from prestashop_webservice.params import Params


class Carrier(BaseModel):
    """Complex queries for carriers endpoint."""

    _data_class = CarrierData

    def get_by_id(self, carrier_id: str) -> CarrierData:
        """Get carrier by ID."""
        return cast(CarrierData, self._query(f"carriers/{carrier_id}", None, "carrier"))

    def get_all(self, limit: int | None = None) -> list[CarrierData]:
        """Get carriers with optional limit."""
        params = Params(limit=limit)
        return cast(list[CarrierData], self._query("carriers", params, "carriers"))

    def get_active(self, limit: int | None = None) -> list[CarrierData]:
        """Get active carriers only."""
        params = Params(filter={"active": "1"}, limit=limit)
        return cast(list[CarrierData], self._query("carriers", params, "carriers"))

    def get_by_reference(self, reference_id: str) -> CarrierData | None:
        """Get carrier by reference identifier."""
        params = Params(filter={"id_reference": reference_id}, limit=1)
        carriers = cast(list[CarrierData], self._query("carriers", params, "carriers"))
        return carriers[0] if carriers else None
