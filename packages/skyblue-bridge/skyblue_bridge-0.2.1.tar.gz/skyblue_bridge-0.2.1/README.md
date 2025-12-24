# SkyBlue Bridge

Python client for interacting with the SkyBlue MT5 bridge microservice.

## Installation

```bash
pip install skyblue-bridge
```

## Usage

```python
from skyblue_bridge import MTClient

client = MTClient(api_key="your-api-key")
print(client.get_server_status())

# Retrieve last 10 hourly candles
ohlc = client.get_ohlc("EURUSD", "1h", 10)

# Fetch order/trade details or adjust stops
details = client.get_order_details(123456789)
client.modify_order(123456789, sl=1.0950, tp=1.1200)
```
