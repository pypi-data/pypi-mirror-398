#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AWS GuardDuty Evidence Integration for RegScale CLI."""

import gzip
import json
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from io import BytesIO
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

from regscale.core.app.api import Api
from regscale.core.app.utils.app_utils import get_current_datetime
from regscale.integrations.commercial.aws.guardduty_control_mappings import GuardDutyControlMapper
from regscale.integrations.compliance_integration import ComplianceIntegration, ComplianceItem
from regscale.integrations.scanner_integration import IntegrationFinding
from regscale.models.regscale_models.evidence import Evidence
from regscale.models.regscale_models.evidence_mapping import EvidenceMapping
from regscale.models.regscale_models.file import File

logger = logging.getLogger("regscale")

GUARDDUTY_CACHE_FILE = os.path.join("artifacts", "aws", "guardduty_data.json")
CACHE_TTL_SECONDS = 4 * 60 * 60

HTML_STRONG_OPEN = "<strong>"
HTML_STRONG_CLOSE = "</strong>"
HTML_P_OPEN = "<p>"
HTML_P_CLOSE = "</p>"
HTML_UL_OPEN = "<ul>"
HTML_UL_CLOSE = "</ul>"
HTML_LI_OPEN = "<li>"
HTML_LI_CLOSE = "</li>"
HTML_H2_OPEN = "<h2>"
HTML_H2_CLOSE = "</h2>"
HTML_H3_OPEN = "<h3>"
HTML_H3_CLOSE = "</h3>"
HTML_BR = "<br>"


@dataclass
class GuardDutyEvidenceConfig:
    """Configuration for AWS GuardDuty evidence collection."""

    plan_id: int
    region: str = "us-east-1"
    framework: str = "NIST800-53R5"
    create_issues: bool = True
    update_control_status: bool = True
    create_poams: bool = False
    create_vulnerabilities: bool = True
    parent_module: str = "securityplans"
    collect_evidence: bool = False
    evidence_as_attachments: bool = True
    evidence_control_ids: Optional[List[str]] = None
    evidence_frequency: int = 30
    force_refresh: bool = False
    account_id: Optional[str] = None
    tags: Optional[Dict[str, str]] = None
    profile: Optional[str] = None
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_session_token: Optional[str] = None


