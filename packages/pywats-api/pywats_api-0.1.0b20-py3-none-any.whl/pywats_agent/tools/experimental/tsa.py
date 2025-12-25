"""\
Experimental TSA Tool ("start_tsa")

A new approach to Test Step Analysis that:
- Acts as "evidence curator" not "storyteller"
- Enforces required context (part + process) before proceeding
- Preprocesses data in the tool layer, not the LLM
- Returns ranked candidate lists, not full datasets
- Uses session caching for efficient drill-down

DESIGN PRINCIPLES:
1. ZERO GUESSING: Require explicit part_number + test_operation
2. COMPATIBILITY CHECK: Validate multi-process TSA is meaningful
3. PREPROCESSING: Normalize, derive metrics, rank candidates
4. SMALL RESPONSES: Return top-K candidates, not full grids
5. SESSION CACHING: Raw data accessible via handles for drill-down

CANDIDATE RANKING CRITERIA:
- Event Rate: step_fail_count / step_count (aka fallout)
- Causal Rate: step_caused_uut_failed / total_uut_failed (impact)
- Infra Suspect: step_error + step_terminated (equipment issues)
- Cpk: Process capability (lower = worse)
- Time: Average step time (anomaly detection)

USAGE PATTERN:
1. LLM calls start_tsa(part_number, test_operation)
2. Tool validates context, loads data, preprocesses
3. Returns StartTsaResponse with top-K candidates
4. LLM can request drill-down via session handle
5. Session expires after TTL (default 5 min)

Author: Experimental variant system
"""

import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, TYPE_CHECKING, Tuple
from enum import Enum
from dataclasses import dataclass, field
from threading import Lock
from pydantic import BaseModel, Field

from ...result import AgentResult

if TYPE_CHECKING:
    from pywats import pyWATS
    from pywats.domains.analytics.models import StepAnalysisRow


# =============================================================================
# Configuration Constants
# =============================================================================

# Top-K settings for each candidate list
TOP_K_RELIABILITY = 10      # Reliability failures (event rate)
TOP_K_IMPACT = 10           # Impact failures (causal rate)
TOP_K_CAPABILITY = 10       # Capability concerns (cpk)
TOP_K_INFRA = 5             # Infrastructure suspects (errors)
TOP_K_TIME = 5              # Time anomalies

# Cpk thresholds
CPK_CAPABLE = 1.33
CPK_MARGINAL = 1.0
CPK_CRITICAL = 0.67

# Session settings
SESSION_TTL_MINUTES = 5
MAX_ACTIVE_SESSIONS = 100

# Sequence signature settings
SIGNATURE_SAMPLE_SIZE = 5   # Sample N steps for signature


# =============================================================================
# Data Models - Input/Output Structures
# =============================================================================

class TsaCandidate(BaseModel):
    """
    A single step that's a candidate for investigation.
    
    Contains pre-computed investigation-ready metrics.
    """
    step_name: str
    step_path: str
    step_type: Optional[str] = None
    step_group: Optional[str] = None
    
    # Counts
    step_count: int = 0
    step_passed: int = 0
    step_failed: int = 0
    step_error: int = 0
    step_terminated: int = 0
    caused_uut_failed: int = 0
    
    # Computed rates (tool-layer derived)
    event_fail_rate: float = 0.0       # step_failed / step_count
    causal_rate: float = 0.0           # caused_uut_failed / total_failed_units
    infra_suspect_rate: float = 0.0    # (error + terminated) / step_count
    
    # Capability (if measurement)
    cpk: Optional[float] = None
    cpk_status: Optional[str] = None   # "capable", "marginal", "incapable", "critical"
    
    # Measurement stats (if applicable)
    avg: Optional[float] = None
    stdev: Optional[float] = None
    limit_low: Optional[float] = None
    limit_high: Optional[float] = None
    
    # Time analysis
    avg_time_ms: Optional[float] = None
    
    # Ranking info (filled by tool)
    rank: int = 0
    rank_reason: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return self.model_dump(exclude_none=True)


class TsaCandidateList(BaseModel):
    """
    A ranked list of candidates for a specific concern type.
    
    Each list is pre-sorted by the tool, top-K only.
    """
    concern_type: str                   # "reliability", "impact", "capability", "infra", "time"
    title: str                          # Human-readable title
    count: int = 0                      # Total candidates in this category (before top-K)
    candidates: List[TsaCandidate] = Field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "concern_type": self.concern_type,
            "title": self.title,
            "count": self.count,
            "top_k": len(self.candidates),
            "candidates": [c.to_dict() for c in self.candidates],
        }


class TsaScope(BaseModel):
    """
    Defines the scope/filter of the TSA analysis.
    """
    part_number: str
    test_operation: str
    revision: Optional[str] = None
    sw_filename: Optional[str] = None
    days: int = 30
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    run: int = 1


