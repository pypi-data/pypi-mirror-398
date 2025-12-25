#!/usr/bin/env python
"""
FedRAMP Rev 5 POAM Export

This module provides FedRAMP Rev 5 POAM Excel export functionality with advanced features:
- Dynamic POAM ID generation based on source file path properties
- KEV date determination from CISA KEV catalog
- Deviation status mapping (Approved/Pending/Rejected)
- Custom milestone and comment generation
- Excel formatting optimized for FedRAMP Rev 5 template
"""

import functools
import logging
import re
import shutil
from datetime import datetime, timedelta
from html import unescape
from pathlib import Path
from typing import List, Optional

import openpyxl
from openpyxl.worksheet.worksheet import Worksheet

from regscale.core.app.api import Api
from regscale.core.app.application import Application
from regscale.core.utils.date import datetime_obj
from regscale.integrations.public.cisa import pull_cisa_kev
from regscale.models.regscale_models import (
    Asset,
    Deviation,
    File,
    Issue,
    IssueSeverity,
    IssueStatus,
    Link,
    Property,
    ScanHistory,
    SecurityPlan,
    VulnerabilityMapping,
)

logger = logging.getLogger("regscale")

# FedRAMP POAM Export Constants
POAM_CLOSED_DATE_ROUNDING_DAY = 25  # FedRAMP requirement: round closed dates to 25th of month
EXCEL_TEMPLATE_HEADER_ROWS = 6  # Number of header rows in FedRAMP template before data starts


@functools.lru_cache(maxsize=1)
def get_cached_cisa_kev():
    """
    Pull the CISA KEV with caching

    :return: CISA KEV data
    :rtype: dict
    """
    return pull_cisa_kev()


def set_short_date(date_str: str) -> str:
    """
    Convert datetime string to short date format (MM/DD/YY)

    :param str date_str: Date string to convert
    :return: Formatted date string
    :rtype: str
    """
    return datetime_obj(date_str).strftime("%m/%d/%y")


def strip_html(input_str: str) -> str:
    """
    Strip HTML tags from input string

    :param str input_str: String with HTML tags
    :return: String with HTML removed
    :rtype: str
    """
    if not input_str:
        return ""
    no_html = re.sub("<[^>]*>", "", input_str)  # Use negated character class instead of reluctant quantifier
    return unescape(no_html)


def convert_to_list(asset_identifier: str) -> List[str]:
    """
    Convert asset identifier string to list, supporting multiple formats

    Data could be <p> tag delimited, tab delimited, or newline delimited

    :param str asset_identifier: Asset identifier string
    :return: List of asset identifiers
    :rtype: List[str]
    """
    if not asset_identifier:
        return []

    # Check for <p> tags and split by them
    if "<p>" in asset_identifier and "</p>" in asset_identifier:
        return re.findall(r"<p>([^<]*)</p>", asset_identifier)
    # Check for tab characters and split by them
    if "\t" in asset_identifier:
        return asset_identifier.split("\t")
    # Otherwise, split by newlines
    return asset_identifier.splitlines()


def determine_kev_date(cve: str) -> str:
    """
    Determine KEV due date from CISA KEV catalog

    :param str cve: CVE identifier
    :return: KEV due date or "N/A"
    :rtype: str
    """
    if not cve:
        return "N/A"

    kev_data = get_cached_cisa_kev()
    for item in kev_data.get("vulnerabilities", []):
        if item.get("cveID", "").lower() == cve.lower():
            logger.info("Matched CVE: %s. KEV due date: %s", item.get("cveID"), item.get("dueDate"))
            due_date = item.get("dueDate")
            return set_short_date(due_date)
    return "N/A"


def determine_poam_id(poam: Issue, props: List[Property]) -> str:
    """
    Determine POAM ID based on source file path patterns

    Maps source file path keywords to POAM prefixes:
    - pdf -> DC
    - signatures -> CPT
    - campaign -> ALM
    - learning manager -> CCD
    - cce -> CCE

    :param Issue poam: POAM issue object
    :param List[Property] props: Properties for the POAM
    :return: Generated POAM ID
    :rtype: str
    """
    # Define mapping from file path keywords to POAM prefixes
    source_path_mappings = {
        "pdf": "DC",
        "signatures": "CPT",
        "campaign": "ALM",
        "learning manager": "CCD",
        "cce": "CCE",
    }

    # Look for source_file_path property
    source_file_path = None
    for prop in props:
        if prop.key == "source_file_path":
            source_file_path = prop.value.lower()
            break

    if source_file_path:
        # Check each mapping pattern
        for keyword, prefix in source_path_mappings.items():
            if keyword in source_file_path:
                return f"{prefix}-{poam.id}"

    return f"UNK-{poam.id}"


