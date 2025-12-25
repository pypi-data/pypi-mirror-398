#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AWS Config Compliance Integration for RegScale CLI."""

import gzip
import json
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from io import BytesIO
from typing import Any, Dict, List, Optional, Tuple

import boto3
from botocore.exceptions import ClientError

from regscale.core.app.utils.app_utils import get_current_datetime
from regscale.integrations.compliance_integration import ComplianceIntegration, ComplianceItem

logger = logging.getLogger("regscale")

# Constants for file paths and cache TTL
CONFIG_COMPLIANCE_CACHE_FILE = os.path.join("artifacts", "aws", "config_compliance_assessments.json")
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
HTML_H4_OPEN = "<h4>"
HTML_H4_CLOSE = "</h4>"
HTML_BR = "<br>"


class AWSConfigComplianceItem(ComplianceItem):
    """
    Compliance item from AWS Config rule evaluation.

    Represents a control assessment based on AWS Config rule evaluations.
    Multiple Config rules can map to a single control, and the control passes
    only if ALL associated rules are compliant.
    """

    def __init__(
        self,
        control_id: str,
        control_name: str,
        framework: str,
        rule_evaluations: List[Dict[str, Any]],
        resource_id: Optional[str] = None,
        resource_name: Optional[str] = None,
    ):
        """
        Initialize from AWS Config rule evaluations.

        :param str control_id: Control identifier (e.g., AC-2, SI-3)
        :param str control_name: Human-readable control name
        :param str framework: Compliance framework
        :param List[Dict[str, Any]] rule_evaluations: Config rule evaluation results
        :param Optional[str] resource_id: Resource identifier (AWS account ID typically)
        :param Optional[str] resource_name: Resource name
        """
        self._control_id = control_id
        self._control_name = control_name
        self._framework = framework
        self.rule_evaluations = rule_evaluations
        self._resource_id = resource_id or ""
        self._resource_name = resource_name or ""

        # Cache for aggregated compliance result
        self._aggregated_compliance_result = None

    @property
    def resource_id(self) -> str:
        """Unique identifier for the resource being assessed."""
        return self._resource_id

    @property
    def resource_name(self) -> str:
        """Human-readable name of the resource."""
        return self._resource_name

    @property
    def control_id(self) -> str:
        """Control identifier (e.g., AC-3, SI-2)."""
        return self._control_id

    def _aggregate_rule_compliance(self) -> Optional[str]:
        """
        Aggregate rule evaluation results to determine overall control compliance.

        AWS Config rule compliance types:
        - "COMPLIANT": Resource is compliant with the rule
        - "NON_COMPLIANT": Resource violates the rule
        - "NOT_APPLICABLE": Rule doesn't apply to this resource
        - "INSUFFICIENT_DATA": Not enough data to determine compliance

        Aggregation Logic:
        1. If ANY rule shows "NON_COMPLIANT" → Control FAILS
        2. If ALL applicable rules show "COMPLIANT" → Control PASSES
        3. If only NOT_APPLICABLE or INSUFFICIENT_DATA → INCONCLUSIVE

        :return: "PASS", "FAIL", or None (if inconclusive/no data)
        :rtype: Optional[str]
        """
        if not self.rule_evaluations:
            logger.debug(f"Control {self.control_id}: No rule evaluations available")
            return None

        compliant_count = 0
        non_compliant_count = 0
        not_applicable_count = 0
        insufficient_data_count = 0

        for evaluation in self.rule_evaluations:
            compliance_type = evaluation.get("compliance_type", "").upper()

            if compliance_type == "NON_COMPLIANT":
                non_compliant_count += 1
            elif compliance_type == "COMPLIANT":
                compliant_count += 1
            elif compliance_type == "NOT_APPLICABLE":
                not_applicable_count += 1
            else:  # INSUFFICIENT_DATA or other
                insufficient_data_count += 1

        total_evaluations = len(self.rule_evaluations)

        logger.debug(
            f"Control {self.control_id} rule summary: "
            f"{non_compliant_count} NON_COMPLIANT, {compliant_count} COMPLIANT, "
            f"{not_applicable_count} NOT_APPLICABLE, {insufficient_data_count} INSUFFICIENT_DATA "
            f"out of {total_evaluations} total"
        )

        # If ANY rule is non-compliant, the control fails
        if non_compliant_count > 0:
            logger.info(
                f"Control {self.control_id} FAILS: {non_compliant_count} non-compliant rule(s) "
                f"out of {total_evaluations}"
            )
            return "FAIL"

        # If we have compliant rules and no failures, control passes
        if compliant_count > 0:
            if not_applicable_count > 0 or insufficient_data_count > 0:
                logger.info(
                    f"Control {self.control_id} PASSES: {compliant_count} compliant, "
                    f"{not_applicable_count} not applicable, "
                    f"{insufficient_data_count} insufficient data (no failures)"
                )
            else:
                logger.info(f"Control {self.control_id} PASSES: All {compliant_count} rules compliant")
            return "PASS"

        # If no applicable compliance checks available, we cannot determine status
        logger.warning(
            f"Control {self.control_id}: No conclusive compliance checks in {total_evaluations} evaluation(s)"
        )
        return None

    @property
    def compliance_result(self) -> Optional[str]:
        """
        Result of compliance check (PASS, FAIL, etc).

        Aggregates Config rule evaluations to determine control-level compliance.

        :return: "PASS", "FAIL", or None (if no conclusive data available)
        :rtype: Optional[str]
        """
        # Use cached result if available
        if self._aggregated_compliance_result is not None or hasattr(self, "_result_was_cached"):
            return self._aggregated_compliance_result

        # Aggregate rule compliance checks
        result = self._aggregate_rule_compliance()

        if result is None:
            logger.info(
                f"Control {self.control_id}: No conclusive data for compliance determination. "
                f"Control status will not be updated. Rule evaluations: {len(self.rule_evaluations)}"
            )

        # Cache the result (including None)
        self._aggregated_compliance_result = result
        self._result_was_cached = True
        return result

    @property
    def severity(self) -> Optional[str]:
        """Severity level of the compliance violation (if failed)."""
        if self.compliance_result != "FAIL":
            return None

        # Determine severity based on number of non-compliant rules
        non_compliant_count = sum(
            1 for eval in self.rule_evaluations if eval.get("compliance_type", "").upper() == "NON_COMPLIANT"
        )

        if non_compliant_count >= 5:
            return "HIGH"
        elif non_compliant_count >= 2:
            return "MEDIUM"
        return "LOW"

    @property
    def description(self) -> str:
        """Description of the compliance check using HTML formatting."""
        desc_parts = [
            f"{HTML_H3_OPEN}AWS Config compliance assessment for control {self.control_id}{HTML_H3_CLOSE}",
            HTML_P_OPEN,
            f"{HTML_STRONG_OPEN}Control:{HTML_STRONG_CLOSE} {self._control_name}{HTML_BR}",
            f"{HTML_STRONG_OPEN}Framework:{HTML_STRONG_CLOSE} {self._framework}{HTML_BR}",
            f"{HTML_STRONG_OPEN}Total Rules:{HTML_STRONG_CLOSE} {len(self.rule_evaluations)}",
            HTML_P_CLOSE,
        ]

        # Add compliance summary
        compliant_rules = [e for e in self.rule_evaluations if e.get("compliance_type") == "COMPLIANT"]
        non_compliant_rules = [e for e in self.rule_evaluations if e.get("compliance_type") == "NON_COMPLIANT"]

        desc_parts.extend(
            [
                f"{HTML_H4_OPEN}Compliance Summary{HTML_H4_CLOSE}",
                HTML_UL_OPEN,
                f"{HTML_LI_OPEN}{HTML_STRONG_OPEN}Compliant Rules:{HTML_STRONG_CLOSE} {len(compliant_rules)}"
                f"{HTML_LI_CLOSE}",
                f"{HTML_LI_OPEN}{HTML_STRONG_OPEN}Non-Compliant Rules:{HTML_STRONG_CLOSE} {len(non_compliant_rules)}"
                f"{HTML_LI_CLOSE}",
                HTML_UL_CLOSE,
            ]
        )

        # Add non-compliant rules details
        if non_compliant_rules:
            desc_parts.append(f"{HTML_H4_OPEN}Non-Compliant Rules{HTML_H4_CLOSE}")
            desc_parts.append(HTML_UL_OPEN)
            for rule_eval in non_compliant_rules[:10]:  # Show up to 10 non-compliant rules
                rule_name = rule_eval.get("rule_name", "Unknown")
                resource_count = rule_eval.get("non_compliant_resource_count", 0)
                desc_parts.append(
                    f"{HTML_LI_OPEN}{HTML_STRONG_OPEN}{rule_name}{HTML_STRONG_CLOSE}: "
                    f"{resource_count} non-compliant resource(s){HTML_LI_CLOSE}"
                )
            if len(non_compliant_rules) > 10:
                desc_parts.append(
                    f"{HTML_LI_OPEN}... and {len(non_compliant_rules) - 10} more non-compliant rule(s){HTML_LI_CLOSE}"
                )
            desc_parts.append(HTML_UL_CLOSE)

        return "\n".join(desc_parts)

    @property
    def framework(self) -> str:
        """Compliance framework (e.g., NIST800-53R5, CSF)."""
        return self._framework


