#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""QRadar integration CLI commands for RegScale"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import click

from regscale.models import regscale_ssp_id
from regscale.core.app.application import Application
from regscale.core.app.utils.app_utils import error_and_exit
from regscale.integrations.commercial.qradar.constants import (
    ASSESSMENT_RESULT_FAIL,
    ASSESSMENT_RESULT_PASS,
    ASSESSMENT_TYPE_CONTROL_TESTING,
    CONFIG_SECTION,
    DEFAULT_AUDIT_CONTROLS,
    DEFAULT_TIME_WINDOW_HOURS,
    FIELD_AWS_ACCOUNT_ID,
    SEVERITY_MODERATE,
    STATUS_FULLY_IMPLEMENTED,
    STATUS_IN_REMEDIATION,
)

logger = logging.getLogger("regscale")


@dataclass
class QRadarQueryConfig:
    """
    Configuration for a QRadar query.

    Allows querying on any field, not just AWS Account ID.
    This makes the integration flexible enough to query by username,
    IP address, hostname, or any other QRadar field.

    Attributes:
        field_name: QRadar field to query (e.g., "AWS Account ID", "username", "sourceip")
        field_value: Value to search for in the specified field
        time_window_hours: How many hours back to look for events (default: 8)
    """

    field_name: str
    field_value: str
    time_window_hours: int = DEFAULT_TIME_WINDOW_HOURS

    @property
    def display_name(self) -> str:
        """Human-readable description of what we're querying."""
        return f"{self.field_name}: {self.field_value}"


@dataclass
class ControlAssessmentContext:
    """
    Encapsulates control-related data for assessments.

    These three pieces of data are always used together and represent:
    - The control IDs (e.g., "AU-02", "AU-03")
    - The RegScale implementation IDs for those controls
    - The full ControlImplementation objects

    Bundling them prevents misalignment and makes the relationship explicit.

    Attributes:
        control_ids: List of control ID strings (e.g., ["AU-02", "AU-03"])
        implementation_ids: List of RegScale control implementation IDs
        implementations: List of full ControlImplementation objects
    """

    control_ids: List[str]
    implementation_ids: List[int]
    implementations: List[Any]  # List[ControlImplementation] but avoid circular import

    def __post_init__(self) -> None:
        """Validate that all three lists have matching lengths."""
        if not (len(self.control_ids) == len(self.implementation_ids) == len(self.implementations)):
            raise ValueError(
                f"Misaligned control data: {len(self.control_ids)} control_ids, "
                f"{len(self.implementation_ids)} implementation_ids, "
                f"{len(self.implementations)} implementations"
            )

    @property
    def count(self) -> int:
        """Number of controls in this context."""
        return len(self.control_ids)


def _add_kwarg_if_present(
    kwargs: Dict[str, Any], cli_value: Any, config: Dict[str, Any], cli_key: str, config_key: str
) -> None:
    """
    Add a kwarg to the dictionary if CLI value or config value is present.

    Args:
        kwargs: Dictionary to add kwargs to
        cli_value: Value from CLI argument
        config: Configuration dictionary
        cli_key: Key to use in kwargs dictionary
        config_key: Key to look up in config dictionary
    """
    if cli_value or config.get(config_key):
        kwargs[cli_key] = cli_value or config.get(config_key)