def determine_poam_service_name(_poam: Issue, props: List[Property]) -> str:
    """
    Determine service name from source file path

    :param Issue _poam: POAM issue object (unused, kept for API consistency)
    :param List[Property] props: Properties for the POAM
    :return: Service name
    :rtype: str
    """
    for prop in props:
        if prop.key == "source_file_path":
            value_lower = prop.value.lower()
            if "pdf" in value_lower:
                return "PDF Services"
            if "signatures" in value_lower:
                return "Signatures"
    return "UNKNOWN"


def lookup_scan_date(poam: Issue, assets: List[Asset]) -> str:
    """
    Lookup the scan date from vulnerability mappings

    :param Issue poam: POAM issue object
    :param List[Asset] assets: List of assets
    :return: Scan date string
    :rtype: str
    """
    poam_assets = convert_to_list(poam.assetIdentifier)
    for asset_name in poam_assets:
        matching_asset = [asset for asset in assets if asset.name == asset_name]
        if matching_asset:
            vulns = VulnerabilityMapping.find_by_asset(matching_asset[0].id)
            scans = [vuln.scanId for vuln in vulns]
            if scans:
                scan_date = ScanHistory.get_object(scans[0]).scanDate
                return set_short_date(scan_date)
    return set_short_date(poam.dateLastUpdated)


def determine_poam_comment(poam: Issue, assets: List[Asset]) -> str:  # pylint: disable=unused-argument
    """
    Determine and update POAM comment with appropriate status-based messages

    :param Issue poam: POAM issue object
    :param List[Asset] assets: List of assets
    :return: Updated POAM comment
    :rtype: str
    """
    # Comment templates
    closed_comment_template = (
        "Per review of the latest scan report on %s, (TGRC) can confirm that this issue "
        "no longer persists. This POAM will be submitted for closure."
    )
    open_comment_template = "POAM entry added"

    if not poam.dateFirstDetected:
        return "N/A"

    original_comment = poam.poamComments
    current_comment = poam.poamComments or ""
    detection_date = set_short_date(poam.dateFirstDetected)

    # Determine new comment based on POAM status
    if poam.dateCompleted:
        # Closed POAM: Add closure comment if not already present
        updated_comment = _generate_closed_poam_comment(
            poam, current_comment, closed_comment_template, open_comment_template
        )
    else:
        # Open POAM: Add detection/creation comment
        updated_comment = _generate_open_poam_comment(current_comment, detection_date, open_comment_template)

    # Save POAM if comment changed
    if updated_comment != original_comment:
        logger.info("Updating POAM comment for POAM #%s", poam.id)
        poam.poamComments = updated_comment
        poam.save()

    return updated_comment or "N/A"


def _generate_closed_poam_comment(poam: Issue, current_comment: str, template: str, _open_template: str) -> str:
    """
    Generate comment for closed POAMs

    :param Issue poam: POAM issue object
    :param str current_comment: Current comment text
    :param str template: Template for closed comment
    :param str _open_template: Template for open comment (unused, kept for API consistency)
    :return: Generated comment
    :rtype: str
    """
    closed_blurb = "This POAM will be submitted for closure"
    open_blurb = "POAM entry added"

    if open_blurb not in current_comment:
        current_comment = f"{set_short_date(poam.dateCreated)}: {open_blurb}"
    if closed_blurb in current_comment:
        return current_comment  # Already has closed comment

    return template % set_short_date(poam.dateCompleted) + "\n" + current_comment


def _generate_open_poam_comment(current_comment: str, detection_date: str, template: str) -> str:
    """
    Generate comment for open POAMs

    :param str current_comment: Current comment text
    :param str detection_date: Detection date string
    :param str template: Template for open comment
    :return: Generated comment
    :rtype: str
    """
    # If comment already has "entry added", return unchanged
    if current_comment and "entry added" in current_comment:
        return current_comment

    new_entry = f"{detection_date}: {template}"

    # If there's existing comment (without "entry added"), prepend new entry
    if current_comment:
        return f"{new_entry}\n{current_comment}"

    # No existing comment, return just the new entry
    return new_entry


