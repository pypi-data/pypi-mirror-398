"""
Agent autonomy and analytical style configuration.

This module provides controls for:
1. How thorough/careful the agent is in analytics (rigor)
2. How write operations are handled (permissions)

These are separate concerns:
- Analytics: No data risk, but cost/thoroughness trade-off
- Writes: Real risk, always requires caution

Usage:
    >>> from pywats_agent import AgentConfig, AnalyticalRigor, WriteMode
    >>> 
    >>> # Quick analysis, no writes allowed
    >>> config = AgentConfig(
    ...     rigor=AnalyticalRigor.QUICK,
    ...     write_mode=WriteMode.BLOCKED,
    ... )
    >>> 
    >>> # Thorough analysis for production investigation
    >>> config = AgentConfig(
    ...     rigor=AnalyticalRigor.THOROUGH,
    ...     write_mode=WriteMode.CONFIRM_ALL,
    ... )
    >>> 
    >>> # Get system prompt instructions
    >>> print(config.get_system_prompt())
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class AnalyticalRigor(str, Enum):
    """
    How thorough the agent is when analyzing data.
    
    This affects:
    - How many API calls to make for cross-validation
    - How much data to gather before drawing conclusions
    - Confidence level required before stating findings
    - Whether to suggest additional analysis
    
    No data risk at any level - purely cost/speed vs thoroughness trade-off.
    """
    
    QUICK = "quick"
    """
    Fast, minimal analysis. Good for:
    - Quick status checks
    - Simple queries with obvious answers
    - Cost-sensitive environments
    - When user wants a fast answer, not a report
    
    Behavior:
    - Uses smallest reasonable sample sizes
    - Makes confident statements with less data
    - Skips cross-validation steps
    - Doesn't proactively suggest follow-up analysis
    """
    
    BALANCED = "balanced"
    """
    Reasonable thoroughness (default). Good for:
    - Most day-to-day questions
    - Standard yield monitoring
    - Typical troubleshooting
    
    Behavior:
    - Uses standard sample sizes
    - States findings with appropriate caveats
    - Does basic cross-validation
    - May suggest obvious follow-up questions
    """
    
    THOROUGH = "thorough"
    """
    More rigorous analysis. Good for:
    - Production investigations
    - Quality audits
    - When accuracy matters more than speed
    
    Behavior:
    - Uses larger sample sizes
    - Cross-validates findings across dimensions
    - States confidence levels explicitly
    - Proactively identifies potential issues
    - Suggests follow-up analysis
    """
    
    EXHAUSTIVE = "exhaustive"
    """
    Leave no stone unturned. Good for:
    - Root cause investigations for critical issues
    - Customer escalations
    - Compliance/audit requirements
    - When you need to be 100% sure
    
    Behavior:
    - Maximum sample sizes
    - Extensive cross-validation
    - Checks for edge cases and outliers
    - Very explicit about uncertainty
    - Comprehensive follow-up suggestions
    - May make multiple rounds of queries
    """


class WriteMode(str, Enum):
    """
    How write operations (create/update/delete) are handled.
    
    Unlike analytics, writes have real risk and should always
    be handled cautiously. Most deployments should use BLOCKED
    or CONFIRM_ALL.
    """
    
    BLOCKED = "blocked"
    """
    No write operations allowed.
    
    The agent can analyze data and suggest actions, but cannot
    actually modify anything. Safest option for:
    - Analytics-only deployments
    - Viewer/read-only users
    - When you don't trust the integration yet
    
    Write tools (control_panel create/update/delete) return errors.
    """
    
    CONFIRM_ALL = "confirm_all"
    """
    All writes require explicit confirmation.
    
    The agent will:
    - Explain what it wants to do
    - List affected entities
    - Wait for user approval before executing
    
    This is the safest mode that still allows writes.
    Recommended for most write-enabled deployments.
    """
    
    CONFIRM_DESTRUCTIVE = "confirm_destructive"
    """
    Only destructive operations require confirmation.
    
    - Creates: Execute immediately
    - Updates: Execute immediately
    - Deletes: Require confirmation
    - Revokes: Require confirmation
    
    For environments where creates/updates are low-risk
    but you want protection against accidental deletions.
    """


# ============================================================================
# Agent Configuration
# ============================================================================

class AgentConfig(BaseModel):
    """
    Configuration for agent behavior.
    
    Combines analytical rigor (how thorough) with write mode (how cautious).
    """
    
    rigor: AnalyticalRigor = Field(
        default=AnalyticalRigor.BALANCED,
        description="How thorough the agent is in analysis"
    )
    
    write_mode: WriteMode = Field(
        default=WriteMode.BLOCKED,
        description="How write operations are handled"
    )
    
    # Analytics tuning
    max_api_calls_per_question: int = Field(
        default=10,
        description="Maximum API calls for a single question (prevents runaway costs)"
    )
    
    prefer_aggregated_data: bool = Field(
        default=True,
        description="Prefer aggregated endpoints over raw data when possible"
    )
    
    # Confidence settings
    state_uncertainty: bool = Field(
        default=True,
        description="Whether to explicitly state uncertainty in findings"
    )
    
    suggest_followups: bool = Field(
        default=True,
        description="Whether to proactively suggest follow-up analysis"
    )
    
    def get_system_prompt(self) -> str:
        """
        Generate system prompt instructions based on configuration.
        
        Returns:
            Instructions for the LLM about how to behave
        """
        parts = []
        
        # Rigor instructions
        parts.append(self._get_rigor_prompt())
        
        # Write mode instructions
        parts.append(self._get_write_mode_prompt())
        
        # Additional settings
        if not self.suggest_followups:
            parts.append(
                "Do not proactively suggest follow-up analysis unless asked."
            )
        
        if self.max_api_calls_per_question < 5:
            parts.append(
                f"Minimize API calls. Maximum {self.max_api_calls_per_question} "
                "calls per question. Get the answer efficiently."
            )
        
        return "\n\n".join(parts)
    
    def _get_rigor_prompt(self) -> str:
        """Get system prompt for analytical rigor level."""
        
        if self.rigor == AnalyticalRigor.QUICK:
            return """ANALYTICAL STYLE: QUICK