class GuardDutyComplianceItem(ComplianceItem):
    """
    Compliance item representing a GuardDuty assessment for a specific control.

    Maps GuardDuty detector and finding data to compliance control requirements.
    """

    def __init__(self, control_id: str, guardduty_data: Dict[str, Any], control_mapper: GuardDutyControlMapper):
        """
        Initialize GuardDuty compliance item.

        :param str control_id: The control ID being assessed (e.g., 'SI-4', 'IR-4')
        :param Dict[str, Any] guardduty_data: Complete GuardDuty data including detectors and findings
        :param GuardDutyControlMapper control_mapper: Control mapper for compliance assessment
        """
        self._control_id = control_id
        self.guardduty_data = guardduty_data
        self.control_mapper = control_mapper

        # Assess compliance for this specific control
        all_results = control_mapper.assess_guardduty_compliance(guardduty_data)
        self._compliance_result = all_results.get(control_id, "PASS")

        # Extract detector and finding statistics
        self.detectors = guardduty_data.get("Detectors", [])
        self.findings = guardduty_data.get("Findings", [])

        # Count findings by severity
        self.high_severity_findings = self._count_findings_by_severity("HIGH")
        self.critical_severity_findings = self._count_findings_by_severity("CRITICAL")
        self.medium_severity_findings = self._count_findings_by_severity("MEDIUM")
        self.low_severity_findings = self._count_findings_by_severity("LOW")

        # Get the account ID from the first detector if available
        self._account_id = self._extract_account_id()

    def _count_findings_by_severity(self, severity: str) -> int:
        """Count findings matching the specified severity level."""
        count = 0
        for finding in self.findings:
            finding_severity = self.control_mapper._get_severity_level(finding.get("Severity", 0))
            if finding_severity == severity:
                count += 1
        return count

    def _extract_account_id(self) -> str:
        """Extract AWS account ID from detector or finding data."""
        if self.detectors:
            # Try to get from first detector
            detector = self.detectors[0]
            if isinstance(detector, dict):
                return detector.get("AccountId", "")

        if self.findings:
            # Try to get from first finding
            finding = self.findings[0]
            if isinstance(finding, dict):
                return finding.get("AccountId", "")

        return ""

    @property
    def resource_id(self) -> str:
        """Unique identifier for the GuardDuty service in this account/region."""
        if self._account_id:
            return f"guardduty-{self._account_id}"
        return "guardduty-service"

    @property
    def resource_name(self) -> str:
        """Human-readable name of the GuardDuty service."""
        if self._account_id:
            return f"AWS GuardDuty - Account {self._account_id}"
        return "AWS GuardDuty Service"

    @property
    def control_id(self) -> str:
        """Control identifier (e.g., SI-4, IR-4)."""
        return self._control_id

    @property
    def compliance_result(self) -> str:
        """Result of compliance check (PASS, FAIL)."""
        return self._compliance_result

    @property
    def severity(self) -> Optional[str]:
        """Severity level based on the control and findings."""
        if self.compliance_result == "PASS":
            return None

        # Determine severity based on control and findings
        if self._control_id == "IR-4":
            # IR-4 fails if there are high/critical severity findings
            if self.critical_severity_findings > 0:
                return "CRITICAL"
            elif self.high_severity_findings > 0:
                return "HIGH"
            else:
                return "MEDIUM"
        elif self._control_id == "SI-4":
            # SI-4 fails if detector is disabled
            return "HIGH"
        elif self._control_id in ["IR-5", "SI-3", "RA-5"]:
            # Other controls have medium severity for failures
            return "MEDIUM"

        return "MEDIUM"

    @property
    def description(self) -> str:
        """Detailed description of the GuardDuty compliance assessment."""
        desc_parts = self._build_assessment_header()
        desc_parts.extend(self._build_detector_summary())
        desc_parts.extend(self._build_findings_summary())
        desc_parts.extend(self._build_control_assessment())

        if self.compliance_result == "FAIL":
            desc_parts.extend(self._build_remediation_guidance())

        return "\n".join(desc_parts)

    def _build_assessment_header(self) -> List[str]:
        """Build the assessment header section."""
        control_desc = self.control_mapper.get_control_description(self._control_id)
        return [
            f"{HTML_H3_OPEN}GuardDuty Compliance Assessment{HTML_H3_CLOSE}",
            HTML_P_OPEN,
            f"{HTML_STRONG_OPEN}Control:{HTML_STRONG_CLOSE} {self._control_id} - {control_desc}{HTML_BR}",
            f"{HTML_STRONG_OPEN}Result:{HTML_STRONG_CLOSE} {self._compliance_result}{HTML_BR}",
            f"{HTML_STRONG_OPEN}Account:{HTML_STRONG_CLOSE} {self._account_id or 'N/A'}",
            HTML_P_CLOSE,
        ]

    def _build_detector_summary(self) -> List[str]:
        """Build detector status summary."""
        enabled_count = sum(1 for d in self.detectors if d.get("Status") == "ENABLED")
        disabled_count = len(self.detectors) - enabled_count

        return [
            f"{HTML_H3_OPEN}Detector Status{HTML_H3_CLOSE}",
            HTML_UL_OPEN,
            f"{HTML_LI_OPEN}Total Detectors: {len(self.detectors)}{HTML_LI_CLOSE}",
            f"{HTML_LI_OPEN}Enabled: {enabled_count}{HTML_LI_CLOSE}",
            f"{HTML_LI_OPEN}Disabled/Suspended: {disabled_count}{HTML_LI_CLOSE}",
            HTML_UL_CLOSE,
        ]

    def _build_findings_summary(self) -> List[str]:
        """Build findings summary."""
        total_findings = len(self.findings)

        return [
            f"{HTML_H3_OPEN}Findings Summary{HTML_H3_CLOSE}",
            HTML_UL_OPEN,
            f"{HTML_LI_OPEN}Total Findings: {total_findings}{HTML_LI_CLOSE}",
            f"{HTML_LI_OPEN}Critical: {self.critical_severity_findings}{HTML_LI_CLOSE}",
            f"{HTML_LI_OPEN}High: {self.high_severity_findings}{HTML_LI_CLOSE}",
            f"{HTML_LI_OPEN}Medium: {self.medium_severity_findings}{HTML_LI_CLOSE}",
            f"{HTML_LI_OPEN}Low: {self.low_severity_findings}{HTML_LI_CLOSE}",
            HTML_UL_CLOSE,
        ]

    def _build_control_assessment(self) -> List[str]:
        """Build control-specific assessment details."""
        control_mapping = self.control_mapper.mappings.get(self._control_id, {})
        checks = control_mapping.get("checks", {})

        section_parts = [
            f"{HTML_H3_OPEN}Control Assessment Details{HTML_H3_CLOSE}",
            HTML_UL_OPEN,
        ]

        for check_name, check_info in checks.items():
            if self.compliance_result == "PASS":
                criteria = check_info.get("pass_criteria", "")
            else:
                criteria = check_info.get("fail_criteria", "")
            section_parts.append(f"{HTML_LI_OPEN}{criteria}{HTML_LI_CLOSE}")

        section_parts.append(HTML_UL_CLOSE)
        return section_parts

    def _build_remediation_guidance(self) -> List[str]:
        """Build remediation guidance for failed controls."""
        section_parts = [
            f"{HTML_H3_OPEN}Remediation Guidance{HTML_H3_CLOSE}",
            HTML_UL_OPEN,
        ]

        if self._control_id == "SI-4":
            section_parts.append(f"{HTML_LI_OPEN}Enable all GuardDuty detectors in the region{HTML_LI_CLOSE}")
            section_parts.append(f"{HTML_LI_OPEN}Ensure detectors are actively monitoring{HTML_LI_CLOSE}")
        elif self._control_id == "IR-4":
            section_parts.append(
                f"{HTML_LI_OPEN}Review and remediate all high and critical severity findings{HTML_LI_CLOSE}"
            )
            section_parts.append(f"{HTML_LI_OPEN}Integrate GuardDuty with incident response workflow{HTML_LI_CLOSE}")
        elif self._control_id == "IR-5":
            section_parts.append(
                f"{HTML_LI_OPEN}Implement systematic tracking of all GuardDuty findings{HTML_LI_CLOSE}"
            )
            section_parts.append(f"{HTML_LI_OPEN}Document incident response for each finding{HTML_LI_CLOSE}")
        elif self._control_id == "SI-3":
            section_parts.append(f"{HTML_LI_OPEN}Enable malware protection features in GuardDuty{HTML_LI_CLOSE}")
            section_parts.append(f"{HTML_LI_OPEN}Monitor and respond to malware-related findings{HTML_LI_CLOSE}")
        elif self._control_id == "RA-5":
            section_parts.append(f"{HTML_LI_OPEN}Enable GuardDuty threat intelligence feeds{HTML_LI_CLOSE}")
            section_parts.append(f"{HTML_LI_OPEN}Keep threat intelligence sources current{HTML_LI_CLOSE}")

        section_parts.append(HTML_UL_CLOSE)
        return section_parts

    @property
    def framework(self) -> str:
        """Compliance framework used for assessment."""
        return self.control_mapper.framework


