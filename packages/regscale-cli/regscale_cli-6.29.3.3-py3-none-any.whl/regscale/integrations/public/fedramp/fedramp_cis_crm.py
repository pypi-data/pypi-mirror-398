#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pylint: disable=C0415
"""standard python imports"""
from __future__ import annotations

import json
import math
import re
import shutil
from collections import Counter
from concurrent.futures import as_completed
from concurrent.futures.thread import ThreadPoolExecutor
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from tempfile import gettempdir
from threading import Thread
from types import ModuleType
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Literal, Optional, Tuple, TypeVar

import click

from regscale.core.app.api import Api
from regscale.core.app.utils.api_handler import APIInsertionError, APIUpdateError
from regscale.core.app.utils.app_utils import compute_hash, create_progress_object, error_and_exit, get_current_datetime
from regscale.core.utils.graphql import GraphQLQuery
from regscale.integrations.control_matcher import ControlMatcher
from regscale.integrations.public.fedramp.ssp_logger import SSPLogger
from regscale.models import ControlObjective, ImplementationObjective, ImportValidater, Parameter, Profile
from regscale.models.regscale_models import (
    ControlImplementation,
    File,
    LeveragedAuthorization,
    SecurityControl,
    SecurityPlan,
)
from regscale.models.regscale_models.compliance_settings import ComplianceSettings
from regscale.models.regscale_models.control_implementation import ControlImplementationStatus
from regscale.utils.threading import ThreadSafeDict, ThreadSafeSet
from regscale.utils.version import RegscaleVersion

# For type annotations only
if TYPE_CHECKING:
    import pandas as pd

T = TypeVar("T")

logger = SSPLogger()
progress = create_progress_object()

SERVICE_PROVIDER_CORPORATE = "Service Provider Corporate"
SERVICE_PROVIDER_SYSTEM_SPECIFIC = "Service Provider System Specific"
SERVICE_PROVIDER_HYBRID = "Service Provider Hybrid (Corporate and System Specific)"
PROVIDER_SYSTEM_SPECIFIC = "Provider (System Specific)"
CUSTOMER_PROVIDED = "Customer Provided"
CUSTOMER_CONFIGURED = "Customer Configured"
PROVIDED_BY_CUSTOMER = "Provided by Customer (Customer System Specific)"
CONFIGURED_BY_CUSTOMER = "Configured by Customer (Customer System Specific)"
INHERITED = "Inherited from pre-existing FedRAMP Authorization"
SHARED = "Shared (Service Provider and Customer Responsibility)"
NOT_IMPLEMENTED = ControlImplementationStatus.NotImplemented.value
PARTIALLY_IMPLEMENTED = ControlImplementationStatus.PartiallyImplemented.value
CONTROL_ID = "Control ID"
ALT_IMPLEMENTATION = "Alternate Implementation"
ALTERNATIVE_IMPLEMENTATION = "Alternative Implementation"
CAN_BE_INHERITED_CSP = "Can Be Inherited from CSP"
IMPACT_LEVEL = "Impact Level"
SYSTEM_NAME = "System Name"
CSP = "CSP"

EXISTING_IMPLEMENTATIONS: ThreadSafeDict[int, ControlImplementation] = ThreadSafeDict()
UPDATED_IMPLEMENTATION_OBJECTIVES: ThreadSafeSet[ImplementationObjective] = ThreadSafeSet()

STATUS_MAPPING = {
    "Implemented": ControlImplementationStatus.Implemented,
    PARTIALLY_IMPLEMENTED: ControlImplementationStatus.PartiallyImplemented,
    ControlImplementationStatus.Planned.value: ControlImplementationStatus.Planned,
    "N/A": ControlImplementationStatus.NA,
    ALTERNATIVE_IMPLEMENTATION: ControlImplementationStatus.Alternative,
    ALT_IMPLEMENTATION: ControlImplementationStatus.Alternative,
}

RESPONSIBILITY_MAP = {
    # Original keys
    SERVICE_PROVIDER_CORPORATE: SERVICE_PROVIDER_CORPORATE,
    SERVICE_PROVIDER_SYSTEM_SPECIFIC: PROVIDER_SYSTEM_SPECIFIC,
    SERVICE_PROVIDER_HYBRID: "Hybrid",
    PROVIDED_BY_CUSTOMER: "Customer",
    CONFIGURED_BY_CUSTOMER: CUSTOMER_CONFIGURED,
    "Shared": "Shared",
    "Inherited": "Inherited",
    # Boolean keys
    "bServiceProviderCorporate": "Provider",
    "bServiceProviderSystemSpecific": PROVIDER_SYSTEM_SPECIFIC,
    "bServiceProviderHybrid": "Hybrid",
    "bProvidedByCustomer": "Customer",
    "bConfiguredByCustomer": CUSTOMER_CONFIGURED,
    "bShared": "Shared",
    "bInherited": "Inherited",
}
REGSCALE_SSP_ID: int = 0
INITIAL_IMPORT = True


@lru_cache(maxsize=1)
def get_pandas() -> ModuleType:
    """
    Lazily import pandas only once when needed

    :return: The pandas module
    :rtype: ModuleType
    """
    import pandas as pd

    return pd


def _build_potential_oscal_ids(variation: str) -> List[str]:
    """
    Build potential OSCAL ID formats from a control ID variation.

    :param str variation: Control ID variation (e.g., "AC-1", "AC-01", "AC-1.a")
    :return: List of potential OSCAL IDs
    :rtype: List[str]
    """
    variation_lower = variation.lower()
    oscal_ids = []

    # Check if this is a control with a letter part (e.g., "ac-1.a")
    if re.match(r"^[a-z]+-\d+\.[a-z]$", variation_lower):
        # For letter parts, map to OSCAL format: ac-1.a -> ac-1_smt.a
        base_control = variation_lower.rsplit(".", 1)[0]  # Get "ac-1" from "ac-1.a"
        letter_part = variation_lower.rsplit(".", 1)[1]  # Get "a" from "ac-1.a"
        oscal_ids.extend(
            [
                f"{base_control}_smt.{letter_part}",  # ac-1_smt.a (primary format)
                f"{variation_lower}_smt",  # ac-1.a_smt (alternative format)
            ]
        )
    else:
        # Base control without letter part - include all potential letter variations
        oscal_ids.extend(
            [
                f"{variation_lower}_smt",
                f"{variation_lower}_smt.a",
                f"{variation_lower}_smt.b",
                f"{variation_lower}_smt.c",
            ]
        )

    return oscal_ids


def _matches_oscal_id(obj_id: str, variation: str) -> bool:
    """
    Check if an objective's otherId matches any OSCAL ID format for the given variation.

    :param str obj_id: The objective's otherId
    :param str variation: Control ID variation
    :return: True if matches, False otherwise
    :rtype: bool
    """
    potential_ids = _build_potential_oscal_ids(variation)
    return obj_id in potential_ids or obj_id.startswith(f"{variation.lower()}_smt")


def _find_matching_objectives(control_objectives: List[ControlObjective], variations: set) -> List[ControlObjective]:
    """
    Find objectives that match any of the control ID variations.

    :param List[ControlObjective] control_objectives: List of objectives to search
    :param set variations: Set of control ID variations
    :return: List of matched objectives
    :rtype: List[ControlObjective]
    """
    matched_objectives = []

    for obj in control_objectives:
        if not hasattr(obj, "otherId") or not obj.otherId:
            continue

        obj_id = obj.otherId
        for variation in variations:
            if _matches_oscal_id(obj_id, variation):
                if obj not in matched_objectives:
                    matched_objectives.append(obj)
                break

    return matched_objectives


def find_objectives_using_control_matcher(
    source: str, control_objectives: List[ControlObjective], control_matcher: ControlMatcher
) -> Tuple[List[ControlObjective], str]:
    """
    Find control objectives using ControlMatcher for consistent control ID parsing and matching.

    :param str source: The source control ID (e.g., "AC-1(a)", "AC-01 (a)")
    :param List[ControlObjective] control_objectives: List of ControlObjective objects to search
    :param ControlMatcher control_matcher: Instance of ControlMatcher for parsing and variations
    :return: Tuple of (matched objectives list, status_message)
    :rtype: Tuple[List[ControlObjective], str]
    """
    # Parse the control ID using ControlMatcher
    parsed_id = control_matcher.parse_control_id(source)
    if not parsed_id:
        return [], f"Unable to parse control {source}"

    # Get all variations of this control ID
    # pylint: disable=protected-access  # Using internal method for control ID variation matching
    variations = control_matcher._get_control_id_variations(parsed_id)
    if not variations:
        return [], f"Unable to generate variations for {source}"

    # Find matching objectives
    matched_objectives = _find_matching_objectives(control_objectives, variations)

    if matched_objectives:
        return matched_objectives, f"Found {len(matched_objectives)} objective(s) for {source}"

    return [], f"No database match found for {source} (parsed: {parsed_id})"


def transform_control(control: str) -> str:
    """
    Function to parse the control string and transform it to the RegScale format
    ex: AC-1 (a) -> ac-1.a or AC-6 (10) -> ac-6.10

    :param str control: Control ID as a string
    :return: Transformed control ID to match RegScale control ID format
    :rtype: str
    """
    # Use regex to match the pattern and capture the parts (handle extra spaces)
    # Now handles both uppercase and lowercase letters in parentheses
    if match := re.match(r"([A-Z]+)-(\d+)\s*\(\s*(\d+|[A-Z])\s*\)", control, re.IGNORECASE):
        control_name = match.group(1).lower()
        control_number = match.group(2)
        try:
            sub_control = match.group(3).lower()  # Normalize to lowercase
            transformed_control = f"{control_name}-{control_number}.{sub_control}"
        except IndexError:
            transformed_control = f"{control_name}-{control_number}"

        return transformed_control
    return control.lower()


