#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AWS Organizations Control Mappings for RegScale Compliance Integration."""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger("regscale")

# NIST 800-53 R5 Control Mappings for AWS Organizations
ORG_CONTROL_MAPPINGS = {
    "AC-1": {
        "name": "Policy and Procedures",
        "description": "Develop, document, and disseminate access control policy and procedures",
        "checks": {
            "scp_attached": {
                "weight": 100,
                "pass_criteria": "Organization has Service Control Policies attached to enforce access controls",
                "fail_criteria": "No SCPs attached or SCPs not enforcing proper access restrictions",
            },
            "organizational_structure": {
                "weight": 80,
                "pass_criteria": "Clear OU hierarchy established for governance",
                "fail_criteria": "Flat structure with no organizational units",
            },
        },
    },
    "PM-9": {
        "name": "Risk Management Strategy",
        "description": "Develop comprehensive risk management strategy for the organization",
        "checks": {
            "account_governance": {
                "weight": 100,
                "pass_criteria": "Accounts organized by risk profile (prod, dev, sandbox) with appropriate SCPs",
                "fail_criteria": "All accounts in same OU without risk-based segmentation",
            },
            "policy_enforcement": {
                "weight": 90,
                "pass_criteria": "SCPs enforce security guardrails (e.g., region restrictions, service restrictions)",
                "fail_criteria": "No restrictive SCPs or only default FullAWSAccess policy",
            },
        },
    },
    "AC-2": {
        "name": "Account Management",
        "description": "Manage system accounts including creation, enabling, modification, and removal",
        "checks": {
            "active_accounts": {
                "weight": 100,
                "pass_criteria": "All accounts are ACTIVE with proper metadata (email, name)",
                "fail_criteria": "SUSPENDED or accounts missing contact information",
            },
            "account_tracking": {
                "weight": 80,
                "pass_criteria": "Accounts have tags or metadata for ownership and purpose",
                "fail_criteria": "Accounts lack identification or ownership information",
            },
        },
    },
    "AC-6": {
        "name": "Least Privilege",
        "description": "Employ the principle of least privilege",
        "checks": {
            "restrictive_scps": {
                "weight": 100,
                "pass_criteria": "SCPs implement least privilege by denying unnecessary services/actions",
                "fail_criteria": "SCPs use FullAWSAccess or overly permissive policies",
            },
        },
    },
}

# ISO 27001 Control Mappings
ISO_27001_MAPPINGS = {
    "A.6.1.1": {
        "name": "Information security roles and responsibilities",
        "org_attributes": ["organizational_units", "account_tags", "scp_policies"],
    },
    "A.6.1.2": {
        "name": "Segregation of duties",
        "org_attributes": ["organizational_structure", "scp_enforcement", "account_separation"],
    },
}

# SCP patterns that indicate good security posture
RESTRICTIVE_SCP_PATTERNS = [
    "DenyAllOutsideRegion",
    "RestrictRegions",
    "DenyRootAccount",
    "RequireMFA",
    "DenyLeaveOrganization",
    "PreventSCPRemoval",
    "DenyCloudTrailDelete",
    "DenyGuardDutyDisable",
    "DenyConfigDisable",
]

# Account statuses that are compliant
COMPLIANT_ACCOUNT_STATUSES = ["ACTIVE"]


