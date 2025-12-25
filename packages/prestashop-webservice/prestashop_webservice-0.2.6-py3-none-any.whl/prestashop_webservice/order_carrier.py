from prestashop_webservice.base_model import BaseModel
from prestashop_webservice.models import OrderCarrierData
from prestashop_webservice.params import Params


class OrderCarrier(BaseModel):
    """Complex queries for order_carriers endpoint."""

    _data_class = OrderCarrierData

    def get_by_order(self, order_id: str) -> list[OrderCarrierData]:
        """Get carriers for a specific order."""
        params = Params(
            filter={"id_order": order_id},
            display=["id", "id_order", "tracking_number"],
        )
        return self._query("order_carriers", params, "order_carriers")

    def get_by_tracking(self, tracking: str) -> list[OrderCarrierData]:
        """Find order carriers by tracking number."""
        params = Params(
            filter={"tracking_number": tracking},
            display=["id", "id_order", "tracking_number"],
        )
        result = self._query("order_carriers", params, "order_carriers")
        return result if result is not None else []

    def get_latest_by_tracking(self, tracking: str) -> OrderCarrierData | None:
        """Get the most recent order carrier by tracking number."""
        carriers = self.get_by_tracking(tracking)
        if not carriers:
            return None
        return max(carriers, key=lambda r: r.id)