def set_milestones(poam: Issue, index: int, sheet: Worksheet, column_l_date: str, all_milestones: List[dict]) -> None:
    """
    Set milestones in the worksheet

    :param Issue poam: POAM issue object
    :param int index: Row index
    :param Worksheet sheet: Worksheet object
    :param str column_l_date: Scheduled completion date
    :param List[dict] all_milestones: All milestones
    """
    milestones = [milestone for milestone in all_milestones if milestone.get("parent_id", 0) == poam.id]
    milestone_text = f"{column_l_date}: System will be updated as part of the monthly patching cycle.\n".join(
        [set_short_date(milestone.get("MilestoneDate", "")) for milestone in milestones]
    )
    if milestone_text:
        sheet[f"M{index}"].value = milestone_text
    else:
        sheet[f"M{index}"].value = f"{column_l_date}: System will be updated as part of the monthly patching cycle."


def set_status(poam: Issue, index: int, sheet: Worksheet) -> None:
    """
    Set status completion date with rounding logic for closed POAMs

    Closed dates are rounded to the 25th of the month:
    - If closed on or before the 25th, use the 25th of that month
    - If closed after the 25th, use the 25th of the next month

    :param Issue poam: POAM issue object
    :param int index: Row index
    :param Worksheet sheet: Worksheet object
    """
    if poam.status == "Closed" and poam.dateCompleted:
        day_of_month = datetime_obj(poam.dateCompleted).day
        if day_of_month <= POAM_CLOSED_DATE_ROUNDING_DAY:
            new_date_completed = datetime_obj(poam.dateCompleted).replace(day=POAM_CLOSED_DATE_ROUNDING_DAY)
        else:
            # Move to 25th of next month
            next_month = datetime_obj(poam.dateCompleted) + timedelta(days=31)
            new_date_completed = next_month.replace(day=POAM_CLOSED_DATE_ROUNDING_DAY)
        sheet[f"O{index}"].value = set_short_date(new_date_completed)
    elif poam.status == "Closed":
        sheet[f"O{index}"].value = ""
    if poam.status == "Open" and poam.dateLastUpdated:
        sheet[f"O{index}"].value = set_short_date(poam.dateLastUpdated)
    elif poam.status == "Open":
        sheet[f"O{index}"].value = ""


def set_vendor_info(poam: Issue, index: int, sheet: Worksheet) -> None:
    """
    Set vendor dependency information

    :param Issue poam: POAM issue object
    :param int index: Row index
    :param Worksheet sheet: Worksheet object
    """
    sheet[f"P{index}"].value = poam.vendorDependency or "No"
    sheet[f"R{index}"].value = poam.vendorName if poam.vendorName else "N/A"
    if sheet[f"P{index}"].value == "No":
        sheet[f"Q{index}"].value = "N/A"
    elif poam.vendorLastUpdate:
        sheet[f"Q{index}"].value = set_short_date(poam.vendorLastUpdate)
    else:
        sheet[f"Q{index}"].value = ""


def set_risk_info(poam: Issue, index: int, sheet: Worksheet) -> None:
    """
    Set risk adjustment and deviation information

    Maps deviation status to Yes/Pending/No based on approval state

    :param Issue poam: POAM issue object
    :param int index: Row index
    :param Worksheet sheet: Worksheet object
    """
    deviation_map = {"Approved": "Yes", "Pending": "Pending", "Rejected": "No"}
    deviation_status = ""
    deviation_obj = Deviation.get_by_issue(poam.id)
    if deviation_obj:
        deviation_status = deviation_obj.deviationStatus
    deviation_rationale = strip_html(poam.deviationRationale)

    original_risk_rating = (
        poam.originalRiskRating if poam.originalRiskRating else IssueSeverity(poam.severityLevel).name
    )
    sheet[f"S{index}"].value = poam.originalRiskRating if poam.originalRiskRating else original_risk_rating

    # Set defaults
    sheet[f"T{index}"].value = poam.adjustedRiskRating or "N/A"
    sheet[f"U{index}"].value = poam.riskAdjustment or "No"
    sheet[f"V{index}"].value = poam.falsePositive or "No"
    sheet[f"W{index}"].value = "No"

    if poam.operationalRequirement or poam.riskAdjustment or poam.falsePositive:
        sheet[f"X{index}"].value = deviation_rationale

    if poam.falsePositive in ["Yes", "Pending"]:
        sheet[f"V{index}"].value = deviation_map.get(deviation_status, "No")

    if poam.riskAdjustment in ["Yes", "Pending"]:
        sheet[f"U{index}"].value = deviation_map.get(deviation_status, "No")

    if poam.operationalRequirement in ["Yes", "Pending"]:
        sheet[f"W{index}"].value = deviation_map.get(deviation_status, "No")
        if poam.operationalRequirement == "Yes" and deviation_map.get(deviation_status, "No") == "Pending":
            sheet[f"U{index}"].value = "No"
            sheet[f"V{index}"].value = "No"
            sheet[f"W{index}"].value = "Pending"

    if not deviation_rationale:
        sheet[f"X{index}"].value = "N/A"