class OrgControlMapper:
    """Map AWS Organizations attributes to compliance control status."""

    def __init__(self, framework: str = "NIST800-53R5"):
        """
        Initialize Organizations control mapper.

        :param str framework: Compliance framework (NIST800-53R5 or ISO27001)
        """
        self.framework = framework
        self.mappings = ORG_CONTROL_MAPPINGS if framework == "NIST800-53R5" else ISO_27001_MAPPINGS

    def assess_organization_compliance(self, org_data: Dict) -> Dict[str, str]:
        """
        Assess AWS Organizations compliance against all mapped controls.

        :param Dict org_data: Organization structure and metadata
        :return: Dictionary mapping control IDs to compliance results (PASS/FAIL)
        :rtype: Dict[str, str]
        """
        results = {}

        if self.framework == "NIST800-53R5":
            results["AC-1"] = self._assess_ac1(org_data)
            results["PM-9"] = self._assess_pm9(org_data)
            results["AC-2"] = self._assess_ac2(org_data)
            results["AC-6"] = self._assess_ac6(org_data)

        return results

    def _assess_ac1(self, org_data: Dict) -> str:
        """
        Assess AC-1 (Access Control Policy and Procedures) compliance.

        :param Dict org_data: Organization data
        :return: Compliance result (PASS/FAIL)
        :rtype: str
        """
        scps = org_data.get("service_control_policies", [])
        ous = org_data.get("organizational_units", [])

        # Check if organization has SCPs beyond default FullAWSAccess
        restrictive_scps = [scp for scp in scps if scp.get("Name") != "FullAWSAccess"]

        if not restrictive_scps:
            logger.debug("Organization FAILS AC-1: No restrictive SCPs attached")
            return "FAIL"

        # Check for organizational structure (OUs)
        if len(ous) < 2:  # Should have at least root + 1 OU
            logger.debug("Organization FAILS AC-1: No organizational structure (only root OU)")
            return "FAIL"

        logger.debug(f"Organization PASSES AC-1: {len(restrictive_scps)} restrictive SCPs, {len(ous)} OUs")
        return "PASS"

    def _assess_pm9(self, org_data: Dict) -> str:
        """
        Assess PM-9 (Risk Management Strategy) compliance.

        :param Dict org_data: Organization data
        :return: Compliance result (PASS/FAIL)
        :rtype: str
        """
        ous = org_data.get("organizational_units", [])
        scps = org_data.get("service_control_policies", [])

        # Check for risk-based OU structure (prod, dev, sandbox, etc.)
        ou_names = [ou.get("Name", "").lower() for ou in ous]
        has_env_separation = any(
            env in " ".join(ou_names) for env in ["prod", "production", "dev", "development", "sandbox", "test"]
        )

        if not has_env_separation:
            logger.debug("Organization FAILS PM-9: No environment-based OU separation")
            return "FAIL"

        # Check for restrictive SCPs
        has_restrictive_scps = any(
            any(pattern.lower() in scp.get("Name", "").lower() for pattern in RESTRICTIVE_SCP_PATTERNS) for scp in scps
        )

        if not has_restrictive_scps:
            logger.debug("Organization FAILS PM-9: No restrictive SCPs enforcing security guardrails")
            return "FAIL"

        logger.debug("Organization PASSES PM-9: Environment separation and restrictive SCPs present")
        return "PASS"

    def _assess_ac2(self, org_data: Dict) -> str:
        """
        Assess AC-2 (Account Management) compliance.

        :param Dict org_data: Organization data
        :return: Compliance result (PASS/FAIL)
        :rtype: str
        """
        accounts = org_data.get("accounts", [])

        if not accounts:
            logger.debug("Organization FAILS AC-2: No accounts found")
            return "FAIL"

        # Check account statuses
        non_active_accounts = [acc for acc in accounts if acc.get("Status") not in COMPLIANT_ACCOUNT_STATUSES]

        if non_active_accounts:
            logger.debug(f"Organization FAILS AC-2: {len(non_active_accounts)} accounts not in ACTIVE status")
            return "FAIL"

        # Check for accounts missing email
        accounts_missing_email = [acc for acc in accounts if not acc.get("Email")]

        if accounts_missing_email:
            logger.debug(f"Organization FAILS AC-2: {len(accounts_missing_email)} accounts missing contact email")
            return "FAIL"

        logger.debug(f"Organization PASSES AC-2: All {len(accounts)} accounts are ACTIVE with contact info")
        return "PASS"

    def _assess_ac6(self, org_data: Dict) -> str:
        """
        Assess AC-6 (Least Privilege) compliance.

        :param Dict org_data: Organization data
        :return: Compliance result (PASS/FAIL)
        :rtype: str
        """
        scps = org_data.get("service_control_policies", [])

        # Check if only FullAWSAccess is attached (not least privilege)
        only_full_access = len(scps) == 1 and scps[0].get("Name") == "FullAWSAccess"

        if only_full_access:
            logger.debug("Organization FAILS AC-6: Only FullAWSAccess SCP attached (not least privilege)")
            return "FAIL"

        # Check for at least one restrictive SCP
        has_restrictive = any(
            any(pattern.lower() in scp.get("Name", "").lower() for pattern in RESTRICTIVE_SCP_PATTERNS)
            or "Deny" in scp.get("Name", "")
            for scp in scps
        )

        if not has_restrictive:
            logger.debug("Organization FAILS AC-6: No restrictive/deny SCPs implementing least privilege")
            return "FAIL"

        logger.debug("Organization PASSES AC-6: Restrictive SCPs implementing least privilege")
        return "PASS"

    def get_control_description(self, control_id: str) -> Optional[str]:
        """
        Get human-readable description for a control.

        :param str control_id: Control identifier (e.g., AC-1)
        :return: Control description or None
        :rtype: Optional[str]
        """
        control_data = self.mappings.get(control_id)
        if control_data:
            return f"{control_data.get('name')}: {control_data.get('description', '')}"
        return None

    def get_mapped_controls(self) -> List[str]:
        """
        Get list of all control IDs mapped for this framework.

        :return: List of control IDs
        :rtype: List[str]
        """
        return list(self.mappings.keys())

    def get_check_details(self, control_id: str) -> Optional[Dict]:
        """
        Get detailed check criteria for a control.

        :param str control_id: Control identifier
        :return: Dictionary of check details or None
        :rtype: Optional[Dict]
        """
        control_data = self.mappings.get(control_id)
        if control_data:
            return control_data.get("checks", {})
        return None
