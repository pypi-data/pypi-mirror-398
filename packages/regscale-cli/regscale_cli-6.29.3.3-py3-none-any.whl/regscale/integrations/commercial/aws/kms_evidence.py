#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AWS KMS Evidence Integration for RegScale CLI."""

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
from regscale.integrations.commercial.aws.kms_control_mappings import KMSControlMapper
from regscale.integrations.compliance_integration import ComplianceIntegration, ComplianceItem
from regscale.models import regscale_models
from regscale.models.regscale_models.evidence import Evidence
from regscale.models.regscale_models.evidence_mapping import EvidenceMapping
from regscale.models.regscale_models.file import File

logger = logging.getLogger("regscale")

# Constants for file paths and cache TTL
KMS_CACHE_FILE = os.path.join("artifacts", "aws", "kms_data.json")
CACHE_TTL_SECONDS = 4 * 60 * 60  # 4 hours in seconds

# HTML tag constants to avoid duplication
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
class KMSEvidenceConfig:
    """Configuration for AWS KMS evidence collection."""

    plan_id: int
    region: str = "us-east-1"
    framework: str = "NIST800-53R5"
    create_issues: bool = True
    update_control_status: bool = True
    create_poams: bool = False
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


class KMSComplianceItem(ComplianceItem):
    """
    Compliance item representing a single KMS key assessment.

    Maps KMS key attributes to compliance control requirements.
    """

    def __init__(self, key_data: Dict[str, Any], control_mapper: KMSControlMapper):
        """
        Initialize KMS compliance item from key data.

        :param Dict[str, Any] key_data: KMS key metadata and attributes
        :param KMSControlMapper control_mapper: Control mapper for compliance assessment
        """
        self.key_data = key_data
        self.control_mapper = control_mapper

        # Extract key attributes
        self._key_id = key_data.get("KeyId", "")
        self._key_arn = key_data.get("Arn", "")
        self._key_state = key_data.get("KeyState", "Unknown")
        self._rotation_enabled = key_data.get("RotationEnabled", False)
        self._key_manager = key_data.get("KeyManager", "CUSTOMER")
        self._description = key_data.get("Description", "")
        self._tags = key_data.get("Tags", [])

        # Assess compliance for all mapped controls
        self._compliance_results = control_mapper.assess_key_compliance(key_data)

        # Extract region and account from ARN
        self._region = self._extract_region_from_arn(self._key_arn)
        self._account_id = self._extract_account_from_arn(self._key_arn)

    @property
    def resource_id(self) -> str:
        """Unique identifier for the KMS key."""
        return self._key_id

    @property
    def resource_name(self) -> str:
        """Human-readable name of the KMS key."""
        # Try to get alias from tags or description
        for tag in self._tags:
            if tag.get("TagKey") == "Name":
                return f"{tag.get('TagValue')} ({self._key_id[:8]}...)"

        if self._description:
            return f"{self._description[:50]} ({self._key_id[:8]}...)"

        return f"KMS Key {self._key_id[:12]}..."

    @property
    def control_id(self) -> str:
        """
        Primary control identifier for this key assessment.

        Returns the first failing control, or first passing control if all pass.
        """
        # Return first failing control for issue creation
        for control_id, result in self._compliance_results.items():
            if result == "FAIL":
                return control_id

        # If all pass, return first control
        return list(self._compliance_results.keys())[0] if self._compliance_results else "SC-12"

    @property
    def compliance_result(self) -> str:
        """
        Overall compliance result for this key.

        Returns FAIL if any control fails, PASS if all pass.
        """
        if not self._compliance_results:
            return "PASS"

        # If ANY control fails, the key fails overall
        if "FAIL" in self._compliance_results.values():
            return "FAIL"

        return "PASS"

    @property
    def severity(self) -> Optional[str]:
        """Severity level based on which controls are failing."""
        if self.compliance_result == "PASS":
            return None

        # SC-12 failures (rotation) are HIGH severity
        if self._compliance_results.get("SC-12") == "FAIL":
            return "HIGH"

        # SC-13 failures (crypto protection) are MEDIUM severity
        if self._compliance_results.get("SC-13") == "FAIL":
            return "MEDIUM"

        # SC-28 failures (data at rest) are MEDIUM severity
        if self._compliance_results.get("SC-28") == "FAIL":
            return "MEDIUM"

        return "MEDIUM"

    @property
    def description(self) -> str:
        """Detailed description of the KMS key compliance assessment."""
        desc_parts = self._build_key_details()

        if self._description:
            desc_parts.extend(self._build_description_section())

        desc_parts.extend(self._build_compliance_results_section())

        if self.compliance_result == "FAIL":
            desc_parts.extend(self._build_remediation_section())

        return "\n".join(desc_parts)

    def _build_key_details(self) -> List[str]:
        """Build the key details section of the description."""
        rotation_status = "Yes" if self._rotation_enabled else "No"
        return [
            f"{HTML_H3_OPEN}AWS KMS Key Compliance Assessment{HTML_H3_CLOSE}",
            HTML_P_OPEN,
            f"{HTML_STRONG_OPEN}Key ID:{HTML_STRONG_CLOSE} {self._key_id}{HTML_BR}",
            f"{HTML_STRONG_OPEN}Key ARN:{HTML_STRONG_CLOSE} {self._key_arn}{HTML_BR}",
            f"{HTML_STRONG_OPEN}Key State:{HTML_STRONG_CLOSE} {self._key_state}{HTML_BR}",
            f"{HTML_STRONG_OPEN}Key Manager:{HTML_STRONG_CLOSE} {self._key_manager}{HTML_BR}",
            f"{HTML_STRONG_OPEN}Rotation Enabled:{HTML_STRONG_CLOSE} {rotation_status}{HTML_BR}",
            f"{HTML_STRONG_OPEN}Region:{HTML_STRONG_CLOSE} {self._region}",
            HTML_P_CLOSE,
        ]

    def _build_description_section(self) -> List[str]:
        """Build the optional description section."""
        return [
            HTML_P_OPEN,
            f"{HTML_STRONG_OPEN}Description:{HTML_STRONG_CLOSE} {self._description}",
            HTML_P_CLOSE,
        ]

    def _build_compliance_results_section(self) -> List[str]:
        """Build the compliance results section."""
        section_parts = [
            f"{HTML_H3_OPEN}Control Compliance Results{HTML_H3_CLOSE}",
            HTML_UL_OPEN,
        ]

        for control_id, result in self._compliance_results.items():
            result_item = self._format_compliance_result(control_id, result)
            section_parts.append(result_item)

        section_parts.append(HTML_UL_CLOSE)
        return section_parts

    def _format_compliance_result(self, control_id: str, result: str) -> str:
        """Format a single compliance result item."""
        result_color = "#d32f2f" if result == "FAIL" else "#2e7d32"
        control_desc = self.control_mapper.get_control_description(control_id)
        return (
            f"{HTML_LI_OPEN}{HTML_STRONG_OPEN}{control_id}:{HTML_STRONG_CLOSE} "
            f"<span style='color: {result_color};'>{result}</span> - {control_desc}{HTML_LI_CLOSE}"
        )

    def _build_remediation_section(self) -> List[str]:
        """Build remediation guidance for failed controls."""
        section_parts = [
            f"{HTML_H3_OPEN}Remediation Guidance{HTML_H3_CLOSE}",
            HTML_UL_OPEN,
        ]

        section_parts.extend(self._get_sc12_remediation())
        section_parts.extend(self._get_sc13_remediation())
        section_parts.extend(self._get_sc28_remediation())

        section_parts.append(HTML_UL_CLOSE)
        return section_parts

    def _get_sc12_remediation(self) -> List[str]:
        """Get remediation steps for SC-12 control failures."""
        items = []
        if self._compliance_results.get("SC-12") == "FAIL":
            if not self._rotation_enabled and self._key_manager == "CUSTOMER":
                items.append(
                    f"{HTML_LI_OPEN}Enable automatic key rotation for this customer-managed key{HTML_LI_CLOSE}"
                )
            if self._key_state in ["PendingDeletion", "Disabled"]:
                items.append(f"{HTML_LI_OPEN}Key is {self._key_state} - review key lifecycle{HTML_LI_CLOSE}")
        return items

    def _get_sc13_remediation(self) -> List[str]:
        """Get remediation steps for SC-13 control failures."""
        items = []
        if self._compliance_results.get("SC-13") == "FAIL":
            key_spec = self.key_data.get("KeySpec", "Unknown")
            items.append(
                f"{HTML_LI_OPEN}Review key specification ({key_spec}) - ensure FIPS-validated "
                f"algorithms are used{HTML_LI_CLOSE}"
            )
        return items

    def _get_sc28_remediation(self) -> List[str]:
        """Get remediation steps for SC-28 control failures."""
        items = []
        if self._compliance_results.get("SC-28") == "FAIL":
            items.append(
                f"{HTML_LI_OPEN}Ensure key is enabled and available for data-at-rest encryption{HTML_LI_CLOSE}"
            )
        return items

    @property
    def framework(self) -> str:
        """Compliance framework used for assessment."""
        return self.control_mapper.framework

    @staticmethod
    def _extract_region_from_arn(arn: str) -> str:
        """Extract AWS region from KMS key ARN."""
        try:
            # ARN format: arn:aws:kms:region:account:key/key-id
            return arn.split(":")[3]
        except (IndexError, AttributeError):
            return "unknown"

    @staticmethod
    def _extract_account_from_arn(arn: str) -> str:
        """Extract AWS account ID from KMS key ARN."""
        try:
            # ARN format: arn:aws:kms:region:account:key/key-id
            return arn.split(":")[4]
        except (IndexError, AttributeError):
            return "unknown"