class TsaTotals(BaseModel):
    """
    Overall summary totals from the TSA.
    """
    total_steps: int = 0
    total_measurements: int = 0
    total_executions: int = 0
    
    # UUT level (for causal rate calculation)
    total_uut_tested: int = 0
    total_uut_failed: int = 0
    
    # Step level
    total_step_failures: int = 0
    total_caused_uut_fail: int = 0
    
    # Capability distribution
    capable_count: int = 0
    marginal_count: int = 0
    incapable_count: int = 0
    critical_count: int = 0
    
    # Rates
    overall_pass_rate: Optional[float] = None
    avg_cpk: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump(exclude_none=True)


class TsaGroupSummary(BaseModel):
    """
    Summary of step groups (for large test sequences).
    
    Helps LLM navigate without full dataset.
    """
    group_name: str
    step_count: int = 0
    failure_count: int = 0
    measurement_count: int = 0
    worst_cpk: Optional[float] = None
    has_critical: bool = False


class StartTsaInput(BaseModel):
    """
    Input parameters for starting a TSA session.
    
    REQUIRED: part_number AND test_operation
    Tool will refuse to guess these.
    """
    part_number: str = Field(
        ..., 
        description="Product part number (REQUIRED - do not guess)"
    )
    test_operation: str = Field(
        ..., 
        description="Test operation/process name (REQUIRED - do not guess)"
    )
    
    # Optional filters
    revision: Optional[str] = Field(
        default=None,
        description="Product revision to filter to"
    )
    sw_filename: Optional[str] = Field(
        default=None,
        description="Test software filename to filter to"
    )
    days: int = Field(
        default=30,
        description="Days of data to analyze (default 30)"
    )
    run: int = Field(
        default=1,
        description="Run number (default 1 = first pass)"
    )
    
    # Multi-process support (experimental)
    additional_processes: Optional[List[str]] = Field(
        default=None,
        description="Additional processes for multi-process TSA (requires compatibility check)"
    )


class StartTsaResponse(BaseModel):
    """
    Response from start_tsa tool.
    
    Contains:
    - case_id: Unique ID for this analysis session
    - dataset_handle: Reference for drill-down operations
    - scope: What was analyzed (filters applied)
    - totals: High-level summary numbers
    - candidate_lists: Pre-ranked lists of investigation candidates
    - group_summary: Overview of step groups (for navigation)
    - warnings: Any data quality or compatibility warnings
    """
    case_id: str
    dataset_handle: str
    
    scope: TsaScope
    totals: TsaTotals
    
    # Pre-computed capability coverage
    capability_coverage: Dict[str, int] = Field(default_factory=dict)
    
    # Top-K candidate lists by concern type
    candidate_lists: List[TsaCandidateList] = Field(default_factory=list)
    
    # Group navigation (for large sequences)
    group_summary: List[TsaGroupSummary] = Field(default_factory=list)
    
    # Warnings and recommendations
    warnings: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    
    # Metadata
    expires_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "dataset_handle": self.dataset_handle,
            "scope": self.scope.model_dump(exclude_none=True),
            "totals": self.totals.to_dict(),
            "capability_coverage": self.capability_coverage,
            "candidate_lists": [cl.to_dict() for cl in self.candidate_lists],
            "group_summary": [gs.model_dump() for gs in self.group_summary],
            "warnings": self.warnings,
            "recommendations": self.recommendations,
        }


# =============================================================================
# Session Management
# =============================================================================

@dataclass
class TsaSession:
    """
    Cached TSA session holding raw data and indexes.
    
    Enables drill-down without re-fetching.
    """
    session_id: str
    case_id: str
    scope: TsaScope
    
    # Raw data (kept for drill-down)
    raw_steps: List["StepAnalysisRow"] = field(default_factory=list)
    
    # Indexes for fast lookup
    step_by_path: Dict[str, "StepAnalysisRow"] = field(default_factory=dict)
    step_by_name: Dict[str, List["StepAnalysisRow"]] = field(default_factory=dict)
    steps_by_group: Dict[str, List["StepAnalysisRow"]] = field(default_factory=dict)
    
    # Derived data
    total_uut_failed: int = 0
    sequence_signature: str = ""
    
    # Session metadata
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime = field(default_factory=lambda: datetime.now() + timedelta(minutes=SESSION_TTL_MINUTES))
    access_count: int = 0
    
    @property
    def is_expired(self) -> bool:
        return datetime.now() > self.expires_at
    
    def touch(self) -> None:
        """Update access time."""
        self.access_count += 1
    
    def get_step(self, path: str) -> Optional["StepAnalysisRow"]:
        """Get step by path."""
        self.touch()
        return self.step_by_path.get(path)
    
    def get_group(self, group: str) -> List["StepAnalysisRow"]:
        """Get all steps in a group."""
        self.touch()
        return self.steps_by_group.get(group, [])


