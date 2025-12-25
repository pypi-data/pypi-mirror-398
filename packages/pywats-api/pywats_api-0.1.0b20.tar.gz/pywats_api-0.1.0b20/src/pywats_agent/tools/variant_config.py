"""
User-defined agent variants configuration.

This file is where you define your experimental variants.
Edit this file to create new tool configurations without
touching the main agent codebase.

QUICK START:
1. Copy one of the example variants below
2. Modify to fit your experiment
3. Use it: create_agent_tools(api, variant="my_variant_name")

The variants defined here are automatically loaded when the
variants module is imported.
"""

from pywats_agent.tools.variants import (
    ExperimentalVariant,
    register_variant,
)


# ============================================================================
# Example Variants - Copy and modify these
# ============================================================================

# Example 1: Focused investigation variant
# ----------------------------------------
# Starts with investigation profile but adds trend analysis
_investigation_trends = ExperimentalVariant(
    name="investigation_trends",
    description="Investigation with yield trend support",
    base_profile="investigation",
    include_tools=["analyze_yield_trend"],
)

# Example 2: Minimal + specific tools
# -----------------------------------
# Starts minimal and adds only what you need
_focused_yield = ExperimentalVariant(
    name="focused_yield",
    description="Yield analysis with trends only (no deviation/discovery)",
    base_profile="minimal",
    include_tools=["analyze_yield_trend"],
)

# Example 3: Full minus specific tools
# ------------------------------------
# Start with everything, remove what you don't want
_no_measurement = ExperimentalVariant(
    name="no_measurement",
    description="Full profile without measurement tools",
    base_profile="full",
    exclude_tools=["get_measurement_data", "get_aggregated_measurements"],
)

# Example 4: A/B testing with different prompts
# ---------------------------------------------
# Override a tool's description to test different prompts
_alternative_root_cause = ExperimentalVariant(
    name="root_cause_alt_prompt",
    description="Testing alternative root cause prompt wording",
    base_profile="investigation",
    tool_overrides={
        "analyze_root_cause": {
            "description": (
                "Investigate why manufacturing yield is lower than expected. "
                "This tool performs a systematic 9-step root cause analysis: "
                "1) Assess overall yield, 2) Split by dimensions, 3) Analyze trends, "
                "4) Prioritize suspects, 5-9) Deep dive into failing steps. "
                "Use this when the user asks about quality problems, failure patterns, "
                "or wants to understand what's causing defects."
            )
        }
    },
)


# ============================================================================
# Register Your Variants Here
# ============================================================================
# Uncomment the variants you want to make available

register_variant(_investigation_trends)
register_variant(_focused_yield)
register_variant(_no_measurement)
register_variant(_alternative_root_cause)


# ============================================================================
# Add Your Custom Variants Below
# ============================================================================

# TSA - Experimental "start_tsa" approach
# ------------------------------------------
# New TSA design philosophy:
# - "Evidence curator" not "storyteller"
# - Enforce required context (no guessing)
# - Preprocess + rank in tool layer
# - Return top-K candidates, not full grids
# - Session caching for drill-down
_tsa = ExperimentalVariant(
    name="tsa",
    description=(
        "Experimental TSA with preprocessing, ranking, and session caching. "
        "Uses start_tsa instead of analyze_test_steps."
    ),
    base_profile="investigation",
    exclude_tools=["analyze_test_steps"],  # Replace with new approach
    include_tools=["start_tsa"],  # Add new tool
    tool_overrides={
        "start_tsa": {
            "description": (
                "Start a Test Step Analysis (TSA) session for root cause investigation. "
                "REQUIRES explicit part_number AND test_operation - do not guess these. "
                "Returns pre-ranked candidate lists by concern type: "
                "RELIABILITY (fallout), IMPACT (root cause), CAPABILITY (Cpk), "
                "INFRASTRUCTURE (errors), TIME (anomalies). "
                "Use after yield analysis identifies a problematic part+process."
            )
        }
    },
)
register_variant(_tsa)
