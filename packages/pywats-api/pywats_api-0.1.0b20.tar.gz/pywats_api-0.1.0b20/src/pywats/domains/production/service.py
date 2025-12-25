"""Production service - business logic layer.

High-level operations for production unit management.
"""
from typing import Optional, List, Dict, Any, Sequence, Union
import logging

from .models import (
    Unit, UnitChange, ProductionBatch, SerialNumberType,
    UnitVerification, UnitVerificationGrade, UnitPhase
)
from .enums import UnitPhaseFlag
from .repository import ProductionRepository

logger = logging.getLogger(__name__)


class ProductionService:
    """
    Production business logic.

    Provides high-level operations for managing production units,
    serial numbers, batches, and assembly relationships.
    
    Unit Phases:
        The service caches available unit phases on first access.
        Use get_phases() to retrieve all phases, or get_phase() to
        look up a specific phase by ID, code, or name.
    """

    def __init__(self, repository: ProductionRepository, base_url: str = ""):
        """
        Initialize with repository.

        Args:
            repository: ProductionRepository for data access
            base_url: Base URL for internal API calls
        """
        self._repository = repository
        self._base_url = base_url.rstrip("/") if base_url else ""
        
        # Phase cache (loaded on first access)
        self._phases: Optional[List[UnitPhase]] = None
        self._phase_by_id: Dict[int, UnitPhase] = {}
        self._phase_by_code: Dict[str, UnitPhase] = {}
        self._phase_by_name: Dict[str, UnitPhase] = {}

    # =========================================================================
    # Unit Operations
    # =========================================================================

    def get_unit(
        self, serial_number: str, part_number: str
    ) -> Optional[Unit]:
        """
        Get a production unit.

        Args:
            serial_number: The unit serial number
            part_number: The product part number

        Returns:
            Unit if found, None otherwise
        """
        return self._repository.get_unit(serial_number, part_number)

    def create_units(self, units: Sequence[Unit]) -> List[Unit]:
        """
        Create multiple production units.

        Args:
            units: List of Unit objects to create

        Returns:
            List of created Unit objects
        """
        results = self._repository.save_units(units)
        for unit in results:
            logger.info(f"UNIT_CREATED: {unit.serial_number} (pn={unit.part_number})")
        return results

    def update_unit(self, unit: Unit) -> Optional[Unit]:
        """
        Update a production unit.

        Args:
            unit: Unit object with updated fields

        Returns:
            Updated Unit object
        """
        result = self._repository.save_units([unit])
        if result:
            logger.info(f"UNIT_UPDATED: {unit.serial_number} (pn={unit.part_number})")
        return result[0] if result else None

    # =========================================================================
    # Unit Verification
    # =========================================================================

    def verify_unit(
        self,
        serial_number: str,
        part_number: str,
        revision: Optional[str] = None
    ) -> Optional[UnitVerification]:
        """
        Verify a unit and get its status.

        Args:
            serial_number: The unit serial number
            part_number: The product part number
            revision: Optional product revision

        Returns:
            UnitVerification result
        """
        return self._repository.get_unit_verification(
            serial_number, part_number, revision
        )

    def get_unit_grade(
        self,
        serial_number: str,
        part_number: str,
        revision: Optional[str] = None
    ) -> Optional[UnitVerificationGrade]:
        """
        Get complete verification grade for a unit.

        Args:
            serial_number: The unit serial number
            part_number: The product part number
            revision: Optional product revision

        Returns:
            UnitVerificationGrade result
        """
        return self._repository.get_unit_verification_grade(
            serial_number, part_number, revision
        )

    def is_unit_passing(
        self,
        serial_number: str,
        part_number: str
    ) -> bool:
        """
        Check if a unit is passing all tests.

        Args:
            serial_number: The unit serial number
            part_number: The product part number

        Returns:
            True if unit is passing
        """
        grade = self._repository.get_unit_verification_grade(
            serial_number, part_number
        )
        if grade:
            return grade.all_processes_passed_last_run
        return False

    # =========================================================================
    # Unit Phases
    # =========================================================================

    def _load_phases(self) -> None:
        """Load and cache unit phases from server."""
        if self._phases is not None:
            return  # Already loaded
        
        if not self._base_url:
            logger.warning("Cannot load phases: base_url not set")
            self._phases = []
            return
        
        phases = self._repository.get_unit_phases(self._base_url)
        self._phases = phases
        
        # Build lookup dictionaries
        self._phase_by_id = {p.phase_id: p for p in phases}
        self._phase_by_code = {p.code.lower(): p for p in phases if p.code}
        self._phase_by_name = {p.name.lower(): p for p in phases if p.name}
        
        logger.debug(f"Loaded {len(phases)} unit phases from server")

    def get_phases(self) -> List[UnitPhase]:
        """
        Get all available unit phases.
        
        Phases are cached after the first call.
        
        Returns:
            List of UnitPhase objects
            
        Example:
            phases = api.production.get_phases()
            for phase in phases:
                print(f"{phase.phase_id}: {phase.name}")
        """
        self._load_phases()
        return list(self._phases or [])

    def get_phase(
        self, 
        identifier: Union[int, str]
    ) -> Optional[UnitPhase]:
        """
        Get a unit phase by ID, code, or name.
        
        Args:
            identifier: Phase ID (int), code (str), or name (str)
            
        Returns:
            UnitPhase if found, None otherwise
            
        Example:
            # By ID
            phase = api.production.get_phase(16)
            
            # By code
            phase = api.production.get_phase("Finalized")
            
            # By name (case-insensitive)
            phase = api.production.get_phase("Under production")
        """
        self._load_phases()
        
        if isinstance(identifier, int):
            return self._phase_by_id.get(identifier)
        
        # Try by code first (case-insensitive)
        identifier_lower = identifier.lower()
        if identifier_lower in self._phase_by_code:
            return self._phase_by_code[identifier_lower]
        
        # Then by name (case-insensitive)
        return self._phase_by_name.get(identifier_lower)

    def get_phase_id(self, phase: Union[int, str, UnitPhaseFlag]) -> Optional[int]:
        """
        Resolve a phase identifier to its ID.
        
        Args:
            phase: Phase ID (int), code (str), name (str), or UnitPhaseFlag enum
            
        Returns:
            Phase ID if found, None otherwise
            
        Example:
            phase_id = api.production.get_phase_id("Finalized")  # Returns 16
            phase_id = api.production.get_phase_id(UnitPhaseFlag.FINALIZED)  # Returns 16
        """
        if isinstance(phase, UnitPhaseFlag):
            return int(phase)
        if isinstance(phase, int):
            return phase
        
        phase_obj = self.get_phase(phase)
        return phase_obj.phase_id if phase_obj else None

    # =========================================================================
    # Unit Phase and Process
    # =========================================================================

    def set_unit_phase(
        self,
        serial_number: str,
        part_number: str,
        phase: Union[int, str, UnitPhaseFlag],
        comment: Optional[str] = None
    ) -> bool:
        """
        Set a unit's current phase.

        Args:
            serial_number: The unit serial number
            part_number: The product part number
            phase: Phase ID (int), code (str), name (str), or UnitPhaseFlag enum
            comment: Optional comment

        Returns:
            True if successful
            
        Example:
            # By phase ID
            api.production.set_unit_phase("SN001", "PART001", 16)
            
            # By phase code
            api.production.set_unit_phase("SN001", "PART001", "Finalized")
            
            # By phase name
            api.production.set_unit_phase("SN001", "PART001", "Under production")
            
            # By enum (recommended)
            api.production.set_unit_phase("SN001", "PART001", UnitPhaseFlag.FINALIZED)
        """
        # Resolve phase to ID if string
        phase_id = self.get_phase_id(phase)
        if phase_id is None:
            raise ValueError(f"Unknown phase: {phase}")
        
        return self._repository.set_unit_phase(
            serial_number, part_number, phase_id, comment
        )

    def set_unit_process(
        self,
        serial_number: str,
        part_number: str,
        process_code: Optional[int] = None,
        comment: Optional[str] = None
    ) -> bool:
        """
        Set a unit's process.

        Args:
            serial_number: The unit serial number
            part_number: The product part number
            process_code: The process code
            comment: Optional comment

        Returns:
            True if successful
        """
        return self._repository.set_unit_process(
            serial_number, part_number, process_code, comment
        )

    # =========================================================================
    # Unit Changes
    # =========================================================================

    def get_unit_changes(
        self,
        serial_number: Optional[str] = None,
        part_number: Optional[str] = None,
        top: Optional[int] = None
    ) -> List[UnitChange]:
        """
        Get unit change records.

        Args:
            serial_number: Optional serial number filter
            part_number: Optional part number filter
            top: Max number of records

        Returns:
            List of UnitChange objects
        """
        return self._repository.get_unit_changes(
            serial_number=serial_number,
            part_number=part_number,
            top=top
        )

    def acknowledge_unit_change(self, change_id: str) -> bool:
        """
        Acknowledge and delete a unit change record.

        Args:
            change_id: The change record ID

        Returns:
            True if successful
        """
        return self._repository.delete_unit_change(change_id)

    # =========================================================================
    # Assembly (Parent/Child Unit Relationships)
    # =========================================================================
    #
    # These methods manage ACTUAL UNIT assemblies during production.
    # 
    # KEY CONCEPT DISTINCTION:
    # ========================
    # 
    # Box Build Template (Product Domain):
    #   - Defines WHAT subunits are REQUIRED (design-time)
    #   - Managed via api.product_internal.get_box_build()
    #   - Example: "Controller Module requires 1x Power Supply, 2x Sensor"
    #
    # Unit Assembly (Production Domain - THIS SECTION):
    #   - ATTACHES actual units with serial numbers (runtime/production)
    #   - Managed via these methods below
    #   - Example: "Unit CTRL-001 contains PSU-456 and SNS-789, SNS-790"
    #
    # WORKFLOW:
    # 1. Create production units (both parent and children)
    # 2. Test and finalize child units (set phase to "Finalized")
    # 3. Use add_child_to_assembly() to attach children to parent
    # 4. Use verify_assembly() to confirm all required parts are attached
    #
    # VALIDATION RULES for add_child_to_assembly():
    # - Child unit must not already have a parent
    # - Parent's box build template must define the child as valid
    # - Child unit must be in phase "Finalized" (or have PhaseFinalized tag)
    # - The relation cannot create a loop
    # =========================================================================

    def add_child_to_assembly(
        self,
        parent_serial: str,
        parent_part: str,
        child_serial: str,
        child_part: str
    ) -> bool:
        """
        Add a child unit to a parent assembly (box build).
        
        This attaches an ACTUAL production unit (with serial number) to a parent
        assembly. The child must match one of the subunits defined in the parent's
        box build template.

        Prerequisites:
            - Parent's box build template must define this child product as valid
            - Child unit must be in phase "Finalized" (or product has PhaseFinalized tag)
            - Child unit must not already have a parent
            
        Args:
            parent_serial: Parent unit serial number
            parent_part: Parent product part number
            child_serial: Child unit serial number
            child_part: Child product part number

        Returns:
            True if successful
            
        Raises:
            API error if validation fails (child not finalized, not in template, etc.)
            
        Example:
            # 1. First, ensure box build template is defined (Product domain)
            # template = api.product_internal.get_box_build("MODULE", "A")
            # template.add_subunit("PCBA", "A").save()
            
            # 2. Finalize the child unit
            api.production.set_unit_phase("PCBA-001", "PCBA", "Finalized")
            
            # 3. Add child to parent assembly
            api.production.add_child_to_assembly(
                parent_serial="MODULE-001",
                parent_part="MODULE",
                child_serial="PCBA-001", 
                child_part="PCBA"
            )
            
        See Also:
            - BoxBuildTemplate: Define what subunits are required
            - verify_assembly(): Check if all required parts are attached
            - remove_child_from_assembly(): Detach a child unit
        """
        return self._repository.add_child_unit(
            parent_serial, parent_part, child_serial, child_part
        )

    def remove_child_from_assembly(
        self,
        parent_serial: str,
        parent_part: str,
        child_serial: str,
        child_part: str
    ) -> bool:
        """
        Remove a child unit from a parent assembly.
        
        Detaches an actual production unit from its parent assembly.
        The child unit will be available for reassignment to another parent.

        Args:
            parent_serial: Parent unit serial number
            parent_part: Parent product part number
            child_serial: Child unit serial number
            child_part: Child product part number

        Returns:
            True if successful
        """
        return self._repository.remove_child_unit(
            parent_serial, parent_part, child_serial, child_part
        )

    def verify_assembly(
        self,
        serial_number: str,
        part_number: str,
        revision: str
    ) -> Optional[Dict[str, Any]]:
        """
        Verify that assembly child units match the box build template.
        
        Checks whether all required subunits (as defined in the product's
        box build template) have been attached to this specific unit.
        
        This compares:
        - Box Build Template: "What subunits are REQUIRED" (Product domain)
        - Current Assembly: "What units are ATTACHED" (Production domain)

        Args:
            serial_number: Parent serial number
            part_number: Parent part number
            revision: Parent revision

        Returns:
            Verification results or None
        """
        return self._repository.check_child_units(
            serial_number, part_number, revision
        )

    # =========================================================================
    # Serial Numbers
    # =========================================================================

    def get_serial_number_types(self) -> List[SerialNumberType]:
        """
        Get all serial number types.

        Returns:
            List of SerialNumberType objects
        """
        return self._repository.get_serial_number_types()

    def allocate_serial_numbers(
        self,
        type_name: str,
        count: int = 1,
        reference_sn: Optional[str] = None,
        reference_pn: Optional[str] = None,
        station_name: Optional[str] = None
    ) -> List[str]:
        """
        Allocate serial numbers from pool.

        Args:
            type_name: Serial number type name
            count: Number to allocate
            reference_sn: Optional reference serial number
            reference_pn: Optional reference part number
            station_name: Optional station name

        Returns:
            List of allocated serial numbers
        """
        return self._repository.take_serial_numbers(
            type_name, count, reference_sn, reference_pn, station_name
        )

    def find_serial_numbers_in_range(
        self,
        type_name: str,
        from_serial: str,
        to_serial: str
    ) -> List[Dict[str, Any]]:
        """
        Find serial numbers in a range.

        Args:
            type_name: Serial number type name
            from_serial: Start of range
            to_serial: End of range

        Returns:
            List of serial number records
        """
        return self._repository.get_serial_numbers_by_range(
            type_name, from_serial, to_serial
        )

    def find_serial_numbers_by_reference(
        self,
        type_name: str,
        reference_serial: Optional[str] = None,
        reference_part: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Find serial numbers by reference.

        Args:
            type_name: Serial number type name
            reference_serial: Reference serial number
            reference_part: Reference part number

        Returns:
            List of serial number records
        """
        return self._repository.get_serial_numbers_by_reference(
            type_name, reference_serial, reference_part
        )

    def import_serial_numbers(
        self,
        file_content: bytes,
        content_type: str = "text/csv"
    ) -> bool:
        """
        Import serial numbers from file.

        Args:
            file_content: File content as bytes
            content_type: MIME type (text/csv or application/xml)

        Returns:
            True if successful
        """
        return self._repository.upload_serial_numbers(file_content, content_type)

    def export_serial_numbers(
        self,
        type_name: str,
        state: Optional[str] = None,
        format: str = "csv"
    ) -> Optional[bytes]:
        """
        Export serial numbers to file.

        Args:
            type_name: Serial number type name
            state: Optional state filter
            format: Output format (csv or xml)

        Returns:
            File content as bytes or None
        """
        return self._repository.export_serial_numbers(type_name, state, format)

    # =========================================================================
    # Batches
    # =========================================================================

    def save_batches(
        self, batches: Sequence[ProductionBatch]
    ) -> List[ProductionBatch]:
        """
        Create or update production batches.

        Args:
            batches: List of ProductionBatch objects

        Returns:
            List of saved ProductionBatch objects
        """
        return self._repository.save_batches(batches)
