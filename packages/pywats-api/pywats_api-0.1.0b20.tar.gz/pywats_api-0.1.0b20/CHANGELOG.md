# Changelog

All notable changes to PyWATS will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0b20] - 2025-12-22

### Changed
- Beta version bump for ongoing development

## [0.1.0b19] - 2025-12-21

### Changed
- **Agent tool surface unified** - single canonical executor/tool interface (removed internal v1/v2 naming)
- **Wrapped tool module renamed** - internal wrapper module renamed to non-versioned name
- **Experimental TSA module renamed** - experimental TSA implementation renamed to non-versioned module

### Fixed
- **Tool result robustness** - tool execution guardrails to avoid blank/no-response outcomes (summary always present; empty data treated as explicit no-data)
- **Mypy configuration** - corrected `tool.mypy.python_version` to a real Python version

## [0.1.0b17] - 2025-12-21

### Added
- **Agent execution core** - LLM-safe tool results via bounded envelopes + out-of-band data handles
- **DynamicYield filter support** - Added misc-info and asset filter fields to `WATSFilter`

### Changed
- **Agent public API (BETA)** - canonical exports (breaking changes by design)

## [0.1.0b15] - 2025-12-21

### Fixed
- **Agent package bundling** - `pywats_agent` is now properly included in `pywats-api` package
  - Agent tools available via `from pywats_agent.tools import ...`
  - No separate package installation required

## [0.1.0b14] - 2025-12-21

### Fixed
- **Missing type imports** - Added missing `Any` imports to asset and product service modules
  - Fixed F821 linting errors that were blocking CI

### Added
- **Pre-release validation script** - New `scripts/pre_release_check.ps1` to catch errors before releasing
  - Runs flake8 linting checks (same as CI)
  - Optionally runs full test suite
  - Use `.\scripts\pre_release_check.ps1` before every release

## [0.1.0b12] - 2025-12-21

### Fixed
- **Import path issues** - Resolved package shadowing and import errors
  - Removed stale `src/pywats_agent/` directory that shadowed the correct package location
  - Fixed test imports to use public API (`pywats_agent.tools`) instead of internal paths (`pywats_agent.tools.shared.*`)
  - Added missing exports to `pywats_agent.tools.__init__.py` (TemporalMatrix, DeviationMatrix, DeviationCell, session creators)
  - All 877 tests now pass (589 agent tests + 288 API tests)

## [0.1.0b11] - Previous Release

### Added

- **Agent Autonomy System** - Configurable rigor and write safety controls
  - `AnalyticalRigor` enum: QUICK, BALANCED, THOROUGH, EXHAUSTIVE
    - Controls how thorough analytics operations are (data gathering, cross-validation)
    - Affects system prompt instructions and default parameters
  - `WriteMode` enum: BLOCKED, CONFIRM_ALL, CONFIRM_DESTRUCTIVE
    - Controls whether write operations (POST/PUT/DELETE) are allowed
    - Enforces confirmation requirements for mutations
  - `AgentConfig` class for unified configuration
    - `get_system_prompt()` - Generates rigor/write mode instructions
    - `get_default_parameters(rigor)` - Returns sample sizes scaled by rigor
    - `allows_write(operation)` - Checks if write operation is permitted
    - `requires_confirmation(operation)` - Checks if confirmation needed
  - 6 presets for common scenarios:
    - `viewer` - Read-only analytics, writes blocked
    - `quick_check` - Fast spot-checks, writes blocked  
    - `investigation` - Balanced analysis (default)
    - `audit` - Maximum thoroughness, all writes confirmed
    - `admin` - Balanced analysis with full write access
    - `power_user` - Quick analysis with full write access
  - `AgentContext` integration - Config flows through context to agent
  - 33 unit tests

- **Visualization Sidecar System** - Optional rich visualization for UI
  - `VisualizationPayload` - Bypasses LLM context, goes directly to UI
  - `VizBuilder` - Fluent builder for common chart types:
    - `line_chart()`, `area_chart()`, `bar_chart()` - Trends and comparisons
    - `pie_chart()`, `pareto_chart()` - Distribution analysis
    - `control_chart()` - SPC with UCL/LCL/target lines
    - `heatmap()`, `histogram()`, `scatter()` - Advanced analysis
    - `table()`, `kpi()`, `kpi_row()`, `dashboard()` - Data display
  - Reference lines, annotations, and drill-down support
  - `AgentResult.viz_payload` - Optional field (UI infers from data when absent)
  - `to_openai_response()` excludes viz (saves tokens)
  - `to_ui_response()` includes viz (for frontend rendering)
  - 37 unit tests

