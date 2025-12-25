# Usage Guide

## Quick Start

```python
from prestashop_webservice import Client, Params, Sort, SortOrder

# 1. Initialize
repo = Client(
    prestashop_base_url="https://your-store.com/api",
    prestashop_ws_key="YOUR_API_KEY"
)

# 2. Make a simple query
order = repo.query_order(order_id="123")

# 3. Query with parameters
params = Params(
    filter={"id_customer": "456"},
    limit=10
)
orders = repo.query_orders(params=params)
```

## Basic Concepts

### 1. Singleton Pattern

The `Client` class uses the Singleton pattern, which means only one instance will exist in your entire application:

```python
repo1 = Client(
    prestashop_base_url="https://store1.com/api",
    prestashop_ws_key="KEY1"
)

repo2 = Client(
    prestashop_base_url="https://store2.com/api",  # This is ignored
    prestashop_ws_key="KEY2"  # This is also ignored
)

# repo1 and repo2 are the same instance
assert repo1 is repo2  # True
```

### 2. Cache System

All queries are automatically cached:

```python
# First call: makes HTTP request
order1 = repo.query_order(order_id="123")

# Second call: uses cache (instant)
order2 = repo.query_order(order_id="123")

# Cache expires after 24 hours (86400 seconds)
```

### 3. Query Parameters

The `Params` object allows you to build complex queries safely:

```python
from prestashop_webservice import Params, Sort, SortOrder

params = Params(
    filter={"active": "1", "id_category": "5"},
    sort=Sort(field="price", order=SortOrder.ASC),
    display=["id", "name", "price"],
    limit=50
)
```

## Common Use Cases

### Search for customer orders

```python
# Step 1: Search customer by email
customer_params = Params(
    filter={"email": "customer@email.com"}
)
customers = repo.query_customers(params=customer_params)

if customers:
    customer_id = customers[0]["id"]

    # Step 2: Get customer orders
    orders_params = Params(
        filter={"id_customer": str(customer_id)},
        sort=Sort(field="date_add", order=SortOrder.DESC)
    )
    orders = repo.query_orders(params=orders_params)
```

### Get complete order details

```python
order_id = "12345"

# 1. Basic order data
order = repo.query_order(order_id=order_id)

# 2. Delivery address
delivery_address_id = order.get("id_address_delivery")
delivery_address = repo.query_address(address_id=delivery_address_id)

# 3. Customer
customer_id = order.get("id_customer")
customer = repo.query_customer(customer_id=customer_id)

# 4. Status history
history_params = Params(
    filter={"id_order": order_id}
)
histories = repo.query_order_histories(params=history_params)

# 5. Shipping information
carrier_params = Params(
    filter={"id_order": order_id}
)
carrier_info = repo.query_order_carriers(params=carrier_params)
```

### List products by category

```python
category_id = "5"

params = Params(
    filter={
        "id_category_default": category_id,
        "active": "1"
    },
    sort=Sort(field="name", order=SortOrder.ASC),
    display=["id", "name", "price", "quantity"],
    limit=100
)

products = repo.query_products(params=params)
```

### Get recent orders

```python
params = Params(
    sort=Sort(field="date_add", order=SortOrder.DESC),
    display=["id", "reference", "total_paid", "current_state", "date_add"],
    limit=20
)

recent_orders = repo.query_orders(params=params)

for order in recent_orders:
    print(f"Order {order['reference']}: {order['total_paid']}€")
```

### Check product stock

```python
product_ids = ["1", "2", "3", "4", "5"]

for product_id in product_ids:
    product = repo.query_product(product_id=product_id)
    quantity = product.get("quantity", 0)
    name = product.get("name", "N/A")
    print(f"{name}: {quantity} units")
```

## Error Handling

```python
from httpx import HTTPStatusError

try:
    order = repo.query_order(order_id="99999")
except HTTPStatusError as e:
    if e.response.status_code == 404:
        print("Order not found")
    elif e.response.status_code == 401:
        print("Invalid API Key")
    else:
        print(f"HTTP Error: {e}")
except Exception as e:
    print(f"Error: {e}")
```

## Advanced Configuration

### Adjust connection limits

For high-load APIs:

```python
repo = Client(
    prestashop_base_url="https://your-store.com/api",
    prestashop_ws_key="YOUR_KEY",
    max_connections=10,  # More simultaneous connections
    max_keepalive_connections=5,
    keepalive_expiry=30.0  # Keep connections alive longer
)
```

### Customize logging

```python
from src.logger import logger

# Change log level
logger.remove()
logger.add("custom.log", level="DEBUG")

# Now you'll see all requests in the log
```

## Best Practices

1. **Use cache to your advantage**: Identical queries are served from cache, so don't be afraid to call methods multiple times.

2. **Filter on the server**: Use `filter` parameters instead of fetching all records and filtering in Python.

3. **Limit results**: Always use `limit` to avoid loading too much data.

4. **Select only necessary fields**: Use `display` to reduce response size.

5. **Handle errors appropriately**: PrestaShop API can return 404, 401, etc. errors.

## Quick Filter Reference

PrestaShop filters support various operators:

```python
# Equality
Params(filter={"id_customer": "123"})

# Range
Params(filter={"id": "[1|100]"})  # Between 1 and 100

# Greater than
Params(filter={"total_paid": ">[50]"})

# Less than
Params(filter={"total_paid": "<[100]"})

# Multiple values
Params(filter={"id": "[1|2|3|4|5]"})

# Partial search (with %)
Params(filter={"name": "[%shirt%]"})
```

## Next Steps

- Read the [PrestaShop API documentation](https://devdocs.prestashop.com/)
- Review the [examples](../examples/)
- Check the [API reference](API_REFERENCE.md)
