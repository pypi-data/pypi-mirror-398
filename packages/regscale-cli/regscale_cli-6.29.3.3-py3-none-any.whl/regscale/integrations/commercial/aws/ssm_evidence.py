#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AWS Systems Manager Evidence Integration for RegScale Compliance."""

import gzip
import json
import logging
import os
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import boto3

from regscale.core.app.api import Api
from regscale.integrations.commercial.aws.inventory.resources.systems_manager import SystemsManagerCollector
from regscale.integrations.commercial.aws.ssm_control_mappings import SSMControlMapper
from regscale.integrations.compliance_integration import ComplianceIntegration
from regscale.models.regscale_models.file import File

logger = logging.getLogger("regscale")


@dataclass
class SSMEvidenceConfig:
    """Configuration for AWS Systems Manager evidence collection."""

    plan_id: int
    region: str = "us-east-1"
    framework: str = "NIST800-53R5"
    create_issues: bool = False
    update_control_status: bool = True
    create_poams: bool = False
    parent_module: str = "securityplans"
    account_id: Optional[str] = None
    tags: Optional[Dict[str, str]] = None
    create_evidence: bool = False
    create_ssp_attachment: bool = True
    evidence_control_ids: Optional[List[str]] = None
    force_refresh: bool = False
    aws_profile: Optional[str] = None
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_session_token: Optional[str] = None


class SSMComplianceItem:
    """Represents Systems Manager configuration for compliance assessment."""

    def __init__(self, ssm_data: Dict[str, Any]):
        """
        Initialize SSM compliance item from configuration data.

        :param Dict ssm_data: SSM configuration data from SystemsManagerCollector
        """
        self.managed_instances = ssm_data.get("ManagedInstances", [])
        self.parameters = ssm_data.get("Parameters", [])
        self.documents = ssm_data.get("Documents", [])
        self.patch_baselines = ssm_data.get("PatchBaselines", [])
        self.maintenance_windows = ssm_data.get("MaintenanceWindows", [])
        self.associations = ssm_data.get("Associations", [])
        self.inventory_entries = ssm_data.get("InventoryEntries", [])
        self.compliance_summary = ssm_data.get("ComplianceSummary", {})
        self.raw_data = ssm_data

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return self.raw_data


