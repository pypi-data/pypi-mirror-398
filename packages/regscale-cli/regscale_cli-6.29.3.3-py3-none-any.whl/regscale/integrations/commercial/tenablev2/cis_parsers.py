"""Functions for parsing CIS benchmark output from Tenable"""

import logging
import re
from typing import Union, Optional

from regscale.core.app.utils.app_utils import get_current_datetime
from regscale.integrations.scanner_integration import IntegrationFinding, issue_due_date
from regscale.models import regscale_models

logger = logging.getLogger("regscale")

# Constants
_FAR_FUTURE_DATE = "2099-12-31T23:59:59Z"  # Used for passed findings with no remediation needed


def parse_cis_compliance_result(compliance_data: dict, finding: IntegrationFinding) -> IntegrationFinding:
    """
    Parses CIS benchmark compliance data from Tenable and constructs an IntegrationFinding.

    This function processes CIS benchmark compliance check results from either Tenable.io
    compliance export API or Tenable Security Center analysis API, extracting key fields
    and mapping them to RegScale checklist format.

    :param dict compliance_data: The CIS compliance data dictionary from Tenable API
    :param IntegrationFinding finding: The finding object to update with parsed data
    :return: An IntegrationFinding object containing the parsed CIS compliance information
    :rtype: IntegrationFinding

    Example compliance_data structure (Tenable.io):
    {
        "check_id": "123456",
        "check_name": "Ensure SSH Protocol is set to 2",
        "audit_file": "CIS_AlmaLinux_OS_8_Server_v3.0.0_L1.audit",
        "benchmark_name": "CIS AlmaLinux OS 8 Benchmark",
        "benchmark_version": "v3.0.0",
        "status": "FAILED",
        "actual_value": "1",
        "expected_value": "2",
        "check_info": "Description of the check...",
        "solution": "Edit /etc/ssh/sshd_config...",
        "reference": "800-53|AC-17,CSCv7|9.2",
        "see_also": "https://workbench.cisecurity.org/benchmarks/123",
        "asset": {
            "uuid": "abc-123-def",
            "id": "456"
        }
    }
    """

    # Extract basic CIS benchmark information
    check_id = compliance_data.get("check_id", "")
    check_name = compliance_data.get("check_name", "")
    audit_file = compliance_data.get("audit_file", "")
    benchmark_name = compliance_data.get("benchmark_name", "")
    benchmark_version = compliance_data.get("benchmark_version", "")
    status = compliance_data.get("status", "UNKNOWN")

    # Extract check details
    check_info = compliance_data.get("check_info", "")
    solution = compliance_data.get("solution", "")
    reference = compliance_data.get("reference", "")
    see_also = compliance_data.get("see_also", "")

    # Extract actual vs expected values
    actual_value = compliance_data.get("actual_value", "")
    expected_value = compliance_data.get("expected_value", "")

    # Parse CIS level (1 or 2) from audit file name
    # Example: "CIS_AlmaLinux_OS_8_Server_v3.0.0_L1.audit" -> Level 1
    cis_level = _extract_cis_level(audit_file)

    # Parse CIS benchmark ID from check_name or see_also URL
    # Example: "1.1.1.1 Ensure mounting of cramfs filesystems is disabled"
    cis_benchmark_id = _extract_cis_benchmark_id(check_name, see_also)

    # Create descriptive title
    title = f"CIS {cis_benchmark_id}: {check_name}" if cis_benchmark_id else check_name
    issue_title = title

    # Map status to checklist status
    checklist_status = _map_cis_status_to_checklist(status)

    # Map status to issue status (for tracking open/closed)
    issue_status = (
        regscale_models.IssueStatus.Open
        if status in ["FAILED", "WARNING", "ERROR"]
        else regscale_models.IssueStatus.Closed
    )

    # Map status to severity for failed checks
    severity = _map_cis_status_to_severity(status, cis_level, check_name)

    # Set priority based on severity
    priority = severity.value.title() if severity else "Medium"

    # Create comprehensive description
    description = _create_cis_description(
        check_info=check_info,
        benchmark_name=benchmark_name,
        benchmark_version=benchmark_version,
        cis_level=cis_level,
        actual_value=actual_value,
        expected_value=expected_value,
        solution=solution,
    )

    # Create detailed results text
    results = _create_cis_results_text(compliance_data, cis_level, cis_benchmark_id)

    # Extract control references (e.g., NIST 800-53 controls)
    control_references = _extract_control_references(reference)

    # Set timestamps
    current_datetime = get_current_datetime()
    created_date = compliance_data.get("first_seen", current_datetime)
    last_seen = compliance_data.get("last_seen", current_datetime)

    # Calculate due date based on severity (skip for NotAssigned/passed findings)
    if severity != regscale_models.IssueSeverity.NotAssigned:
        due_date = issue_due_date(severity, created_date)
    else:
        # For passed findings, set a far future date since no remediation is needed
        due_date = _FAR_FUTURE_DATE

    # Update finding object
    finding.title = title
    finding.category = f"CIS Benchmark - Level {cis_level}"
    finding.plugin_id = check_id
    finding.plugin_name = check_name
    finding.severity = severity
    finding.description = description
    finding.status = issue_status
    finding.checklist_status = checklist_status
    finding.priority = priority
    finding.first_seen = created_date
    finding.last_seen = last_seen
    finding.issue_title = issue_title
    finding.issue_type = "Risk"
    finding.date_created = created_date
    finding.date_last_updated = last_seen
    finding.due_date = due_date
    finding.external_id = f"CIS:{check_id}:{finding.asset_identifier}"
    finding.recommendation_for_mitigation = solution
    finding.results = results
    finding.baseline = f"{benchmark_name} {benchmark_version}"
    finding.vulnerability_number = cis_benchmark_id
    finding.rule_id = cis_benchmark_id
    finding.control_labels = control_references
    finding.observations = f"Actual: {actual_value}, Expected: {expected_value}"
    finding.gaps = check_info
    finding.evidence = f"Status: {status}, Check ID: {check_id}"
    finding.impact = f"CIS Level {cis_level} compliance impact"

    return finding


