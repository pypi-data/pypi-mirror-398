#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AWS S3 Evidence Integration for RegScale Compliance."""

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
from regscale.integrations.commercial.aws.inventory.resources.s3 import S3Collector
from regscale.integrations.commercial.aws.s3_control_mappings import S3ControlMapper
from regscale.integrations.compliance_integration import ComplianceIntegration
from regscale.models.regscale_models.evidence import Evidence
from regscale.models.regscale_models.evidence_mapping import EvidenceMapping
from regscale.models.regscale_models.file import File

logger = logging.getLogger("regscale")

# HTML formatting constants
HTML_UL_CLOSE = "</ul>"


@dataclass
class S3EvidenceConfig:
    """Configuration for AWS S3 evidence collection."""

    plan_id: int
    region: str = "us-east-1"
    framework: str = "NIST800-53R5"
    create_issues: bool = False
    update_control_status: bool = True
    create_poams: bool = False
    parent_module: str = "securityplans"
    account_id: Optional[str] = None
    tags: Optional[Dict[str, str]] = None
    bucket_name_filter: Optional[str] = None
    create_evidence: bool = False
    create_ssp_attachment: bool = True
    evidence_control_ids: Optional[List[str]] = None
    force_refresh: bool = False
    aws_profile: Optional[str] = None
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_session_token: Optional[str] = None


class S3ComplianceItem:
    """Represents S3 bucket configuration for compliance assessment."""

    def __init__(self, bucket_data: Dict[str, Any]):
        """
        Initialize S3 compliance item from bucket data.

        :param Dict bucket_data: Bucket configuration data from S3Collector
        """
        self.bucket_name = bucket_data.get("Name", "")
        self.region = bucket_data.get("Region", "")
        self.creation_date = bucket_data.get("CreationDate", "")
        self.encryption = bucket_data.get("Encryption", {})
        self.versioning = bucket_data.get("Versioning", {})
        self.public_access_block = bucket_data.get("PublicAccessBlock", {})
        self.policy_status = bucket_data.get("PolicyStatus", {})
        self.acl = bucket_data.get("ACL", {})
        self.logging = bucket_data.get("Logging", {})
        self.tags = bucket_data.get("Tags", [])
        self.raw_data = bucket_data

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return self.raw_data