def new_leveraged_auth(
    ssp: SecurityPlan, user_id: str, instructions_data: dict, version: Literal["rev4", "rev5"]
) -> int:
    """
    Function to create a new Leveraged Authorization in RegScale.

    :param SecurityPlan ssp: RegScale SSP Object
    :param str user_id: RegScale user ID
    :param dict instructions_data: Data parsed from Instructions worksheet in the FedRAMP CIS CRM workbook
    :param Literal["rev4", "rev5"] version: FedRAMP revision version
    :return: Newly created Leveraged Authorization ID in RegScale
    :rtype: int
    """
    leveraged_auth = LeveragedAuthorization(
        title=instructions_data[CSP],
        servicesUsed=instructions_data[CSP],
        fedrampId=(instructions_data["System Identifier"] if version == "rev5" else instructions_data[SYSTEM_NAME]),
        authorizationType="FedRAMP Ready",
        impactLevel=instructions_data[IMPACT_LEVEL],
        dateAuthorized="",
        natureOfAgreement="Other",
        dataTypes="Other",
        authorizedUserTypes="Other",
        authenticationType="Other",
        createdById=user_id,
        securityPlanId=ssp.id,
        ownerId=user_id,
        lastUpdatedById=user_id,
        description="Imported from FedRAMP CIS CRM Workbook on " + get_current_datetime("%m/%d/%Y %H:%M:%S"),
    )
    new_leveraged_auth_id = leveraged_auth.create()
    return new_leveraged_auth_id.id


def gen_key(control_id: str) -> str:
    """
    Function to generate a key for the control ID by stripping letter-based parts.
    Handles both parentheses notation (AC-1(a)) and dot notation (ac-1.a).

    Examples:
    - AC-1 (a) -> AC-1
    - ac-1.a -> ac-1
    - AC-2(1) -> AC-2(1) (numeric enhancement preserved)
    - AC-17.2 -> AC-17.2 (numeric enhancement preserved)

    :param str control_id: The control ID to generate a key for
    :return: The generated key with letter parts stripped
    :rtype: str
    """
    # First, try parentheses notation: ALPHA-NUM(LETTER) -> ALPHA-NUM
    # Captures everything up to either:
    # 1. The last (number) if it exists (preserved)
    # 2. The main control number if no enhancement exists
    # Excludes trailing (letter) - handles extra spaces like AC-6 ( 1 ) ( a )
    pattern_paren = r"^(\w+-\d+(?:\s*\(\s*\d+\s*\))?)(?:\s*\(\s*[a-zA-Z]\s*\))?$"
    if match := re.match(pattern_paren, control_id):
        return match.group(1)

    # Try dot notation: alpha-num.letter -> alpha-num
    # Preserves numeric enhancements (ac-17.2) but strips letter parts (ac-1.a)
    pattern_dot = r"^([a-z]+-\d+)\.([a-z])$"
    if match := re.match(pattern_dot, control_id, re.IGNORECASE):
        # Check if the part after dot is a single letter (not a number)
        return match.group(1)

    # No match, return as-is
    return control_id


def _is_letter_based_control_part(control_id: str) -> bool:
    """
    Check if a control ID is a letter-based part (e.g., AC-1(a), ac-1.a).
    Returns True for ALPHA-NUMERIC(ALPHA) or alpha-numeric.alpha patterns.
    Returns False for numeric enhancements (AC-1(1), ac-17.2).

    :param str control_id: The control ID to check
    :return: True if it's a letter-based control part
    :rtype: bool
    """
    # Pattern 1: Parentheses notation - ALPHA-NUMERIC(ALPHA) like AC-1(a), AC-2(B)
    pattern_paren = r"^[A-Za-z]+-\d+\s*\(\s*[a-zA-Z]\s*\)$"
    if re.match(pattern_paren, control_id):
        return True

    # Pattern 2: Dot notation - alpha-numeric.alpha like ac-1.a, ac-2.b
    # Exclude numeric enhancements like ac-17.2
    pattern_dot = r"^[a-z]+-\d+\.([a-z])$"
    match = re.match(pattern_dot, control_id, re.IGNORECASE)
    if match and match.group(1).isalpha():
        return True

    return False


def map_implementation_status(control_id: str, cis_data: dict) -> str:
    """
    Function to map the selected implementation status on the CIS worksheet to a RegScale status.
    Aggregates letter-based control parts (AC-1(a), AC-1(b), AC-1(c)) into base control (AC-1).

    Aggregation logic for letter-based parts:
    - All "Implemented" → "Fully Implemented"
    - Mix with at least one "Implemented" → "Partially Implemented"
    - All "Not Implemented" or empty → "Not Implemented"
    - Any "Planned" (no implemented) → "Planned"

    :param str control_id: The control ID from RegScale
    :param dict cis_data: Data from the CIS worksheet to map the status from
    :return: RegScale control implementation status
    :rtype: str
    """

    # Extract matching records (gen_key strips letter parts to match base control)
    cis_records = [
        value
        for value in cis_data.values()
        if gen_key(value.get("regscale_control_id", "")).lower() == control_id.lower()
    ]

    status_ret = ControlImplementationStatus.NotImplemented

    logger.debug("Found %d CIS records for control %s", len(cis_records), control_id)

    if not cis_records:
        # Alerts if a control exists in regscale but is missing from CIS worksheet
        logger.warning(f"No CIS records found for control {control_id}")
        return status_ret

    # Check if these are letter-based control parts that need aggregation
    has_letter_parts = any(_is_letter_based_control_part(rec.get("control_id", "")) for rec in cis_records)

    # Count implementation statuses
    status_counts = Counter(record.get("implementation_status", "") for record in cis_records)
    logger.debug("Status distribution for %s: %s (letter parts: %s)", control_id, dict(status_counts), has_letter_parts)

    # Early return for simple case: all same status
    if len(status_counts) == 1:
        status = next(iter(status_counts))
        mapped_status = STATUS_MAPPING.get(status, ControlImplementationStatus.NotImplemented)
        # If all letter parts have same status and it's "Implemented", return FullyImplemented
        if has_letter_parts and status == "Implemented":
            return ControlImplementationStatus.FullyImplemented
        return mapped_status

    # Aggregate statuses for letter-based control parts or multiple records
    implemented_count = status_counts.get("Implemented", 0)
    not_implemented_count = status_counts.get("", 0)  # Empty status counts as not implemented
    partially_implemented_count = status_counts.get("Partially Implemented", 0)
    planned_count = status_counts.get("Planned", 0)
    total_count = sum(status_counts.values())

    # Aggregation logic
    if implemented_count == total_count:
        # All parts are implemented
        return ControlImplementationStatus.FullyImplemented
    elif implemented_count > 0 or partially_implemented_count > 0:
        # Mix of implemented and other statuses, or any partially implemented
        return ControlImplementationStatus.PartiallyImplemented
    elif planned_count > 0 and not_implemented_count == 0:
        # All are planned (no not-implemented)
        return ControlImplementationStatus.Planned
    elif any(status in ["N/A", ALTERNATIVE_IMPLEMENTATION] for status in status_counts):
        # Any N/A or Alternative
        return ControlImplementationStatus.NA
    else:
        # Default: not implemented
        return ControlImplementationStatus.NotImplemented


def map_origination(control_id: str, cis_data: dict) -> dict:
    """
    Map control implementation responsibility from CRM worksheet data.

    :param control_id: RegScale control ID
    :param cis_data: Data from the CRM worksheet
    :return: Responsibility information in regscale format
    """
    # Define mapping of origination strings to boolean keys
    origination_mapping = {
        SERVICE_PROVIDER_CORPORATE: "bServiceProviderCorporate",
        SERVICE_PROVIDER_SYSTEM_SPECIFIC: "bServiceProviderSystemSpecific",
        SERVICE_PROVIDER_HYBRID: "bServiceProviderHybrid",
        PROVIDED_BY_CUSTOMER: "bProvidedByCustomer",
        CONFIGURED_BY_CUSTOMER: "bConfiguredByCustomer",
        SHARED: "bShared",
        INHERITED: "bInherited",
    }

    # Initialize result with all flags set to False
    result = dict.fromkeys(origination_mapping.values(), False)
    result["record_text"] = ""

    # Find matching CIS records
    matching_records = [
        record
        for record in cis_data.values()
        if record.get("regscale_control_id") and gen_key(record["regscale_control_id"]).lower() == control_id.lower()
    ]

    # Process each matching record
    for record in matching_records:
        control_origination = record.get("control_origination", "")

        # Set flags based on origination string content
        for origination_str, bool_key in origination_mapping.items():
            if origination_str in control_origination:
                result[bool_key] = True
        if control_origination not in result["record_text"]:
            result["record_text"] += control_origination

    return result


def clean_customer_responsibility(value: str):
    """
    Function to clean the customer responsibility value

    :param str value: The value to clean
    :return: The cleaned value
    :rtype: str
    """
    if not value:
        return ""
    try:
        return "" if math.isnan(float(value)) else str(value)
    except (ValueError, TypeError):
        return str(value)


