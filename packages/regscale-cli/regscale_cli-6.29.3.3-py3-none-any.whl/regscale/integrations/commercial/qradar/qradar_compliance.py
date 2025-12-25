#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""QRadar SIEM Compliance Integration for RegScale."""

import gzip
import json
import logging
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from regscale.core.app.api import Api
from regscale.core.app.application import Application
from regscale.integrations.commercial.qradar.qradar_control_mappings import QRadarControlMapper
from regscale.integrations.compliance_integration import ComplianceIntegration
from regscale.models.regscale_models.file import File

logger = logging.getLogger("regscale")


@dataclass
class QRadarComplianceConfig:
    """Configuration for QRadar SIEM compliance assessment."""

    plan_id: int
    framework: str = "NIST800-53R5"
    create_issues: bool = False
    update_control_status: bool = True
    create_poams: bool = False
    parent_module: str = "securityplans"
    create_evidence: bool = True
    create_ssp_attachment: bool = True
    evidence_control_ids: Optional[List[str]] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    api_version: Optional[str] = None
    time_window_hours: int = 24
    severity_threshold: int = 5
    verify_ssl: bool = True
    timeout: int = 60  # Increased from 30 to 60 seconds for initial request
    max_retries: int = 3
    query_timeout: int = 900  # Increased from 300 to 900 seconds (15 minutes)
    max_events: int = 10000


class QRadarComplianceItem:
    """Represents QRadar event data for compliance assessment."""

    def __init__(self, qradar_data: Dict[str, Any]):
        """
        Initialize QRadar compliance item from event data.

        :param Dict qradar_data: QRadar event data and statistics
        """
        self.events = qradar_data.get("events", [])
        self.total_events = qradar_data.get("total_events", 0)
        self.unique_categories = qradar_data.get("unique_categories", 0)
        self.unique_log_sources = qradar_data.get("unique_log_sources", 0)
        self.categories = qradar_data.get("categories", [])
        self.log_sources = qradar_data.get("log_sources", [])
        self.high_severity_count = qradar_data.get("high_severity_count", 0)
        self.critical_severity_count = qradar_data.get("critical_severity_count", 0)
        self.severity_distribution = qradar_data.get("severity_distribution", {})
        self.category_distribution = qradar_data.get("category_distribution", {})
        self.raw_data = qradar_data

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return self.raw_data


