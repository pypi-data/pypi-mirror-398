"""Functions for parsing STIG output from Tenable"""

import logging
import re
from typing import Union

from regscale.core.app.utils.app_utils import get_current_datetime
from regscale.integrations.scanner_integration import IntegrationFinding, issue_due_date
from regscale.models import regscale_models

logger = logging.getLogger("regscale")

# Constants
DEFAULT_CCI_REF = "CCI-000366"  # Default CCI reference for STIG findings
UNKNOWN_VULN_NUM = "unknown"
_SOLUTION_KEYWORD = "Solution:"
_REFERENCE_INFO_KEYWORD = "Reference Information:"

# Status mapping for STIG results
_RESULT_STATUS_MAP = {
    "PASSED": regscale_models.ChecklistStatus.PASS,
    "FAILED": regscale_models.ChecklistStatus.FAIL,
    "ERROR": regscale_models.ChecklistStatus.FAIL,
    "NOT APPLICABLE": regscale_models.ChecklistStatus.NOT_APPLICABLE,
    "NOT_APPLICABLE": regscale_models.ChecklistStatus.NOT_APPLICABLE,
}

# Severity mapping for STIG findings
_SEVERITY_MAP = {
    "critical": regscale_models.IssueSeverity.Critical,
    "high": regscale_models.IssueSeverity.High,
    "medium": regscale_models.IssueSeverity.Moderate,
    "low": regscale_models.IssueSeverity.Low,
}


def _extract_field(pattern: str, text: str, flags: Union[int, re.RegexFlag] = 0, group: int = 1) -> str:
    """
    Extracts a field from a string using a regular expression.

    :param str pattern: The regular expression pattern to search for
    :param str text: The string to search in
    :param int flags: Optional regular expression flags, defaults to 0
    :param int group: The group number to return from the match, defaults to 1
    :return: The extracted field as a string. Empty string if no match was found
    :rtype: str
    """
    match = re.search(pattern, text, flags)
    return match.group(group).strip() if match else ""


def _extract_reference_dict(output: str) -> dict:
    """
    Extract and parse reference information into dictionary.

    :param str output: The STIG output string
    :return: Dictionary of reference information
    :rtype: dict
    """
    ref_info = _extract_field(r"Reference Information:\s*(.+)", output, flags=re.DOTALL)
    ref_dict = {}
    for item in ref_info.split(","):
        if "|" in item:
            parts = item.split("|", 1)
            if len(parts) == 2:
                ref_dict[parts[0].strip()] = parts[1].strip()
    return ref_dict


def _map_result_to_status(result: str) -> regscale_models.ChecklistStatus:
    """
    Map result string to ChecklistStatus enum.

    :param str result: The result string from STIG output
    :return: ChecklistStatus enum value
    :rtype: regscale_models.ChecklistStatus
    """
    result_key = result.upper().replace("_", " ").strip()
    if result_key not in _RESULT_STATUS_MAP:
        logger.warning("Result '%s' not found in status map", result)
        return regscale_models.ChecklistStatus.NOT_REVIEWED
    return _RESULT_STATUS_MAP[result_key]


def _map_severity_to_enum(severity: str) -> regscale_models.IssueSeverity:
    """
    Map severity string to IssueSeverity enum.

    :param str severity: The severity string
    :return: IssueSeverity enum value
    :rtype: regscale_models.IssueSeverity
    """
    return _SEVERITY_MAP.get(severity.lower(), regscale_models.IssueSeverity.NotAssigned)


