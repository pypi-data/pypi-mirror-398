from prestashop_webservice.base_model import BaseModel
from prestashop_webservice.models import OrderStateData


class OrderState(BaseModel):
    """Complex queries for order_states endpoint."""

    _data_class = OrderStateData

    def get_by_id(self, state_id: str) -> OrderStateData:
        """Get order state by ID."""
        return self._query(f"order_states/{state_id}", None, "order_state")