## [0.1.0b10] - 2025-12-20

### Added

- **UnitAnalysisTool** - Comprehensive individual unit analysis
  - Complete test history and status determination for any serial number
  - Production/MES tracking information (phase, batch, location)
  - Unit verification and grading (when rules configured)
  - Sub-unit (component) tracking from production and test reports
  - Multiple analysis scopes: quick, standard, full, history, verify
  - Status classification: passing, failing, in_progress, repaired, scrapped
  - 40+ unit tests

- **ControlPanelTool** - Unified administrative tool for managing WATS configuration
  - Single tool handles 5 domains: Asset, Product, Production, Software, Process
  - 12 operation types: list, get, search, create, update, delete, domain-specific
  - Entity support: assets, types, products, revisions, units, phases, packages, folders
  - Comprehensive input validation and confirmation for destructive operations
  - 50+ unit tests covering all domains and operations

- **SubUnitAnalysisTool** - Deep analysis of sub-unit (component) relationships
  - Uses query_header endpoint with OData expansion for efficient bulk queries
  - 4 query types:
    - `filter_by_subunit`: Find parent units containing a specific component
    - `get_subunits`: Get all sub-units for filtered parent reports
    - `statistics`: Aggregate sub-unit counts by type/part number/revision
    - `deviation`: Detect parents with missing, extra, or unexpected sub-units
  - Supports both UUT and UUR report types
  - Automatic baseline inference for deviation detection
  - 25 unit tests

- **Report Service Enhancements** - Extended query_header capabilities
  - OData $expand support for sub-units, misc info, assets, attachments
  - New service methods: `query_headers_with_subunits()`, `query_headers_by_subunit_part_number()`, `query_headers_by_subunit_serial()`
  - Support for OData $filter, $top, $orderby, $skip parameters

- **Report Models** - New models for expanded header data
  - `HeaderSubUnit`: serial_number, part_number, revision, part_type
  - `HeaderMiscInfo`: description, value
  - `HeaderAsset`: serial_number, running_count, total_count, calibration info

## [0.1.0b8] - 2025-12-19

### Added

- **Agent Tools in Main Package** - `pywats_agent` is now included in `pywats-api`
  - Install with `pip install pywats-api[agent]` for explicit dependency
  - Or just `pip install pywats-api` - agent tools are always included, no extra deps needed
  - LangChain integration available with `pip install pywats-api[langchain]`

### Fixed

- **Tool Selection Patterns** - Fixed regex patterns in `AgentTestHarness`
  - Added `\bwhat.?step\b` pattern for "What step is causing..." queries
  - Added `\bstep.*caus` pattern for step causation queries
  - Fixed plural forms `measurements?` for individual/raw measurements

## [0.1.0b7] - 2025-12-19

### Added

- **Agent Analysis Tools** (`pywats_agent.tools`) - Comprehensive root cause analysis workflow
  - **ProcessCapabilityTool** - Advanced SPC with:
    - Dual Cpk analysis (Cpk vs Cpk_wof - with/without failures)
    - Stability assessment before trusting Cpk values
    - Hidden mode detection (outliers, trends, drift, bimodal, centering, approaching limits)
    - Improvement priority matrix (critical → high → medium → low)
  - **StepAnalysisTool** - Test Step Analysis (TSA) for:
    - Root cause identification (steps causing unit failures)
    - Process capability (Cpk) analysis per measurement
    - Data integrity checks for SW versions and revisions
  - **DimensionalAnalysisTool** - Failure mode detection across dimensions:
    - Station, operator, fixture, batch, SW version analysis
    - Statistical significance assessment
    - Prioritized recommendations
  - **AdaptiveTimeFilter** - Dynamic time windows for varying production volumes:
    - Automatically adjusts query window based on volume
    - Prevents query overload for high-volume customers
  - **ProcessResolver** - Fuzzy matching for process/test operation names:
    - Handles imprecise user input ("PCBA" → "PCBA test")
    - Common alias expansion
    - Diagnoses mixed-test process issues