class TsaSessionManager:
    """
    Manages TSA sessions with auto-expiration.
    
    Thread-safe singleton.
    """
    _instance: Optional["TsaSessionManager"] = None
    _lock = Lock()
    
    def __new__(cls) -> "TsaSessionManager":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._sessions: Dict[str, TsaSession] = {}
                cls._instance._sessions_lock = Lock()
            return cls._instance
    
    @classmethod
    def get_instance(cls) -> "TsaSessionManager":
        return cls()
    
    def create_session(
        self,
        scope: TsaScope,
        raw_steps: List["StepAnalysisRow"],
        total_uut_failed: int,
    ) -> TsaSession:
        """Create new session with fetched data."""
        # Cleanup expired sessions
        self._cleanup_expired()
        
        # Generate IDs
        session_id = str(uuid.uuid4())
        case_id = f"TSA-{datetime.now().strftime('%Y%m%d%H%M%S')}-{session_id[:8]}"
        
        # Build indexes
        step_by_path: Dict[str, StepAnalysisRow] = {}
        step_by_name: Dict[str, List[StepAnalysisRow]] = {}
        steps_by_group: Dict[str, List[StepAnalysisRow]] = {}
        
        for step in raw_steps:
            path = step.step_path or ""
            name = step.step_name or "Unknown"
            group = step.step_group or "Other"
            
            step_by_path[path] = step
            
            if name not in step_by_name:
                step_by_name[name] = []
            step_by_name[name].append(step)
            
            if group not in steps_by_group:
                steps_by_group[group] = []
            steps_by_group[group].append(step)
        
        # Build sequence signature (sample of step names for compatibility check)
        signature = self._build_signature(raw_steps)
        
        session = TsaSession(
            session_id=session_id,
            case_id=case_id,
            scope=scope,
            raw_steps=raw_steps,
            step_by_path=step_by_path,
            step_by_name=step_by_name,
            steps_by_group=steps_by_group,
            total_uut_failed=total_uut_failed,
            sequence_signature=signature,
        )
        
        with self._sessions_lock:
            # Enforce max sessions
            if len(self._sessions) >= MAX_ACTIVE_SESSIONS:
                self._evict_oldest()
            self._sessions[session_id] = session
        
        return session
    
    def get_session(self, session_id: str) -> Optional[TsaSession]:
        """Get session by ID."""
        with self._sessions_lock:
            session = self._sessions.get(session_id)
            if session and not session.is_expired:
                session.touch()
                return session
            elif session:
                # Expired, remove it
                del self._sessions[session_id]
        return None
    
    def _build_signature(self, steps: List["StepAnalysisRow"]) -> str:
        """Build a signature from sampled step names for compatibility checks."""
        if not steps:
            return ""
        
        # Sample evenly distributed steps
        sample_size = min(SIGNATURE_SAMPLE_SIZE, len(steps))
        indices = [i * len(steps) // sample_size for i in range(sample_size)]
        sampled_names = [steps[i].step_name or "" for i in indices]
        
        # Hash the sampled names
        combined = "|".join(sampled_names)
        return hashlib.md5(combined.encode()).hexdigest()[:8]
    
    def _cleanup_expired(self) -> None:
        """Remove expired sessions."""
        with self._sessions_lock:
            expired = [
                sid for sid, session in self._sessions.items()
                if session.is_expired
            ]
            for sid in expired:
                del self._sessions[sid]
    
    def _evict_oldest(self) -> None:
        """Evict oldest session to make room."""
        with self._sessions_lock:
            if self._sessions:
                oldest_id = min(
                    self._sessions.keys(),
                    key=lambda sid: self._sessions[sid].created_at
                )
                del self._sessions[oldest_id]


# =============================================================================
# Main Tool Implementation
# =============================================================================

class StartTsaTool:
    """
    Start Test Step Analysis (TSA) - Experimental.
    
    A new approach to TSA that:
    1. ENFORCES required context (part_number + test_operation)
    2. Validates compatibility for multi-process TSA
    3. Loads data WITHOUT dumping to LLM
    4. PREPROCESSES: normalize, derive metrics, rank candidates
    5. Returns TOP-K candidates per concern type
    6. Caches raw data for drill-down via session handle
    
    PHILOSOPHY:
    - Tool is "evidence curator", not "storyteller"
    - LLM gets structured candidates, not raw grids
    - Pre-computed metrics reduce LLM computation
    - Session enables efficient follow-up questions
    
    CANDIDATE LISTS:
    1. RELIABILITY: Steps with high event_fail_rate (fallout)
    2. IMPACT: Steps causing most UUT failures (causal)
    3. CAPABILITY: Measurements with poor Cpk
    4. INFRASTRUCTURE: Steps with errors/terminations
    5. TIME: Steps with anomalous timing
    
    Example:
        >>> tool = StartTsaTool(api)
        >>> result = tool.start_tsa(StartTsaInput(
        ...     part_number="PCBA-001",
        ...     test_operation="FCT"
        ... ))
        >>> # Returns StartTsaResponse with candidates + session handle
    """
    
    name = "start_tsa"
    description = """
Start a Test Step Analysis (TSA) session for root cause investigation.

WHEN TO USE:
- After yield analysis reveals problems at a specific part+process
- When you need to identify WHICH step is causing failures
- When you need process capability (Cpk) analysis
- When investigating test sequence health

IMPORTANT REQUIREMENTS:
- MUST specify part_number (do not guess - ask user if unknown)
- MUST specify test_operation (do not guess - ask user if unknown)
- Tool will validate and refuse if context is missing

WHAT YOU GET BACK:
- case_id: Reference for this analysis
- dataset_handle: For drill-down requests
- totals: Overall summary (steps, measurements, Cpk distribution)
- candidate_lists: Pre-ranked lists of investigation candidates:
  * RELIABILITY: High failure rate steps
  * IMPACT: Steps causing UUT failures (root cause)
  * CAPABILITY: Low Cpk measurements
  * INFRASTRUCTURE: Error/termination suspects
  * TIME: Timing anomalies
- warnings: Data quality or compatibility issues

NEXT STEPS AFTER CALLING:
1. Review candidate lists by concern type
2. Focus on IMPACT list for root cause (steps causing UUT failures)
3. Check CAPABILITY list for process issues
4. Use dataset_handle for drill-down on specific steps
"""
    
    def __init__(self, api: "pyWATS"):
        """Initialize with pyWATS API instance."""
        self._api = api
        self._session_manager = TsaSessionManager.get_instance()
    
    @staticmethod
    def get_parameters_schema() -> Dict[str, Any]:
        """Get OpenAI-compatible parameter schema."""
        return {
            "type": "object",
            "properties": {
                "part_number": {
                    "type": "string",
                    "description": "Product part number (REQUIRED - do not guess, ask user)"
                },
                "test_operation": {
                    "type": "string",
                    "description": "Test operation name (REQUIRED - do not guess, ask user)"
                },
                "revision": {
                    "type": "string",
                    "description": "Product revision (recommended for clean analysis)"
                },
                "sw_filename": {
                    "type": "string",
                    "description": "Test software filename (recommended to avoid merging)"
                },
                "days": {
                    "type": "integer",
                    "description": "Days of data to analyze (default: 30)",
                    "default": 30
                },
                "run": {
                    "type": "integer",
                    "description": "Run number (default: 1 for first pass)",
                    "default": 1
                },
            },
            "required": ["part_number", "test_operation"]
        }
    
    @classmethod
    def get_definition(cls) -> Dict[str, Any]:
        """Get OpenAI-compatible tool definition."""
        return {
            "name": cls.name,
            "description": cls.description,
            "parameters": cls.get_parameters_schema(),
        }
    
    def start_tsa(self, input_params: StartTsaInput) -> AgentResult:
        """
        Start TSA session with preprocessing and caching.
        
        Args:
            input_params: TSA parameters with required part_number + test_operation
            
        Returns:
            AgentResult with StartTsaResponse or error
        """
        try:
            # Step 0: Validate required context
            validation_error = self._validate_context(input_params)
            if validation_error:
                return validation_error
            
            # Step 1: Check compatibility (if multi-process)
            if input_params.additional_processes:
                compat_error = self._check_compatibility(input_params)
                if compat_error:
                    return compat_error
            
            # Step 2: Load TSA grid from API
            raw_steps, totals = self._load_tsa_grid(input_params)
            
            if not raw_steps:
                return self._no_data_response(input_params)
            
            # Step 3: Create session for caching
            scope = TsaScope(
                part_number=input_params.part_number,
                test_operation=input_params.test_operation,
                revision=input_params.revision,
                sw_filename=input_params.sw_filename,
                days=input_params.days,
                run=input_params.run,
            )
            
            session = self._session_manager.create_session(
                scope=scope,
                raw_steps=raw_steps,
                total_uut_failed=totals.total_uut_failed,
            )
            
            # Step 3: Preprocess and rank candidates
            candidate_lists = self._preprocess_and_rank(raw_steps, totals)
            
            # Build group summary
            group_summary = self._build_group_summary(session)
            
            # Check for data warnings
            warnings = self._check_data_warnings(raw_steps, input_params)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(candidate_lists, totals)
            
            # Build response
            response = StartTsaResponse(
                case_id=session.case_id,
                dataset_handle=session.session_id,
                scope=scope,
                totals=totals,
                capability_coverage={
                    "capable": totals.capable_count,
                    "marginal": totals.marginal_count,
                    "incapable": totals.incapable_count,
                    "critical": totals.critical_count,
                },
                candidate_lists=candidate_lists,
                group_summary=group_summary,
                warnings=warnings,
                recommendations=recommendations,
                expires_at=session.expires_at,
            )
            
            # Build summary for agent
            summary = self._build_summary(response)
            
            return AgentResult.ok(
                data=response.to_dict(),
                summary=summary,
                metadata={
                    "session_id": session.session_id,
                    "case_id": session.case_id,
                    "expires_at": session.expires_at.isoformat(),
                    "total_steps": totals.total_steps,
                    "has_capability_concerns": totals.incapable_count + totals.critical_count > 0,
                    "has_causal_steps": totals.total_caused_uut_fail > 0,
                }
            )
            
        except Exception as e:
            return AgentResult.fail(f"TSA failed: {str(e)}")
    
    def start_tsa_from_dict(self, params: Dict[str, Any]) -> AgentResult:
        """Start TSA from dictionary parameters (for LLM tool calls)."""
        input_params = StartTsaInput(**params)
        return self.start_tsa(input_params)
    
    # =========================================================================
    # Step 0: Context Validation
    # =========================================================================
    
    def _validate_context(self, input_params: StartTsaInput) -> Optional[AgentResult]:
        """
        Validate required context is present.
        
        Returns error if missing, None if valid.
        """
        missing = []
        
        if not input_params.part_number or input_params.part_number.strip() == "":
            missing.append("part_number")
        
        if not input_params.test_operation or input_params.test_operation.strip() == "":
            missing.append("test_operation")
        
        if missing:
            # Return candidates from available data
            suggestions = self._get_context_suggestions()
            
            return AgentResult.fail(
                f"Required context missing: {', '.join(missing)}. "
                f"Please specify before proceeding.",
                error_type="missing_context",
                metadata={
                    "missing_fields": missing,
                    "suggestions": suggestions,
                }
            )
        
        return None
    
    def _get_context_suggestions(self) -> Dict[str, List[str]]:
        """Get suggestions for missing context from API."""
        suggestions = {}
        
        try:
            # Get available test operations
            processes = self._api.process.get_test_operations()
            if processes:
                suggestions["test_operations"] = [
                    p.name for p in processes[:10]
                ]
        except Exception:
            pass
        
        return suggestions
    
    # =========================================================================
    # Step 1: Compatibility Check
    # =========================================================================
    
    def _check_compatibility(self, input_params: StartTsaInput) -> Optional[AgentResult]:
        """
        Check if multi-process TSA is compatible.
        
        Compares sequence signatures to detect incompatible test programs.
        """
        # TODO: Implement signature comparison for multi-process
        # For now, warn but allow
        return None
    
    # =========================================================================
    # Step 2: Load TSA Grid
    # =========================================================================
    
    def _load_tsa_grid(
        self,
        input_params: StartTsaInput
    ) -> Tuple[List["StepAnalysisRow"], TsaTotals]:
        """
        Load TSA data from API without dumping to LLM.
        
        Returns raw steps and computed totals.
        """
        from pywats.domains.report.models import WATSFilter
        
        # Build filter
        filter_params = {
            "part_number": input_params.part_number,
            "test_operation": input_params.test_operation,
            "run": input_params.run,
        }
        
        if input_params.revision:
            filter_params["revision"] = input_params.revision
        if input_params.sw_filename:
            filter_params["sw_filename"] = input_params.sw_filename
        
        # Date handling
        filter_params["date_from"] = datetime.now() - timedelta(days=input_params.days)
        
        wats_filter = WATSFilter(**filter_params)
        
        # Fetch step analysis data
        raw_steps = self._api.analytics.get_test_step_analysis(wats_filter)
        
        # Compute totals
        totals = self._compute_totals(raw_steps)
        
        return raw_steps, totals
    
    def _compute_totals(self, raw_steps: List["StepAnalysisRow"]) -> TsaTotals:
        """Compute overall totals from raw step data."""
        totals = TsaTotals()
        
        cpk_values = []
        
        for step in raw_steps:
            totals.total_steps += 1
            totals.total_executions += step.step_count or 0
            
            # Step-level failures
            totals.total_step_failures += step.step_failed_count or 0
            totals.total_caused_uut_fail += step.step_caused_uut_failed or 0
            
            # Cpk distribution
            if step.cpk is not None:
                totals.total_measurements += 1
                cpk_values.append(step.cpk)
                
                if step.cpk >= CPK_CAPABLE:
                    totals.capable_count += 1
                elif step.cpk >= CPK_MARGINAL:
                    totals.marginal_count += 1
                elif step.cpk >= CPK_CRITICAL:
                    totals.incapable_count += 1
                else:
                    totals.critical_count += 1
        
        # Estimate UUT totals from step data
        # Note: This is approximate - ideally we'd query UUT data separately
        if raw_steps:
            # Use max step count as proxy for UUT count
            max_count = max((s.step_count or 0) for s in raw_steps)
            totals.total_uut_tested = max_count
            totals.total_uut_failed = totals.total_caused_uut_fail
        
        # Average Cpk
        if cpk_values:
            totals.avg_cpk = sum(cpk_values) / len(cpk_values)
        
        # Overall pass rate
        if totals.total_executions > 0:
            passed = totals.total_executions - totals.total_step_failures
            totals.overall_pass_rate = (passed / totals.total_executions) * 100
        
        return totals
    
    # =========================================================================
    # Step 3: Preprocessing and Ranking
    # =========================================================================
    
    def _preprocess_and_rank(
        self,
        raw_steps: List["StepAnalysisRow"],
        totals: TsaTotals
    ) -> List[TsaCandidateList]:
        """
        Preprocess step data and produce ranked candidate lists.
        
        This is the core "evidence curator" logic.
        """
        # 3A: Convert to candidates with computed metrics
        candidates = [
            self._step_to_candidate(step, totals)
            for step in raw_steps
        ]
        
        # 3B-3C: Produce ranked lists for each concern type
        lists = []
        
        # RELIABILITY: High event failure rate
        reliability = self._rank_by_reliability(candidates)
        lists.append(reliability)
        
        # IMPACT: High causal rate (root cause)
        impact = self._rank_by_impact(candidates)
        lists.append(impact)
        
        # CAPABILITY: Poor Cpk
        capability = self._rank_by_capability(candidates)
        lists.append(capability)
        
        # INFRASTRUCTURE: Errors and terminations
        infra = self._rank_by_infrastructure(candidates)
        lists.append(infra)
        
        # TIME: Anomalous timing (placeholder)
        time_anomalies = self._rank_by_time(candidates)
        lists.append(time_anomalies)
        
        return lists
    
    def _step_to_candidate(
        self,
        step: "StepAnalysisRow",
        totals: TsaTotals
    ) -> TsaCandidate:
        """Convert raw step to candidate with computed metrics."""
        step_count = step.step_count or 0
        step_failed = step.step_failed_count or 0
        step_error = step.step_error_count or 0
        step_terminated = step.step_terminated_count or 0
        caused_failed = step.step_caused_uut_failed or 0
        
        # Compute rates
        event_fail_rate = (step_failed / step_count * 100) if step_count > 0 else 0.0
        
        causal_rate = 0.0
        if totals.total_uut_failed > 0 and caused_failed > 0:
            causal_rate = (caused_failed / totals.total_uut_failed) * 100
        
        infra_suspect = step_error + step_terminated
        infra_suspect_rate = (infra_suspect / step_count * 100) if step_count > 0 else 0.0
        
        # Cpk status
        cpk_status = None
        if step.cpk is not None:
            if step.cpk >= CPK_CAPABLE:
                cpk_status = "capable"
            elif step.cpk >= CPK_MARGINAL:
                cpk_status = "marginal"
            elif step.cpk >= CPK_CRITICAL:
                cpk_status = "incapable"
            else:
                cpk_status = "critical"
        
        return TsaCandidate(
            step_name=step.step_name or "Unknown",
            step_path=step.step_path or "",
            step_type=step.step_type,
            step_group=step.step_group,
            step_count=step_count,
            step_passed=step.step_passed_count or 0,
            step_failed=step_failed,
            step_error=step_error,
            step_terminated=step_terminated,
            caused_uut_failed=caused_failed,
            event_fail_rate=round(event_fail_rate, 2),
            causal_rate=round(causal_rate, 2),
            infra_suspect_rate=round(infra_suspect_rate, 2),
            cpk=step.cpk,
            cpk_status=cpk_status,
            avg=step.avg,
            stdev=step.stdev,
            limit_low=step.limit1,
            limit_high=step.limit2,
            avg_time_ms=step.step_time_avg,
        )
    
    def _rank_by_reliability(self, candidates: List[TsaCandidate]) -> TsaCandidateList:
        """Rank by event failure rate (fallout)."""
        # Filter to steps with failures
        failing = [c for c in candidates if c.step_failed > 0]
        
        # Sort by failure rate descending
        failing.sort(key=lambda c: c.event_fail_rate, reverse=True)
        
        # Take top K
        top_k = failing[:TOP_K_RELIABILITY]
        
        # Add rank info
        for i, c in enumerate(top_k, 1):
            c.rank = i
            c.rank_reason = f"{c.event_fail_rate:.1f}% fail rate ({c.step_failed}/{c.step_count})"
        
        return TsaCandidateList(
            concern_type="reliability",
            title="Reliability Failures (High Event Rate)",
            count=len(failing),
            candidates=top_k,
        )
    
    def _rank_by_impact(self, candidates: List[TsaCandidate]) -> TsaCandidateList:
        """Rank by causal rate (steps causing UUT failures)."""
        # Filter to steps causing UUT failures
        causal = [c for c in candidates if c.caused_uut_failed > 0]
        
        # Sort by caused failures descending
        causal.sort(key=lambda c: c.caused_uut_failed, reverse=True)
        
        # Take top K
        top_k = causal[:TOP_K_IMPACT]
        
        # Add rank info
        for i, c in enumerate(top_k, 1):
            c.rank = i
            c.rank_reason = f"Caused {c.caused_uut_failed} UUT failures ({c.causal_rate:.1f}% of total)"
        
        return TsaCandidateList(
            concern_type="impact",
            title="Impact (Root Cause - Steps Causing UUT Failures)",
            count=len(causal),
            candidates=top_k,
        )
    
    def _rank_by_capability(self, candidates: List[TsaCandidate]) -> TsaCandidateList:
        """Rank by Cpk (worst capability first)."""
        # Filter to measurements with Cpk
        with_cpk = [c for c in candidates if c.cpk is not None]
        
        # Sort by Cpk ascending (worst first)
        with_cpk.sort(key=lambda c: c.cpk if c.cpk is not None else 999)
        
        # Take top K (worst)
        top_k = with_cpk[:TOP_K_CAPABILITY]
        
        # Add rank info
        for i, c in enumerate(top_k, 1):
            c.rank = i
            status_emoji = {
                "critical": "[CRITICAL]",
                "incapable": "[INCAPABLE]",
                "marginal": "[MARGINAL]",
                "capable": "[OK]",
            }.get(c.cpk_status or "", "")
            c.rank_reason = f"Cpk={c.cpk:.2f} {status_emoji}"
        
        return TsaCandidateList(
            concern_type="capability",
            title="Capability Concerns (Low Cpk Measurements)",
            count=len([c for c in with_cpk if (c.cpk or 999) < CPK_CAPABLE]),
            candidates=top_k,
        )
    
    def _rank_by_infrastructure(self, candidates: List[TsaCandidate]) -> TsaCandidateList:
        """Rank by infrastructure issues (errors + terminations)."""
        # Filter to steps with infra issues
        infra = [c for c in candidates if c.step_error > 0 or c.step_terminated > 0]
        
        # Sort by infra suspect rate descending
        infra.sort(key=lambda c: c.infra_suspect_rate, reverse=True)
        
        # Take top K
        top_k = infra[:TOP_K_INFRA]
        
        # Add rank info
        for i, c in enumerate(top_k, 1):
            c.rank = i
            c.rank_reason = f"{c.step_error} errors, {c.step_terminated} terminated"
        
        return TsaCandidateList(
            concern_type="infrastructure",
            title="Infrastructure Suspects (Errors/Terminations)",
            count=len(infra),
            candidates=top_k,
        )
    
    def _rank_by_time(self, candidates: List[TsaCandidate]) -> TsaCandidateList:
        """Rank by timing anomalies."""
        # Filter to steps with timing data
        with_time = [c for c in candidates if c.avg_time_ms is not None and c.avg_time_ms > 0]
        
        # Sort by time descending (slowest first)
        with_time.sort(key=lambda c: c.avg_time_ms or 0, reverse=True)
        
        # Take top K
        top_k = with_time[:TOP_K_TIME]
        
        # Add rank info
        for i, c in enumerate(top_k, 1):
            c.rank = i
            time_str = f"{c.avg_time_ms:.1f}ms" if c.avg_time_ms else "N/A"
            c.rank_reason = f"Avg time: {time_str}"
        
        return TsaCandidateList(
            concern_type="time",
            title="Time Analysis (Slowest Steps)",
            count=len(with_time),
            candidates=top_k,
        )
    
    # =========================================================================
    # Supporting Methods
    # =========================================================================
    
    def _build_group_summary(self, session: TsaSession) -> List[TsaGroupSummary]:
        """Build summary of step groups for navigation."""
        summaries = []
        
        for group_name, steps in session.steps_by_group.items():
            failure_count = sum(s.step_failed_count or 0 for s in steps)
            measurement_count = sum(1 for s in steps if s.cpk is not None)
            
            cpk_values = [s.cpk for s in steps if s.cpk is not None]
            worst_cpk = min(cpk_values) if cpk_values else None
            has_critical = any(s.step_caused_uut_failed and s.step_caused_uut_failed > 0 for s in steps)
            
            summaries.append(TsaGroupSummary(
                group_name=group_name,
                step_count=len(steps),
                failure_count=failure_count,
                measurement_count=measurement_count,
                worst_cpk=worst_cpk,
                has_critical=has_critical,
            ))
        
        # Sort by criticality
        summaries.sort(key=lambda s: (not s.has_critical, s.failure_count * -1))
        
        return summaries
    
    def _check_data_warnings(
        self,
        raw_steps: List["StepAnalysisRow"],
        input_params: StartTsaInput
    ) -> List[str]:
        """Check for data quality warnings."""
        warnings = []
        
        # Check for multiple SW versions
        sw_versions = set()
        revisions = set()
        
        for step in raw_steps:
            # Note: These aren't in StepAnalysisRow, would need separate check
            pass
        
        if len(sw_versions) > 1:
            warnings.append(
                f"Multiple SW versions detected ({len(sw_versions)}). "
                "Consider filtering to specific sw_filename for clean analysis."
            )
        
        if len(revisions) > 1:
            warnings.append(
                f"Multiple product revisions detected ({len(revisions)}). "
                "Consider filtering to specific revision."
            )
        
        # Check for low sample counts
        low_sample_steps = [s for s in raw_steps if (s.step_count or 0) < 10]
        if len(low_sample_steps) > len(raw_steps) * 0.5:
            warnings.append(
                "Many steps have low sample counts (<10). "
                "Results may not be statistically significant."
            )
        
        return warnings
    
    def _generate_recommendations(
        self,
        candidate_lists: List[TsaCandidateList],
        totals: TsaTotals
    ) -> List[str]:
        """Generate recommendations based on analysis."""
        recommendations = []
        
        # Check impact list (root cause)
        impact_list = next((cl for cl in candidate_lists if cl.concern_type == "impact"), None)
        if impact_list and impact_list.candidates:
            top = impact_list.candidates[0]
            recommendations.append(
                f"PRIORITY: Investigate '{top.step_name}' which caused "
                f"{top.caused_uut_failed} UUT failures ({top.causal_rate:.1f}% of total)."
            )
        
        # Check capability
        if totals.critical_count > 0:
            recommendations.append(
                f"URGENT: {totals.critical_count} measurements have CRITICAL Cpk (<{CPK_CRITICAL}). "
                "High defect rate expected."
            )
        elif totals.incapable_count > 0:
            recommendations.append(
                f"ACTION: {totals.incapable_count} measurements have low Cpk (<{CPK_MARGINAL}). "
                "Review test limits or process parameters."
            )
        
        # Check infrastructure
        infra_list = next((cl for cl in candidate_lists if cl.concern_type == "infrastructure"), None)
        if infra_list and infra_list.count > 0:
            recommendations.append(
                f"INVESTIGATE: {infra_list.count} steps with errors/terminations may indicate "
                "equipment or test code issues."
            )
        
        if not recommendations:
            recommendations.append(
                "Process appears healthy. Continue monitoring for trending changes."
            )
        
        return recommendations
    
    def _build_summary(self, response: StartTsaResponse) -> str:
        """Build human-readable summary for agent."""
        lines = [
            f"TSA Session Started: {response.case_id}",
            f"Scope: {response.scope.part_number} - {response.scope.test_operation} "
            f"(last {response.scope.days} days)",
            "",
            "=== TOTALS ===",
            f"- Steps: {response.totals.total_steps}",
            f"- Measurements: {response.totals.total_measurements}",
            f"- Caused UUT Failures: {response.totals.total_caused_uut_fail}",
        ]
        
        if response.totals.avg_cpk is not None:
            lines.append(f"- Average Cpk: {response.totals.avg_cpk:.2f}")
        
        lines.append("")
        lines.append("=== CANDIDATE SUMMARY ===")
        
        for cl in response.candidate_lists:
            if cl.candidates:
                lines.append(f"- {cl.title}: {cl.count} total, top {len(cl.candidates)} shown")
        
        if response.warnings:
            lines.append("")
            lines.append("=== WARNINGS ===")
            for w in response.warnings:
                lines.append(f"- {w}")
        
        if response.recommendations:
            lines.append("")
            lines.append("=== RECOMMENDATIONS ===")
            for r in response.recommendations:
                lines.append(f"- {r}")
        
        lines.append("")
        lines.append(f"Dataset handle for drill-down: {response.dataset_handle}")
        
        return "\n".join(lines)
    
    def _no_data_response(self, input_params: StartTsaInput) -> AgentResult:
        """Return response when no data found."""
        return AgentResult.fail(
            f"No step data found for {input_params.part_number} - "
            f"{input_params.test_operation} in the last {input_params.days} days.",
            error_type="no_data",
            metadata={
                "part_number": input_params.part_number,
                "test_operation": input_params.test_operation,
                "days": input_params.days,
                "suggestions": [
                    "Check part number spelling",
                    "Check test operation name",
                    "Try increasing the days parameter",
                    "Verify data exists in WATS for this combination",
                ]
            }
        )


# =============================================================================
# Tool Definition Export
# =============================================================================

def get_start_tsa_tool_definition() -> Dict[str, Any]:
    """Get OpenAI tool definition for start_tsa."""
    return {
        "name": StartTsaTool.name,
        "description": StartTsaTool.description,
        "parameters": StartTsaTool.get_parameters_schema(),
    }
