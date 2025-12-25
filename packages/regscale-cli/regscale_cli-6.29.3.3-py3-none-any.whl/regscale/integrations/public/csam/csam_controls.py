#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Integrates CSAM into RegScale"""

# standard python imports
import logging
from typing import List, Optional, Tuple, Any, Dict
from rich.progress import track
from rich.console import Console
from regscale.core.app.application import Application
from regscale.models.regscale_models import (
    Catalog,
    ControlImplementation,
    InheritedControl,
    Inheritance,
    SecurityControl,
    SecurityPlan,
)
from regscale.integrations.control_matcher import ControlMatcher
from regscale.models.regscale_models.form_field_value import FormFieldValue
from regscale.integrations.public.csam.csam_common import (
    retrieve_from_csam,
    retrieve_ssps_custom_form_map,
    CSAM_FIELD_NAME,
    SSP_BASIC_TAB,
)

FULLY_IMPLEMENTED = "Fully Implemented"

logger = logging.getLogger("regscale")
console = Console()


def _get_control_set_and_controls(system_id: int) -> Tuple[Optional[str], Optional[list]]:
    """
    Determine the control set and retrieve appropriate controls for a system

    :param int system_id: CSAM system ID
    :return: Tuple of (control_set, controls) or (None, None) if not supported
    :return_type: Tuple[Optional[str], Optional[list]]
    """
    rev5_catalog_id, rev4_catalog_id = get_catalogs()
    rev5_controls = SecurityControl.get_list_by_catalog(catalog_id=rev5_catalog_id)
    rev4_controls = SecurityControl.get_list_by_catalog(catalog_id=rev4_catalog_id)

    imp = retrieve_from_csam(csam_endpoint=f"/CSAM/api/v1/systems/{system_id}/controls/AC-1")

    if not imp:
        return None, None

    control_set = imp[0].get("controlSet")
    if control_set == "NIST 800-53 Rev4":
        return control_set, rev4_controls
    if control_set == "NIST 800-53 Rev5":
        return control_set, rev5_controls

    logger.warning(f"System framework {control_set} for system {system_id} is not supported")
    return None, None


def _process_controls_for_ssp(regscale_ssp_id: int, system_id: int, controls: list) -> list:
    """
    Process and build control implementations for a single SSP

    :param int regscale_ssp_id: RegScale SSP ID
    :param int system_id: CSAM system ID
    :param list controls: List of security controls
    :return: List of control implementations
    :return_type: list
    """
    results = retrieve_controls(csam_id=system_id, controls=controls, regscale_id=regscale_ssp_id)

    if not results:
        logger.warning(f"No controls found for system id: {system_id}")
        return []

    return build_implementations(results=results, regscale_id=regscale_ssp_id)


def import_csam_controls(import_ids: Optional[List[int]] = None):
    """
    Import Controls from CSAM

    :param list import_ids: Filtered list of SSPs
    :return: None
    """

    # Get existing ssps by CSAM Id
    custom_fields_basic_map = FormFieldValue.check_custom_fields([CSAM_FIELD_NAME], "securityplans", SSP_BASIC_TAB)
    ssp_map = retrieve_ssps_custom_form_map(
        tab_name=SSP_BASIC_TAB, field_form_id=custom_fields_basic_map[CSAM_FIELD_NAME]
    )

    plans = import_ids if import_ids else list(ssp_map.keys())

    for regscale_ssp_id in plans:
        system_id = ssp_map.get(regscale_ssp_id)

        if not system_id:
            continue

        # Get control set and controls for the system
        _, controls = _get_control_set_and_controls(system_id)

        if not controls:
            continue

        # Process and build control implementations
        control_implementations = _process_controls_for_ssp(regscale_ssp_id, system_id, controls)

        if not control_implementations:
            continue

        # Save the control implementations
        for index in track(
            range(len(control_implementations)),
            description=f"Saving {len(control_implementations)} control implementations...",
        ):
            control_implementation = control_implementations[index]
            control_implementation.create() if control_implementation.id == 0 else control_implementation.save()