class AWSS3EvidenceIntegration(ComplianceIntegration):
    """AWS S3 evidence integration for compliance data collection."""

    def __init__(self, config: S3EvidenceConfig):
        """
        Initialize AWS S3 evidence integration.

        :param S3EvidenceConfig config: Configuration object containing all parameters
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
        self.title = "AWS S3"
        self.account_id = config.account_id
        self.tags = config.tags or {}
        self.bucket_name_filter = config.bucket_name_filter
        self.create_evidence = config.create_evidence
        self.create_ssp_attachment = config.create_ssp_attachment
        self.evidence_control_ids = config.evidence_control_ids or []
        self.force_refresh = config.force_refresh

        # Initialize control mapper
        self.control_mapper = S3ControlMapper(framework=config.framework)

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
        self.cache_dir = Path(tempfile.gettempdir()) / "regscale" / "aws_s3_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Data storage
        self.raw_s3_data: Dict[str, Any] = {}
        self.buckets: List[S3ComplianceItem] = []

    def _get_cache_file_path(self) -> Path:
        """Get cache file path for S3 data."""
        cache_key = f"{self.region}_{self.account_id or 'default'}"
        return self.cache_dir / f"s3_buckets_{cache_key}.json"

    def _is_cache_valid(self) -> bool:
        """Check if cache is valid and not expired."""
        cache_file = self._get_cache_file_path()
        if not cache_file.exists():
            return False

        cache_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
        return cache_age < timedelta(hours=self.cache_ttl_hours)

    def _save_cache(self, data: Dict[str, Any]) -> None:
        """Save S3 data to cache."""
        cache_file = self._get_cache_file_path()
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, default=str)
            logger.debug(f"Saved S3 data to cache: {cache_file}")
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")

    def _load_cached_data(self) -> Optional[List[Dict[str, Any]]]:
        """Load S3 data from cache."""
        cache_file = self._get_cache_file_path()
        try:
            with open(cache_file, encoding="utf-8") as f:
                data = json.load(f)

            # Validate cache format - must be a list of dicts
            if not isinstance(data, list):
                logger.warning("Invalid cache format detected (not a list). Invalidating cache.")
                return None

            # Check if first item is a dict (bucket configuration)
            if data and not isinstance(data[0], dict):
                logger.warning("Invalid cache format detected (items not dicts). Invalidating cache.")
                return None

            logger.info(f"Loaded S3 data from cache (age: {self._get_cache_age_hours():.1f} hours)")
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
        Fetch S3 bucket configuration data from AWS.

        :return: List of bucket configurations
        :rtype: List[Dict[str, Any]]
        """
        # Check cache first
        if not self.force_refresh and self._is_cache_valid():
            cached_data = self._load_cached_data()
            if cached_data:
                return cached_data

        # Fetch fresh data
        return self._fetch_fresh_s3_data()

    def _fetch_fresh_s3_data(self) -> List[Dict[str, Any]]:
        """
        Fetch fresh S3 bucket data from AWS API.

        :return: List of bucket configurations
        :rtype: List[Dict[str, Any]]
        """
        logger.info(f"Fetching S3 bucket configurations from AWS region: {self.region}")

        # Initialize AWS session
        if not self.session:
            self._initialize_aws_session()

        # Create S3 collector
        self.collector = S3Collector(
            session=self.session, region=self.region, account_id=self.account_id, tags=self.tags
        )

        # Collect S3 data
        self.raw_s3_data = self.collector.collect()
        buckets = self.raw_s3_data.get("Buckets", [])

        # Apply bucket name filter if specified
        if self.bucket_name_filter:
            buckets = [b for b in buckets if self.bucket_name_filter in b.get("Name", "")]
            logger.info(f"Applied bucket name filter '{self.bucket_name_filter}': {len(buckets)} buckets match")

        logger.info(f"Collected {len(buckets)} S3 bucket(s) from region {self.region}")

        # Save to cache
        self._save_cache(buckets)

        return buckets

    def sync_compliance_data(self) -> None:
        """Sync S3 compliance data to RegScale."""
        logger.info("Starting AWS S3 compliance data sync to RegScale")

        # Fetch bucket data
        bucket_data = self.fetch_compliance_data()
        if not bucket_data:
            logger.warning("No S3 bucket data to sync")
            return

        # Convert to compliance items
        self.buckets = [S3ComplianceItem(bucket) for bucket in bucket_data]
        logger.info(f"Processing {len(self.buckets)} S3 bucket(s) for compliance assessment")

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

        logger.info("AWS S3 compliance sync completed successfully")

    def create_compliance_item(self, raw_data: Dict[str, Any]):
        """
        Create a ComplianceItem from raw S3 bucket data.

        :param Dict[str, Any] raw_data: Raw S3 bucket data
        :return: S3ComplianceItem instance
        :rtype: S3ComplianceItem
        """
        return S3ComplianceItem(raw_data)

    def _assess_compliance(self) -> Dict[str, Any]:
        """
        Assess S3 compliance against NIST controls.

        :return: Compliance assessment results
        :rtype: Dict[str, Any]
        """
        logger.info("Assessing S3 compliance against NIST 800-53 R5 controls")

        # Assess each bucket individually
        bucket_assessments = []
        for bucket_item in self.buckets:
            bucket_result = self.control_mapper.assess_bucket_compliance(bucket_item.to_dict())
            bucket_assessments.append({"bucket_name": bucket_item.bucket_name, "controls": bucket_result})

        # Get overall compliance results
        bucket_dicts = [b.to_dict() for b in self.buckets]
        overall_results = self.control_mapper.assess_all_buckets_compliance(bucket_dicts)

        # Log summary
        passed_controls = [ctrl for ctrl, result in overall_results.items() if result == "PASS"]
        failed_controls = [ctrl for ctrl, result in overall_results.items() if result == "FAIL"]

        logger.info("S3 Compliance Assessment Summary:")
        logger.info(f"  Total Buckets: {len(self.buckets)}")
        logger.info(f"  Controls Passed: {len(passed_controls)} - {', '.join(passed_controls)}")
        logger.info(f"  Controls Failed: {len(failed_controls)} - {', '.join(failed_controls)}")

        return {"overall": overall_results, "buckets": bucket_assessments}

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

            # Use first bucket as placeholder for the base class
            placeholder_item = self.buckets[0] if self.buckets else None
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
        logger.info("Creating S3 evidence artifacts in RegScale")

        # Create comprehensive evidence file
        evidence_file_path = self._create_evidence_file(compliance_results)

        if self.create_ssp_attachment:
            self._create_ssp_attachment_with_evidence(evidence_file_path)

        if self.create_evidence:
            self._create_evidence_records(evidence_file_path, compliance_results)

        # Clean up temporary file
        if os.path.exists(evidence_file_path):
            os.remove(evidence_file_path)
            logger.debug(f"Cleaned up temporary evidence file: {evidence_file_path}")

    def _create_evidence_file(self, compliance_results: Dict[str, Any]) -> str:
        """
        Create JSONL.GZ evidence file with S3 configuration data.

        :param Dict compliance_results: Compliance assessment results
        :return: Path to created evidence file
        :rtype: str
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        evidence_file = os.path.join(tempfile.gettempdir(), f"s3_evidence_{self.region}_{timestamp}.jsonl.gz")

        try:
            with gzip.open(evidence_file, "wt", encoding="utf-8") as f:
                # Write metadata
                metadata = {
                    "type": "metadata",
                    "timestamp": datetime.now().isoformat(),
                    "region": self.region,
                    "account_id": self.account_id,
                    "bucket_count": len(self.buckets),
                    "compliance_framework": "NIST800-53R5",
                }
                f.write(json.dumps(metadata) + "\n")

                # Write compliance summary
                summary = {"type": "compliance_summary", "results": compliance_results["overall"]}
                f.write(json.dumps(summary) + "\n")

                # Write bucket configurations
                for bucket_item in self.buckets:
                    bucket_record = {
                        "type": "bucket_configuration",
                        "bucket_name": bucket_item.bucket_name,
                        "region": bucket_item.region,
                        "encryption": bucket_item.encryption,
                        "versioning": bucket_item.versioning,
                        "public_access_block": bucket_item.public_access_block,
                        "policy_status": bucket_item.policy_status,
                        "acl": bucket_item.acl,
                        "logging": bucket_item.logging,
                        "tags": bucket_item.tags,
                    }
                    f.write(json.dumps(bucket_record, default=str) + "\n")

            logger.info(f"Created evidence file: {evidence_file}")
            return evidence_file

        except Exception as e:
            logger.error(f"Failed to create evidence file: {e}", exc_info=True)
            raise

    def _create_ssp_attachment_with_evidence(self, evidence_file_path: str) -> None:
        """
        Create SSP attachment with S3 evidence.

        :param str evidence_file_path: Path to evidence file
        """
        try:
            date_str = datetime.now().strftime("%Y%m%d")
            file_name_pattern = f"s3_evidence_{self.region}_{date_str}"

            # Check if evidence for today already exists using base class method
            if self.check_for_existing_evidence(file_name_pattern):
                logger.info(
                    f"Evidence file for S3 in region {self.region} already exists for today. "
                    "Skipping upload to avoid duplicates."
                )
                return

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"s3_evidence_{self.region}_{timestamp}.jsonl.gz"

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
                tags="aws,s3,storage,compliance,automated",
            )

            if success:
                logger.info(f"Successfully uploaded S3 evidence file: {file_name}")
            else:
                logger.error("Failed to upload S3 evidence file")

        except Exception as e:
            logger.error(f"Failed to create SSP attachment: {e}", exc_info=True)

    def _create_evidence_records(self, evidence_file_path: str, compliance_results: Dict[str, Any]) -> None:
        """
        Create evidence records in RegScale.

        :param str evidence_file_path: Path to evidence file
        :param Dict compliance_results: Compliance assessment results
        """
        try:
            description = self._build_evidence_description(compliance_results)

            # Calculate due date (30 days from now as default)
            due_date = (datetime.now() + timedelta(days=30)).isoformat()

            # Create evidence record using Evidence model directly
            evidence = Evidence(
                title=f"AWS S3 Compliance Evidence - {self.region}",
                description=description,
                status="Collected",
                updateFrequency=30,
                dueDate=due_date,
            )

            created_evidence = evidence.create()
            if not created_evidence or not created_evidence.id:
                logger.error("Failed to create evidence record")
                return

            logger.info(f"Created evidence record: {created_evidence.id}")

            # Upload evidence file
            self._upload_evidence_file(created_evidence.id, evidence_file_path)

            # Link evidence to SSP
            self._link_evidence_to_ssp(created_evidence.id)

            # Link to controls if specified
            if self.evidence_control_ids:
                self._link_evidence_to_controls(created_evidence.id, is_attachment=False)

        except Exception as e:
            logger.error(f"Failed to create evidence record: {e}", exc_info=True)

    def _upload_evidence_file(self, evidence_id: int, file_path: str) -> None:
        """
        Upload evidence file to RegScale.

        :param int evidence_id: Evidence record ID
        :param str file_path: Path to evidence file
        """
        try:
            # Read the compressed file
            with open(file_path, "rb") as f:
                file_data = f.read()

            # Generate filename from the path
            file_name = os.path.basename(file_path)

            # Upload file to Evidence record
            success = File.upload_file_to_regscale(
                file_name=file_name,
                parent_id=evidence_id,
                parent_module="evidence",
                api=self.api,
                file_data=file_data,
                tags="aws,s3,storage,compliance,automated",
            )

            if success:
                logger.info(f"Uploaded evidence file for evidence ID: {evidence_id}")
            else:
                logger.warning(f"Failed to upload evidence file for evidence ID: {evidence_id}")
        except Exception as e:
            logger.error(f"Failed to upload evidence file: {e}", exc_info=True)

    def _link_evidence_to_ssp(self, evidence_id: int) -> None:
        """
        Link evidence to Security Plan.

        :param int evidence_id: Evidence record ID
        :return: None
        :rtype: None
        """
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

    def _build_evidence_description(self, compliance_results: Dict[str, Any]) -> str:
        """
        Build HTML-formatted evidence description.

        :param Dict compliance_results: Compliance assessment results
        :return: HTML description
        :rtype: str
        """
        overall_results = compliance_results.get("overall", {})
        passed_controls = [ctrl for ctrl, result in overall_results.items() if result == "PASS"]
        failed_controls = [ctrl for ctrl, result in overall_results.items() if result == "FAIL"]

        desc_parts = [
            "<h3>AWS S3 Storage Configuration Evidence</h3>",
            f"<p><strong>Region:</strong> {self.region}</p>",
            f"<p><strong>Account ID:</strong> {self.account_id or 'N/A'}</p>",
            f"<p><strong>Collection Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>",
            f"<p><strong>Total Buckets:</strong> {len(self.buckets)}</p>",
            "<h4>Compliance Summary</h4>",
            f"<p><strong>Controls Passed:</strong> {len(passed_controls)}</p>",
            "<ul>",
        ]

        for control in passed_controls:
            control_desc = self.control_mapper.get_control_description(control)
            desc_parts.append(f"<li>{control}: {control_desc}</li>")

        desc_parts.append(HTML_UL_CLOSE)

        if failed_controls:
            desc_parts.append(f"<p><strong>Controls Failed:</strong> {len(failed_controls)}</p>")
            desc_parts.append("<ul>")
            for control in failed_controls:
                control_desc = self.control_mapper.get_control_description(control)
                desc_parts.append(f"<li>{control}: {control_desc}</li>")
            desc_parts.append(HTML_UL_CLOSE)

        desc_parts.extend(
            [
                "<h4>Bucket Configurations</h4>",
                "<ul>",
            ]
        )

        for bucket_item in self.buckets[:10]:  # Limit to first 10 for description
            encryption_status = "Enabled" if bucket_item.encryption.get("Enabled") else "Disabled"
            versioning_status = bucket_item.versioning.get("Status", "Disabled")
            desc_parts.append(
                f"<li><strong>{bucket_item.bucket_name}</strong>: "
                f"Encryption={encryption_status}, Versioning={versioning_status}</li>"
            )

        if len(self.buckets) > 10:
            desc_parts.append(f"<li><em>... and {len(self.buckets) - 10} more buckets</em></li>")

        desc_parts.append(HTML_UL_CLOSE)
        desc_parts.append("<p><em>Complete configuration data available in attached evidence file.</em></p>")

        return "".join(desc_parts)
