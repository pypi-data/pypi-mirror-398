#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AWS Organizations Evidence Integration for RegScale CLI."""

import gzip
import json
import logging
import os
import time
from datetime import datetime, timedelta
from io import BytesIO
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

from regscale.core.app.api import Api
from regscale.core.app.utils.app_utils import get_current_datetime
from regscale.integrations.commercial.aws.org_control_mappings import OrgControlMapper
from regscale.integrations.compliance_integration import ComplianceIntegration, ComplianceItem
from regscale.models import regscale_models
from regscale.models.regscale_models.evidence import Evidence
from regscale.models.regscale_models.evidence_mapping import EvidenceMapping
from regscale.models.regscale_models.file import File

logger = logging.getLogger("regscale")

# Constants
ORG_CACHE_FILE = os.path.join("artifacts", "aws", "org_data.json")
CACHE_TTL_SECONDS = 4 * 60 * 60  # 4 hours

# HTML constants
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


class OrgComplianceItem(ComplianceItem):
    """Compliance item representing AWS Organizations assessment."""

    def __init__(self, org_data: Dict[str, Any], control_mapper: OrgControlMapper):
        """
        Initialize Organizations compliance item.

        :param Dict[str, Any] org_data: Organization structure and metadata
        :param OrgControlMapper control_mapper: Control mapper for compliance assessment
        """
        self.org_data = org_data
        self.control_mapper = control_mapper

        # Extract organization attributes
        self._org_id = org_data.get("Id", "")
        self._org_arn = org_data.get("Arn", "")
        self._master_account_id = org_data.get("MasterAccountId", "")
        self._accounts = org_data.get("accounts", [])
        self._ous = org_data.get("organizational_units", [])
        self._scps = org_data.get("service_control_policies", [])

        # Assess compliance
        self._compliance_results = control_mapper.assess_organization_compliance(org_data)

    @property
    def resource_id(self) -> str:
        """Unique identifier for the organization."""
        return self._org_id

    @property
    def resource_name(self) -> str:
        """Human-readable name of the organization."""
        return f"AWS Organization {self._org_id[:12]}..."

    @property
    def control_id(self) -> str:
        """Primary control identifier."""
        # Return first failing control, or first control if all pass
        for control_id, result in self._compliance_results.items():
            if result == "FAIL":
                return control_id
        return list(self._compliance_results.keys())[0] if self._compliance_results else "AC-1"

    @property
    def compliance_result(self) -> str:
        """Overall compliance result."""
        if not self._compliance_results:
            return "PASS"
        if "FAIL" in self._compliance_results.values():
            return "FAIL"
        return "PASS"

    @property
    def severity(self) -> Optional[str]:
        """Severity level based on which controls are failing."""
        if self.compliance_result == "PASS":
            return None

        # AC-1, PM-9, AC-6 failures are HIGH severity (governance/policy issues)
        if self._compliance_results.get("AC-1") == "FAIL" or self._compliance_results.get("PM-9") == "FAIL":
            return "HIGH"

        if self._compliance_results.get("AC-6") == "FAIL":
            return "MEDIUM"

        # AC-2 failures are MEDIUM severity (account management)
        if self._compliance_results.get("AC-2") == "FAIL":
            return "MEDIUM"

        return "MEDIUM"

    @property
    def description(self) -> str:
        """Detailed description of the Organizations compliance assessment."""
        desc_parts = self._build_org_summary()
        desc_parts.extend(self._build_compliance_results())

        if self.compliance_result == "FAIL":
            desc_parts.extend(self._build_remediation_guidance())

        return "\n".join(desc_parts)

    def _build_org_summary(self) -> List[str]:
        """Build organization summary section."""
        return [
            f"{HTML_H3_OPEN}AWS Organizations Governance Assessment{HTML_H3_CLOSE}",
            HTML_P_OPEN,
            f"{HTML_STRONG_OPEN}Organization ID:{HTML_STRONG_CLOSE} {self._org_id}{HTML_BR}",
            f"{HTML_STRONG_OPEN}Organization ARN:{HTML_STRONG_CLOSE} {self._org_arn}{HTML_BR}",
            f"{HTML_STRONG_OPEN}Master Account:{HTML_STRONG_CLOSE} {self._master_account_id}{HTML_BR}",
            f"{HTML_STRONG_OPEN}Total Accounts:{HTML_STRONG_CLOSE} {len(self._accounts)}{HTML_BR}",
            f"{HTML_STRONG_OPEN}Organizational Units:{HTML_STRONG_CLOSE} {len(self._ous)}{HTML_BR}",
            f"{HTML_STRONG_OPEN}Service Control Policies:{HTML_STRONG_CLOSE} {len(self._scps)}",
            HTML_P_CLOSE,
        ]

    def _build_compliance_results(self) -> List[str]:
        """Build compliance results section."""
        results = [
            f"{HTML_H3_OPEN}Control Compliance Results{HTML_H3_CLOSE}",
            HTML_UL_OPEN,
        ]

        for control_id, result in self._compliance_results.items():
            results.append(self._format_control_result(control_id, result))

        results.append(HTML_UL_CLOSE)
        return results

    def _format_control_result(self, control_id: str, result: str) -> str:
        """Format a single control compliance result."""
        result_color = "#d32f2f" if result == "FAIL" else "#2e7d32"
        control_desc = self.control_mapper.get_control_description(control_id)
        return (
            f"{HTML_LI_OPEN}{HTML_STRONG_OPEN}{control_id}:{HTML_STRONG_CLOSE} "
            f"<span style='color: {result_color};'>{result}</span> - {control_desc}{HTML_LI_CLOSE}"
        )

    def _build_remediation_guidance(self) -> List[str]:
        """Build remediation guidance for failed controls."""
        guidance = [
            f"{HTML_H3_OPEN}Remediation Guidance{HTML_H3_CLOSE}",
            HTML_UL_OPEN,
        ]

        guidance.extend(self._get_ac1_remediation())
        guidance.extend(self._get_pm9_remediation())
        guidance.extend(self._get_ac2_remediation())
        guidance.extend(self._get_ac6_remediation())

        guidance.append(HTML_UL_CLOSE)
        return guidance

    def _get_ac1_remediation(self) -> List[str]:
        """Get AC-1 control remediation steps."""
        items = []
        if self._compliance_results.get("AC-1") == "FAIL":
            if len(self._ous) < 2:
                items.append(f"{HTML_LI_OPEN}Create organizational units (OUs) for governance structure{HTML_LI_CLOSE}")

            restrictive_scps = [scp for scp in self._scps if scp.get("Name") != "FullAWSAccess"]
            if not restrictive_scps:
                items.append(f"{HTML_LI_OPEN}Attach Service Control Policies to enforce access controls{HTML_LI_CLOSE}")
        return items

    def _get_pm9_remediation(self) -> List[str]:
        """Get PM-9 control remediation steps."""
        items = []
        if self._compliance_results.get("PM-9") == "FAIL":
            items.append(
                f"{HTML_LI_OPEN}Organize accounts by risk profile (prod, dev, sandbox) using OUs{HTML_LI_CLOSE}"
            )
            items.append(f"{HTML_LI_OPEN}Implement restrictive SCPs for security guardrails{HTML_LI_CLOSE}")
        return items

    def _get_ac2_remediation(self) -> List[str]:
        """Get AC-2 control remediation steps."""
        items = []
        if self._compliance_results.get("AC-2") == "FAIL":
            non_active = [acc for acc in self._accounts if acc.get("Status") != "ACTIVE"]
            if non_active:
                items.append(
                    f"{HTML_LI_OPEN}Review and activate or remove {len(non_active)} suspended accounts{HTML_LI_CLOSE}"
                )
        return items

    def _get_ac6_remediation(self) -> List[str]:
        """Get AC-6 control remediation steps."""
        items = []
        if self._compliance_results.get("AC-6") == "FAIL":
            items.append(
                f"{HTML_LI_OPEN}Implement least privilege SCPs (deny unnecessary services/actions){HTML_LI_CLOSE}"
            )
        return items

    @property
    def framework(self) -> str:
        """Compliance framework used for assessment."""
        return self.control_mapper.framework


