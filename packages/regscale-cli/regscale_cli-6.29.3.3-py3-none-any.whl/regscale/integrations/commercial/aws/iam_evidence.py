#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AWS IAM Evidence Integration for RegScale CLI."""

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
from regscale.integrations.commercial.aws.iam_control_mappings import IAMControlMapper
from regscale.integrations.compliance_integration import ComplianceIntegration, ComplianceItem
from regscale.models.regscale_models.evidence import Evidence
from regscale.models.regscale_models.evidence_mapping import EvidenceMapping
from regscale.models.regscale_models.file import File

logger = logging.getLogger("regscale")

IAM_CACHE_FILE = os.path.join("artifacts", "aws", "iam_data.json")
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


class IAMComplianceItem(ComplianceItem):
    """Compliance item representing AWS IAM assessment."""

    def __init__(self, iam_data: Dict[str, Any], control_mapper: IAMControlMapper):
        self.iam_data = iam_data
        self.control_mapper = control_mapper
        self._users = iam_data.get("users", [])
        self._groups = iam_data.get("groups", [])
        self._roles = iam_data.get("roles", [])
        self._policies = iam_data.get("policies", [])
        self._compliance_results = control_mapper.assess_iam_compliance(iam_data)

    @property
    def resource_id(self) -> str:
        return "iam-account"

    @property
    def resource_name(self) -> str:
        return f"AWS IAM Account ({len(self._users)} users, {len(self._roles)} roles)"

    @property
    def control_id(self) -> str:
        for control_id, result in self._compliance_results.items():
            if result == "FAIL":
                return control_id
        return list(self._compliance_results.keys())[0] if self._compliance_results else "AC-2"

    @property
    def compliance_result(self) -> str:
        if not self._compliance_results:
            return "PASS"
        return "FAIL" if "FAIL" in self._compliance_results.values() else "PASS"

    @property
    def severity(self) -> Optional[str]:
        if self.compliance_result == "PASS":
            return None
        if self._compliance_results.get("AC-2") == "FAIL" or self._compliance_results.get("IA-2") == "FAIL":
            return "HIGH"
        return "MEDIUM"

    @property
    def description(self) -> str:
        desc_parts = [
            f"{HTML_H3_OPEN}AWS IAM Access Control Assessment{HTML_H3_CLOSE}",
            HTML_P_OPEN,
            f"{HTML_STRONG_OPEN}Users:{HTML_STRONG_CLOSE} {len(self._users)}{HTML_BR}",
            f"{HTML_STRONG_OPEN}Groups:{HTML_STRONG_CLOSE} {len(self._groups)}{HTML_BR}",
            f"{HTML_STRONG_OPEN}Roles:{HTML_STRONG_CLOSE} {len(self._roles)}{HTML_BR}",
            f"{HTML_STRONG_OPEN}Managed Policies:{HTML_STRONG_CLOSE} {len(self._policies)}",
            HTML_P_CLOSE,
            f"{HTML_H3_OPEN}Control Compliance Results{HTML_H3_CLOSE}",
            HTML_UL_OPEN,
        ]

        for control_id, result in self._compliance_results.items():
            result_color = "#d32f2f" if result == "FAIL" else "#2e7d32"
            control_desc = self.control_mapper.get_control_description(control_id)
            desc_parts.append(
                f"{HTML_LI_OPEN}{HTML_STRONG_OPEN}{control_id}:{HTML_STRONG_CLOSE} "
                f"<span style='color: {result_color};'>{result}</span> - {control_desc}{HTML_LI_CLOSE}"
            )
        desc_parts.append(HTML_UL_CLOSE)

        if self.compliance_result == "FAIL":
            desc_parts.append(f"{HTML_H3_OPEN}Remediation Guidance{HTML_H3_CLOSE}")
            desc_parts.append(HTML_UL_OPEN)
            if self._compliance_results.get("AC-2") == "FAIL":
                desc_parts.append(f"{HTML_LI_OPEN}Enable MFA for all IAM users{HTML_LI_CLOSE}")
                desc_parts.append(f"{HTML_LI_OPEN}Secure root account with MFA and remove access keys{HTML_LI_CLOSE}")
            if self._compliance_results.get("AC-6") == "FAIL":
                desc_parts.append(
                    f"{HTML_LI_OPEN}Remove AdministratorAccess from users, use groups/roles{HTML_LI_CLOSE}"
                )
            if self._compliance_results.get("IA-2") == "FAIL":
                desc_parts.append(f"{HTML_LI_OPEN}Strengthen password policy requirements{HTML_LI_CLOSE}")
            if self._compliance_results.get("IA-5") == "FAIL":
                desc_parts.append(f"{HTML_LI_OPEN}Rotate access keys older than 90 days{HTML_LI_CLOSE}")
            if self._compliance_results.get("AC-3") == "FAIL":
                desc_parts.append(f"{HTML_LI_OPEN}Review and restrict role trust policies{HTML_LI_CLOSE}")
            desc_parts.append(HTML_UL_CLOSE)

        return "\n".join(desc_parts)

    @property
    def framework(self) -> str:
        return self.control_mapper.framework


