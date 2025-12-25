#!/usr/bin/env python
"""RegScale CLI command to normalize CCI data from XML files."""
import datetime
import logging
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Tuple

import click
from rich.progress import Progress, TaskID

from regscale.core.app.application import Application
from regscale.core.app.utils.app_utils import create_progress_object, error_and_exit
from regscale.models.regscale_models import Catalog, SecurityControl, CCI, ControlObjective

logger = logging.getLogger("regscale")

# RegScale date format constant
REGSCALE_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class CCIImporter:
    """Imports CCI data from XML files and maps to security controls."""

    def __init__(self, xml_data: ET.Element, version: str = "5", verbose: bool = False):
        """
        Initialize the CCI importer.

        :param ET.Element xml_data: The root element of the XML data
        :param str version: NIST version to use for filtering
        :param bool verbose: Whether to output verbose information
        """
        self.xml_data = xml_data
        self.normalized_cci: Dict[str, List[Dict]] = {}
        self.cci_grouped_by_index: Dict[str, str] = {}
        self.verbose = verbose
        self.reference_version = version
        self._user_context: Optional[Tuple[Optional[str], int]] = None

    @staticmethod
    def _parse_control_id(ref_index: str) -> str:
        """
        Extract the main control_id from a reference index (e.g., 'AC-1 a 1 (b)' -> 'AC-1').

        :param str ref_index: Reference index string to parse
        :return: Main control ID
        :rtype: str
        """
        parts = ref_index.strip().split()
        return parts[0] if parts else ""

    @staticmethod
    def format_index(index: str) -> str:
        """
        Format index according to ControlObjective matching requirements.

        Examples:
            'AC-1 a 1' -> 'AC-1(a)(1)'
            'IA-13 (03) (a)' -> 'IA-13(03)(a)'
            'AC-1 a 1 (a)' -> 'AC-1(a)(1)(a)'

        :param str index: Raw index string from XML
        :return: Formatted index string
        :rtype: str
        """
        import re

        index = index.strip()

        # Pattern: match either (text) or non-whitespace text
        pattern = r"\([^)]+\)|[^\s()]+"
        parts = re.findall(pattern, index)

        if len(parts) <= 1:
            return parts[0] if parts else index

        # First part is the base control (e.g., 'AC-1', 'IA-13')
        result = parts[0]

        # Process remaining parts
        for part in parts[1:]:
            if part.startswith("("):
                # Already has parentheses, just append
                result += part
            else:
                # Need to add parentheses
                result += f"({part})"

        return result

    @staticmethod
    def parse_objective_id(objective_id: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Parse an objective otherId to extract control base and part.

        Supports both NIST 800-53 Revision 4 and 5 formats:

        Revision 5 Examples:
            "ac-1_smt.a" -> ("AC-1", "a")
            "ac-2.3_smt.a" -> ("AC-2(3)", "a")
            "au-10.1_smt.a" -> ("AU-10(1)", "a")
            "ac-2.4_smt" -> ("AC-2(4)", None)

        Revision 4 Examples:
            "ac-1_smt.a.1" -> ("AC-1", "a")
            "ac-1_smt.b.2" -> ("AC-1", "b")
            "ac-2.3_smt.d" -> ("AC-2(3)", "d")

        :param str objective_id: Objective otherId value
        :return: Tuple of (control_base, part_letter or None)
        :rtype: Tuple[Optional[str], Optional[str]]
        """
        import re

        # Pattern 1: xx-nn[.nn]_smt.x[.nn] (with part letter, optional subpart for rev 4)
        # Matches: ac-1_smt.a, ac-1_smt.a.1, ac-2.3_smt.d
        match = re.match(r"^([a-z]+)-(\d+)(?:\.(\d+))?_smt\.([a-z]+)(?:\.\d+)?$", objective_id.lower())

        if match:
            family = match.group(1).upper()
            control_num = match.group(2)
            enhancement = match.group(3)
            part = match.group(4)
        else:
            # Pattern 2: xx-nn[.nn]_smt[.x][.nn] (without clear part letter, or just enhancement)
            # Matches: ac-2.4_smt, ac-1_smt
            match = re.match(r"^([a-z]+)-(\d+)(?:\.(\d+))?_smt(?:\.[a-z]+)?(?:\.\d+)?$", objective_id.lower())
            if not match:
                return None, None

            family = match.group(1).upper()
            control_num = match.group(2)
            enhancement = match.group(3)
            part = None

        if enhancement:
            # Enhancement like AC-2(3)
            control_base = f"{family}-{control_num}({enhancement})"
        else:
            # Base control like AC-1
            control_base = f"{family}-{control_num}"

        return control_base, part

    @staticmethod
    def find_matching_ccis(control_base: str, part: Optional[str], cci_map: Dict[str, str]) -> List[str]:
        """
        Find all CCI IDs that match the control base and part.

        Examples:
            control_base="AC-1", part="a" matches:
                - AC-1(a)(1)(a)
                - AC-1(a)(1)(b)
                - AC-1(a)(2)
                - AC-1(a)

        :param str control_base: Control identifier (e.g., "AC-1", "AC-2(3)")
        :param Optional[str] part: Part letter (e.g., "a", "b") or None for enhancements
        :param Dict[str, str] cci_map: Map of formatted index to comma-separated CCI IDs
        :return: List of CCI ID strings (comma-separated)
        :rtype: List[str]
        """
        matching_ccis = []

        for index, cci_ids in cci_map.items():
            # Check if index starts with control_base
            if index.startswith(control_base):
                # Extract the part after control_base
                remainder = index[len(control_base) :]

                # For enhancements without parts, only match exact control (no remainder)
                # And Check if the remainder starts with (part)
                if (part is None and remainder == "") or remainder.startswith(f"({part})") or remainder == f"({part})":
                    matching_ccis.append(cci_ids)

        return matching_ccis

    def find_matching_ccis_by_name(self, control_base: str, name: str, cci_map: Dict[str, str]) -> List[str]:
        """
        Find CCIs by matching control base and objective name field.
        Fallback method when otherId matching fails.

        Supports both NIST 800-53 Revision 4 and 5 label formats:

        Revision 5 Examples:
            control_base="AC-2(4)", name="AC-2(4)" -> matches AC-2(4)
            control_base="AC-1", name="a" -> matches AC-1(a), AC-1(a)(1), etc.

        Revision 4 Examples:
            control_base="AC-1", name="a.1." -> matches AC-1(a), AC-1(a)(1), etc.
            control_base="AC-1", name="b.2." -> matches AC-1(b), AC-1(b)(2), etc.

        :param str control_base: Control identifier
        :param str name: Objective name field
        :param Dict[str, str] cci_map: Map of formatted index to comma-separated CCI IDs
        :return: List of CCI ID strings (comma-separated)
        :rtype: List[str]
        """
        import re

        matching_ccis = []

        # Remove trailing period and whitespace from name for matching
        clean_name = name.strip().rstrip(".").strip()

        # If name exactly matches control_base, match that control
        if clean_name == control_base:
            if control_base in cci_map:
                matching_ccis.append(cci_map[control_base])
            return matching_ccis

        # Try to extract part letter from different formats
        part = None

        # Check if name is a single letter (Revision 5 format: "a", "b")
        if len(clean_name) == 1 and clean_name.isalpha():
            part = clean_name.lower()
        elif match := re.match(r"^([a-z])\.\d+$", clean_name.lower()):
            part = match.group(1)

        # If we extracted a part letter, try matching
        if part:
            matching_ccis = self._extract_part_letter(cci_map, control_base, part, matching_ccis)

        return matching_ccis

    @staticmethod
    def _extract_part_letter(
        cci_map: Dict[str, str], control_base: str, part: str, matching_ccis: List[str]
    ) -> List[str]:
        """
        Extract the part letter from the name.

        :param Dict[str, str] cci_map: The map of CCI IDs to their indices.
        :param str control_base: The control base to match against.
        :param str part: The part letter to match against.
        :param List[str] matching_ccis: The list of matching CCI IDs.
        :rtype: List[str]
        """
        for index, cci_ids in cci_map.items():
            if index.startswith(control_base):
                remainder = index[len(control_base) :]
                if remainder.startswith(f"({part})") or remainder == f"({part})":
                    matching_ccis.append(cci_ids)
        return matching_ccis

    @staticmethod
    def ccis_already_present(current_other_id: str, new_cci_ids: str) -> bool:
        """
        Check if any of the new CCI IDs are already present in current otherId.
        Prevents duplicate CCI mappings.

        :param str current_other_id: Current otherId value
        :param str new_cci_ids: Comma-separated string of CCI IDs to add
        :return: True if any CCIs are already present
        :rtype: bool
        """
        if not current_other_id:
            return False

        # Extract individual CCI IDs from both strings
        existing_ccis: set[str] = {cci.strip() for cci in current_other_id.split(",") if cci.strip().startswith("CCI-")}
        new_ccis: set[str] = {cci.strip() for cci in new_cci_ids.split(",") if cci.strip().startswith("CCI-")}

        # Check if there's any overlap
        return bool(existing_ccis & new_ccis)

    @staticmethod
    def _extract_cci_data(cci_item: ET.Element) -> Tuple[Optional[str], str]:
        """
        Extract CCI ID and definition from CCI item.

        :param ET.Element cci_item: XML element containing CCI data
        :return: Tuple of (cci_id, definition)
        :rtype: Tuple[Optional[str], str]
        """
        cci_id = cci_item.get("id")
        definition_elem = cci_item.find(".//{http://iase.disa.mil/cci}definition")
        definition = definition_elem.text if definition_elem is not None and definition_elem.text else ""
        return cci_id, definition

    def _process_references(self, references: List[ET.Element], cci_id: str, definition: str) -> None:
        """
        Process reference elements and add to normalized CCI data.

        :param List[ET.Element] references: List of reference XML elements
        :param str cci_id: CCI identifier
        :param str definition: CCI definition text
        :rtype: None
        """
        for ref in references:
            if not self._is_valid_reference(ref):
                continue

            ref_index = ref.get("index")
            if ref_index:
                main_control = self._parse_control_id(ref_index)
                self._add_cci_to_control(main_control, cci_id, definition)

    def _is_valid_reference(self, ref: ET.Element) -> bool:
        """
        Check if reference matches the target version.

        :param ET.Element ref: Reference XML element
        :return: True if reference version matches target version
        :rtype: bool
        """
        ref_version = ref.get("version")
        return ref_version is not None and ref_version == self.reference_version

    def _add_cci_to_control(self, main_control: str, cci_id: str, definition: str) -> None:
        """
        Add CCI data to the normalized structure for a control.

        :param str main_control: Control identifier
        :param str cci_id: CCI identifier
        :param str definition: CCI definition
        :rtype: None
        """
        if main_control not in self.normalized_cci:
            self.normalized_cci[main_control] = []
        self.normalized_cci[main_control].append({"cci_id": cci_id, "definition": definition})

    def parse_cci(self) -> None:
        """
        Parse CCI items from XML and create both mapping structures.

        Creates:
        - normalized_cci: Dict[control_id, List[Dict]] - for SecurityControl mapping
        - cci_grouped_by_index: Dict[formatted_index, str] - for ControlObjective mapping

        :rtype: None
        """
        if self.verbose:
            logger.info("Parsing CCI items from XML...")

        # Track all CCI items with formatted indices for objective mapping
        from collections import defaultdict

        temp_grouped: Dict[str, List[str]] = defaultdict(list)

        for cci_item in self.xml_data.findall(".//{http://iase.disa.mil/cci}cci_item"):
            cci_id, definition = self._extract_cci_data(cci_item)
            if not cci_id:
                continue

            references = cci_item.findall(".//{http://iase.disa.mil/cci}reference")

            for ref in references:
                if not self._is_valid_reference(ref):
                    continue

                ref_index = ref.get("index")
                if ref_index:
                    # Existing: simple control ID for SecurityControl mapping
                    main_control = self._parse_control_id(ref_index)
                    self._add_cci_to_control(main_control, cci_id, definition)

                    # NEW: formatted index for ControlObjective mapping
                    formatted_index = self.format_index(ref_index)
                    temp_grouped[formatted_index].append(cci_id)

        # Convert to comma-separated format
        self.cci_grouped_by_index = {index: ", ".join(cci_list) for index, cci_list in temp_grouped.items()}

        if self.verbose:
            logger.info(f"Created {len(self.normalized_cci)} control mappings")
            logger.info(f"Created {len(self.cci_grouped_by_index)} formatted index mappings")

    @staticmethod
    def _get_catalog(catalog_id: int) -> Catalog:
        """
        Get the catalog with specified ID.

        :param int catalog_id: ID of the catalog to retrieve
        :return: Catalog instance
        :rtype: Catalog
        :raises SystemExit: If catalog not found
        """
        try:
            catalog = Catalog.get(id=catalog_id)
            if catalog is None:
                error_and_exit(f"Catalog with id {catalog_id} not found. Please ensure the catalog exists.")
            return catalog
        except Exception:
            error_and_exit(f"Catalog with id {catalog_id} not found. Please ensure the catalog exists.")

    def _get_user_context(self) -> Tuple[Optional[str], int]:
        """
        Get user ID and tenant ID from application config.

        :return: Tuple of (user_id, tenant_id)
        :rtype: Tuple[Optional[str], int]
        """
        if self._user_context is None:
            app = Application()
            user_id = app.config.get("userId")
            tenant_id = app.config.get("tenantId", 1)

            try:
                user_id = str(user_id) if user_id else None
            except (TypeError, ValueError):
                user_id = None
                if self.verbose:
                    logger.warning("userId in config is not set or invalid; created_by will be None.")

            # Convert tenant_id to int if it's a string
            try:
                tenant_id = int(tenant_id)
            except (TypeError, ValueError):
                tenant_id = 1
                if self.verbose:
                    logger.warning("tenantId in config is not valid; using default value 1.")

            self._user_context = (user_id, tenant_id)

        return self._user_context

    @staticmethod
    def _find_existing_cci(control_id: int, cci_id: str) -> Optional[CCI]:
        """
        Find existing CCI by ID within a control.

        :param int control_id: Security control ID
        :param str cci_id: CCI identifier to search for
        :return: Existing CCI instance or None
        :rtype: Optional[CCI]
        """
        try:
            existing_ccis: List[CCI] = CCI.get_all_by_parent(parent_id=control_id)
            for existing in existing_ccis:
                if existing.uuid == cci_id:
                    return existing
        except Exception:
            pass
        return None

    @staticmethod
    def _create_cci_data(
        cci_id: str, definition: str, user_id: Optional[str], tenant_id: int, current_time: str
    ) -> Dict:
        """
        Create common CCI data structure.

        :param str cci_id: CCI identifier
        :param str definition: CCI definition
        :param Optional[str] user_id: User ID
        :param int tenant_id: Tenant ID
        :param str current_time: Current timestamp string
        :return: Dictionary with common CCI attributes
        :rtype: Dict
        """
        return {
            "name": cci_id,
            "description": definition,
            "controlType": "policy",
            "publishDate": current_time,
            "dateLastUpdated": current_time,
            "lastUpdatedById": user_id,
            "isPublic": True,
            "tenantsId": tenant_id,
        }

    @staticmethod
    def _update_existing_cci(existing_cci: CCI, cci_data: Dict) -> None:
        """
        Update an existing CCI with new data.

        :param CCI existing_cci: CCI instance to update
        :param Dict cci_data: Dictionary with CCI attributes
        :rtype: None
        """
        for key, value in cci_data.items():
            setattr(existing_cci, key, value)
        existing_cci.create_or_update()

    @staticmethod
    def _create_new_cci(cci_id: str, cci_data: Dict, control_id: int, user_id: Optional[str], current_time: str) -> CCI:
        """
        Create a new CCI instance.

        :param str cci_id: CCI identifier
        :param Dict cci_data: Dictionary with common CCI attributes
        :param int control_id: Security control ID
        :param Optional[str] user_id: User ID
        :param str current_time: Current timestamp string
        :return: Created CCI instance
        :rtype: CCI
        """
        new_cci = CCI(
            uuid=cci_id,
            securityControlId=control_id,
            createdById=user_id,
            dateCreated=current_time,
            **cci_data,
        )
        new_cci.create()
        return new_cci

    def _process_cci_for_control(
        self, control_id: int, cci_list: List[Dict], user_id: Optional[str], tenant_id: int
    ) -> Tuple[int, int]:
        """
        Process all CCI items for a specific control.

        :param int control_id: Security control ID
        :param List[Dict] cci_list: List of CCI data dictionaries
        :param Optional[str] user_id: User ID
        :param int tenant_id: Tenant ID
        :return: Tuple of (created_count, updated_count)
        :rtype: Tuple[int, int]
        """
        created_count = 0
        updated_count = 0
        current_time = datetime.datetime.now().strftime(REGSCALE_DATE_FORMAT)

        for cci in cci_list:
            cci_id = cci["cci_id"]
            definition = cci["definition"]

            existing_cci = self._find_existing_cci(control_id, cci_id)
            cci_data = self._create_cci_data(cci_id, definition, user_id, tenant_id, current_time)

            if existing_cci:
                self._update_existing_cci(existing_cci, cci_data)
                updated_count += 1
            else:
                self._create_new_cci(cci_id, cci_data, control_id, user_id, current_time)
                created_count += 1

        return created_count, updated_count

    def map_to_security_controls(self, catalog_id: int = 1) -> Dict[str, int]:
        """
        Map normalized CCI data to security controls in the database.

        :param int catalog_id: ID of the catalog containing security controls (default: 1)
        :return: Dictionary with operation statistics
        :rtype: Dict[str, int]
        """
        if self.verbose:
            logger.info("Mapping CCI data to security controls...")

        catalog = self._get_catalog(catalog_id)
        security_controls: List[SecurityControl] = SecurityControl.get_all_by_parent(parent_id=catalog.id)
        control_map = {sc.controlId: sc.id for sc in security_controls}

        user_id, tenant_id = self._get_user_context()

        created_count = 0
        updated_count = 0
        skipped_count = 0

        with create_progress_object() as progress:
            logger.info(f"Parsing and mapping {len(self.normalized_cci)} normalized CCI entries...")
            main_task = progress.add_task("Parsing and mapping CCIs...", total=len(self.normalized_cci))
            for main_control, cci_list in self.normalized_cci.items():
                if main_control in control_map:
                    control_id = control_map[main_control]
                    control_created, control_updated = self._process_cci_for_control(
                        control_id, cci_list, user_id, tenant_id
                    )
                    created_count += control_created
                    updated_count += control_updated
                else:
                    skipped_count += len(cci_list)
                    if self.verbose:
                        logger.warning(f"Warning: Control not found for key: {main_control}")
                progress.update(main_task, advance=1)

        return {
            "created": created_count,
            "updated": updated_count,
            "skipped": skipped_count,
            "total_processed": len(self.normalized_cci),
        }

    def map_to_control_objectives(self, catalog_id: int = 1) -> Dict[str, int]:
        """
        Map grouped CCI data to control objectives in the database.
        Updates the otherId field of existing ControlObjective records.

        :param int catalog_id: ID of the catalog containing control objectives (default: 1)
        :return: Dictionary with operation statistics
        :rtype: Dict[str, int]
        """
        if self.verbose:
            logger.info("Mapping CCI data to control objectives...")

        # Fetch all objectives for the catalog
        objectives: List[ControlObjective] = ControlObjective.get_by_catalog(catalog_id=catalog_id)

        if self.verbose:
            logger.info(f"Found {len(objectives)} objectives in catalog {catalog_id}")

        objectives_updated = 0
        objectives_skipped = 0
        objectives_not_found = 0

        with create_progress_object() as progress:
            logger.info(f"Processing {len(objectives)} objectives...")
            task = progress.add_task("Mapping CCIs to objectives...", total=len(objectives))

            for obj in objectives:
                objective_id = obj.otherId

                # Skip objectives without proper otherId
                if not objective_id or "_smt" not in objective_id:
                    objectives_not_found += 1
                    progress.update(task, advance=1)
                    continue

                # Extract just the objective ID part (before any CCIs)
                # Format: "ac-1_smt.a" or "ac-1_smt.a, CCI-000001, CCI-000002"
                objective_id_parts = objective_id.split(",")
                base_objective_id = objective_id_parts[0].strip()

                # Parse the objective ID
                control_base, part = self.parse_objective_id(base_objective_id)

                if not control_base:
                    objectives_not_found += 1
                    progress.update(task, advance=1)
                    continue

                # Find matching CCIs by otherId
                matching_ccis = self.find_matching_ccis(control_base, part, self.cci_grouped_by_index)

                # Fallback: try matching by name
                if not matching_ccis and obj.name:
                    matching_ccis = self.find_matching_ccis_by_name(control_base, obj.name, self.cci_grouped_by_index)

                if matching_ccis:
                    skipped_count, updated_count = self._handle_matching_ccis(
                        control_objective=obj,
                        matching_ccis=matching_ccis,
                        base_objective_id=base_objective_id,
                    )
                    objectives_skipped += skipped_count
                    objectives_updated += updated_count
                else:
                    objectives_not_found += 1

                progress.update(task, advance=1)

        return {
            "updated": objectives_updated,
            "skipped": objectives_skipped,
            "not_found": objectives_not_found,
            "total_processed": len(objectives),
        }

    def _handle_matching_ccis(
        self,
        control_objective: ControlObjective,
        matching_ccis: List[str],
        base_objective_id: str,
    ) -> Tuple[int, int]:
        """
        Handle matching CCIs.

        :param ControlObjective control_objective: ControlObjective instance
        :param List[str] matching_ccis: List of matching CCI IDs
        :param str base_objective_id: Base objective ID
        :return: Tuple of (number of objectives skipped, number of objectives updated)
        :rtype: Tuple[int, int]
        """
        # Combine all CCI IDs
        all_cci_ids = ", ".join(matching_ccis)

        # Check for duplicates
        if self.ccis_already_present(control_objective.otherId, all_cci_ids):
            if self.verbose:
                logger.info(f"Skipping {base_objective_id} - CCIs already present")
            return 1, 0

        # Update the otherId field
        control_objective.otherId = f"{control_objective.otherId}, {all_cci_ids}"
        control_objective.save()

        if self.verbose:
            logger.info(f"Updated {base_objective_id} with {all_cci_ids}")
        return 0, 1

    def get_normalized_cci(self) -> Dict[str, List[Dict]]:
        """
        Get the normalized CCI data.

        :return: Dictionary of normalized CCI data
        :rtype: Dict[str, List[Dict]]
        """
        return self.normalized_cci


def _load_xml_file(xml_file: str) -> ET.Element:
    """
    Load and parse XML file.

    :param str xml_file: Path to XML file
    :return: Root element of parsed XML
    :rtype: ET.Element
    :raises click.ClickException: If XML parsing fails
    """
    try:
        logger.info(f"Loading XML file: {xml_file}")
        tree = ET.parse(xml_file)
        return tree.getroot()
    except ET.ParseError as e:
        error_and_exit(f"Failed to parse XML file: {e}")


def _display_verbose_output(normalized_data: Dict[str, List[Dict]]) -> None:
    """
    Display detailed normalized CCI data.

    :param Dict[str, List[Dict]] normalized_data: Dictionary of normalized CCI data
    :rtype: None
    """
    logger.info("\nNormalized CCI Data:")
    for key, value in normalized_data.items():
        logger.info(f"  {key}: {len(value)} CCI items")
        for cci in value:
            definition_preview = cci["definition"][:100] + "..." if len(cci["definition"]) > 100 else cci["definition"]
            logger.info(f"    - {cci['cci_id']}: {definition_preview}")


def _display_results(stats: Dict[str, int]) -> None:
    """
    Display database operation results.

    :param Dict[str, int] stats: Dictionary with operation statistics
    :rtype: None
    """
    logger.info(
        f"[green]\nDatabase operations completed:"
        f"[green]\n  - Created: {stats['created']}"
        f"[green]\n  - Updated: {stats['updated']}"
        f"[green]\n  - Skipped: {stats['skipped']}"
        f"[green]\n  - Total processed: {stats['total_processed']}",
    )


def _display_objective_results(stats: Dict[str, int]) -> None:
    """
    Display control objective mapping results.

    :param Dict[str, int] stats: Dictionary with operation statistics
    :rtype: None
    """
    logger.info(
        f"[green]\nControl objective operations completed:"
        f"[green]\n  - Updated: {stats['updated']}"
        f"[green]\n  - Skipped: {stats['skipped']}"
        f"[green]\n  - Not found: {stats['not_found']}"
        f"[green]\n  - Total processed: {stats['total_processed']}",
    )


def _process_cci_import(
    importer: CCIImporter, dry_run: bool, verbose: bool, catalog_id: int, disable_objectives: bool = False
) -> None:
    """
    Process CCI import with optional database operations.

    :param CCIImporter importer: CCIImporter instance
    :param bool dry_run: Whether to skip database operations
    :param bool verbose: Whether to display verbose output
    :param int catalog_id: ID of the catalog containing security controls
    :param bool disable_objectives: Whether to disable mapping to control objectives
    :rtype: None
    """
    importer.parse_cci()
    normalized_data = importer.get_normalized_cci()

    logger.info(f"[green]Successfully parsed {len(normalized_data)} normalized CCI entries[/green]")

    if verbose:
        _display_verbose_output(normalized_data)

    if not dry_run:
        # Map to SecurityControl (existing functionality)
        stats = importer.map_to_security_controls(catalog_id)
        _display_results(stats)

        # Map to ControlObjective (new functionality)
        if not disable_objectives:
            logger.info("\n[cyan]Mapping CCIs to control objectives...[/cyan]")
            obj_stats = importer.map_to_control_objectives(catalog_id)
            _display_objective_results(obj_stats)
    else:
        logger.info("\n[yellow]DRY RUN MODE: No database changes were made[/yellow]")


@click.command(name="cci_importer")
@click.option(
    "--xml_file", "-f", type=click.Path(exists=True), default=None, required=False, help="Path to the CCI XML file."
)
@click.option("--dry-run", "-d", is_flag=True, help="Parse and display normalized data without saving to database")
@click.option("--verbose", "-v", is_flag=True, help="Display detailed output including all normalized CCI data")
@click.option(
    "--nist-version", "-n", type=click.Choice(["4", "5"]), default="5", help="NIST 800-53 Revision version (default: 5)"
)
@click.option(
    "--catalog-id", "-c", type=click.INT, default=1, help="ID of the catalog containing security controls (default: 1)"
)
@click.option(
    "--disable-objectives",
    "-o",
    is_flag=True,
    help="Disable mapping CCIs to control objectives (updates otherId field)",
)
def cci_importer(
    xml_file: str, dry_run: bool, verbose: bool, nist_version: str, catalog_id: int, disable_objectives: bool
) -> None:
    """Import CCI data from XML files and map to security controls and/or objectives.

    By default, maps CCIs to SecurityControl entities. Use --disable-objectives flag
    to also update ControlObjective.otherId fields with CCI mappings.

    If no XML file is specified, defaults to packaged CCI_List.xml.
    """

    try:
        if not xml_file:
            import importlib.resources as pkg_resources
            from regscale.models import integration_models

            files = pkg_resources.files(integration_models)
            cci_path = files / "CCI_List.xml"
            xml_file = str(cci_path)
        root = _load_xml_file(xml_file)
        importer = CCIImporter(root, version=nist_version, verbose=verbose)
        _process_cci_import(importer, dry_run, verbose, catalog_id, disable_objectives)
    except Exception as e:
        error_and_exit(f"Unexpected error: {e}")
