from prestashop_webservice.base_model import BaseModel
from prestashop_webservice.models import OrderData
from prestashop_webservice.params import Params


class Order(BaseModel):
    """Complex queries for orders endpoint."""

    _data_class = OrderData

    def get_by_id(self, order_id: str) -> OrderData:
        """Get order by ID."""
        return self._query(f"orders/{order_id}", None, "order")

    def exists(self, order_id: str) -> bool:
        """Check if order exists by ID."""
        try:
            self.get_by_id(order_id)
            return True
        except Exception:
            return False

    def get_by_reference(self, reference: str) -> OrderData | None:
        """Get order by reference."""
        params = Params(
            filter={"reference": reference},
            display=["id", "reference", "total_paid", "current_state"],
        )
        orders: list[OrderData] = self._query("orders", params, "orders")
        return orders[0] if orders else None

    def get_by_customer(self, customer_id: str, limit: int = 999) -> list[OrderData]:
        """Get all orders for a customer."""
        params = Params(
            filter={"id_customer": customer_id},
            display=["id", "id_customer", "date_add", "total_paid", "reference"],
            limit=limit,
        )
        return self._query("orders", params, "orders")

    def get_latest_by_customer(self, customer_id: str) -> OrderData | None:
        """Get the most recent order for a customer."""
        params = Params(
            filter={"id_customer": customer_id},
            display=["id", "id_customer", "date_add", "total_paid", "reference"],
            limit=1,
        )
        orders: list[OrderData] = self._query("orders", params, "orders")
        return orders[0] if orders else None

    def get_recent(self, limit: int = 10) -> list[OrderData]:
        """Get recent orders."""
        params = Params(
            display=["id", "reference", "total_paid", "date_add", "id_customer"],
            limit=limit,
        )
        return self._query("orders", params, "orders")  # type: ignore

    def get_by_status(self, status_id: str, limit: int = 100) -> list[OrderData]:
        """Get orders by status."""
        params = Params(
            filter={"current_state": status_id},
            display=["id", "current_state", "reference", "date_add"],
            limit=limit,
        )
        return self._query("orders", params, "orders")

    def get_shipped_orders(
        self, start_date: str = "2025-11-10", end_date: str = "3500-12-11"
    ) -> list[OrderData]:
        """Get orders with shipped status."""
        params = Params(
            filter={"current_state": "4", "date_add": f"[{start_date},{end_date}]"},
            display=["id", "shipping_number"],
            date=True,
        )
        return self._query("orders", params, "orders")

    def get_total_wrapping(self, order_id: str) -> str | None:
        """Get total wrapping (donation) for an order."""
        order = self.get_by_id(order_id)
        return order.total_wrapping

    def get_total_shipping(self, order_id: str) -> str | None:
        """Get total shipping cost for an order."""
        order = self.get_by_id(order_id)
        return order.total_shipping

    def get_total_discounts(self, order_id: str) -> str | None:
        """Get total discounts for an order."""
        order = self.get_by_id(order_id)
        return order.total_discounts

    def get_all_orders_since(
        self, start_date: str = "2025-11-10", end_date: str = "3500-12-11"
    ) -> list[OrderData]:
        """Get all orders since a specific date."""
        params = Params(
            filter={"date_add": f"[{start_date},{end_date}]"},
            display=["id", "reference", "date_add", "current_state", "total_paid"],
            date=True,
        )
        return self._query("orders", params, "orders")

    def get_orders_available_at_pickup_point(
        self, start_date: str = "2025-11-10", end_date: str = "3500-12-11"
    ) -> list[OrderData]:
        """Get orders with shipped status."""
        params = Params(
            filter={"current_state": "41", "date_add": f"[{start_date},{end_date}]"},
            display=["id", "shipping_number"],
            date=True,
        )
        return self._query("orders", params, "orders")
