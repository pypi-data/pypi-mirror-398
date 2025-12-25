# PrestaShop Webservice

Python client for PrestaShop API with caching, logging, and type hints.

## Installation

```bash
pip install prestashop-webservice
```

## Quick Start

```python
from prestashop_webservice import Client, Params, Sort, SortOrder

# Initialize client
client = Client(
    prestashop_base_url="https://your-store.com/api",
    prestashop_ws_key="YOUR_API_KEY"
)

# Simple queries
order = client.query_order(order_id="123")
customer = client.query_customer(customer_id="456")

# Advanced queries with parameters
params = Params(
    filter={"id_customer": "123"},
    sort=Sort(field="date_add", order=SortOrder.DESC),
    display=["id", "total_paid", "reference"],
    limit=10
)
orders = client.query_orders(params=params)
```

## Features

- 🚀 HTTP client with connection pooling
- 💾 Automatic caching (24h TTL)
- 📝 Logging with Loguru
- 🎯 Full type hints
- 🔒 Singleton pattern

## Available Methods

- `query_order()`, `query_orders()`, `exists_order()`
- `query_customer()`, `query_customers()`
- `query_product()`, `query_address()`, `query_country()`
- `query_order_carriers()`, `query_order_histories()`, `query_order_state()`

## License

MIT License - See [LICENSE](LICENSE) file for details.
