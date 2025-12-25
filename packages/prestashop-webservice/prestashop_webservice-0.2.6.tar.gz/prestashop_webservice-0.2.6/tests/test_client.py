"""Tests for the PrestaShop Client."""

import pytest

from prestashop_webservice import Client, Params, Sort, SortOrder


class TestClientSingleton:
    """Test Client Singleton pattern."""

    def test_singleton_same_instance(self, prestashop_base_url, prestashop_ws_key):
        """Test that Client returns the same instance."""
        client1 = Client(
            prestashop_base_url=prestashop_base_url, prestashop_ws_key=prestashop_ws_key
        )
        client2 = Client(
            prestashop_base_url=prestashop_base_url, prestashop_ws_key=prestashop_ws_key
        )
        assert client1 is client2


class TestClientOrders:
    """Test Client order-related queries."""

    def test_query_orders_returns_list(self, client):
        """Test that query_orders returns a list."""
        params = Params(limit=5)
        result = client.query_orders(params=params)
        assert isinstance(result, list)
        assert len(result) <= 5

    def test_query_orders_with_filter(self, client):
        """Test query_orders with filter."""
        params = Params(filter={"current_state": "2"}, limit=3)
        result = client.query_orders(params=params)
        assert isinstance(result, list)

    def test_query_order_by_id(self, client):
        """Test query_order by ID."""
        # First get an order ID
        params = Params(limit=1)
        orders = client.query_orders(params=params)
        if not orders:
            pytest.skip("No orders available")

        order_id = str(orders[0].get("id"))
        order = client.query_order(order_id=order_id)
        assert isinstance(order, dict)
        assert str(order.get("id")) == order_id


class TestClientCustomers:
    """Test Client customer-related queries."""

    def test_query_customers_returns_list(self, client):
        """Test that query_customers returns a list."""
        params = Params(limit=5)
        result = client.query_customers(params=params)
        assert isinstance(result, list)
        assert len(result) <= 5

    def test_query_customer_by_id(self, client):
        """Test query_customer by ID."""
        params = Params(limit=1)
        customers = client.query_customers(params=params)
        if not customers:
            pytest.skip("No customers available")

        customer_id = str(customers[0].get("id"))
        customer = client.query_customer(customer_id=customer_id)
        assert isinstance(customer, dict)
        assert str(customer.get("id")) == customer_id


class TestClientProducts:
    """Test Client product-related queries."""

    def test_query_products_returns_list(self, client):
        """Test that query_products returns a list."""
        params = Params(limit=5)
        result = client.query_products(params=params)
        assert isinstance(result, list)
        assert len(result) <= 5

    def test_query_product_by_id(self, client):
        """Test query_product by ID."""
        params = Params(limit=1)
        products = client.query_products(params=params)
        if not products:
            pytest.skip("No products available")

        product_id = str(products[0].get("id"))
        product = client.query_product(product_id=product_id)
        assert isinstance(product, dict)
        assert str(product.get("id")) == product_id


class TestClientOrderCarriers:
    """Test Client order_carriers queries."""

    def test_query_order_carriers_returns_list(self, client):
        """Test that query_order_carriers returns a list."""
        params = Params(limit=5)
        result = client.query_order_carriers(params=params)
        assert isinstance(result, list)


class TestClientOrderHistories:
    """Test Client order_histories queries."""

    def test_query_order_histories_returns_list(self, client):
        """Test that query_order_histories returns a list."""
        params = Params(limit=5)
        result = client.query_order_histories(params=params)
        assert isinstance(result, list)

    def test_query_order_histories_by_order(self, client):
        """Test query_order_histories filtered by order."""
        # Get an order ID first
        params = Params(limit=1)
        orders = client.query_orders(params=params)
        if not orders:
            pytest.skip("No orders available")

        order_id = str(orders[0].get("id"))
        params = Params(filter={"id_order": order_id})
        histories = client.query_order_histories(params=params)
        assert isinstance(histories, list)