def _build_qradar_kwargs(
    base_url: Optional[str],
    api_key: Optional[str],
    time_window: Optional[int],
    severity_threshold: Optional[int],
    account_id: Optional[str],
    verify_ssl: Optional[bool],
    qradar_config: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Build kwargs dict for QRadar integration from CLI args and config.

    Args:
        base_url: QRadar instance URL from CLI
        api_key: QRadar API key from CLI
        time_window: Time window in hours from CLI
        severity_threshold: Minimum severity from CLI
        account_id: AWS account ID filter from CLI
        verify_ssl: SSL verification from CLI
        qradar_config: Configuration from init.yaml

    Returns:
        Dict of kwargs for QRadar integration
    """
    kwargs: Dict[str, Any] = {}
    _add_kwarg_if_present(kwargs, base_url, qradar_config, "base_url", "base_url")
    _add_kwarg_if_present(kwargs, api_key, qradar_config, "api_key", "api_key")
    _add_kwarg_if_present(kwargs, time_window, qradar_config, "time_window_hours", "time_window_hours")
    _add_kwarg_if_present(kwargs, severity_threshold, qradar_config, "severity_threshold", "severity_threshold")
    _add_kwarg_if_present(kwargs, account_id, qradar_config, "account_id_filter", "account_id_filter")

    # Handle verify_ssl separately since None is a valid CLI value
    if verify_ssl is not None:
        kwargs["verify_ssl"] = verify_ssl
    elif "verify_ssl" in qradar_config:
        kwargs["verify_ssl"] = qradar_config.get("verify_ssl")
    return kwargs


def _handle_sync_with_assets(regscale_ssp_id: int, generate_evidence: bool, kwargs: Dict[str, Any]) -> tuple[int, int]:
    """
    Sync QRadar findings with asset generation.

    Args:
        regscale_ssp_id: RegScale Security Plan ID
        generate_evidence: Whether to generate evidence
        kwargs: QRadar integration kwargs

    Returns:
        Tuple of (findings_processed, assets_processed)
    """
    from regscale.models.integration_models.qradar_models.connectors.events import QRadarIntegration

    logger.info("Syncing findings with asset generation enabled")
    scanner = QRadarIntegration(plan_id=regscale_ssp_id, **kwargs)
    kwargs["create_evidence"] = generate_evidence
    return scanner.sync_findings_and_assets(**kwargs)


def _handle_sync_findings_only(regscale_ssp_id: int, generate_evidence: bool, kwargs: Dict[str, Any]) -> int:
    """
    Sync QRadar findings without asset generation.

    Args:
        regscale_ssp_id: RegScale Security Plan ID
        generate_evidence: Whether to generate evidence
        kwargs: QRadar integration kwargs

    Returns:
        Number of findings processed
    """
    from regscale.models.integration_models.qradar_models.connectors.events import QRadarIntegration

    logger.info("Syncing findings only (no asset generation)")
    kwargs["suppress_asset_not_found_errors"] = True
    kwargs["create_evidence"] = generate_evidence
    return QRadarIntegration.sync_findings(plan_id=regscale_ssp_id, **kwargs)


def _normalize_control_id(control_id: str) -> str:
    """
    Normalize control ID by adding leading zero if needed (e.g., AU-2 -> AU-02).

    Args:
        control_id: Control ID to normalize

    Returns:
        Normalized control ID
    """
    if "-" in control_id:
        parts = control_id.split("-")
        if len(parts) == 2:
            family = parts[0].upper()
            number = parts[1]
            # Add leading zero if number is single digit
            if number.isdigit() and len(number) == 1:
                return f"{family}-0{number}"
    return control_id.upper()


def _build_control_lookup(implementations: list) -> tuple[Dict[str, Any], list[str]]:
    """
    Build lookup dictionary mapping control IDs to implementations.

    Args:
        implementations: List of ControlImplementation objects

    Returns:
        Tuple of (control_lookup dict, list of all control IDs)
    """
    from regscale.models.regscale_models.security_control import SecurityControl

    control_lookup = {}
    all_control_ids = []

    for impl in implementations:
        try:
            sec_control = SecurityControl.get_object(object_id=impl.controlID)
            if sec_control and sec_control.controlId:
                control_lookup[sec_control.controlId] = impl
                all_control_ids.append(sec_control.controlId)
                logger.debug(f"Mapped control {sec_control.controlId} to implementation {impl.id}")
        except Exception as e:
            logger.debug(f"Could not fetch security control for implementation {impl.id}: {e}")

    return control_lookup, all_control_ids


def _match_control_implementation(
    control_label: str, control_lookup: Dict[str, Any], all_control_ids: list, ssp_id: int
) -> tuple[Optional[int], Optional[Any]]:
    """
    Match a control label to an implementation, trying exact and alternate formats.

    Args:
        control_label: Control ID to match (e.g., "AU-02")
        control_lookup: Dictionary mapping control IDs to implementations
        all_control_ids: List of all available control IDs
        ssp_id: Security Plan ID (for logging)

    Returns:
        Tuple of (implementation_id, implementation_object) or (None, None)
    """
    # Try exact match first
    if control_label in control_lookup:
        impl = control_lookup[control_label]
        logger.info(f"Found control implementation {impl.id} for control {control_label}")
        return impl.id, impl

    # Try without leading zero (AU-05 -> AU-5)
    if "-" in control_label:
        family, number = control_label.split("-", 1)
        alt_label = f"{family}-{number.lstrip('0')}"
        if alt_label in control_lookup:
            impl = control_lookup[alt_label]
            logger.info(f"Found control implementation {impl.id} for control {control_label} (matched as {alt_label})")
            return impl.id, impl

    # No match found
    logger.warning(
        f"No control implementation found for {control_label} in security plan {ssp_id}. "
        f"Available controls: {', '.join(sorted(all_control_ids)[:20])}"
    )
    return None, None


def _get_control_implementation_ids(control_labels: list, ssp_id: int) -> tuple:
    """
    Fetch control implementation IDs and objects for given control labels.

    Args:
        control_labels: List of control IDs (e.g., ["AU-02", "AU-03"])
        ssp_id: Security Plan ID

    Returns:
        Tuple of (list[int], list[ControlImplementation]): Control implementation IDs and objects
    """
    from regscale.models.regscale_models.control_implementation import ControlImplementation

    control_impl_ids = []
    control_implementations = []

    try:
        # Get all control implementations for this security plan
        implementations = ControlImplementation.get_all_by_parent(parent_module="securityplans", parent_id=ssp_id)
        logger.info(f"Found {len(implementations)} control implementations in security plan {ssp_id}")

        # Build lookup dictionary: control_label -> implementation
        control_lookup, all_control_ids = _build_control_lookup(implementations)

        # Log sample of available controls for debugging
        if all_control_ids:
            sample_controls = sorted(all_control_ids)[:10]
            logger.info(f"Sample available control IDs: {', '.join(sample_controls)}")

        # Find matching implementations for requested control labels
        for control_label in control_labels:
            impl_id, impl = _match_control_implementation(control_label, control_lookup, all_control_ids, ssp_id)
            if impl_id and impl:
                control_impl_ids.append(impl_id)
                control_implementations.append(impl)

    except Exception as e:
        logger.error(f"Error fetching control implementations: {e}")

    return control_impl_ids, control_implementations


def _query_qradar_for_identifier(
    qradar_client: Any, query_config: QRadarQueryConfig, query_timeout: int = 900
) -> tuple[bool, int]:
    """
    Query QRadar for events matching the specified field/value.

    This flexible query function allows searching by any QRadar field (AWS Account ID,
    username, source IP, hostname, etc.) instead of being hardcoded to just AWS accounts.

    Args:
        qradar_client: QRadar API client
        query_config: Configuration specifying what field to query and what value to search for
        query_timeout: Query timeout in seconds (default: 900)

    Returns:
        Tuple of (identifier_found, event_count)
    """
    logger.info(f"Querying QRadar for {query_config.display_name}")

    # Build targeted AQL query for the specified field
    aql_query = f"""
        SELECT "{query_config.field_name}" AS 'query_result'
        FROM events
        WHERE "{query_config.field_name}" = '{query_config.field_value}'
        LIMIT 1
        LAST {query_config.time_window_hours} HOURS
    """

    # Execute query with timeout handling
    logger.info(
        f"Executing optimized existence check for {query_config.display_name} "
        f"(last {query_config.time_window_hours} hours, timeout: {query_timeout}s)"
    )
    logger.debug(f"AQL query: {aql_query}")

    try:
        filtered_events = qradar_client.execute_aql_query(aql_query, query_timeout=query_timeout)
        logger.info(f"Query completed successfully, found {len(filtered_events)} result(s)")
        logger.debug(f"Raw filtered_events response: {filtered_events}")
    except Exception as e:
        # Treat timeout or any query failure as "not found"
        error_msg = str(e)
        if "timed out" in error_msg.lower():
            logger.warning(
                f"Query timed out after {query_timeout} seconds for {query_config.display_name}. "
                f"Treating as 'not found' (no events in last {query_config.time_window_hours} hours)"
            )
        else:
            logger.warning(
                f"Query failed for {query_config.display_name}: {error_msg}. "
                f"Treating as 'not found' (no events in last {query_config.time_window_hours} hours)"
            )
        return False, 0

    # Check if identifier was found in results
    identifier_found = False
    event_count = 0

    if filtered_events and len(filtered_events) > 0:
        result = filtered_events[0]
        logger.debug(f"First result keys: {list(result.keys())}")
        logger.debug(f"First result: {result}")

        # Extract the queried field value from results
        result_value = result.get("query_result", "")
        logger.debug(f"Extracted value: '{result_value}', searching for: '{query_config.field_value}'")

        if result_value == query_config.field_value:
            identifier_found = True
            event_count = 1  # Minimum 1 event found
            logger.info(
                f"Found {query_config.display_name} in QRadar "
                f"(at least 1 event in last {query_config.time_window_hours} hours)"
            )
        else:
            logger.info(
                f"{query_config.display_name} not found in QRadar "
                f"(no events in last {query_config.time_window_hours} hours)"
            )

    return identifier_found, event_count


def _query_qradar_for_account(qradar_client: Any, account_id: str) -> tuple[bool, int]:
    """
    Query QRadar for AWS Account logging data (backward compatibility wrapper).

    DEPRECATED: Use _query_qradar_for_identifier() with QRadarQueryConfig for more flexibility.

    Args:
        qradar_client: QRadar API client
        account_id: AWS Account ID to search for

    Returns:
        Tuple of (account_found, event_count)
    """
    query_config = QRadarQueryConfig(field_name="AWS Account ID", field_value=account_id, time_window_hours=8)
    return _query_qradar_for_identifier(qradar_client, query_config)


def _close_existing_poams_for_account(regscale_ssp_id: int, account_id: str) -> int:
    """
    Close existing POAMs related to missing QRadar logs for a specific account.

    Args:
        regscale_ssp_id: Security Plan ID
        account_id: AWS Account ID to filter POAMs for

    Returns:
        Number of POAMs closed
    """
    from datetime import datetime, timezone
    from regscale.models.regscale_models.issue import Issue
    from regscale.models.regscale_models import IssueStatus

    closed_poam_count = 0
    try:
        all_issues = Issue.get_all_by_parent(parent_module="securityplans", parent_id=regscale_ssp_id)
        # Build the exact title pattern for this specific account
        title_pattern = f"QRadar SIEM Logging Assessment: No valid logs found for AWS Account {account_id}"
        for existing_issue in all_issues:
            if existing_issue.title == title_pattern and existing_issue.status == IssueStatus.Open:
                existing_issue.status = IssueStatus.Closed
                existing_issue.dateCompleted = datetime.now(timezone.utc).strftime("%Y-%m-%d")
                existing_issue.save()
                closed_poam_count += 1
                logger.info(f"Closed existing POAM/Issue {existing_issue.id} for account {account_id}")

        if closed_poam_count > 0:
            logger.info(
                f"Closed {closed_poam_count} POAM(s) for AWS Account {account_id} in security plan {regscale_ssp_id}"
            )
    except Exception as e:
        logger.warning(f"Could not check/close existing POAMs for account {account_id}: {e}")

    return closed_poam_count


def _create_qradar_assessments_per_control(
    query_config: QRadarQueryConfig,
    assessment_result: str,
    event_count: int,
    control_context: ControlAssessmentContext,
) -> list:
    """
    Create Assessment records for QRadar query - one per control.

    Args:
        query_config: Configuration specifying what was queried (field + value)
        assessment_result: "Pass" or "Fail"
        event_count: Number of events found (0 if not found)
        control_context: Bundle of control IDs, implementation IDs, and objects

    Returns:
        List of created Assessment objects
    """
    from datetime import datetime, timezone
    from regscale.models.regscale_models.assessment import (
        Assessment,
        AssessmentStatus,
        AssessmentResultsStatus,
    )

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    assessments = []

    # Map control implementations by their ID for quick lookup
    impl_by_id = {impl.id: impl for impl in control_context.implementations}

    # Create one assessment per control
    for i, control_id in enumerate(control_context.control_ids):
        impl_id = control_context.implementation_ids[i]
        if impl_id not in impl_by_id:
            logger.warning(f"Could not find implementation for control {control_id}")
            continue

        impl = impl_by_id[impl_id]

        # Build control-specific assessment report
        if assessment_result == ASSESSMENT_RESULT_PASS:
            description = f"""**Assessment Summary**

{query_config.display_name} is actively logging to QRadar SIEM for control {control_id}.

**Assessment Details:**
- **Assessment Date:** {timestamp}
- **Result:** PASS
- **Events Found:** {event_count} event(s) in last {query_config.time_window_hours} hours
- **Control:** {control_id}
- **Query Field:** {query_config.field_name}
- **Query Value:** {query_config.field_value}
- **Assessment Type:** QRadar Logging Coverage
- **Query Type:** Targeted AQL Query
- **Time Range:** Last {query_config.time_window_hours} Hours

**Findings:**
The queried identifier ({query_config.display_name}) is successfully forwarding logs to the QRadar SIEM platform, satisfying the logging and monitoring requirements for {control_id}. Evidence of active logging has been captured and linked to this control implementation.

**Control Evaluation:**
{control_id}: {STATUS_FULLY_IMPLEMENTED} - Logs actively flowing to SIEM

**Recommendation:**
Continue monitoring log flow to ensure consistent SIEM coverage for this control."""
            summary = f"{query_config.display_name} logging verified for {control_id} ({event_count} events)"
            result_status = AssessmentResultsStatus.PASS
        else:
            description = f"""**Assessment Summary**

No QRadar SIEM logs found for {query_config.display_name} affecting control {control_id}.

**Assessment Details:**
- **Assessment Date:** {timestamp}
- **Result:** FAIL
- **Events Found:** 0 events in last {query_config.time_window_hours} hours
- **Control:** {control_id}
- **Query Field:** {query_config.field_name}
- **Query Value:** {query_config.field_value}
- **Assessment Type:** QRadar Logging Coverage
- **Query Type:** Targeted AQL Query
- **Time Range:** Last {query_config.time_window_hours} Hours

**Findings:**
The queried identifier ({query_config.display_name}) is NOT forwarding logs to the QRadar SIEM platform. This represents a gap in logging and monitoring requirements for {control_id}.

**Impact:**
Without SIEM integration, security events and audit logs for {query_config.display_name} are not being centrally monitored, analyzed, or retained according to {control_id} compliance requirements.

**Control Evaluation:**
{control_id}: {STATUS_IN_REMEDIATION} - No logs flowing to SIEM

**Required Actions:**
1. Verify logging is enabled for {query_config.display_name}
2. Verify log forwarding to QRadar is configured
3. Check QRadar log sources for proper integration
4. Validate network connectivity and security group rules

A POAM has been created to track remediation of this finding."""
            summary = f"No logs found for {query_config.display_name} - {control_id} assessment failed"
            result_status = AssessmentResultsStatus.FAIL

        # Create assessment for this specific control
        assessment = Assessment(
            title=f"QRadar SIEM Assessment for {control_id.upper()} - {query_config.field_name}",
            assessmentType=ASSESSMENT_TYPE_CONTROL_TESTING,
            parentId=impl.id,
            parentModule="controls",
            status=AssessmentStatus.COMPLETE,
            assessmentResult=result_status,
            plannedStart=timestamp,
            plannedFinish=timestamp,
            actualFinish=timestamp,
            assessmentReport=description,
            summaryOfResults=summary,
            targets=f"{query_config.field_name}: {query_config.field_value}",
            automationInfo="Automated QRadar SIEM assessment via RegScale CLI",
            automationId=f"qradar-query-{query_config.field_name}-{query_config.field_value}-{control_id}",
            metadata=f'{{"field_name": "{query_config.field_name}", "field_value": "{query_config.field_value}", "event_count": {event_count}, "control": "{control_id}"}}',
            isPublic=True,
        )

        created_assessment = assessment.create()
        assessments.append(created_assessment)
        logger.info(f"Created assessment {created_assessment.id} for control {control_id} (implementation {impl.id})")

    return assessments


def _create_ssp_level_assessment(
    regscale_ssp_id: int,
    query_config: QRadarQueryConfig,
    assessment_result: str,
    event_count: int,
    control_context: ControlAssessmentContext,
    control_assessments: list,
) -> Any:
    """
    Create an SSP-level summary assessment for overall visibility.

    Args:
        regscale_ssp_id: Security Plan ID
        query_config: Configuration specifying what was queried (field + value)
        assessment_result: "Pass" or "Fail"
        event_count: Number of events found (0 if not found)
        control_context: Bundle of control IDs, implementation IDs, and objects
        control_assessments: List of control-level Assessment objects

    Returns:
        Created Assessment object
    """
    from datetime import datetime, timezone
    from regscale.models.regscale_models.assessment import Assessment, AssessmentStatus, AssessmentResultsStatus

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Build SSP-level summary
    if assessment_result == ASSESSMENT_RESULT_PASS:
        description = f"""**Assessment Summary**

{query_config.display_name} is actively logging to QRadar SIEM.

**Assessment Details:**
- **Assessment Date:** {timestamp}
- **Result:** PASS
- **Events Found:** {event_count} event(s) in last {query_config.time_window_hours} hours
- **Controls Assessed:** {', '.join(control_context.control_ids)} ({control_context.count} controls)
- **Control-Level Assessments Created:** {len(control_assessments)}
- **Assessment Type:** QRadar Logging Coverage
- **Query Field:** {query_config.field_name}
- **Query Value:** {query_config.field_value}
- **Query Type:** Targeted AQL Query
- **Time Range:** Last {query_config.time_window_hours} Hours

**Findings:**
The specified identifier is successfully forwarding logs to the QRadar SIEM platform, satisfying logging and monitoring control requirements across all assessed controls. Individual control assessments have been created and linked to their respective control implementations.

**Controls Evaluated:**
{chr(10).join(f'- {control_id}: {STATUS_FULLY_IMPLEMENTED} (Logs actively flowing to SIEM)' for control_id in control_context.control_ids)}

**Control Assessment IDs:**
{chr(10).join(f'- {control_context.control_ids[i]}: Assessment {control_assessments[i].id}' for i in range(min(control_context.count, len(control_assessments))))}

**Recommendation:**
Continue monitoring log flow to ensure consistent SIEM coverage. Review individual control assessments for detailed findings."""
        summary = f"{query_config.display_name} logging verified - {control_context.count} controls passing ({event_count} events)"
        result_status = AssessmentResultsStatus.PASS
    else:
        description = f"""**Assessment Summary**

No QRadar SIEM logs found for {query_config.display_name}.

**Assessment Details:**
- **Assessment Date:** {timestamp}
- **Result:** FAIL
- **Events Found:** 0 events in last {query_config.time_window_hours} hours
- **Controls Assessed:** {', '.join(control_context.control_ids)} ({control_context.count} controls)
- **Control-Level Assessments Created:** {len(control_assessments)}
- **Assessment Type:** QRadar Logging Coverage
- **Query Field:** {query_config.field_name}
- **Query Value:** {query_config.field_value}
- **Query Type:** Targeted AQL Query
- **Time Range:** Last {query_config.time_window_hours} Hours

**Findings:**
The specified identifier is NOT forwarding logs to the QRadar SIEM platform. This represents a gap in logging and monitoring requirements affecting all assessed controls. Individual control assessments have been created and linked to their respective control implementations.

**Impact:**
Without SIEM integration, security events and audit logs from this identifier are not being centrally monitored, analyzed, or retained according to compliance requirements.

**Controls Evaluated:**
{chr(10).join(f'- {control_id}: {STATUS_IN_REMEDIATION} (No logs flowing to SIEM)' for control_id in control_context.control_ids)}

**Control Assessment IDs:**
{chr(10).join(f'- {control_context.control_ids[i]}: Assessment {control_assessments[i].id}' for i in range(min(control_context.count, len(control_assessments))))}

**Required Actions:**
1. Verify logging is enabled for {query_config.field_name}: {query_config.field_value}
2. Verify log forwarding to QRadar is configured
3. Check QRadar log sources for integration
4. Validate network connectivity and security group rules

A POAM has been created to track remediation. Review individual control assessments for detailed findings."""
        summary = f"No logs found for {query_config.display_name} - {control_context.count} controls failing"
        result_status = AssessmentResultsStatus.FAIL

    # Create SSP-level assessment
    assessment = Assessment(
        title=f"QRadar SIEM Logging Assessment - {query_config.display_name}",
        assessmentType=ASSESSMENT_TYPE_CONTROL_TESTING,
        securityPlanId=regscale_ssp_id,
        parentModule="securityplans",
        parentId=regscale_ssp_id,
        status=AssessmentStatus.COMPLETE,
        assessmentResult=result_status,
        plannedStart=timestamp,
        plannedFinish=timestamp,
        actualFinish=timestamp,
        assessmentReport=description,
        summaryOfResults=summary,
        targets=f"{query_config.field_name}: {query_config.field_value}",
        automationInfo="Automated QRadar SIEM logging assessment via RegScale CLI",
        automationId=f"qradar-query-{query_config.field_name}-{query_config.field_value}-ssp",
        metadata=f'{{"field_name": "{query_config.field_name}", "field_value": "{query_config.field_value}", "event_count": {event_count}, "controls": {control_context.control_ids}, "control_assessment_count": {len(control_assessments)}}}',
        isPublic=True,
    )

    created_assessment = assessment.create()
    logger.info(f"Created SSP-level summary assessment {created_assessment.id} for {query_config.display_name}")
    return created_assessment


def _create_logging_evidence(
    regscale_ssp_id: int,
    account_id: str,
    event_count: int,
    control_ids_to_map: list,
    control_impl_ids: list,
    assessments: Optional[list] = None,
) -> None:
    """
    Create evidence documenting AWS account logging to QRadar.

    Args:
        regscale_ssp_id: Security Plan ID
        account_id: AWS Account ID
        event_count: Number of events found
        control_ids_to_map: List of control IDs to map to
        control_impl_ids: List of control implementation IDs
        assessments: Optional list of Assessment objects to link evidence to
    """
    from datetime import datetime, timezone
    from regscale.core.app.api import Api
    from regscale.models.regscale_models.evidence import Evidence
    from regscale.models.regscale_models.evidence_mapping import EvidenceMapping
    from regscale.models.regscale_models.file import File
    import gzip
    import json

    api = Api()
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    # Create evidence file content (JSONL.GZ format)
    evidence_data = [
        {
            "type": "metadata",
            "timestamp": timestamp,
            "source": "QRadar SIEM",
            "assessment_type": "AWS Account Logging Coverage",
            "query_type": "Targeted AQL Query",
            "time_range": "Last 8 Hours",
        },
        {
            "type": "account_summary",
            "account_id": account_id,
            "event_count": event_count,
            "assessment_date": timestamp,
            "assessment_result": "PASS",
            "controls_assessed": control_ids_to_map,
        },
    ]

    # Convert to JSONL format and compress
    jsonl_content = "\n".join(json.dumps(record) for record in evidence_data)
    compressed_content = gzip.compress(jsonl_content.encode("utf-8"))

    # Create Evidence record
    evidence_title = f"QRadar AWS Account Logging Assessment - {account_id} - {timestamp}"
    evidence_desc = (
        f"AWS Account {account_id} is actively logging to QRadar SIEM "
        f"(at least {event_count} event found in last 8 hours, assessed {timestamp})"
    )

    evidence = Evidence(title=evidence_title, description=evidence_desc, parentId=regscale_ssp_id)
    created_evidence = evidence.create()

    if created_evidence and created_evidence.id:
        # Upload evidence file
        filename = (
            f"qradar_logging_evidence_{account_id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.jsonl.gz"
        )
        File.upload_file_to_regscale(
            file_name=filename,
            parent_id=created_evidence.id,
            parent_module="evidence",
            api=api,
            file_data=compressed_content,
        )

        # Link evidence to SSP
        EvidenceMapping(evidenceID=created_evidence.id, mappedID=regscale_ssp_id, mappingType="securityplans").create()

        # Link evidence to control implementations
        for control_impl_id in control_impl_ids:
            EvidenceMapping(evidenceID=created_evidence.id, mappedID=control_impl_id, mappingType="controls").create()

        # Link evidence to assessments if provided
        if assessments:
            for assessment in assessments:
                EvidenceMapping(
                    evidenceID=created_evidence.id, mappedID=assessment.id, mappingType="assessments"
                ).create()
            logger.info(
                f"Created evidence record {created_evidence.id} and linked to {len(assessments)} assessments and {len(control_impl_ids)} controls"
            )
        else:
            logger.info(f"Created evidence record {created_evidence.id} and linked to {len(control_impl_ids)} controls")


def _set_control_defaults(control_impl: Any) -> None:
    """
    Set default values for required control implementation fields.

    Args:
        control_impl: ControlImplementation object
    """
    if not control_impl.responsibility:
        control_impl.responsibility = control_impl.get_default_responsibility(parent_id=control_impl.parentId)
        logger.debug(f"Setting default responsibility for implementation {control_impl.id}")

    if not control_impl.implementation:
        control_id = getattr(control_impl.control, "controlId", "control") if control_impl.control else "control"
        control_impl.implementation = f"Implementation details for {control_id} will be documented."
        logger.debug(f"Setting default implementation statement for implementation {control_impl.id}")


def _update_control_objectives(control_impl: Any, status_value: str) -> None:
    """
    Update objectives for a control implementation to match its status.

    Args:
        control_impl: ControlImplementation object
        status_value: Status value to set on objectives
    """
    from regscale.models.regscale_models.implementation_objective import ImplementationObjective

    try:
        objectives = ImplementationObjective.get_all_by_parent(
            parent_module=control_impl.get_module_slug(),
            parent_id=control_impl.id,
        )
        for objective in objectives:
            objective.status = status_value
            objective.save()
        if objectives:
            logger.debug(f"Updated {len(objectives)} objectives for control {control_impl.id}")
    except Exception as obj_error:
        logger.warning(f"Could not update objectives for control {control_impl.id}: {obj_error}")


def _update_controls_to_passing(control_implementations: list, account_id: str) -> None:
    """
    Update control implementations to 'Fully Implemented' status.

    Args:
        control_implementations: List of ControlImplementation objects
        account_id: AWS Account ID (for logging)
    """
    from regscale.models.regscale_models import ControlImplementationStatus
    from regscale.core.app.utils.app_utils import get_current_datetime

    for control_impl in control_implementations:
        try:
            control_impl.status = ControlImplementationStatus.FullyImplemented.value
            control_impl.dateLastAssessed = get_current_datetime()
            control_impl.lastAssessmentResult = "Pass"
            _set_control_defaults(control_impl)
            control_impl.save()
            _update_control_objectives(control_impl, ControlImplementationStatus.FullyImplemented.value)
            logger.info(
                f"Updated control {control_impl.id} to 'Fully Implemented' status (account {account_id} is logging to QRadar)"
            )
        except Exception as e:
            logger.warning(f"Could not update control implementation {control_impl.id}: {e}")


def _check_existing_poam_for_account(regscale_ssp_id: int, account_id: str) -> bool:
    """
    Check if a POAM already exists for this account.

    Args:
        regscale_ssp_id: Security Plan ID
        account_id: AWS Account ID

    Returns:
        True if POAM exists, False otherwise
    """
    from regscale.models.regscale_models.issue import Issue
    from regscale.models.regscale_models import IssueStatus

    issue_title = f"QRadar SIEM Logging Assessment: No valid logs found for AWS Account {account_id}"

    try:
        all_issues = Issue.get_all_by_parent(parent_module="securityplans", parent_id=regscale_ssp_id)
        for existing_issue in all_issues:
            if existing_issue.title == issue_title and existing_issue.status == IssueStatus.Open:
                logger.info(
                    f"POAM already exists for AWS Account {account_id} (Issue ID: {existing_issue.id}). "
                    f"Skipping duplicate creation."
                )
                return True
    except Exception as e:
        logger.warning(f"Could not check for existing POAM: {e}. Will attempt to create new POAM.")

    return False


def _create_missing_logs_poam(
    regscale_ssp_id: int, account_id: str, control_ids_to_map: list, control_impl_ids: list
) -> Any:
    """
    Create a POAM documenting missing QRadar logs for an AWS account.

    Args:
        regscale_ssp_id: Security Plan ID
        account_id: AWS Account ID
        control_ids_to_map: List of control IDs to map to
        control_impl_ids: List of control implementation IDs

    Returns:
        Created Issue object or None
    """
    from datetime import datetime, timedelta, timezone
    from regscale.models.regscale_models.issue import Issue, IssueIdentification
    from regscale.models.regscale_models import IssueStatus, IssueSeverity

    due_date = (datetime.now(timezone.utc) + timedelta(days=90)).strftime("%Y-%m-%d")

    issue = Issue(
        parentId=regscale_ssp_id,
        parentModule="securityplans",
        securityPlanId=regscale_ssp_id,
        title=f"QRadar SIEM Logging Assessment: No valid logs found for AWS Account {account_id}",
        description=f"""
**AWS Account ID:** {account_id}
**Assessment Date:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}
**Time Range:** Last 8 Hours
**Mapped Controls:** {', '.join(control_ids_to_map)}

