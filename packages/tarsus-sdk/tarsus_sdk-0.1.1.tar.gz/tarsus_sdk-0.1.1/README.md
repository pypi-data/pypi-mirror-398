# Tarsus Python SDK

The official Python client for the Tarsus API.

## Installation

```bash
pip install tarsus-sdk
```

## Usage

```python
import tarsus

# Initialize client (uses TARSUS_API_KEY environment variable by default)
client = tarsus.init()

# List products
products = client.products.list()
for product in products:
    print(product.name)
```
