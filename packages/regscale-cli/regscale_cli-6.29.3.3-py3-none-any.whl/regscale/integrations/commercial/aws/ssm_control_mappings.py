#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AWS Systems Manager Control Mappings for RegScale Compliance Integration."""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger("regscale")

# NIST 800-53 R5 Control Mappings for AWS Systems Manager
SSM_CONTROL_MAPPINGS = {
    "CM-2": {
        "name": "Baseline Configuration",
        "description": "Develop, document, and maintain baseline configurations for systems",
        "checks": {
            "managed_instances": {
                "weight": 100,
                "pass_criteria": "Managed instances are registered and reporting to Systems Manager",
                "fail_criteria": "No managed instances or instances not reporting",
            },
            "inventory_collection": {
                "weight": 90,
                "pass_criteria": "SSM Inventory configured to collect system configuration data",
                "fail_criteria": "SSM Inventory not configured",
            },
            "state_manager": {
                "weight": 85,
                "pass_criteria": "State Manager associations configured for baseline enforcement",
                "fail_criteria": "No State Manager associations",
            },
        },
    },
    "CM-6": {
        "name": "Configuration Settings",
        "description": "Establish and document configuration settings for systems using configuration management",
        "checks": {
            "ssm_documents": {
                "weight": 100,
                "pass_criteria": "SSM Documents configured for configuration enforcement",
                "fail_criteria": "No SSM Documents configured",
            },
            "parameters": {
                "weight": 95,
                "pass_criteria": "SSM Parameter Store used for configuration management",
                "fail_criteria": "No parameters configured",
            },
            "associations": {
                "weight": 90,
                "pass_criteria": "Associations configured to enforce configuration settings",
                "fail_criteria": "No associations configured",
            },
        },
    },
    "SI-2": {
        "name": "Flaw Remediation",
        "description": "Identify, report, and correct system flaws including patch management",
        "checks": {
            "patch_baselines": {
                "weight": 100,
                "pass_criteria": "Patch baselines configured for all operating systems",
                "fail_criteria": "No patch baselines configured",
            },
            "patch_compliance": {
                "weight": 100,
                "pass_criteria": "Instances compliant with patch baselines",
                "fail_criteria": "Instances missing critical patches",
            },
            "maintenance_windows": {
                "weight": 85,
                "pass_criteria": "Maintenance windows configured for patching",
                "fail_criteria": "No maintenance windows configured",
            },
        },
    },
    "CM-3": {
        "name": "Configuration Change Control",
        "description": "Determine types of changes that are configuration controlled",
        "checks": {
            "automation_documents": {
                "weight": 100,
                "pass_criteria": "Automation documents for change control processes",
                "fail_criteria": "No automation documents for change control",
            },
        },
    },
    "CM-8": {
        "name": "System Component Inventory",
        "description": "Develop and document an inventory of system components",
        "checks": {
            "inventory_data": {
                "weight": 100,
                "pass_criteria": "SSM Inventory collecting component data",
                "fail_criteria": "No inventory data being collected",
            },
        },
    },
}