- Give fast, direct answers
- Use minimal data to reach conclusions
- Don't over-qualify statements with caveats
- Skip cross-validation unless specifically asked
- One or two API calls should usually suffice
- If the answer is reasonably clear, state it confidently"""

        elif self.rigor == AnalyticalRigor.BALANCED:
            return """ANALYTICAL STYLE: BALANCED
- Provide thorough but efficient analysis
- Use appropriate caveats when data is limited
- Cross-validate findings when it adds value
- Make a reasonable number of API calls (3-5 typical)
- Mention if additional analysis could provide more certainty
- Balance speed with accuracy"""

        elif self.rigor == AnalyticalRigor.THOROUGH:
            return """ANALYTICAL STYLE: THOROUGH
- Conduct rigorous analysis before drawing conclusions
- Cross-validate findings across multiple dimensions
- Explicitly state confidence levels
- Use larger sample sizes and wider date ranges
- Look for edge cases and exceptions
- Proactively identify potential issues
- Suggest relevant follow-up analysis
- It's better to be thorough than fast"""

        else:  # EXHAUSTIVE
            return """ANALYTICAL STYLE: EXHAUSTIVE
- Leave no stone unturned - this is critical analysis
- Make multiple rounds of queries if needed
- Cross-validate everything across all dimensions
- Check for outliers, edge cases, and anomalies
- Be very explicit about any uncertainty
- If something could be misinterpreted, clarify it
- Comprehensive follow-up suggestions
- Do not cut corners - accuracy is paramount
- Consider time-based variations and trends
- Check data quality and completeness"""
    
    def _get_write_mode_prompt(self) -> str:
        """Get system prompt for write mode."""
        
        if self.write_mode == WriteMode.BLOCKED:
            return """WRITE OPERATIONS: BLOCKED
You can analyze data and suggest actions, but cannot modify anything.
If asked to create, update, or delete data, explain what would need
to be done and suggest the user do it manually or contact an admin."""

        elif self.write_mode == WriteMode.CONFIRM_ALL:
            return """WRITE OPERATIONS: CONFIRM ALL
Before executing ANY write operation (create, update, delete):
1. Explain exactly what you plan to do
2. List all entities/records that will be affected
3. Explain the impact of the change
4. Ask for explicit confirmation before proceeding
5. Only proceed if the user confirms with "yes", "confirm", or similar

Never assume permission - always ask first."""

        else:  # CONFIRM_DESTRUCTIVE
            return """WRITE OPERATIONS: CONFIRM DESTRUCTIVE ONLY
- Creates and updates: You can execute these directly
- Deletes and revokes: ALWAYS ask for confirmation first

For destructive operations:
1. Explain what will be deleted/revoked
2. Warn about any cascade effects
3. Ask for explicit confirmation
4. Only proceed on clear confirmation"""
    
    def get_default_parameters(self) -> Dict[str, Any]:
        """
        Get default tool parameters based on rigor level.
        
        Returns:
            Dictionary of parameter defaults
        """
        defaults = {}
        
        if self.rigor == AnalyticalRigor.QUICK:
            defaults["top_count"] = 100
            defaults["max_results"] = 100
            defaults["include_details"] = False
        elif self.rigor == AnalyticalRigor.BALANCED:
            defaults["top_count"] = 500
            defaults["max_results"] = 500
            defaults["include_details"] = True
        elif self.rigor == AnalyticalRigor.THOROUGH:
            defaults["top_count"] = 1000
            defaults["max_results"] = 1000
            defaults["include_details"] = True
        else:  # EXHAUSTIVE
            defaults["top_count"] = 5000
            defaults["max_results"] = 5000
            defaults["include_details"] = True
        
        return defaults
    
    def allows_write(self, operation: str) -> bool:
        """
        Check if a write operation is allowed.
        
        Args:
            operation: Operation type (create, update, delete, etc.)
            
        Returns:
            True if operation is allowed (possibly with confirmation)
        """
        if self.write_mode == WriteMode.BLOCKED:
            return False
        return True
    
    def requires_confirmation(self, operation: str) -> bool:
        """
        Check if an operation requires user confirmation.
        
        Args:
            operation: Operation type (create, update, delete, etc.)
            
        Returns:
            True if confirmation is required before executing
        """
        if self.write_mode == WriteMode.BLOCKED:
            return True  # Would be blocked anyway
        
        if self.write_mode == WriteMode.CONFIRM_ALL:
            return operation in {"create", "update", "delete", "revoke", "set_phase", "set_state"}
        
        if self.write_mode == WriteMode.CONFIRM_DESTRUCTIVE:
            return operation in {"delete", "revoke"}
        
        return False


