from prestashop_webservice.base_model import BaseModel
from prestashop_webservice.models import CountryData
from prestashop_webservice.params import Params


class Country(BaseModel):
    """Complex queries for countries endpoint."""

    _data_class = CountryData

    def get_by_id(self, country_id: str) -> CountryData:
        """Get country by ID."""
        return self._query(f"countries/{country_id}", None, "country")

    def get_by_iso_code(self, iso_code: str) -> CountryData | None:
        """Get country by ISO code."""
        params = Params(
            filter={"iso_code": iso_code},
            display=["id", "iso_code", "name"],
        )
        countries = self._query("countries", params, "countries")
        return countries[0] if countries else None

    def get_active(self) -> list[CountryData]:
        """Get all active countries."""
        params = Params(
            filter={"active": "1"},
            display=["id", "iso_code", "name", "active"],
        )
        return self._query("countries", params, "countries")