def _extract_cis_level(audit_file: str) -> str:
    """
    Extract CIS level (1 or 2) from audit file name.

    :param str audit_file: The audit file name
    :return: CIS level as string ("1" or "2"), defaults to "1" if not found
    :rtype: str

    Examples:
        "CIS_AlmaLinux_OS_8_Server_v3.0.0_L1.audit" -> "1"
        "CIS_Windows_Server_2019_v1.2.1_L2.audit" -> "2"
    """
    match = re.search(r"_L([12])\.audit", audit_file, re.IGNORECASE)
    return match.group(1) if match else "1"


def _extract_cis_benchmark_id(check_name: str, see_also: str) -> str:
    """
    Extract CIS benchmark ID from check name or see_also URL.

    :param str check_name: The check name
    :param str see_also: The see_also URL
    :return: CIS benchmark ID (e.g., "1.1.1.1") or empty string
    :rtype: str

    Examples:
        "1.1.1.1 Ensure mounting of cramfs filesystems is disabled" -> "1.1.1.1"
        "2.3.4 Ensure telnet client is not installed" -> "2.3.4"
    """
    # Try to extract from check name (most common format)
    if match := re.match(r"^([\d.]+)\s+", check_name):
        return match.group(1)

    # Try to extract from see_also URL
    # Example: "https://workbench.cisecurity.org/benchmarks/123"
    if see_also and "workbench.cisecurity.org" in see_also:
        # Extract numeric ID from URL
        if match := re.search(r"/benchmarks/(\d+)", see_also):
            return match.group(1)

    return ""


def _map_cis_status_to_checklist(status: str) -> regscale_models.ChecklistStatus:
    """
    Map CIS compliance status to RegScale ChecklistStatus enum.

    :param str status: The CIS compliance status
    :return: RegScale ChecklistStatus enum value
    :rtype: regscale_models.ChecklistStatus

    Status Mapping:
        PASSED -> PASS
        FAILED -> FAIL
        WARNING -> NOT_REVIEWED (manual check required)
        ERROR -> FAIL
        NOT_APPLICABLE -> NOT_APPLICABLE
    """
    status_map = {
        "PASSED": regscale_models.ChecklistStatus.PASS,
        "FAILED": regscale_models.ChecklistStatus.FAIL,
        "ERROR": regscale_models.ChecklistStatus.FAIL,
        "WARNING": regscale_models.ChecklistStatus.NOT_REVIEWED,  # Manual check required
        "NOT_APPLICABLE": regscale_models.ChecklistStatus.NOT_APPLICABLE,
        "NOT APPLICABLE": regscale_models.ChecklistStatus.NOT_APPLICABLE,
    }

    result_key = status.upper().replace("_", " ").strip()
    if result_key not in status_map:
        logger.warning(f"CIS status '{status}' not found in status map, defaulting to NOT_REVIEWED")
        return regscale_models.ChecklistStatus.NOT_REVIEWED

    return status_map[result_key]