# ============================================================================
# Preset Configurations
# ============================================================================

# Common presets for easy use
PRESETS: Dict[str, AgentConfig] = {
    "viewer": AgentConfig(
        rigor=AnalyticalRigor.BALANCED,
        write_mode=WriteMode.BLOCKED,
    ),
    
    "quick_check": AgentConfig(
        rigor=AnalyticalRigor.QUICK,
        write_mode=WriteMode.BLOCKED,
        max_api_calls_per_question=3,
        suggest_followups=False,
    ),
    
    "investigation": AgentConfig(
        rigor=AnalyticalRigor.THOROUGH,
        write_mode=WriteMode.BLOCKED,
    ),
    
    "audit": AgentConfig(
        rigor=AnalyticalRigor.EXHAUSTIVE,
        write_mode=WriteMode.BLOCKED,
        state_uncertainty=True,
    ),
    
    "admin": AgentConfig(
        rigor=AnalyticalRigor.BALANCED,
        write_mode=WriteMode.CONFIRM_ALL,
    ),
    
    "power_user": AgentConfig(
        rigor=AnalyticalRigor.BALANCED,
        write_mode=WriteMode.CONFIRM_DESTRUCTIVE,
    ),
}


def get_preset(name: str) -> AgentConfig:
    """
    Get a preset configuration by name.
    
    Args:
        name: Preset name (viewer, quick_check, investigation, audit, admin, power_user)
        
    Returns:
        AgentConfig for the preset
        
    Raises:
        KeyError: If preset name is unknown
    """
    if name not in PRESETS:
        raise KeyError(
            f"Unknown preset: {name}. "
            f"Available: {', '.join(PRESETS.keys())}"
        )
    return PRESETS[name].model_copy()
