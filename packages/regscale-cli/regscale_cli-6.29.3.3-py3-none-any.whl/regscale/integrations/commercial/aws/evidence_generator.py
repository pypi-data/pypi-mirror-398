#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AWS Evidence Generator for SSP compliance documentation"""

import gzip
import json
import logging
from datetime import datetime, timedelta, timezone
from io import BytesIO
from typing import List, Optional

from regscale.core.app.api import Api
from regscale.models.regscale_models.evidence import Evidence
from regscale.models.regscale_models.evidence_mapping import EvidenceMapping
from regscale.models.regscale_models.file import File

logger = logging.getLogger("regscale")


class AWSEvidenceGenerator:
    """Generate compliance evidence from AWS security findings"""

    def __init__(self, api: Api, ssp_id: Optional[int] = None):
        """
        Initialize evidence generator

        :param Api api: RegScale API instance
        :param Optional[int] ssp_id: Security Plan ID to link evidence
        """
        self.api = api
        self.ssp_id = ssp_id

    def create_evidence_from_scan(
        self,
        service_name: str,
        findings: List[dict],
        ocsf_data: Optional[List[dict]] = None,
        update_frequency: int = 30,
        control_ids: Optional[List[int]] = None,
    ) -> Optional[Evidence]:
        """
        Create evidence record from AWS service scan

        :param str service_name: AWS service name (GuardDuty, SecurityHub, etc.)
        :param List[dict] findings: List of AWS findings (native format)
        :param Optional[List[dict]] ocsf_data: OCSF-formatted findings
        :param int update_frequency: Evidence update frequency in days (default: 30)
        :param Optional[List[int]] control_ids: Control IDs to link evidence
        :return: Created Evidence object or None
        :rtype: Optional[Evidence]
        """
        if not findings:
            logger.warning("No findings provided, skipping evidence creation")
            return None

        # Generate evidence title with timestamp
        scan_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        title = f"{service_name} Findings Scan - {scan_timestamp}"

        # Create description with finding summary
        total_findings = len(findings)
        severity_counts = self._count_severities(findings, service_name)
        description = self._build_evidence_description(service_name, total_findings, severity_counts, ocsf_data)

        # Calculate due date based on update frequency
        due_date = (datetime.now() + timedelta(days=update_frequency)).isoformat()

        try:
            # Create evidence record
            evidence = Evidence(
                title=title,
                description=description,
                status="Collected",
                updateFrequency=update_frequency,
                dueDate=due_date,
            )

            # Create evidence in RegScale
            created_evidence = evidence.create()
            if not created_evidence or not created_evidence.id:
                logger.error("Failed to create evidence record")
                return None

            logger.info("Created evidence record %s: %s", created_evidence.id, title)

            # Upload findings as file attachments
            self._attach_findings_files(
                created_evidence.id,
                findings,
                ocsf_data,
                service_name,
            )

            # Link evidence to SSP if provided
            if self.ssp_id:
                self._link_to_ssp(created_evidence.id)

            # Link evidence to specific controls if provided
            if control_ids:
                self._link_to_controls(created_evidence.id, control_ids)

            return created_evidence

        except Exception as ex:
            logger.error("Failed to create evidence: %s", ex)
            return None

    def _count_severities(self, findings: List[dict], service_name: str) -> dict:
        """
        Count findings by severity level

        :param List[dict] findings: AWS findings
        :param str service_name: AWS service name for severity field mapping
        :return: Dictionary with severity counts
        :rtype: dict
        """
        severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}

        for finding in findings:
            # Map service-specific severity fields
            if service_name == "GuardDuty":
                severity = finding.get("Severity", 0)
                # GuardDuty uses numeric severity (1.0-8.9)
                if severity >= 7.0:
                    severity_counts["HIGH"] += 1
                elif severity >= 4.0:
                    severity_counts["MEDIUM"] += 1
                else:
                    severity_counts["LOW"] += 1

            elif service_name == "SecurityHub":
                # Security Hub uses normalized severity
                severity_label = finding.get("Severity", {}).get("Label", "INFO")
                severity_counts[severity_label] = severity_counts.get(severity_label, 0) + 1

            elif service_name == "CloudTrail":
                # CloudTrail events don't have severity, count as INFO
                severity_counts["INFO"] += 1

        return severity_counts

    def _build_evidence_description(
        self,
        service_name: str,
        total_findings: int,
        severity_counts: dict,
        ocsf_data: Optional[List[dict]],
    ) -> str:
        """
        Build evidence description with finding summary

        :param str service_name: AWS service name
        :param int total_findings: Total number of findings
        :param dict severity_counts: Severity breakdown
        :param Optional[List[dict]] ocsf_data: OCSF-formatted findings
        :return: Evidence description text
        :rtype: str
        """
        description_parts = [
            f"Automated evidence collection from AWS {service_name}.",
            f"Total findings: {total_findings}",
            "",
            "Severity Breakdown:",
        ]

        for severity, count in severity_counts.items():
            if count > 0:
                description_parts.append(f"  - {severity}: {count}")

        description_parts.extend(["", "Files attached:"])
        description_parts.append(f"  - {service_name.lower()}_findings_native.jsonl.gz (AWS native format, compressed)")

        if ocsf_data:
            description_parts.append(
                f"  - {service_name.lower()}_findings_ocsf.jsonl.gz (OCSF normalized format, compressed)"
            )

        return "\n".join(description_parts)

    def _attach_findings_files(
        self,
        evidence_id: int,
        findings: List[dict],
        ocsf_data: Optional[List[dict]],
        service_name: str,
    ) -> None:
        """
        Upload findings as file attachments to evidence

        :param int evidence_id: Evidence record ID
        :param List[dict] findings: Native AWS findings
        :param Optional[List[dict]] ocsf_data: OCSF-formatted findings
        :param str service_name: AWS service name
        """
        # Upload native findings as compressed JSONL
        native_jsonl = "\n".join([json.dumps(f) for f in findings])

        # Compress the JSONL data
        compressed_buffer = BytesIO()
        with gzip.open(compressed_buffer, "wt", encoding="utf-8", compresslevel=9) as gz_file:
            gz_file.write(native_jsonl)

        compressed_data = compressed_buffer.getvalue()

        success = File.upload_file_to_regscale(
            file_name=f"{service_name.lower()}_findings_native.jsonl.gz",
            parent_id=evidence_id,
            parent_module="evidence",
            api=self.api,
            file_data=compressed_data,
            tags=f"aws,{service_name.lower()},native,compressed",
        )

        if success:
            logger.info("Uploaded compressed native findings file for evidence %s", evidence_id)
        else:
            logger.warning("Failed to upload compressed native findings file for evidence %s", evidence_id)

        # Upload OCSF findings if available
        if ocsf_data:
            ocsf_jsonl = "\n".join([json.dumps(f) for f in ocsf_data])

            # Compress the OCSF JSONL data
            compressed_buffer = BytesIO()
            with gzip.open(compressed_buffer, "wt", encoding="utf-8", compresslevel=9) as gz_file:
                gz_file.write(ocsf_jsonl)

            compressed_data = compressed_buffer.getvalue()

            success = File.upload_file_to_regscale(
                file_name=f"{service_name.lower()}_findings_ocsf.jsonl.gz",
                parent_id=evidence_id,
                parent_module="evidence",
                api=self.api,
                file_data=compressed_data,
                tags=f"aws,{service_name.lower()},ocsf,compressed",
            )

            if success:
                logger.info("Uploaded compressed OCSF findings file for evidence %s", evidence_id)
            else:
                logger.warning("Failed to upload compressed OCSF findings file for evidence %s", evidence_id)

    def _link_to_ssp(self, evidence_id: int) -> None:
        """
        Link evidence to Security Plan

        :param int evidence_id: Evidence record ID
        """
        if not self.ssp_id:
            return

        mapping = EvidenceMapping(
            evidenceID=evidence_id,
            mappedID=self.ssp_id,
            mappingType="securityplans",
        )

        try:
            mapping.create()
            logger.info("Linked evidence %s to SSP %s", evidence_id, self.ssp_id)
        except Exception as ex:
            logger.warning("Failed to link evidence to SSP: %s", ex)

    def _link_to_controls(self, evidence_id: int, control_ids: List[int]) -> None:
        """
        Link evidence to specific security controls

        :param int evidence_id: Evidence record ID
        :param List[int] control_ids: List of control IDs
        """
        for control_id in control_ids:
            mapping = EvidenceMapping(
                evidenceID=evidence_id,
                mappedID=control_id,
                mappingType="securityControlAssessments",
            )

            try:
                mapping.create()
                logger.info("Linked evidence %s to control %s", evidence_id, control_id)
            except Exception as ex:
                logger.warning("Failed to link evidence to control %s: %s", control_id, ex)
