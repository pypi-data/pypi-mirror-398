#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Integrates CSAM into RegScale"""

# standard python imports
import logging
from typing import List, Optional
from rich.progress import track
from rich.console import Console
from regscale.core.app.api import Api
from regscale.core.app.utils.api_handler import APIHandler, APIInsertionError, APIResponseError, APIUpdateError
from regscale.core.app.application import Application
from regscale.core.app.utils.parser_utils import safe_date_str
from regscale.models.regscale_models import Issue
from regscale.models.regscale_models.form_field_value import FormFieldValue
from regscale.integrations.public.csam.csam_common import (
    retrieve_ssps_custom_form_map,
    retrieve_from_csam,
    CSAM_FIELD_NAME,
    SSP_BASIC_TAB,
)

logger = logging.getLogger("regscale")
console = Console()

####################################################################################################
#
# IMPORT SSP / POAM FROM DoJ's CSAM GRC
# CSAM API Docs: https://csam.dhs.gov/CSAM/api/docs/index.html (required PIV)
#
####################################################################################################

SEVERITY_NOT_ASSIGNED = "IV - Not Assigned"


def import_csam_poams(import_ids: Optional[List[int]] = None):
    """
    Import the POA&Ms from CSAM
    """
    # Get existing ssps by CSAM Id
    custom_fields_basic_map = FormFieldValue.check_custom_fields([CSAM_FIELD_NAME], "securityplans", SSP_BASIC_TAB)
    ssp_map = retrieve_ssps_custom_form_map(
        tab_name=SSP_BASIC_TAB, field_form_id=custom_fields_basic_map[CSAM_FIELD_NAME]
    )

    plans = import_ids if import_ids else list(ssp_map.keys())

    all_issues = []
    logger.info(f"Retrieving POA&Ms for {len(plans)} SSPs...")
    for regscale_ssp_id in plans:
        results = []
        system_id = ssp_map.get(regscale_ssp_id)

        results = retrieve_from_csam(
            csam_endpoint=f"/CSAM/api/v1/systems/{system_id}/poams",
        )

        if not results:
            logger.warning(f"No POA&MS found for CSAM id: {system_id}, RegScale id: {regscale_ssp_id}")
            continue

        issues = process_poam(results=results, regscale_id=regscale_ssp_id, csam_id=system_id)

        all_issues.extend(issues)

    create_issues(all_issues)


def process_poam(results: list, regscale_id: int, csam_id: int) -> list[Issue]:
    """
    Process the results from the CSAM query
    per CSAM system

    :param results: results from CSAM
    :param regscale_id: id of RegScale SSP
    :param csam_id: id of the CSAM Record
    :return: list of RegScale Issues
    """
    severity_map = {
        "High": "I - High - Significant Deficiency",
        "Medium": "II - Moderate - Reportable Condition",
        "Low": "III - Low - Other Weakness",
        "N/A": SEVERITY_NOT_ASSIGNED,
        "None": SEVERITY_NOT_ASSIGNED,
    }
    status_map = {
        "Cancelled": "Cancelled",
        "Completed": "Closed",
        "In Progress": "Open",
        "Not Started": "Open",
        "Delayed": "Delayed",
        "Planned/Pending": "Open",
    }

    # Parse the results
    poam_list = []
    for index in track(
        range(len(results)),
        description=f"Building {len(results)} POA&Ms for SSP {regscale_id}...",
    ):
        result = results[index]

        # Get the affected controls
        controls = get_poam_controls(poam_id=result.get("poamId"), csam_id=csam_id)

        # Check if the POAM exists:
        existing_issue = Issue.find_by_other_identifier(result.get("poamId"))
        if existing_issue:
            new_issue = existing_issue[0]
        else:
            new_issue = Issue()

        # Update the issue
        new_issue.isPoam = True
        new_issue.parentId = regscale_id
        new_issue.parentModule = "securityplans"
        new_issue.otherIdentifier = result.get("poamId")
        new_issue.title = result.get("title")
        new_issue.securityPlanId = regscale_id
        new_issue.identification = "Other"
        new_issue.costEstimate = result.get("cost")
        new_issue.description = result.get("description")
        new_issue.sourceReport = "Imported from CSAM"
        new_issue.dueDate = safe_date_str(result.get("plannedFinishDate"))
        new_issue.dateCompleted = (
            safe_date_str(result.get("actualFinishDate")) if result.get("actualFinishDate") else ""
        )
        new_issue.affectedControls = controls
        new_issue.poamComments = result.get("delayReason")
        # Update with IssueSeverity String
        severity = severity_map.get(result.get("csamDerivedSeverity"))
        if not severity:
            severity = SEVERITY_NOT_ASSIGNED
        new_issue.severityLevel = severity
        # Update with IssueStatus String
        new_issue.status = status_map.get(result.get("status"))
        if not new_issue.status:
            new_issue.status = "Open"
        # Handle when the issue is open, or pending, or delayed and still has as "date closed"
        if new_issue.status != "Closed":
            new_issue.dateCompleted = None

        poam_list.append(new_issue)

    return poam_list


def get_poam_controls(poam_id: int, csam_id: int) -> str:
    controls = []

    results = retrieve_from_csam(csam_endpoint=f"/CSAM/api/v1/systems/{csam_id}/poams/{poam_id}/controls")

    if len(results) == 0:
        return ""

    for result in results:
        if result.get("controlSet") == "NIST 800-53 Rev5":
            controls.append(result.get("controlId"))

    affected_controls = ", ".join(controls)

    return affected_controls


def create_issues(poam_list: list):
    """
    Create the RegScale Poams from a list
    of RegScale Issues

    :param poam_list: _description_
    """
    for index in track(
        range(len(poam_list)),
        description=f"Updating RegScale with {len(poam_list)} POA&Ms...",
    ):
        poam = poam_list[index]
        if poam.id == 0:
            try:
                poam.create()
            except APIInsertionError:
                continue
        else:
            try:
                poam.save()
            except APIUpdateError:
                continue
    logger.info(f"Added or updated {len(poam_list)} POA&Ms in RegScale")