class QRadarComplianceIntegration(ComplianceIntegration):
    """QRadar SIEM compliance integration for control assessment and evidence collection."""

    def __init__(self, config: QRadarComplianceConfig):
        """
        Initialize QRadar compliance integration.

        :param QRadarComplianceConfig config: Configuration object containing all parameters
        """
        super().__init__(
            plan_id=config.plan_id,
            framework=config.framework,
            create_issues=config.create_issues,
            update_control_status=config.update_control_status,
            create_poams=config.create_poams,
            parent_module=config.parent_module,
        )

        self.plan_id = config.plan_id
        self.title = "QRadar SIEM"
        self.create_evidence = config.create_evidence
        self.create_ssp_attachment = config.create_ssp_attachment
        self.evidence_control_ids = config.evidence_control_ids or []

        # QRadar configuration
        self.base_url = config.base_url
        self.api_key = config.api_key
        self.api_version = config.api_version
        self.time_window_hours = config.time_window_hours
        self.severity_threshold = config.severity_threshold
        self.verify_ssl = config.verify_ssl
        self.timeout = config.timeout
        self.max_retries = config.max_retries
        self.query_timeout = config.query_timeout
        self.max_events = config.max_events

        # Initialize control mapper
        self.control_mapper = QRadarControlMapper(framework=config.framework)

        # Initialize components
        self.api = Api()
        self.app = Application()
        self._qradar_client: Optional[Any] = None

        # Data storage
        self.raw_qradar_data: Dict[str, Any] = {}
        self.qradar_item: Optional[QRadarComplianceItem] = None

        # Calculate time range for queries
        from datetime import timezone

        self.end_time = datetime.now(timezone.utc)
        self.start_time = self.end_time - timedelta(hours=self.time_window_hours)

        logger.info(f"Initialized QRadar compliance integration for plan {self.plan_id}")

    @property
    def qradar_client(self) -> Any:
        """
        Lazy initialization of QRadar API client.

        Returns:
            QRadarAPIClient instance

        Raises:
            ValueError: If base_url or api_key not configured
        """
        if self._qradar_client is None:
            # Get configuration from init.yaml if not provided
            if not self.base_url or not self.api_key:
                qradar_config = self.app.config.get("qradar", {})
                self.base_url = self.base_url or qradar_config.get("base_url")
                self.api_key = self.api_key or qradar_config.get("api_key")

            # Validate required configuration
            if not self.base_url:
                raise ValueError(
                    "QRadar base_url required. Add to init.yaml under 'qradar' section or pass as --base-url"
                )
            if not self.api_key:
                raise ValueError(
                    "QRadar api_key required. Add to init.yaml under 'qradar' section or pass as --api-key"
                )

            # Import here to avoid circular dependencies
            from regscale.integrations.commercial.qradar.qradar_api_client import QRadarAPIClient

            logger.info(f"Creating QRadar API client for {self.base_url}")
            self._qradar_client = QRadarAPIClient(
                base_url=self.base_url,
                api_key=self.api_key,
                verify_ssl=self.verify_ssl,
                timeout=self.timeout,
                max_retries=self.max_retries,
                api_version=self.api_version,
            )

        return self._qradar_client

    def fetch_compliance_data(self) -> Dict[str, Any]:
        """
        Fetch QRadar event data for compliance assessment.

        :return: QRadar event data and statistics
        :rtype: Dict[str, Any]
        """
        logger.info(f"Fetching QRadar events for compliance assessment (time window: {self.time_window_hours}h)")

        return self._fetch_qradar_events()

    def _fetch_qradar_events(self) -> Dict[str, Any]:
        """
        Fetch events from QRadar and compile statistics.

        :return: Dictionary containing events and statistics
        :rtype: Dict[str, Any]
        """
        # Format times for QRadar API
        start_time_str = self.start_time.strftime("%Y-%m-%d %H:%M:%S")
        end_time_str = self.end_time.strftime("%Y-%m-%d %H:%M:%S")

        logger.info(f"Fetching QRadar events from {start_time_str} to {end_time_str}")

        try:
            # Use the QRadar API client to fetch events
            raw_events = self.qradar_client.get_events(
                start_time=start_time_str,
                end_time=end_time_str,
                filters={},
                limit=self.max_events,
            )

            logger.info(f"Retrieved {len(raw_events)} events from QRadar")

            # Compile statistics from events
            statistics = self._compile_event_statistics(raw_events)

            return statistics

        except Exception as e:
            logger.error(f"Failed to fetch events from QRadar: {str(e)}")
            logger.debug(f"Failed to fetch events from QRadar: {str(e)}", exc_info=True)
            raise

    def _compile_event_statistics(self, raw_events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Compile statistics from QRadar events for compliance assessment.

        :param List[Dict[str, Any]] raw_events: Raw event data from QRadar
        :return: Dictionary with compiled statistics
        :rtype: Dict[str, Any]
        """
        # Initialize counters
        categories = set()
        log_sources = set()
        severity_counts: Dict[int, int] = {}
        category_counts: Dict[str, int] = {}
        high_severity_count = 0
        critical_severity_count = 0

        # Process events
        for event in raw_events:
            # Extract category
            category = (
                event.get("category") or event.get("qidname_qid") or event.get("categoryname_category") or "Unknown"
            )
            categories.add(category)
            category_counts[category] = category_counts.get(category, 0) + 1

            # Extract log source
            log_source = event.get("logsourcename_logsourceid") or event.get("log_source") or "Unknown"
            log_sources.add(log_source)

            # Extract severity/magnitude
            magnitude = event.get("magnitude") or 0
            severity_counts[magnitude] = severity_counts.get(magnitude, 0) + 1

            # Count high/critical severity
            if magnitude >= 8:
                high_severity_count += 1
            if magnitude >= 9:
                critical_severity_count += 1

        statistics = {
            "events": raw_events,
            "total_events": len(raw_events),
            "unique_categories": len(categories),
            "unique_log_sources": len(log_sources),
            "categories": list(categories),
            "log_sources": list(log_sources),
            "high_severity_count": high_severity_count,
            "critical_severity_count": critical_severity_count,
            "severity_distribution": severity_counts,
            "category_distribution": category_counts,
        }

        logger.info(
            f"Compiled QRadar statistics: {len(raw_events)} events, {len(categories)} categories, {len(log_sources)} log sources"
        )
        logger.debug(f"High severity: {high_severity_count}, Critical severity: {critical_severity_count}")

        return statistics

    def sync_compliance_data(self) -> None:
        """Sync QRadar compliance data to RegScale."""
        logger.info("Starting QRadar compliance data sync to RegScale")

        # Fetch QRadar event data
        qradar_data = self.fetch_compliance_data()
        if not qradar_data or qradar_data.get("total_events", 0) == 0:
            logger.warning("No QRadar event data to sync")
            return

        # Convert to compliance item
        self.qradar_item = QRadarComplianceItem(qradar_data)
        logger.info(
            f"Processing {self.qradar_item.total_events} QRadar events for compliance assessment "
            f"({self.qradar_item.unique_categories} categories, {self.qradar_item.unique_log_sources} log sources)"
        )

        # Assess compliance
        compliance_results = self._assess_compliance()

        # Populate control dictionaries for assessment creation
        if self.update_control_status:
            self._populate_control_results(compliance_results["overall"])
            # Create control assessments and update implementation statuses
            self._process_control_assessments()

        # Create evidence artifacts
        if self.create_evidence or self.create_ssp_attachment:
            self._create_evidence_artifacts(compliance_results)

        logger.info("QRadar compliance sync completed successfully")

    def create_compliance_item(self, raw_data: Dict[str, Any]):
        """
        Create a ComplianceItem from raw QRadar data.

        :param Dict[str, Any] raw_data: Raw QRadar event data
        :return: QRadarComplianceItem instance
        :rtype: QRadarComplianceItem
        """
        return QRadarComplianceItem(raw_data)

    def _assess_compliance(self) -> Dict[str, Any]:
        """
        Assess QRadar compliance against NIST controls.

        :return: Compliance assessment results
        :rtype: Dict[str, Any]
        """
        logger.info("Assessing QRadar compliance against NIST 800-53 R5 controls")

        # Assess overall compliance
        overall_results = self.control_mapper.assess_qradar_compliance(self.qradar_item.to_dict())

        # Log summary
        passed_controls = [ctrl for ctrl, result in overall_results.items() if result == "PASS"]
        failed_controls = [ctrl for ctrl, result in overall_results.items() if result == "FAIL"]

        logger.info("QRadar Compliance Assessment Summary:")
        logger.info(f"  Total Events: {self.qradar_item.total_events}")
        logger.info(f"  Event Categories: {self.qradar_item.unique_categories}")
        logger.info(f"  Log Sources: {self.qradar_item.unique_log_sources}")
        logger.info(f"  High Severity Events: {self.qradar_item.high_severity_count}")
        logger.info(f"  Critical Severity Events: {self.qradar_item.critical_severity_count}")
        logger.info(f"  Controls Passed: {len(passed_controls)} - {', '.join(passed_controls)}")
        logger.info(f"  Controls Failed: {len(failed_controls)} - {', '.join(failed_controls)}")

        return {"overall": overall_results}

    def _populate_control_results(self, control_results: Dict[str, str]) -> None:
        """
        Populate passing_controls and failing_controls dictionaries from assessment results.

        This method converts the control-level assessment results into the format expected
        by the base class _process_control_assessments() method.

        :param Dict[str, str] control_results: Control assessment results (e.g., {"AC-2": "PASS", "AC-3": "FAIL"})
        :return: None
        :rtype: None
        """
        for control_id, result in control_results.items():
            # Normalize control ID to lowercase for consistent lookup
            control_key = control_id.lower()

            # Create a simple compliance item placeholder for the base class
            # The base class uses these to determine pass/fail status
            if result in self.PASS_STATUSES:
                self.passing_controls[control_key] = self.qradar_item
            elif result in self.FAIL_STATUSES:
                self.failing_controls[control_key] = self.qradar_item

        logger.debug(
            f"Populated control results: {len(self.passing_controls)} passing, {len(self.failing_controls)} failing"
        )

    def _create_evidence_artifacts(self, compliance_results: Dict[str, Any]) -> None:
        """
        Create evidence artifacts in RegScale.

        :param Dict compliance_results: Compliance assessment results
        """
        logger.info("Creating QRadar compliance evidence artifacts in RegScale")

        # Create comprehensive evidence file
        evidence_file_path = self._create_evidence_file(compliance_results)

        if self.create_ssp_attachment:
            self._create_ssp_attachment_with_evidence(evidence_file_path)

        # Clean up temporary file
        if os.path.exists(evidence_file_path):
            os.remove(evidence_file_path)
            logger.debug(f"Cleaned up temporary evidence file: {evidence_file_path}")

    def _create_evidence_file(self, compliance_results: Dict[str, Any]) -> str:
        """
        Create JSONL.GZ evidence file with QRadar compliance data.

        :param Dict compliance_results: Compliance assessment results
        :return: Path to created evidence file
        :rtype: str
        """
        evidence_file = self._get_evidence_file_path()

        try:
            with gzip.open(evidence_file, "wt", encoding="utf-8") as f:
                self._write_metadata(f)
                self._write_compliance_summary(f, compliance_results)
                self._write_event_statistics(f)
                self._write_sample_events(f)

            logger.info(f"Created QRadar compliance evidence file: {evidence_file}")
            return evidence_file

        except Exception as e:
            logger.error(f"Failed to create evidence file: {e}", exc_info=True)
            raise

    def _get_evidence_file_path(self) -> str:
        """Generate evidence file path with timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return os.path.join(tempfile.gettempdir(), f"qradar_compliance_{timestamp}.jsonl.gz")

    def _write_metadata(self, file_handle) -> None:
        """Write metadata record to evidence file."""
        metadata = {
            "type": "metadata",
            "timestamp": datetime.now().isoformat(),
            "source": "QRadar SIEM",
            "security_plan_id": self.plan_id,
            "time_window_hours": self.time_window_hours,
            "total_events": self.qradar_item.total_events,
            "compliance_framework": self.framework,
        }
        file_handle.write(json.dumps(metadata) + "\n")

    def _write_compliance_summary(self, file_handle, compliance_results: Dict[str, Any]) -> None:
        """Write compliance summary to evidence file."""
        summary = {
            "type": "compliance_summary",
            "results": compliance_results["overall"],
            "total_events": self.qradar_item.total_events,
            "unique_categories": self.qradar_item.unique_categories,
            "unique_log_sources": self.qradar_item.unique_log_sources,
            "high_severity_count": self.qradar_item.high_severity_count,
            "critical_severity_count": self.qradar_item.critical_severity_count,
        }
        file_handle.write(json.dumps(summary) + "\n")

    def _write_event_statistics(self, file_handle) -> None:
        """Write event statistics to evidence file."""
        statistics = {
            "type": "event_statistics",
            "severity_distribution": self.qradar_item.severity_distribution,
            "category_distribution": self.qradar_item.category_distribution,
            "categories": self.qradar_item.categories,
            "log_sources": self.qradar_item.log_sources,
        }
        file_handle.write(json.dumps(statistics) + "\n")

    def _write_sample_events(self, file_handle) -> None:
        """Write sample events to evidence file (limited to first 100)."""
        sample_size = min(100, len(self.qradar_item.events))
        for event in self.qradar_item.events[:sample_size]:
            event_record = {"type": "sample_event", "event_data": event}
            file_handle.write(json.dumps(event_record, default=str) + "\n")

    def _create_ssp_attachment_with_evidence(self, evidence_file_path: str) -> None:
        """
        Create SSP attachment with QRadar compliance evidence.

        :param str evidence_file_path: Path to evidence file
        """
        try:
            date_str = datetime.now().strftime("%Y%m%d")
            file_name_pattern = f"qradar_compliance_{date_str}"

            # Check if evidence for today already exists using base class method
            if self.check_for_existing_evidence(file_name_pattern):
                logger.info(
                    "Evidence file for QRadar compliance already exists for today. "
                    "Skipping upload to avoid duplicates."
                )
                return

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"qradar_compliance_{timestamp}.jsonl.gz"

            # Read the compressed file
            with open(evidence_file_path, "rb") as f:
                file_data = f.read()

            # Upload file to RegScale
            success = File.upload_file_to_regscale(
                file_name=file_name,
                parent_id=self.plan_id,
                parent_module="securityplans",
                api=self.api,
                file_data=file_data,
                tags="qradar,siem,compliance,security,monitoring,automated",
            )

            if success:
                logger.info(f"Successfully uploaded QRadar compliance evidence file: {file_name}")
                # Link to controls if specified
                if self.evidence_control_ids:
                    # Note: SSP attachments don't have IDs returned by upload_file_to_regscale
                    # This would need to be implemented if attachment-to-control linking is required
                    logger.info(f"Evidence uploaded for controls: {', '.join(self.evidence_control_ids)}")
            else:
                logger.error("Failed to upload QRadar compliance evidence file")

        except Exception as e:
            logger.error(f"Failed to create SSP attachment: {e}", exc_info=True)

    def _link_evidence_to_controls(self, evidence_id: int, is_attachment: bool = False) -> None:
        """
        Link evidence to specified control IDs.

        :param int evidence_id: Evidence or attachment ID
        :param bool is_attachment: True if linking attachment, False for evidence record
        """
        try:
            for control_id in self.evidence_control_ids:
                if is_attachment:
                    self.api.link_ssp_attachment_to_control(self.plan_id, evidence_id, control_id)
                else:
                    self.api.link_evidence_to_control(evidence_id, control_id)
                logger.info(f"Linked evidence {evidence_id} to control {control_id}")
        except Exception as e:
            logger.error(f"Failed to link evidence to controls: {e}", exc_info=True)
