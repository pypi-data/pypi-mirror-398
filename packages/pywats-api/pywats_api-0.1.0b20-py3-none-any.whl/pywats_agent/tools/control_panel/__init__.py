"""
Control Panel Manager tools for WATS agent.

Provides comprehensive management tools for WATS configuration:
- Asset management (types, instances, calibration, maintenance)
- Product management (products, revisions, BOM, box build templates)
- Production management (units, phases, assembly)
- Software management (packages, releases, files)
- Process configuration (test/repair/WIP operations)
"""

from .control_panel_tool import (
    ControlPanelTool,
    ControlPanelInput,
    ControlPanelResult,
    ManagementDomain,
    OperationType,
    DOMAIN_ENTITIES,
    get_definition,
)

__all__ = [
    "ControlPanelTool",
    "ControlPanelInput",
    "ControlPanelResult",
    "ManagementDomain",
    "OperationType",
    "DOMAIN_ENTITIES",
    "get_definition",
]