def _map_cis_status_to_severity(status: str, cis_level: str, check_name: str) -> regscale_models.IssueSeverity:
    """
    Map CIS compliance status and level to IssueSeverity enum.

    CIS severity mapping follows Tenable conventions:
    - PASSED: NotAssigned (Info level)
    - FAILED: High for Level 1, Moderate for Level 2
    - WARNING: Moderate (manual check)
    - ERROR: High

    :param str status: The CIS compliance status
    :param str cis_level: The CIS level ("1" or "2")
    :param str check_name: The check name (for additional context)
    :return: IssueSeverity enum value
    :rtype: regscale_models.IssueSeverity
    """
    # Check for critical keywords in check name
    critical_keywords = ["critical", "essential", "must", "required"]
    is_critical = any(keyword in check_name.lower() for keyword in critical_keywords)

    status_upper = status.upper()

    if status_upper == "PASSED":
        return regscale_models.IssueSeverity.NotAssigned
    elif status_upper == "FAILED":
        # Level 1 failures are generally more critical
        if cis_level == "1" or is_critical:
            return regscale_models.IssueSeverity.High
        else:
            return regscale_models.IssueSeverity.Moderate
    elif status_upper == "WARNING":
        # Manual checks are moderate severity
        return regscale_models.IssueSeverity.Moderate
    elif status_upper == "ERROR":
        return regscale_models.IssueSeverity.High
    else:
        return regscale_models.IssueSeverity.Low


def _create_cis_description(
    check_info: str,
    benchmark_name: str,
    benchmark_version: str,
    cis_level: str,
    actual_value: str,
    expected_value: str,
    solution: str,
) -> str:
    """
    Create a comprehensive description for the CIS finding.

    :param str check_info: The check information
    :param str benchmark_name: The benchmark name
    :param str benchmark_version: The benchmark version
    :param str cis_level: The CIS level
    :param str actual_value: The actual value found
    :param str expected_value: The expected value
    :param str solution: The solution/remediation
    :return: Formatted description
    :rtype: str
    """
    description_parts = [
        f"**CIS Benchmark**: {benchmark_name} {benchmark_version}",
        f"**CIS Level**: {cis_level}",
        "",
        "**Check Information**:",
        check_info or "No detailed information available.",
        "",
        "**Compliance Status**:",
        f"- Expected Value: {expected_value or 'N/A'}",
        f"- Actual Value: {actual_value or 'N/A'}",
    ]

    if solution:
        description_parts.extend(
            [
                "",
                "**Remediation**:",
                solution,
            ]
        )

    return "\n".join(description_parts)


def _create_cis_results_text(compliance_data: dict, cis_level: str, cis_benchmark_id: str) -> str:
    """
    Create detailed results text for the CIS finding.

    :param dict compliance_data: The CIS compliance data dictionary
    :param str cis_level: The CIS level
    :param str cis_benchmark_id: The CIS benchmark ID
    :return: Formatted results text
    :rtype: str
    """
    check_id = compliance_data.get("check_id", "")
    check_name = compliance_data.get("check_name", "")
    benchmark_name = compliance_data.get("benchmark_name", "")
    benchmark_version = compliance_data.get("benchmark_version", "")
    status = compliance_data.get("status", "UNKNOWN")
    actual_value = compliance_data.get("actual_value", "")
    expected_value = compliance_data.get("expected_value", "")
    check_info = compliance_data.get("check_info", "")
    solution = compliance_data.get("solution", "")
    reference = compliance_data.get("reference", "")

    results = (
        f"CIS Benchmark ID: {cis_benchmark_id}, Status: {status}, Level: {cis_level}<br><br>"
        f"Benchmark: {benchmark_name} {benchmark_version}<br><br>"
        f"Check Name: {check_name}<br><br>"
        f"Check Content: {check_info}<br><br>"
        f"Expected Value: {expected_value}<br>"
        f"Actual Value: {actual_value}<br><br>"
        f"Fix Text: {solution}<br><br>"
        f"References: {reference}<br>"
        f"Check ID: {check_id}"
    )

    return results