def parse_stig_output(output: str, finding: IntegrationFinding) -> IntegrationFinding:
    """
    Parses STIG output and constructs a finding dictionary matching IntegrationFinding.

    :param str output: The STIG output string to parse.
    :param IntegrationFinding finding: The finding to update.
    :return: An IntegrationFinding object containing the parsed finding information.
    :rtype: IntegrationFinding
    """
    # Extract fields using optimized regex patterns (preventing catastrophic backtracking)
    check_name_full = _extract_field(r"Check Name:\s*([^\n]+)", output)
    check_name_parts = check_name_full.split(":", 1)
    rule_id = check_name_parts[0].strip()
    check_description = check_name_parts[1].strip() if len(check_name_parts) > 1 else ""

    # Extract baseline from Target keyword
    baseline = _extract_field(r"(.*?)\s+Target\s+(.*)", check_description, group=2)
    target_match = _extract_field(r"(.*?)\s+Target\s+(.*)", check_description)
    if target_match:
        check_description = check_description[: check_description.find(target_match) + len(target_match)].strip()

    information = _extract_field(r"Information:\s*([^\n]+)", output)
    vuln_discuss = _extract_field(r"VulnDiscussion='([^']+)'\s", output)
    result = _extract_field(r"Result:\s*([^\n]+)", output, flags=re.IGNORECASE)
    # Extract solution using a safe pattern that avoids backtracking
    # Split on reference keyword and take the solution section
    if _SOLUTION_KEYWORD in output and _REFERENCE_INFO_KEYWORD in output:
        solution_start = output.find(_SOLUTION_KEYWORD) + len(_SOLUTION_KEYWORD)
        ref_start = output.find(_REFERENCE_INFO_KEYWORD, solution_start)
        solution = output[solution_start:ref_start].strip()
    elif _SOLUTION_KEYWORD in output:
        solution_start = output.find(_SOLUTION_KEYWORD) + len(_SOLUTION_KEYWORD)
        solution = output[solution_start:].strip()
    else:
        solution = ""

    # Extract reference information using helper function
    ref_dict = _extract_reference_dict(output)

    # Extract specific references
    cci_ref = ref_dict.get("CCI", DEFAULT_CCI_REF)
    severity_str = ref_dict.get("SEVERITY", "").lower()
    oval_def = ref_dict.get("OVAL-DEF", "")
    generated_date = ref_dict.get("GENERATED-DATE", "")
    updated_date = ref_dict.get("UPDATED-DATE", "")
    scan_date = ref_dict.get("SCAN-DATE", "")
    rule_id_full = ref_dict.get("RULE-ID", "")
    group_id = ref_dict.get("GROUP-ID", "")

    # Extract vulnerability number
    vuln_num_match = re.search(r"SV-\d+r\d+_rule", rule_id)
    vuln_num = vuln_num_match.group(0) if vuln_num_match else UNKNOWN_VULN_NUM

    title = f"{vuln_num}: {check_description}"
    issue_title = title

    # Map result to status using helper function
    status = _map_result_to_status(result)

    # Map severity to IssueSeverity enum using helper function
    priority = (severity_str or "").title()
    severity = _map_severity_to_enum(severity_str)

    results = (
        f"Vulnerability Number: {vuln_num}, Severity: {severity.value}, "
        f"Rule Title: {check_description}<br><br>"
        f"Check Content: {information}<br><br>"
        f"Vulnerability Discussion: {vuln_discuss}<br><br>"
        f"Fix Text: {solution}<br><br>"
        f"STIG Reference: {rule_id}"
    )

    current_datetime = get_current_datetime()
    finding.title = title
    finding.category = "STIG"
    finding.plugin_id = cci_ref
    finding.plugin_name = rule_id
    finding.severity = severity
    finding.description = f"{information}\n\nVulnerability Discussion: {vuln_discuss}\n\nSolution: {solution}"
    finding.status = status
    finding.priority = priority  # Set priority based on severity
    finding.first_seen = current_datetime
    finding.last_seen = current_datetime
    finding.issue_title = issue_title
    finding.issue_type = "Risk"
    finding.date_created = generated_date
    finding.date_last_updated = updated_date
    finding.due_date = issue_due_date(severity, generated_date)
    finding.external_id = f"{cci_ref}:{vuln_num}:{finding.asset_identifier}"
    finding.recommendation_for_mitigation = solution
    finding.cci_ref = cci_ref
    finding.rule_id = rule_id
    finding.results = results
    finding.baseline = baseline
    finding.vulnerability_number = vuln_num
    finding.oval_def = oval_def
    finding.scan_date = scan_date
    finding.rule_id_full = rule_id_full
    finding.group_id = group_id

    return finding
