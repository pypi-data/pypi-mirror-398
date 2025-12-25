"""
Entry point for running the WATS MCP server.

Usage:
    python -m pywats_mcp

Required environment variables:
    WATS_BASE_URL - Your WATS server URL (e.g., https://company.wats.com)
    WATS_AUTH_TOKEN - Your WATS API token (base64 encoded)
"""

import asyncio
from .server import main

if __name__ == "__main__":
    asyncio.run(main())