- **Documentation** - Enhanced domain knowledge documentation:
  - Process Capability Analysis section in WATS_DOMAIN_KNOWLEDGE.md
  - Workflow examples in YIELD_METRICS_GUIDE.md
  - Dual Cpk interpretation guide

## [0.1.0b6] - 2025-12-18

### Added

- **Request Throttling** - Built-in rate limiting to comply with WATS API limits (500 requests/minute)
  - New `RateLimiter` class with sliding window algorithm
  - Thread-safe implementation for concurrent usage
  - Configurable via `configure_throttling()` function
  - Can be disabled for testing with `configure_throttling(enabled=False)`
  - Statistics tracking (total requests, wait time, throttle count)

- **Analytics Typed Models** - New Pydantic models for analytics responses
  - `TopFailedStep` - Failed step statistics
  - `RepairStatistics` - Repair loop metrics
  - `RepairHistoryRecord` - Individual repair records
  - `MeasurementData` - Measurement values with statistics
  - `AggregatedMeasurement` - Time-series measurement aggregations
  - `OeeAnalysisResult` - OEE (Overall Equipment Effectiveness) analysis

- **Analytics Documentation** - Added docstrings with examples to all 23 analytics service methods

### Fixed

- **RootCause Acceptance Tests** - Fixed `DummyRootCauseRepository` to properly inherit from `RootCauseRepository`

## [0.1.0b5] - 2025-12-17

### Fixed

- **CI/CD** - Added `contents: read` permission to publish workflow for private repo checkout.

## [0.1.0b4] - 2025-12-17

### Fixed

- **Release pipeline** - Fixed flake8 `F821` (missing `Path` import) blocking the PyPI publish workflow.

## [0.1.0b3] - 2025-12-17

### Fixed

- **Cross-platform packaging** - Corrected package directory casing to `src/pywats` to avoid Linux/macOS import/install issues.
- **Release hygiene** - Ensured `tests/`, `docs/`, and other dev-only folders are excluded from PyPI artifacts and added publish-time guards.
- **UUT report parsing robustness** - Added a safe fallback for unknown step types and improved tolerance for null numeric values.
- **Query filtering** - Normalized `status=all` to omit the status filter (treat as “no status filter”).

## [0.1.0b2] - 2025-12-15

### Changed

- **Architecture Refactoring** - Internal API separation
  - All internal endpoint implementations now in separate `_internal` files
  - New `AssetRepositoryInternal` and `AssetServiceInternal` for file operations
  - New `ProductionRepositoryInternal` and `ProductionServiceInternal` for MES operations
  - Public repositories delegate to internal repositories for internal endpoints
  - Added `api.asset_internal` for asset file operations (upload, download, list, delete)
  - Added `api.production_internal` for MES unit phases

### Fixed

- CompOp export path handling for None values
- TestInstanceConfig field mapping for process_code/test_operation

## [0.1.0b1] - 2025-12-14

### Added

- **PyWATS API Library** (`pywats`)
  - Product management (get, create, update products and revisions)
  - Asset management (equipment tracking, calibration, maintenance)
  - Report submission and querying (UUT/UUR reports in WSJF format)
  - Production/serial number management (units, batches, assemblies)
  - RootCause ticket system (issue tracking and resolution)
  - Software distribution (package management, releases)
  - Statistics and analytics endpoints
  - Station concept for multi-station deployments

- **PyWATS Client Application** (`pywats_client`)
  - Desktop GUI mode (PySide6/Qt)
  - Headless mode for servers and embedded systems (Raspberry Pi)
  - Connection management with encrypted token storage
  - Converter framework for custom file format processing
  - Report queue with offline support
  - HTTP control API for remote management

- **Developer Features**
  - Comprehensive type hints throughout
  - Pydantic models for data validation
  - Structured logging with debug mode
  - Async-ready architecture

### Requirements

- Python 3.10 or later
- **WATS Server 2025.3.9.824 or later**

### Notes

This is a **beta release**. The API is stabilizing but may have breaking changes
before the 1.0 release. Please report issues on GitHub.

---

## Version History

| Version | Date | Status |
|---------|------|--------|
| 0.1.0b2 | 2025-12-15 | Beta - Architecture refactoring |
| 0.1.0b1 | 2025-12-14 | Beta - Initial public release |
