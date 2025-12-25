from prestashop_webservice.base_model import BaseModel
from prestashop_webservice.models import CustomerData
from prestashop_webservice.params import Params


class Customer(BaseModel):
    """Complex queries for customers endpoint."""

    _data_class = CustomerData

    def get_by_id(self, customer_id: str) -> CustomerData:
        """Get customer by ID."""
        return self._query(f"customers/{customer_id}", None, "customer")

    def get_by_email(self, email: str) -> CustomerData | None:
        """Get customer by email."""
        email = email.strip().lower()
        params = Params(
            filter={"email": email},
            display=["id", "email", "firstname", "lastname"],
        )
        customers = self._query("customers", params, "customers")
        return customers[0] if customers else None

    def get_active(self, limit: int = 100) -> list[CustomerData]:
        """Get active customers."""
        params = Params(
            filter={"active": "1"},
            display=["id", "firstname", "lastname", "email", "active"],
            limit=limit,
        )
        return self._query("customers", params, "customers")

    def search_by_name(self, name: str, limit: int = 50) -> list[CustomerData]:
        """Search customers by firstname or lastname."""
        params = Params(
            filter={"firstname": f"%{name}%"},
            display=["id", "firstname", "lastname", "email"],
            limit=limit,
        )
        result = self._query("customers", params, "customers")
        return result if result is not None else []