class AWSGuardDutyEvidenceIntegration(ComplianceIntegration):
    """Process AWS GuardDuty findings and create assessments/issues in RegScale."""

    def __init__(self, config: GuardDutyEvidenceConfig):
        """
        Initialize AWS GuardDuty evidence integration.

        :param GuardDutyEvidenceConfig config: Configuration object containing all parameters
        """
        super().__init__(
            plan_id=config.plan_id,
            framework=config.framework,
            create_issues=config.create_issues,
            update_control_status=config.update_control_status,
            create_poams=config.create_poams,
            parent_module=config.parent_module,
        )

        # Initialize API for file operations
        self.api = Api()

        self.region = config.region
        self.title = "AWS GuardDuty"
        self.framework = config.framework
        self.create_issues = config.create_issues
        self.create_vulnerabilities = config.create_vulnerabilities
        self.collect_evidence = config.collect_evidence
        self.evidence_as_attachments = config.evidence_as_attachments
        self.evidence_control_ids = config.evidence_control_ids
        self.evidence_frequency = config.evidence_frequency
        self.force_refresh = config.force_refresh
        self.account_id = config.account_id
        self.tags = config.tags or {}

        self.control_mapper = GuardDutyControlMapper(framework=config.framework)

        profile = config.profile
        aws_access_key_id = config.aws_access_key_id
        aws_secret_access_key = config.aws_secret_access_key
        aws_session_token = config.aws_session_token

        if aws_access_key_id and aws_secret_access_key:
            logger.info("Initializing AWS GuardDuty client with explicit credentials")
            self.session = boto3.Session(
                region_name=config.region,
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                aws_session_token=aws_session_token,
            )
        else:
            logger.info(f"Initializing AWS GuardDuty client with profile: {profile if profile else 'default'}")
            self.session = boto3.Session(profile_name=profile, region_name=config.region)

        try:
            self.client = self.session.client("guardduty")
            logger.info("Successfully created AWS GuardDuty client")
        except Exception as e:
            logger.error(f"Failed to create AWS GuardDuty client: {e}")
            raise

        self.raw_guardduty_data: Dict[str, Any] = {}
        self.findings_with_cves: List[Dict[str, Any]] = []
        self.findings_without_cves: List[Dict[str, Any]] = []

    def fetch_compliance_data(self) -> List[Dict[str, Any]]:
        """
        Fetch GuardDuty compliance data.

        Returns the raw GuardDuty data which will be used to create compliance items
        for each control that GuardDuty maps to.

        :return: List containing raw GuardDuty data
        :rtype: List[Dict[str, Any]]
        """
        self.fetch_guardduty_data()

        # Return the raw data wrapped in a list
        # We'll create multiple compliance items from this single data set
        return [self.raw_guardduty_data] if self.raw_guardduty_data else []

    def create_compliance_item(self, raw_data: Dict[str, Any]) -> List[ComplianceItem]:
        """
        Create compliance items from GuardDuty data.

        Unlike other integrations that map 1:1 from raw data to compliance items,
        GuardDuty creates multiple compliance items (one per control) from the same data set.

        :param Dict[str, Any] raw_data: Raw GuardDuty data
        :return: List of compliance items for each control
        :rtype: List[ComplianceItem]
        """
        compliance_items = []

        # Get all controls that GuardDuty maps to
        control_results = self.control_mapper.assess_guardduty_compliance(raw_data)

        # Create a compliance item for each control
        for control_id in control_results:
            compliance_item = GuardDutyComplianceItem(
                control_id=control_id, guardduty_data=raw_data, control_mapper=self.control_mapper
            )
            compliance_items.append(compliance_item)

        return compliance_items

    def process_compliance_data(self) -> None:
        """
        Override process_compliance_data to handle GuardDuty's unique pattern.

        GuardDuty creates multiple compliance items from a single data fetch,
        so we need to handle this differently than the base implementation.
        """
        logger.info("Processing GuardDuty compliance data...")

        self._reset_compliance_state()
        # GuardDuty doesn't need control filtering since it maps to specific controls
        # allowed_controls = self._build_allowed_controls_set()
        raw_compliance_data = self.fetch_compliance_data()

        # Process the raw data - GuardDuty returns a list with one item
        for raw_item in raw_compliance_data:
            try:
                # Create multiple compliance items from the single raw data
                compliance_items = self.create_compliance_item(raw_item)

                # Process each compliance item
                for compliance_item in compliance_items:
                    control_id = getattr(compliance_item, "control_id", "")
                    resource_id = getattr(compliance_item, "resource_id", "")

                    if not control_id or not resource_id:
                        continue

                    # Add to collections
                    self.all_compliance_items.append(compliance_item)

                    # Build asset mapping
                    self.asset_compliance_map[compliance_item.resource_id].append(compliance_item)

                    # Categorize by result
                    if compliance_item.compliance_result in self.FAIL_STATUSES:
                        self.failed_compliance_items.append(compliance_item)
                        self.failing_controls[control_id.lower()] = compliance_item
                    else:
                        self.passing_controls[control_id.lower()] = compliance_item

            except Exception as e:
                logger.error(f"Error processing GuardDuty compliance data: {e}")
                continue

        logger.info(
            f"Processed {len(self.all_compliance_items)} compliance items: "
            f"{len(self.passing_controls)} passing controls, "
            f"{len(self.failing_controls)} failing controls"
        )

    def _is_cache_valid(self) -> bool:
        if not os.path.exists(GUARDDUTY_CACHE_FILE):
            return False
        file_age = time.time() - os.path.getmtime(GUARDDUTY_CACHE_FILE)
        is_valid = file_age < CACHE_TTL_SECONDS
        if is_valid:
            logger.info(f"Using cached GuardDuty data (age: {file_age / 3600:.1f} hours)")
        return is_valid

    def _load_cached_data(self) -> Dict[str, Any]:
        try:
            with open(GUARDDUTY_CACHE_FILE, encoding="utf-8") as file:
                data = json.load(file)

            # Validate cache format - must be a dict
            if not isinstance(data, dict):
                logger.warning("Invalid cache format detected (not a dict). Invalidating cache.")
                return {}

            return data
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Error reading cache: {e}")
            return {}

    def _save_to_cache(self, guardduty_data: Dict[str, Any]) -> None:
        try:
            os.makedirs(os.path.dirname(GUARDDUTY_CACHE_FILE), exist_ok=True)
            with open(GUARDDUTY_CACHE_FILE, "w", encoding="utf-8") as file:
                json.dump(guardduty_data, file, indent=2, default=str)
            logger.info(f"Cached GuardDuty data to {GUARDDUTY_CACHE_FILE}")
        except IOError as e:
            logger.warning(f"Error writing cache: {e}")

    def _fetch_fresh_guardduty_data(self) -> Dict[str, Any]:
        logger.info("Fetching GuardDuty data from AWS...")

        from regscale.integrations.commercial.aws.inventory.resources.guardduty import GuardDutyCollector

        collector = GuardDutyCollector(
            session=self.session, region=self.region, account_id=self.account_id, tags=self.tags
        )

        guardduty_data = collector.collect()
        logger.info(
            f"Fetched {len(guardduty_data.get('Detectors', []))} detector(s), "
            f"{len(guardduty_data.get('Findings', []))} finding(s)"
        )

        return guardduty_data

    def fetch_guardduty_data(self) -> Dict[str, Any]:
        if not self.force_refresh and self._is_cache_valid():
            cached_data = self._load_cached_data()
            if cached_data:
                self.raw_guardduty_data = cached_data
                return cached_data

        if self.force_refresh:
            logger.info("Force refresh requested, fetching fresh GuardDuty data...")

        try:
            guardduty_data = self._fetch_fresh_guardduty_data()
            self.raw_guardduty_data = guardduty_data
            self._save_to_cache(guardduty_data)
            return guardduty_data
        except ClientError as e:
            logger.error(f"Error fetching GuardDuty data: {e}")
            return {}

    def _classify_findings(self) -> None:
        """Classify findings into those with CVEs (vulnerabilities) and those without (issues)."""
        findings = self.raw_guardduty_data.get("Findings", [])

        for finding in findings:
            if self.control_mapper.has_cve_reference(finding):
                self.findings_with_cves.append(finding)
            else:
                self.findings_without_cves.append(finding)

        logger.info(
            f"Classified findings: {len(self.findings_with_cves)} with CVEs (vulnerabilities), "
            f"{len(self.findings_without_cves)} without CVEs (issues)"
        )

    def _extract_resource_identifier(self, finding: Dict[str, Any]) -> str:
        """
        Extract resource identifier from GuardDuty finding.

        :param Dict[str, Any] finding: GuardDuty finding
        :return: Resource identifier (instance ID, ARN, or account ID)
        :rtype: str
        """
        resource = finding.get("Resource", {})

        # Try to get EC2 instance ID first
        instance_id = self._extract_ec2_instance_id(resource)
        if instance_id:
            return instance_id

        # Try to get resource ARN based on type
        resource_arn = self._extract_resource_arn(resource)
        if resource_arn:
            return resource_arn

        # Fallback to account ID if no specific resource found
        account_id = finding.get("AccountId", "")
        return account_id if account_id else ""

    def _extract_ec2_instance_id(self, resource: Dict[str, Any]) -> str:
        """Extract EC2 instance ID from resource details."""
        instance_details = resource.get("InstanceDetails", {})
        if instance_details:
            instance_id = instance_details.get("InstanceId")
            if instance_id:
                return instance_id
        return ""

    def _extract_resource_arn(self, resource: Dict[str, Any]) -> str:
        """Extract ARN based on resource type."""
        resource_type = resource.get("ResourceType", "")

        resource_extractors = {
            "S3Bucket": lambda: self._extract_s3_arn(resource),
            "EKSCluster": lambda: resource.get("EksClusterDetails", {}).get("Arn", ""),
            "ECSCluster": lambda: resource.get("EcsClusterDetails", {}).get("Arn", ""),
            "Lambda": lambda: resource.get("LambdaDetails", {}).get("FunctionArn", ""),
            "RDSDBInstance": lambda: resource.get("RdsDbInstanceDetails", {}).get("DbInstanceArn", ""),
        }

        extractor = resource_extractors.get(resource_type)
        if extractor:
            return extractor() or ""
        return ""

    def _extract_s3_arn(self, resource: Dict[str, Any]) -> str:
        """Extract S3 bucket ARN from resource details."""
        s3_details = resource.get("S3BucketDetails", [])
        if s3_details:
            return s3_details[0].get("Arn", "")
        return ""

    def _parse_guardduty_finding_as_issue(self, finding: Dict[str, Any]) -> IntegrationFinding:
        """Parse GuardDuty finding as RegScale Issue."""
        finding_id = finding.get("Id", "")
        finding_type = finding.get("Type", "")
        title = finding.get("Title", "")
        severity = self.control_mapper._get_severity_level(finding.get("Severity", 0))

        # Extract resource identifier
        asset_identifier = self._extract_resource_identifier(finding)

        # Create URL-safe external_id by replacing colons with dashes
        # GuardDuty IDs are like "41:UnauthorizedAccess:EC2/SSHBruteForce"
        external_id = finding_id.replace(":", "-")

        # Build detailed description with original finding ID
        detailed_description = self._build_finding_description(finding)

        # Map severity to RegScale
        severity_map = {"LOW": "Low", "MEDIUM": "Moderate", "HIGH": "High", "CRITICAL": "Critical"}
        regscale_severity = severity_map.get(severity, "Moderate")

        # Create IntegrationFinding
        integration_finding = IntegrationFinding(
            asset_identifier=asset_identifier,
            control_labels=[],
            category="Security",
            external_id=external_id,
            title=f"{finding_type}: {title}",
            description=detailed_description,
            severity=regscale_severity,
            status="Open",
            plugin_id=finding_type,
            plugin_name=f"AWS GuardDuty - {finding_type}",
            comments=f"GuardDuty Finding ID: {finding_id}\nRegion: {finding.get('Region', self.region)}",
        )

        return integration_finding

    def _parse_guardduty_finding_as_vulnerability(self, finding: Dict[str, Any]) -> IntegrationFinding:
        """Parse GuardDuty finding with CVE as RegScale Vulnerability."""
        finding_id = finding.get("Id", "")
        finding_type = finding.get("Type", "")
        title = finding.get("Title", "")
        severity = self.control_mapper._get_severity_level(finding.get("Severity", 0))

        # Extract CVEs
        cves = self.control_mapper.extract_cves_from_finding(finding)
        primary_cve = cves[0] if cves else None

        # Extract resource identifier
        asset_identifier = self._extract_resource_identifier(finding)

        # Create URL-safe external_id by replacing colons with dashes
        external_id = finding_id.replace(":", "-")

        # Build detailed description
        detailed_description = self._build_finding_description(finding)

        # Map severity
        severity_map = {"LOW": "Low", "MEDIUM": "Moderate", "HIGH": "High", "CRITICAL": "Critical"}
        regscale_severity = severity_map.get(severity, "Moderate")

        integration_finding = IntegrationFinding(
            asset_identifier=asset_identifier,
            control_labels=[],
            category="Vulnerability",
            external_id=external_id,
            title=f"{finding_type}: {title}",
            description=detailed_description,
            severity=regscale_severity,
            status="Open",
            vulnerability_number=primary_cve,
            plugin_id=finding_type,
            plugin_name=f"AWS GuardDuty - {finding_type}",
            comments=f"GuardDuty Finding ID: {finding_id}\nCVEs: {', '.join(cves)}\nRegion: {finding.get('Region', self.region)}",
        )

        return integration_finding

    def _build_finding_description(self, finding: Dict[str, Any]) -> str:
        """Build HTML-formatted finding description."""
        # Extract finding metadata
        metadata = self._extract_finding_metadata(finding)

        # Build base description
        desc_parts = self._build_finding_header()
        desc_parts.extend(self._build_finding_details(metadata))

        # Add CVE information if present
        cve_section = self._build_cve_section(finding)
        if cve_section:
            desc_parts.extend(cve_section)

        return "\n".join(desc_parts)

    def _extract_finding_metadata(self, finding: Dict[str, Any]) -> Dict[str, str]:
        """Extract metadata from finding for description building."""
        resource = finding.get("Resource", {})
        service = finding.get("Service", {})
        action = service.get("Action", {})

        return {
            "description": finding.get("Description", ""),
            "finding_type": finding.get("Type", ""),
            "severity": self.control_mapper._get_severity_level(finding.get("Severity", 0)),
            "created_at": finding.get("CreatedAt", ""),
            "updated_at": finding.get("UpdatedAt", ""),
            "resource_type": resource.get("ResourceType", ""),
            "action_type": action.get("ActionType", "N/A"),
        }

    def _build_finding_header(self) -> List[str]:
        """Build the header section of finding description."""
        return [
            f"{HTML_H3_OPEN}GuardDuty Security Finding{HTML_H3_CLOSE}",
            HTML_P_OPEN,
        ]

    def _build_finding_details(self, metadata: Dict[str, str]) -> List[str]:
        """Build the details section of finding description."""
        details = [
            f"{HTML_STRONG_OPEN}Finding Type:{HTML_STRONG_CLOSE} {metadata['finding_type']}{HTML_BR}",
            f"{HTML_STRONG_OPEN}Severity:{HTML_STRONG_CLOSE} {metadata['severity']}{HTML_BR}",
            f"{HTML_STRONG_OPEN}Resource Type:{HTML_STRONG_CLOSE} {metadata['resource_type']}{HTML_BR}",
            f"{HTML_STRONG_OPEN}Action Type:{HTML_STRONG_CLOSE} {metadata['action_type']}{HTML_BR}",
            f"{HTML_STRONG_OPEN}Created:{HTML_STRONG_CLOSE} {metadata['created_at']}{HTML_BR}",
            f"{HTML_STRONG_OPEN}Updated:{HTML_STRONG_CLOSE} {metadata['updated_at']}",
            HTML_P_CLOSE,
            f"{HTML_H3_OPEN}Description{HTML_H3_CLOSE}",
            f"{HTML_P_OPEN}{metadata['description']}{HTML_P_CLOSE}",
        ]
        return details

    def _build_cve_section(self, finding: Dict[str, Any]) -> List[str]:
        """Build CVE references section if CVEs are present."""
        if not self.control_mapper.has_cve_reference(finding):
            return []

        cves = self.control_mapper.extract_cves_from_finding(finding)
        cve_parts = [
            f"{HTML_H3_OPEN}CVE References{HTML_H3_CLOSE}",
            HTML_UL_OPEN,
        ]

        for cve in cves:
            cve_parts.append(f"{HTML_LI_OPEN}{cve}{HTML_LI_CLOSE}")

        cve_parts.append(HTML_UL_CLOSE)
        return cve_parts

    def sync_compliance(self) -> None:
        """
        Main method to sync GuardDuty compliance data.

        This extends the base sync_compliance to:
        1. Create assessments for controls (SI-4, IR-4, IR-5, SI-3, RA-5)
        2. Update control implementation status
        3. Create issues for failed compliance
        4. Process individual findings as issues/vulnerabilities
        5. Collect evidence if requested
        """
        # Call the base class sync_compliance to handle control assessments and issues
        super().sync_compliance()

        # Additionally process individual findings as issues/vulnerabilities
        self._process_individual_findings()

        # If evidence collection is enabled, collect evidence after compliance sync
        if self.collect_evidence:
            logger.info("Evidence collection enabled, starting evidence collection...")
            self._collect_guardduty_evidence()

    def _process_individual_findings(self) -> None:
        """Process individual GuardDuty findings as issues or vulnerabilities."""
        # Classify findings
        self._classify_findings()

        # Create issues for findings without CVEs
        if self.create_issues and self.findings_without_cves:
            logger.info(f"Creating {len(self.findings_without_cves)} issues from GuardDuty findings...")
            issues = [self._parse_guardduty_finding_as_issue(f) for f in self.findings_without_cves]
            self.update_regscale_findings(issues)

        # Create vulnerabilities for findings with CVEs
        if self.create_vulnerabilities and self.findings_with_cves:
            logger.info(f"Creating {len(self.findings_with_cves)} vulnerabilities from GuardDuty CVE findings...")
            vulns = [self._parse_guardduty_finding_as_vulnerability(f) for f in self.findings_with_cves]
            self.update_regscale_findings(vulns)

    def sync_findings(self) -> None:
        """
        Legacy method for backward compatibility.
        Redirects to sync_compliance which now handles everything.
        """
        logger.info("sync_findings called - redirecting to sync_compliance for full compliance integration")
        self.sync_compliance()

    def _collect_guardduty_evidence(self) -> None:
        if not self.raw_guardduty_data:
            logger.warning("No GuardDuty data available for evidence collection")
            return

        scan_date = get_current_datetime(dt_format="%Y-%m-%d %H:%M:%S")

        if self.evidence_as_attachments:
            logger.info("Creating SSP file attachment with GuardDuty evidence...")
            self._create_ssp_attachment(scan_date)
        else:
            logger.info("Creating Evidence record with GuardDuty evidence...")
            self._create_evidence_record(scan_date)

    def _create_ssp_attachment(self, scan_date: str) -> None:
        try:
            # Check for existing evidence to avoid duplicates
            date_str = datetime.now().strftime("%Y%m%d")
            file_name_pattern = f"guardduty_evidence_{date_str}"

            if self.check_for_existing_evidence(file_name_pattern):
                logger.info(
                    "Evidence file for GuardDuty already exists for today. Skipping upload to avoid duplicates."
                )
                return

            # Add timestamp to make filename unique if run multiple times per day
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"guardduty_evidence_{timestamp}.jsonl.gz"

            # Build compliance assessment
            compliance_results = self.control_mapper.assess_guardduty_compliance(self.raw_guardduty_data)

            evidence_entry = {
                **self.raw_guardduty_data,
                "compliance_assessment": {
                    "control_results": compliance_results,
                    "assessed_controls": list(compliance_results.keys()),
                    "assessment_date": scan_date,
                },
                "findings_summary": {
                    "total": len(self.raw_guardduty_data.get("Findings", [])),
                    "with_cves": len(self.findings_with_cves),
                    "without_cves": len(self.findings_without_cves),
                },
            }

            jsonl_content = json.dumps(evidence_entry, default=str)

            compressed_buffer = BytesIO()
            with gzip.open(compressed_buffer, "wt", encoding="utf-8", compresslevel=9) as gz_file:
                gz_file.write(jsonl_content)

            compressed_data = compressed_buffer.getvalue()

            api = Api()
            success = File.upload_file_to_regscale(
                file_name=file_name,
                parent_id=self.plan_id,
                parent_module=self.parent_module,
                api=api,
                file_data=compressed_data,
                tags="aws,guardduty,threat-detection,automated",
            )

            if success:
                logger.info(f"Successfully uploaded GuardDuty evidence file: {file_name}")
            else:
                logger.error("Failed to upload GuardDuty evidence file")

        except Exception as e:
            logger.error(f"Error creating SSP attachment: {e}", exc_info=True)

    def _create_evidence_record(self, scan_date: str) -> None:
        try:
            title = f"AWS GuardDuty Evidence - {scan_date}"
            description = self._build_evidence_description(scan_date)
            due_date = (datetime.now() + timedelta(days=self.evidence_frequency)).isoformat()

            evidence = Evidence(
                title=title,
                description=description,
                status="Collected",
                updateFrequency=self.evidence_frequency,
                dueDate=due_date,
            )

            created_evidence = evidence.create()
            if not created_evidence or not created_evidence.id:
                logger.error("Failed to create evidence record")
                return

            logger.info(f"Created evidence record {created_evidence.id}: {title}")
            self._upload_evidence_file(created_evidence.id, scan_date)
            self._link_evidence_to_ssp(created_evidence.id)

            # Link to controls if specified
            if self.evidence_control_ids:
                self._link_evidence_to_controls(created_evidence.id, is_attachment=False)

        except Exception as e:
            logger.error(f"Error creating evidence record: {e}", exc_info=True)

    def _build_evidence_description(self, scan_date: str) -> str:
        """Build HTML-formatted evidence description."""
        # Get summary data
        summary = self._get_guardduty_summary()
        compliance_results = self.control_mapper.assess_guardduty_compliance(self.raw_guardduty_data)

        # Build description parts
        desc_parts = self._build_evidence_header(scan_date)
        desc_parts.extend(self._build_summary_section(summary))
        desc_parts.extend(self._build_compliance_section(compliance_results))

        return "\n".join(desc_parts)

    def _get_guardduty_summary(self) -> Dict[str, int]:
        """Extract summary statistics from GuardDuty data."""
        return {
            "detectors": len(self.raw_guardduty_data.get("Detectors", [])),
            "total_findings": len(self.raw_guardduty_data.get("Findings", [])),
            "cve_findings": len(self.findings_with_cves),
            "security_issues": len(self.findings_without_cves),
        }

    def _build_evidence_header(self, scan_date: str) -> List[str]:
        """Build evidence header section."""
        return [
            "<h1>AWS GuardDuty Threat Detection Evidence</h1>",
            f"{HTML_P_OPEN}{HTML_STRONG_OPEN}Assessment Date:{HTML_STRONG_CLOSE} {scan_date}{HTML_P_CLOSE}",
        ]

    def _build_summary_section(self, summary: Dict[str, int]) -> List[str]:
        """Build GuardDuty summary section."""
        return [
            f"{HTML_H2_OPEN}GuardDuty Summary{HTML_H2_CLOSE}",
            HTML_UL_OPEN,
            f"{HTML_LI_OPEN}{HTML_STRONG_OPEN}Detectors:{HTML_STRONG_CLOSE} {summary['detectors']}{HTML_LI_CLOSE}",
            f"{HTML_LI_OPEN}{HTML_STRONG_OPEN}Total Findings:{HTML_STRONG_CLOSE} {summary['total_findings']}{HTML_LI_CLOSE}",
            f"{HTML_LI_OPEN}{HTML_STRONG_OPEN}CVE-Related Findings:{HTML_STRONG_CLOSE} {summary['cve_findings']}{HTML_LI_CLOSE}",
            f"{HTML_LI_OPEN}{HTML_STRONG_OPEN}Security Issues:{HTML_STRONG_CLOSE} {summary['security_issues']}{HTML_LI_CLOSE}",
            HTML_UL_CLOSE,
        ]

    def _build_compliance_section(self, compliance_results: Dict[str, str]) -> List[str]:
        """Build control compliance results section."""
        section_parts = [
            f"{HTML_H2_OPEN}Control Compliance Results{HTML_H2_CLOSE}",
            HTML_UL_OPEN,
        ]

        for control_id, result in compliance_results.items():
            control_item = self._format_control_result(control_id, result)
            section_parts.append(control_item)

        section_parts.append(HTML_UL_CLOSE)
        return section_parts

    def _format_control_result(self, control_id: str, result: str) -> str:
        """Format a single control result for display."""
        control_desc = self.control_mapper.get_control_description(control_id)
        result_color = "#d32f2f" if result == "FAIL" else "#2e7d32"
        return (
            f"{HTML_LI_OPEN}{HTML_STRONG_OPEN}{control_id}:{HTML_STRONG_CLOSE} "
            f"<span style='color: {result_color};'>{result}</span> - {control_desc}{HTML_LI_CLOSE}"
        )

    def _upload_evidence_file(self, evidence_id: int, scan_date: str) -> None:
        try:
            compliance_results = self.control_mapper.assess_guardduty_compliance(self.raw_guardduty_data)
            evidence_entry = {
                **self.raw_guardduty_data,
                "compliance_assessment": {
                    "control_results": compliance_results,
                    "assessed_controls": list(compliance_results.keys()),
                    "assessment_date": scan_date,
                },
            }
            jsonl_content = json.dumps(evidence_entry, default=str)

            compressed_buffer = BytesIO()
            with gzip.open(compressed_buffer, "wt", encoding="utf-8", compresslevel=9) as gz_file:
                gz_file.write(jsonl_content)

            compressed_data = compressed_buffer.getvalue()
            file_name = f"guardduty_evidence_{scan_date}.jsonl.gz"

            api = Api()
            success = File.upload_file_to_regscale(
                file_name=file_name,
                parent_id=evidence_id,
                parent_module="evidence",
                api=api,
                file_data=compressed_data,
                tags="aws,guardduty,threat-detection",
            )

            if success:
                logger.info(f"Uploaded GuardDuty evidence file to Evidence {evidence_id}")
            else:
                logger.warning(f"Failed to upload evidence file to Evidence {evidence_id}")

        except Exception as e:
            logger.error(f"Error uploading evidence file: {e}", exc_info=True)

    def _link_evidence_to_ssp(self, evidence_id: int) -> None:
        try:
            mapping = EvidenceMapping(evidenceID=evidence_id, mappedID=self.plan_id, mappingType=self.parent_module)
            mapping.create()
            logger.info(f"Linked evidence {evidence_id} to SSP {self.plan_id}")
        except Exception as ex:
            logger.warning(f"Failed to link evidence to SSP: {ex}")

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

    def _map_resource_type_to_asset_type(self, compliance_item: ComplianceItem) -> str:
        """
        Map GuardDuty service to RegScale asset type.

        :param ComplianceItem compliance_item: Compliance item
        :return: Asset type string
        :rtype: str
        """
        return "AWS GuardDuty Service"

    def fetch_findings(self, *args, **kwargs):
        """
        Fetch findings from GuardDuty (implements ScannerIntegration abstract method).

        This method is not used in the current implementation as GuardDuty findings
        are fetched and processed directly in sync_compliance().

        :return: Empty iterator
        :rtype: Iterator
        """
        return iter([])

    def fetch_assets(self, *args, **kwargs):
        """
        Fetch assets from GuardDuty (implements ScannerIntegration abstract method).

        GuardDuty creates a single asset representing the GuardDuty service itself.

        :return: Iterator of assets
        :rtype: Iterator
        """
        # GuardDuty represents a service-level asset, not individual resources
        # We create one asset per account/region combination
        if self.all_compliance_items:
            # Use the first compliance item to get account info
            first_item = self.all_compliance_items[0]
            asset = self.create_asset_from_compliance_item(first_item)
            if asset:
                yield asset
