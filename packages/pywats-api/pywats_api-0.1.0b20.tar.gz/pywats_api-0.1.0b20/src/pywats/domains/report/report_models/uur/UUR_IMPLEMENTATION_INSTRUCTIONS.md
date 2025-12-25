# UUR (Unit Under Repair) Report Model – Structure & Creation Flow

This document summarizes how the Interface.TDM UUR (Unit Under Repair) reporting classes work together, how
validation operates, and the dual relationships between repair (UUR) context and the originating test (UUT)
context (process codes & report GUIDs). It is intended to support implementing / aligning a Python API model.

---
## 1. Core Object Model

| Concept | Class | WRML Element | Notes |
|---------|-------|--------------|-------|
| Base report abstraction | `Report` | `WATSReport` | Shared by UUT (`UUTReport`) and UUR (`UURReport`). Handles file persistence, timing, validation scaffolding. |
| UUR (repair) report | `UURReport` | `WATSReport` (`type = UUR`) + `UUR_type` header | Contains repair meta + failures + part hierarchy + misc repair fields + attachments. |
| Repair type definition | `RepairType` | `Process` (IsRepairOperation) + embedded `Models.RepairType` | Provides fail‑code tree (categories + fail codes), misc info definitions, masks, UUT required, component ref regex. |
| Fail code category / leaf | `FailCode` | Category or Failcode node in definition | Category (non‑selectable) vs selectable (fc.Status > 0). Tree exposed via `GetRootFailcodes` / `GetChildFailCodes`. |
| Misc repair info collection | `MiscUURInfoColletion` | `MiscInfo_type[]` | Ordered, indexer by ordinal or description; each element has regex / allowed list validation. |
| Individual misc repair info | `MiscUURInfo` | `MiscInfo_type` | Wraps definition + instance value (validated on submit). |
| Part / sub‑unit entry | `UURPartInfo` | `ReportUnitHierarchy_type` | Index 0 represents the MAIN unit (mirrors UUT PN/SN/REV). Additional indices describe subparts replaced / repaired. |
| Failure instance | `Failure` | `Failures_type` | Linked to part index (0 = main), references fail code GUID; may contain attachments. |
| Attachment (repair or failure) | `UURAttachment` | `Binary_type` | At report level (no `FailIdx`) or per failure (`FailIdxSpecified`). |

---
## 2. Dual Process / GUID Semantics

A UUR report simultaneously references:

1. The **repair process** (the selected `RepairType`).
   * Stored in `reportRow.Process` (top level `WATSReport.Process`).
   * Set in constructor of `UURReport` via the passed `RepairType` (uses its `Code`).

2. The **original test operation** (the process where the UUT failed or is being verified against).
   * Stored inside `uurHeader.Process` (the embedded `UUR_type.Process`).
   * Exposed/controlled by the `OperationType` property (maps to underlying test process).

3. Two conceptually distinct GUIDs:
   * `Report.ReportId` – the UUR report’s own GUID (new unless replacing).
   * `UURReport.UUTGuid` – the GUID of the referenced UUT report being repaired (parsed from `UUR_type.ReferencedUUT`).

Thus: Repair submission carries both the repair context (what kind of repair activity this is) and the original test
context (what operation the tested unit belonged to). The Python model must keep both mappings explicit.

---
## 3. Construction Flow (Creating a UURReport)

Typical creation (simplified):

```
var uur = new UURReport(api, repairType, uutReport, operationType, operatorName)
```

Internally the constructor:
1. Sets `reportRow.type = UUR`.
2. Sets top-level `reportRow.Process` to the **repairType** (repair process code).
3. Creates `uurHeader` (`UUR_type`):
   * Sets `uurHeader.Process` to the **test operation type** (original test process code – short parsed from operationType.Code).
   * Sets operator (`UserLoginName`), flags `Active = true`.
4. Inserts `uurHeader` as `reportRow.Item`.
5. Builds `MiscInfo` collection from `repairType.repairtype.MiscInfos` definitions.
6. Adds MAIN unit part info as a `ReportUnitHierarchy_type` with `Idx = 0` using the current report’s PN/SN/REV.

If loading from existing WRML (`UURReport(TDM, WATSReport)`):
* Resolves the `RepairType` by code or name.
* Re-hydrates misc infos by matching GUID ids.
* Loads existing failures.
* Reuses the embedded `UUR_type` header.

---
## 4. Part Hierarchy & Failure Mapping

### 4.1 Part Indices
* Index 0 always = main (root) unit (even if its serial appears blank in a subunit failure context in external usage descriptions).
* Additional subparts are added via `AddUURPartInfo` – they get sequential indices and `ParentIDX = 0` (single-level hierarchy in current code).
* Replacement logic: `ReplacedIDX` can indicate which prior part index is replaced.