def _extract_control_references(reference: str) -> list:
    """
    Extract control framework references from the reference string.

    :param str reference: The reference string (e.g., "800-53|AC-17,CSCv7|9.2")
    :return: List of control reference strings
    :rtype: list

    Example:
        "800-53|AC-17,CSCv7|9.2,PCI-DSSv3.2.1|2.2.4"
        -> ["800-53:AC-17", "CSCv7:9.2", "PCI-DSSv3.2.1:2.2.4"]
    """
    if not reference:
        return []

    control_refs = []

    # Split by comma to get individual framework references
    ref_parts = reference.split(",")

    for part in ref_parts:
        # Split by pipe to get framework and control ID
        if "|" in part:
            framework, control_id = part.split("|", 1)
            control_refs.append(f"{framework.strip()}:{control_id.strip()}")

    return control_refs


def parse_tenable_sc_cis_result(plugin_output: str, finding: IntegrationFinding) -> IntegrationFinding:
    """
    Parse CIS benchmark results from Tenable Security Center plugin output.

    This function handles the text-based plugin output format from Tenable SC
    and extracts CIS benchmark compliance information.

    :param str plugin_output: The plugin output text from Tenable SC
    :param IntegrationFinding finding: The finding object to update
    :return: Updated IntegrationFinding object
    :rtype: IntegrationFinding

    Example plugin_output format:
        Check Name: 1.1.1.1: Ensure mounting of cramfs filesystems is disabled
        Information: The cramfs filesystem...
        Result: FAILED
        Solution: Edit /etc/modprobe.d/...
        Reference Information: Benchmark|CIS AlmaLinux OS 8 Benchmark v3.0.0 Level 1,Level|1
    """
    # Extract fields using regex patterns (optimized to avoid catastrophic backtracking)
    check_name = _extract_field(r"Check Name:\s*([^\n]+)", plugin_output, re.MULTILINE)
    information = _extract_field(r"Information:\s*([^\n]+)", plugin_output, re.MULTILINE)
    result = _extract_field(r"Result:\s*([^\n]+)", plugin_output, re.IGNORECASE | re.MULTILINE)
    solution = _extract_field(r"Solution:\s*(.*?)(?=\n\nReference Information:)", plugin_output, re.DOTALL)
    ref_info = _extract_field(r"Reference Information:\s*(.*)", plugin_output, re.DOTALL | re.MULTILINE)

    # Parse reference information with error handling
    ref_dict = {}
    for item in ref_info.split(","):
        if "|" in item:
            parts = item.split("|", 1)
            if len(parts) == 2:
                ref_dict[parts[0].strip()] = parts[1].strip()
    benchmark_info = ref_dict.get("Benchmark", "")
    level_info = ref_dict.get("Level", "1")

    # Create compliance data structure
    compliance_data = {
        "check_id": finding.plugin_id or "",
        "check_name": check_name,
        "audit_file": f"CIS_L{level_info}.audit",
        "benchmark_name": benchmark_info,
        "benchmark_version": "",  # Not always available in SC output
        "status": result.upper(),
        "actual_value": "",  # Not always in SC output
        "expected_value": "",  # Not always in SC output
        "check_info": information,
        "solution": solution,
        "reference": ref_info,
        "see_also": "",
        "first_seen": finding.first_seen or get_current_datetime(),
        "last_seen": finding.last_seen or get_current_datetime(),
    }

    # Parse using main CIS parser
    return parse_cis_compliance_result(compliance_data, finding)


def _extract_field(pattern: str, text: str, flags: Union[int, re.RegexFlag] = 0, group: int = 1) -> str:
    """
    Extract a field from a string using a regular expression.

    :param str pattern: The regular expression pattern to search for
    :param str text: The string to search in
    :param Union[int, re.RegexFlag] flags: Optional regular expression flags
    :param int group: The group number to return from the match
    :return: The extracted field as a string, empty string if no match
    :rtype: str
    """
    match = re.search(pattern, text, flags)
    return match.group(group).strip() if match else ""