def get_multi_status(record: dict) -> str:
    """
    Function to get the multi-select status from the record
    """
    status_list = []
    status_map = {
        "Implemented": ControlImplementationStatus.Implemented.value,
        "Planned": ControlImplementationStatus.Implemented.Planned.value,
        PARTIALLY_IMPLEMENTED: PARTIALLY_IMPLEMENTED,
        "N/A": ControlImplementationStatus.NA.value,
        NOT_IMPLEMENTED: NOT_IMPLEMENTED,
        "Not Applicable": ControlImplementationStatus.NA.value,
        ALTERNATIVE_IMPLEMENTATION: ControlImplementationStatus.Alternative.value,
        ALT_IMPLEMENTATION: ControlImplementationStatus.Alternative.value,
    }
    # Get implementation status with default value
    implementation_status = record.get("implementation_status", NOT_IMPLEMENTED)

    # Handle empty or None status
    if not implementation_status:
        return NOT_IMPLEMENTED

    if RegscaleVersion.meets_minimum_version("6.20.17.0"):
        # Process multiple statuses
        status_list = []
        for status in implementation_status.split(","):
            status = status.strip()
            if status not in status_map:
                logger.warning(f"Unknown implementation status: {status}")
                continue
            status_list.append(status_map[status])
        return ",".join(status_list) if status_list else NOT_IMPLEMENTED
    else:
        # Legacy method - single status
        return status_map.get(implementation_status, NOT_IMPLEMENTED)


def _calculate_responsibility(control_originations: List[str], imp: ControlImplementation) -> str:
    """
    Calculate responsibility from control originations.

    :param List[str] control_originations: List of control origination values
    :param ControlImplementation imp: Control implementation
    :return: Calculated responsibility value
    :rtype: str
    """
    try:
        if RegscaleVersion.meets_minimum_version("6.20.17.0"):
            return ",".join(control_originations)
        return next(iter(control_originations))
    except StopIteration:
        if imp.responsibility:
            return imp.responsibility.split(",")[0]
        return SERVICE_PROVIDER_CORPORATE


def _create_new_implementation_objective(
    leverage_auth_id: int,
    imp: ControlImplementation,
    objective: ControlObjective,
    cis_record: dict,
    responsibility: str,
    cloud_responsibility: str,
    customer_responsibility: str,
    can_be_inherited_from_csp: str,
) -> ImplementationObjective:
    """
    Create a new implementation objective.

    :param int leverage_auth_id: Leveraged authorization ID
    :param ControlImplementation imp: Control implementation
    :param ControlObjective objective: Control objective
    :param dict cis_record: CIS record data
    :param str responsibility: Responsibility value
    :param str cloud_responsibility: Cloud responsibility value
    :param str customer_responsibility: Customer responsibility value
    :param str can_be_inherited_from_csp: Can be inherited flag
    :return: New implementation objective
    :rtype: ImplementationObjective
    """
    imp_obj = ImplementationObjective(
        id=0,
        uuid="",
        inherited=can_be_inherited_from_csp in ["Yes", "Partial"],
        implementationId=imp.id,
        status=get_multi_status(cis_record),
        objectiveId=objective.id,
        notes=objective.name,
        securityControlId=objective.securityControlId,
        securityPlanId=REGSCALE_SSP_ID,
        responsibility=responsibility,
        cloudResponsibility=cloud_responsibility,
        customerResponsibility=customer_responsibility,
        authorizationId=leverage_auth_id,
        parentObjectiveId=objective.parentObjectiveId,
    )
    logger.debug(
        "Creating new Implementation Objective for Control %s with status: %s responsibility: %s",
        imp_obj.securityControlId,
        imp_obj.status,
        imp_obj.responsibility,
    )
    return imp_obj


def _update_existing_implementation_objective(
    ex_obj: ImplementationObjective,
    cis_record: dict,
    responsibility: str,
    cloud_responsibility: str,
    customer_responsibility: str,
) -> None:
    """
    Update an existing implementation objective.

    :param ImplementationObjective ex_obj: Existing implementation objective
    :param dict cis_record: CIS record data
    :param str responsibility: Responsibility value
    :param str cloud_responsibility: Cloud responsibility value
    :param str customer_responsibility: Customer responsibility value
    :rtype: None
    """
    ex_obj.status = get_multi_status(cis_record)
    ex_obj.responsibility = responsibility
    if cloud_responsibility.strip():
        logger.debug(f"Updating Implementation Objective #{ex_obj.id} with responsibility: {responsibility}")
        ex_obj.cloudResponsibility = cloud_responsibility
    if customer_responsibility.strip():
        logger.debug(
            f"Updating Implementation Objective #{ex_obj.id} with cloud responsibility: {cloud_responsibility}"
        )
        ex_obj.customerResponsibility = customer_responsibility


def update_imp_objective(
    leverage_auth_id: int,
    existing_imp_obj: List[ImplementationObjective],
    imp: ControlImplementation,
    objectives: List[ControlObjective],
    record: dict,
) -> None:
    """
    Update the control objectives with the given record data.

    :param int leverage_auth_id: The leveraged authorization ID
    :param List[ImplementationObjective] existing_imp_obj: The existing implementation objective
    :param ControlImplementation imp: The control implementation to update
    :param List[ControlObjective] objectives: The control objective to update
    :param dict record: The CIS/CRM record data to update the objective with
    :rtype: None
    :return: None
    """
    cis_record = record.get("cis", {})
    crm_record = record.get("crm", {})

    # Parse and clean control originations
    control_originations = [orig.strip() for orig in cis_record.get("control_origination", "").split(",")]

    # Calculate responsibility
    responsibility = _calculate_responsibility(control_originations, imp)

    # Parse responsibility fields
    customer_responsibility = clean_customer_responsibility(
        crm_record.get("specific_inheritance_and_customer_agency_csp_responsibilities")
    )
    can_be_inherited_from_csp: str = crm_record.get("can_be_inherited_from_csp") or ""
    cloud_responsibility = customer_responsibility if can_be_inherited_from_csp.lower() == "yes" else ""
    customer_responsibility = customer_responsibility if can_be_inherited_from_csp.lower() != "yes" else ""

    existing_pairs = {(obj.objectiveId, obj.implementationId) for obj in existing_imp_obj}
    logger.debug(f"CRM Record: {crm_record}")

    for objective in objectives:
        if objective.securityControlId != imp.controlID:
            continue

        current_pair = (objective.id, imp.id)
        if current_pair not in existing_pairs:
            imp_obj = _create_new_implementation_objective(
                leverage_auth_id,
                imp,
                objective,
                cis_record,
                responsibility,
                cloud_responsibility,
                customer_responsibility,
                can_be_inherited_from_csp,
            )
            UPDATED_IMPLEMENTATION_OBJECTIVES.add(imp_obj)
        else:
            ex_obj = next((obj for obj in existing_imp_obj if obj.objectiveId == objective.id), None)
            if ex_obj:
                _update_existing_implementation_objective(
                    ex_obj, cis_record, responsibility, cloud_responsibility, customer_responsibility
                )
                UPDATED_IMPLEMENTATION_OBJECTIVES.add(ex_obj)


def parse_control_details(
    version: Literal["rev4", "rev5"], control_imp: ControlImplementation, control: SecurityControl, cis_data: dict
) -> ControlImplementation:
    """
    Function to parse control details from RegScale and CIS data and returns an updated ControlImplementation object

    :param Literal["rev4", "rev5"] version: The version of the workbook
    :param ControlImplementation control_imp: RegScale ControlImplementation object to update
    :param SecurityControl control: RegScale control
    :param dict cis_data: Data from the CIS worksheet
    :return: Updated ControlImplementation object
    :rtype: ControlImplementation
    """
    control_id = control.controlId if version == "rev5" else control.sortId
    status = map_implementation_status(control_id=control_id, cis_data=cis_data)
    origination_bool = map_origination(control_id=control_id, cis_data=cis_data)
    control_imp.status = status
    if status == ControlImplementationStatus.Planned:
        control_imp.plannedImplementationDate = get_current_datetime("%Y-%m-%d")
        control_imp.stepsToImplement = "To be updated"
    control_imp.controlSource = "Baseline" if not origination_bool["bInherited"] else "Inherited"
    control_imp.exclusionJustification = (
        "Imported from FedRAMP CIS CRM Workbook" if status == ControlImplementationStatus.NA else None
    )

    control_imp.bInherited = origination_bool["bInherited"]
    control_imp.inheritable = origination_bool["bInherited"]
    control_imp.bServiceProviderCorporate = origination_bool["bServiceProviderCorporate"]
    control_imp.bServiceProviderSystemSpecific = origination_bool["bServiceProviderSystemSpecific"]
    control_imp.bServiceProviderHybrid = origination_bool["bServiceProviderHybrid"]
    control_imp.bConfiguredByCustomer = origination_bool["bConfiguredByCustomer"]
    control_imp.bShared = origination_bool["bShared"]
    control_imp.bProvidedByCustomer = origination_bool["bProvidedByCustomer"]
    control_imp.responsibility = get_responsibility(origination_bool)
    logger.debug(f"Control Implementation Responsibility: {control_imp.responsibility}")
    logger.debug(f"Control Implementation Status: {control_imp.status}")
    if status == ControlImplementationStatus.Planned:
        control_imp.stepsToImplement = "PLANNED"
        control_imp.plannedImplementationDate = get_current_datetime("%Y-%m-%d")
    if status in [ControlImplementationStatus.Planned, ControlImplementationStatus.NotImplemented]:
        control_imp.exclusionJustification = "Imported from FedRAMP CIS CRM Workbook"
    if updated_control := control_imp.save():
        logger.debug("Control Implementation #%s updated successfully", control_imp.id)
        return updated_control
    logger.error("Failed to update Control Implementation \n" + json.dumps(control_imp.model_dump()))
    return control_imp


