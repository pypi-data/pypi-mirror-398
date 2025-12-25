"""
Agent variants and tool profiles.

This module provides a way to create multiple "flavors" of the agent layer:
- Different tool sets for different use cases
- Experimental variants that can be tested in isolation
- Production vs development configurations

CORE CONCEPT:
┌─────────────────────────────────────────────────────────────────────────────────┐
│  PROFILE: Named collection of tools                                             │
│  VARIANT: Configuration that may customize tool behavior                        │
│                                                                                 │
│  You can mix profiles (tool sets) and variants (behavior) independently.       │
└─────────────────────────────────────────────────────────────────────────────────┘

BUILT-IN PROFILES:
    - "full": All available tools (default)
    - "yield": Yield-focused tools (trend, deviation, discovery)
    - "investigation": Root cause and dimensional analysis
    - "capability": Process capability and measurement tools
    - "minimal": Just the core yield tool

EXPERIMENTAL VARIANTS:
    Create your own experimental tool configurations without
    touching the main codebase. Each variant can:
    - Include/exclude specific tools
    - Override tool descriptions (for A/B testing prompts)
    - Add custom pre/post processing

Usage:
    >>> from pywats_agent.tools.variants import get_profile, create_agent_tools
    >>> 
    >>> # Get a pre-defined profile
    >>> profile = get_profile("yield")
    >>> tools = profile.create_tools(api)
    >>> 
    >>> # Create tools from profile name directly
    >>> tools = create_agent_tools(api, profile="investigation")
    >>> 
    >>> # Create a custom experimental variant
    >>> from pywats_agent.tools.variants import ToolProfile, ExperimentalVariant
    >>> 
    >>> my_variant = ExperimentalVariant(
    ...     name="test",
    ...     base_profile="yield",
    ...     include_tools=["analyze_root_cause"],  # Add extra tools
    ...     exclude_tools=["yield_discovery"],      # Remove tools
    ... )
    >>> tools = my_variant.create_tools(api)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Type, Any, Callable, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from ._base import AgentTool
    from pywats import pyWATS


# ============================================================================
# Tool Categories and Mappings
# ============================================================================

class ToolCategory(str, Enum):
    """Categories of agent tools."""
    YIELD = "yield"
    ROOT_CAUSE = "root_cause"
    CAPABILITY = "capability"
    MEASUREMENT = "measurement"
    STEP = "step"
    UNIT = "unit"
    ADMIN = "admin"  # Administrative/management tools
    SHARED = "shared"


# Map tool names to categories
TOOL_CATEGORIES: Dict[str, ToolCategory] = {
    # Yield tools
    "analyze_yield": ToolCategory.YIELD,
    "analyze_yield_trend": ToolCategory.YIELD,
    "analyze_yield_deviation": ToolCategory.YIELD,
    "yield_discovery": ToolCategory.YIELD,
    
    # Root cause tools
    "analyze_root_cause": ToolCategory.ROOT_CAUSE,
    "analyze_dimensions": ToolCategory.ROOT_CAUSE,
    
    # Capability tools
    "analyze_process_capability": ToolCategory.CAPABILITY,
    
    # Measurement tools
    "get_measurement_data": ToolCategory.MEASUREMENT,
    "get_aggregated_measurements": ToolCategory.MEASUREMENT,
    
    # Step tools
    "analyze_test_steps": ToolCategory.STEP,
    "analyze_step": ToolCategory.STEP,
    
    # Unit tools
    "analyze_unit": ToolCategory.UNIT,
    "analyze_subunits": ToolCategory.UNIT,
    
    # Admin tools
    "control_panel": ToolCategory.ADMIN,
}


# ============================================================================
# Profile Definitions
# ============================================================================

@dataclass
class ToolProfile:
    """
    A named collection of tools.
    
    Profiles define which tools are available for a given use case.
    This allows creating focused tool sets for specific tasks.
    """
    name: str
    description: str
    tools: Set[str]  # Tool names to include
    
    # Optional customizations
    tool_overrides: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    def get_tools(self) -> Set[str]:
        """Get the set of tool names in this profile."""
        return self.tools.copy()
    
    def create_tools(self, api: "pyWATS") -> Dict[str, "AgentTool"]:
        """
        Create tool instances for this profile.
        
        Args:
            api: pyWATS instance
            
        Returns:
            Dictionary mapping tool names to instances
        """
        from ._registry import create_tool_instance
        
        tools = {}
        for name in self.tools:
            tool = create_tool_instance(name, api)
            if tool:
                tools[name] = tool
        
        return tools
    
    def get_definitions(self) -> List[Dict[str, Any]]:
        """
        Get OpenAI-format tool definitions for this profile.
        
        Returns:
            List of tool definition dictionaries
        """
        from ._registry import get_tool
        
        definitions = []
        for name in self.tools:
            cls = get_tool(name)
            if cls:
                definition = cls.get_definition()
                
                # Apply any overrides
                if name in self.tool_overrides:
                    overrides = self.tool_overrides[name]
                    if "description" in overrides:
                        definition["function"]["description"] = overrides["description"]
                
                definitions.append(definition)
        
        return definitions


# ============================================================================
# Built-in Profiles
# ============================================================================

PROFILES: Dict[str, ToolProfile] = {
    "full": ToolProfile(
        name="full",
        description="All available tools - complete agent capability",
        tools={
            # Yield
            "analyze_yield",
            "analyze_yield_trend",
            "analyze_yield_deviation",
            "yield_discovery",
            # Root cause
            "analyze_root_cause",
            "analyze_dimensions",
            # Capability
            "analyze_process_capability",
            # Measurement
            "get_measurement_data",
            "get_aggregated_measurements",
            # Step
            "analyze_test_steps",
            "analyze_step",
            # Unit
            "analyze_unit",
            "analyze_subunits",
            # Admin
            "control_panel",
        },
    ),
    
    "yield": ToolProfile(
        name="yield",
        description="Yield-focused analysis tools - trends, deviations, discovery",
        tools={
            "analyze_yield",
            "analyze_yield_trend",
            "analyze_yield_deviation",
            "yield_discovery",
        },
    ),
    
    "investigation": ToolProfile(
        name="investigation",
        description="Root cause investigation - dimensional analysis and failure modes",
        tools={
            "analyze_yield",
            "analyze_root_cause",
            "analyze_dimensions",
            "analyze_test_steps",
        },
    ),
    
    "capability": ToolProfile(
        name="capability",
        description="Process capability and measurement analysis",
        tools={
            "analyze_process_capability",
            "get_measurement_data",
            "get_aggregated_measurements",
            "analyze_step",
        },
    ),
    
    "minimal": ToolProfile(
        name="minimal",
        description="Minimal tool set - just core yield analysis",
        tools={
            "analyze_yield",
        },
    ),
    
    "unit": ToolProfile(
        name="unit",
        description="Unit-focused analysis - serial number history, verification, sub-units",
        tools={
            "analyze_unit",
            "analyze_subunits",  # Deep sub-unit analysis for large datasets
            "analyze_yield",  # Useful for context
        },
    ),
    
    "admin": ToolProfile(
        name="admin",
        description="Administrative tools - manage assets, products, production, software",
        tools={
            "control_panel",
            "analyze_unit",  # Useful for viewing unit data
        },
    ),
}


# ============================================================================
# Experimental Variants
# ============================================================================

@dataclass
class ExperimentalVariant:
    """
    An experimental variant of the agent layer.
    
    Variants allow you to test new ideas in isolation without modifying
    the main codebase. Each variant can:
    - Start from a base profile
    - Include additional tools
    - Exclude specific tools
    - Override tool descriptions (for prompt A/B testing)
    - Add custom hooks
    
    Example:
        >>> variant = ExperimentalVariant(
        ...     name="investigation_trends",
        ...     description="Testing new root cause prompt",
        ...     base_profile="investigation",
        ...     include_tools=["analyze_yield_trend"],
        ...     tool_overrides={
        ...         "analyze_root_cause": {
        ...             "description": "New experimental prompt for root cause..."
        ...         }
        ...     }
        ... )
        >>> tools = variant.create_tools(api)
    """
    name: str
    description: str = ""
    
    # Start from a base profile
    base_profile: str = "full"
    
    # Modifications
    include_tools: List[str] = field(default_factory=list)
    exclude_tools: List[str] = field(default_factory=list)
    
    # Override tool properties
    tool_overrides: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Hooks for custom behavior
    pre_execute: Optional[Callable[[str, Dict], Dict]] = None
    post_execute: Optional[Callable[[str, Any], Any]] = None
    
    def get_effective_tools(self) -> Set[str]:
        """Calculate the effective tool set for this variant."""
        # Start from base profile
        base = PROFILES.get(self.base_profile, PROFILES["full"])
        tools = base.get_tools()
        
        # Add included tools
        tools.update(self.include_tools)
        
        # Remove excluded tools
        tools -= set(self.exclude_tools)
        
        return tools
    
    def create_tools(self, api: "pyWATS") -> Dict[str, "AgentTool"]:
        """
        Create tool instances for this variant.
        
        Args:
            api: pyWATS instance
            
        Returns:
            Dictionary mapping tool names to instances
        """
        from ._registry import create_tool_instance
        
        tools = {}
        for name in self.get_effective_tools():
            tool = create_tool_instance(name, api)
            if tool:
                # Wrap with hooks if provided
                if self.pre_execute or self.post_execute:
                    tool = self._wrap_tool(tool)
                tools[name] = tool
        
        return tools
    
    def get_definitions(self) -> List[Dict[str, Any]]:
        """Get OpenAI-format tool definitions for this variant."""
        from ._registry import get_tool
        
        definitions = []
        for name in self.get_effective_tools():
            cls = get_tool(name)
            if cls:
                definition = cls.get_definition()
                
                # Handle different definition formats:
                # Some tools return {"name", "description", "parameters"}
                # Others return {"function": {"name", "description", "parameters"}}
                def get_desc_container(d):
                    """Get the dict containing 'description'."""
                    if "function" in d:
                        return d["function"]
                    return d
                
                desc_container = get_desc_container(definition)
                
                # Apply overrides from base profile
                base = PROFILES.get(self.base_profile)
                if base and name in base.tool_overrides:
                    for key, value in base.tool_overrides[name].items():
                        if key == "description":
                            desc_container["description"] = value
                
                # Apply variant-specific overrides (take precedence)
                if name in self.tool_overrides:
                    for key, value in self.tool_overrides[name].items():
                        if key == "description":
                            desc_container["description"] = value
                
                definitions.append(definition)
        
        return definitions
    
    def _wrap_tool(self, tool: "AgentTool") -> "AgentTool":
        """Wrap a tool with pre/post hooks."""
        original_execute = tool.execute
        
        def wrapped_execute(params: Dict) -> Any:
            # Pre-execute hook
            if self.pre_execute:
                params = self.pre_execute(tool.name, params)
            
            # Execute tool
            result = original_execute(params)
            
            # Post-execute hook
            if self.post_execute:
                result = self.post_execute(tool.name, result)
            
            return result
        
        tool.execute = wrapped_execute
        return tool
    
    def to_profile(self) -> ToolProfile:
        """Convert this variant to a ToolProfile."""
        return ToolProfile(
            name=self.name,
            description=self.description or f"Variant based on {self.base_profile}",
            tools=self.get_effective_tools(),
            tool_overrides=self.tool_overrides,
        )


# ============================================================================
# Variant Registry
# ============================================================================

# Store for user-defined variants
_VARIANTS: Dict[str, ExperimentalVariant] = {}


def register_variant(variant: ExperimentalVariant) -> None:
    """
    Register an experimental variant.
    
    Args:
        variant: The variant to register
        
    Example:
        >>> my_variant = ExperimentalVariant(
        ...     name="test",
        ...     base_profile="yield",
        ... )
        >>> register_variant(my_variant)
    """
    _VARIANTS[variant.name] = variant


def get_variant(name: str) -> Optional[ExperimentalVariant]:
    """Get a registered variant by name."""
    return _VARIANTS.get(name)


def list_variants() -> List[str]:
    """List all registered variant names."""
    return list(_VARIANTS.keys())


def clear_variants() -> None:
    """Clear all registered variants (for testing)."""
    _VARIANTS.clear()


# ============================================================================
# Convenience Functions
# ============================================================================

def get_profile(name: str) -> Optional[ToolProfile]:
    """
    Get a built-in profile by name.
    
    Args:
        name: Profile name
        
    Returns:
        ToolProfile or None
    """
    return PROFILES.get(name)


def list_profiles() -> List[str]:
    """List all available profile names."""
    return list(PROFILES.keys())


def create_agent_tools(
    api: "pyWATS",
    profile: str = "full",
    variant: Optional[str] = None,
) -> Dict[str, "AgentTool"]:
    """
    Create agent tools with a specific profile or variant.
    
    This is the main entry point for getting tools.
    
    Args:
        api: pyWATS instance
        profile: Profile name to use (default: "full")
        variant: Optional variant name (overrides profile)
        
    Returns:
        Dictionary mapping tool names to instances
        
    Example:
        >>> # Use a built-in profile
        >>> tools = create_agent_tools(api, profile="yield")
        >>> 
        >>> # Use a registered variant
        >>> tools = create_agent_tools(api, variant="my_experiment")
    """
    if variant:
        v = get_variant(variant)
        if v:
            return v.create_tools(api)
        raise ValueError(f"Unknown variant: {variant}")
    
    p = get_profile(profile)
    if p:
        return p.create_tools(api)
    
    raise ValueError(f"Unknown profile: {profile}")


def get_tool_definitions(
    profile: str = "full",
    variant: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Get tool definitions for a profile or variant.
    
    Args:
        profile: Profile name
        variant: Optional variant name (overrides profile)
        
    Returns:
        List of OpenAI-format tool definitions
    """
    if variant:
        v = get_variant(variant)
        if v:
            return v.get_definitions()
        raise ValueError(f"Unknown variant: {variant}")
    
    p = get_profile(profile)
    if p:
        return p.get_definitions()
    
    raise ValueError(f"Unknown profile: {profile}")