def set_end_columns(
    _ssp: SecurityPlan,
    poam: Issue,
    index: int,
    sheet: Worksheet,
    props: List[Property],
    assets: List[Asset],
    all_links: List[dict],
    all_files: List[dict],
):
    """
    Set end columns including links, files, KEV data, and service names

    :param SecurityPlan _ssp: Security plan object (unused, kept for API consistency)
    :param Issue poam: POAM issue object
    :param int index: Row index
    :param Worksheet sheet: Worksheet object
    :param List[Property] props: Properties list
    :param List[Asset] assets: Assets list
    :param List[dict] all_links: All links
    :param List[dict] all_files: All files
    """
    grouped_links = [link for link in all_links if link.parentID == poam.id]
    grouped_files = [file for file in all_files if file.parentId == poam.id]

    aggregate_link_txt = "".join([f"\t{lin['Title']}: {lin['URL']};\n" for lin in grouped_links])
    aggregate_file_txt = "".join([f"\t{fil['TrustedDisplayName']};\n" for fil in grouped_files])

    sheet[f"Y{index}"].value = "N/A"
    if grouped_links:
        sheet[f"Y{index}"].value = "Links:\n" + aggregate_link_txt
    if grouped_files:
        sheet[f"Y{index}"].value = "\nFiles:\n" + aggregate_file_txt

    sheet[f"Z{index}"].value = determine_poam_comment(poam, assets)
    sheet[f"AA{index}"].value = poam.autoApproved
    sheet[f"AB{index}"].value = poam.kevList if poam.kevList == "Yes" else "No"
    sheet[f"AC{index}"].value = determine_kev_date(poam.cve)
    sheet[f"AD{index}"].value = poam.cve or "N/A"
    service_name = determine_poam_service_name(poam, props)
    sheet[f"AE{index}"].value = service_name
    sheet[f"I{index}"].value = service_name


def _normalize_source_report(poam: Issue) -> None:
    """
    Normalize source report name (e.g., SAP Concur -> Tenable SC)

    :param Issue poam: POAM issue object
    """
    if poam.sourceReport == "SAP Concur":
        poam.sourceReport = "Tenable SC"


def _populate_basic_poam_columns(sheet: Worksheet, index: int, poam: Issue, point_of_contact: str) -> None:
    """
    Populate basic POAM columns B-I (control, title, description, assets, POC, service)

    :param Worksheet sheet: Worksheet object
    :param int index: Row index
    :param Issue poam: POAM issue object
    :param str point_of_contact: Point of Contact name
    """
    sheet[f"B{index}"].value = "RA-5"
    title = poam.title or poam.cve
    sheet[f"C{index}"].value = title
    sheet[f"D{index}"].value = strip_html(poam.description)
    sheet[f"G{index}"].value = "\n".join(convert_to_list(poam.assetIdentifier))
    sheet[f"H{index}"].value = point_of_contact if point_of_contact else ""


def _populate_date_and_milestone_columns(sheet: Worksheet, index: int, poam: Issue, all_milestones: List[dict]) -> None:
    """
    Populate date and milestone columns K-M (detection date, due date, milestones)

    :param Worksheet sheet: Worksheet object
    :param int index: Row index
    :param Issue poam: POAM issue object
    :param List[dict] all_milestones: All milestones
    """
    sheet[f"K{index}"].value = set_short_date(poam.dateFirstDetected)
    column_l_date = (
        (datetime_obj(poam.dueDate) + timedelta(days=-1)).strftime("%m/%d/%y") if datetime_obj(poam.dueDate) else ""
    )
    sheet[f"L{index}"].value = column_l_date
    set_milestones(poam, index, sheet, column_l_date, all_milestones)


