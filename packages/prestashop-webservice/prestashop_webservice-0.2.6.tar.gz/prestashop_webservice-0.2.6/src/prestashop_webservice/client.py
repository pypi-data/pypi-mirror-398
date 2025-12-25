from typing import cast

from cachetools import TTLCache, cached
from httpx import BasicAuth, Limits, Timeout
from httpx import Client as HTTPXClient

from prestashop_webservice.config import Config
from prestashop_webservice.logger import logger
from prestashop_webservice.params import Params


class Client:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(
        self,
        prestashop_base_url: str,
        prestashop_ws_key: str,
        max_connections: int = Config.MAX_CONNECTIONS,
        max_keepalive_connections: int = Config.MAX_KEEPALIVE_CONNECTIONS,
        keepalive_expiry: float = Config.KEEPALIVE_EXPIRY,
    ):
        if getattr(self, "_initialized", False):
            return

        self.base_url = prestashop_base_url.rstrip("/api")
        self.client = HTTPXClient(
            base_url=prestashop_base_url,
            timeout=Timeout(connect=5.0, read=10.0, write=10.0, pool=5.0),
            limits=Limits(
                max_connections=max_connections,
                max_keepalive_connections=max_keepalive_connections,
                keepalive_expiry=keepalive_expiry,
            ),
            follow_redirects=False,
            auth=BasicAuth(prestashop_ws_key, ""),
            params={"output_format": "JSON"},
        )
        self._initialized = True

    @cached(cache=TTLCache(maxsize=100, ttl=86400))
    def query_order(self, params: Params | None = None, order_id: str = "") -> dict:
        return cast(dict, self._query(f"orders/{order_id}", params, "order"))

    def query_address(self, params: Params | None = None, address_id: str = "") -> dict:
        return cast(dict, self._query(f"addresses/{address_id}", params, "address"))

    @cached(cache=TTLCache(maxsize=100, ttl=86400))
    def query_order_carriers(self, params: Params | None = None) -> list[dict]:
        return cast(list[dict], self._query("order_carriers", params, "order_carriers"))

    @cached(cache=TTLCache(maxsize=200, ttl=86400))
    def query_customer(self, params: Params | None = None, customer_id: str = "") -> dict:
        return cast(dict, self._query(f"customers/{customer_id}", params, "customer"))

    @cached(cache=TTLCache(maxsize=100, ttl=86400))
    def query_customers(self, params: Params | None = None) -> list[dict]:
        return cast(list[dict], self._query("customers", params, "customers"))

    @cached(cache=TTLCache(maxsize=200, ttl=86400))
    def query_orders(self, params: Params | None = None) -> list[dict]:
        return cast(list[dict], self._query("orders", params, "orders"))

    @cached(cache=TTLCache(maxsize=500, ttl=86400))
    def query_product(self, params: Params | None = None, product_id: str = "") -> dict:
        return cast(dict, self._query(f"products/{product_id}", params, "product"))

    @cached(cache=TTLCache(maxsize=50, ttl=86400))
    def query_country(self, params: Params | None = None, country_id: str = "") -> dict:
        return cast(dict, self._query(f"countries/{country_id}", params, "country"))

    @cached(cache=TTLCache(maxsize=100, ttl=86400))
    def query_countries(self, params: Params | None = None) -> list[dict]:
        return cast(list[dict], self._query("countries", params, "countries"))

    @cached(cache=TTLCache(maxsize=100, ttl=86400))
    def query_addresses(self, params: Params | None = None) -> list[dict]:
        return cast(list[dict], self._query("addresses", params, "addresses"))

    @cached(cache=TTLCache(maxsize=500, ttl=86400))
    def query_products(self, params: Params | None = None) -> list[dict]:
        return cast(list[dict], self._query("products", params, "products"))

    @cached(cache=TTLCache(maxsize=50, ttl=86400))
    def query_state(self, params: Params | None = None, state_id: str = "") -> dict:
        return cast(dict, self._query(f"states/{state_id}", params, "state"))

    @cached(cache=TTLCache(maxsize=200, ttl=86400))
    def query_product_images(
        self, params: Params | None = None, product_id: str = ""
    ) -> list[dict]:
        return cast(list[dict], self._query(f"images/products/{product_id}", params, "image"))

    @cached(cache=TTLCache(maxsize=100, ttl=86400))
    def query_order_histories(self, params: Params | None = None) -> list[dict]:
        return cast(list[dict], self._query("order_histories", params, "order_histories"))

    @cached(cache=TTLCache(maxsize=50, ttl=86400))
    def query_order_state(self, params: Params | None = None, state_id: str = "") -> dict:
        return cast(dict, self._query(f"order_states/{state_id}", params, "order_state"))

    @cached(cache=TTLCache(maxsize=500, ttl=86400))
    def query_combination(self, params: Params | None = None, combination_id: str = "") -> dict:
        return cast(dict, self._query(f"combinations/{combination_id}", params, "combination"))

    @cached(cache=TTLCache(maxsize=500, ttl=86400))
    def query_combinations(self, params: Params | None = None) -> list[dict]:
        return cast(list[dict], self._query("combinations", params, "combinations"))

    def post(self, endpoint: str, xml_payload: str) -> dict:
        logger.debug(f"POSTing to {endpoint}")

        response = self.client.post(
            f"/{endpoint}",
            content=xml_payload,
            headers={"Content-Type": "application/xml"},
        )
        response.raise_for_status()

        return response.json() or {}

    def _query(
        self, endpoint: str, params: Params | None = None, response_key: str = ""
    ) -> dict | list:
        logger.debug(f"Requesting {endpoint}")

        response = self.client.get(f"/{endpoint}", params=params.to_dict() if params else None)
        response.raise_for_status()

        json_response = response.json() or {}

        if response_key:
            result = json_response.get(response_key, {})
            return result if result else {}

        return json_response