class AWSIAMEvidenceIntegration(ComplianceIntegration):
    """Process AWS IAM data and create evidence/compliance records in RegScale."""

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
        self.title = "AWS IAM"
        self.collect_evidence = collect_evidence
        self.evidence_as_attachments = evidence_as_attachments
        self.evidence_control_ids = evidence_control_ids
        self.evidence_frequency = evidence_frequency
        self.force_refresh = force_refresh
        self.control_mapper = IAMControlMapper(framework=framework)
        self.api = Api()

        profile = kwargs.get("profile")
        aws_access_key_id = kwargs.get("aws_access_key_id")
        aws_secret_access_key = kwargs.get("aws_secret_access_key")
        aws_session_token = kwargs.get("aws_session_token")

        if aws_access_key_id and aws_secret_access_key:
            logger.info("Initializing AWS IAM client with explicit credentials")
            self.session = boto3.Session(
                region_name=region,
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                aws_session_token=aws_session_token,
            )
        else:
            logger.info(f"Initializing AWS IAM client with profile: {profile if profile else 'default'}")
            self.session = boto3.Session(profile_name=profile, region_name=region)

        try:
            self.client = self.session.client("iam")
            logger.info("Successfully created AWS IAM client")
        except Exception as e:
            logger.error(f"Failed to create AWS IAM client: {e}")
            raise

        self.raw_iam_data: Dict[str, Any] = {}

    def _is_cache_valid(self) -> bool:
        if not os.path.exists(IAM_CACHE_FILE):
            return False
        file_age = time.time() - os.path.getmtime(IAM_CACHE_FILE)
        is_valid = file_age < CACHE_TTL_SECONDS
        if is_valid:
            logger.info(f"Using cached IAM data (age: {file_age / 3600:.1f} hours)")
        return is_valid

    def _load_cached_data(self) -> Dict[str, Any]:
        try:
            with open(IAM_CACHE_FILE, encoding="utf-8") as file:
                data = json.load(file)

            # Validate cache format - must be a dict
            if not isinstance(data, dict):
                logger.warning("Invalid cache format detected (not a dict). Invalidating cache.")
                return {}

            return data
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Error reading cache: {e}")
            return {}

    def _save_to_cache(self, iam_data: Dict[str, Any]) -> None:
        try:
            os.makedirs(os.path.dirname(IAM_CACHE_FILE), exist_ok=True)
            with open(IAM_CACHE_FILE, "w", encoding="utf-8") as file:
                json.dump(iam_data, file, indent=2, default=str)
            logger.info(f"Cached IAM data to {IAM_CACHE_FILE}")
        except IOError as e:
            logger.warning(f"Error writing cache: {e}")

    def _fetch_fresh_iam_data(self) -> Dict[str, Any]:
        logger.info("Fetching IAM data from AWS...")
        iam_data = {}

        try:
            iam_data["account_summary"] = self.client.get_account_summary().get("SummaryMap", {})
            iam_data["password_policy"] = self._get_password_policy()
            iam_data["users"] = self._list_users()
            logger.info(f"Found {len(iam_data['users'])} IAM users")
            iam_data["groups"] = self._list_groups()
            logger.info(f"Found {len(iam_data['groups'])} IAM groups")
            iam_data["roles"] = self._list_roles()
            logger.info(f"Found {len(iam_data['roles'])} IAM roles")
            iam_data["policies"] = self._list_policies()
            logger.info(f"Found {len(iam_data['policies'])} customer managed policies")
        except ClientError as e:
            logger.error(f"Error fetching IAM data: {e}")
            return {}

        return iam_data

    def _get_password_policy(self) -> Dict[str, Any]:
        try:
            return self.client.get_account_password_policy().get("PasswordPolicy", {})
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchEntity":
                logger.warning("No account password policy configured")
                return {}
            raise

    def _list_users(self) -> List[Dict[str, Any]]:
        users = []
        try:
            paginator = self.client.get_paginator("list_users")
            for page in paginator.paginate():
                for user in page.get("Users", []):
                    user_name = user["UserName"]
                    user["MfaEnabled"] = self._user_has_mfa(user_name)
                    user["AccessKeys"] = self._list_user_access_keys(user_name)
                    user["AttachedPolicies"] = self._list_user_attached_policies(user_name)
                    user["InlinePolicies"] = self._list_user_inline_policies(user_name)
                    user["PasswordLastUsed"] = self._get_password_last_used(user)
                    users.append(user)
        except ClientError as e:
            logger.error(f"Error listing users: {e}")
        return users

    def _user_has_mfa(self, user_name: str) -> bool:
        try:
            mfa_devices = self.client.list_mfa_devices(UserName=user_name).get("MFADevices", [])
            return len(mfa_devices) > 0
        except ClientError:
            return False

    def _list_user_access_keys(self, user_name: str) -> List[Dict[str, Any]]:
        try:
            keys = self.client.list_access_keys(UserName=user_name).get("AccessKeyMetadata", [])
            for key in keys:
                created_date = key.get("CreateDate")
                if created_date:
                    age = (datetime.now(created_date.tzinfo) - created_date).days
                    key["AgeDays"] = age
            return keys
        except ClientError:
            return []

    def _list_user_attached_policies(self, user_name: str) -> List[Dict[str, Any]]:
        try:
            return self.client.list_attached_user_policies(UserName=user_name).get("AttachedPolicies", [])
        except ClientError:
            return []

    def _list_user_inline_policies(self, user_name: str) -> List[Dict[str, Any]]:
        try:
            policy_names = self.client.list_user_policies(UserName=user_name).get("PolicyNames", [])
            policies = []
            for policy_name in policy_names:
                policy_doc = self.client.get_user_policy(UserName=user_name, PolicyName=policy_name)
                policies.append({"PolicyName": policy_name, "PolicyDocument": policy_doc.get("PolicyDocument", {})})
            return policies
        except ClientError:
            return []

    def _get_password_last_used(self, user: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        password_last_used = user.get("PasswordLastUsed")
        if password_last_used:
            days_since = (datetime.now(password_last_used.tzinfo) - password_last_used).days
            return {"LastUsedDate": password_last_used, "DaysSinceUsed": days_since}
        return None

    def _list_groups(self) -> List[Dict[str, Any]]:
        groups = []
        try:
            paginator = self.client.get_paginator("list_groups")
            for page in paginator.paginate():
                groups.extend(page.get("Groups", []))
        except ClientError as e:
            logger.error(f"Error listing groups: {e}")
        return groups

    def _list_roles(self) -> List[Dict[str, Any]]:
        roles = []
        try:
            paginator = self.client.get_paginator("list_roles")
            for page in paginator.paginate():
                for role in page.get("Roles", []):
                    role_name = role["RoleName"]
                    role["AttachedPolicies"] = self._list_role_attached_policies(role_name)
                    roles.append(role)
        except ClientError as e:
            logger.error(f"Error listing roles: {e}")
        return roles

    def _list_role_attached_policies(self, role_name: str) -> List[Dict[str, Any]]:
        try:
            return self.client.list_attached_role_policies(RoleName=role_name).get("AttachedPolicies", [])
        except ClientError:
            return []

    def _list_policies(self) -> List[Dict[str, Any]]:
        policies = []
        try:
            paginator = self.client.get_paginator("list_policies")
            for page in paginator.paginate(Scope="Local"):
                policies.extend(page.get("Policies", []))
        except ClientError as e:
            logger.error(f"Error listing policies: {e}")
        return policies

    def fetch_compliance_data(self) -> List[Dict[str, Any]]:
        if not self.force_refresh and self._is_cache_valid():
            cached_data = self._load_cached_data()
            if cached_data:
                self.raw_iam_data = cached_data
                return [cached_data]

        if self.force_refresh:
            logger.info("Force refresh requested, fetching fresh IAM data...")

        try:
            iam_data = self._fetch_fresh_iam_data()
            self.raw_iam_data = iam_data
            self._save_to_cache(iam_data)
            return [iam_data] if iam_data else []
        except ClientError as e:
            logger.error(f"Error fetching IAM data: {e}")
            return []

    def create_compliance_item(self, raw_data: Dict[str, Any]) -> ComplianceItem:
        return IAMComplianceItem(raw_data, self.control_mapper)

    def _map_resource_type_to_asset_type(self, compliance_item: ComplianceItem) -> str:
        """
        Map IAM account to RegScale asset type.

        :param ComplianceItem compliance_item: IAM compliance item
        :return: Asset type string
        :rtype: str
        """
        return "AWS IAM Account"

    def sync_compliance(self) -> None:
        super().sync_compliance()
        if self.collect_evidence:
            logger.info("Evidence collection enabled, starting evidence collection...")
            self._collect_iam_evidence()

    def _collect_iam_evidence(self) -> None:
        if not self.raw_iam_data:
            logger.warning("No IAM data available for evidence collection")
            return

        scan_date = get_current_datetime(dt_format="%Y-%m-%d %H:%M:%S")

        if self.evidence_as_attachments:
            logger.info("Creating SSP file attachment with IAM evidence...")
            self._create_ssp_attachment(scan_date)
        else:
            logger.info("Creating Evidence record with IAM evidence...")
            self._create_evidence_record(scan_date)

    def _create_ssp_attachment(self, scan_date: str) -> None:
        try:
            # Check for existing evidence to avoid duplicates
            date_str = datetime.now().strftime("%Y%m%d")
            file_name_pattern = f"iam_evidence_{date_str}"

            if self.check_for_existing_evidence(file_name_pattern):
                logger.info("Evidence file for IAM already exists for today. Skipping upload to avoid duplicates.")
                return

            # Add timestamp to make filename unique if run multiple times per day
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"iam_evidence_{timestamp}.jsonl.gz"

            compliance_item = self.create_compliance_item(self.raw_iam_data)
            evidence_entry = {
                **self.raw_iam_data,
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
            api = Api()
            success = File.upload_file_to_regscale(
                file_name=file_name,
                parent_id=self.plan_id,
                parent_module=self.parent_module,
                api=api,
                file_data=compressed_data,
                tags="aws,iam,access-control,automated",
            )

            if success:
                logger.info(f"Successfully uploaded IAM evidence file: {file_name}")
            else:
                logger.error("Failed to upload IAM evidence file")

        except Exception as e:
            logger.error(f"Error creating SSP attachment: {e}", exc_info=True)

    def _create_evidence_record(self, scan_date: str) -> None:
        try:
            title = f"AWS IAM Evidence - {scan_date}"
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
        users = self.raw_iam_data.get("users", [])
        groups = self.raw_iam_data.get("groups", [])
        roles = self.raw_iam_data.get("roles", [])
        compliance_item = self.create_compliance_item(self.raw_iam_data)

        desc_parts = [
            "<h1>AWS IAM Access Control Evidence</h1>",
            f"{HTML_P_OPEN}{HTML_STRONG_OPEN}Assessment Date:{HTML_STRONG_CLOSE} {scan_date}{HTML_P_CLOSE}",
            f"{HTML_H2_OPEN}IAM Summary{HTML_H2_CLOSE}",
            HTML_UL_OPEN,
            f"{HTML_LI_OPEN}{HTML_STRONG_OPEN}Users:{HTML_STRONG_CLOSE} {len(users)}{HTML_LI_CLOSE}",
            f"{HTML_LI_OPEN}{HTML_STRONG_OPEN}Groups:{HTML_STRONG_CLOSE} {len(groups)}{HTML_LI_CLOSE}",
            f"{HTML_LI_OPEN}{HTML_STRONG_OPEN}Roles:{HTML_STRONG_CLOSE} {len(roles)}{HTML_LI_CLOSE}",
            HTML_UL_CLOSE,
            f"{HTML_H2_OPEN}Control Compliance Results{HTML_H2_CLOSE}",
            HTML_UL_OPEN,
        ]

        for control_id, result in compliance_item._compliance_results.items():
            control_desc = self.control_mapper.get_control_description(control_id)
            result_color = "#d32f2f" if result == "FAIL" else "#2e7d32"
            desc_parts.append(
                f"{HTML_LI_OPEN}{HTML_STRONG_OPEN}{control_id}:{HTML_STRONG_CLOSE} "
                f"<span style='color: {result_color};'>{result}</span> - {control_desc}{HTML_LI_CLOSE}"
            )

        desc_parts.append(HTML_UL_CLOSE)
        return "\n".join(desc_parts)

    def _upload_evidence_file(self, evidence_id: int, scan_date: str) -> None:
        try:
            compliance_item = self.create_compliance_item(self.raw_iam_data)
            evidence_entry = {
                **self.raw_iam_data,
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
            file_name = f"iam_evidence_{scan_date}.jsonl.gz"

            api = Api()
            success = File.upload_file_to_regscale(
                file_name=file_name,
                parent_id=evidence_id,
                parent_module="evidence",
                api=api,
                file_data=compressed_data,
                tags="aws,iam,access-control",
            )

            if success:
                logger.info(f"Uploaded IAM evidence file to Evidence {evidence_id}")
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