### 4.2 Failure Association
Failures (`Failures_type`) are stored in `reportRow.Items` with:
* `Idx` – internal failure incremental counter.
* `PartIdx` – which part entry (0 = main) the failure belongs to.
* `Failcode` – GUID string of fail code (leaf).
* `Category` / `Code` – denormalized textual metadata (copied from fail code + its parent category). 

Two helper paths:
* Main unit failure: `UURReport.AddFailure(FailCode, componentRef, comment, stepOrderNumber)` – wraps internal `AddFailure(failCode, componentRef, 0)`.
* Subpart failure: `UURPartInfo.AddFailure` – uses that subpart’s `Idx` when calling internal `UURReport.AddFailure`.

Important nuance from your note: In WRML export the **SubUnit (ReportUnitHierarchy_type)** collection is how context is established; a failure pointing to a part index whose subunit has blank serial can semantically mean the main unit (blank SN allowed upstream). The C# model enforces main unit identity at creation (idx 0 with actual PN/SN/REV), but your Python layer can allow blank serial representation if ingesting external data—still mapping it to index 0.

### 4.3 Linking to Test Steps
* `Failure.FailedStepOrderNumber` stored in `failRow.StepID` ties the failure back to a UUT test step order.
* This aligns the dual model: UUR shows repair categorization while still traceable to original test execution context.

### 4.4 Attachments
* Report-level attachments: `Binary_type` with NO `FailIdxSpecified`.
* Failure-level attachments: `Binary_type` with `FailIdxSpecified = true` and `FailIdx = failure.Idx`.

---
## 5. Fail Code Tree & Selection

Fail codes come from `RepairTypeSelected.repairtype.Categories`:
* Categories: non-selectable containers (Selectable = false).
* Failcodes: leaves (Selectable = fc.Status > 0).
* Exposed methods:
  * `GetRootFailcodes()` – top-level nodes (categories).
  * `GetChildFailCodes(FailCode parent)` – children beneath a category or nested node.
  * `GetFailCode(Guid)` – searches categories then their failcodes; returns wrapper.

Validation when adding a failure:
* Confirms the provided fail code GUID belongs under some category for this repair type.
* Throws if not found: ensures integrity across repair type boundaries.

---
## 6. Misc Repair Information (Structured Fields)

Each `MiscUURInfo` definition contains:
* `Description` – human key.
* `ValidRegularExpression` (may also encode multiple alternatives separated by `;`).
* `InputMask` – UI hint.

On submission (`Report.ValidateForSubmit`):
* Iterates over `UURReport.MiscInfo`:
  * If value not empty: must match regex OR one of the literal tokens derived from splitting regex string by `;` (code treats both patterns & enumerations).
  * If value empty: checks whether empty string matches regex; if not, error that field cannot be blank.
* Valid misc infos are assigned incremental `idx` and inserted into `reportRow.Items` unless already present.
* Accumulates `ReportValidationResult` errors and throws `WATSReportValidationException` if any fail.

Python model tip: Represent each definition with (id, description, pattern, allowed_literals, required_flag) precompiled to accelerate validation.

---
## 7. Time & Metadata Semantics

Base `Report` handles multiple time representations:
* `StartDateTimeOffset` (authoritative with timezone).
* `StartDateTime` (local) and `StartDateTimeUTC` (UTC) – harmonized in `ValidateReportRow`.
* For UUR: `Confirmed`, `Finalized`, `ExecutionTime` captured in `uurHeader`.
  * If `Finalized < StartDateTimeUTC`, it is normalized to `DateTime.UtcNow` during validation.

---
## 8. Validation Pipeline for UUR

Call sequence before enqueueing / saving:
1. Business construction ensures mandatory structural items (main PartInfo idx 0, header, etc.).
2. `Report.ValidateReport()` – adjusts times, truncations (generic). 
3. `Report.ValidateForSubmit()` – domain logic:
   * UUR: finalize timestamp correction; misc info validation; (failures assumed correct because added through controlled API); part hierarchy consistency implied.
   * Throws `WATSReportValidationException` containing all field errors.
4. `SaveToFile()` → sets transfer status and persists XML (WRML subset) for transfer service.

---
## 9. File / Transfer Semantics

* Each report serialized as `Reports` container with a single `WATSReport` entry.
* File naming: `<ReportId>.<ReportTransferStatus>` (e.g. `GUID.Queued`).
* Status transitions rename the file – important for any external file watcher (Python ingestion should replicate if simulating client).

Transfer statuses (enum): `InMemory`, `Queued`, `Transfering`, `Error`, `InvalidReport`.

---
## 10. Edge & Special Cases

