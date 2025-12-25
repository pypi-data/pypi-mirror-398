from prestashop_webservice.base_model import BaseModel
from prestashop_webservice.logger import logger
from prestashop_webservice.models import OrderHistoryData
from prestashop_webservice.params import Params


class OrderHistory(BaseModel):
    """Complex queries for order_histories endpoint."""

    _data_class = OrderHistoryData

    def get_by_order(self, order_id: str) -> list[OrderHistoryData]:
        """Get history for a specific order."""
        params = Params(
            filter={"id_order": order_id},
            display=["id", "id_order", "id_order_state", "date_add"],
        )
        return self._query("order_histories", params, "order_histories")

    def get_recent_changes(self, limit: int = 20) -> list[OrderHistoryData]:
        """Get recent order status changes."""
        params = Params(
            display=["id", "id_order", "id_order_state", "date_add"],
            limit=limit,
        )
        return self._query("order_histories", params, "order_histories")

    def get_by_status(self, status_id: str, limit: int = 100) -> list[OrderHistoryData]:
        """Get order histories by status."""
        params = Params(
            filter={"id_order_state": status_id},
            display=["id", "id_order", "id_order_state"],
            limit=limit,
        )
        return self._query("order_histories", params, "order_histories")

    def create(self, order_id: str, order_state_id: str, date_add: str | None = None) -> bool:
        xml_payload = f"""<?xml version="1.0" encoding="UTF-8"?>
        <prestashop xmlns:xlink="http://www.w3.org/1999/xlink">
            <order_history>
                <id_order>{order_id}</id_order>
                <id_order_state>{order_state_id}</id_order_state>"""
        if date_add:
            xml_payload += f"\n                <date_add>{date_add}</date_add>"
        xml_payload += """
            </order_history>
        </prestashop>"""

        logger.debug(f"Creating order history for order {order_id} with state {order_state_id}")

        try:
            self.client.post("order_histories", xml_payload)
            logger.info(f"Order {order_id} status updated to {order_state_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update order {order_id}: {e}")
            return False
