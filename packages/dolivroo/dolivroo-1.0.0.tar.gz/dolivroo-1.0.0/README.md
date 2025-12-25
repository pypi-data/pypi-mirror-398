# Dolivroo Python SDK

Official Python SDK for the Dolivroo Delivery API.

## Installation

```bash
pip install dolivroo
```

## Quick Start

```python
from dolivroo import Dolivroo

client = Dolivroo('your-api-key')

# Create a parcel
parcel = client.parcels.create('yalidine', {
    'customer': {
        'first_name': 'Mohamed',
        'last_name': 'Ali',
        'phone': '0555000000'
    },
    'destination': {
        'wilaya': 'Alger',
        'commune': 'Bab El Oued'
    },
    'package': {
        'products': 'T-Shirt x2'
    },
    'payment': {
        'amount': 2500
    }
})

print(f"Tracking ID: {parcel['tracking_id']}")
```

## API Reference

### Parcels

```python
# Create
client.parcels.create('yalidine', order_data)

# Get details
client.parcels.get('TRACKING123', 'yalidine')

# List all
client.parcels.list('yalidine', page=1, per_page=25)

# Update
client.parcels.update('TRACKING123', 'yalidine', updates)

# Cancel
client.parcels.cancel('TRACKING123', 'yalidine')

# Get label
client.parcels.get_label('TRACKING123', 'yalidine')

# Track
client.parcels.track('TRACKING123', 'yalidine')
```

### Rates

```python
# Get rates
client.rates.get('yalidine', 'Alger', 'Oran')

# Compare all providers
client.rates.compare('Alger', 'Oran')
```

### Wilayas

```python
# List all
client.wilayas.list()

# List for provider
client.wilayas.list('yalidine')
```

### Bulk Operations

```python
# Create multiple parcels
client.bulk.create_parcels('yalidine', [order1, order2, order3])
```

## Error Handling

```python
from dolivroo import Dolivroo, AuthenticationError, ValidationError, RateLimitError

try:
    client.parcels.create('yalidine', order)
except AuthenticationError:
    print('Invalid API key')
except ValidationError as e:
    print(f'Validation errors: {e.errors}')
except RateLimitError as e:
    print(f'Rate limited, retry after: {e.retry_after}')
```

## Configuration

```python
client = Dolivroo(
    api_key='your-api-key',
    base_url='https://custom-api.com/api/v1/unified',  # Optional
    timeout=60,  # Optional, in seconds
    verify_ssl=True  # Optional
)
```

## License

MIT
