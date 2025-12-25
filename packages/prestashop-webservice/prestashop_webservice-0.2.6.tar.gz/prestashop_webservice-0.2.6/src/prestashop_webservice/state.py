from prestashop_webservice.base_model import BaseModel
from prestashop_webservice.models import StateData


class State(BaseModel):
    """Complex queries for states endpoint."""

    _data_class = StateData

    def get_by_id(self, state_id: str) -> StateData:
        """Get state by ID (geographic state/province)."""
        return self._query(f"states/{state_id}", None, "state")
