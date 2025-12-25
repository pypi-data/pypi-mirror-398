#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AWS CloudWatch Logs Evidence Integration for RegScale Compliance."""

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
from regscale.integrations.commercial.aws.cloudwatch_control_mappings import CloudWatchControlMapper
from regscale.integrations.commercial.aws.inventory.resources.cloudwatch import CloudWatchLogsCollector
from regscale.integrations.compliance_integration import ComplianceIntegration
from regscale.models.regscale_models.file import File

logger = logging.getLogger("regscale")


@dataclass
class CloudWatchEvidenceConfig:
    """Configuration for AWS CloudWatch Logs evidence collection."""

    plan_id: int
    region: str = "us-east-1"
    framework: str = "NIST800-53R5"
    create_issues: bool = False
    update_control_status: bool = True
    create_poams: bool = False
    parent_module: str = "securityplans"
    account_id: Optional[str] = None
    tags: Optional[Dict[str, str]] = None
    log_group_prefix: Optional[str] = None
    create_evidence: bool = False
    create_ssp_attachment: bool = True
    evidence_control_ids: Optional[List[str]] = None
    force_refresh: bool = False
    aws_profile: Optional[str] = None
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_session_token: Optional[str] = None


class CloudWatchComplianceItem:
    """Represents CloudWatch Logs configuration for compliance assessment."""

    def __init__(self, cloudwatch_data: Dict[str, Any]):
        """
        Initialize CloudWatch compliance item from configuration data.

        :param Dict cloudwatch_data: CloudWatch Logs data from CloudWatchLogsCollector
        """
        self.log_groups = cloudwatch_data.get("LogGroups", [])
        self.log_group_metrics = cloudwatch_data.get("LogGroupMetrics", {})
        self.retention_policies = cloudwatch_data.get("RetentionPolicies", {})
        self.raw_data = cloudwatch_data

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return self.raw_data