def get_responsibility(origination_bool: dict) -> str:
    """
    Function to map the responsibility based on origination booleans.
    Returns comma-separated string of all responsibilities for True booleans.

    :param dict origination_bool: Dictionary containing origination booleans
    :return: Comma-separated responsibility string
    :rtype: str
    """
    responsibilities = []

    if origination_bool.get("bServiceProviderCorporate", False):
        responsibilities.append(SERVICE_PROVIDER_CORPORATE)
    if origination_bool.get("bServiceProviderSystemSpecific", False):
        responsibilities.append(SERVICE_PROVIDER_SYSTEM_SPECIFIC)
    if origination_bool.get("bServiceProviderHybrid", False):
        responsibilities.append(SERVICE_PROVIDER_HYBRID)
    if origination_bool.get("bProvidedByCustomer", False):
        responsibilities.append(PROVIDED_BY_CUSTOMER)
    if origination_bool.get("bConfiguredByCustomer", False):
        responsibilities.append(CONFIGURED_BY_CUSTOMER)
    if origination_bool.get("bInherited", False):
        responsibilities.append(INHERITED)
    if origination_bool.get("bShared", False):
        responsibilities.append(SHARED)

    # Return comma-separated string, or NA if no responsibilities found
    return ",".join(responsibilities) if responsibilities else ControlImplementationStatus.NA.value


def fetch_and_update_imps(
    control: dict, api: Api, cis_data: dict, version: Literal["rev4", "rev5"]
) -> Optional[ControlImplementation]:
    """
    Function to fetch implementation objectives from RegScale via API

    :param dict control: RegScale control as a dictionary
    :param Api api: RegScale API object
    :param dict cis_data: Data from the CIS worksheet
    :param Literal["rev4", "rev5"] version: The version of the workbook
    :return: An updated control implementation if found
    :rtype: Optional[ControlImplementation]
    """
    # get the control and control implementation objects
    regscale_control = SecurityControl.get_object(control.controlID)
    if not regscale_control:
        api.logger.error(f"Failed to fetch control with ID {control['scId']}")
        return None

    control_id = regscale_control.controlId if regscale_control else ""
    security_control_id = regscale_control.id if regscale_control else 0
    regscale_control_imp = EXISTING_IMPLEMENTATIONS.get(security_control_id)

    if not regscale_control_imp:
        api.logger.error(f"Failed to find control implementation for control ID {control_id}")
        return None

    updated_control = parse_control_details(
        version=version, control_imp=regscale_control_imp, control=regscale_control, cis_data=cis_data
    )

    # Find the index of the old implementation and replace it with the updated one
    EXISTING_IMPLEMENTATIONS[updated_control.controlID] = updated_control

    return updated_control


def get_all_imps(api: Api, cis_data: dict, version: Literal["rev4", "rev5"]) -> None:
    """
    Function to retrieve control implementations and their objectives from RegScale

    :param Api api: The RegScale API object
    :param dict cis_data: The data from the CIS worksheet
    :param Literal["rev4", "rev5"] version: The version of the workbook
    :return: None
    :rtype: None
    """
    # Check if the response is successful
    if EXISTING_IMPLEMENTATIONS:
        # Get Control Implementations For SSP
        fetching_imps = progress.add_task(
            f"[magenta]Updating {len(EXISTING_IMPLEMENTATIONS)} implementation(s)...",
            total=len(EXISTING_IMPLEMENTATIONS),
        )
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [
                executor.submit(fetch_and_update_imps, control, api, cis_data, version)
                for control in EXISTING_IMPLEMENTATIONS.values()
            ]

            # Just wait for all tasks to complete
            for future in as_completed(futures):
                try:
                    # Only call result() to propagate any exceptions
                    future.result()
                    progress.update(fetching_imps, advance=1)
                except Exception as e:
                    logger.error(f"Error updating implementation: {e}")


def get_all_control_objectives(imps: List[ControlImplementation]) -> List[ControlObjective]:
    """
    Get All Control Objectives from GraphQL

    :param List[ControlImplementation] imps: The Implementations
    :return: List of ControlObjective
    :rtype: List[ControlObjective]
    """
    api = Api()
    res = []
    # list of int to string
    if imps:
        query = GraphQLQuery()
        query.start_query()
        query.add_query(
            entity="controlObjectives",
            items=["id", "description", "otherId", "name", "securityControlId"],
            where={"securityControlId": {"in": [c.controlID for c in imps]}},
        )
        query.end_query()
        dat = api.graph(query=query.build())
        res = [ControlObjective(**d) for d in dat.get("controlObjectives", {}).get("items", [])]
    return res


def clean_key(key: str) -> str:
    """
    Clean the key by removing spaces
    """
    return key.replace(" ", "")


def update_all_objectives(
    leveraged_auth_id: int,
    cis_data: Dict[str, Dict[str, str]],
    crm_data: Dict[str, Dict[str, str]],
    version: Literal["rev4", "rev5"],
) -> set:
    """
    Updates all objectives for the given control implementations based on CIS worksheet data.
    Uses parallel processing and displays progress bars.

    :param int leveraged_auth_id: The leveraged authorization ID
    :param Dict[str, Dict[str, str]] cis_data: The CIS data to update from
    :param Dict[str, Dict[str, str]] crm_data: The CRM data to update from
    :param Literal["rev4", "rev5"] version: The version of the workbook
    :return: A set of errors, if any
    :rtype: set
    """

    all_control_objectives = get_all_control_objectives(imps=EXISTING_IMPLEMENTATIONS.values())
    # Create ControlMatcher instance for consistent control ID parsing
    control_matcher = ControlMatcher()

    error_set = set()
    process_task = progress.add_task(
        "[cyan]Processing control objectives...", total=len(EXISTING_IMPLEMENTATIONS.values())
    )
    # Create a combined dataset for easier access
    combined_data = {key: {"cis": cis_data[key], "crm": crm_data.get(clean_key(key), {})} for key in cis_data}

    # Process implementations in parallel
    with ThreadPoolExecutor(max_workers=30) as executor:
        # Submit all tasks
        future_to_control = {
            executor.submit(
                process_implementation,
                leveraged_auth_id,
                imp,
                combined_data,
                version,
                all_control_objectives,
                control_matcher,
            ): imp
            for imp in EXISTING_IMPLEMENTATIONS.values()
        }

        # Process results as they complete
        for future in as_completed(future_to_control):
            result = future.result()
            if isinstance(result[0], list):
                error_lst = result[0]
                for inf in error_lst:
                    error_set.add(inf)
            progress.update(process_task, advance=1)
    save_task = progress.add_task("[yellow]Saving control objectives...", total=len(UPDATED_IMPLEMENTATION_OBJECTIVES))
    # Process implementations in parallel
    # Note, not using threadpool executor here due to phantom 500 errors. This is a workaround
    for obj in UPDATED_IMPLEMENTATION_OBJECTIVES:
        try:
            obj.create_or_update()
            progress.update(save_task, advance=1)
        except APIInsertionError as e:
            error_set.add(f"Failed to create Implementation Objective: {e}")
        except APIUpdateError as e:
            error_set.add(f"Failed to update Implementation Objective: {e}")
    return error_set


def report(error_set: set):
    """
    Function to report errors to the user

    :param set error_set: Set of errors to report
    :rtype: None
    """
    from rich.console import Console
    from rich.table import Table

    console = Console()

    if error_set:
        table = Table(title="Unmapped Control Objectives")

        table.add_column(justify="left", style="red", no_wrap=True)

        for error in sorted(error_set):
            table.add_row(error)

        console.print(table)


def process_implementation(
    leveraged_auth_id: int,
    implementation: ControlImplementation,
    sheet_data: dict,
    version: Literal["rev4", "rev5"],
    all_objectives: List[ControlObjective],
    control_matcher: ControlMatcher,
) -> Tuple[List[str], List[ImplementationObjective]]:
    """
    Processes a single implementation and its associated records.

    :param int leveraged_auth_id: The leveraged authorization ID
    :param ControlImplementation implementation: The control implementation to process
    :param dict sheet_data: The CIS/CRM data to process
    :param Literal["rev4", "rev5"] version: The version of the workbook
    :param List[ControlObjective] all_objectives: all the control objectives
    :param ControlMatcher control_matcher: ControlMatcher instance for control ID parsing
    :rtype Tuple[List[str], List[ImplementationObjective]]
    :returns A list of updated implementation objectives
    """

    errors = []
    processed_objectives = []

    existing_objectives, filtered_records = gen_filtered_records(implementation, sheet_data, control_matcher)
    result = None
    for record in filtered_records:
        res = process_single_record(
            leveraged_auth_id=leveraged_auth_id,
            implementation=implementation,
            record=record,
            control_objectives=all_objectives,
            existing_objectives=existing_objectives,
            version=version,
            control_matcher=control_matcher,
        )
        if isinstance(res, tuple):
            method_errors, result = res
            errors.extend(method_errors)
        if result:
            processed_objectives.append(result)
    # Update Control Origin at the Implementation Level
    return errors, processed_objectives


