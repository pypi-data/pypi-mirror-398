"""
Debug tool for testing server connectivity and basic yield queries.

This tool provides simple commands for verifying that the WATS server is responding
and that the dynamic yield endpoint is working correctly.
"""

from __future__ import annotations

from typing import Any, Dict

from pywats_agent.result import AgentResult

from ._base import AgentTool, ToolInput


class DebugTool(AgentTool):
    """Debug tool for server connectivity and quick yield checks.

    PRIMARY DEBUG TOOL for verifying WATS server connectivity and testing
    the dynamic yield endpoint with a standard query.

    This tool makes a real API call to get_dynamic_yield with a fixed query:
    - Top 10 products by unit count
    - Last 30 days
    - Grouped by part_number only
    """

    name = "debug_server"
    description = (
        "DEBUG TOOL: Check server connectivity and test dynamic yield endpoint. "
        "Returns top 10 products by volume from the last 30 days. "
        "Use for: 'check server', 'test connection', 'show top runners', 'smoke test'."
    )
    input_model = ToolInput  # No parameters needed

    def _execute(self, input: ToolInput) -> AgentResult:
        from pywats.domains.report import WATSFilter, DateGrouping

        print("\n" + "=" * 60)
        print("DEBUG: Testing server connection and dynamic yield")
        print("=" * 60)

        try:
            version = self._api.analytics.get_version()
            print(f"✓ Server responding - Version: {version}")
        except Exception as e:
            error_msg = f"✗ Server connection failed: {str(e)}"
            print(error_msg)
            print("=" * 60 + "\n")
            return AgentResult.fail(error_msg)

        try:
            filter_obj = WATSFilter(
                top_count=10,
                period_count=30,
                date_grouping=DateGrouping.DAY,
                dimensions="partNumber",
            )

            print(f"\nFilter: {filter_obj.model_dump(by_alias=True, exclude_none=True)}")
            print("Calling api.analytics.get_dynamic_yield...")

            result = self._api.analytics.get_dynamic_yield(filter_obj)

            print("✓ Dynamic yield query successful")
            print(f"  Rows returned: {len(result) if result else 0}")

            if result and len(result) > 0:
                print("\n  Top 3 runners:")
                for idx, row in enumerate(result[:3], 1):
                    print(f"    {idx}. {row}")

            print("=" * 60 + "\n")

            summary_lines = [
                "✓ Server is responding",
                "✓ Dynamic yield endpoint working",
                f"✓ Found {len(result)} products in last 30 days",
            ]

            if result and len(result) > 0:
                summary_lines.append("\nTop 10 runners (by unit count):")
                for idx, row in enumerate(result[:10], 1):
                    part = getattr(row, "part_number", "N/A")
                    units = getattr(row, "unit_count", 0)
                    fpy = getattr(row, "fpy", 0)
                    summary_lines.append(f"{idx}. {part}: {units} units, FPY={fpy:.1f}%")

            return AgentResult.ok(
                summary="\n".join(summary_lines),
                data=result,
                metadata={
                    "row_count": len(result) if result else 0,
                    "server_version": version,
                },
            )

        except Exception as e:
            error_msg = f"✗ Dynamic yield query failed: {str(e)}"
            print(error_msg)
            print("=" * 60 + "\n")
            return AgentResult.fail(error_msg)


def get_debug_tool_definition() -> Dict[str, Any]:
    """Get tool definition for LLM function calling."""

    return {
        "type": "function",
        "function": {
            "name": "debug_server",
            "description": (
                "DEBUG TOOL: Check WATS server connectivity and test dynamic yield endpoint. "
                "Returns top 10 products by volume from last 30 days. "
                "Use for: 'check server', 'test connection', 'show top runners', 'smoke test'."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    }


__all__ = [
    "DebugTool",
    "get_debug_tool_definition",
]