class AWSCloudWatchEvidenceIntegration(ComplianceIntegration):
    """AWS CloudWatch Logs evidence integration for compliance data collection."""

    def __init__(self, config: CloudWatchEvidenceConfig):
        """
        Initialize AWS CloudWatch Logs evidence integration.

        :param CloudWatchEvidenceConfig config: Configuration object containing all parameters
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
        self.title = "AWS CloudWatch Logs"
        self.account_id = config.account_id
        self.tags = config.tags or {}
        self.log_group_prefix = config.log_group_prefix
        self.create_evidence = config.create_evidence
        self.create_ssp_attachment = config.create_ssp_attachment
        self.evidence_control_ids = config.evidence_control_ids or []
        self.force_refresh = config.force_refresh

        # Initialize control mapper
        self.control_mapper = CloudWatchControlMapper(framework=config.framework)

        # AWS credentials
        self.aws_profile = config.aws_profile
        self.aws_access_key_id = config.aws_access_key_id
        self.aws_secret_access_key = config.aws_secret_access_key
        self.aws_session_token = config.aws_session_token

        # Initialize components
        self.api = Api()
        self.session = None
        self.collector = None

        # Cache configuration
        self.cache_ttl_hours = 4
        self.cache_dir = Path(tempfile.gettempdir()) / "regscale" / "aws_cloudwatch_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Data storage
        self.raw_cloudwatch_data: Dict[str, Any] = {}
        self.cloudwatch_item: Optional[CloudWatchComplianceItem] = None

    def _get_cache_file_path(self) -> Path:
        """Get cache file path for CloudWatch data."""
        cache_key = f"{self.region}_{self.account_id or 'default'}"
        return self.cache_dir / f"cloudwatch_logs_{cache_key}.json"

    def _is_cache_valid(self) -> bool:
        """Check if cache is valid and not expired."""
        cache_file = self._get_cache_file_path()
        if not cache_file.exists():
            return False

        cache_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
        return cache_age < timedelta(hours=self.cache_ttl_hours)

    def _save_cache(self, data: Dict[str, Any]) -> None:
        """Save CloudWatch data to cache."""
        cache_file = self._get_cache_file_path()
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, default=str)
            logger.debug(f"Saved CloudWatch data to cache: {cache_file}")
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")

    def _load_cached_data(self) -> Optional[Dict[str, Any]]:
        """Load CloudWatch data from cache."""
        cache_file = self._get_cache_file_path()
        try:
            with open(cache_file, encoding="utf-8") as f:
                data = json.load(f)

            # Validate cache format - must be a dict
            if not isinstance(data, dict):
                logger.warning("Invalid cache format detected (not a dict). Invalidating cache.")
                return None

            logger.info(f"Loaded CloudWatch data from cache (age: {self._get_cache_age_hours():.1f} hours)")
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
        Fetch CloudWatch Logs configuration data from AWS.

        :return: CloudWatch Logs configuration data
        :rtype: Dict[str, Any]
        """
        # Check cache first
        if not self.force_refresh and self._is_cache_valid():
            cached_data = self._load_cached_data()
            if cached_data:
                return cached_data

        # Fetch fresh data
        return self._fetch_fresh_cloudwatch_data()

    def _fetch_fresh_cloudwatch_data(self) -> Dict[str, Any]:
        """
        Fetch fresh CloudWatch Logs data from AWS API.

        :return: CloudWatch Logs configuration data
        :rtype: Dict[str, Any]
        """
        logger.info(f"Fetching CloudWatch Logs configurations from AWS region: {self.region}")

        # Initialize AWS session
        if not self.session:
            self._initialize_aws_session()

        # Create CloudWatch Logs collector
        self.collector = CloudWatchLogsCollector(
            session=self.session, region=self.region, account_id=self.account_id, tags=self.tags
        )

        # Collect CloudWatch data
        self.raw_cloudwatch_data = self.collector.collect()

        # Apply log group prefix filter if specified
        if self.log_group_prefix:
            original_count = len(self.raw_cloudwatch_data.get("LogGroups", []))
            self.raw_cloudwatch_data["LogGroups"] = [
                lg
                for lg in self.raw_cloudwatch_data.get("LogGroups", [])
                if lg.get("logGroupName", "").startswith(self.log_group_prefix)
            ]
            filtered_count = len(self.raw_cloudwatch_data["LogGroups"])
            logger.info(
                f"Applied log group prefix filter '{self.log_group_prefix}': {filtered_count}/{original_count} log groups match"
            )

        log_group_count = len(self.raw_cloudwatch_data.get("LogGroups", []))
        logger.info(f"Collected {log_group_count} CloudWatch log group(s) from region {self.region}")

        # Save to cache
        self._save_cache(self.raw_cloudwatch_data)

        return self.raw_cloudwatch_data

    def sync_compliance_data(self) -> None:
        """Sync CloudWatch Logs compliance data to RegScale."""
        logger.info("Starting AWS CloudWatch Logs compliance data sync to RegScale")

        # Fetch CloudWatch data
        cloudwatch_data = self.fetch_compliance_data()
        if not cloudwatch_data or not cloudwatch_data.get("LogGroups"):
            logger.warning("No CloudWatch Logs data to sync")
            return

        # Convert to compliance item
        self.cloudwatch_item = CloudWatchComplianceItem(cloudwatch_data)
        logger.info(
            f"Processing {len(self.cloudwatch_item.log_groups)} CloudWatch log group(s) for compliance assessment"
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

        logger.info("AWS CloudWatch Logs compliance sync completed successfully")

    def create_compliance_item(self, raw_data: Dict[str, Any]):
        """
        Create a ComplianceItem from raw CloudWatch data.

        :param Dict[str, Any] raw_data: Raw CloudWatch Logs data
        :return: CloudWatchComplianceItem instance
        :rtype: CloudWatchComplianceItem
        """
        return CloudWatchComplianceItem(raw_data)

    def _assess_compliance(self) -> Dict[str, Any]:
        """
        Assess CloudWatch compliance against NIST controls.

        :return: Compliance assessment results
        :rtype: Dict[str, Any]
        """
        logger.info("Assessing CloudWatch Logs compliance against NIST 800-53 R5 controls")

        # Assess overall compliance
        overall_results = self.control_mapper.assess_cloudwatch_compliance(self.cloudwatch_item.to_dict())

        # Log summary
        passed_controls = [ctrl for ctrl, result in overall_results.items() if result == "PASS"]
        failed_controls = [ctrl for ctrl, result in overall_results.items() if result == "FAIL"]

        logger.info("CloudWatch Logs Compliance Assessment Summary:")
        logger.info(f"  Total Log Groups: {len(self.cloudwatch_item.log_groups)}")
        logger.info(
            f"  Total Stored Bytes: {sum(m.get('StoredBytes', 0) for m in self.cloudwatch_item.log_group_metrics.values())}"
        )
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
                self.passing_controls[control_key] = self.cloudwatch_item
            elif result in self.FAIL_STATUSES:
                self.failing_controls[control_key] = self.cloudwatch_item

        logger.debug(
            f"Populated control results: {len(self.passing_controls)} passing, {len(self.failing_controls)} failing"
        )

    def _create_evidence_artifacts(self, compliance_results: Dict[str, Any]) -> None:
        """
        Create evidence artifacts in RegScale.

        :param Dict compliance_results: Compliance assessment results
        """
        logger.info("Creating CloudWatch Logs evidence artifacts in RegScale")

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
        Create JSONL.GZ evidence file with CloudWatch Logs configuration data.

        :param Dict compliance_results: Compliance assessment results
        :return: Path to created evidence file
        :rtype: str
        """
        evidence_file = self._get_evidence_file_path()

        try:
            with gzip.open(evidence_file, "wt", encoding="utf-8") as f:
                self._write_metadata(f)
                self._write_compliance_summary(f, compliance_results)
                self._write_log_group_configurations(f)

            logger.info(f"Created evidence file: {evidence_file}")
            return evidence_file

        except Exception as e:
            logger.error(f"Failed to create evidence file: {e}", exc_info=True)
            raise

    def _get_evidence_file_path(self) -> str:
        """Generate evidence file path with timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return os.path.join(tempfile.gettempdir(), f"cloudwatch_evidence_{self.region}_{timestamp}.jsonl.gz")

    def _write_metadata(self, file_handle) -> None:
        """Write metadata record to evidence file."""
        metadata = {
            "type": "metadata",
            "timestamp": datetime.now().isoformat(),
            "region": self.region,
            "account_id": self.account_id,
            "log_group_count": len(self.cloudwatch_item.log_groups),
            "compliance_framework": "NIST800-53R5",
        }
        file_handle.write(json.dumps(metadata) + "\n")

    def _write_compliance_summary(self, file_handle, compliance_results: Dict[str, Any]) -> None:
        """Write compliance summary to evidence file."""
        summary = {"type": "compliance_summary", "results": compliance_results["overall"]}
        file_handle.write(json.dumps(summary) + "\n")

    def _write_log_group_configurations(self, file_handle) -> None:
        """Write log group configuration records to evidence file."""
        for log_group in self.cloudwatch_item.log_groups:
            log_group_record = self._build_log_group_record(log_group)
            file_handle.write(json.dumps(log_group_record, default=str) + "\n")

    def _build_log_group_record(self, log_group: Dict[str, Any]) -> Dict[str, Any]:
        """Build log group configuration record for evidence file."""
        log_group_name = log_group.get("logGroupName", "")
        metrics = self.cloudwatch_item.log_group_metrics.get(log_group_name, {})

        return {
            "type": "log_group_configuration",
            "log_group_name": log_group_name,
            "log_group_arn": log_group.get("arn"),
            "creation_time": log_group.get("creationTime"),
            "retention_days": log_group.get("retentionInDays"),
            "stored_bytes": log_group.get("storedBytes", 0),
            "kms_key_id": log_group.get("kmsKeyId"),
            "metric_filter_count": metrics.get("MetricFilterCount", 0),
            "subscription_filter_count": metrics.get("SubscriptionFilterCount", 0),
            "metric_filters": log_group.get("MetricFilters", []),
            "subscription_filters": log_group.get("SubscriptionFilters", []),
            "tags": log_group.get("Tags", {}),
        }

    def _create_ssp_attachment_with_evidence(self, evidence_file_path: str) -> None:
        """
        Create SSP attachment with CloudWatch evidence.

        :param str evidence_file_path: Path to evidence file
        """
        try:
            date_str = datetime.now().strftime("%Y%m%d")
            file_name_pattern = f"cloudwatch_evidence_{self.region}_{date_str}"

            # Check if evidence for today already exists using base class method
            if self.check_for_existing_evidence(file_name_pattern):
                logger.info(
                    f"Evidence file for CloudWatch Logs in region {self.region} already exists for today. "
                    "Skipping upload to avoid duplicates."
                )
                return

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"cloudwatch_evidence_{self.region}_{timestamp}.jsonl.gz"

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
                tags="aws,cloudwatch,logs,monitoring,compliance,automated",
            )

            if success:
                logger.info(f"Successfully uploaded CloudWatch Logs evidence file: {file_name}")
                # Link to controls if specified
                if self.evidence_control_ids:
                    # Note: SSP attachments don't have IDs returned by upload_file_to_regscale
                    # This would need to be implemented if attachment-to-control linking is required
                    pass
            else:
                logger.error("Failed to upload CloudWatch Logs evidence file")

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
