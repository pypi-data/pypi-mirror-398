"""Query-based search functionality for QRadar integration.

This module provides functionality to search for specific terms in QRadar logs
and create either evidence (if found) or issues (if not found) in RegScale.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from regscale.core.app.api import Api
from regscale.integrations.commercial.qradar.qradar_evidence import QRadarEvidenceCollector
from regscale.models.regscale_models.issue import Issue
from regscale.models.integration_models.qradar_models.connectors.events import (
    QRadarIntegration,
)

logger = logging.getLogger(__name__)


def handle_query_search(
    plan_id: int,
    query_term: str,
    qradar_config: Dict[str, Any],
    cli_kwargs: Dict[str, Any],
) -> str:
    """
    Search for query term in QRadar logs and create evidence or issue.

    Args:
        plan_id: RegScale security plan ID
        query_term: Term to search for in logs
        qradar_config: QRadar configuration dictionary
        cli_kwargs: Additional CLI arguments (verify_ssl, time_window, etc.)

    Returns:
        Success message string

    Workflow:
        1. Fetch events from QRadar
        2. Search case-insensitively for query term across all event fields
        3. If found: Create evidence file with matching events
        4. If not found: Create issue/POAM in RegScale
    """
    logger.info(f"Starting query search for term: '{query_term}'")

    # Extract configuration parameters
    time_window = cli_kwargs.get("time_window") or qradar_config.get("time_window", 24)
    verify_ssl = cli_kwargs.get("verify_ssl")
    if verify_ssl is None:
        verify_ssl = qradar_config.get("verify_ssl", True)

    # Initialize QRadar events integration
    try:
        qradar_integration = QRadarIntegration(
            plan_id=plan_id,
            qradar_config=qradar_config,
            time_window_hours=time_window,
            verify_ssl=verify_ssl,
        )
    except Exception as e:
        error_msg = f"Failed to initialize QRadar integration: {str(e)}"
        logger.error(error_msg)
        return error_msg

    # Fetch events from QRadar
    logger.info(f"Fetching QRadar events from last {time_window} hours...")
    try:
        events = qradar_integration._fetch_qradar_events()  # pylint: disable=protected-access
        logger.info(f"Retrieved {len(events)} total events from QRadar")
    except Exception as e:
        error_msg = f"Failed to fetch events from QRadar: {str(e)}"
        logger.error(error_msg)
        return error_msg

    if not events:
        logger.warning("No events retrieved from QRadar")
        return "No events found in QRadar for the specified time window"

    # Search for query term across all event fields (case-insensitive)
    matching_events = _search_events_for_term(events, query_term)

    if matching_events:
        # Query term found - create evidence
        return _create_evidence_for_matches(
            plan_id=plan_id,
            query_term=query_term,
            matching_events=matching_events,
            total_events=len(events),
        )
    else:
        # Query term not found - create issue
        return _create_issue_for_missing_term(
            plan_id=plan_id,
            query_term=query_term,
            total_events_searched=len(events),
            time_window=time_window,
        )


def _search_events_for_term(events: List[Any], query_term: str) -> List[Any]:
    """
    Search events for query term across all fields (case-insensitive).

    Args:
        events: List of QRadarEvent objects
        query_term: Term to search for

    Returns:
        List of matching events
    """
    query_lower = query_term.lower()
    matching_events = []

    logger.info(f"Searching {len(events)} events for term: '{query_term}'")

    for event in events:
        # Search across all relevant event fields
        searchable_fields = [
            str(getattr(event, "event_name", "")),
            str(getattr(event, "source_ip", "")),
            str(getattr(event, "dest_ip", "")),
            str(getattr(event, "source_port", "")),
            str(getattr(event, "dest_port", "")),
            str(getattr(event, "username", "")),
            str(getattr(event, "category", "")),
            str(getattr(event, "log_source", "")),
        ]

        # Check if query term appears in any field
        for field_value in searchable_fields:
            if query_lower in field_value.lower():
                matching_events.append(event)
                logger.debug(f"Match found: '{query_term}' in '{field_value}'")
                break  # Only add each event once

    logger.info(f"Found {len(matching_events)} events matching '{query_term}'")
    return matching_events


def _create_evidence_for_matches(
    plan_id: int,
    query_term: str,
    matching_events: List[Any],
    total_events: int,
) -> str:
    """
    Create evidence file for matching events.

    Args:
        plan_id: RegScale security plan ID
        query_term: Query term that was searched
        matching_events: List of events containing the query term
        total_events: Total number of events searched

    Returns:
        Success message
    """
    logger.info(f"Creating evidence file for {len(matching_events)} matching events")

    try:
        # Get API instance
        api = Api()

        # Create evidence collector with query metadata
        evidence_collector = QRadarEvidenceCollector(
            plan_id=plan_id,
            api=api,
            events=matching_events,
            create_ssp_attachment=True,
            compliance_results={
                "query_mode": True,
                "query_term": query_term,
                "total_events_searched": total_events,
                "matching_events_count": len(matching_events),
                "search_timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

        # Upload evidence
        success = evidence_collector.collect_and_upload_evidence()

        if success:
            success_msg = (
                f"[OK] Query term '{query_term}' found in {len(matching_events)} of {total_events} events. "
                f"Evidence file uploaded to security plan {plan_id}."
            )
            logger.info(success_msg)
            return success_msg
        else:
            error_msg = f"Failed to upload evidence file for query term '{query_term}'"
            logger.error(error_msg)
            return error_msg

    except Exception as e:
        error_msg = f"Error creating evidence for query term '{query_term}': {str(e)}"
        logger.error(error_msg)
        return error_msg


def _create_issue_for_missing_term(
    plan_id: int,
    query_term: str,
    total_events_searched: int,
    time_window: int,
) -> str:
    """
    Create issue/POAM when query term is not found in logs.

    Args:
        plan_id: RegScale security plan ID
        query_term: Query term that was searched
        total_events_searched: Total number of events searched
        time_window: Time window in hours that was searched

    Returns:
        Success message
    """
    logger.info(f"Creating issue for missing query term: '{query_term}'")

    try:
        # Create issue in RegScale
        issue = Issue()
        issue.title = f"QRadar Query Not Found: {query_term}"
        issue.description = (
            f"## Query Search Results\n\n"
            f"**Query Term:** `{query_term}`\n\n"
            f"**Status:** Not Found\n\n"
            f"**Search Details:**\n"
            f"- Total events searched: {total_events_searched}\n"
            f"- Time window: Last {time_window} hours\n"
            f"- Search timestamp: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
            f"**Finding:**\n"
            f"The query term '{query_term}' was not found in any of the {total_events_searched} "
            f"QRadar events retrieved from the last {time_window} hours. This may indicate:\n\n"
            f"1. The expected logs are not being generated\n"
            f"2. The logs are not being forwarded to QRadar\n"
            f"3. The query term does not match the actual log content\n"
            f"4. The time window needs to be extended\n\n"
            f"**Recommended Actions:**\n"
            f"- Verify that the expected system/application is configured to send logs to QRadar\n"
            f"- Check QRadar log source configuration and connectivity\n"
            f"- Verify the query term matches the expected log format\n"
            f"- Consider extending the time window if logs may be delayed\n"
            f"- Review QRadar event collection status for relevant log sources\n"
        )
        issue.securityPlanId = plan_id
        issue.parentId = plan_id
        issue.parentModule = "securityplans"
        issue.status = "Open"
        issue.identification = f"QRadar-Query-{query_term}"

        # Set due date to 30 days from now (standard remediation period)
        issue.dueDate = (datetime.now(timezone.utc) + timedelta(days=30)).strftime("%Y-%m-%d")

        # Create the issue using the Issue model's create() method
        created_issue = issue.create()

        if created_issue:
            success_msg = (
                f"[X] Query term '{query_term}' NOT found in {total_events_searched} events "
                f"(last {time_window} hours). Issue #{created_issue.id} created in security plan {plan_id}."
            )
            logger.info(success_msg)
            return success_msg
        else:
            error_msg = f"Failed to create issue for missing query term '{query_term}'"
            logger.error(error_msg)
            return error_msg

    except Exception as e:
        error_msg = f"Error creating issue for missing query term '{query_term}': {str(e)}"
        logger.error(error_msg)
        return error_msg