| Scenario | Handling / Impact |
|----------|-------------------|
| Missing or invalid fail code on add | Immediate exception – cannot create dangling failure. |
| Blank misc info where regex forbids blank | Validation exception before submission. |
| Duplicate misc description names | Indexer by description would throw (Single). Assumed unique per definition. |
| Large attachment | Size check against `api.proxy.MaxAttachmentFileSize`; throws if exceeded. |
| Failure attachments vs report attachments | Distinguished solely by presence of `FailIdxSpecified`. |
| Replacing a report | Caller sets `ReportId` manually before save; file naming logic will use given GUID. |
| Referenced UUT GUID missing/invalid | `UUTGuid` property returns `Guid.Empty`; caller must assign if required by repair type (`RepairType.UUTRequired`). |

---
## 11. Suggested Python Model Mapping

| Python Layer | C# Mapping | Notes |
|--------------|-----------|-------|
| RepairProcessContext | `RepairType` (code, id, name) | plus component ref mask info. |
| TestProcessContext | `OperationType` (original test) | store both codes for dual mapping. |
| UURHeader | `UUR_type` + top-level `WATSReport.Process` | split fields: repair_process_code, test_process_code, operator, times. |
| Parts list | `ReportUnitHierarchy_type[]` | enforce idx 0 main unit, allow optional blank input but hydrate PN/SN if known. |
| Failures list | `Failures_type[]` | include part_index, step_order, component_ref, failcode_id, plus attachments. |
| Misc fields | `MiscUURInfo[]` + definitions | precompile regex + emptiness rule. |
| Attachments | `Binary_type[]` | keyed by (failure_idx or report). |
| Validation | Mirror `ValidateForSubmit` rules | accumulate all errors. |

---
## 12. High-Level Creation Algorithm (Pseudo)

```
create_uut_report(...) -> obtain uut_report_guid, pn, sn, rev, operation_process_code
select repair_type
select test_operation_type (may differ from repair_type process)
uur = new UURReport(api, repair_type, uutReport, operationType, operator)
uur.UUTGuid = uut_report_guid
# Add / replace parts
if subparts:
    for sp in subparts:
        part = uur.AddUURPartInfo(sp.pn, sp.sn, sp.rev)
# Add failures
for f in failures:
    if f.part_index == 0:
        fail = uur.AddFailure(f.failcode, f.component_ref, f.comment, f.step_order)
    else:
        part = uur.PartInfo[f.part_index]
        fail = part.AddFailure(f.failcode, f.component_ref, f.comment, f.step_order)
    attach failure-level files
# Set misc infos
for (k,v) in misc_values:
    uur.MiscInfo[k] = v
# Times
uur.StartDateTimeOffset = ...
uur.Finalized = ...
# Validate & persist
uur.ValidateReport()
uur.ValidateForSubmit()
uur.SaveToFile()
```

---
## 13. Key Validation Rules Summary

| Area | Rule |
|------|------|
| Part hierarchy | Index 0 exists & represents main unit. Additional parts get sequential indices. |
| Fail codes | Must belong to the selected repair type’s category tree. |
| Misc info (non-empty) | Must match regex OR be in semicolon-separated literal list derived from definition string. |
| Misc info (empty) | Allowed only if empty string matches regex; else error. |
| Timestamps | `Finalized` coerced ≥ start; timezone normalization applied. |
| Attachments | Size ≤ `MaxAttachmentFileSize`. |
| Failure step linkage | `FailedStepOrderNumber` optional; when set links back to UUT test step ordering. |
| Referenced UUT GUID | Required logically if `RepairType.UUTRequired` (enforced externally – code property available). |

---
## 14. Practical Notes for API Consumers

1. **Do not conflate repair process code with test operation code** – always transmit/store both.
2. **Fail code paths**: Keep parent category + leaf code pairing for richer filtering downstream even though leaf GUID is authoritative.
3. **Subpart vs Main Unit Failures**: Use `PartIdx` semantics; blank serials in external feeds should normalize to index 0 if representing main.
4. **Bulk Validation**: Collect all misc field errors before rejecting to mirror C# batch exception style.
5. **Idempotent Updates**: If regenerating a UUR to replace one, reuse the `ReportId` before saving so file watcher treats it as a replacement.

---
## 15. Minimal Field Set for Successful UUR Submission

| Field | Requirement |
|-------|-------------|
| ReportId | Auto or supplied. |
| Repair process code | From `RepairType`. |
| Test operation process code | From `OperationType`. |
| Main Part (Idx 0) PN/SN/REV | Recommended (SN may be blank only in external legacy cases). |
| Failures (optional) | At least 1 for meaningful repair, but not strictly required by code. |
| Misc infos | Each must pass regex / emptiness rule if value present / required. |
| UUTGuid | Required if `RepairType.UUTRequired == true`. |
| Finalized time | Auto-normalized if earlier than start. |

---
**End of Document**