class SSMControlMapper:
    """Map AWS Systems Manager configurations to compliance control status."""

    def __init__(self, framework: str = "NIST800-53R5"):
        """
        Initialize SSM control mapper.

        :param str framework: Compliance framework
        """
        self.framework = framework
        self.mappings = SSM_CONTROL_MAPPINGS

    def assess_ssm_compliance(self, ssm_data: Dict) -> Dict[str, str]:
        """
        Assess Systems Manager compliance against all mapped controls.

        :param Dict ssm_data: Systems Manager configuration data
        :return: Dictionary mapping control IDs to compliance results (PASS/FAIL)
        :rtype: Dict[str, str]
        """
        results = {}

        if self.framework == "NIST800-53R5":
            results["CM-2"] = self._assess_cm2(ssm_data)
            results["CM-6"] = self._assess_cm6(ssm_data)
            results["SI-2"] = self._assess_si2(ssm_data)
            results["CM-3"] = self._assess_cm3(ssm_data)
            results["CM-8"] = self._assess_cm8(ssm_data)

        return results

    def _assess_cm2(self, ssm_data: Dict) -> str:
        """
        Assess CM-2 (Baseline Configuration) compliance.

        :param Dict ssm_data: SSM configuration data
        :return: Compliance result (PASS/FAIL)
        :rtype: str
        """
        managed_instances = ssm_data.get("ManagedInstances", [])
        associations = ssm_data.get("Associations", [])

        # Check if managed instances exist and are reporting
        if not managed_instances:
            logger.debug("SSM FAILS CM-2: No managed instances registered")
            return "FAIL"

        # Check for online instances
        online_instances = [i for i in managed_instances if i.get("PingStatus") == "Online"]
        if not online_instances:
            logger.debug("SSM FAILS CM-2: No online managed instances")
            return "FAIL"

        # Check for State Manager associations for baseline enforcement
        if not associations:
            logger.debug("SSM FAILS CM-2: No State Manager associations configured")
            return "FAIL"

        logger.debug(f"SSM PASSES CM-2: {len(online_instances)} online instances with {len(associations)} associations")
        return "PASS"

    def _assess_cm6(self, ssm_data: Dict) -> str:
        """
        Assess CM-6 (Configuration Settings) compliance.

        :param Dict ssm_data: SSM configuration data
        :return: Compliance result (PASS/FAIL)
        :rtype: str
        """
        documents = ssm_data.get("Documents", [])
        parameters = ssm_data.get("Parameters", [])
        associations = ssm_data.get("Associations", [])

        # Check for SSM Documents for configuration enforcement
        if not documents:
            logger.debug("SSM FAILS CM-6: No SSM Documents configured")
            return "FAIL"

        # Check for Parameter Store usage
        if not parameters:
            logger.debug("SSM FAILS CM-6: No SSM parameters configured")
            return "FAIL"

        # Check for associations to enforce configuration
        if not associations:
            logger.debug("SSM FAILS CM-6: No associations configured for configuration enforcement")
            return "FAIL"

        logger.debug(f"SSM PASSES CM-6: {len(documents)} documents, {len(parameters)} parameters configured")
        return "PASS"

    def _assess_si2(self, ssm_data: Dict) -> str:
        """
        Assess SI-2 (Flaw Remediation / Patch Management) compliance.

        :param Dict ssm_data: SSM configuration data
        :return: Compliance result (PASS/FAIL)
        :rtype: str
        """
        patch_baselines = ssm_data.get("PatchBaselines", [])
        managed_instances = ssm_data.get("ManagedInstances", [])
        maintenance_windows = ssm_data.get("MaintenanceWindows", [])

        # Check for patch baselines
        if not patch_baselines:
            logger.debug("SSM FAILS SI-2: No patch baselines configured")
            return "FAIL"

        # Check patch compliance on instances
        if managed_instances:
            instances_with_patches = [i for i in managed_instances if i.get("PatchSummary")]
            if not instances_with_patches:
                logger.debug("SSM FAILS SI-2: No patch data available for managed instances")
                return "FAIL"

            # Check for missing patches
            total_missing = sum(i.get("PatchSummary", {}).get("Missing", 0) for i in instances_with_patches)
            if total_missing > 0:
                logger.debug(f"SSM FAILS SI-2: {total_missing} missing patches across managed instances")
                return "FAIL"

        # Check for maintenance windows (recommended but not required)
        if not maintenance_windows:
            logger.debug("SSM PASSES SI-2: Patch baselines configured (maintenance windows recommended)")
        else:
            logger.debug(
                f"SSM PASSES SI-2: {len(patch_baselines)} baselines, {len(maintenance_windows)} maintenance windows"
            )

        return "PASS"

    def _assess_cm3(self, ssm_data: Dict) -> str:
        """
        Assess CM-3 (Configuration Change Control) compliance.

        :param Dict ssm_data: SSM configuration data
        :return: Compliance result (PASS/FAIL)
        :rtype: str
        """
        documents = ssm_data.get("Documents", [])

        # Check for Automation documents for change control
        automation_docs = [d for d in documents if d.get("DocumentType") == "Automation"]

        if not automation_docs:
            logger.debug("SSM FAILS CM-3: No Automation documents configured for change control")
            return "FAIL"

        logger.debug(f"SSM PASSES CM-3: {len(automation_docs)} Automation documents configured")
        return "PASS"

    def _assess_cm8(self, ssm_data: Dict) -> str:
        """
        Assess CM-8 (System Component Inventory) compliance.

        :param Dict ssm_data: SSM configuration data
        :return: Compliance result (PASS/FAIL)
        :rtype: str
        """
        managed_instances = ssm_data.get("ManagedInstances", [])

        # Check if SSM Inventory is collecting data
        if not managed_instances:
            logger.debug("SSM FAILS CM-8: No managed instances for inventory collection")
            return "FAIL"

        # Check if instances are reporting
        online_instances = [i for i in managed_instances if i.get("PingStatus") == "Online"]
        if not online_instances:
            logger.debug("SSM FAILS CM-8: No online instances reporting inventory data")
            return "FAIL"

        logger.debug(f"SSM PASSES CM-8: {len(online_instances)} instances reporting inventory data")
        return "PASS"

    def get_control_description(self, control_id: str) -> Optional[str]:
        """Get human-readable description for a control."""
        control_data = self.mappings.get(control_id)
        if control_data:
            return f"{control_data.get('name')}: {control_data.get('description', '')}"
        return None

    def get_mapped_controls(self) -> List[str]:
        """Get list of all control IDs mapped for this framework."""
        return list(self.mappings.keys())

    def get_check_details(self, control_id: str) -> Optional[Dict]:
        """Get detailed check criteria for a control."""
        control_data = self.mappings.get(control_id)
        if control_data:
            return control_data.get("checks", {})
        return None
