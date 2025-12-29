# SGData SDK (Python)

Python client for Singapore Government Data APIs. A unified SDK providing access to weather, air quality, and carpark availability data from data.gov.sg.

This is the Python version of [sgdata-sdk](https://github.com/KT-afk/sgdata-sdk) (TypeScript).

## Features

- **Single Unified Client**: One client class for all 9 core endpoints
- **Full Type Hints**: Complete type annotations for better IDE support
- **Optional Historical Data**: Access current or historical data with optional parameters
- **Simple API**: Clean, intuitive interface following Python best practices
- **Zero Configuration**: Works out of the box with sensible defaults

## Installation

```bash
pip install sgdata-sdk
```

## Quick Start

```python
from sgdata import SGDataClient

# Initialize the client
client = SGDataClient()

# Get current PSI readings
psi_data = client.get_psi()
print(psi_data)

# Get historical PSI data
historical_psi = client.get_psi(date_time="2024-01-15T12:00:00")

# Use as context manager (auto-closes session)
with SGDataClient() as client:
    weather = client.get_2hour_weather_forecast()
    rainfall = client.get_rainfall()
```

## Available Endpoints

### Air Quality
- `get_psi()` - Pollutant Standards Index
- `get_pm25()` - PM2.5 readings

### Weather Forecasts
- `get_2hour_weather_forecast()` - Short-term forecast
- `get_24hour_weather_forecast()` - Daily forecast
- `get_4day_weather_forecast()` - Extended forecast

### Weather Measurements
- `get_rainfall()` - Rainfall measurements
- `get_relative_humidity()` - Humidity readings
- `get_air_temperature()` - Temperature readings

### Transport
- `get_carpark_availability()` - HDB carpark availability

## Usage Examples

### Current Data

```python
from sgdata import SGDataClient

client = SGDataClient()

# Get current air quality
psi = client.get_psi()
pm25 = client.get_pm25()

# Get current weather
forecast_2h = client.get_2hour_weather_forecast()
forecast_24h = client.get_24hour_weather_forecast()
forecast_4d = client.get_4day_weather_forecast()

# Get current measurements
rainfall = client.get_rainfall()
humidity = client.get_relative_humidity()
temperature = client.get_air_temperature()

# Get carpark availability
carparks = client.get_carpark_availability()
```

### Historical Data

All endpoints (except carpark availability) support both `date_time` and `date` parameters:

```python
# Using date_time (ISO 8601 format)
psi = client.get_psi(date_time="2024-01-15T12:00:00")

# Using date (YYYY-MM-DD format)
psi = client.get_psi(date="2024-01-15")

# Carpark availability only supports date_time
carparks = client.get_carpark_availability(date_time="2024-01-15T12:00:00")
```

### Error Handling

```python
import requests
from sgdata import SGDataClient

client = SGDataClient()

try:
    data = client.get_psi()
except requests.HTTPError as e:
    print(f"HTTP error: {e}")
except requests.RequestException as e:
    print(f"Request failed: {e}")
```

### Custom Configuration

```python
# Custom base URL and timeout
client = SGDataClient(
    base_url="https://custom-api.example.com/v1",
    timeout=60
)

# Access the requests session for advanced configuration
client.session.headers.update({"Custom-Header": "value"})
```

## API Reference

### SGDataClient

#### `__init__(base_url: Optional[str] = None, timeout: int = 30)`

Initialize the client.

**Parameters:**
- `base_url`: Custom API base URL (default: `https://api.data.gov.sg/v1`)
- `timeout`: Request timeout in seconds (default: 30)

#### Endpoint Methods

All endpoint methods follow this pattern:

```python
def get_endpoint_name(
    self,
    date_time: Optional[str] = None,
    date: Optional[str] = None
) -> Dict[str, Any]:
    """Endpoint description."""
```

**Parameters:**
- `date_time`: ISO 8601 datetime string (e.g., "2024-01-15T12:00:00")
- `date`: Date string in YYYY-MM-DD format (e.g., "2024-01-15")

**Returns:**
- `Dict[str, Any]`: Parsed JSON response from the API

**Raises:**
- `requests.HTTPError`: If the request fails (4xx, 5xx status codes)
- `requests.RequestException`: For other request-related errors

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/KT-afk/sgdata-sdk-python.git
cd sgdata-sdk-python

# Install in development mode with dev dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

### Type Checking

```bash
mypy sgdata
```

### Code Formatting

```bash
# Format code
black sgdata tests

# Lint code
ruff check sgdata tests
```

## Design Decisions

### Why a Single Client?

Unlike the existing `datagovsg` package which has 4 separate clients, this SDK uses a single unified `SGDataClient` class. This approach:

- Simplifies the API surface
- Reduces import complexity
- Makes it easier to discover available endpoints
- Follows the principle of cohesion (all endpoints are related to SG government data)

### Why Optional Parameters Instead of Separate Methods?

Instead of having separate methods like `get_psi()` and `get_historical_psi(date)`, we use optional parameters:

- Cleaner API with fewer methods to learn
- More intuitive - "get PSI data, optionally at this time"
- Consistent pattern across all endpoints
- Aligns with the TypeScript SDK design

### Why Not `**kwargs`?

We use explicit `date_time` and `date` parameters instead of `**kwargs` for:

- Better IDE autocomplete and type checking
- Clear documentation of available parameters
- Prevention of typos (e.g., `datetime` vs `date_time`)
- Explicit is better than implicit (Zen of Python)

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Related Projects

- [sgdata-sdk](https://github.com/KT-afk/sgdata-sdk) - TypeScript version
- [data.gov.sg](https://data.gov.sg) - Official Singapore Government Data Portal

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