def map_weakness_detector_and_id_for_rev5_issues(
    worksheet: Worksheet, column1: str, column2: str, row_number: int, issue: Issue
):
    """
    Map weakness detector (column E) and source ID (column F)

    :param Worksheet worksheet: Worksheet object
    :param str column1: First column letter (E)
    :param str column2: Second column letter (F)
    :param int row_number: Row number
    :param Issue issue: Issue object
    """
    worksheet[f"{column1}{row_number}"] = issue.sourceReport or ""
    worksheet[f"{column2}{row_number}"] = issue.cve or issue.pluginId or issue.title


def process_row(
    ssp: SecurityPlan,
    poam: Issue,
    index: int,
    sheet: Worksheet,
    assets: List[Asset],
    all_milestones: List[dict],
    all_links: List[dict],
    all_files: List[dict],
    point_of_contact: str = "",
):
    """
    Process a single POAM row in the worksheet

    :param SecurityPlan ssp: Security plan object
    :param Issue poam: POAM issue object
    :param int index: Row index
    :param Worksheet sheet: Worksheet object
    :param List[Asset] assets: Assets list
    :param List[dict] all_milestones: All milestones
    :param List[dict] all_links: All links
    :param List[dict] all_files: All files
    :param str point_of_contact: Point of Contact name for POAMs
    """
    index = EXCEL_TEMPLATE_HEADER_ROWS + index  # Adjust for header rows

    if not index or index < EXCEL_TEMPLATE_HEADER_ROWS:
        return

    try:
        props = Property.get_all_by_parent(parent_id=poam.id, parent_module="issues")

        # Normalize source report name
        _normalize_source_report(poam)

        # Populate basic columns (B-I)
        _populate_basic_poam_columns(sheet, index, poam, point_of_contact)

        # Map weakness detector and source ID (E-F)
        map_weakness_detector_and_id_for_rev5_issues(
            worksheet=sheet, column1="E", column2="F", row_number=index, issue=poam
        )

        # Populate remediation and date columns (J-M)
        sheet[f"J{index}"].value = strip_html(poam.remediationDescription)
        _populate_date_and_milestone_columns(sheet, index, poam, all_milestones)

        # Populate changes and status columns (N-R)
        sheet[f"N{index}"].value = strip_html(poam.changes)
        set_status(poam, index, sheet)
        set_vendor_info(poam, index, sheet)

        # Populate risk and deviation columns (S-X)
        set_risk_info(poam, index, sheet)

        # Populate end columns (Y-AE)
        set_end_columns(ssp, poam, index, sheet, props, assets, all_links, all_files)

        # Set POAM ID (column A)
        new_poam_id = determine_poam_id(poam, props)
        logger.info("Generated POAM ID For POAM #%s: %s", poam.id, new_poam_id)
        sheet[f"A{index}"].value = new_poam_id

    except (KeyError, AttributeError, ValueError, TypeError) as e:
        logger.error("Error processing POAM #%s: %s", poam.id, e)


def update_column_widths(ws: Worksheet) -> None:
    """
    Update column widths and formatting for the worksheet

    :param Worksheet ws: Worksheet to format
    """
    # Define specific column widths
    fixed_widths = {
        "A": 15,  # POAM ID
        "B": 10,  # Control
        "C": 40,  # Title
        "D": 50,  # Description
        "E": 20,  # Source Report
        "F": 20,  # Plugin ID/CVE
        "G": 30,  # Asset Identifier
        "H": 15,  # Point of Contact
        "I": 50,  # Service Name
        "J": 15,  # Remediation
        "K": 15,  # Detection Date
        "L": 15,  # Due Date
        "M": 15,  # Milestones
        "N": 30,  # Changes
        "O": 15,  # Completion Date
        "P": 15,  # Vendor Dependency
        "Q": 15,  # Vendor Last Update
        "R": 20,  # Vendor Name
        "S": 15,  # Original Risk
        "T": 15,  # Adjusted Risk
        "U": 15,  # Risk Adjustment
        "V": 15,  # False Positive
        "W": 15,  # Operational Requirement
        "X": 30,  # Deviation Rationale
        "Y": 40,  # Links and Files
        "Z": 50,  # POAM Comments
        "AA": 15,  # Auto Approved
        "AB": 15,  # KEV List
        "AC": 15,  # KEV Due Date
        "AD": 20,  # CVE
        "AE": 30,  # Service Name
    }

    # Apply fixed widths
    for col, width in fixed_widths.items():
        ws.column_dimensions[col].width = width

    # Enable text wrapping for specific columns
    wrap_columns = ["C", "D", "I", "X", "Y", "Z"]
    for col in wrap_columns:
        for cell in ws[col]:
            if not isinstance(cell, openpyxl.cell.cell.MergedCell) and cell.value:
                cell.alignment = openpyxl.styles.Alignment(wrap_text=True)