def _extract_base_control_id(control_id: str) -> str:
    """
    Extract the base control ID from a control ID that may have a letter part.

    Examples:
    - "AC-1.a" -> "AC-1"
    - "AC-17.2" -> "AC-17.2" (numeric parts are preserved)
    - "AC-1" -> "AC-1"

    :param str control_id: Control ID that may have a letter part
    :return: Base control ID without letter part
    :rtype: str
    """
    # Check if the control has a letter part (e.g., AC-1.a)
    match = re.match(r"^([A-Z]+-\d+)\.[A-Z]$", control_id, re.IGNORECASE)
    if match:
        return match.group(1)
    return control_id


def gen_filtered_records(
    implementation: ControlImplementation, sheet_data: dict, control_matcher: ControlMatcher
) -> Tuple[List[ImplementationObjective], List[Dict[str, str]]]:
    """
    Generates filtered records for a given implementation using ControlMatcher.

    :param ControlImplementation implementation: The control implementation to filter records for
    :param dict sheet_data: The CIS/CRM data to filter
    :param ControlMatcher control_matcher: ControlMatcher instance for control ID matching
    :returns A tuple of existing objectives, and filtered records
    :rtype Tuple[List[ImplementationObjective], List[Dict[str, str]]]
    """
    security_control = SecurityControl.get_object(implementation.controlID)
    existing_objectives = ImplementationObjective.get_by_control(implementation.id)

    # Get all variations of the control ID using ControlMatcher
    # pylint: disable=protected-access  # Using internal method for control ID variation matching
    control_variations = control_matcher._get_control_id_variations(security_control.controlId)

    # Filter records that match any variation of the control ID
    filtered_records = []
    for record in sheet_data.values():
        record_control_id = record["cis"].get("regscale_control_id", "")
        # Parse the record's control ID
        parsed_record_id = control_matcher.parse_control_id(record_control_id)
        if not parsed_record_id:
            continue
        # Get variations for the parsed record ID
        # pylint: disable=protected-access  # Using internal method for control ID variation matching
        record_variations = control_matcher._get_control_id_variations(parsed_record_id)

        # Check if the parsed record control ID matches any variation
        if control_variations & record_variations:
            filtered_records.append(record)
        else:
            # If no direct match and record has a letter part, try matching the base control
            base_control_id = _extract_base_control_id(parsed_record_id)
            if base_control_id != parsed_record_id:
                base_variations = control_matcher._get_control_id_variations(base_control_id)
                if control_variations & base_variations:
                    filtered_records.append(record)

    return existing_objectives, filtered_records


def get_matching_cis_records(control_id: str, cis_data: dict) -> List[Dict[str, str]]:
    """
    Finds matching CIS records for a given control ID.

    :param str control_id: The control ID to match
    :param dict cis_data: The CIS data to search
    :rtype List[Dict[str, str]]
    :returns A list of matching CIS records
    """
    return [value for value in cis_data.values() if value["regscale_control_id"].lower() == control_id.lower()]


def process_single_record(**kwargs) -> Tuple[List[str], Optional[ImplementationObjective]]:
    """
    Processes a single CIS record and returns updated objective if successful.

    :rtype Tuple[List[str], Optional[ImplementationObjective]]
    :returns A list of errors and the Implementation Objective if successful, otherwise None
    """
    errors = []
    leveraged_auth_id: int = kwargs.get("leveraged_auth_id")
    implementation: ControlImplementation = kwargs.get("implementation")
    record: dict = kwargs.get("record")
    control_objectives: List[ControlObjective] = kwargs.get("control_objectives")
    existing_objectives: List[ImplementationObjective] = kwargs.get("existing_objectives")
    control_matcher: ControlMatcher = kwargs.get("control_matcher")
    result = None

    # Get the control ID from the CIS/CRM record
    key = record["cis"]["control_id"]

    # Use ControlMatcher to find matching objectives
    mapped_objectives, status = find_objectives_using_control_matcher(key, control_objectives, control_matcher)

    logger.debug(f"Control matching result for {key}: {status}")

    # Add to errors list if no objectives found
    if not mapped_objectives:
        errors.append(f"{key}: {status}")
    else:
        # Update implementation objectives with the matched control objectives
        update_imp_objective(
            leverage_auth_id=leveraged_auth_id,
            existing_imp_obj=existing_objectives,
            imp=implementation,
            objectives=mapped_objectives,
            record=record,
        )

    return errors, result


def parse_crm_worksheet(file_path: click.Path, crm_sheet_name: str, version: Literal["rev4", "rev5"]) -> dict:
    """
    Function to format CRM content.

    :param click.Path file_path: The file path to the FedRAMP CIS CRM workbook
    :param str crm_sheet_name: The name of the CRM sheet to parse
    :param Literal["rev4", "rev5"] version: The version of the workbook
    :return: Formatted CRM content
    :rtype: dict
    """
    logger.info("Parsing CRM worksheet...")
    formatted_crm = {}

    if not crm_sheet_name:
        return formatted_crm

    # Value for rev4
    skip_rows = 3

    validator = ImportValidater(
        file_path=file_path,
        disable_mapping=True,
        required_headers=[],
        mapping_file_path=gettempdir(),
        prompt=False,
        ignore_unnamed=True,
        worksheet_name=crm_sheet_name,
        warn_extra_headers=False,
    )

    if validator.data.empty:
        return {}

    # find index of row where the first column == Control ID
    skip_rows = determine_skip_row(original_df=validator.data, text_to_find=CONTROL_ID, original_skip=skip_rows)

    logger.debug(f"Skipping {skip_rows} rows in CRM worksheet")

    # Define required columns
    required_columns = [
        CONTROL_ID,
        "Can Be Inherited from CSP",
        "Specific Inheritance and Customer Agency/CSP Responsibilities",
    ]

    try:
        # Get the header row (which is at skip_rows - 1)
        header_row = validator.data.iloc[skip_rows - 1]

        # Get data rows starting from skip_rows
        data = validator.data.iloc[skip_rows:].reset_index(drop=True)

        # Set column names from header row
        data.columns = header_row

        # Find required columns by name (case-insensitive, handle extra columns in AWS CIS/CRM)
        available_columns = data.columns.tolist()
        columns_to_use = []
        missing_columns = []

        for required_col in required_columns:
            # Find column that matches (case-insensitive, strip whitespace)
            matching_col = next(
                (col for col in available_columns if str(col).strip().lower() == required_col.lower()), None
            )
            if matching_col is not None:
                columns_to_use.append(matching_col)
            else:
                missing_columns.append(required_col)

        if missing_columns:
            error_msg = (
                f"Required columns not found in the CRM worksheet: {', '.join(missing_columns)}\n"
                f"Available columns: {', '.join(str(col) for col in available_columns)}"
            )
            error_and_exit(error_msg)

        logger.debug(f"Found all required columns in CRM worksheet: {', '.join(required_columns)}")

        # Keep only the required columns
        data = data[columns_to_use]

        # Rename the columns to standardize names
        data.columns = required_columns
        logger.debug(f"Using columns: {', '.join(required_columns)}")

    except KeyError as e:
        error_and_exit(f"KeyError: {e} - One or more columns specified in usecols are not found in the dataframe.")
    except Exception as e:
        error_and_exit(f"An error occurred while processing CRM worksheet: {str(e)}")
    # Filter rows where "Can Be Inherited from CSP" is not equal to "No"
    exclude_no = data[data[CAN_BE_INHERITED_CSP] != "No"]

    # Iterate through each row and add to the dictionary
    for _, row in exclude_no.iterrows():
        control_id = row[CONTROL_ID]
        if version == "rev5":
            control_id = row[CONTROL_ID].replace(" ", "")

        # Convert camel case to snake case, remove special characters, and convert to lowercase
        clean_control_id = re.sub(r"\W+", "", control_id)
        clean_control_id = re.sub("([a-z0-9])([A-Z])", r"\1_\2", clean_control_id).lower()

        # Handle NaN values for the specific inheritance field
        inheritance_field = row["Specific Inheritance and Customer Agency/CSP Responsibilities"]
        if get_pandas().isna(inheritance_field):
            inheritance_field = ""

        # Use clean_control_id as the key to avoid overwriting
        formatted_crm[control_id] = {
            "control_id": control_id,
            "clean_control_id": clean_control_id,
            "regscale_control_id": transform_control(control_id),
            "can_be_inherited_from_csp": row[CAN_BE_INHERITED_CSP],
            "specific_inheritance_and_customer_agency_csp_responsibilities": inheritance_field,
        }

    return formatted_crm


def _get_expected_cis_columns() -> List[str]:
    """
    Get the expected column names for CIS worksheet in order.
    These match the FedRAMP Rev 5 CIS worksheet format.

    :return: List of expected column names
    :rtype: List[str]
    """
    return [
        CONTROL_ID,  # "Control ID"
        "Implemented",
        ControlImplementationStatus.PartiallyImplemented,  # "Partially Implemented"
        "Planned",
        ALTERNATIVE_IMPLEMENTATION,  # "Alternative Implementation"
        ControlImplementationStatus.NA,  # "N/A"
        SERVICE_PROVIDER_CORPORATE,
        SERVICE_PROVIDER_SYSTEM_SPECIFIC,
        SERVICE_PROVIDER_HYBRID,
        CONFIGURED_BY_CUSTOMER,
        PROVIDED_BY_CUSTOMER,
        SHARED,
        INHERITED,  # "Inherited from pre-existing FedRAMP Authorization"
    ]