def build_implementations(results: list, regscale_id: int) -> list:
    """
    Build out the control implementations
    from the results returned from CSAM

    :param list results: records from CSAM
    :param int regscale_id: RegScale SSP Id
    :return: list of ControlImplementation objects
    :return_type: list
    """
    matcher = ControlMatcher()
    control_implementations = []

    # Loop through the results and create or update the controls
    for index in track(
        range(len(results)),
        description=f"Importing {len(results)} controls for system id: {regscale_id}...",
    ):
        result = results[index]

        # Match existing controlImplementation
        implementation = matcher.find_control_implementation(
            control_id=result["controlId"], parent_id=regscale_id, parent_module="securityplans"
        )

        # Set values
        status_lst = [FULLY_IMPLEMENTED if result["statedImplementationStatus"] == "Implemented" else "Not Implemented"]

        status = FULLY_IMPLEMENTED if result["statedImplementationStatus"] == "Implemented" else "Not Implemented"

        responsibility = (
            result["applicability"]
            if result["applicability"] in ["Hybrid", "Inherited"]
            else "Provider (System Specific)"
        )

        impl = result["implementationStatement"]

        if implementation:
            # Update it
            implementation.status_lst = status_lst
            implementation.status = status
            implementation.responsibility = responsibility
            implementation.controlSource = "Baseline"
            implementation.implementation = impl
        else:
            # Build it from the catalog
            implementation = ControlImplementation(
                status_lst=status_lst,
                status=status,
                parentId=regscale_id,
                parentModule="securityplans",
                controlID=result["controlID"],
                responsibility=responsibility,
                controlSource="Baseline",
                implementation=impl,
            )

        control_implementations.append(implementation)

    return control_implementations


def retrieve_controls(csam_id: int, controls: list, regscale_id: int) -> list:
    """
    Takes a system id and list of controls
    returns a list of implmentations for
    that system id and framework

    :param int system_id: CSAM system id
    :param str framework: Framework name
    :param list controls: list of possible controls
    :param int regscale_id: RegScale SSP Id
    :return: list of control implementations
    :return_type: list
    """
    imps = []
    # Loop through the controls and get the implementations
    for index in track(
        range(len(controls)),
        description=f"Retrieving implementations for system id: {csam_id}...",
    ):
        control = controls[index]
        implementations = retrieve_from_csam(
            csam_endpoint=f"/CSAM/api/v1/systems/{csam_id}/controls/{control.controlId}",
        )

        if len(implementations) == 0:
            logger.debug(f"No implementations found for control {control.controlId} in system id: {csam_id}")
            continue

        # Add the RegScale SSP Id and controlID to the implementation
        for impl in implementations:
            if "NotApplicable" in impl["applicability"]:
                continue

            impl["securityPlanId"] = regscale_id
            impl["controlID"] = control.id
            imps.append(impl)
    return imps


def set_inheritable(regscale_id: int):
    """
    Given a RegScale SSP Id
    Sets the inheritable flag on all control implementations

    :param int regscale_id: id of Security Plan
    :return: None
    """

    # Get list of existing controlimplementations
    implementations = ControlImplementation.get_list_by_parent(regscale_id=regscale_id, regscale_module="securityplans")
    implementations = implementations.get("items")

    for index in track(
        range(len(implementations)),
        description="Setting controls Inheritable...",
    ):
        implementation = implementations[index]
        imp = ControlImplementation.get_object(object_id=implementation["id"])
        if imp.status in [FULLY_IMPLEMENTED, "Partially Implemented", "In Remediation"]:
            imp.inheritable = True
            imp.save()


def trim_inheritances(inheritances=List[Dict]) -> List[Dict]:
    """
    Trim out the records that aren't inherited
    Trim down to one record per Control (vice "deterineifs")

    :param inheritances: list of controlImplementations
    :return: trimed list of dict
    """

    unique_controls = []
    new_list = []

    for inheritance in inheritances:
        if inheritance.get("isInherited") is False:
            continue

        if inheritance.get("controlId") in unique_controls:
            continue

        unique_controls.append(inheritance.get("controlId"))
        new_list.append(inheritance)

    return new_list


def process_inheritances(inheritances: List[Dict[str, Any]], ssp: SecurityPlan, ssp_map: Dict[str, int]):
    matcher = ControlMatcher()
    linked_ssps = []
    for inheritance in inheritances:
        # If not inherited, skip
        if inheritance.get("isInherited") is False:
            continue

        # Check if the control exists in plan
        control_id = matcher.find_control_implementation(
            control_id=inheritance.get("controlId"), parent_id=ssp.id, parent_module="securityplans"
        )
        if not control_id:
            logger.debug(
                f"Control {inheritance.get('controlId')} not found in RegScale for SSP {ssp.systemName} (ID: {ssp.id})"
            )
            continue

        # Find the baseControl in RegScale
        # Find the SSP
        base_ssp = ssp_map.get(inheritance.get("offeringSystemName"))
        if not base_ssp:
            logger.debug(f"Base SSP {inheritance.get('offeringSystemName')} not found in RegScale, skipping")
            continue

        # Find the source control
        base_control_id = matcher.find_control_implementation(
            control_id=inheritance.get("controlId"), parent_id=base_ssp, parent_module="securityplans"
        )

        if not base_control_id:
            logger.debug(f"Control not found in Base SSP: {inheritance.get('offeringSystemName')}, skipping")
            continue

        # Create or update the inheritance record
        # Add the parent if not already linked
        if base_ssp not in linked_ssps:
            linked_ssps.append(base_ssp)

        # Create the records
        create_inheritance(
            parent_id=ssp.id,
            parent_module="securityplans",
            hybrid=inheritance.get("isHybrid", True),
            base_id=base_ssp,
            control_id=control_id.id,
            base_control_id=base_control_id.id,
        )

    # Create the Inheritance Record(s)
    for inheritance_ssp in linked_ssps:
        create_inheritance_linage(
            parent_id=ssp.id,
            parent_module="securityplans",
            base_id=inheritance_ssp,
        )