def align_column(column_letter: str, worksheet: Worksheet) -> None:
    """
    Align column text to the left and wrap text

    :param str column_letter: Column letter to align
    :param Worksheet worksheet: Worksheet object
    """
    for cell in worksheet[column_letter]:
        cell.alignment = openpyxl.styles.Alignment(wrap_text=True, horizontal="left")
        cell.value = cell.value.strip() if cell.value else ""


def update_header(ssp: SecurityPlan, sheet: Worksheet) -> Worksheet:
    """
    Update the header rows of the worksheet with SSP information

    :param SecurityPlan ssp: Security plan object
    :param Worksheet sheet: Worksheet object
    :return: Updated worksheet
    :rtype: Worksheet
    """
    sheet["A3"] = ssp.cspOrgName or "N/A"
    sheet["B3"] = ssp.systemName
    sheet["C3"] = ssp.overallCategorization
    sheet["D3"] = datetime.now().strftime("%m/%d/%Y")
    return sheet


def get_all_poams(ssp_id: str) -> List[Issue]:
    """
    Get all POAMs for the given SSP ID, including those from child assets

    :param str ssp_id: SSP ID
    :return: List of POAM issues
    :rtype: List[Issue]
    """
    logger.info("Getting POAMs for SSP %s", ssp_id)
    poams = [iss for iss in Issue.get_all_by_parent(parent_id=ssp_id, parent_module="securityplans") if iss.isPoam]

    assets = Asset.get_all_by_parent(parent_id=ssp_id, parent_module="securityplans")
    unique_poams = {
        (
            poam.otherIdentifier,
            poam.assetIdentifier,
            poam.cve,
            poam.pluginId,
            poam.title,
        )
        for poam in poams
    }

    for asset in assets:
        asset_poams = [iss for iss in Issue.get_all_by_parent(parent_id=asset.id, parent_module="assets") if iss.isPoam]
        for asset_poam in asset_poams:
            if not asset_poam.otherIdentifier:
                continue
            poam_tuple = (
                asset_poam.otherIdentifier,
                asset_poam.assetIdentifier,
                asset_poam.cve,
                asset_poam.pluginId,
                asset_poam.title,
            )
            if poam_tuple not in unique_poams:
                poams.append(asset_poam)
                unique_poams.add(poam_tuple)

    logger.info("Found %s POAMs", len(poams))
    return poams


def gen_links(all_poams: List[Issue]) -> List[dict]:
    """
    Generate list of links for all POAMs

    :param List[Issue] all_poams: All POAM issues
    :return: List of link dicts
    :rtype: List[dict]
    """
    logger.info("Building list of links")
    res = [Link.get_all_by_parent(parent_id=iss.id, parent_module="issues") for iss in all_poams]
    return [link for sublist in res for link in sublist]


def gen_files(all_poams: List[Issue], api: Api) -> List[dict]:
    """
    Generate list of files for all POAMs

    :param List[Issue] all_poams: All POAM issues
    :param Api api: API client
    :return: List of file dicts
    :rtype: List[dict]
    """
    logger.info("Building list of files")
    res = [
        File.get_files_for_parent_from_regscale(parent_id=iss.id, parent_module="issues", api=api) for iss in all_poams
    ]
    return [file for sublist in res for file in sublist]


def gen_milestones(all_poams: List[Issue], api: Api, app: Application) -> List[dict]:
    """
    Generate list of milestones for all POAMs

    :param List[Issue] all_poams: All POAM issues
    :param Api api: API client
    :param Application app: Application object
    :return: List of milestone dicts
    :rtype: List[dict]
    """
    logger.info("Building list of milestones")
    milestones = []
    url = app.config["domain"] + "/api/milestones/getAllByParent/"
    for iss in all_poams:
        dat = api.get(f"{url}{iss.id}/issues").json()
        milestones.extend(dat)
    return milestones