def _normalize_cis_columns(cis_df: "pd.DataFrame", expected_columns: List[str]) -> "pd.DataFrame":
    """
    Normalize CIS dataframe columns by matching expected columns and handling missing ones.
    Uses fuzzy matching to handle truncated column names from merged cells.

    :param pd.DataFrame cis_df: The CIS dataframe
    :param List[str] expected_columns: List of expected column names
    :return: Normalized dataframe with standardized column names
    :rtype: pd.DataFrame
    """
    available_columns = cis_df.columns.tolist()
    columns_to_keep = []

    logger.debug(f"Available CIS columns: {available_columns}")

    for expected_col in expected_columns:
        matching_col = None

        # Try exact match first (case-insensitive)
        matching_col = next(
            (col for col in available_columns if str(col).strip().lower() == expected_col.lower()), None
        )

        # If no exact match, try partial/fuzzy match for truncated column names
        if matching_col is None:
            # Create a simplified version for matching (first few significant words)
            # Filter out common words and take first 3 significant words
            skip_words = {"from", "by", "to", "the", "and", "or", "a", "an"}
            expected_words = [w for w in expected_col.lower().split() if w not in skip_words][:3]

            for col in available_columns:
                col_str = str(col).lower()
                # Check if at least 2 of the significant words are in the column name (handles truncation & variations)
                matches = sum(1 for word in expected_words if word in col_str)
                if matches >= min(2, len(expected_words)):  # Need at least 2 matches, or all if less than 2 words
                    matching_col = col
                    logger.debug(
                        f"Fuzzy matched '{expected_col}' to '{col}' (matched {matches}/{len(expected_words)} words)"
                    )
                    break

        if matching_col is not None:
            columns_to_keep.append(matching_col)
        else:
            logger.info(f"Expected column '{expected_col}' not found in CIS worksheet. Using empty values.")
            cis_df[expected_col] = ""
            columns_to_keep.append(expected_col)

    cis_df = cis_df[columns_to_keep]
    cis_df.columns = expected_columns
    return cis_df.fillna("")


def _find_control_id_row_index(df: "pd.DataFrame") -> Optional[int]:
    """
    Find the row index containing 'Control ID' in the first column.

    :param pd.DataFrame df: The dataframe to search
    :return: Row index if found, None otherwise
    :rtype: Optional[int]
    """
    for idx, row in df.iterrows():
        if row.iloc[0] == CONTROL_ID:
            return idx
    return None


def _merge_header_rows(header_row, sub_header_row) -> List[str]:
    """
    Merge two header rows into a single list of column names.

    FedRAMP Rev5 has a two-row header structure where main headers span multiple columns
    and sub-headers provide specific column names.

    :param header_row: The main header row (categories)
    :param sub_header_row: The sub-header row (specific columns)
    :return: List of merged column names
    :rtype: List[str]
    """
    pd = get_pandas()
    merged_headers = []
    current_category = None

    for i, (main, sub) in enumerate(zip(header_row, sub_header_row)):
        # Update current category if main header has a value
        if pd.notna(main) and main and str(main).strip():
            current_category = str(main)

        # Determine which header value to use
        header_value = _select_header_value(pd, main, sub, current_category, i)
        merged_headers.append(header_value)

    return merged_headers


def _select_header_value(pd: "pd.DataFrame", main, sub, current_category: Optional[str], index: int) -> str:
    """
    Select the appropriate header value based on priority: sub-header > main header > category > unnamed.

    :param pd.DataFrame pd: The pandas dataframe
    :param main: Main header value
    :param sub: Sub-header value
    :param Optional[str] current_category: Current category from merged cells
    :param int index: Column index for fallback naming
    :return: Selected header value
    :rtype: str
    """
    if pd.notna(sub) and sub and str(sub).strip():
        return str(sub)
    if pd.notna(main) and main and str(main).strip():
        return str(main)
    if current_category:
        return f"{current_category}_{index}"
    return f"Unnamed_{index}"


def _load_and_prepare_cis_dataframe(file_path: click.Path, cis_sheet_name: str, skip_rows: int):
    """
    Load and prepare the CIS dataframe from the workbook.

    :param click.Path file_path: The file path to the workbook
    :param str cis_sheet_name: The sheet name to parse
    :param int skip_rows: Number of rows to skip
    :return: Tuple of (prepared dataframe, updated skip_rows) or (None, skip_rows) if empty
    """
    # Read the Excel file directly with pandas to preserve "N/A" as string
    pd = get_pandas()
    df = pd.read_excel(file_path, sheet_name=cis_sheet_name, header=None, keep_default_na=False)

    if df.empty:
        return None, skip_rows

    # Find the row with "Control ID"
    control_id_row_idx = _find_control_id_row_index(df)
    if control_id_row_idx is None:
        logger.error("Could not find 'Control ID' in CIS worksheet")
        return None, skip_rows

    # Extract and merge the two header rows
    header_row = df.iloc[control_id_row_idx]
    sub_header_row = df.iloc[control_id_row_idx + 1]
    merged_headers = _merge_header_rows(header_row, sub_header_row)

    # Get data starting from two rows after the main header row
    cis_df = df.iloc[control_id_row_idx + 2 :].reset_index(drop=True)
    cis_df.columns = merged_headers
    cis_df.dropna(how="all", inplace=True)
    cis_df.reset_index(drop=True, inplace=True)

    skip_rows = control_id_row_idx + 2

    return cis_df, skip_rows


def _extract_status(data_row) -> str:
    """
    Extract the first non-empty implementation status from the CIS worksheet.

    :param data_row: The data row to extract the status from
    :return: The implementation status
    :rtype: str
    """
    selected_status = []
    for col in [
        "Implemented",
        ControlImplementationStatus.PartiallyImplemented,
        "Planned",
        ALTERNATIVE_IMPLEMENTATION,  # Use the correct constant
        ControlImplementationStatus.NA,
    ]:
        if data_row[col]:
            selected_status.append(col)
    return ", ".join(selected_status) if selected_status else ""


def _extract_origination(data_row) -> str:
    """
    Extract the first non-empty control origination from the CIS worksheet.

    :param data_row: The data row to extract the origination from
    :return: The control origination
    :rtype: str
    """
    selected_origination = []
    for col in [
        SERVICE_PROVIDER_CORPORATE,
        SERVICE_PROVIDER_SYSTEM_SPECIFIC,
        SERVICE_PROVIDER_HYBRID,
        CONFIGURED_BY_CUSTOMER,
        PROVIDED_BY_CUSTOMER,
        SHARED,
        INHERITED,
    ]:
        if data_row[col]:
            selected_origination.append(col)
    return ", ".join(selected_origination) if selected_origination else ""


def _process_cis_row(row) -> dict:
    """
    Process a row from the CIS worksheet.

    :param row: The row to process
    :return: The processed row
    :rtype: dict
    """
    return {
        "control_id": row[CONTROL_ID],
        "regscale_control_id": transform_control(row[CONTROL_ID]),
        "implementation_status": _extract_status(row),
        "control_origination": _extract_origination(row),
    }


def parse_cis_worksheet(file_path: click.Path, cis_sheet_name: str) -> dict:
    """
    Function to parse and format the CIS worksheet content

    :param click.Path file_path: The file path to the FedRAMP CIS CRM workbook
    :param str cis_sheet_name: The name of the CIS sheet to parse
    :return: Formatted CIS content
    :rtype: dict
    """
    logger.info("Parsing CIS worksheet...")

    # Load and prepare the dataframe
    cis_df, _ = _load_and_prepare_cis_dataframe(file_path, cis_sheet_name, skip_rows=2)
    if cis_df is None:
        return {}

    # Get expected columns and normalize the dataframe
    expected_columns = _get_expected_cis_columns()
    cis_df = _normalize_cis_columns(cis_df, expected_columns)

    # Process rows in parallel
    with ThreadPoolExecutor() as executor:
        results = list(executor.map(_process_cis_row, [row for _, row in cis_df.iterrows()]))

    # Index by control_id
    return {clean_key(result["control_id"]): result for result in results}


def determine_skip_row(original_df: "pd.DataFrame", text_to_find: str, original_skip: int):
    """
    Function to determine the row to skip when parsing a worksheet

    :param pd.DataFrame original_df: The original dataframe to search
    :param str text_to_find: The text to find
    :param int original_skip: The original row to skip
    :return: The row to skip
    :rtype: int
    """
    skip_rows = original_skip
    for idx, row in original_df.iterrows():
        if row.iloc[0] == text_to_find:
            skip_rows = idx + 1
            break
    return skip_rows


def _drop_rows_nan(instructions_df: "pd.DataFrame") -> "pd.DataFrame":
    """
    Drop any row with nan and every row after it

    :param pd.DataFrame instructions_df: The instructions dataframe to process
    :return: The processed dataframe
    :rtype: pd.DataFrame
    """
    # Find the first row containing any NaN value
    first_nan_index = None
    for i in range(len(instructions_df)):
        if instructions_df.iloc[i].isna().any():
            first_nan_index = i
            break

    # If a row with NaN is found, keep only rows before it
    if first_nan_index is not None:
        instructions_df = instructions_df.iloc[:first_nan_index]
    else:
        # Otherwise, just drop any rows with NaN values as before
        instructions_df = instructions_df.dropna()
    return instructions_df