@dataclass
class ConfigEvidenceConfig:
    """Configuration for evidence collection from AWS Config."""

    collect_evidence: bool = False
    evidence_as_attachments: bool = True
    evidence_as_records: bool = False
    evidence_control_ids: Optional[List[str]] = None
    evidence_frequency: int = 30


@dataclass
class ConfigFilterConfig:
    """Configuration for filtering AWS Config resources."""

    account_id: Optional[str] = None
    tags: Optional[Dict[str, str]] = None
    conformance_pack_name: Optional[str] = None


class AWSConfigCompliance(ComplianceIntegration):
    """Process AWS Config compliance assessments and create compliance records in RegScale."""

    def __init__(
        self,
        plan_id: int,
        region: str = "us-east-1",
        framework: str = "NIST800-53R5",
        create_issues: bool = True,
        update_control_status: bool = True,
        create_poams: bool = False,
        parent_module: str = "securityplans",
        evidence_config: Optional[ConfigEvidenceConfig] = None,
        filter_config: Optional[ConfigFilterConfig] = None,
        use_security_hub: bool = False,
        force_refresh: bool = False,
        **kwargs,
    ):
        """
        Initialize AWS Config compliance integration.

        :param int plan_id: RegScale plan ID
        :param str region: AWS region
        :param str framework: Compliance framework
        :param bool create_issues: Whether to create issues for failed compliance
        :param bool update_control_status: Whether to update control implementation status
        :param bool create_poams: Whether to mark issues as POAMs
        :param str parent_module: RegScale parent module
        :param Optional[ConfigEvidenceConfig] evidence_config: Evidence collection configuration
        :param Optional[ConfigFilterConfig] filter_config: Resource filtering configuration
        :param bool use_security_hub: Include Security Hub control findings
        :param bool force_refresh: Force refresh of compliance data by bypassing cache
        :param kwargs: Additional parameters including AWS credentials
        """
        super().__init__(
            plan_id=plan_id,
            framework=framework,
            create_issues=create_issues,
            update_control_status=update_control_status,
            create_poams=create_poams,
            parent_module=parent_module,
            **kwargs,
        )

        self.region = region
        self.title = "AWS Config"

        # Evidence collection parameters
        self.evidence_config = evidence_config or ConfigEvidenceConfig()
        self.collect_evidence = self.evidence_config.collect_evidence
        self.evidence_as_attachments = self.evidence_config.evidence_as_attachments
        self.evidence_as_records = self.evidence_config.evidence_as_records
        self.evidence_control_ids = self.evidence_config.evidence_control_ids
        self.evidence_frequency = self.evidence_config.evidence_frequency

        # Filtering parameters
        self.filter_config = filter_config or ConfigFilterConfig()
        self.conformance_pack_name = self.filter_config.conformance_pack_name
        self.account_id = self.filter_config.account_id
        self.tags = self.filter_config.tags or {}

        # Security Hub integration
        self.use_security_hub = use_security_hub

        # Cache control
        self.force_refresh = force_refresh

        # Extract AWS credentials from kwargs
        profile = kwargs.get("profile")
        aws_access_key_id = kwargs.get("aws_access_key_id")
        aws_secret_access_key = kwargs.get("aws_secret_access_key")
        aws_session_token = kwargs.get("aws_session_token")

        # Initialize AWS session
        if aws_access_key_id and aws_secret_access_key:
            logger.info("Initializing AWS Config client with explicit credentials")
            self.session = boto3.Session(
                region_name=region,
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                aws_session_token=aws_session_token,
            )
        else:
            logger.info(f"Initializing AWS Config client with profile: {profile if profile else 'default'}")
            self.session = boto3.Session(profile_name=profile, region_name=region)

        try:
            self.config_client = self.session.client("config")
            logger.info("Successfully created AWS Config client")

            if self.use_security_hub:
                self.securityhub_client = self.session.client("securityhub")
                logger.info("Successfully created AWS Security Hub client")
        except Exception as e:
            logger.error(f"Failed to create AWS client: {e}")
            raise

    def fetch_compliance_data(self) -> List[Dict[str, Any]]:
        """
        Fetch raw compliance data from AWS Config.

        Returns control-level compliance data aggregated from Config rules.

        :return: List of raw compliance data (control + rule evaluations)
        :rtype: List[Dict[str, Any]]
        """
        # Check cache first unless force refresh
        if not self.force_refresh and self._is_cache_valid():
            cached_data = self._load_cached_data()
            if cached_data:
                return cached_data

        if self.force_refresh:
            logger.info("Force refresh requested, fetching fresh data from AWS Config...")

        try:
            compliance_data = self._fetch_fresh_compliance_data()
            self._save_to_cache(compliance_data)
            return compliance_data
        except ClientError as e:
            logger.error(f"Error fetching compliance data from AWS Config: {e}")
            return []

    def _fetch_fresh_compliance_data(self) -> List[Dict[str, Any]]:
        """
        Fetch fresh compliance data from AWS Config.

        :return: List of raw compliance data
        :rtype: List[Dict[str, Any]]
        """
        logger.info("Fetching compliance data from AWS Config...")

        # Initialize and fetch Config rules
        config_collector = self._initialize_config_collector()
        config_rules = self._fetch_config_rules(config_collector)

        # Build control mappings from rules
        control_mappings, _ = self._build_control_mappings(config_collector, config_rules)

        # Get and build compliance data
        compliance_data = self._build_compliance_data(config_collector, control_mappings)

        logger.info(f"Fetched {len(compliance_data)} control compliance items from AWS Config")
        return compliance_data

    def _initialize_config_collector(self):
        """Initialize Config collector with filtering."""
        from regscale.integrations.commercial.aws.inventory.resources.config import ConfigCollector

        self._log_filtering_info()

        return ConfigCollector(session=self.session, region=self.region, account_id=self.account_id, tags=self.tags)

    def _log_filtering_info(self) -> None:
        """Log filtering information if filters are applied."""
        if self.account_id:
            logger.info(f"Filtering Config rules by account ID: {self.account_id}")
        if self.tags:
            logger.info(f"Filtering Config rules by tags: {self.tags}")

    def _fetch_config_rules(self, config_collector) -> List[Dict[str, Any]]:
        """Fetch Config rules from AWS."""
        config_data = config_collector.collect()
        config_rules = config_data.get("ConfigRules", [])
        logger.info(f"Found {len(config_rules)} Config rules after filtering")
        return config_rules

    def _build_control_mappings(self, config_collector, config_rules: List[Dict[str, Any]]) -> Tuple[Dict, Dict]:
        """Build mappings between rules and controls."""
        from regscale.integrations.commercial.aws.conformance_pack_mappings import map_rule_to_controls

        control_mappings = {}  # control_id -> list of rule names
        rule_metadata = {}  # rule_name -> {rule data, tags}

        for rule in config_rules:
            self._process_single_rule(rule, config_collector, control_mappings, rule_metadata, map_rule_to_controls)

        logger.info(f"Mapped {len(config_rules)} rules to {len(control_mappings)} controls")
        return control_mappings, rule_metadata

    def _process_single_rule(
        self, rule: Dict, config_collector, control_mappings: Dict, rule_metadata: Dict, map_rule_to_controls
    ) -> None:
        """Process a single Config rule and map to controls."""
        rule_name = rule.get("ConfigRuleName", "")
        rule_tags = self._get_rule_tags(rule, config_collector)

        # Map rule to controls
        control_ids = map_rule_to_controls(
            rule_name=rule_name,
            rule_description=rule.get("Description"),
            rule_tags=rule_tags,
            framework=self.framework,
        )

        # Store mappings
        self._store_control_mappings(control_ids, rule_name, control_mappings)
        rule_metadata[rule_name] = rule

    def _get_rule_tags(self, rule: Dict, config_collector) -> Dict:
        """Get or fetch tags for a rule."""
        rule_tags = rule.get("Tags", {})
        rule_arn = rule.get("ConfigRuleArn", "")

        if not rule_tags and rule_arn:
            try:
                rule_tags = config_collector._get_rule_tags(self.config_client, rule_arn)
                rule["Tags"] = rule_tags
            except Exception as e:
                logger.debug(f"Could not fetch tags for rule {rule.get('ConfigRuleName', '')}: {e}")

        return rule_tags

    def _store_control_mappings(self, control_ids: List[str], rule_name: str, control_mappings: Dict) -> None:
        """Store control to rule mappings."""
        for control_id in control_ids:
            if control_id not in control_mappings:
                control_mappings[control_id] = []
            control_mappings[control_id].append(rule_name)

    def _build_compliance_data(self, config_collector, control_mappings: Dict) -> List[Dict[str, Any]]:
        """Build compliance data structure from control mappings."""
        control_compliance = config_collector.get_aggregate_compliance_by_control(control_mappings)
        compliance_data = []
        account_id = self._get_aws_account_id()

        for control_id, rule_evaluations in control_compliance.items():
            if rule_evaluations:
                compliance_data.append(self._create_compliance_item_dict(control_id, rule_evaluations, account_id))

        return compliance_data

    def _create_compliance_item_dict(self, control_id: str, rule_evaluations: List, account_id: str) -> Dict[str, Any]:
        """Create a compliance item dictionary."""
        return {
            "control_id": control_id,
            "control_name": f"Control {control_id}",  # Will be enriched by RegScale lookup
            "rule_evaluations": rule_evaluations,
            "resource_id": account_id,
            "resource_name": f"AWS Account {account_id}",
        }

    def _get_aws_account_id(self) -> str:
        """
        Get AWS account ID from STS.

        :return: AWS account ID
        :rtype: str
        """
        try:
            sts_client = self.session.client("sts")
            response = sts_client.get_caller_identity()
            return response.get("Account", "")
        except Exception as e:
            logger.warning(f"Could not get AWS account ID: {e}")
            return ""

    def create_compliance_item(self, raw_data: Dict[str, Any]) -> ComplianceItem:
        """
        Create a ComplianceItem from raw compliance data.

        :param Dict[str, Any] raw_data: Raw compliance data (control + rule evaluations)
        :return: ComplianceItem instance
        :rtype: ComplianceItem
        """
        control_id = raw_data.get("control_id", "")
        control_name = raw_data.get("control_name", "")
        rule_evaluations = raw_data.get("rule_evaluations", [])
        resource_id = raw_data.get("resource_id")
        resource_name = raw_data.get("resource_name")

        return AWSConfigComplianceItem(
            control_id=control_id,
            control_name=control_name,
            framework=self.framework,
            rule_evaluations=rule_evaluations,
            resource_id=resource_id,
            resource_name=resource_name,
        )

    def _is_cache_valid(self) -> bool:
        """Check if the cache file exists and is within the TTL."""
        if not os.path.exists(CONFIG_COMPLIANCE_CACHE_FILE):
            return False

        file_age = time.time() - os.path.getmtime(CONFIG_COMPLIANCE_CACHE_FILE)
        is_valid = file_age < CACHE_TTL_SECONDS

        if is_valid:
            hours_old = file_age / 3600
            logger.info(f"Using cached Config compliance data (age: {hours_old:.1f} hours)")

        return is_valid

    def _load_cached_data(self) -> List[Dict[str, Any]]:
        """Load compliance data from cache file."""
        try:
            with open(CONFIG_COMPLIANCE_CACHE_FILE, encoding="utf-8") as file:
                cached_data = json.load(file)
                logger.info(f"Loaded {len(cached_data)} compliance items from cache")
                return cached_data
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Error reading cache file: {e}. Fetching fresh data.")
            return []

    def _save_to_cache(self, compliance_data: List[Dict[str, Any]]) -> None:
        """Save compliance data to cache file."""
        try:
            os.makedirs(os.path.dirname(CONFIG_COMPLIANCE_CACHE_FILE), exist_ok=True)

            with open(CONFIG_COMPLIANCE_CACHE_FILE, "w", encoding="utf-8") as file:
                json.dump(compliance_data, file, indent=2, default=str)

            logger.info(f"Cached {len(compliance_data)} compliance items")
        except IOError as e:
            logger.warning(f"Error writing to cache file: {e}")

    def sync_compliance(self) -> None:
        """
        Sync compliance data from AWS Config to RegScale.

        Extends the base sync_compliance method to add evidence collection.

        :return: None
        :rtype: None
        """
        # Call the base class sync_compliance to handle control assessments
        super().sync_compliance()

        # If evidence collection is enabled, collect evidence after compliance sync
        if self.collect_evidence:
            logger.info("Evidence collection enabled, starting evidence collection...")
            try:
                # Collect evidence based on mode
                if self.evidence_as_records:
                    logger.info("Creating individual Evidence records per control...")
                    self._collect_evidence_as_records()
                else:
                    logger.info("Creating consolidated evidence file for SSP...")
                    self._collect_evidence_as_ssp_attachment()
            except Exception as e:
                logger.error(f"Error during evidence collection: {e}", exc_info=True)

    def _collect_evidence_as_ssp_attachment(self) -> None:
        """
        Collect evidence and attach as file to SecurityPlan (default mode).

        :return: None
        :rtype: None
        """
        from regscale.core.app.api import Api
        from regscale.models.regscale_models.file import File

        logger.info("Collecting evidence as SSP-level attachment...")

        # Collect all evidence data
        all_evidence = self._collect_all_evidence_data()

        if not all_evidence:
            logger.warning("No evidence data collected")
            return

        # Generate filename
        scan_date = get_current_datetime(dt_format="%Y-%m-%d %H:%M:%S")
        safe_framework = self.framework.replace(" ", "_").replace("/", "_")
        file_name = f"config_compliance_{safe_framework}_{scan_date}.jsonl.gz"

        # Compress evidence data
        jsonl_content = "\n".join([json.dumps(item, default=str) for item in all_evidence])

        compressed_buffer = BytesIO()
        with gzip.open(compressed_buffer, "wt", encoding="utf-8", compresslevel=9) as gz_file:
            gz_file.write(jsonl_content)

        compressed_data = compressed_buffer.getvalue()
        compressed_size_mb = len(compressed_data) / (1024 * 1024)
        uncompressed_size_mb = len(jsonl_content.encode("utf-8")) / (1024 * 1024)
        compression_ratio = (1 - (len(compressed_data) / len(jsonl_content.encode("utf-8")))) * 100

        logger.info(
            "Compressed evidence: %.2f MB -> %.2f MB (%.1f%% reduction)",
            uncompressed_size_mb,
            compressed_size_mb,
            compression_ratio,
        )

        # Upload to SecurityPlan
        api = Api()
        success = File.upload_file_to_regscale(
            file_name=file_name,
            parent_id=self.plan_id,
            parent_module="securityplans",
            api=api,
            file_data=compressed_data,
            tags=f"aws,config,compliance,{safe_framework.lower()}",
        )

        if success:
            logger.info(f"Successfully uploaded evidence file '{file_name}' to SecurityPlan {self.plan_id}")
        else:
            logger.warning(f"Failed to upload evidence file to SecurityPlan {self.plan_id}")

    def _collect_evidence_as_records(self) -> None:
        """
        Collect evidence and create individual Evidence records per control.

        :return: None
        :rtype: None
        """
        from regscale.core.app.api import Api
        from regscale.models.regscale_models.evidence import Evidence
        from regscale.models.regscale_models.evidence_mapping import EvidenceMapping
        from regscale.models.regscale_models.file import File

        logger.info("Collecting evidence as individual records per control...")

        # Collect evidence grouped by control
        evidence_by_control = self._collect_evidence_by_control()

        if not evidence_by_control:
            logger.warning("No evidence data collected")
            return

        scan_date = get_current_datetime(dt_format="%Y-%m-%d %H:%M:%S")
        safe_framework = self.framework.replace(" ", "_").replace("/", "_")
        api = Api()
        evidence_records_created = 0

        for control_id, control_evidence in evidence_by_control.items():
            # Filter by evidence_control_ids if specified
            if self.evidence_control_ids and control_id not in self.evidence_control_ids:
                continue

            try:
                # Create Evidence record
                title = f"AWS Config Evidence - {control_id} - {scan_date}"
                description = self._build_evidence_description(control_id, control_evidence)
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
                    logger.error(f"Failed to create evidence record for control {control_id}")
                    continue

                logger.info(f"Created evidence record {created_evidence.id}: {title}")

                # Compress and upload evidence file
                file_name = f"config_evidence_{control_id}_{scan_date}.jsonl.gz"
                jsonl_content = "\n".join([json.dumps(item, default=str) for item in control_evidence])

                compressed_buffer = BytesIO()
                with gzip.open(compressed_buffer, "wt", encoding="utf-8", compresslevel=9) as gz_file:
                    gz_file.write(jsonl_content)

                compressed_data = compressed_buffer.getvalue()

                success = File.upload_file_to_regscale(
                    file_name=file_name,
                    parent_id=created_evidence.id,
                    parent_module="evidence",
                    api=api,
                    file_data=compressed_data,
                    tags=f"aws,config,{control_id.lower()},{safe_framework.lower()}",
                )

                if success:
                    logger.info(f"Uploaded evidence file for control {control_id}")

                # Map evidence to SSP
                mapping = EvidenceMapping(
                    evidenceID=created_evidence.id, mappedID=self.plan_id, mappingType="securityplans"
                )
                mapping.create()
                logger.info(f"Linked evidence {created_evidence.id} to SSP {self.plan_id}")

                evidence_records_created += 1

            except Exception as ex:
                logger.error(f"Failed to create evidence record for control {control_id}: {ex}", exc_info=True)

        logger.info(f"Created {evidence_records_created} evidence record(s)")

    def _collect_all_evidence_data(self) -> List[Dict[str, Any]]:
        """
        Collect all evidence data for SSP-level attachment.

        :return: List of evidence items
        :rtype: List[Dict[str, Any]]
        """
        from regscale.integrations.commercial.aws.inventory.resources.config import ConfigCollector

        all_evidence = []
        config_collector = ConfigCollector(session=self.session, region=self.region)

        # Get all Config rules
        config_data = config_collector.collect()
        config_rules = config_data.get("ConfigRules", [])

        for rule in config_rules:
            rule_name = rule.get("ConfigRuleName", "")

            try:
                # Get compliance details for this rule
                compliance_details = config_collector.get_compliance_details(rule_name)

                for detail in compliance_details:
                    evidence_item = {
                        "rule_name": rule_name,
                        "compliance_type": detail.get("ComplianceType", ""),
                        "resource_type": detail.get("EvaluationResultIdentifier", {})
                        .get("EvaluationResultQualifier", {})
                        .get("ResourceType", ""),
                        "resource_id": detail.get("EvaluationResultIdentifier", {})
                        .get("EvaluationResultQualifier", {})
                        .get("ResourceId", ""),
                        "config_rule_invoked_time": str(detail.get("ConfigRuleInvokedTime", "")),
                        "result_recorded_time": str(detail.get("ResultRecordedTime", "")),
                        "annotation": detail.get("Annotation", ""),
                    }
                    all_evidence.append(evidence_item)

            except Exception as e:
                logger.debug(f"Error collecting evidence for rule {rule_name}: {e}")

        logger.info(f"Collected {len(all_evidence)} evidence items")
        return all_evidence

    def _collect_evidence_by_control(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Collect evidence data grouped by control ID.

        :return: Dictionary mapping control_id to list of evidence items
        :rtype: Dict[str, List[Dict[str, Any]]]
        """
        from regscale.integrations.commercial.aws.inventory.resources.config import ConfigCollector
        from regscale.integrations.commercial.aws.conformance_pack_mappings import map_rule_to_controls

        evidence_by_control = {}
        config_collector = ConfigCollector(session=self.session, region=self.region)

        # Get all Config rules
        config_data = config_collector.collect()
        config_rules = config_data.get("ConfigRules", [])

        for rule in config_rules:
            rule_name = rule.get("ConfigRuleName", "")
            rule_description = rule.get("Description")
            rule_tags = rule.get("Tags", {})

            # Map rule to controls
            control_ids = map_rule_to_controls(
                rule_name=rule_name,
                rule_description=rule_description,
                rule_tags=rule_tags,
                framework=self.framework,
            )

            if not control_ids:
                continue

            try:
                # Get compliance details for this rule
                compliance_details = config_collector.get_compliance_details(rule_name)

                for detail in compliance_details:
                    evidence_item = {
                        "rule_name": rule_name,
                        "compliance_type": detail.get("ComplianceType", ""),
                        "resource_type": detail.get("EvaluationResultIdentifier", {})
                        .get("EvaluationResultQualifier", {})
                        .get("ResourceType", ""),
                        "resource_id": detail.get("EvaluationResultIdentifier", {})
                        .get("EvaluationResultQualifier", {})
                        .get("ResourceId", ""),
                        "config_rule_invoked_time": str(detail.get("ConfigRuleInvokedTime", "")),
                        "result_recorded_time": str(detail.get("ResultRecordedTime", "")),
                        "annotation": detail.get("Annotation", ""),
                    }

                    # Add to each control this rule maps to
                    for control_id in control_ids:
                        if control_id not in evidence_by_control:
                            evidence_by_control[control_id] = []
                        evidence_by_control[control_id].append(evidence_item)

            except Exception as e:
                logger.debug(f"Error collecting evidence for rule {rule_name}: {e}")

        logger.info(f"Collected evidence for {len(evidence_by_control)} controls")
        return evidence_by_control

    def _build_evidence_description(self, control_id: str, control_evidence: List[Dict[str, Any]]) -> str:
        """
        Build HTML description for evidence record.

        :param str control_id: Control ID
        :param List[Dict[str, Any]] control_evidence: Evidence items for this control
        :return: HTML description
        :rtype: str
        """
        compliant_count = sum(1 for e in control_evidence if e.get("compliance_type") == "COMPLIANT")
        non_compliant_count = sum(1 for e in control_evidence if e.get("compliance_type") == "NON_COMPLIANT")

        desc_parts = [
            f"{HTML_H3_OPEN}AWS Config Evidence for Control {control_id}{HTML_H3_CLOSE}",
            f"{HTML_P_OPEN}{HTML_STRONG_OPEN}Framework:{HTML_STRONG_CLOSE} {self.framework}{HTML_P_CLOSE}",
            f"{HTML_H4_OPEN}Summary{HTML_H4_CLOSE}",
            HTML_UL_OPEN,
            f"{HTML_LI_OPEN}{HTML_STRONG_OPEN}Total Evidence Items:{HTML_STRONG_CLOSE} {len(control_evidence)}"
            f"{HTML_LI_CLOSE}",
            f"{HTML_LI_OPEN}{HTML_STRONG_OPEN}Compliant:{HTML_STRONG_CLOSE} {compliant_count}{HTML_LI_CLOSE}",
            f"{HTML_LI_OPEN}{HTML_STRONG_OPEN}Non-Compliant:{HTML_STRONG_CLOSE} {non_compliant_count}"
            f"{HTML_LI_CLOSE}",
            HTML_UL_CLOSE,
        ]

        return "\n".join(desc_parts)
