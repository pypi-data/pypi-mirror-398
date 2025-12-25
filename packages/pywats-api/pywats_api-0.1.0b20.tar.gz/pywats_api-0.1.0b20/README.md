# PyWATS

[![PyPI version](https://badge.fury.io/py/pywats-api.svg)](https://badge.fury.io/py/pywats-api)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python library for interacting with the [WATS](https://wats.com) (Web-based Automated Test System) API.

> **⚠️ Beta Release**: This is a beta version. The API is stabilizing but may have changes before 1.0.

## Requirements

- **Python 3.10** or later
- **WATS Server 2025.3.9.824** or later

## Features

- **PyWATS Library** - Core API library for WATS integration
  - Product management
  - Asset management  
  - Report creation and submission
  - Production/serial number management
  - RootCause ticket system
  - Software distribution
  - Statistics and analytics

- **PyWATS Client** - Desktop and headless client application
  - Connection management
  - Converter configuration
  - Report queue management
  - **GUI Mode**: Qt-based desktop application (Windows, macOS, Linux)
  - **Headless Mode**: CLI and HTTP API for servers, Raspberry Pi, embedded systems

## Installation

### From PyPI (Recommended)

```bash
# Install core API library only
pip install pywats-api

# Install with GUI client (requires Qt)
pip install pywats-api[client]

# Install headless client (no Qt - for Raspberry Pi, servers)
pip install pywats-api[client-headless]

# Install with MCP server (for AI assistant integration)
pip install pywats-api[mcp]
```

### From Source (Development)

```bash
# Clone the repository
git clone https://github.com/olreppe/pyWATS.git
cd pyWATS

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Install in development mode
pip install -e ".[dev]"
```

## Configuration

Create a configuration with your WATS credentials:

```python
from pywats import pyWATS

api = pyWATS(
    base_url="https://your-server.wats.com",
    token="your_base64_encoded_token"
)
```

Or use environment variables:

```env
WATS_BASE_URL=https://your-server.wats.com
WATS_AUTH_TOKEN=your_base64_encoded_token
```

## Quick Start

```python
from pywats import pyWATS, WATSFilter

# Initialize API
api = pyWATS(
    base_url="https://your-server.wats.com",
    token="your_token"
)

# Test connection
if api.test_connection():
    print(f"Connected! Server version: {api.get_version()}")

# Get products
products = api.product.get_products()
for p in products:
    print(f"{p.part_number}: {p.name}")

# Query recent reports
filter = WATSFilter(top_count=10)
headers = api.report.query_uut_headers(filter)
```

### Enable Debug Logging

```python
from pywats import pyWATS, enable_debug_logging

# Quick debug mode - shows all library operations
enable_debug_logging()

# Or configure logging your way
import logging
logging.basicConfig(level=logging.INFO)
logging.getLogger('pywats').setLevel(logging.DEBUG)

# Now use the API with detailed logging
api = pyWATS(base_url="...", token="...")
```

See [LOGGING_STRATEGY.md](LOGGING_STRATEGY.md) for comprehensive logging documentation.

## Running the GUI Client

```bash
python -m pywats_client
```

### GUI Configuration

The GUI supports modular tab configuration and logging control:

- **Tab Visibility**: Show/hide tabs (Software, SN Handler, etc.) based on your needs
- **Logging Integration**: Automatic PyWATS library logging when debug mode is enabled
- **Multiple Instances**: Run multiple client instances with separate configurations

See [GUI Configuration Guide](src/pywats_client/GUI_CONFIGURATION.md) for detailed setup instructions.

## Running Headless (Raspberry Pi, Servers)

For systems without display or Qt support:

```bash
# Initialize configuration
pywats-client config init

# Test connection
pywats-client test-connection

# Run service with HTTP control API
pywats-client start --api --api-port 8765

# Run as daemon (Linux)
pywats-client start --daemon
```

### CLI Commands

```bash
pywats-client config show          # Show configuration
pywats-client config set key value # Set config value
pywats-client status               # Show service status
pywats-client converters list      # List converters
```

### HTTP Control API

When running with `--api`, manage the service remotely:

```bash
curl http://localhost:8765/status    # Get status
curl http://localhost:8765/config    # Get configuration
curl -X POST http://localhost:8765/restart  # Restart services
```

See [Headless Operation Guide](src/pywats_client/control/HEADLESS_GUIDE.md) for complete documentation.

## Project Structure

```
pyWATS/
├── src/
│   ├── pywats/              # Core library
│   │   ├── domains/         # Domain models and services
│   │   ├── core/            # HTTP client, exceptions, station
│   │   ├── models/          # Report models (UUT/UUR)
│   └── pywats_client/       # Client application
│       ├── core/            # Core client functionality
│       ├── gui/             # Qt GUI components (optional)
│       ├── control/         # Headless control (CLI, HTTP API)
│       └── services/        # Background services
├── converters/              # User converter plugins
├── docs/                    # Documentation
│   ├── api_specs/           # OpenAPI specifications
│   ├── examples/            # Usage examples
│   └── gui_screens/         # GUI screenshots
├── pyproject.toml           # Project configuration
└── requirements.txt         # Dependencies
```

## Documentation

- [Architecture Overview](docs/ARCHITECTURE.md) - System design and layered architecture
- [Report Module](docs/usage/REPORT_MODULE.md) - Test reports and factory methods
- [Product Module](docs/usage/PRODUCT_MODULE.md) - Product/BOM management
- [Production Module](docs/usage/PRODUCTION_MODULE.md) - Serial number and unit tracking

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html
```

## Contributing

This project is maintained by [Virinco AS](https://virinco.com). 

## License

MIT License - see [LICENSE](LICENSE) for details.

## Links

- [WATS Website](https://wats.com)
- [Virinco](https://virinco.com)
- [GitHub Repository](https://github.com/olreppe/pyWATS)
- [Changelog](CHANGELOG.md)
