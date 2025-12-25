# pyWATS MCP Server

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server for interacting with WATS (Web-based Automated Test System) manufacturing test data.

This server allows AI assistants like Claude, ChatGPT, and VS Code Copilot to query and analyze your WATS test data.

## Installation

```bash
pip install pywats-api[mcp]
```

Or from source:
```bash
pip install -e ".[mcp]"
```

## Configuration

Set environment variables:

```bash
export WATS_BASE_URL="https://your-company.wats.com"
export WATS_AUTH_TOKEN="your_base64_encoded_token"
```

### Claude Desktop

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS or `%APPDATA%\Claude\claude_desktop_config.json` on Windows):

```json
{
  "mcpServers": {
    "wats": {
      "command": "python",
      "args": ["-m", "pywats_mcp"],
      "env": {
        "WATS_BASE_URL": "https://your-company.wats.com",
        "WATS_AUTH_TOKEN": "your_token_here"
      }
    }
  }
}
```

### VS Code (Copilot)

Add to your VS Code settings (`.vscode/settings.json` or user settings):

```json
{
  "mcp": {
    "servers": {
      "wats": {
        "command": "python",
        "args": ["-m", "pywats_mcp"],
        "env": {
          "WATS_BASE_URL": "https://your-company.wats.com",
          "WATS_AUTH_TOKEN": "your_token_here"
        }
      }
    }
  }
}
```

## Available Tools (25 tools)

### Connection & System
| Tool | Description |
|------|-------------|
| `wats_test_connection` | Test connection to WATS server and get version info |
| `wats_get_version` | Get WATS server version information |
| `wats_get_processes` | Get all defined test processes/operations |

### Products
| Tool | Description |
|------|-------------|
| `wats_get_products` | List products (part numbers) |
| `wats_get_product` | Get detailed product information |
| `wats_get_product_revisions` | Get all revisions for a product |

### Reports
| Tool | Description |
|------|-------------|
| `wats_query_reports` | Query test reports with filters (part number, serial, status, station, etc.) |
| `wats_get_report` | Get full report details including all measurements |
| `wats_get_report_steps` | Get step hierarchy and results for a report |
| `wats_get_failures` | Get recent test failures |
| `wats_search_serial` | Search all test history for a serial number |

### Statistics & Yield
| Tool | Description |
|------|-------------|
| `wats_get_yield` | Calculate yield (pass rate) statistics |
| `wats_get_yield_by_station` | Compare yield across different test stations |
| `wats_get_yield_trend` | Get yield trend over time (daily breakdown) |

### Assets / Equipment
| Tool | Description |
|------|-------------|
| `wats_get_assets` | List equipment/assets |
| `wats_get_asset` | Get detailed asset information |
| `wats_get_calibration_due` | Get assets with calibration due within N days |
| `wats_get_asset_types` | Get all asset types defined in WATS |

### Production / Units
| Tool | Description |
|------|-------------|
| `wats_get_unit` | Get production unit information |
| `wats_get_unit_history` | Get complete test/production history for a unit |

### RootCause / Issue Tracking
| Tool | Description |
|------|-------------|
| `wats_get_tickets` | List RootCause tickets (open/closed/all) |
| `wats_get_ticket` | Get detailed ticket information |
| `wats_create_ticket` | Create a new RootCause ticket |

### Software Distribution
| Tool | Description |
|------|-------------|
| `wats_get_software_packages` | List software packages |
| `wats_get_software_package` | Get software package details |

## Usage Examples

Once configured, you can ask your AI assistant:

**Test Data Analysis:**
- "Show me yesterday's test failures"
- "What's the yield for Product X this week?"
- "Search for all tests of serial number ABC123"
- "Compare yield across our ICT stations"
- "Show me the yield trend for the last month"

**Equipment Management:**
- "Which assets need calibration in the next 30 days?"
- "Get details for multimeter SN12345"
- "List all our test fixtures"

**Issue Tracking:**
- "List open RootCause tickets"
- "Create a ticket for the yield drop on line 2"
- "Get details for ticket #123"

**Production Tracking:**
- "Show me the test history for unit XYZ789"
- "What phase is serial SN12345 in?"

## Running Standalone

```bash
# Set environment variables first
export WATS_BASE_URL="https://your-company.wats.com"
export WATS_AUTH_TOKEN="your_token"

# Run the server
python -m pywats_mcp
```

## Requirements

- Python 3.10+
- pywats-api
- mcp>=1.0.0 (Model Context Protocol SDK)

## License

MIT License - see LICENSE file in the root directory.
