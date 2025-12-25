#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AWS CloudTrail Evidence Integration for RegScale Compliance."""

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
from regscale.integrations.commercial.aws.cloudtrail_control_mappings import CloudTrailControlMapper
from regscale.integrations.commercial.aws.inventory.resources.cloudtrail import CloudTrailCollector
from regscale.integrations.compliance_integration import ComplianceIntegration
from regscale.models.regscale_models.file import File

logger = logging.getLogger("regscale")


@dataclass
class CloudTrailEvidenceConfig:
    """Configuration for AWS CloudTrail evidence collection."""

    plan_id: int
    region: str = "us-east-1"
    framework: str = "NIST800-53R5"
    create_issues: bool = False
    update_control_status: bool = True
    create_poams: bool = False
    parent_module: str = "securityplans"
    account_id: Optional[str] = None
    tags: Optional[Dict[str, str]] = None
    trail_name_filter: Optional[str] = None
    create_evidence: bool = False
    create_ssp_attachment: bool = True
    evidence_control_ids: Optional[List[str]] = None
    force_refresh: bool = False
    aws_profile: Optional[str] = None
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_session_token: Optional[str] = None


class CloudTrailComplianceItem:
    """Represents CloudTrail trail configuration for compliance assessment."""

    def __init__(self, trail_data: Dict[str, Any]):
        """
        Initialize CloudTrail compliance item from trail data.

        :param Dict trail_data: Trail configuration data from CloudTrailCollector
        """
        self.trail_name = trail_data.get("Name", "")
        self.trail_arn = trail_data.get("TrailARN", "")
        self.s3_bucket_name = trail_data.get("S3BucketName", "")
        self.is_multi_region = trail_data.get("IsMultiRegionTrail", False)
        self.is_organization_trail = trail_data.get("IsOrganizationTrail", False)
        self.log_file_validation_enabled = trail_data.get("LogFileValidationEnabled", False)
        self.kms_key_id = trail_data.get("KmsKeyId")
        self.cloud_watch_logs_log_group_arn = trail_data.get("CloudWatchLogsLogGroupArn")
        self.sns_topic_arn = trail_data.get("SnsTopicARN")
        self.status = trail_data.get("Status", {})
        self.event_selectors = trail_data.get("EventSelectors", [])
        self.tags = trail_data.get("Tags", {})
        self.region = trail_data.get("Region", "")
        self.raw_data = trail_data

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return self.raw_data