def process_worksheet(
    ssp: SecurityPlan,
    sheet_name: str,
    workbook_path: Path,
    all_poams: List[Issue],
    all_milestones: List[dict],
    all_links: List[dict],
    all_files: List[dict],
    point_of_contact: str = "",
):
    """
    Process a single worksheet (Open or Closed POAMs)

    :param SecurityPlan ssp: Security plan object
    :param str sheet_name: Worksheet name ("Open POA&M Items" or "Closed POA&M Items")
    :param Path workbook_path: Path to workbook file
    :param List[Issue] all_poams: All POAM issues
    :param str point_of_contact: Point of Contact name for POAMs
    :param List[dict] all_milestones: All milestones
    :param List[dict] all_links: All links
    :param List[dict] all_files: All files
    """
    logger.info("Processing worksheet: %s", sheet_name)

    wb = openpyxl.load_workbook(workbook_path)
    sheet = wb[sheet_name]

    status = IssueStatus.Closed if sheet_name == "Closed POA&M Items" else IssueStatus.Open

    sheet = update_header(ssp=ssp, sheet=sheet)

    assets = Asset.get_all_by_parent(parent_id=ssp.id, parent_module="securityplans")

    # Process POAMs matching the status
    matching_poams = [poam for poam in sorted(all_poams, key=lambda x: x.id) if poam.status == status]

    for ix, poam in enumerate(matching_poams):
        process_row(
            ssp=ssp,
            poam=poam,
            index=ix,
            sheet=sheet,
            assets=assets,
            all_milestones=all_milestones,
            all_links=all_links,
            all_files=all_files,
            point_of_contact=point_of_contact,
        )

    logger.info("Processed %s %s POAMs out of %s Total POAMs", len(matching_poams), status, len(all_poams))

    # Format worksheet
    update_column_widths(sheet)
    align_column("G", sheet)

    # Format date column
    for cell in sheet["L"]:
        if cell.row >= 6:
            cell.number_format = "mm/dd/yyyy"

    wb.save(workbook_path)
    logger.info("Saved worksheet: %s", sheet_name)


def export_poam_v5(ssp_id: str, output_file: str, template_path: Optional[Path] = None, point_of_contact: str = ""):
    """
    Export FedRAMP Rev 5 POAM Excel file

    :param str ssp_id: SSP ID
    :param str output_file: Output file path
    :param Optional[Path] template_path: Path to FedRAMP POAM template
    :param str point_of_contact: Point of Contact name for POAMs (defaults to empty string)
    """
    logger.info("Starting FedRAMP Rev 5 POAM export for SSP %s", ssp_id)

    app = Application()
    api = Api()

    # Get SSP info
    ssp = SecurityPlan.get_object(ssp_id)
    if not ssp:
        logger.error("SSP %s not found", ssp_id)
        return

    logger.info("Exporting POAMs for SSP: %s", ssp.systemName)

    # Get all POAMs
    all_poams = get_all_poams(ssp_id)
    if not all_poams:
        logger.warning("No POAMs found for SSP %s", ssp_id)
        return

    # Get related data
    all_links = gen_links(all_poams)
    all_files = gen_files(all_poams, api)
    all_milestones = gen_milestones(all_poams, api, app)

    # Copy template to output location
    if not template_path:
        import importlib.resources as pkg_resources
        from regscale import templates

        files = pkg_resources.files(templates)
        template_path = files / "FedRAMP-POAM-Template.xlsx"
        # Look for template in templates directory first, then current directory
        template_path = Path(template_path)

    if not template_path.exists():
        logger.error("Template file not found: %s", template_path)
        logger.error("Please provide a FedRAMP POAM template Excel file or place it in ./templates/ directory")
        return

    output_path = Path(output_file)
    if output_path.suffix != ".xlsx":
        output_path = output_path.with_suffix(".xlsx")

    shutil.copy(template_path, output_path)
    logger.info("Copied template to: %s", output_path)

    # Process both worksheets
    for sheet_name in ["Open POA&M Items", "Closed POA&M Items"]:
        process_worksheet(
            ssp=ssp,
            sheet_name=sheet_name,
            workbook_path=output_path,
            all_poams=all_poams,
            all_milestones=all_milestones,
            all_links=all_links,
            all_files=all_files,
            point_of_contact=point_of_contact,
        )

    logger.info("POAMs exported successfully to: %s", output_path.absolute())