def parse_instructions_worksheet(
    df: Dict[str, "pd.DataFrame"],
    version: Literal["rev4", "rev5"],
    instructions_sheet_name: str = "Instructions",
) -> list[dict]:
    """
    Function to parse the instructions sheet from the FedRAMP Rev5 CIS/CRM workbook

    :param Dict[str, "pd.DataFrame"] df: The dataframe to parse
    :param Literal["rev4", "rev5"] version: The version of the FedRAMP CIS CRM workbook
    :param str instructions_sheet_name: The name of the instructions sheet to parse, defaults to "Instructions"
    :return: List of formatted instructions content as a dictionary
    :rtype: list[dict]
    """
    pd = get_pandas()
    df = df[instructions_sheet_name].iloc[2:]
    if len(df) == 0:
        return []
    instructions_df = df.dropna(axis=1, how="all")

    if version == "rev5":
        relevant_columns = [CSP, SYSTEM_NAME, "System Identifier", IMPACT_LEVEL]
        # Set the appropriate headers
        # Find the row with the CSP column e.g. "System Name (CSP to complete all cells)"
        for index in range(len(instructions_df)):
            # Check if CSP is in the non-NaN values of this row
            row_values = [val for val in instructions_df.iloc[index].values if not pd.isna(val)]
            if CSP in row_values:
                # Keep only columns that have non-NaN values in this row
                non_nan_cols = instructions_df.columns[~instructions_df.iloc[index].isna()]
                instructions_df = instructions_df.loc[:, non_nan_cols]
                instructions_df.columns = relevant_columns
                instructions_df = instructions_df[index + 1 :]
                break

    else:
        for index in range(len(instructions_df)):
            if CSP in instructions_df.iloc[index].values:
                instructions_df.columns = instructions_df.iloc[index]
                instructions_df = instructions_df[index + 1 :]
                break
        # delete the rows before the found row
        relevant_columns = [SYSTEM_NAME, CSP, IMPACT_LEVEL]
    try:
        instructions_df = instructions_df[relevant_columns]
        # drop any row with nan
        instructions_df = _drop_rows_nan(instructions_df)

    except KeyError:
        error_and_exit(
            f"Unable to find the relevant columns in the Instructions worksheet. Do you have the correct "
            f"revision set?\nRevision: {version}",
            show_exec=False,
        )
    # convert the dataframe to a dictionary
    return instructions_df.to_dict(orient="records")


def update_customer_text():
    """
    Update the implementation responsibility texts from the objective data
    """
    with ThreadPoolExecutor() as executor:
        executor.map(_update_imp_customer, EXISTING_IMPLEMENTATIONS.values())


def _update_imp_customer(imp: ControlImplementation):
    """
    Update the implementation responsibility text for a given implementation

    :param ControlImplementation imp: The implementation to update
    :rtype: None
    :return: None
    """
    # Get relevant objectives and sort them
    objs = _get_sorted_objectives(imp.id)

    # Generate formatted responsibility texts
    customer_text = _format_responsibility_text(objs, "customerResponsibility")
    cloud_text = _format_responsibility_text(objs, "cloudResponsibility")

    # Update implementation if we have content
    if customer_text or cloud_text:
        _save_implementation_text(imp, customer_text, cloud_text)


def _get_sorted_objectives(imp_id: int) -> List[ImplementationObjective]:
    """
    Get relevant objectives sorted by notes field

    :param int imp_id: The implementation ID to filter objectives by
    :rtype: list
    :return: Sorted list of objectives
    :rtype: List[ImplementationObjective]
    """
    objs = [obj for obj in UPDATED_IMPLEMENTATION_OBJECTIVES if obj.implementationId == imp_id]
    return sorted(objs, key=lambda x: x.notes)


def _format_responsibility_text(objs: list, resp_attr: str) -> str:
    """
    Format responsibility text for the given objects and attribute

    :param list objs: The list of objects to format
    :param str resp_attr: The attribute to format
    :rtype: str
    :return: Formatted text
    """
    text = ""
    multi_part = len(objs) > 1

    for obj in objs:
        resp_text = getattr(obj, resp_attr, "")
        if resp_text:
            if multi_part:
                text += f"<p>part: {obj.notes}</p>"
            text += f"<p>{resp_text}</p>"

    return text


def _save_implementation_text(imp: ControlImplementation, customer_text: str, cloud_text: str):
    """
    Save the implementation texts and update parameters

    :param ControlImplementation imp: The implementation to save
    :param str customer_text: The customer responsibility text
    :param str cloud_text: The cloud responsibility text
    :rtype: None
    :return: None
    """
    imp.customerImplementation = customer_text
    imp.cloudImplementation = cloud_text

    # Update parameters in background thread
    if INITIAL_IMPORT:
        _spin_off_thread(parameter_merge, imp.id, imp.controlID)

    # Save implementation changes
    imp.save()


def parse_and_map_data(
    leveraged_auth_id: int, api: Api, cis_data: dict, crm_data: dict, version: Literal["rev5", "rev4"]
) -> None:
    """
    Function to parse and map data from RegScale and the workbook.

    :param int leveraged_auth_id: The leveraged authorization ID
    :param Api api: RegScale API object
    :param int ssp_id: RegScale SSP ID #
    :param dict cis_data: Parsed CIS data to update the control implementations and objectives
    :param dict crm_data: Parsed CRM data to update the control implementations and objectives
    :param version: Literal["rev4", "rev5", "4", "5"],
    :rtype: None
    """
    with progress:
        get_all_imps(api=api, cis_data=cis_data, version=version)
        error_set = update_all_objectives(
            leveraged_auth_id=leveraged_auth_id,
            cis_data=cis_data,
            crm_data=crm_data,
            version=version,
        )
        # Don't call this on re-import
        update_customer_text()

    report(error_set)


def extract_control_name(control_string: str) -> str:
    """
    Extracts the control name (e.g., 'AC-20(1)') from a given string.

    :param str control_string: The string to extract the control name from
    :return: The extracted control name
    :rtype: str
    """
    pattern = r"^[A-Za-z]{2}-\d{1,3}(?:\s*\(\s*\d+\s*\))?"
    match = re.match(pattern, control_string.upper())
    return match.group() if match else ""


def rev_4_map(control_id: str) -> Optional[str]:
    """
    Maps a control ID to its corresponding revision 4 control ID.

    :param str control_id: The control ID to map
    :return: The mapped control ID or None if not found
    :rtype: Optional[str]
    """
    # Regex pattern to match different control ID formats - handles extra spaces like AC-6 ( 1 ) ( a )
    pattern = r"^([A-Z]{2})-(\d{2})\s*(?:\(\s*(\d{2})\s*\))?\s*(?:\(\s*([a-z])\s*\))?$"

    match = re.match(pattern, control_id, re.IGNORECASE)

    if not match:
        return None

    # Extract components
    prefix, number, subnum, letter = match.groups()

    # Convert to lowercase
    prefix = prefix.lower()

    # Construct statement ID
    if subnum:
        # With sub-number
        base_id = f"{prefix}-{number}.{int(subnum)}_smt"
        return f"{base_id}{f'.{letter}' if letter else ''}"
    else:
        # Without sub-number
        base_id = f"{prefix}-{number}_smt"
        return f"{base_id}{f'.{letter}' if letter else ''}"


def build_implementations_dict(security_plan_id) -> None:
    """
    Save the implementations to a dictionary

    :param int security_plan_id: The security plan id
    :rtype: None
    :return: None
    """
    logger.info("Saving to an implementation dictionary ..")
    imps = ControlImplementation.get_list_by_plan(security_plan_id)
    for imp in imps:
        EXISTING_IMPLEMENTATIONS[imp.controlID] = imp
    logger.debug("Built %s implementations", len(imps))


def create_backup_file(security_plan_id: int):
    """
    Create a backup file for the given security plan ID.

    :param int security_plan_id: The security plan ID
    """
    logger.info("Creating a CIS/CRM Backup file of the current SSP state ..")
    # Export CIS/CRM to file system, and save to artifacts folder
    res = SecurityPlan.export_cis_crm(security_plan_id)
    status = res.get("status")
    if status and status == "complete":
        file_name = res.get("trustedDisplayName")
        logger.info(f"A CIS/CRM Backup file saved to SSP# {security_plan_id} file subsystem as {file_name}!")
        return
    continue_anyway = click.prompt("Unable to create a backup file. Would you like to continue?", type=bool)
    if not continue_anyway:
        error_and_exit("Backup file creation failed.")


