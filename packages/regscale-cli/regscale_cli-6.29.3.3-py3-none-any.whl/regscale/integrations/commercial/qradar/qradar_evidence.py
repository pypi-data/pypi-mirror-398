"""QRadar evidence collection and upload module."""

import gzip
import json
import logging
import os
import tempfile
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from regscale.models.regscale_models.file import File
from regscale.models.regscale_models.evidence_mapping import EvidenceMapping
from regscale.models.integration_models.qradar_models.event import QRadarEvent

logger = logging.getLogger("regscale")


class QRadarEvidenceCollector:
    """
    Collect and upload QRadar security event evidence to RegScale.

    This class creates JSONL.GZ evidence files containing QRadar security events
    and uploads them as SSP attachments or Evidence records in RegScale.

    Follows the AWS integration pattern for evidence collection.
    """

    def __init__(
        self,
        plan_id: int,
        api: Any,  # RegScale API instance from Application
        events: List[QRadarEvent],
        control_ids: Optional[List[int]] = None,
        create_ssp_attachment: bool = True,
        compliance_results: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize QRadar evidence collector.

        Args:
            plan_id: RegScale Security Plan ID
            api: RegScale API client instance from Application().api
            events: List of QRadarEvent objects to include in evidence
            control_ids: Optional list of control IDs to link evidence to
            create_ssp_attachment: If True, create SSP attachment (default: True)
            compliance_results: Optional compliance assessment results to include
        """
        self.plan_id = plan_id
        self.api = api
        self.events = events
        self.control_ids = control_ids or []
        self.create_ssp_attachment = create_ssp_attachment
        self.compliance_results = compliance_results

    def collect_and_upload_evidence(self) -> bool:
        """
        Collect QRadar events and upload as evidence file.

        Creates both SSP attachment (for easy viewing in security plan)
        and Evidence record (for control linking and evidence tracking).

        Returns:
            bool: True if evidence was successfully uploaded
        """
        if not self.events:
            logger.info("No QRadar events to include in evidence file")
            return False

        try:
            # Create evidence file
            evidence_file_path = self._create_evidence_file()

            # Create both SSP attachment and Evidence record
            # SSP attachment provides easy viewing in security plan
            # Evidence record enables control linking and evidence tracking
            ssp_success = self._create_ssp_attachment_with_evidence(evidence_file_path)
            evidence_success = self._create_evidence_record_with_file(evidence_file_path)

            # Evidence record is critical for control linking
            if ssp_success and evidence_success:
                logger.info("Successfully created both SSP attachment and Evidence record")
            elif evidence_success:
                logger.warning("Created Evidence record but SSP attachment failed")
            elif ssp_success:
                logger.warning("Created SSP attachment but Evidence record failed")
            else:
                logger.error("Failed to create both SSP attachment and Evidence record")

            # Clean up temporary file
            if os.path.exists(evidence_file_path):
                os.remove(evidence_file_path)
                logger.debug("Cleaned up temporary evidence file: %s", evidence_file_path)

            # Return true if Evidence record was created (critical for control linking)
            return evidence_success

        except Exception as exc:
            logger.error("Failed to collect and upload QRadar evidence: %s", exc)
            logger.debug("Failed to collect and upload QRadar evidence: %s", exc, exc_info=True)
            return False

    def _create_evidence_file(self) -> str:
        """
        Create JSONL.GZ evidence file with QRadar security events.

        Returns:
            str: Path to created evidence file
        """
        evidence_file = self._get_evidence_file_path()

        try:
            with gzip.open(evidence_file, "wt", encoding="utf-8") as f:
                # Write metadata record
                self._write_metadata(f)

                # Write summary record
                self._write_event_summary(f)

                # Write compliance assessment results if available
                if self.compliance_results:
                    self._write_compliance_results(f)

                # Write individual event records
                self._write_event_records(f)

            logger.info("Created QRadar evidence file: %s (%d events)", evidence_file, len(self.events))
            return evidence_file

        except Exception as exc:
            logger.error("Failed to create QRadar evidence file: %s", exc)
            logger.debug("Failed to create QRadar evidence file: %s", exc, exc_info=True)
            raise

    def _get_evidence_file_path(self) -> str:
        """Generate evidence file path with timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return os.path.join(tempfile.gettempdir(), f"qradar_evidence_{timestamp}.jsonl.gz")

    def _write_metadata(self, file_handle) -> None:
        """Write metadata record to evidence file."""
        metadata = {
            "type": "metadata",
            "timestamp": datetime.now().isoformat(),
            "source": "QRadar SIEM",
            "security_plan_id": self.plan_id,
            "event_count": len(self.events),
            "evidence_framework": "Security Event Logging",
        }

        # Include compliance assessment info if available
        if self.compliance_results:
            metadata["includes_compliance_assessment"] = True
            metadata["compliance_framework"] = self.compliance_results.get("framework", "NIST800-53R5")

        file_handle.write(json.dumps(metadata) + "\n")

    def _write_event_summary(self, file_handle) -> None:
        """Write event summary statistics to evidence file."""
        # Calculate summary statistics
        severity_counts: Dict[int, int] = {}
        category_counts: Dict[str, int] = {}
        source_ips: set[str] = set()
        log_sources: set[str] = set()

        for event in self.events:
            # Count severity levels
            severity = event.get_severity_value()
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

            # Count categories
            category = event.category or "Unknown"
            category_counts[category] = category_counts.get(category, 0) + 1

            # Track unique source IPs
            if event.source_ip:
                source_ips.add(event.source_ip)

            # Track unique log sources
            if event.log_source:
                log_sources.add(event.log_source)

        summary = {
            "type": "event_summary",
            "total_events": len(self.events),
            "severity_distribution": severity_counts,
            "category_distribution": category_counts,
            "unique_source_ips": len(source_ips),
            "unique_log_sources": len(log_sources),
            "log_sources": sorted(log_sources),
        }
        file_handle.write(json.dumps(summary) + "\n")

    def _write_compliance_results(self, file_handle) -> None:
        """Write compliance assessment results to evidence file."""
        if not self.compliance_results:
            return

        # Extract compliance assessment data
        overall_results = self.compliance_results.get("overall", {})
        passed_controls = [ctrl for ctrl, result in overall_results.items() if result == "PASS"]
        failed_controls = [ctrl for ctrl, result in overall_results.items() if result == "FAIL"]

        compliance_record = {
            "type": "compliance_assessment",
            "framework": self.compliance_results.get("framework", "NIST800-53R5"),
            "assessment_timestamp": datetime.now().isoformat(),
            "total_controls_assessed": len(overall_results),
            "controls_passed": len(passed_controls),
            "controls_failed": len(failed_controls),
            "passing_controls": passed_controls,
            "failing_controls": failed_controls,
            "detailed_results": overall_results,
        }
        file_handle.write(json.dumps(compliance_record) + "\n")
        logger.debug(f"Wrote compliance results: {len(passed_controls)} passed, {len(failed_controls)} failed")

    def _write_event_records(self, file_handle) -> None:
        """Write individual event records to evidence file."""
        for event in self.events:
            event_record = self._build_event_record(event)
            file_handle.write(json.dumps(event_record, default=str) + "\n")

    def _build_event_record(self, event: QRadarEvent) -> Dict[str, Any]:
        """
        Build event record for evidence file.

        Args:
            event: QRadarEvent object

        Returns:
            Dict containing event data
        """
        record = {
            "type": "security_event",
            "event_name": event.event_name,
            "log_source": event.log_source,
            "category": event.category,
            "severity": event.get_severity_value(),
            "magnitude": event.magnitude,
            "event_count": event.event_count,
            "source_ip": event.source_ip,
            "source_port": event.source_port,
            "destination_ip": event.dest_ip,
            "destination_port": event.dest_port,
            "username": event.username,
            "event_time": event.event_time,
        }

        # Include any extra fields from Pydantic model
        if hasattr(event, "__pydantic_extra__") and event.__pydantic_extra__:
            # Type ignore since we're adding a dict value which is valid for JSON serialization
            record["additional_fields"] = event.__pydantic_extra__  # type: ignore[assignment]

        return record

    def _create_ssp_attachment_with_evidence(self, evidence_file_path: str) -> bool:
        """
        Create SSP attachment with QRadar evidence.

        Args:
            evidence_file_path: Path to evidence file

        Returns:
            bool: True if upload was successful
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"qradar_evidence_{timestamp}.jsonl.gz"

            # Read the compressed file
            with open(evidence_file_path, "rb") as f:
                file_data = f.read()

            # Upload file to RegScale
            result = File.upload_file_to_regscale(
                file_name=file_name,
                parent_id=self.plan_id,
                parent_module="securityplans",
                api=self.api,
                file_data=file_data,
                tags="qradar,siem,security,events,compliance,automated",
            )

            success = bool(result)
            if success:
                logger.info("Successfully uploaded QRadar evidence file: %s", file_name)
                # Note: SSP attachments don't return IDs from upload_file_to_regscale
                # Control linking would need additional implementation
            else:
                logger.error("Failed to upload QRadar evidence file")

            return success

        except Exception as exc:
            logger.error("Failed to create SSP attachment: %s", exc)
            logger.debug("Failed to create SSP attachment: %s", exc, exc_info=True)
            return False

    def _create_evidence_record_with_file(self, evidence_file_path: str) -> bool:
        """
        Create Evidence record and upload file.

        Args:
            evidence_file_path: Path to evidence file

        Returns:
            bool: True if creation was successful
        """
        try:
            from regscale.models.regscale_models import Evidence
            from datetime import timedelta

            # Create Evidence record
            timestamp_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            evidence_title = f"QRadar Security Events - {timestamp_str}"

            evidence_description = (
                f"QRadar SIEM security events collected on {timestamp_str}. "
                f"Contains {len(self.events)} security events from QRadar. "
                "Evidence includes event details, severity information, and source/destination data."
            )

            # Calculate due date (30 days from now for monthly evidence collection)
            due_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

            evidence_record = Evidence(
                title=evidence_title,
                description=evidence_description,
                status="Active",
                updateFrequency=30,
                dueDate=due_date,
            )

            created_evidence = evidence_record.create()
            logger.info("Created Evidence record: %s (ID: %s)", evidence_title, created_evidence.id)

            # Upload file to evidence record
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"qradar_evidence_{timestamp}.jsonl.gz"

            with open(evidence_file_path, "rb") as f:
                file_data = f.read()

            result = File.upload_file_to_regscale(
                file_name=file_name,
                parent_id=created_evidence.id,
                parent_module="evidence",
                api=self.api,
                file_data=file_data,
                tags="qradar,siem,security,events,compliance,automated",
            )

            file_success = bool(result)
            if file_success:
                logger.info("Successfully uploaded file to Evidence record %d", created_evidence.id)

                # Link evidence to SSP for Evidence Freshness and SSP statistics
                self._link_evidence_to_ssp(created_evidence.id)

                # Link evidence to controls
                if self.control_ids:
                    self._link_evidence_to_controls(created_evidence.id)
            else:
                logger.error("Failed to upload file to Evidence record %d", created_evidence.id)

            return file_success

        except Exception as exc:
            logger.error("Failed to create Evidence record: %s", exc)
            logger.debug("Failed to create Evidence record: %s", exc, exc_info=True)
            return False

    def _link_evidence_to_ssp(self, evidence_id: int) -> None:
        """
        Link evidence record to the security plan.

        This creates an EvidenceMapping to link the evidence to the SSP, which is
        required for the evidence to appear in:
        - Evidence Freshness dashboard
        - SSP top-level aggregation statistics
        - SSP Evidence tab

        Args:
            evidence_id: Evidence record ID
        """
        try:
            mapping = EvidenceMapping(evidenceID=evidence_id, mappedID=self.plan_id, mappingType="securityplans")
            mapping.create()
            logger.info("Linked evidence %d to SSP %d", evidence_id, self.plan_id)
        except Exception as exc:
            logger.warning("Failed to link evidence %d to SSP %d: %s", evidence_id, self.plan_id, exc)

    def _link_evidence_to_controls(self, evidence_id: int) -> None:
        """
        Link evidence record to specified control implementation IDs.

        Uses EvidenceMapping with mappingType="controls" to link evidence to
        control implementations, following the AWS Audit Manager pattern.

        Args:
            evidence_id: Evidence record ID
        """
        try:
            for control_id in self.control_ids:
                try:
                    # Create evidence mapping to control implementation
                    # Note: control_id here is actually the control implementation ID from get_control_implementation_ids()
                    mapping = EvidenceMapping(evidenceID=evidence_id, mappedID=control_id, mappingType="controls")
                    created_mapping = mapping.create()

                    if created_mapping and created_mapping.id:
                        logger.info("Linked evidence %d to control implementation %d", evidence_id, control_id)
                    else:
                        logger.warning(
                            "Failed to create evidence mapping for control %d: mapping.create() returned %s",
                            control_id,
                            created_mapping,
                        )
                except Exception as exc:
                    logger.warning("Failed to link evidence %d to control %d: %s", evidence_id, control_id, exc)
        except Exception as exc:
            logger.error("Error linking evidence to controls: %s", exc)
            logger.debug("Error linking evidence to controls: %s", exc, exc_info=True)