class AWSOrganizationsEvidenceIntegration(ComplianceIntegration):
    """Process AWS Organizations data and create evidence/compliance records in RegScale."""

    def __init__(
        self,
        plan_id: int,
        region: str = "us-east-1",
        framework: str = "NIST800-53R5",
        create_issues: bool = True,
        update_control_status: bool = True,
        create_poams: bool = False,
        parent_module: str = "securityplans",
        collect_evidence: bool = False,
        evidence_as_attachments: bool = True,
        evidence_control_ids: Optional[List[str]] = None,
        evidence_frequency: int = 30,
        force_refresh: bool = False,
        **kwargs,
    ):
        """
        Initialize AWS Organizations evidence integration.

        :param int plan_id: RegScale plan ID
        :param str region: AWS region
        :param str framework: Compliance framework
        :param bool create_issues: Create issues for non-compliant organization
        :param bool update_control_status: Update control implementation status
        :param bool create_poams: Mark issues as POAMs
        :param str parent_module: RegScale parent module
        :param bool collect_evidence: Collect evidence artifacts
        :param bool evidence_as_attachments: Attach evidence to SSP vs create Evidence records
        :param Optional[List[str]] evidence_control_ids: Specific control IDs for evidence
        :param int evidence_frequency: Evidence update frequency in days
        :param bool force_refresh: Force refresh by bypassing cache
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

        # Initialize API for file operations
        self.api = Api()

        self.region = region
        self.title = "AWS Organizations"
        self.collect_evidence = collect_evidence
        self.evidence_as_attachments = evidence_as_attachments
        self.evidence_control_ids = evidence_control_ids
        self.evidence_frequency = evidence_frequency
        self.force_refresh = force_refresh

        # Initialize control mapper
        self.control_mapper = OrgControlMapper(framework=framework)

        # Extract AWS credentials
        profile = kwargs.get("profile")
        aws_access_key_id = kwargs.get("aws_access_key_id")
        aws_secret_access_key = kwargs.get("aws_secret_access_key")
        aws_session_token = kwargs.get("aws_session_token")

        if aws_access_key_id and aws_secret_access_key:
            logger.info("Initializing AWS Organizations client with explicit credentials")
            self.session = boto3.Session(
                region_name=region,
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                aws_session_token=aws_session_token,
            )
        else:
            logger.info(f"Initializing AWS Organizations client with profile: {profile if profile else 'default'}")
            self.session = boto3.Session(profile_name=profile, region_name=region)

        try:
            self.client = self.session.client("organizations")
            logger.info("Successfully created AWS Organizations client")
        except Exception as e:
            logger.error(f"Failed to create AWS Organizations client: {e}")
            raise

        # Store raw org data
        self.raw_org_data: Dict[str, Any] = {}

    def _is_cache_valid(self) -> bool:
        """Check if cache is valid."""
        if not os.path.exists(ORG_CACHE_FILE):
            return False
        file_age = time.time() - os.path.getmtime(ORG_CACHE_FILE)
        is_valid = file_age < CACHE_TTL_SECONDS
        if is_valid:
            logger.info(f"Using cached Organizations data (age: {file_age / 3600:.1f} hours)")
        return is_valid

    def _load_cached_data(self) -> Dict[str, Any]:
        """Load Organizations data from cache."""
        try:
            with open(ORG_CACHE_FILE, encoding="utf-8") as file:
                data = json.load(file)

            # Validate cache format - must be a dict
            if not isinstance(data, dict):
                logger.warning("Invalid cache format detected (not a dict). Invalidating cache.")
                return {}

            return data
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Error reading cache: {e}")
            return {}

    def _save_to_cache(self, org_data: Dict[str, Any]) -> None:
        """Save Organizations data to cache."""
        try:
            os.makedirs(os.path.dirname(ORG_CACHE_FILE), exist_ok=True)
            with open(ORG_CACHE_FILE, "w", encoding="utf-8") as file:
                json.dump(org_data, file, indent=2, default=str)
            logger.info(f"Cached Organizations data to {ORG_CACHE_FILE}")
        except IOError as e:
            logger.warning(f"Error writing cache: {e}")

    def _fetch_fresh_org_data(self) -> Dict[str, Any]:
        """Fetch fresh Organizations data from AWS."""
        logger.info("Fetching Organizations data from AWS...")

        org_data = {}

        try:
            # Get organization details
            org_response = self.client.describe_organization()
            org_data.update(org_response.get("Organization", {}))

            # Get all accounts
            accounts = []
            paginator = self.client.get_paginator("list_accounts")
            for page in paginator.paginate():
                accounts.extend(page.get("Accounts", []))
            org_data["accounts"] = accounts
            logger.info(f"Found {len(accounts)} accounts in organization")

            # Get organizational units
            ous = self._list_organizational_units()
            org_data["organizational_units"] = ous
            logger.info(f"Found {len(ous)} organizational units")

            # Get service control policies
            scps = self._list_service_control_policies()
            org_data["service_control_policies"] = scps
            logger.info(f"Found {len(scps)} service control policies")

        except ClientError as e:
            logger.error(f"Error fetching Organizations data: {e}")
            return {}

        return org_data

    def _list_organizational_units(self) -> List[Dict[str, Any]]:
        """List all organizational units recursively."""
        ous = []

        def traverse_ous(parent_id: str):
            try:
                paginator = self.client.get_paginator("list_organizational_units_for_parent")
                for page in paginator.paginate(ParentId=parent_id):
                    for ou in page.get("OrganizationalUnits", []):
                        ous.append(ou)
                        # Recursively get child OUs
                        traverse_ous(ou["Id"])
            except ClientError as e:
                logger.debug(f"Error listing OUs for parent {parent_id}: {e}")

        try:
            # Start from root
            roots = self.client.list_roots().get("Roots", [])
            for root in roots:
                traverse_ous(root["Id"])
        except ClientError as e:
            logger.error(f"Error getting roots: {e}")

        return ous

    def _list_service_control_policies(self) -> List[Dict[str, Any]]:
        """List all service control policies with their content."""
        scps = []
        try:
            paginator = self.client.get_paginator("list_policies")
            for page in paginator.paginate(Filter="SERVICE_CONTROL_POLICY"):
                for policy_summary in page.get("Policies", []):
                    # Get full policy details including content
                    try:
                        policy_detail = self.client.describe_policy(PolicyId=policy_summary["Id"])
                        scps.append(policy_detail.get("Policy", {}))
                    except ClientError as e:
                        logger.debug(f"Error describing policy {policy_summary['Id']}: {e}")
        except ClientError as e:
            logger.error(f"Error listing SCPs: {e}")

        return scps

    def fetch_compliance_data(self) -> List[Dict[str, Any]]:
        """Fetch raw Organizations data."""
        if not self.force_refresh and self._is_cache_valid():
            cached_data = self._load_cached_data()
            if cached_data:
                self.raw_org_data = cached_data
                return [cached_data]

        if self.force_refresh:
            logger.info("Force refresh requested, fetching fresh Organizations data...")

        try:
            org_data = self._fetch_fresh_org_data()
            self.raw_org_data = org_data
            self._save_to_cache(org_data)
            return [org_data] if org_data else []
        except ClientError as e:
            logger.error(f"Error fetching Organizations data: {e}")
            return []

    def create_compliance_item(self, raw_data: Dict[str, Any]) -> ComplianceItem:
        """Create compliance item from Organizations data."""
        return OrgComplianceItem(raw_data, self.control_mapper)

    def sync_compliance(self) -> None:
        """Main method to sync Organizations compliance data."""
        super().sync_compliance()

        if self.collect_evidence:
            logger.info("Evidence collection enabled, starting evidence collection...")
            self._collect_org_evidence()

    def _collect_org_evidence(self) -> None:
        """Collect Organizations evidence."""
        if not self.raw_org_data:
            logger.warning("No Organizations data available for evidence collection")
            return

        scan_date = get_current_datetime(dt_format="%Y-%m-%d %H:%M:%S")

        if self.evidence_as_attachments:
            logger.info("Creating SSP file attachment with Organizations evidence...")
            self._create_ssp_attachment(scan_date)
        else:
            logger.info("Creating Evidence record with Organizations evidence...")
            self._create_evidence_record(scan_date)

    def _create_ssp_attachment(self, scan_date: str) -> None:
        """Create SSP file attachment with Organizations evidence."""
        try:
            # Check for existing evidence to avoid duplicates
            date_str = datetime.now().strftime("%Y%m%d")
            file_name_pattern = f"org_evidence_{date_str}"

            if self.check_for_existing_evidence(file_name_pattern):
                logger.info(
                    "Evidence file for Organizations already exists for today. Skipping upload to avoid duplicates."
                )
                return

            # Add timestamp to make filename unique if run multiple times per day
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"org_evidence_{timestamp}.jsonl.gz"

            # Prepare JSONL content
            compliance_item = self.create_compliance_item(self.raw_org_data)
            evidence_entry = {
                **self.raw_org_data,
                "compliance_assessment": {
                    "overall_result": compliance_item.compliance_result,
                    "control_results": compliance_item._compliance_results,
                    "assessed_controls": list(compliance_item._compliance_results.keys()),
                    "assessment_date": scan_date,
                },
            }
            jsonl_content = json.dumps(evidence_entry, default=str)

            # Compress
            compressed_buffer = BytesIO()
            with gzip.open(compressed_buffer, "wt", encoding="utf-8", compresslevel=9) as gz_file:
                gz_file.write(jsonl_content)

            compressed_data = compressed_buffer.getvalue()

            # Upload
            api = Api()
            success = File.upload_file_to_regscale(
                file_name=file_name,
                parent_id=self.plan_id,
                parent_module=self.parent_module,
                api=api,
                file_data=compressed_data,
                tags="aws,organizations,governance,automated",
            )

            if success:
                logger.info(f"Successfully uploaded Organizations evidence file: {file_name}")
            else:
                logger.error("Failed to upload Organizations evidence file")

        except Exception as e:
            logger.error(f"Error creating SSP attachment: {e}", exc_info=True)

    def _create_evidence_record(self, scan_date: str) -> None:
        """Create Evidence record with Organizations evidence."""
        try:
            title = f"AWS Organizations Evidence - {scan_date}"
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

            # Upload evidence file
            self._upload_evidence_file(created_evidence.id, scan_date)

            # Link to SSP
            self._link_evidence_to_ssp(created_evidence.id)

            # Link to controls if specified
            if self.evidence_control_ids:
                self._link_evidence_to_controls(created_evidence.id, is_attachment=False)

        except Exception as e:
            logger.error(f"Error creating evidence record: {e}", exc_info=True)

    def _build_evidence_description(self, scan_date: str) -> str:
        """Build HTML evidence description."""
        accounts = self.raw_org_data.get("accounts", [])
        ous = self.raw_org_data.get("organizational_units", [])
        scps = self.raw_org_data.get("service_control_policies", [])

        compliance_item = self.create_compliance_item(self.raw_org_data)
        control_stats = dict(compliance_item._compliance_results.items())

        desc_parts = [
            "<h1>AWS Organizations Governance Evidence</h1>",
            f"{HTML_P_OPEN}{HTML_STRONG_OPEN}Assessment Date:{HTML_STRONG_CLOSE} {scan_date}{HTML_P_CLOSE}",
            f"{HTML_H2_OPEN}Organization Summary{HTML_H2_CLOSE}",
            HTML_UL_OPEN,
            f"{HTML_LI_OPEN}{HTML_STRONG_OPEN}Total Accounts:{HTML_STRONG_CLOSE} {len(accounts)}{HTML_LI_CLOSE}",
            f"{HTML_LI_OPEN}{HTML_STRONG_OPEN}Organizational Units:{HTML_STRONG_CLOSE} {len(ous)}{HTML_LI_CLOSE}",
            f"{HTML_LI_OPEN}{HTML_STRONG_OPEN}Service Control Policies:{HTML_STRONG_CLOSE} {len(scps)}{HTML_LI_CLOSE}",
            HTML_UL_CLOSE,
            f"{HTML_H2_OPEN}Control Compliance Results{HTML_H2_CLOSE}",
            HTML_UL_OPEN,
        ]

        for control_id, result in control_stats.items():
            control_desc = self.control_mapper.get_control_description(control_id)
            result_color = "#d32f2f" if result == "FAIL" else "#2e7d32"
            desc_parts.append(
                f"{HTML_LI_OPEN}{HTML_STRONG_OPEN}{control_id}:{HTML_STRONG_CLOSE} "
                f"<span style='color: {result_color};'>{result}</span> - {control_desc}{HTML_LI_CLOSE}"
            )

        desc_parts.append(HTML_UL_CLOSE)
        return "\n".join(desc_parts)

    def _upload_evidence_file(self, evidence_id: int, scan_date: str) -> None:
        """Upload evidence file to Evidence record."""
        try:
            compliance_item = self.create_compliance_item(self.raw_org_data)
            evidence_entry = {
                **self.raw_org_data,
                "compliance_assessment": {
                    "overall_result": compliance_item.compliance_result,
                    "control_results": compliance_item._compliance_results,
                    "assessed_controls": list(compliance_item._compliance_results.keys()),
                    "assessment_date": scan_date,
                },
            }
            jsonl_content = json.dumps(evidence_entry, default=str)

            compressed_buffer = BytesIO()
            with gzip.open(compressed_buffer, "wt", encoding="utf-8", compresslevel=9) as gz_file:
                gz_file.write(jsonl_content)

            compressed_data = compressed_buffer.getvalue()
            file_name = f"org_evidence_{scan_date}.jsonl.gz"

            api = Api()
            success = File.upload_file_to_regscale(
                file_name=file_name,
                parent_id=evidence_id,
                parent_module="evidence",
                api=api,
                file_data=compressed_data,
                tags="aws,organizations,governance",
            )

            if success:
                logger.info(f"Uploaded Organizations evidence file to Evidence {evidence_id}")
            else:
                logger.warning(f"Failed to upload evidence file to Evidence {evidence_id}")

        except Exception as e:
            logger.error(f"Error uploading evidence file: {e}", exc_info=True)

    def _link_evidence_to_ssp(self, evidence_id: int) -> None:
        """Link evidence to Security Plan."""
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