def create_inheritance(
    parent_id: int, parent_module: str, base_id: int, hybrid: bool, control_id: int, base_control_id: int
):
    """
    Creates the records for inheritance

    :param int parent_id: Id of inheriting record
    :param str parent_module: Module of inheriting record
    :param int base_id: Id of inherited record
    :param bool hybrid: Is the control hybrid
    :param int control_id: Id of inheriting control
    :param int base_control_id: Id of inherited control
    :return: None
    """

    # Update the control implementation
    control_impl = ControlImplementation.get_object(object_id=control_id)
    if control_impl:
        control_impl.bInherited = True
        control_impl.responsibility = "Hybrid" if hybrid else "Inherited"
        control_impl.inheritedControlId = base_control_id
        control_impl.inheritedSecurityPlanId = base_id
        control_impl.save()

    # Check if the Inherited Control already exists
    existing = InheritedControl.get_all_by_control(control_id=control_id)
    for exists in existing:
        if exists["inheritedControlId"] == base_control_id:
            return

    InheritedControl(
        parentId=parent_id, parentModule=parent_module, baseControlId=control_id, inheritedControlId=base_control_id
    ).create()


def create_inheritance_linage(parent_id: int, parent_module: str, base_id: int):
    """
    Creates a RegScale Inheritance Record

    :param int parent_id: Id of inheriting record
    :param str parent_module: Module of inheriting record
    :param int base_control_id: Id of inherited control
    :return: None
    """
    # Check if the Inheritance already exists
    existing = Inheritance.get_all_by_parent(parent_id=parent_id, parent_module=parent_module)
    for exists in existing:
        if exists.planId == base_id:
            return

    # Update Lineage (no way to update.. only create)
    Inheritance(recordId=parent_id, recordModule=parent_module, planId=base_id).create()


def import_csam_inheritance(import_ids: Optional[List[int]] = None):
    """
    Import control inheritance from CSAM

    :param list import_ids: List of SSPs to import
    :return: None
    """

    # Get list of existing SSPs in RegScale
    existing_ssps = SecurityPlan.get_ssp_list()
    ssp_map = {ssp["title"]: ssp["id"] for ssp in existing_ssps}

    if not import_ids:
        import_ids = [ssp["id"] for ssp in existing_ssps]

    # Get Inheritance data from CSAM
    for index in track(
        range(len(import_ids)),
        description=f"Importing inheritance for {len(import_ids)} Systems...",
    ):
        ssp = SecurityPlan.get_object(object_id=import_ids[index])
        # Get the inheritance data from CSAM

        inheritances = retrieve_from_csam(
            csam_endpoint=f"/CSAM/api/v1/systems/{ssp.otherIdentifier}/inheritedcontrols",
        )
        if not inheritances:
            logger.debug(f"No inheritance data found for SSP {ssp.systemName} (ID: {ssp.id})")
            continue

        inheritances = trim_inheritances(inheritances=inheritances)

        process_inheritances(inheritances=inheritances, ssp=ssp, ssp_map=ssp_map)


def get_catalogs() -> Tuple[Optional[int], Optional[int]]:
    """
    Get the catalog ids for NIST SP 800-53 Rev 5 and Rev 4

    :return: tuple of catalog ids
    :return_type: Tuple[Optional[int], Optional[int]]
    """
    # Find the Catalogs
    # Use the init.yaml values, otherwise search for the catalogs by guid
    app = Application()
    catalogs = app.config.get("csamFrameworkCatalog")
    rev5_catalog = Catalog.find_by_guid("b0c40faa-fda4-4ed3-83df-368908d9e9b2")  # NIST SP 800-53 Rev 5
    rev4_catalog = Catalog.find_by_guid("02158108-e491-49de-b9a8-3cb1cb8197dd")  # NIST SP 800-53 Rev 4

    if catalogs:
        rev5_catalog_id = catalogs.get("800-53r5")
        rev4_catalog_id = catalogs.get("800-53r4")
    elif rev5_catalog and rev4_catalog:
        rev5_catalog_id = rev5_catalog.id
        rev4_catalog_id = rev4_catalog.id

    return rev5_catalog_id, rev4_catalog_id