def create_new_security_plan(profile_id: int, system_name: str):
    """
    Create a new FedRamp security plan and map controls based on the profile id.

    :param int profile_id: The profile id to map controls from
    :param str system_name: The system name to create the security plan for
    :rtype: SecurityPlan
    :return: The created security plan
    """
    global INITIAL_IMPORT
    compliance_settings = ComplianceSettings.get_by_current_tenant()
    try:
        compliance_setting = next(
            (
                setting.id
                for setting in compliance_settings
                if setting and setting.title == "FedRAMP Compliance Setting"
            ),
            2,
        )
    except TypeError:
        compliance_setting = 2
    existing_plans = SecurityPlan.get_list()
    existing_plan = [plan for plan in existing_plans if plan and plan.systemName == system_name]
    if not existing_plan:
        profile = Profile.get_object(profile_id)
        if not profile:
            error_and_exit("Unable to find the profile with the given ID, please try again")
        logger.info(f"Loading Profile Mappings from profile #{profile.id} - {profile.name}..")
        ret = SecurityPlan(
            **{
                "status": "Under Development",
                "systemType": "Major Application",
                "systemName": system_name,
                "users": 0,
                "privilegedUsers": 0,
                "usersMFA": 0,
                "privilegedUsersMFA": 0,
                "internalUsers": 0,
                "externalUsers": 0,
                "internalUsersFuture": 0,
                "externalUsersFuture": 0,
                "hva": False,
                "isPublic": True,
                "bModelSaaS": False,
                "bModelPaaS": False,
                "bModelIaaS": False,
                "bModelOther": False,
                "otherModelRemarks": "",
                "bDeployPrivate": False,
                "bDeployPublic": False,
                "bDeployGov": False,
                "bDeployHybrid": False,
                "bDeployOther": False,
                "fedrampDateSubmitted": "",
                "fedrampDateAuthorized": "",
                "defaultAssessmentDays": 0,
                "complianceSettingsId": compliance_setting,
            }
        ).create()
        logger.info(f"Created the new Security Plan as ID# {ret.id}")
        logger.info("Building the implementations from the profile mappings ..")
        Profile.apply_profile(ret.id, "securityplans", profile_id, True)
        build_implementations_dict(security_plan_id=ret.id)

    else:
        INITIAL_IMPORT = False
        ret = next(iter(existing_plan), None)
        logger.info(f"Found existing SSP# {ret.id}")
        create_backup_file(ret.id)
        existing_imps = ControlImplementation.get_list_by_plan(ret.id)
        for imp in existing_imps:
            EXISTING_IMPLEMENTATIONS[imp.controlID] = imp

    if ret is None:
        raise ValueError("Unable to create a new security plan.")

    if not EXISTING_IMPLEMENTATIONS:
        # We must have some implementations, build them if empty.
        Profile.apply_profile(ret.id, "securityplans", profile_id, True)
        build_implementations_dict(security_plan_id=ret.id)

    return ret


def parameter_merge(implementation_id: int, security_control_id: int):
    """
    Merge parameters for a given implementation ID and security control ID.

    :param int implementation_id: The implementation ID
    :param int security_control_id: The security control ID
    :rtype: None
    """
    parameters = Parameter.merge_parameters(implementation_id, security_control_id)
    for param in parameters:
        param.create()


def objective_merge(implementation_id: int, security_control_id: int):
    """
    Merge objectives for a given implementation ID and security control ID.

    :param int implementation_id: The implementation ID
    :param int security_control_id: The security control ID
    :rtype: None
    """
    imp_objectives = ImplementationObjective.merge_objectives(implementation_id, security_control_id)
    for obj in imp_objectives:
        obj.create()


def _spin_off_thread(function: Callable[..., T], *args: Any) -> Thread:
    """
    Spin off a thread to run the function with the given arguments.

    :param function: The function to run
    :param args: The arguments to pass to the function
    :return: The thread object
    """
    thread = Thread(target=function, args=args)
    thread.start()
    return thread


def _check_sheet_names_exist(
    file_path: click.Path, cis_sheet_name: str, crm_sheet_name: str
) -> dict[str, "pd.DataFrame"]:
    """
    Check if the sheet names exist in the workbook.

    :param click.Path file_path: The file path to the FedRAMP CIS CRM workbook
    :param str cis_sheet_name: The name of the CIS sheet to check
    :param str crm_sheet_name: The name of the CRM sheet to check
    :raises SystemExit: If the sheet names do not exist
    :rtype: dict[str, pd.DataFrame]
    :return: A dictionary of dataframes for each sheet
    """
    pd = get_pandas()

    df = pd.read_excel(file_path, sheet_name=None)
    sheet_names = df.keys()
    if cis_sheet_name not in sheet_names:
        error_and_exit(f"The CIS sheet name '{cis_sheet_name}' does not exist in the workbook.")
    if crm_sheet_name and crm_sheet_name not in sheet_names:
        error_and_exit(f"The CRM sheet name '{crm_sheet_name}' does not exist in the workbook.")
    return df


def copy_and_rename_file(file_path: Path, new_name: str) -> Path:
    """
    Copy and rename a file.
    """
    temp_folder = Path(gettempdir()) / "regscale"
    temp_folder.mkdir(exist_ok=True)  # Ensure directory exists

    new_file_path = temp_folder / new_name
    shutil.copy(file_path, new_file_path)
    return new_file_path


def upload_file(file_path: Path, ssp_id: int, parent_module: str, api: Api) -> None:
    """
    Upload a file to RegScale

    :param Path file_path: The path to the file to upload
    :param int ssp_id: The ID of the SSP to upload the file to
    :param str parent_module: The module to upload the file to
    :param Api api: The API object to use to upload the file
    :rtype: None
    """
    file_hash = None
    with open(file_path, "rb") as f:
        file_hash = compute_hash(f)
    existing_files = File.get_files_for_parent_from_regscale(ssp_id, parent_module)
    identical_file = next((file for file in existing_files if file.shaHash == file_hash), None)
    if file_hash and identical_file:
        logger.info(
            f"An identical file {identical_file.trustedDisplayName} already exists in RegScale, skipping upload."
        )
        return
    File.upload_file_to_regscale(
        file_name=file_path.absolute(), parent_id=ssp_id, parent_module=parent_module, api=api, tags="cis-crm"
    )


def parse_and_import_ciscrm(
    file_path: click.Path,
    version: Literal["rev4", "rev5", "4", "5"],
    cis_sheet_name: str,
    crm_sheet_name: Optional[str],
    profile_id: int,
    leveraged_auth_id: int = 0,
) -> None:
    """
    Parse and import the FedRAMP Rev5 CIS/CRM Workbook into a RegScale System Security Plan

    :param click.Path file_path: The file path to the FedRAMP CIS CRM .xlsx file
    :param Literal["rev4", "rev5"] version: FedRAMP revision version
    :param str cis_sheet_name: CIS sheet name in the FedRAMP CIS CRM .xlsx to parse
    :param Optional[str] crm_sheet_name: CRM sheet name in the FedRAMP CIS CRM .xlsx to parse
    :param int profile_id: The ID number from RegScale of the RegScale Profile to generate the control mapping
    :param int leveraged_auth_id: RegScale Leveraged Authorization ID #, if none provided, one will be created
    :raises ValueError: If the SSP with the given ID is not found in RegScale
    :rtype: None
    """
    global REGSCALE_SSP_ID  # Declare that you're modifying the global variable
    sys_name_key = "System Name"
    api = Api()

    df = _check_sheet_names_exist(file_path, cis_sheet_name, crm_sheet_name)

    if "5" in version:
        version = "rev5"
    else:
        version = "rev4"
    # No longer loading JSON mappings - using smart algorithm only
    # parse the instructions worksheet to get the csp name, system name, and other data
    instructions_data = parse_instructions_worksheet(df=df, version=version)  # type: ignore

    # get the system names from the instructions data by dropping any non-string values

    system_names = [
        entry[sys_name_key]
        for entry in instructions_data
        if isinstance(entry[sys_name_key], str) and cis_sheet_name in entry[sys_name_key].lower()
    ]
    if not system_names:
        system_names = [entry[sys_name_key] for entry in instructions_data if isinstance(entry[sys_name_key], str)]
    name_match: str = system_names[0]

    # create the new security plan
    ssp: SecurityPlan = create_new_security_plan(profile_id=profile_id, system_name=name_match)
    REGSCALE_SSP_ID = ssp.id

    if not ssp:
        raise ValueError("Unable to create a new SSP.")
    # update the instructions data to the matched system names
    instructions_data = [
        (
            entry
            if isinstance(entry[sys_name_key], str)
            and entry[sys_name_key] == name_match
            or entry[sys_name_key] == ssp.systemName
            else None
        )
        for entry in instructions_data
    ]
    # remove any None values from the instructions data
    instructions_data = [entry for entry in instructions_data if entry][0]
    if not any(instructions_data):
        raise ValueError("Unable to parse data from Instructions sheet.")

    # start parsing the workbook
    cis_data = parse_cis_worksheet(file_path=file_path, cis_sheet_name=cis_sheet_name)
    crm_data = {}
    if crm_sheet_name:
        # type: ignore
        crm_data = parse_crm_worksheet(file_path=file_path, crm_sheet_name=crm_sheet_name, version=version)
    if leveraged_auth_id == 0:
        auths = LeveragedAuthorization.get_all_by_parent(ssp.id)
        if auths:
            leveraged_auth_id = next((auth.id for auth in auths))
        else:
            leveraged_auth_id = new_leveraged_auth(
                ssp=ssp,
                user_id=api.app.config["userId"],
                instructions_data=instructions_data,
                version=version,  # type: ignore
            )
    # Update objectives using the mapped data using threads
    parse_and_map_data(
        leveraged_auth_id=leveraged_auth_id,
        api=api,
        cis_data=cis_data,
        crm_data=crm_data,
        version=version,  # type: ignore
    )
    file_path = Path(file_path)
    file_name = f"{file_path.stem}_update_{datetime.now().strftime('%Y%m%d')}{file_path.suffix}"
    if INITIAL_IMPORT:
        file_name = f"{file_path.stem}_initial_import{file_path.suffix}"
        # upload workbook to the SSP
    file_path = copy_and_rename_file(file_path, file_name)
    upload_file(file_path, ssp.id, "securityplans", api)