class AWSCloudTrailEvidenceIntegration(ComplianceIntegration):
    """AWS CloudTrail evidence integration for compliance data collection."""

    def __init__(self, config: CloudTrailEvidenceConfig):
        """
        Initialize AWS CloudTrail evidence integration.

        :param CloudTrailEvidenceConfig config: Configuration object containing all parameters
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
        self.title = "AWS CloudTrail"
        self.account_id = config.account_id
        self.tags = config.tags or {}
        self.trail_name_filter = config.trail_name_filter
        self.create_evidence = config.create_evidence
        self.create_ssp_attachment = config.create_ssp_attachment
        self.evidence_control_ids = config.evidence_control_ids or []
        self.force_refresh = config.force_refresh

        # Initialize control mapper
        self.control_mapper = CloudTrailControlMapper(framework=config.framework)

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
        self.cache_dir = Path(tempfile.gettempdir()) / "regscale" / "aws_cloudtrail_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Data storage
        self.raw_cloudtrail_data: Dict[str, Any] = {}
        self.trails: List[CloudTrailComplianceItem] = []

    def _get_cache_file_path(self) -> Path:
        """Get cache file path for CloudTrail data."""
        cache_key = f"{self.region}_{self.account_id or 'default'}"
        return self.cache_dir / f"cloudtrail_trails_{cache_key}.json"

    def _is_cache_valid(self) -> bool:
        """Check if cache is valid and not expired."""
        cache_file = self._get_cache_file_path()
        if not cache_file.exists():
            return False

        cache_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
        return cache_age < timedelta(hours=self.cache_ttl_hours)

    def _save_cache(self, data: Dict[str, Any]) -> None:
        """Save CloudTrail data to cache."""
        cache_file = self._get_cache_file_path()
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, default=str)
            logger.debug(f"Saved CloudTrail data to cache: {cache_file}")
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")

    def _load_cached_data(self) -> Optional[List[Dict[str, Any]]]:
        """Load CloudTrail data from cache."""
        cache_file = self._get_cache_file_path()
        try:
            with open(cache_file, encoding="utf-8") as f:
                data = json.load(f)

            # Validate cache format - must be a list of dicts
            if not isinstance(data, list):
                logger.warning("Invalid cache format detected (not a list). Invalidating cache.")
                return None

            # Check if first item is a dict (trail configuration)
            if data and not isinstance(data[0], dict):
                logger.warning("Invalid cache format detected (items not dicts). Invalidating cache.")
                return None

            logger.info(f"Loaded CloudTrail data from cache (age: {self._get_cache_age_hours():.1f} hours)")
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

    def fetch_compliance_data(self) -> List[Dict[str, Any]]:
        """
        Fetch CloudTrail trail configuration data from AWS.

        :return: List of trail configurations
        :rtype: List[Dict[str, Any]]
        """
        # Check cache first
        if not self.force_refresh and self._is_cache_valid():
            cached_data = self._load_cached_data()
            if cached_data:
                return cached_data

        # Fetch fresh data
        return self._fetch_fresh_cloudtrail_data()

    def _fetch_fresh_cloudtrail_data(self) -> List[Dict[str, Any]]:
        """
        Fetch fresh CloudTrail trail data from AWS API.

        :return: List of trail configurations
        :rtype: List[Dict[str, Any]]
        """
        logger.info(f"Fetching CloudTrail trail configurations from AWS region: {self.region}")

        # Initialize AWS session
        if not self.session:
            self._initialize_aws_session()

        # Create CloudTrail collector
        self.collector = CloudTrailCollector(
            session=self.session, region=self.region, account_id=self.account_id, tags=self.tags
        )

        # Collect CloudTrail data
        self.raw_cloudtrail_data = self.collector.collect()
        trails = self.raw_cloudtrail_data.get("Trails", [])

        # Apply trail name filter if specified
        if self.trail_name_filter:
            trails = [t for t in trails if self.trail_name_filter in t.get("Name", "")]
            logger.info(f"Applied trail name filter '{self.trail_name_filter}': {len(trails)} trails match")

        logger.info(f"Collected {len(trails)} CloudTrail trail(s) from region {self.region}")

        # Save to cache
        self._save_cache(trails)

        return trails

    def sync_compliance_data(self) -> None:
        """Sync CloudTrail compliance data to RegScale."""
        logger.info("Starting AWS CloudTrail compliance data sync to RegScale")

        # Fetch trail data
        trail_data = self.fetch_compliance_data()
        if not trail_data:
            logger.warning("No CloudTrail trail data to sync")
            return

        # Convert to compliance items
        self.trails = [CloudTrailComplianceItem(trail) for trail in trail_data]
        logger.info(f"Processing {len(self.trails)} CloudTrail trail(s) for compliance assessment")

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

        logger.info("AWS CloudTrail compliance sync completed successfully")

    def create_compliance_item(self, raw_data: Dict[str, Any]):
        """
        Create a ComplianceItem from raw CloudTrail trail data.

        :param Dict[str, Any] raw_data: Raw CloudTrail trail data
        :return: CloudTrailComplianceItem instance
        :rtype: CloudTrailComplianceItem
        """
        return CloudTrailComplianceItem(raw_data)

    def _assess_compliance(self) -> Dict[str, Any]:
        """
        Assess CloudTrail compliance against NIST controls.

        :return: Compliance assessment results
        :rtype: Dict[str, Any]
        """
        logger.info("Assessing CloudTrail compliance against NIST 800-53 R5 controls")

        # Assess each trail individually
        trail_assessments = []
        for trail_item in self.trails:
            trail_result = self.control_mapper.assess_trail_compliance(trail_item.to_dict())
            trail_assessments.append({"trail_name": trail_item.trail_name, "controls": trail_result})

        # Get overall compliance results
        trail_dicts = [t.to_dict() for t in self.trails]
        overall_results = self.control_mapper.assess_all_trails_compliance(trail_dicts)

        # Log summary
        passed_controls = [ctrl for ctrl, result in overall_results.items() if result == "PASS"]
        failed_controls = [ctrl for ctrl, result in overall_results.items() if result == "FAIL"]

        logger.info("CloudTrail Compliance Assessment Summary:")
        logger.info(f"  Total Trails: {len(self.trails)}")
        logger.info(f"  Controls Passed: {len(passed_controls)} - {', '.join(passed_controls)}")
        logger.info(f"  Controls Failed: {len(failed_controls)} - {', '.join(failed_controls)}")

        return {"overall": overall_results, "trails": trail_assessments}

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

            # Use first trail as placeholder for the base class
            placeholder_item = self.trails[0] if self.trails else None
            if not placeholder_item:
                continue

            # Create a simple compliance item placeholder for the base class
            if result in self.PASS_STATUSES:
                self.passing_controls[control_key] = placeholder_item
            elif result in self.FAIL_STATUSES:
                self.failing_controls[control_key] = placeholder_item

        logger.debug(
            f"Populated control results: {len(self.passing_controls)} passing, {len(self.failing_controls)} failing"
        )

    def _create_evidence_artifacts(self, compliance_results: Dict[str, Any]) -> None:
        """
        Create evidence artifacts in RegScale.

        :param Dict compliance_results: Compliance assessment results
        """
        logger.info("Creating CloudTrail evidence artifacts in RegScale")

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
        Create JSONL.GZ evidence file with CloudTrail configuration data.

        :param Dict compliance_results: Compliance assessment results
        :return: Path to created evidence file
        :rtype: str
        """
        evidence_file = self._get_evidence_file_path()

        try:
            with gzip.open(evidence_file, "wt", encoding="utf-8") as f:
                self._write_metadata(f)
                self._write_compliance_summary(f, compliance_results)
                self._write_trail_configurations(f)

            logger.info(f"Created evidence file: {evidence_file}")
            return evidence_file

        except Exception as e:
            logger.error(f"Failed to create evidence file: {e}", exc_info=True)
            raise

    def _get_evidence_file_path(self) -> str:
        """Generate evidence file path with timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return os.path.join(tempfile.gettempdir(), f"cloudtrail_evidence_{self.region}_{timestamp}.jsonl.gz")

    def _write_metadata(self, file_handle) -> None:
        """Write metadata record to evidence file."""
        metadata = {
            "type": "metadata",
            "timestamp": datetime.now().isoformat(),
            "region": self.region,
            "account_id": self.account_id,
            "trail_count": len(self.trails),
            "compliance_framework": "NIST800-53R5",
        }
        file_handle.write(json.dumps(metadata) + "\n")

    def _write_compliance_summary(self, file_handle, compliance_results: Dict[str, Any]) -> None:
        """Write compliance summary to evidence file."""
        summary = {"type": "compliance_summary", "results": compliance_results["overall"]}
        file_handle.write(json.dumps(summary) + "\n")

    def _write_trail_configurations(self, file_handle) -> None:
        """Write trail configuration records to evidence file."""
        for trail_item in self.trails:
            trail_record = self._build_trail_record(trail_item)
            file_handle.write(json.dumps(trail_record, default=str) + "\n")

    def _build_trail_record(self, trail_item: CloudTrailComplianceItem) -> Dict[str, Any]:
        """Build trail configuration record for evidence file."""
        return {
            "type": "trail_configuration",
            "trail_name": trail_item.trail_name,
            "trail_arn": trail_item.trail_arn,
            "s3_bucket": trail_item.s3_bucket_name,
            "multi_region": trail_item.is_multi_region,
            "organization_trail": trail_item.is_organization_trail,
            "log_validation": trail_item.log_file_validation_enabled,
            "kms_encryption": bool(trail_item.kms_key_id),
            "cloudwatch_logs": bool(trail_item.cloud_watch_logs_log_group_arn),
            "sns_notifications": bool(trail_item.sns_topic_arn),
            "status": trail_item.status,
            "event_selectors": trail_item.event_selectors,
            "tags": trail_item.tags,
        }

    def _create_ssp_attachment_with_evidence(self, evidence_file_path: str) -> None:
        """
        Create SSP attachment with CloudTrail evidence.

        :param str evidence_file_path: Path to evidence file
        """
        try:
            date_str = datetime.now().strftime("%Y%m%d")
            file_name_pattern = f"cloudtrail_evidence_{self.region}_{date_str}"

            # Check if evidence for today already exists using base class method
            if self.check_for_existing_evidence(file_name_pattern):
                logger.info(
                    f"Evidence file for CloudTrail in region {self.region} already exists for today. "
                    "Skipping upload to avoid duplicates."
                )
                return

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"cloudtrail_evidence_{self.region}_{timestamp}.jsonl.gz"

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
                tags="aws,cloudtrail,audit,logging,compliance,automated",
            )

            if success:
                logger.info(f"Successfully uploaded CloudTrail evidence file: {file_name}")
                # Link to controls if specified
                if self.evidence_control_ids:
                    # Note: SSP attachments don't have IDs returned by upload_file_to_regscale
                    # This would need to be implemented if attachment-to-control linking is required
                    pass
            else:
                logger.error("Failed to upload CloudTrail evidence file")

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