class AWSKMSEvidenceIntegration(ComplianceIntegration):
    """Process AWS KMS key data and create evidence/compliance records in RegScale."""

    def __init__(self, config: KMSEvidenceConfig):
        """
        Initialize AWS KMS evidence integration.

        :param KMSEvidenceConfig config: Configuration object containing all parameters
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
        self.title = "AWS KMS"
        self.framework = config.framework

        # Evidence collection parameters
        self.collect_evidence = config.collect_evidence
        self.evidence_as_attachments = config.evidence_as_attachments
        self.evidence_control_ids = config.evidence_control_ids
        self.evidence_frequency = config.evidence_frequency

        # Cache control
        self.force_refresh = config.force_refresh

        # Filtering parameters
        self.account_id = config.account_id
        self.tags = config.tags or {}

        # Initialize control mapper
        self.control_mapper = KMSControlMapper(framework=config.framework)

        # Extract AWS credentials from config
        profile = config.profile
        aws_access_key_id = config.aws_access_key_id
        aws_secret_access_key = config.aws_secret_access_key
        aws_session_token = config.aws_session_token

        # INFO-level logging for credential resolution
        if aws_access_key_id and aws_secret_access_key:
            logger.info("Initializing AWS KMS client with explicit credentials")
            self.session = boto3.Session(
                region_name=config.region,
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                aws_session_token=aws_session_token,
            )
        else:
            logger.info(f"Initializing AWS KMS client with profile: {profile if profile else 'default'}")
            self.session = boto3.Session(profile_name=profile, region_name=config.region)

        try:
            self.client = self.session.client("kms")
            logger.info("Successfully created AWS KMS client")
        except Exception as e:
            logger.error(f"Failed to create AWS KMS client: {e}")
            raise

        # Store raw KMS data for evidence generation
        self.raw_kms_data: List[Dict[str, Any]] = []

    def _is_cache_valid(self) -> bool:
        """
        Check if the cache file exists and is within the TTL.

        :return: True if cache is valid, False otherwise
        :rtype: bool
        """
        if not os.path.exists(KMS_CACHE_FILE):
            logger.debug("Cache file does not exist")
            return False

        file_age = time.time() - os.path.getmtime(KMS_CACHE_FILE)
        is_valid = file_age < CACHE_TTL_SECONDS

        if is_valid:
            hours_old = file_age / 3600
            logger.info(f"Using cached KMS data (age: {hours_old:.1f} hours)")
        else:
            hours_old = file_age / 3600
            logger.debug(f"Cache expired (age: {hours_old:.1f} hours, TTL: {CACHE_TTL_SECONDS / 3600} hours)")

        return is_valid

    def _load_cached_data(self) -> List[Dict[str, Any]]:
        """
        Load KMS data from cache file.

        :return: List of raw KMS key data from cache
        :rtype: List[Dict[str, Any]]
        """
        try:
            with open(KMS_CACHE_FILE, encoding="utf-8") as file:
                cached_data = json.load(file)

            # Validate cache format - must be a list
            if not isinstance(cached_data, list):
                logger.warning("Invalid cache format detected (not a list). Invalidating cache.")
                return []

            # Check if items are dicts
            if cached_data and not isinstance(cached_data[0], dict):
                logger.warning("Invalid cache format detected (items not dicts). Invalidating cache.")
                return []

            logger.info(f"Loaded {len(cached_data)} KMS keys from cache")
            return cached_data
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Error reading cache file: {e}. Fetching fresh data.")
            return []

    def _save_to_cache(self, kms_data: List[Dict[str, Any]]) -> None:
        """
        Save KMS data to cache file.

        :param List[Dict[str, Any]] kms_data: Data to cache
        :return: None
        :rtype: None
        """
        try:
            # Ensure the artifacts directory exists
            os.makedirs(os.path.dirname(KMS_CACHE_FILE), exist_ok=True)

            with open(KMS_CACHE_FILE, "w", encoding="utf-8") as file:
                json.dump(kms_data, file, indent=2, default=str)

            logger.info(f"Cached {len(kms_data)} KMS keys to {KMS_CACHE_FILE}")
        except IOError as e:
            logger.warning(f"Error writing to cache file: {e}")

    def _fetch_fresh_kms_data(self) -> List[Dict[str, Any]]:
        """
        Fetch fresh KMS data from AWS.

        :return: List of KMS key data
        :rtype: List[Dict[str, Any]]
        """
        logger.info("Fetching KMS data from AWS...")

        # Log filtering parameters
        if self.account_id:
            logger.info(f"Filtering KMS keys by account ID: {self.account_id}")
        if self.tags:
            logger.info(f"Filtering KMS keys by tags: {self.tags}")

        # Use inventory collector for consistency
        from regscale.integrations.commercial.aws.inventory.resources.kms import KMSCollector

        collector = KMSCollector(session=self.session, region=self.region, account_id=self.account_id, tags=self.tags)

        inventory = collector.collect()
        keys = inventory.get("Keys", [])

        logger.info(f"Fetched {len(keys)} KMS keys from AWS (after filtering)")
        return keys

    def fetch_compliance_data(self) -> List[Dict[str, Any]]:
        """
        Fetch raw KMS data from AWS.

        Uses cached data if available and not expired (4-hour TTL), unless force_refresh is True.

        :return: List of raw KMS key data
        :rtype: List[Dict[str, Any]]
        """
        # Check if we should use cached data
        if not self.force_refresh and self._is_cache_valid():
            cached_data = self._load_cached_data()
            if cached_data:
                self.raw_kms_data = cached_data
                return cached_data

        # Force refresh requested or no valid cache, fetch fresh data from AWS
        if self.force_refresh:
            logger.info("Force refresh requested, bypassing cache and fetching fresh data from AWS KMS...")

        try:
            kms_data = self._fetch_fresh_kms_data()
            self.raw_kms_data = kms_data
            self._save_to_cache(kms_data)
            return kms_data
        except ClientError as e:
            logger.error(f"Error fetching KMS data from AWS: {e}")
            return []

    def create_compliance_item(self, raw_data: Dict[str, Any]) -> ComplianceItem:
        """
        Create a ComplianceItem from raw KMS key data.

        :param Dict[str, Any] raw_data: Raw KMS key data
        :return: KMSComplianceItem instance
        :rtype: ComplianceItem
        """
        return KMSComplianceItem(raw_data, self.control_mapper)

    def _map_resource_type_to_asset_type(self, compliance_item: ComplianceItem) -> str:
        """
        Map KMS key to RegScale asset type.

        :param ComplianceItem compliance_item: Compliance item
        :return: Asset type string
        :rtype: str
        """
        return "AWS KMS Key"

    def sync_compliance(self) -> None:
        """
        Main method to sync KMS compliance data.

        Extends base sync_compliance to add evidence collection support.

        :return: None
        :rtype: None
        """
        # Call the base class sync_compliance to handle control assessments and issues
        super().sync_compliance()

        # If evidence collection is enabled, collect evidence after compliance sync
        if self.collect_evidence:
            logger.info("Evidence collection enabled, starting evidence collection...")
            self._collect_kms_evidence()

    def _collect_kms_evidence(self) -> None:
        """
        Collect KMS evidence and create Evidence records or SSP attachments.

        :return: None
        :rtype: None
        """
        if not self.raw_kms_data:
            logger.warning("No KMS data available for evidence collection")
            return

        scan_date = get_current_datetime(dt_format="%Y-%m-%d %H:%M:%S")

        if self.evidence_as_attachments:
            logger.info("Creating SSP file attachment with KMS evidence...")
            self._create_ssp_attachment(scan_date)
        else:
            logger.info("Creating Evidence record with KMS evidence...")
            self._create_evidence_record(scan_date)

    def _create_ssp_attachment(self, scan_date: str) -> None:
        """
        Create SSP file attachment with KMS evidence data.

        :param str scan_date: Scan date string
        :return: None
        :rtype: None
        """
        try:
            # Check for existing evidence to avoid duplicates
            date_str = datetime.now().strftime("%Y%m%d")
            account_suffix = f"_{self.account_id}" if self.account_id else ""
            file_name_pattern = f"kms_evidence{account_suffix}_{date_str}"

            if self.check_for_existing_evidence(file_name_pattern):
                logger.info("Evidence file for KMS already exists for today. Skipping upload to avoid duplicates.")
                return

            # Add timestamp to make filename unique if run multiple times per day
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"kms_evidence{account_suffix}_{timestamp}.jsonl.gz"

            # Prepare JSONL content with compliance results
            jsonl_lines = []
            for key_data in self.raw_kms_data:
                compliance_item = self.create_compliance_item(key_data)
                evidence_entry = {
                    **key_data,
                    "compliance_assessment": {
                        "overall_result": compliance_item.compliance_result,
                        "control_results": compliance_item._compliance_results,
                        "assessed_controls": list(compliance_item._compliance_results.keys()),
                        "assessment_date": scan_date,
                    },
                }
                jsonl_lines.append(json.dumps(evidence_entry, default=str))

            jsonl_content = "\n".join(jsonl_lines)

            # Compress the JSONL content
            compressed_buffer = BytesIO()
            with gzip.open(compressed_buffer, "wt", encoding="utf-8", compresslevel=9) as gz_file:
                gz_file.write(jsonl_content)

            compressed_data = compressed_buffer.getvalue()
            compressed_size_mb = len(compressed_data) / (1024 * 1024)
            uncompressed_size_mb = len(jsonl_content.encode("utf-8")) / (1024 * 1024)
            compression_ratio = (1 - (len(compressed_data) / len(jsonl_content.encode("utf-8")))) * 100

            logger.info(
                "Compressed KMS evidence: %.2f MB -> %.2f MB (%.1f%% reduction)",
                uncompressed_size_mb,
                compressed_size_mb,
                compression_ratio,
            )

            # Upload to SSP
            api = Api()
            success = File.upload_file_to_regscale(
                file_name=file_name,
                parent_id=self.plan_id,
                parent_module=self.parent_module,
                api=api,
                file_data=compressed_data,
                tags="aws,kms,encryption,automated",
            )

            if success:
                logger.info(f"Successfully uploaded KMS evidence file to SSP {self.plan_id}: {file_name}")
            else:
                logger.error(f"Failed to upload KMS evidence file to SSP {self.plan_id}")

        except Exception as e:
            logger.error(f"Error creating SSP attachment for KMS evidence: {e}", exc_info=True)

    def _create_evidence_record(self, scan_date: str) -> None:
        """
        Create Evidence record with KMS evidence data.

        :param str scan_date: Scan date string
        :return: None
        :rtype: None
        """
        try:
            # Build evidence title and description
            title = f"AWS KMS Evidence - {scan_date}"
            description = self._build_evidence_description(scan_date)

            # Calculate due date
            due_date = (datetime.now() + timedelta(days=self.evidence_frequency)).isoformat()

            # Create Evidence record
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

            # Upload compressed evidence file
            self._upload_evidence_file(created_evidence.id, scan_date)

            # Link evidence to SSP
            self._link_evidence_to_ssp(created_evidence.id)

            # Link to controls if specified
            if self.evidence_control_ids:
                self._link_evidence_to_controls(created_evidence.id, is_attachment=False)

        except Exception as e:
            logger.error(f"Error creating evidence record for KMS: {e}", exc_info=True)

    def _build_evidence_description(self, scan_date: str) -> str:
        """
        Build HTML-formatted evidence description.

        :param str scan_date: Scan date string
        :return: HTML description
        :rtype: str
        """
        # Gather statistics
        kms_stats = self._calculate_kms_statistics()
        control_stats = self._calculate_control_compliance_stats()

        # Build description
        desc_parts = self._build_evidence_header(scan_date)
        desc_parts.extend(self._build_filter_info())
        desc_parts.extend(self._build_kms_summary(kms_stats))
        desc_parts.extend(self._build_control_compliance_summary(control_stats))

        return "\n".join(desc_parts)

    def _calculate_kms_statistics(self) -> Dict[str, Any]:
        """Calculate KMS key statistics."""
        total_keys = len(self.raw_kms_data)
        rotation_enabled_count = sum(1 for k in self.raw_kms_data if k.get("RotationEnabled", False))
        customer_managed_count = sum(1 for k in self.raw_kms_data if k.get("KeyManager") == "CUSTOMER")

        rotation_pct = rotation_enabled_count / max(total_keys, 1) * 100

        return {
            "total": total_keys,
            "rotation_enabled": rotation_enabled_count,
            "rotation_pct": rotation_pct,
            "customer_managed": customer_managed_count,
        }

    def _calculate_control_compliance_stats(self) -> Dict[str, Dict[str, int]]:
        """Calculate compliance statistics by control."""
        control_stats = {control_id: {"pass": 0, "fail": 0} for control_id in self.control_mapper.get_mapped_controls()}

        for key_data in self.raw_kms_data:
            compliance_item = self.create_compliance_item(key_data)
            self._update_control_stats(control_stats, compliance_item._compliance_results)

        return control_stats

    def _update_control_stats(
        self, control_stats: Dict[str, Dict[str, int]], compliance_results: Dict[str, str]
    ) -> None:
        """Update control statistics with compliance results."""
        for control_id, result in compliance_results.items():
            if result == "PASS":
                control_stats[control_id]["pass"] += 1
            else:
                control_stats[control_id]["fail"] += 1

    def _build_evidence_header(self, scan_date: str) -> List[str]:
        """Build the evidence header section."""
        return [
            "<h1>AWS KMS Evidence</h1>",
            f"{HTML_P_OPEN}{HTML_STRONG_OPEN}Assessment Date:{HTML_STRONG_CLOSE} {scan_date}{HTML_P_CLOSE}",
            f"{HTML_P_OPEN}{HTML_STRONG_OPEN}Region:{HTML_STRONG_CLOSE} {self.region}{HTML_P_CLOSE}",
        ]

    def _build_filter_info(self) -> List[str]:
        """Build filter information section."""
        filter_parts = []

        if self.account_id:
            filter_parts.append(
                f"{HTML_P_OPEN}{HTML_STRONG_OPEN}Filtered by Account ID:{HTML_STRONG_CLOSE} {self.account_id}{HTML_P_CLOSE}"
            )

        if self.tags:
            tags_str = ", ".join([f"{k}={v}" for k, v in self.tags.items()])
            filter_parts.append(
                f"{HTML_P_OPEN}{HTML_STRONG_OPEN}Filtered by Tags:{HTML_STRONG_CLOSE} {tags_str}{HTML_P_CLOSE}"
            )

        return filter_parts

    def _build_kms_summary(self, kms_stats: Dict[str, Any]) -> List[str]:
        """Build KMS summary section."""
        return [
            f"{HTML_H2_OPEN}Summary{HTML_H2_CLOSE}",
            HTML_UL_OPEN,
            f"{HTML_LI_OPEN}{HTML_STRONG_OPEN}Total Keys:{HTML_STRONG_CLOSE} {kms_stats['total']}{HTML_LI_CLOSE}",
            f"{HTML_LI_OPEN}{HTML_STRONG_OPEN}Customer-Managed Keys:{HTML_STRONG_CLOSE} "
            f"{kms_stats['customer_managed']}{HTML_LI_CLOSE}",
            f"{HTML_LI_OPEN}{HTML_STRONG_OPEN}Rotation Enabled:{HTML_STRONG_CLOSE} {kms_stats['rotation_enabled']} "
            f"({kms_stats['rotation_pct']:.1f}%){HTML_LI_CLOSE}",
            HTML_UL_CLOSE,
        ]

    def _build_control_compliance_summary(self, control_stats: Dict[str, Dict[str, int]]) -> List[str]:
        """Build control compliance summary section."""
        section_parts = [
            f"{HTML_H2_OPEN}Control Compliance Results{HTML_H2_CLOSE}",
            HTML_UL_OPEN,
        ]

        for control_id in sorted(control_stats.keys()):
            control_line = self._format_control_stats(control_id, control_stats[control_id])
            section_parts.append(control_line)

        section_parts.append(HTML_UL_CLOSE)
        return section_parts

    def _format_control_stats(self, control_id: str, stats: Dict[str, int]) -> str:
        """Format control statistics for display."""
        total = stats["pass"] + stats["fail"]
        pass_pct = stats["pass"] / max(total, 1) * 100
        control_desc = self.control_mapper.get_control_description(control_id)

        return (
            f"{HTML_LI_OPEN}{HTML_STRONG_OPEN}{control_id}:{HTML_STRONG_CLOSE} "
            f"{stats['pass']} PASS / {stats['fail']} FAIL ({pass_pct:.1f}% compliant) - {control_desc}{HTML_LI_CLOSE}"
        )

    def _upload_evidence_file(self, evidence_id: int, scan_date: str) -> None:
        """
        Upload compressed JSONL evidence file to Evidence record.

        :param int evidence_id: Evidence record ID
        :param str scan_date: Scan date string
        :return: None
        :rtype: None
        """
        try:
            # Prepare JSONL content
            jsonl_lines = []
            for key_data in self.raw_kms_data:
                compliance_item = self.create_compliance_item(key_data)
                evidence_entry = {
                    **key_data,
                    "compliance_assessment": {
                        "overall_result": compliance_item.compliance_result,
                        "control_results": compliance_item._compliance_results,
                        "assessed_controls": list(compliance_item._compliance_results.keys()),
                        "assessment_date": scan_date,
                    },
                }
                jsonl_lines.append(json.dumps(evidence_entry, default=str))

            jsonl_content = "\n".join(jsonl_lines)

            # Compress
            compressed_buffer = BytesIO()
            with gzip.open(compressed_buffer, "wt", encoding="utf-8", compresslevel=9) as gz_file:
                gz_file.write(jsonl_content)

            compressed_data = compressed_buffer.getvalue()

            # Upload
            file_name = f"kms_evidence_{scan_date}.jsonl.gz"
            api = Api()
            success = File.upload_file_to_regscale(
                file_name=file_name,
                parent_id=evidence_id,
                parent_module="evidence",
                api=api,
                file_data=compressed_data,
                tags="aws,kms,encryption",
            )

            if success:
                logger.info(f"Uploaded KMS evidence file to Evidence {evidence_id}")
            else:
                logger.warning(f"Failed to upload KMS evidence file to Evidence {evidence_id}")

        except Exception as e:
            logger.error(f"Error uploading evidence file: {e}", exc_info=True)

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
