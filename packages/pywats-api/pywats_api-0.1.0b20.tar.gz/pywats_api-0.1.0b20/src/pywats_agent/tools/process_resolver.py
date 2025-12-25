"""
Process name resolution and matching utilities.

Handles fuzzy matching of process/test_operation names since users
often use imprecise names like "PCBA" instead of "PCBA test", or
"board test" instead of the configured process name.

PROCESS TERMINOLOGY IN WATS:
- test_operation: For testing (UUT/UUTReport - Unit Under Test)
- repair_operation: For repair logging (UUR/UURReport - Unit Under Repair)
- wip_operation: For production tracking (not used in analysis tools)

COMMON CUSTOMER CONFUSION:
When multiple different tests (e.g., AOI and ICT) are sent to the same
process (e.g., "Structural Tests"), only the FIRST test determines unit
counts and FPY-LPY. Subsequent tests are treated as "retests after pass"
and show 0 units. Diagnosis: Check for different sw_filename within process.

NOTE: This module uses the existing ProcessService available via api.process
which provides cached access to all processes with methods like:
- api.process.get_processes() - all processes
- api.process.get_test_operations() - test operations only
- api.process.get_repair_operations() - repair operations only
- api.process.get_test_operation(name_or_code) - lookup by name or code
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING
import re
from difflib import SequenceMatcher

if TYPE_CHECKING:
    from pywats import pyWATS
    from pywats.domains.process.models import ProcessInfo


# Common aliases for process names
# Maps common user terms to likely process name patterns
PROCESS_ALIASES: Dict[str, List[str]] = {
    # PCBA test aliases
    "pcba": ["pcba test", "pcba", "board test", "pcb test"],
    "board": ["pcba test", "board test", "pcb test"],
    
    # ICT aliases
    "ict": ["ict", "in-circuit", "in circuit", "incircuit"],
    "in-circuit": ["ict", "in-circuit test", "in circuit test"],
    
    # FCT aliases
    "fct": ["fct", "functional", "functional test"],
    "functional": ["fct", "functional test", "functional"],
    
    # EOL aliases
    "eol": ["eol", "end of line", "end-of-line", "endofline"],
    "end of line": ["eol", "end of line", "end-of-line test"],
    
    # AOI aliases
    "aoi": ["aoi", "automated optical", "optical inspection"],
    "optical": ["aoi", "automated optical inspection"],
    
    # AXI/X-Ray aliases
    "axi": ["axi", "x-ray", "xray", "automated x-ray"],
    "x-ray": ["axi", "x-ray inspection", "xray"],
    
    # Final test aliases
    "final": ["final test", "final", "fqc", "final quality"],
    "fqc": ["fqc", "final quality check", "final quality"],
    
    # Burn-in aliases
    "burnin": ["burn-in", "burnin", "burn in", "aging"],
    "burn-in": ["burn-in test", "burn-in", "aging test"],
    
    # Repair aliases
    "repair": ["repair", "rework", "fix"],
    "rework": ["rework", "repair", "rma"],
}


def normalize_process_name(name: str) -> str:
    """
    Normalize a process name for comparison.
    
    - Lowercase
    - Remove extra whitespace
    - Remove common suffixes like "test", "operation"
    
    Args:
        name: Raw process name
        
    Returns:
        Normalized name for comparison
    """
    if not name:
        return ""
    
    # Lowercase and strip
    normalized = name.lower().strip()
    
    # Remove multiple spaces
    normalized = re.sub(r'\s+', ' ', normalized)
    
    return normalized


def calculate_similarity(name1: str, name2: str) -> float:
    """
    Calculate similarity ratio between two process names.
    
    Args:
        name1: First process name
        name2: Second process name
        
    Returns:
        Similarity ratio (0.0 to 1.0)
    """
    n1 = normalize_process_name(name1)
    n2 = normalize_process_name(name2)
    
    # Exact match after normalization
    if n1 == n2:
        return 1.0
    
    # Check if one contains the other
    if n1 in n2 or n2 in n1:
        return 0.9
    
    # Use sequence matching for fuzzy comparison
    return SequenceMatcher(None, n1, n2).ratio()


class ProcessResolver:
    """
    Resolves and matches process/test_operation names.
    
    Handles:
    - Fuzzy matching of user input to actual process names
    - Alias expansion (e.g., "PCBA" -> "PCBA test")
    - Case-insensitive matching
    - Confirmation prompts for ambiguous matches
    
    TERMINOLOGY CLARIFICATION:
    - Process = Generic term for any operation (test, repair, WIP)
    - test_operation = Testing processes (for UUT/UUTReport)
    - repair_operation = Repair processes (for UUR/UURReport)
    - wip_operation = Production tracking (excluded from analysis)
    
    NOTE: This class delegates to api.process which maintains an auto-updating
    cached list of processes. No additional caching is needed here.
    
    Example:
        >>> resolver = ProcessResolver(api)
        >>> 
        >>> # Exact match
        >>> match = resolver.resolve("FCT")
        >>> print(match.name)  # "FCT" or "Functional Test"
        >>> 
        >>> # Fuzzy match
        >>> match = resolver.resolve("board test")
        >>> print(match.name)  # "PCBA test"
        >>> 
        >>> # Ambiguous - needs confirmation
        >>> candidates = resolver.resolve_with_candidates("test")
        >>> if len(candidates) > 1:
        ...     print("Did you mean one of:", [c.name for c in candidates])
    """
    
    def __init__(self, api: "pyWATS"):
        """
        Initialize with a pyWATS instance.
        
        Args:
            api: Configured pyWATS instance (uses api.process for cached process list)
        """
        self._api = api
    
    def get_processes(self) -> List["ProcessInfo"]:
        """
        Get all processes (delegates to api.process which has auto-updating cache).
        
        Returns:
            List of ProcessInfo objects
        """
        return self._api.process.get_processes()
    
    def get_test_operations(self) -> List["ProcessInfo"]:
        """Get only test operations (not repair or WIP)."""
        return self._api.process.get_test_operations()
    
    def get_repair_operations(self) -> List["ProcessInfo"]:
        """Get only repair operations."""
        return self._api.process.get_repair_operations()
    
    def resolve(
        self, 
        user_input: str,
        operation_type: str = "test",
        threshold: float = 0.6
    ) -> Optional[ProcessInfo]:
        """
        Resolve a user-provided process name to an actual process.
        
        Args:
            user_input: User's process name (may be imprecise)
            operation_type: "test", "repair", or "any"
            threshold: Minimum similarity threshold (0.0-1.0)
            
        Returns:
            Best matching ProcessInfo, or None if no good match
        """
        match, _ = self.resolve_with_candidates(user_input, operation_type, threshold)
        return match
    
    def resolve_with_candidates(
        self,
        user_input: str,
        operation_type: str = "test",
        threshold: float = 0.6
    ) -> Tuple[Optional[ProcessInfo], List[ProcessInfo]]:
        """
        Resolve a process name with candidate alternatives.
        
        Use this when you need to confirm with the user for ambiguous matches.
        
        Args:
            user_input: User's process name
            operation_type: "test", "repair", or "any"
            threshold: Minimum similarity threshold
            
        Returns:
            Tuple of (best_match, all_candidates_above_threshold)
        """
        if not user_input:
            return None, []
        
        # Get relevant processes
        if operation_type == "test":
            processes = self.get_test_operations()
        elif operation_type == "repair":
            processes = self.get_repair_operations()
        else:
            processes = self.get_processes()
        
        if not processes:
            return None, []
        
        normalized_input = normalize_process_name(user_input)
        
        # Score each process
        scored: List[Tuple[float, ProcessInfo]] = []
        
        for process in processes:
            # Direct name match
            score = calculate_similarity(user_input, process.name)
            
            # Check if input is a known alias
            for alias_key, alias_patterns in PROCESS_ALIASES.items():
                if normalized_input in [normalize_process_name(a) for a in alias_patterns]:
                    # Check if process name matches any alias pattern
                    for pattern in alias_patterns:
                        pattern_score = calculate_similarity(process.name, pattern)
                        score = max(score, pattern_score * 0.95)  # Slight penalty for alias match
            
            if score >= threshold:
                scored.append((score, process))
        
        # Sort by score descending
        scored.sort(key=lambda x: x[0], reverse=True)
        
        candidates = [p for _, p in scored]
        best_match = candidates[0] if candidates else None
        
        return best_match, candidates
    
    def find_exact_match(self, name: str) -> Optional[ProcessInfo]:
        """
        Find an exact match (case-insensitive) for a process name.
        
        Args:
            name: Process name to match exactly
            
        Returns:
            ProcessInfo if exact match found, None otherwise
        """
        normalized = normalize_process_name(name)
        
        for process in self.get_processes():
            if normalize_process_name(process.name) == normalized:
                return process
        
        return None
    
    def suggest_process_clarification(
        self,
        user_input: str,
        candidates: List[ProcessInfo]
    ) -> str:
        """
        Generate a clarification message for ambiguous process names.
        
        Args:
            user_input: What the user typed
            candidates: Possible matches
            
        Returns:
            User-friendly message asking for clarification
        """
        if not candidates:
            processes = self.get_test_operations()
            process_names = [p.name for p in processes[:10]]  # Show first 10
            return (
                f"I couldn't find a process matching '{user_input}'. "
                f"Available test operations include: {', '.join(process_names)}"
            )
        
        if len(candidates) == 1:
            return f"Did you mean '{candidates[0].name}'?"
        
        names = [c.name for c in candidates[:5]]  # Show top 5
        return (
            f"'{user_input}' could match several processes. "
            f"Did you mean: {', '.join(names)}?"
        )
    
    def get_process_summary(self) -> Dict[str, Any]:
        """
        Get a summary of available processes for agent context.
        
        Returns:
            Dict with test_operations, repair_operations, and counts
        """
        processes = self.get_processes()
        
        return {
            "test_operations": [
                {"code": p.code, "name": p.name}
                for p in processes if p.is_test_operation
            ],
            "repair_operations": [
                {"code": p.code, "name": p.name}
                for p in processes if p.is_repair_operation
            ],
            "total_processes": len(processes),
            "test_count": len([p for p in processes if p.is_test_operation]),
            "repair_count": len([p for p in processes if p.is_repair_operation]),
        }


def diagnose_mixed_process_problem(
    api: "pyWATS",
    process_name: str,
    part_number: Optional[str] = None,
    days: int = 30
) -> Dict[str, Any]:
    """
    Diagnose if a process has mixed tests causing 0-unit yield issues.
    
    When multiple different tests (AOI, ICT) are sent to the same process,
    only the first test determines unit counts. The second test shows 0 units
    because all units already "passed" with the first test.
    
    SYMPTOM: "Why is ICT showing 0 units?"
    DIAGNOSIS: Check for runs with different sw_filename in the same process.
    
    Args:
        api: pyWATS instance
        process_name: Process to diagnose
        part_number: Optional product filter
        days: Days to look back
        
    Returns:
        Dict with diagnosis results:
        - has_mixed_tests: True if multiple sw_filenames found
        - sw_filenames: List of unique software filenames
        - recommendation: What to do about it
    """
    from pywats.domains.report.models import WATSFilter
    from datetime import datetime, timedelta
    
    # Build filter to get reports for this process
    date_from = datetime.now() - timedelta(days=days)
    
    filter_params = {
        "date_from": date_from,
        "test_operation": process_name,
        "dimensions": "swFilename",
    }
    
    if part_number:
        filter_params["part_number"] = part_number
    
    try:
        wats_filter = WATSFilter(**filter_params)
        yield_data = api.analytics.get_dynamic_yield(wats_filter)
        
        # Extract unique software filenames
        sw_filenames = set()
        for d in yield_data:
            sw = getattr(d, 'sw_filename', None) or getattr(d, 'swFilename', None)
            if sw:
                sw_filenames.add(sw)
        
        has_mixed = len(sw_filenames) > 1
        
        result = {
            "has_mixed_tests": has_mixed,
            "sw_filenames": list(sw_filenames),
            "count": len(sw_filenames),
        }
        
        if has_mixed:
            result["recommendation"] = (
                f"Process '{process_name}' has {len(sw_filenames)} different test programs: "
                f"{', '.join(sw_filenames)}. "
                "This likely means different tests are being sent to the same process. "
                "Only the first test type determines unit counts and FPY. "
                "Consider separating into different processes for accurate yield tracking."
            )
            result["explanation"] = (
                "In WATS, once a unit passes a process, subsequent runs are treated as "
                "retests even if they're actually different tests. The second test type "
                "shows 0 units because all units already 'passed' with the first test."
            )
        else:
            result["recommendation"] = None
            result["explanation"] = "Process has a single test program - no mixing detected."
        
        return result
        
    except Exception as e:
        return {
            "has_mixed_tests": None,
            "error": str(e),
            "recommendation": "Unable to diagnose - check process name and filters.",
        }


# Export for use in other modules
__all__ = [
    "ProcessResolver",
    "ProcessInfo",
    "normalize_process_name",
    "calculate_similarity",
    "diagnose_mixed_process_problem",
    "PROCESS_ALIASES",
]