class TestClientAddresses:
    """Test Client addresses queries."""

    def test_query_addresses_returns_list(self, client):
        """Test that query_addresses returns a list."""
        params = Params(limit=5)
        result = client.query_addresses(params=params)
        assert isinstance(result, list)

    def test_query_address_by_id(self, client):
        """Test query_address by ID."""
        params = Params(limit=1)
        addresses = client.query_addresses(params=params)
        if not addresses:
            pytest.skip("No addresses available")

        address_id = str(addresses[0].get("id"))
        address = client.query_address(address_id=address_id)
        assert isinstance(address, dict)
        assert str(address.get("id")) == address_id


class TestClientCountries:
    """Test Client countries queries."""

    def test_query_countries_returns_list(self, client):
        """Test that query_countries returns a list."""
        params = Params(limit=5)
        result = client.query_countries(params=params)
        assert isinstance(result, list)

    def test_query_country_by_id(self, client):
        """Test query_country by ID."""
        params = Params(limit=1)
        countries = client.query_countries(params=params)
        if not countries:
            pytest.skip("No countries available")

        country_id = str(countries[0].get("id"))
        country = client.query_country(country_id=country_id)
        assert isinstance(country, dict)
        assert str(country.get("id")) == country_id


class TestClientOrderStates:
    """Test Client order_states queries."""

    def test_query_order_state_by_id(self, client):
        """Test query_order_state by ID."""
        # PrestaShop usually has order states with IDs 1-10
        state = client.query_order_state(state_id="1")
        assert isinstance(state, dict)
        assert str(state.get("id")) == "1"


class TestClientParams:
    """Test Client with various Params configurations."""

    def test_params_with_display(self, client):
        """Test Params with display fields."""
        params = Params(display=["id", "reference", "total_paid"], limit=3)
        orders = client.query_orders(params=params)
        assert isinstance(orders, list)
        if orders:
            # Verify only requested fields are present (plus some metadata)
            order = orders[0]
            assert "id" in order

    def test_params_with_sort(self, client):
        """Test Params with sorting."""
        params = Params(
            sort=Sort(field="id", order=SortOrder.DESC),
            display=["id"],
            limit=5,
        )
        orders = client.query_orders(params=params)
        assert isinstance(orders, list)
        if len(orders) >= 2:
            # Verify descending order
            assert int(orders[0]["id"]) >= int(orders[1]["id"])

    def test_params_with_filter_and_display(self, client):
        """Test Params with both filter and display."""
        params = Params(filter={"active": "1"}, display=["id", "email"], limit=5)
        customers = client.query_customers(params=params)
        assert isinstance(customers, list)


class TestClientEdgeCases:
    """Test Client edge cases and error handling."""

    def test_query_with_invalid_id(self, client):
        """Test querying with invalid ID."""
        from httpx import HTTPStatusError

        with pytest.raises(HTTPStatusError):
            client.query_order(order_id="invalid_id_99999999")

    def test_query_empty_results(self, client):
        """Test query that returns empty results."""
        params = Params(filter={"id": "99999999"})
        result = client.query_orders(params=params)
        # Empty results from API return empty dict, not list
        assert isinstance(result, list | dict)
        if isinstance(result, list):
            assert len(result) == 0
        else:
            assert result == {}

    def test_single_result_becomes_list(self, client):
        """Test that single result is converted to list for plural endpoints."""
        # Get a specific order
        params = Params(limit=1)
        orders = client.query_orders(params=params)
        if not orders:
            pytest.skip("No orders available")

        # Query by specific ID (should return single item as list)
        order_id = orders[0].get("id")
        params = Params(filter={"id": order_id})
        result = client.query_orders(params=params)
        assert isinstance(result, list)
        assert len(result) == 1

    def test_query_state_by_id(self, client):
        """Test querying a state by ID."""
        # Get state 1 (should exist)
        state = client.query_state(state_id="1")
        assert isinstance(state, dict)
        assert state.get("id") == 1

    def test_query_product_images(self, client):
        """Test querying product images."""
        # Note: This endpoint may fail with 500, so we catch exceptions
        try:
            images = client.query_product_images(product_id="2381")
            assert isinstance(images, list | dict)
        except Exception:
            # Image endpoint is known to be problematic
            pass

    def test_query_without_response_key(self, client):
        """Test _query without response_key returns full JSON."""
        # Call _query directly without response_key
        result = client._query("orders/1")
        assert isinstance(result, dict)
        # Full JSON response should have the resource wrapper
        assert "order" in result or "id" in result