# ============================================================================
# Pretty Printing
# ============================================================================

def print_profiles() -> None:
    """Print all available profiles and their tools."""
    print("=" * 70)
    print("PYWATS AGENT PROFILES")
    print("=" * 70)
    
    for name, profile in PROFILES.items():
        print(f"\n📦 {name.upper()}")
        print(f"   {profile.description}")
        print(f"   Tools ({len(profile.tools)}):")
        for tool in sorted(profile.tools):
            print(f"     • {tool}")
    
    if _VARIANTS:
        print("\n" + "=" * 70)
        print("EXPERIMENTAL VARIANTS")
        print("=" * 70)
        
        for name, variant in _VARIANTS.items():
            tools = variant.get_effective_tools()
            print(f"\n🧪 {name}")
            print(f"   Base: {variant.base_profile}")
            if variant.description:
                print(f"   {variant.description}")
            print(f"   Tools ({len(tools)}): {', '.join(sorted(tools))}")
    
    print()


def print_variant_diff(variant_name: str) -> None:
    """Print the difference between a variant and its base profile."""
    variant = get_variant(variant_name)
    if not variant:
        print(f"Unknown variant: {variant_name}")
        return
    
    base = PROFILES.get(variant.base_profile, PROFILES["full"])
    variant_tools = variant.get_effective_tools()
    base_tools = base.get_tools()
    
    added = variant_tools - base_tools
    removed = base_tools - variant_tools
    
    print(f"Variant: {variant_name} (base: {variant.base_profile})")
    print("-" * 50)
    
    if added:
        print("➕ Added:")
        for t in sorted(added):
            print(f"   • {t}")
    
    if removed:
        print("➖ Removed:")
        for t in sorted(removed):
            print(f"   • {t}")
    
    if variant.tool_overrides:
        print("🔧 Overrides:")
        for tool, overrides in variant.tool_overrides.items():
            print(f"   • {tool}: {list(overrides.keys())}")
    
    if not added and not removed and not variant.tool_overrides:
        print("   (identical to base profile)")
