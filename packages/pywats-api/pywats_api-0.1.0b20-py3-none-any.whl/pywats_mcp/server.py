"""
WATS MCP Server - Comprehensive MCP server for WATS API.

Run with: python -m pywats_mcp
Or configure in Claude Desktop / VS Code settings.
"""

import os
import logging
from typing import Any, Optional
from datetime import datetime, timedelta

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Import pywats API
from pywats import pyWATS

logger = logging.getLogger(__name__)

# Create server instance
server = Server("wats-mcp")

# Global API instance (configured on startup)
_api: Optional[pyWATS] = None


def get_api() -> pyWATS:
    """Get or create the WATS API instance."""
    global _api
    if _api is None:
        base_url = os.environ.get("WATS_BASE_URL")
        token = os.environ.get("WATS_AUTH_TOKEN")
        
        if not base_url or not token:
            raise ValueError(
                "WATS_BASE_URL and WATS_AUTH_TOKEN environment variables required. "
                "Set them before running the MCP server."
            )
        
        _api = pyWATS(base_url=base_url, token=token)
    return _api


# =============================================================================
# Tool Definitions
# =============================================================================

@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available WATS tools."""
    return [
        # ----- Connection & System -----
        Tool(
            name="wats_test_connection",
            description="Test the connection to the WATS server and get version info",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        Tool(
            name="wats_get_version",
            description="Get WATS server version information",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        Tool(
            name="wats_get_processes",
            description="Get all defined test processes/operations in WATS",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        
        # ----- Products -----
        Tool(
            name="wats_get_products",
            description="Get list of products (part numbers) from WATS",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Max products to return", "default": 50}
                }
            }
        ),
        Tool(
            name="wats_get_product",
            description="Get detailed information about a specific product by part number",
            inputSchema={
                "type": "object",
                "properties": {
                    "part_number": {"type": "string", "description": "The product part number"}
                },
                "required": ["part_number"]
            }
        ),
        Tool(
            name="wats_get_product_revisions",
            description="Get all revisions for a specific product",
            inputSchema={
                "type": "object",
                "properties": {
                    "part_number": {"type": "string", "description": "The product part number"}
                },
                "required": ["part_number"]
            }
        ),
        
        # ----- Reports -----
        Tool(
            name="wats_query_reports",
            description="Query test reports (UUT/UUR) with various filters. Returns report headers.",
            inputSchema={
                "type": "object",
                "properties": {
                    "part_number": {"type": "string", "description": "Filter by part number"},
                    "serial_number": {"type": "string", "description": "Filter by serial number"},
                    "status": {"type": "string", "enum": ["passed", "failed", "all"], "description": "Filter by status"},
                    "days": {"type": "integer", "description": "Reports from last N days", "default": 7},
                    "station": {"type": "string", "description": "Filter by station name"},
                    "operator": {"type": "string", "description": "Filter by operator name"},
                    "limit": {"type": "integer", "description": "Max reports to return", "default": 100}
                }
            }
        ),
        Tool(
            name="wats_get_report",
            description="Get full details of a specific test report including all steps and measurements",
            inputSchema={
                "type": "object",
                "properties": {
                    "report_id": {"type": "string", "description": "The report ID (GUID)"}
                },
                "required": ["report_id"]
            }
        ),
        Tool(
            name="wats_get_report_steps",
            description="Get the step hierarchy and results for a specific report",
            inputSchema={
                "type": "object",
                "properties": {
                    "report_id": {"type": "string", "description": "The report ID (GUID)"},
                    "failed_only": {"type": "boolean", "description": "Only show failed steps", "default": False}
                },
                "required": ["report_id"]
            }
        ),
        Tool(
            name="wats_get_failures",
            description="Get recent test failures with failure details",
            inputSchema={
                "type": "object",
                "properties": {
                    "part_number": {"type": "string", "description": "Filter by part number"},
                    "station": {"type": "string", "description": "Filter by station"},
                    "days": {"type": "integer", "description": "Failures from last N days", "default": 1},
                    "limit": {"type": "integer", "description": "Max failures to return", "default": 50}
                }
            }
        ),
        Tool(
            name="wats_search_serial",
            description="Search for all test history of a specific serial number",
            inputSchema={
                "type": "object",
                "properties": {
                    "serial_number": {"type": "string", "description": "The serial number to search"}
                },
                "required": ["serial_number"]
            }
        ),
        
        # ----- Statistics & Yield -----
        Tool(
            name="wats_get_yield",
            description="Get yield (pass rate) statistics for products/stations",
            inputSchema={
                "type": "object",
                "properties": {
                    "part_number": {"type": "string", "description": "Filter by part number"},
                    "station": {"type": "string", "description": "Filter by station"},
                    "days": {"type": "integer", "description": "Calculate over last N days", "default": 7}
                }
            }
        ),
        Tool(
            name="wats_get_yield_by_station",
            description="Compare yield across different test stations",
            inputSchema={
                "type": "object",
                "properties": {
                    "part_number": {"type": "string", "description": "Filter by part number"},
                    "days": {"type": "integer", "description": "Calculate over last N days", "default": 7}
                }
            }
        ),
        Tool(
            name="wats_get_yield_trend",
            description="Get yield trend over time (daily breakdown)",
            inputSchema={
                "type": "object",
                "properties": {
                    "part_number": {"type": "string", "description": "Filter by part number"},
                    "days": {"type": "integer", "description": "Trend over last N days", "default": 30}
                }
            }
        ),
        
        # ----- Assets -----
        Tool(
            name="wats_get_assets",
            description="Get equipment/assets from WATS",
            inputSchema={
                "type": "object",
                "properties": {
                    "asset_type": {"type": "string", "description": "Filter by asset type"},
                    "limit": {"type": "integer", "description": "Max assets to return", "default": 50}
                }
            }
        ),
        Tool(
            name="wats_get_asset",
            description="Get detailed information about a specific asset",
            inputSchema={
                "type": "object",
                "properties": {
                    "identifier": {"type": "string", "description": "Asset ID or serial number"}
                },
                "required": ["identifier"]
            }
        ),
        Tool(
            name="wats_get_calibration_due",
            description="Get assets with calibration due within specified days",
            inputSchema={
                "type": "object",
                "properties": {
                    "days": {"type": "integer", "description": "Calibration due within N days", "default": 30}
                }
            }
        ),
        Tool(
            name="wats_get_asset_types",
            description="Get all asset types defined in WATS",
            inputSchema={"type": "object", "properties": {}}
        ),
        
        # ----- Production / Units -----
        Tool(
            name="wats_get_unit",
            description="Get production unit information by serial and part number",
            inputSchema={
                "type": "object",
                "properties": {
                    "serial_number": {"type": "string", "description": "Unit serial number"},
                    "part_number": {"type": "string", "description": "Product part number"}
                },
                "required": ["serial_number", "part_number"]
            }
        ),
        Tool(
            name="wats_get_unit_history",
            description="Get test and production history for a unit",
            inputSchema={
                "type": "object",
                "properties": {
                    "serial_number": {"type": "string", "description": "Unit serial number"},
                    "part_number": {"type": "string", "description": "Product part number"}
                },
                "required": ["serial_number", "part_number"]
            }
        ),
        
        # ----- RootCause / Tickets -----
        Tool(
            name="wats_get_tickets",
            description="Get RootCause tickets (issue tracking)",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": ["open", "closed", "all"], "default": "open"},
                    "limit": {"type": "integer", "description": "Max tickets to return", "default": 50}
                }
            }
        ),
        Tool(
            name="wats_get_ticket",
            description="Get detailed information about a specific ticket",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticket_id": {"type": "string", "description": "The ticket ID"}
                },
                "required": ["ticket_id"]
            }
        ),
        Tool(
            name="wats_create_ticket",
            description="Create a new RootCause ticket for issue tracking",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Ticket title/subject"},
                    "description": {"type": "string", "description": "Ticket description"},
                    "priority": {"type": "string", "enum": ["low", "medium", "high", "critical"], "default": "medium"},
                    "part_number": {"type": "string", "description": "Related part number"},
                    "serial_number": {"type": "string", "description": "Related serial number"}
                },
                "required": ["title", "description"]
            }
        ),
        
        # ----- Software Distribution -----
        Tool(
            name="wats_get_software_packages",
            description="Get software packages available for distribution",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Max packages to return", "default": 50}
                }
            }
        ),
        Tool(
            name="wats_get_software_package",
            description="Get details of a specific software package",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Package name"},
                    "version": {"type": "string", "description": "Specific version (optional)"}
                },
                "required": ["name"]
            }
        ),
    ]


# =============================================================================
# Tool Call Handler
# =============================================================================

@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Execute a WATS tool."""
    try:
        api = get_api()
        
        # Route to appropriate handler
        handlers = {
            # Connection & System
            "wats_test_connection": _tool_test_connection,
            "wats_get_version": _tool_get_version,
            "wats_get_processes": _tool_get_processes,
            # Products
            "wats_get_products": _tool_get_products,
            "wats_get_product": _tool_get_product,
            "wats_get_product_revisions": _tool_get_product_revisions,
            # Reports
            "wats_query_reports": _tool_query_reports,
            "wats_get_report": _tool_get_report,
            "wats_get_report_steps": _tool_get_report_steps,
            "wats_get_failures": _tool_get_failures,
            "wats_search_serial": _tool_search_serial,
            # Statistics & Yield
            "wats_get_yield": _tool_get_yield,
            "wats_get_yield_by_station": _tool_get_yield_by_station,
            "wats_get_yield_trend": _tool_get_yield_trend,
            # Assets
            "wats_get_assets": _tool_get_assets,
            "wats_get_asset": _tool_get_asset,
            "wats_get_calibration_due": _tool_get_calibration_due,
            "wats_get_asset_types": _tool_get_asset_types,
            # Production / Units
            "wats_get_unit": _tool_get_unit,
            "wats_get_unit_history": _tool_get_unit_history,
            # RootCause / Tickets
            "wats_get_tickets": _tool_get_tickets,
            "wats_get_ticket": _tool_get_ticket,
            "wats_create_ticket": _tool_create_ticket,
            # Software
            "wats_get_software_packages": _tool_get_software_packages,
            "wats_get_software_package": _tool_get_software_package,
        }
        
        handler = handlers.get(name)
        if handler:
            return await handler(api, arguments)
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
            
    except Exception as e:
        logger.exception(f"Error executing tool {name}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


# =============================================================================
# Tool Implementations - Connection & System
# =============================================================================

async def _tool_test_connection(api: pyWATS, args: dict) -> list[TextContent]:
    """Test WATS connection."""
    if api.test_connection():
        version = api.get_version()
        return [TextContent(
            type="text",
            text=f"✅ Connected to WATS server\nServer version: {version}\nBase URL: {api.base_url}"
        )]
    return [TextContent(type="text", text="❌ Connection failed")]


async def _tool_get_version(api: pyWATS, args: dict) -> list[TextContent]:
    """Get WATS version."""
    version = api.get_version()
    return [TextContent(type="text", text=f"WATS Server Version: {version}")]


async def _tool_get_processes(api: pyWATS, args: dict) -> list[TextContent]:
    """Get test processes."""
    processes = api.analytics.get_processes()
    if not processes:
        return [TextContent(type="text", text="No processes defined")]
    
    lines = [f"Test Processes ({len(processes)}):\n"]
    for p in processes:
        code = getattr(p, 'code', getattr(p, 'process_code', 'N/A'))
        name = getattr(p, 'name', 'Unknown')
        lines.append(f"• [{code}] {name}")
    
    return [TextContent(type="text", text="\n".join(lines))]


# =============================================================================
# Tool Implementations - Products
# =============================================================================

async def _tool_get_products(api: pyWATS, args: dict) -> list[TextContent]:
    """Get products list."""
    limit = args.get("limit", 50)
    products = api.product.get_products()
    
    if not products:
        return [TextContent(type="text", text="No products found")]
    
    lines = [f"Products ({len(products)} total, showing {min(len(products), limit)}):\n"]
    for p in products[:limit]:
        pn = getattr(p, 'part_number', 'N/A')
        name = getattr(p, 'name', 'Unknown')
        state = getattr(p, 'state', 'Unknown')
        lines.append(f"• {pn} - {name} [{state}]")
    
    return [TextContent(type="text", text="\n".join(lines))]


async def _tool_get_product(api: pyWATS, args: dict) -> list[TextContent]:
    """Get product details."""
    pn = args.get("part_number")
    if not pn:
        return [TextContent(type="text", text="Error: part_number required")]
    
    product = api.product.get_product(pn)
    if not product:
        return [TextContent(type="text", text=f"Product not found: {pn}")]
    
    lines = [
        f"Product: {pn}",
        "=" * 40,
        f"Name: {getattr(product, 'name', 'N/A')}",
        f"State: {getattr(product, 'state', 'N/A')}",
        f"Non-Serial: {getattr(product, 'non_serial', False)}",
        f"Description: {getattr(product, 'description', 'N/A')}",
    ]
    
    return [TextContent(type="text", text="\n".join(lines))]


async def _tool_get_product_revisions(api: pyWATS, args: dict) -> list[TextContent]:
    """Get product revisions."""
    pn = args.get("part_number")
    if not pn:
        return [TextContent(type="text", text="Error: part_number required")]
    
    revisions = api.product.get_revisions(pn)
    if not revisions:
        return [TextContent(type="text", text=f"No revisions found for: {pn}")]
    
    lines = [f"Revisions for {pn}:\n"]
    for r in revisions:
        rev = getattr(r, 'revision', getattr(r, 'rev', 'N/A'))
        state = getattr(r, 'state', 'Unknown')
        lines.append(f"• Rev {rev} [{state}]")
    
    return [TextContent(type="text", text="\n".join(lines))]


# =============================================================================
# Tool Implementations - Reports
# =============================================================================

async def _tool_query_reports(api: pyWATS, args: dict) -> list[TextContent]:
    """Query test reports."""
    days = args.get("days", 7)
    limit = args.get("limit", 100)
    pn = args.get("part_number")
    sn = args.get("serial_number")
    status = args.get("status", "all")
    station = args.get("station")
    operator = args.get("operator")
    
    from pywats import WATSFilter
    
    filter_obj = WATSFilter(
        start=(datetime.utcnow() - timedelta(days=days)).isoformat() + "Z",
        part_number=pn,
        serial_number=sn,
        station_name=station,
        operator=operator
    )
    
    reports = api.report.query_uut_headers(filter_obj, top=limit)
    
    if not reports:
        return [TextContent(type="text", text=f"No reports found (last {days} days)")]
    
    # Filter by status
    if status == "passed":
        reports = [r for r in reports if getattr(r, 'status', '') == 'P']
    elif status == "failed":
        reports = [r for r in reports if getattr(r, 'status', '') == 'F']
    
    lines = [f"Reports ({len(reports)}, last {days} days):\n"]
    for r in reports[:limit]:
        rid = getattr(r, 'id', 'N/A')
        rsn = getattr(r, 'serial_number', getattr(r, 'sn', 'N/A'))
        rpn = getattr(r, 'part_number', getattr(r, 'pn', 'N/A'))
        rst = getattr(r, 'status', 'U')
        rstart = getattr(r, 'start', 'N/A')
        rstation = getattr(r, 'station_name', 'N/A')
        
        icon = "✅" if rst == 'P' else "❌" if rst == 'F' else "⚪"
        lines.append(f"{icon} {rsn} | {rpn} | {rstation} | {rstart} | {rid}")
    
    return [TextContent(type="text", text="\n".join(lines))]


async def _tool_get_report(api: pyWATS, args: dict) -> list[TextContent]:
    """Get report details."""
    report_id = args.get("report_id")
    if not report_id:
        return [TextContent(type="text", text="Error: report_id required")]
    
    report = api.report.get_report(report_id)
    if not report:
        return [TextContent(type="text", text=f"Report not found: {report_id}")]
    
    lines = [
        f"Report: {report_id}",
        "=" * 50,
        f"Serial: {getattr(report, 'sn', 'N/A')}",
        f"Part Number: {getattr(report, 'pn', 'N/A')}",
        f"Revision: {getattr(report, 'rev', 'N/A')}",
        f"Status: {'PASSED' if getattr(report, 'status', '') == 'P' else 'FAILED'}",
        f"Start: {getattr(report, 'start', 'N/A')}",
        f"Station: {getattr(report, 'station_name', 'N/A')}",
        f"Operator: {getattr(report, 'info', {}).get('operator', 'N/A') if isinstance(getattr(report, 'info', None), dict) else getattr(getattr(report, 'info', None), 'operator', 'N/A')}",
        f"Process Code: {getattr(report, 'process_code', 'N/A')}",
    ]
    
    return [TextContent(type="text", text="\n".join(lines))]


async def _tool_get_report_steps(api: pyWATS, args: dict) -> list[TextContent]:
    """Get report step hierarchy."""
    report_id = args.get("report_id")
    failed_only = args.get("failed_only", False)
    
    if not report_id:
        return [TextContent(type="text", text="Error: report_id required")]
    
    report = api.report.get_report(report_id)
    if not report:
        return [TextContent(type="text", text=f"Report not found: {report_id}")]
    
    root = getattr(report, 'root', None)
    steps = getattr(root, 'steps', []) if root else []
    
    if not steps:
        return [TextContent(type="text", text="No steps in report")]
    
    def format_steps(steps_list, indent=0):
        result = []
        for step in steps_list:
            st = getattr(step, 'status', 'U')
            if failed_only and st != 'F':
                continue
            
            name = getattr(step, 'name', 'Unknown')
            step_type = getattr(step, 'step_type', 'Unknown')
            icon = "✅" if st == 'P' else "❌" if st == 'F' else "⚪"
            
            result.append(f"{'  ' * indent}{icon} {name} [{step_type}]")
            
            # Recurse into child steps
            child_steps = getattr(step, 'steps', [])
            if child_steps:
                result.extend(format_steps(child_steps, indent + 1))
        
        return result
    
    lines = [f"Steps for report {report_id}:", "-" * 40]
    lines.extend(format_steps(steps))
    
    return [TextContent(type="text", text="\n".join(lines))]


async def _tool_get_failures(api: pyWATS, args: dict) -> list[TextContent]:
    """Get recent failures."""
    days = args.get("days", 1)
    limit = args.get("limit", 50)
    pn = args.get("part_number")
    station = args.get("station")
    
    from pywats import WATSFilter
    
    filter_obj = WATSFilter(
        start=(datetime.utcnow() - timedelta(days=days)).isoformat() + "Z",
        part_number=pn,
        station_name=station,
        status="F"
    )
    
    reports = api.report.query_uut_headers(filter_obj, top=limit)
    
    if not reports:
        return [TextContent(type="text", text=f"✅ No failures in the last {days} day(s)!")]
    
    lines = [f"❌ Failures ({len(reports)}, last {days} day(s)):\n"]
    for r in reports[:limit]:
        rsn = getattr(r, 'serial_number', getattr(r, 'sn', 'N/A'))
        rpn = getattr(r, 'part_number', getattr(r, 'pn', 'N/A'))
        rstation = getattr(r, 'station_name', 'N/A')
        rstart = getattr(r, 'start', 'N/A')
        rid = getattr(r, 'id', 'N/A')
        
        lines.append(f"• SN: {rsn} | PN: {rpn} | Station: {rstation} | {rstart}")
    
    return [TextContent(type="text", text="\n".join(lines))]


async def _tool_search_serial(api: pyWATS, args: dict) -> list[TextContent]:
    """Search test history by serial."""
    sn = args.get("serial_number")
    if not sn:
        return [TextContent(type="text", text="Error: serial_number required")]
    
    from pywats import WATSFilter
    filter_obj = WATSFilter(serial_number=sn)
    reports = api.report.query_uut_headers(filter_obj, top=100)
    
    if not reports:
        return [TextContent(type="text", text=f"No test history for: {sn}")]
    
    lines = [f"Test history for {sn} ({len(reports)} tests):\n"]
    for r in reports:
        rst = getattr(r, 'status', 'U')
        rpn = getattr(r, 'part_number', getattr(r, 'pn', 'N/A'))
        rstation = getattr(r, 'station_name', 'N/A')
        rstart = getattr(r, 'start', 'N/A')
        
        icon = "✅" if rst == 'P' else "❌" if rst == 'F' else "⚪"
        lines.append(f"{icon} {rstart} | PN: {rpn} | Station: {rstation}")
    
    return [TextContent(type="text", text="\n".join(lines))]


# =============================================================================
# Tool Implementations - Statistics & Yield
# =============================================================================

async def _tool_get_yield(api: pyWATS, args: dict) -> list[TextContent]:
    """Calculate yield statistics."""
    days = args.get("days", 7)
    pn = args.get("part_number")
    station = args.get("station")
    
    from pywats import WATSFilter
    filter_obj = WATSFilter(
        start=(datetime.utcnow() - timedelta(days=days)).isoformat() + "Z",
        part_number=pn,
        station_name=station
    )
    
    reports = api.report.query_uut_headers(filter_obj, top=10000)
    
    if not reports:
        return [TextContent(type="text", text="No data for yield calculation")]
    
    total = len(reports)
    passed = sum(1 for r in reports if getattr(r, 'status', '') == 'P')
    failed = total - passed
    yield_pct = (passed / total * 100) if total > 0 else 0
    
    context = []
    if pn: context.append(f"PN: {pn}")
    if station: context.append(f"Station: {station}")
    context_str = " | ".join(context) if context else "All"
    
    lines = [
        f"📊 Yield Statistics ({context_str})",
        f"Period: Last {days} days",
        "=" * 40,
        f"Total Tests: {total}",
        f"Passed: {passed} ✅",
        f"Failed: {failed} ❌",
        f"Yield: {yield_pct:.2f}%",
    ]
    
    return [TextContent(type="text", text="\n".join(lines))]


async def _tool_get_yield_by_station(api: pyWATS, args: dict) -> list[TextContent]:
    """Compare yield by station."""
    days = args.get("days", 7)
    pn = args.get("part_number")
    
    from pywats import WATSFilter
    filter_obj = WATSFilter(
        start=(datetime.utcnow() - timedelta(days=days)).isoformat() + "Z",
        part_number=pn
    )
    
    reports = api.report.query_uut_headers(filter_obj, top=10000)
    
    if not reports:
        return [TextContent(type="text", text="No data for station comparison")]
    
    # Group by station
    stations: dict = {}
    for r in reports:
        station = getattr(r, 'station_name', 'Unknown')
        if station not in stations:
            stations[station] = {'total': 0, 'passed': 0}
        stations[station]['total'] += 1
        if getattr(r, 'status', '') == 'P':
            stations[station]['passed'] += 1
    
    lines = [f"📊 Yield by Station (last {days} days):", "=" * 50]
    
    # Sort by yield descending
    sorted_stations = sorted(
        stations.items(),
        key=lambda x: (x[1]['passed'] / x[1]['total'] * 100) if x[1]['total'] > 0 else 0,
        reverse=True
    )
    
    for station, data in sorted_stations:
        yield_pct = (data['passed'] / data['total'] * 100) if data['total'] > 0 else 0
        lines.append(f"• {station}: {yield_pct:.1f}% ({data['passed']}/{data['total']})")
    
    return [TextContent(type="text", text="\n".join(lines))]


async def _tool_get_yield_trend(api: pyWATS, args: dict) -> list[TextContent]:
    """Get yield trend over time."""
    days = args.get("days", 30)
    pn = args.get("part_number")
    
    from pywats import WATSFilter
    filter_obj = WATSFilter(
        start=(datetime.utcnow() - timedelta(days=days)).isoformat() + "Z",
        part_number=pn
    )
    
    reports = api.report.query_uut_headers(filter_obj, top=10000)
    
    if not reports:
        return [TextContent(type="text", text="No data for trend analysis")]
    
    # Group by date
    by_date: dict = {}
    for r in reports:
        start = getattr(r, 'start', None)
        if start:
            if isinstance(start, str):
                date_str = start[:10]
            else:
                date_str = start.strftime('%Y-%m-%d')
            
            if date_str not in by_date:
                by_date[date_str] = {'total': 0, 'passed': 0}
            by_date[date_str]['total'] += 1
            if getattr(r, 'status', '') == 'P':
                by_date[date_str]['passed'] += 1
    
    lines = [f"📈 Yield Trend (last {days} days):", "=" * 50]
    
    for date_str in sorted(by_date.keys())[-14:]:  # Last 14 days
        data = by_date[date_str]
        yield_pct = (data['passed'] / data['total'] * 100) if data['total'] > 0 else 0
        bar = "█" * int(yield_pct / 5)
        lines.append(f"{date_str}: {bar} {yield_pct:.1f}% (n={data['total']})")
    
    return [TextContent(type="text", text="\n".join(lines))]


# =============================================================================
# Tool Implementations - Assets
# =============================================================================

async def _tool_get_assets(api: pyWATS, args: dict) -> list[TextContent]:
    """Get assets list."""
    limit = args.get("limit", 50)
    asset_type = args.get("asset_type")
    
    assets = api.asset.get_assets(top=limit)
    
    if not assets:
        return [TextContent(type="text", text="No assets found")]
    
    if asset_type:
        assets = [a for a in assets if asset_type.lower() in str(getattr(a, 'type', '')).lower()]
    
    lines = [f"Assets ({len(assets)}):\n"]
    for a in assets[:limit]:
        name = getattr(a, 'name', 'Unknown')
        atype = getattr(a, 'type', 'N/A')
        serial = getattr(a, 'serial_number', 'N/A')
        state = getattr(a, 'state', 'Unknown')
        
        lines.append(f"• {name} ({atype}) | SN: {serial} | State: {state}")
    
    return [TextContent(type="text", text="\n".join(lines))]


async def _tool_get_asset(api: pyWATS, args: dict) -> list[TextContent]:
    """Get asset details."""
    identifier = args.get("identifier")
    if not identifier:
        return [TextContent(type="text", text="Error: identifier required")]
    
    asset = api.asset.get_asset(identifier)
    if not asset:
        return [TextContent(type="text", text=f"Asset not found: {identifier}")]
    
    lines = [
        f"Asset: {getattr(asset, 'name', 'Unknown')}",
        "=" * 40,
        f"Serial Number: {getattr(asset, 'serial_number', 'N/A')}",
        f"Type: {getattr(asset, 'type', 'N/A')}",
        f"State: {getattr(asset, 'state', 'N/A')}",
        f"Location: {getattr(asset, 'location', 'N/A')}",
        f"Calibration Due: {getattr(asset, 'calibration_due_date', 'N/A')}",
        f"Description: {getattr(asset, 'description', 'N/A')}",
    ]
    
    return [TextContent(type="text", text="\n".join(lines))]


async def _tool_get_calibration_due(api: pyWATS, args: dict) -> list[TextContent]:
    """Get assets with calibration due."""
    days = args.get("days", 30)
    
    assets = api.asset.get_assets(top=500)
    
    if not assets:
        return [TextContent(type="text", text="No assets found")]
    
    now = datetime.utcnow()
    due_date = now + timedelta(days=days)
    
    due_assets = []
    for a in assets:
        cal_date = getattr(a, 'calibration_due_date', None)
        if cal_date:
            try:
                if isinstance(cal_date, str):
                    cal_dt = datetime.fromisoformat(cal_date.replace('Z', '+00:00')).replace(tzinfo=None)
                else:
                    cal_dt = cal_date.replace(tzinfo=None) if hasattr(cal_date, 'replace') else cal_date
                
                if cal_dt <= due_date:
                    due_assets.append((a, cal_dt))
            except Exception:
                pass
    
    if not due_assets:
        return [TextContent(type="text", text=f"✅ No calibrations due within {days} days")]
    
    # Sort by due date
    due_assets.sort(key=lambda x: x[1])
    
    lines = [f"⚠️ Calibration Due ({len(due_assets)} assets within {days} days):\n"]
    for a, cal_dt in due_assets:
        name = getattr(a, 'name', 'Unknown')
        serial = getattr(a, 'serial_number', 'N/A')
        days_left = (cal_dt - now).days
        
        icon = "🔴" if days_left < 0 else "🟡" if days_left < 7 else "🟢"
        lines.append(f"{icon} {name} (SN: {serial}) - Due: {cal_dt.strftime('%Y-%m-%d')} ({days_left} days)")
    
    return [TextContent(type="text", text="\n".join(lines))]


async def _tool_get_asset_types(api: pyWATS, args: dict) -> list[TextContent]:
    """Get asset types."""
    types = api.asset.get_asset_types()
    
    if not types:
        return [TextContent(type="text", text="No asset types defined")]
    
    lines = [f"Asset Types ({len(types)}):\n"]
    for t in types:
        name = getattr(t, 'name', 'Unknown')
        desc = getattr(t, 'description', '')
        lines.append(f"• {name}" + (f" - {desc}" if desc else ""))
    
    return [TextContent(type="text", text="\n".join(lines))]


# =============================================================================
# Tool Implementations - Production / Units
# =============================================================================

async def _tool_get_unit(api: pyWATS, args: dict) -> list[TextContent]:
    """Get production unit."""
    sn = args.get("serial_number")
    pn = args.get("part_number")
    
    if not sn or not pn:
        return [TextContent(type="text", text="Error: serial_number and part_number required")]
    
    unit = api.production.get_unit(sn, pn)
    if not unit:
        return [TextContent(type="text", text=f"Unit not found: {sn} / {pn}")]
    
    lines = [
        f"Unit: {sn}",
        "=" * 40,
        f"Part Number: {getattr(unit, 'part_number', 'N/A')}",
        f"Phase: {getattr(unit, 'phase', 'N/A')}",
        f"Created: {getattr(unit, 'created', 'N/A')}",
        f"Batch: {getattr(unit, 'batch_number', 'N/A')}",
    ]
    
    return [TextContent(type="text", text="\n".join(lines))]


async def _tool_get_unit_history(api: pyWATS, args: dict) -> list[TextContent]:
    """Get unit history."""
    sn = args.get("serial_number")
    pn = args.get("part_number")
    
    if not sn or not pn:
        return [TextContent(type="text", text="Error: serial_number and part_number required")]
    
    # Get unit info
    unit = api.production.get_unit(sn, pn)
    
    # Get test history
    from pywats import WATSFilter
    filter_obj = WATSFilter(serial_number=sn, part_number=pn)
    reports = api.report.query_uut_headers(filter_obj, top=100)
    
    lines = [f"History for {sn} (PN: {pn})", "=" * 50]
    
    if unit:
        lines.append(f"Current Phase: {getattr(unit, 'phase', 'N/A')}")
        lines.append(f"Created: {getattr(unit, 'created', 'N/A')}")
        lines.append("")
    
    lines.append(f"Test History ({len(reports) if reports else 0} tests):")
    if reports:
        for r in reports:
            rst = getattr(r, 'status', 'U')
            rstation = getattr(r, 'station_name', 'N/A')
            rstart = getattr(r, 'start', 'N/A')
            process = getattr(r, 'process_code', 'N/A')
            
            icon = "✅" if rst == 'P' else "❌" if rst == 'F' else "⚪"
            lines.append(f"  {icon} {rstart} | Process: {process} | Station: {rstation}")
    else:
        lines.append("  No test records")
    
    return [TextContent(type="text", text="\n".join(lines))]


# =============================================================================
# Tool Implementations - RootCause / Tickets
# =============================================================================

async def _tool_get_tickets(api: pyWATS, args: dict) -> list[TextContent]:
    """Get RootCause tickets."""
    status = args.get("status", "open")
    limit = args.get("limit", 50)
    
    if status == "open":
        tickets = api.rootcause.get_open_tickets(limit=limit)
    elif status == "closed":
        tickets = api.rootcause.get_tickets(limit=limit)
        tickets = [t for t in tickets if str(getattr(t, 'status', '')).lower() == 'closed']
    else:
        tickets = api.rootcause.get_tickets(limit=limit)
    
    if not tickets:
        return [TextContent(type="text", text=f"No tickets found ({status})")]
    
    lines = [f"Tickets ({len(tickets)}, {status}):\n"]
    for t in tickets[:limit]:
        tid = getattr(t, 'id', 'N/A')
        title = getattr(t, 'title', getattr(t, 'subject', 'No title'))
        tstatus = getattr(t, 'status', 'Unknown')
        priority = getattr(t, 'priority', 'N/A')
        created = getattr(t, 'created', getattr(t, 'created_date', 'N/A'))
        
        lines.append(f"• [{tstatus}] {title}")
        lines.append(f"  ID: {tid} | Priority: {priority} | Created: {created}")
    
    return [TextContent(type="text", text="\n".join(lines))]


async def _tool_get_ticket(api: pyWATS, args: dict) -> list[TextContent]:
    """Get ticket details."""
    ticket_id = args.get("ticket_id")
    if not ticket_id:
        return [TextContent(type="text", text="Error: ticket_id required")]
    
    ticket = api.rootcause.get_ticket(ticket_id)
    if not ticket:
        return [TextContent(type="text", text=f"Ticket not found: {ticket_id}")]
    
    lines = [
        f"Ticket: {getattr(ticket, 'title', 'No title')}",
        "=" * 50,
        f"ID: {ticket_id}",
        f"Status: {getattr(ticket, 'status', 'N/A')}",
        f"Priority: {getattr(ticket, 'priority', 'N/A')}",
        f"Created: {getattr(ticket, 'created', 'N/A')}",
        f"Assigned To: {getattr(ticket, 'assigned_to', 'N/A')}",
        "",
        "Description:",
        getattr(ticket, 'description', 'No description'),
    ]
    
    return [TextContent(type="text", text="\n".join(lines))]


async def _tool_create_ticket(api: pyWATS, args: dict) -> list[TextContent]:
    """Create a new ticket."""
    title = args.get("title")
    description = args.get("description")
    priority = args.get("priority", "medium")
    pn = args.get("part_number")
    sn = args.get("serial_number")
    
    if not title or not description:
        return [TextContent(type="text", text="Error: title and description required")]
    
    # Map priority string to enum value
    priority_map = {"low": 1, "medium": 2, "high": 3, "critical": 4}
    priority_val = priority_map.get(priority.lower(), 2)
    
    try:
        ticket = api.rootcause.create_ticket(
            title=title,
            description=description,
            priority=priority_val,
            part_number=pn,
            serial_number=sn
        )
        
        if ticket:
            return [TextContent(
                type="text",
                text=f"✅ Ticket created successfully!\nID: {getattr(ticket, 'id', 'N/A')}\nTitle: {title}"
            )]
        else:
            return [TextContent(type="text", text="❌ Failed to create ticket")]
    except Exception as e:
        return [TextContent(type="text", text=f"❌ Error creating ticket: {str(e)}")]


# =============================================================================
# Tool Implementations - Software
# =============================================================================

async def _tool_get_software_packages(api: pyWATS, args: dict) -> list[TextContent]:
    """Get software packages."""
    limit = args.get("limit", 50)
    
    packages = api.software.get_packages()
    
    if not packages:
        return [TextContent(type="text", text="No software packages found")]
    
    lines = [f"Software Packages ({len(packages)}):\n"]
    for p in packages[:limit]:
        name = getattr(p, 'name', 'Unknown')
        version = getattr(p, 'version', 'N/A')
        status = getattr(p, 'status', 'N/A')
        
        lines.append(f"• {name} v{version} [{status}]")
    
    return [TextContent(type="text", text="\n".join(lines))]


async def _tool_get_software_package(api: pyWATS, args: dict) -> list[TextContent]:
    """Get software package details."""
    name = args.get("name")
    version = args.get("version")
    
    if not name:
        return [TextContent(type="text", text="Error: name required")]
    
    if version:
        package = api.software.get_package_by_name(name, version)
    else:
        package = api.software.get_released_package(name)
    
    if not package:
        return [TextContent(type="text", text=f"Package not found: {name}" + (f" v{version}" if version else ""))]
    
    lines = [
        f"Package: {getattr(package, 'name', 'Unknown')}",
        "=" * 40,
        f"Version: {getattr(package, 'version', 'N/A')}",
        f"Status: {getattr(package, 'status', 'N/A')}",
        f"Created: {getattr(package, 'created', 'N/A')}",
        f"Description: {getattr(package, 'description', 'N/A')}",
    ]
    
    return [TextContent(type="text", text="\n".join(lines))]


# =============================================================================
# Main Entry Point
# =============================================================================

async def main():
    """Run the WATS MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