class AWSSSMEvidenceIntegration(ComplianceIntegration):
    """AWS Systems Manager evidence integration for compliance data collection."""

    def __init__(self, config: SSMEvidenceConfig):
        """
        Initialize AWS Systems Manager evidence integration.

        :param SSMEvidenceConfig config: Configuration object containing all parameters
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
        self.region = config.region
        self.title = "AWS Systems Manager"
        self.account_id = config.account_id
        self.tags = config.tags or {}
        self.create_evidence = config.create_evidence
        self.create_ssp_attachment = config.create_ssp_attachment
        self.evidence_control_ids = config.evidence_control_ids or []
        self.force_refresh = config.force_refresh

        # AWS credentials
        self.aws_profile = config.aws_profile
        self.aws_access_key_id = config.aws_access_key_id
        self.aws_secret_access_key = config.aws_secret_access_key
        self.aws_session_token = config.aws_session_token

        # Initialize components
        self.api = Api()
        self.control_mapper = SSMControlMapper(framework=config.framework)
        self.session = None
        self.collector = None

        # Cache configuration
        self.cache_ttl_hours = 4
        self.cache_dir = Path(tempfile.gettempdir()) / "regscale" / "aws_ssm_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Data storage
        self.raw_ssm_data: Dict[str, Any] = {}
        self.ssm_item: Optional[SSMComplianceItem] = None

    def _get_cache_file_path(self) -> Path:
        """Get cache file path for SSM data."""
        cache_key = f"{self.region}_{self.account_id or 'default'}"
        return self.cache_dir / f"ssm_data_{cache_key}.json"

    def _is_cache_valid(self) -> bool:
        """Check if cache is valid and not expired."""
        cache_file = self._get_cache_file_path()
        if not cache_file.exists():
            return False

        cache_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
        return cache_age < timedelta(hours=self.cache_ttl_hours)

    def _save_cache(self, data: Dict[str, Any]) -> None:
        """Save SSM data to cache."""
        cache_file = self._get_cache_file_path()
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, default=str)
            logger.debug(f"Saved SSM data to cache: {cache_file}")
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")

    def _load_cached_data(self) -> Optional[Dict[str, Any]]:
        """Load SSM data from cache."""
        cache_file = self._get_cache_file_path()
        try:
            with open(cache_file, encoding="utf-8") as f:
                data = json.load(f)

            # Validate cache format - must be a dict
            if not isinstance(data, dict):
                logger.warning("Invalid cache format detected (not a dict). Invalidating cache.")
                return None

            logger.info(f"Loaded SSM data from cache (age: {self._get_cache_age_hours():.1f} hours)")
            return data
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}")
            return None

    def _get_cache_age_hours(self) -> float:
        """Get cache age in hours."""
        cache_file = self._get_cache_file_path()
        if not cache_file.exists():
            return float("inf")
        cache_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
        return cache_age.total_seconds() / 3600

    def _initialize_aws_session(self) -> None:
        """Initialize AWS session using provided credentials."""
        if self.aws_access_key_id and self.aws_secret_access_key:
            self.session = boto3.Session(
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                aws_session_token=self.aws_session_token,
                region_name=self.region,
            )
        elif self.aws_profile:
            self.session = boto3.Session(profile_name=self.aws_profile, region_name=self.region)
        else:
            self.session = boto3.Session(region_name=self.region)
        logger.info(f"Initialized AWS session for region: {self.region}")

    def fetch_compliance_data(self) -> Dict[str, Any]:
        """
        Fetch Systems Manager configuration data from AWS.

        :return: SSM configuration data
        :rtype: Dict[str, Any]
        """
        # Check cache first
        if not self.force_refresh and self._is_cache_valid():
            cached_data = self._load_cached_data()
            if cached_data:
                return cached_data

        # Fetch fresh data
        return self._fetch_fresh_ssm_data()

    def _fetch_fresh_ssm_data(self) -> Dict[str, Any]:
        """
        Fetch fresh SSM data from AWS API.

        :return: SSM configuration data
        :rtype: Dict[str, Any]
        """
        logger.info(f"Fetching Systems Manager configurations from AWS region: {self.region}")

        # Initialize AWS session
        if not self.session:
            self._initialize_aws_session()

        # Create SSM collector
        self.collector = SystemsManagerCollector(
            session=self.session, region=self.region, account_id=self.account_id, tags=self.tags
        )

        # Collect SSM data
        self.raw_ssm_data = self.collector.collect()

        managed_instances = len(self.raw_ssm_data.get("ManagedInstances", []))
        parameters = len(self.raw_ssm_data.get("Parameters", []))
        documents = len(self.raw_ssm_data.get("Documents", []))
        patch_baselines = len(self.raw_ssm_data.get("PatchBaselines", []))

        logger.info(
            f"Collected SSM data: {managed_instances} instances, {parameters} parameters, "
            f"{documents} documents, {patch_baselines} patch baselines"
        )

        # Save to cache
        self._save_cache(self.raw_ssm_data)

        return self.raw_ssm_data

    def sync_compliance_data(self) -> None:
        """Sync Systems Manager compliance data to RegScale."""
        logger.info("Starting AWS Systems Manager compliance data sync to RegScale")

        # Fetch SSM data
        ssm_data = self.fetch_compliance_data()
        if not ssm_data:
            logger.warning("No Systems Manager data to sync")
            return

        # Convert to compliance item
        self.ssm_item = SSMComplianceItem(ssm_data)
        logger.info("Processing Systems Manager configuration for compliance assessment")

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

        logger.info("AWS Systems Manager compliance sync completed successfully")

    def create_compliance_item(self, raw_data: Dict[str, Any]):
        """
        Create a ComplianceItem from raw SSM data.

        :param Dict[str, Any] raw_data: Raw SSM configuration data
        :return: SSMComplianceItem instance
        :rtype: SSMComplianceItem
        """
        return SSMComplianceItem(raw_data)

    def _assess_compliance(self) -> Dict[str, Any]:
        """
        Assess Systems Manager compliance against NIST controls.

        :return: Compliance assessment results
        :rtype: Dict[str, Any]
        """
        logger.info("Assessing Systems Manager compliance against NIST 800-53 R5 controls")

        # Assess overall compliance
        overall_results = self.control_mapper.assess_ssm_compliance(self.ssm_item.to_dict())

        # Log summary
        passed_controls = [ctrl for ctrl, result in overall_results.items() if result == "PASS"]
        failed_controls = [ctrl for ctrl, result in overall_results.items() if result == "FAIL"]

        logger.info("Systems Manager Compliance Assessment Summary:")
        logger.info(f"  Managed Instances: {len(self.ssm_item.managed_instances)}")
        logger.info(f"  Parameters: {len(self.ssm_item.parameters)}")
        logger.info(f"  Documents: {len(self.ssm_item.documents)}")
        logger.info(f"  Patch Baselines: {len(self.ssm_item.patch_baselines)}")
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
            if result in self.PASS_STATUSES:
                self.passing_controls[control_key] = self.ssm_item
            elif result in self.FAIL_STATUSES:
                self.failing_controls[control_key] = self.ssm_item

        logger.debug(
            f"Populated control results: {len(self.passing_controls)} passing, {len(self.failing_controls)} failing"
        )

    def _create_evidence_artifacts(self, compliance_results: Dict[str, Any]) -> None:
        """
        Create evidence artifacts in RegScale.

        :param Dict compliance_results: Compliance assessment results
        """
        logger.info("Creating Systems Manager evidence artifacts in RegScale")

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
        Create JSONL.GZ evidence file with Systems Manager configuration data.

        :param Dict compliance_results: Compliance assessment results
        :return: Path to created evidence file
        :rtype: str
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        evidence_file = os.path.join(tempfile.gettempdir(), f"ssm_evidence_{self.region}_{timestamp}.jsonl.gz")

        try:
            with gzip.open(evidence_file, "wt", encoding="utf-8") as f:
                # Write metadata
                metadata = {
                    "type": "metadata",
                    "timestamp": datetime.now().isoformat(),
                    "region": self.region,
                    "account_id": self.account_id,
                    "managed_instances_count": len(self.ssm_item.managed_instances),
                    "parameters_count": len(self.ssm_item.parameters),
                    "documents_count": len(self.ssm_item.documents),
                    "patch_baselines_count": len(self.ssm_item.patch_baselines),
                    "compliance_framework": "NIST800-53R5",
                }
                f.write(json.dumps(metadata) + "\n")

                # Write compliance summary
                summary = {"type": "compliance_summary", "results": compliance_results["overall"]}
                f.write(json.dumps(summary) + "\n")

                # Write managed instances
                for instance in self.ssm_item.managed_instances:
                    instance_record = {
                        "type": "managed_instance",
                        "instance_id": instance.get("InstanceId"),
                        "ping_status": instance.get("PingStatus"),
                        "platform": instance.get("PlatformName"),
                        "agent_version": instance.get("AgentVersion"),
                        "patch_summary": instance.get("PatchSummary", {}),
                    }
                    f.write(json.dumps(instance_record, default=str) + "\n")

                # Write patch baselines
                for baseline in self.ssm_item.patch_baselines:
                    baseline_record = {
                        "type": "patch_baseline",
                        "baseline_id": baseline.get("BaselineId"),
                        "name": baseline.get("BaselineName"),
                        "os": baseline.get("OperatingSystem"),
                        "default": baseline.get("DefaultBaseline", False),
                    }
                    f.write(json.dumps(baseline_record, default=str) + "\n")

                # Write maintenance windows
                for window in self.ssm_item.maintenance_windows:
                    window_record = {
                        "type": "maintenance_window",
                        "window_id": window.get("WindowId"),
                        "name": window.get("Name"),
                        "enabled": window.get("Enabled", False),
                        "schedule": window.get("Schedule"),
                    }
                    f.write(json.dumps(window_record, default=str) + "\n")

                # Write compliance summary
                if self.ssm_item.compliance_summary:
                    compliance_record = {
                        "type": "compliance_data",
                        "total_compliant": self.ssm_item.compliance_summary.get("TotalCompliant", 0),
                        "total_non_compliant": self.ssm_item.compliance_summary.get("TotalNonCompliant", 0),
                        "compliance_types": self.ssm_item.compliance_summary.get("ComplianceTypes", []),
                    }
                    f.write(json.dumps(compliance_record, default=str) + "\n")

            logger.info(f"Created evidence file: {evidence_file}")
            return evidence_file

        except Exception as e:
            logger.error(f"Failed to create evidence file: {e}", exc_info=True)
            raise

    def _create_ssp_attachment_with_evidence(self, evidence_file_path: str) -> None:
        """
        Create SSP attachment with Systems Manager evidence.

        :param str evidence_file_path: Path to evidence file
        """
        try:
            date_str = datetime.now().strftime("%Y%m%d")
            file_name_pattern = f"ssm_evidence_{self.region}_{date_str}"

            # Check if evidence for today already exists using base class method
            if self.check_for_existing_evidence(file_name_pattern):
                logger.info(
                    f"Evidence file for Systems Manager in region {self.region} already exists for today. "
                    "Skipping upload to avoid duplicates."
                )
                return

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"ssm_evidence_{self.region}_{timestamp}.jsonl.gz"

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
                tags="aws,ssm,systems-manager,patch,config,compliance,automated",
            )

            if success:
                logger.info(f"Successfully uploaded Systems Manager evidence file: {file_name}")
                # Note: SSP attachments don't return IDs from upload_file_to_regscale
                # Control linking would need to be implemented if required for attachments
                if self.evidence_control_ids:
                    pass  # Placeholder for future SSP attachment-to-control linking
            else:
                logger.error("Failed to upload Systems Manager evidence file")

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
