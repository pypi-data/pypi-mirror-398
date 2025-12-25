from prestashop_webservice.base_model import BaseModel
from prestashop_webservice.models import AddressData
from prestashop_webservice.params import Params


class Address(BaseModel):
    """Complex queries for addresses endpoint."""

    _data_class = AddressData

    def get_by_id(self, address_id: str) -> AddressData:
        """Get address by ID."""
        return self._query(f"addresses/{address_id}", None, "address")

    def get_by_customer(self, customer_id: str) -> list[AddressData]:
        """Get all addresses for a customer."""
        params = Params(
            filter={"id_customer": customer_id},
            display=["id", "id_customer", "address1", "city", "postcode"],
        )
        return self._query("addresses", params, "addresses")

    def get_by_postal_code(self, postal_code: str) -> list[AddressData]:
        """Get addresses by postal code."""
        params = Params(
            filter={"postcode": postal_code},
            display=["id", "address1", "city", "postcode"],
        )
        return self._query("addresses", params, "addresses")