No logs were found in QRadar for the specified AWS Account ID {account_id} in the last 8 hours. Please investigate why logs are not being forwarded to the SIEM.

This could indicate:
- CloudTrail logs are not configured for this AWS account
- Log forwarding to QRadar is not configured
- The account ID is incorrect or has been recently created
- Network connectivity issues between AWS and QRadar

**Required Actions:**
1. Verify CloudTrail is enabled for account {account_id}
2. Verify log forwarding to QRadar is configured
3. Check QRadar log sources for AWS CloudTrail integration
4. Validate network connectivity and security group rules
""".strip(),
        status=IssueStatus.Open,
        severityLevel=SEVERITY_MODERATE,
        identification=IssueIdentification.SecurityControlAssessment,
        dueDate=due_date,
        controlImplementationIds=control_impl_ids,
    )

    created_issue = issue.create()
    logger.info(f"Created new POAM/Issue {created_issue.id} for AWS Account {account_id}")
    return created_issue


def _update_controls_to_remediation(control_implementations: list, account_id: str) -> None:
    """
    Update control implementations to 'In Remediation' status.

    Args:
        control_implementations: List of ControlImplementation objects
        account_id: AWS Account ID (for logging)
    """
    from regscale.models.regscale_models import ControlImplementationStatus
    from regscale.core.app.utils.app_utils import get_current_datetime

    for control_impl in control_implementations:
        try:
            control_impl.status = ControlImplementationStatus.InRemediation.value
            control_impl.dateLastAssessed = get_current_datetime()
            control_impl.lastAssessmentResult = "Fail"
            _set_control_defaults(control_impl)
            control_impl.save()
            _update_control_objectives(control_impl, ControlImplementationStatus.InRemediation.value)
            logger.info(
                f"Updated control {control_impl.id} to 'In Remediation' status (no logs found for account {account_id})"
            )
        except Exception as e:
            logger.warning(f"Could not update control implementation {control_impl.id}: {e}")


def _handle_account_found(
    regscale_ssp_id: int,
    query_config: QRadarQueryConfig,
    event_count: int,
    control_context: ControlAssessmentContext,
) -> None:
    """
    Handle the case when identifier is found logging to QRadar.

    Args:
        regscale_ssp_id: Security Plan ID
        query_config: Configuration specifying what was queried (field + value)
        event_count: Number of events found
        control_context: Bundle of control IDs, implementation IDs, and objects
    """
    import click

    # Close any existing POAMs (still uses field_value for backward compatibility with POAM lookup)
    closed_poam_count = _close_existing_poams_for_account(regscale_ssp_id, query_config.field_value)

    # Create assessment records (one per control) with detailed descriptions
    control_assessments = _create_qradar_assessments_per_control(
        query_config, ASSESSMENT_RESULT_PASS, event_count, control_context
    )

    # Create SSP-level summary assessment for overall visibility
    ssp_assessment = _create_ssp_level_assessment(
        regscale_ssp_id, query_config, ASSESSMENT_RESULT_PASS, event_count, control_context, control_assessments
    )

    # Create evidence and link to all assessments (control-level + SSP-level)
    all_assessments = control_assessments + [ssp_assessment]
    _create_logging_evidence(
        regscale_ssp_id,
        query_config.field_value,
        event_count,
        control_context.control_ids,
        control_context.implementation_ids,
        all_assessments,
    )

    # Update control status to "Fully Implemented" (PASS)
    try:
        _update_controls_to_passing(control_context.implementations, query_config.field_value)
    except Exception as e:
        logger.warning(f"Could not update control statuses: {e}")

    # Build and display result message
    control_assessment_ids = [str(a.id) for a in control_assessments]
    result_msg = (
        f"Assessment successful: {query_config.display_name} is actively logging to QRadar. "
        f"Created {len(control_assessments)} control assessments ({', '.join(control_assessment_ids)}) "
        f"and 1 SSP-level summary assessment ({ssp_assessment.id}) with evidence. "
        f"Linked to controls: {', '.join(control_context.control_ids)}. Control status updated to passing."
    )
    if closed_poam_count > 0:
        result_msg += f" Closed {closed_poam_count} existing POAM(s) for this identifier."

    logger.info(result_msg)
    click.echo(click.style(result_msg, fg="green"))


def _handle_account_not_found(
    regscale_ssp_id: int,
    query_config: QRadarQueryConfig,
    control_context: ControlAssessmentContext,
) -> None:
    """
    Handle the case when identifier is NOT found logging to QRadar.

    Args:
        regscale_ssp_id: Security Plan ID
        query_config: Configuration specifying what was queried (field + value)
        control_context: Bundle of control IDs, implementation IDs, and objects
    """
    import click

    # Create assessment records (one per control) with detailed descriptions (Fail)
    control_assessments = _create_qradar_assessments_per_control(
        query_config, ASSESSMENT_RESULT_FAIL, 0, control_context
    )

    # Create SSP-level summary assessment for overall visibility
    ssp_assessment = _create_ssp_level_assessment(
        regscale_ssp_id, query_config, ASSESSMENT_RESULT_FAIL, 0, control_context, control_assessments
    )

    # Check if POAM already exists for this identifier (uses field_value for lookup)
    existing_poam_found = _check_existing_poam_for_account(regscale_ssp_id, query_config.field_value)

    if existing_poam_found:
        logger.info("Updating controls to 'In Remediation' status for existing POAM")
        created_issue = None
    else:
        # Create POAM documenting missing logs
        created_issue = _create_missing_logs_poam(
            regscale_ssp_id, query_config.field_value, control_context.control_ids, control_context.implementation_ids
        )

    # Update control status to "In Remediation" (FAIL)
    try:
        _update_controls_to_remediation(control_context.implementations, query_config.field_value)
    except Exception as e:
        logger.warning(f"Could not update control statuses: {e}")

    # Build and display result message
    control_assessment_ids = [str(a.id) for a in control_assessments]
    if created_issue:
        result_msg = (
            f"Assessment completed: No logs found for {query_config.display_name} in QRadar. "
            f"Created {len(control_assessments)} control assessments ({', '.join(control_assessment_ids)}) "
            f"and 1 SSP-level summary assessment ({ssp_assessment.id}). "
            f"POAM/Issue created (ID: {created_issue.id}). "
            f"Controls set to 'In Remediation': {', '.join(control_context.control_ids)}. "
            f"Severity: Moderate (5)."
        )
    else:
        result_msg = (
            f"Assessment completed: No logs found for {query_config.display_name} in QRadar. "
            f"Created {len(control_assessments)} control assessments ({', '.join(control_assessment_ids)}) "
            f"and 1 SSP-level summary assessment ({ssp_assessment.id}). "
            f"POAM already exists for this identifier - no duplicate created. "
            f"Controls remain in 'In Remediation': {', '.join(control_context.control_ids)}."
        )
    logger.info(result_msg)
    click.echo(click.style(result_msg, fg="yellow"))


# Create group to handle QRadar integration
@click.group()
def qradar() -> None:
    """
    Sync events and findings from IBM QRadar SIEM to RegScale.

    QRadar is an enterprise SIEM (Security Information and Event Management) platform
    that collects, normalizes, and analyzes security events from across the IT environment.

    This integration allows you to:
    - Sync assets discovered from QRadar events
    - Create issues/findings from security events
    - Link events to compliance controls
    - Generate evidence for assessments

    Example usage:
        regscale qradar sync-events --base-url https://qradar.example.com --api-key YOUR_KEY --ssp-id 123
        regscale qradar sync-findings --base-url https://qradar.example.com --api-key YOUR_KEY --ssp-id 123
    """


@qradar.command(name="sync-events")  # type: ignore[misc]
@regscale_ssp_id()
@click.option(
    "--base-url",
    help="QRadar instance base URL (overrides config file)",
)
@click.option(
    "--api-key",
    help="QRadar API key (SEC token) (overrides config file)",
)
@click.option(
    "--time-window",
    type=int,
    help="Time window in hours to fetch events (overrides config file)",
)
@click.option(
    "--severity-threshold",
    type=int,
    help="Minimum severity level to sync 0-10 (overrides config file)",
)
@click.option(
    "--verify-ssl/--no-verify-ssl",
    default=None,
    help="Verify SSL certificates (overrides config file)",
)
@click.option(
    "--generate-assets",
    is_flag=True,
    default=False,
    help="Generate and sync assets discovered from filtered events",
)
@click.option(
    "--generate-evidence",
    is_flag=True,
    default=False,
    help="Generate and upload evidence file to security plan",
)
@click.option(
    "--query",
    type=str,
    help="Query term to search for in logs (e.g., AWS account ID). If found, creates evidence; if not found, creates issue.",
)
@click.option(
    "--account-id",
    type=str,
    help="Filter events by AWS Account ID (for CloudTrail events)",
)
def sync_events(
    regscale_ssp_id: int,
    base_url: Optional[str],
    api_key: Optional[str],
    time_window: Optional[int],
    severity_threshold: Optional[int],
    verify_ssl: Optional[bool],
    generate_assets: bool,
    generate_evidence: bool,
    query: Optional[str],
    account_id: Optional[str],
) -> None:
    """
    Sync security events from QRadar into RegScale as findings.

    This command:
    1. Connects to QRadar instance
    2. Fetches security events within the specified time window (filtered by severity)
    3. Creates ONE issue per filtered event (deduplicated by event signature)
    4. Optionally generates and syncs discovered assets (--generate-assets flag)
    5. Optionally uploads evidence file to security plan (--generate-evidence flag)

    Severity Filtering:
    Events are filtered at the QRadar API level using the severity_threshold parameter.
    Only events with severity >= threshold are retrieved and processed.

    Asset Generation:
    When --generate-assets is used, assets are automatically discovered from event
    source/destination IPs and created in RegScale before creating issues.

    Evidence Generation:
    When --generate-evidence is used, a single JSONL.GZ evidence file containing
    all filtered events is uploaded to the security plan.

    Query Mode:
    When --query is provided, the command searches for the specified term
    across all event fields (case-insensitive). If found, matching events
    are collected as evidence. If not found, an issue/POAM is created.

    Args:
        regscale_ssp_id: RegScale Security Plan ID
        base_url: QRadar instance URL
        api_key: QRadar API key (SEC token)
        time_window: Hours of events to retrieve (default: 24)
        severity_threshold: Minimum severity to process (0-10, default: 5)
        verify_ssl: Whether to verify SSL certificates
        generate_assets: Whether to create assets from filtered events
        generate_evidence: Whether to upload evidence file
        query: Search term for query mode (e.g., AWS account ID)

    Examples:
        # Sync last 8 hours of events (issues only)
        regscale qradar sync-events --id 123

        # Sync events with assets and evidence
        regscale qradar sync-events --id 123 --generate-assets --generate-evidence

        # Sync last 7 days of critical events with assets
        regscale qradar sync-events --id 123 --time-window 168 --severity-threshold 8 --generate-assets

        # Search for AWS account ID in logs
        regscale qradar sync-events --id 123 --query "123456789012"
    """
    try:
        logger.info("Starting QRadar event sync for SSP %d", regscale_ssp_id)

        # Load configuration from init.yaml
        app = Application()
        qradar_config = app.config.get(CONFIG_SECTION, {})

        # Build kwargs for integration
        kwargs = _build_qradar_kwargs(
            base_url, api_key, time_window, severity_threshold, account_id, verify_ssl, qradar_config
        )

        # Handle query mode: search for term in logs and create evidence or issue
        if query:
            from regscale.integrations.commercial.qradar.qradar_query import handle_query_search

            result_message = handle_query_search(
                plan_id=regscale_ssp_id, query_term=query, qradar_config=qradar_config, cli_kwargs=kwargs
            )
            logger.info(result_message)
            click.echo(click.style(result_message, fg="green"))
            return

        # Determine sync strategy based on flags
        if generate_assets:
            findings_processed, assets_processed = _handle_sync_with_assets(regscale_ssp_id, generate_evidence, kwargs)
            logger.info("QRadar sync completed: %s findings, %s assets", findings_processed, assets_processed)
            click.echo(
                click.style(
                    f"QRadar sync completed successfully: {findings_processed} findings, {assets_processed} assets",
                    fg="green",
                )
            )
        else:
            findings_processed = _handle_sync_findings_only(regscale_ssp_id, generate_evidence, kwargs)
            logger.info("QRadar event sync completed successfully")
            click.echo(click.style(f"QRadar sync completed: {findings_processed} findings synced", fg="green"))
            click.echo(
                click.style(
                    "Note: Assets were not created. Use --generate-assets flag to create assets from events.",
                    fg="yellow",
                )
            )

    except Exception as exc:
        error_msg = f"Error syncing QRadar events: {exc!s}"
        logger.error(error_msg)
        logger.debug(error_msg, exc_info=True)
        error_and_exit(error_msg)


def _resolve_query_parameters(
    account_id: Optional[str], query_field: Optional[str], query_value: Optional[str]
) -> tuple[str, str]:
    """Resolve query parameters with backward compatibility for account_id."""
    if account_id and not (query_field and query_value):
        return FIELD_AWS_ACCOUNT_ID, account_id
    if not (query_field and query_value):
        error_and_exit("Must provide either --account-id OR both --query-field and --query-value")
    return query_field, query_value


def _load_qradar_config(
    base_url: Optional[str], api_key: Optional[str], verify_ssl: Optional[bool]
) -> tuple[str, str, bool]:
    """Load and validate QRadar configuration from CLI args or init.yaml."""
    app = Application()
    qradar_config = app.config.get(CONFIG_SECTION, {})

    resolved_base_url = base_url or qradar_config.get("base_url")
    resolved_api_key = api_key or qradar_config.get("api_key")
    resolved_verify_ssl = verify_ssl if verify_ssl is not None else qradar_config.get("verify_ssl", True)

    if not resolved_base_url:
        error_and_exit("QRadar base_url required (provide --base-url or add to init.yaml)")
    if not resolved_api_key:
        error_and_exit("QRadar api_key required (provide --api-key or add to init.yaml)")

    return resolved_base_url, resolved_api_key, bool(resolved_verify_ssl)


@qradar.command(name="query-events")  # type: ignore[misc]
@regscale_ssp_id()
@click.option(
    "--base-url",
    help="QRadar instance base URL (overrides config file)",
)
@click.option(
    "--api-key",
    help="QRadar API key (SEC token) (overrides config file)",
)
@click.option(
    "--api-version",
    help="QRadar API version (e.g., 19.0, 26.0) (overrides config file, defaults to 19.0)",
)
@click.option(
    "--account-id",
    type=str,
    help="AWS Account ID to assess for logging coverage (deprecated - use --query-value with --query-field)",
)
@click.option(
    "--query-field",
    type=str,
    help="QRadar field to query (e.g., 'AWS Account ID', 'username', 'sourceip')",
)
@click.option(
    "--query-value",
    type=str,
    help="Value to search for in the specified field",
)
@click.option(
    "--time-window-hours",
    type=int,
    default=8,
    help="How many hours back to query (default: 8)",
)
@click.option(
    "--mapped-controls",
    multiple=True,
    help="Control IDs to associate with assessment (e.g., AU-02, AU-03, AU-06, AU-12). Can be specified multiple times. Accepts formats like AU-2 or AU-02. Default: AU-02, AU-03, AU-06, AU-12.",
)
@click.option(
    "--verify-ssl/--no-verify-ssl",
    default=None,
    help="Verify SSL certificates (overrides config file)",
)
@click.option(
    "--query-timeout",
    type=int,
    default=900,
    help="Query timeout in seconds (default: 900). Queries that timeout will be treated as 'not found'.",
)
def query_events(
    regscale_ssp_id: int,
    base_url: Optional[str],
    api_key: Optional[str],
    api_version: Optional[str],
    account_id: Optional[str],
    query_field: Optional[str],
    query_value: Optional[str],
    time_window_hours: int,
    mapped_controls: tuple,
    verify_ssl: Optional[bool],
    query_timeout: int,
) -> None:
    """
    Assess logging coverage in QRadar SIEM for any identifier.

    This command runs a targeted AQL query to determine if a specified identifier
    (AWS Account ID, username, IP address, etc.) has events logged in the SIEM.
    Based on the results:

    - If identifier found with events: Creates evidence documenting event count
    - If identifier NOT found: Creates POAM/Issue for missing logs

    The assessment evaluates:
    - AU-02 (Audit Events): Events are being generated
    - AU-03 (Content of Audit Records): Audit records contain adequate information
    - AU-06 (Audit Review, Analysis, and Reporting): Logs available for review
    - AU-12 (Audit Generation): System capability to generate audit records

    Performance: Uses targeted query for specific identifier (completes in seconds vs
    5-10 minutes for saved search on production QRadar).

    Args:
        regscale_ssp_id: RegScale Security Plan ID
        base_url: QRadar instance URL
        api_key: QRadar API key (SEC token)
        api_version: QRadar API version (e.g., 19.0, 26.0)
        account_id: AWS Account ID to assess (deprecated - use query_field + query_value)
        query_field: QRadar field to query (e.g., 'AWS Account ID', 'username', 'sourceip')
        query_value: Value to search for in the specified field
        time_window_hours: How many hours back to query (default: 8)
        mapped_controls: Control IDs to map to assessment results
        verify_ssl: Whether to verify SSL certificates

    Examples:
        # Assess AWS account logging (backward compatible)
        regscale qradar query-events --id 123 --account-id 123456789012

        # Query by username
        regscale qradar query-events --id 123 --query-field username --query-value jdoe

        # Query by source IP with custom time window
        regscale qradar query-events --id 123 --query-field sourceip --query-value 10.0.1.5 --time-window-hours 4

        # Query with custom control mapping
        regscale qradar query-events --id 123 --query-field username --query-value jdoe \\
            --mapped-controls AU-02 --mapped-controls AU-06
    """
    from regscale.integrations.commercial.qradar.qradar_api_client import QRadarAPIClient, QRadarAPIException

    try:
        # Resolve query parameters with backward compatibility
        resolved_field, resolved_value = _resolve_query_parameters(account_id, query_field, query_value)
        logger.info(
            f"Starting QRadar logging assessment for {resolved_field} '{resolved_value}' in SSP {regscale_ssp_id}"
        )

        # Load and validate configuration
        resolved_base_url, resolved_api_key, resolved_verify_ssl = _load_qradar_config(base_url, api_key, verify_ssl)

        # Create query configuration
        query_config = QRadarQueryConfig(
            field_name=resolved_field, field_value=resolved_value, time_window_hours=time_window_hours
        )

        # Set up control mappings
        raw_control_ids = list(mapped_controls) if mapped_controls else DEFAULT_AUDIT_CONTROLS
        control_ids_to_map = [_normalize_control_id(cid) for cid in raw_control_ids]
        logger.info(f"Mapping assessment to controls: {', '.join(control_ids_to_map)}")

        # Initialize QRadar client
        qradar_client = QRadarAPIClient(
            base_url=resolved_base_url,
            api_key=resolved_api_key,
            verify_ssl=resolved_verify_ssl,
            api_version=api_version,
        )

        # Query QRadar for identifier logging data
        identifier_found, event_count = _query_qradar_for_identifier(qradar_client, query_config, query_timeout)

        # Get control implementations and bundle them
        control_impl_ids, control_implementations = _get_control_implementation_ids(control_ids_to_map, regscale_ssp_id)
        logger.info(f"Associating assessment with {len(control_impl_ids)} control implementation(s)")

        control_context = ControlAssessmentContext(
            control_ids=control_ids_to_map,
            implementation_ids=control_impl_ids,
            implementations=control_implementations,
        )

        # Process results
        if identifier_found:
            _handle_account_found(regscale_ssp_id, query_config, event_count, control_context)
        else:
            _handle_account_not_found(regscale_ssp_id, query_config, control_context)

    except QRadarAPIException as exc:
        error_msg = f"QRadar API error during assessment: {exc!s}"
        logger.error(error_msg)
        click.echo(click.style(error_msg, fg="red"))
        error_and_exit(error_msg)

    except Exception as exc:
        error_msg = f"Error during QRadar assessment: {exc!s}"
        logger.error(error_msg)
        logger.debug(error_msg, exc_info=True)
        error_and_exit(error_msg)


@qradar.command(name="test-connection")
@click.option(
    "--base-url",
    help="QRadar instance base URL (overrides config file)",
)
@click.option(
    "--api-key",
    help="QRadar API key (SEC token) (overrides config file)",
)
@click.option(
    "--api-version",
    help="QRadar API version (e.g., 19.0, 26.0) (overrides config file, defaults to 19.0)",
)
@click.option(
    "--verify-ssl/--no-verify-ssl",
    default=None,
    help="Verify SSL certificates (overrides config file)",
)
def test_connection(
    base_url: Optional[str],
    api_key: Optional[str],
    api_version: Optional[str],
    verify_ssl: Optional[bool],
) -> None:
    """
    Test connection to QRadar instance.

    Verifies that:
    - QRadar API is accessible
    - API credentials are valid
    - SSL certificates are valid (if verification enabled)

    Args:
        base_url: QRadar instance URL
        api_key: QRadar API key (SEC token)
        verify_ssl: Whether to verify SSL certificates

    Examples:
        # Test connection with config from init.yaml
        regscale qradar test-connection

        # Test connection without SSL verification (development)
        regscale qradar test-connection --no-verify-ssl
    """
    from regscale.integrations.commercial.qradar.qradar_api_client import QRadarAPIClient, QRadarAPIException

    try:
        # Load configuration from init.yaml
        app = Application()
        qradar_config = app.config.get(CONFIG_SECTION, {})

        # Use CLI args if provided, otherwise use config
        base_url = base_url or qradar_config.get("base_url")
        api_key = api_key or qradar_config.get("api_key")
        verify_ssl = verify_ssl if verify_ssl is not None else qradar_config.get("verify_ssl", True)

        # Validate required fields
        if not base_url:
            error_and_exit("QRadar base_url required (provide --base-url or add to init.yaml)")
        if not api_key:
            error_and_exit("QRadar api_key required (provide --api-key or add to init.yaml)")

        logger.info("Testing connection to QRadar at %s", base_url)
        click.echo(f"Connecting to QRadar at {base_url}...")

        # Initialize client
        qradar_client = QRadarAPIClient(
            base_url=base_url,
            api_key=api_key,
            verify_ssl=verify_ssl,
            api_version=api_version,
        )

        # Test connection
        qradar_client.test_connection()

        click.echo(click.style("Connection successful!", fg="green"))
        logger.info("QRadar connection test successful")

    except QRadarAPIException as exc:
        error_msg = f"Connection test failed: {exc!s}"
        logger.error(error_msg)
        click.echo(click.style(error_msg, fg="red"))
        error_and_exit(error_msg)

    except Exception as exc:
        error_msg = f"Connection test failed: {exc!s}"
        logger.error(error_msg)
        logger.debug(error_msg, exc_info=True)
        click.echo(click.style(error_msg, fg="red"))
        error_and_exit(error_msg)


@qradar.command(name="assess-compliance")  # type: ignore[misc]
@regscale_ssp_id()
@click.option(
    "--base-url",
    help="QRadar instance base URL (overrides config file)",
)
@click.option(
    "--api-key",
    help="QRadar API key (SEC token) (overrides config file)",
)
@click.option(
    "--time-window",
    type=int,
    help="Time window in hours to fetch events (overrides config file)",
)
@click.option(
    "--framework",
    default="NIST800-53R5",
    help="Compliance framework to assess against (default: NIST800-53R5)",
)
@click.option(
    "--update-controls/--no-update-controls",
    default=True,
    help="Update control statuses in RegScale (default: enabled)",
)
@click.option(
    "--create-evidence/--no-create-evidence",
    default=True,
    help="Create evidence files in RegScale (default: enabled)",
)
@click.option(
    "--verify-ssl/--no-verify-ssl",
    default=None,
    help="Verify SSL certificates (overrides config file)",
)
def assess_compliance(
    regscale_ssp_id: int,
    base_url: Optional[str],
    api_key: Optional[str],
    time_window: Optional[int],
    framework: str,
    update_controls: bool,
    create_evidence: bool,
    verify_ssl: Optional[bool],
) -> None:
    """
    Assess QRadar SIEM compliance and update control statuses in RegScale.

    This command:
    1. Fetches security events from QRadar within the specified time window
    2. Analyzes event data to assess compliance against NIST 800-53 R5 controls
    3. Updates control implementation statuses in RegScale based on assessment
    4. Creates evidence files documenting the compliance assessment
    5. Links evidence to relevant compliance controls

    The assessment evaluates QRadar's monitoring capabilities across multiple control families:
    - AU (Audit and Accountability): Event logging, content, retention
    - SI (System and Information Integrity): Monitoring, intrusion detection
    - IR (Incident Response): Incident detection and reporting
    - AC (Access Control): Account management, authentication tracking
    - IA (Identification and Authentication): Authentication monitoring
    - SC (System and Communications Protection): Boundary protection
    - RA (Risk Assessment): Vulnerability monitoring

    Args:
        regscale_ssp_id: RegScale Security Plan ID
        base_url: QRadar instance URL
        api_key: QRadar API key (SEC token)
        time_window: Hours of events to analyze (default: 24)
        framework: Compliance framework (default: NIST800-53R5)
        update_controls: Whether to update control statuses
        create_evidence: Whether to create evidence files
        verify_ssl: Whether to verify SSL certificates

    Examples:
        # Assess compliance and update controls using last 8 hours of events
        regscale qradar assess-compliance --id 123

        # Assess compliance using last 7 days of events
        regscale qradar assess-compliance --id 123 --time-window 168

        # Assess compliance without updating controls (read-only)
        regscale qradar assess-compliance --id 123 --no-update-controls

        # Assess compliance without creating evidence files
        regscale qradar assess-compliance --id 123 --no-create-evidence
    """
    from regscale.integrations.commercial.qradar.qradar_compliance import (
        QRadarComplianceConfig,
        QRadarComplianceIntegration,
    )

    try:
        logger.info("Starting QRadar compliance assessment for SSP %d", regscale_ssp_id)

        # Load configuration from init.yaml
        app = Application()
        qradar_config = app.config.get(CONFIG_SECTION, {})

        # Build config object - use CLI args if provided, otherwise use config
        config = QRadarComplianceConfig(
            plan_id=regscale_ssp_id,
            framework=framework,
            update_control_status=update_controls,
            create_evidence=create_evidence,
            create_ssp_attachment=create_evidence,
            base_url=base_url or qradar_config.get("base_url"),
            api_key=api_key or qradar_config.get("api_key"),
            time_window_hours=time_window or qradar_config.get("time_window_hours", 24),
            verify_ssl=verify_ssl if verify_ssl is not None else qradar_config.get("verify_ssl", True),
            timeout=qradar_config.get("timeout", 30),
            max_retries=qradar_config.get("max_retries", 3),
            query_timeout=qradar_config.get("query_timeout", 300),
            max_events=qradar_config.get("max_events", 10000),
        )

        # Create compliance integration instance
        compliance_integration = QRadarComplianceIntegration(config)

        # Run compliance sync
        compliance_integration.sync_compliance_data()

        logger.info("QRadar compliance assessment completed successfully")
        click.echo(click.style("QRadar compliance assessment completed successfully!", fg="green"))

        # Display summary
        if compliance_integration.qradar_item:
            click.echo("\nAssessment Summary:")
            click.echo(f"  Total Events Analyzed: {compliance_integration.qradar_item.total_events}")
            click.echo(f"  Event Categories: {compliance_integration.qradar_item.unique_categories}")
            click.echo(f"  Log Sources: {compliance_integration.qradar_item.unique_log_sources}")
            click.echo(f"  High Severity Events: {compliance_integration.qradar_item.high_severity_count}")
            click.echo(f"  Critical Severity Events: {compliance_integration.qradar_item.critical_severity_count}")

            if update_controls:
                passing_count = len(compliance_integration.passing_controls)
                failing_count = len(compliance_integration.failing_controls)
                click.echo("\nControl Assessment:")
                click.echo(f"  Controls Passing: {passing_count}")
                click.echo(f"  Controls Failing: {failing_count}")

    except Exception as exc:
        error_msg = f"Error during QRadar compliance assessment: {exc!s}"
        logger.error(error_msg)
        logger.debug(error_msg, exc_info=True)
        error_and_exit(error_msg)
