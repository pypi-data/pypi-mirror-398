"""This module contains the Compliance Settings model class."""

from typing import ClassVar, Dict, List, Optional

from pydantic import ConfigDict

from regscale.models.regscale_models.regscale_model import RegScaleModel

# Import the actual RegScale ControlImplementationStatus enum
from regscale.models.regscale_models.control_implementation import ControlImplementationStatus

# Constants
NOT_APPLICABLE_KEY = "not applicable"


class ComplianceSettings(RegScaleModel):
    """
    Compliance Settings model class
    """

    _module_slug = "settings"
    _module_slug_id_url = "/api/compliance/{model_slug}/{id}"
    _unique_fields = [
        ["title"],
    ]

    id: int
    title: str
    hasParts: bool = True
    wayfinderOptionId: Optional[int] = None
    profileIds: Optional[List] = None
    complianceSettingsFieldGroups: Optional[List] = None

    @classmethod
    def get_by_current_tenant(cls) -> List["ComplianceSettings"]:
        """
        Get a list of compliance settings by current tenant.

        :return: A list of compliance settings
        :rtype: List[ComplianceSettings]
        """
        response = cls._get_api_handler().get(
            endpoint=cls.get_endpoint("get_by_current_tenant").format(model_slug=cls._module_slug)
        )
        compliance_settings = []
        if response and response.ok:
            for setting in response.json():
                compliance_settings.append(ComplianceSettings(**setting))
        return compliance_settings

    @staticmethod
    def _get_additional_endpoints() -> ConfigDict:
        """
        Get additional endpoints for the ComplianceSettings model.

        :return: A dictionary of additional endpoints
        :rtype: ConfigDict
        """
        return ConfigDict(  # type: ignore
            get_by_current_tenant="/api/compliance/{model_slug}",  # type: ignore
            get_by_compliance_id="/api/compliance/{model_slug}/{id}/",  # type: ignore
        )

    @classmethod
    def _get_endpoints(cls) -> ConfigDict:
        """
        Get the endpoints for the API.

        :return: A dictionary of endpoints
        :rtype: ConfigDict
        """
        endpoints = ConfigDict(  # type: ignore
            get=cls._module_slug_id_url,  # type: ignore
            insert="/api/compliance/{model_slug}/",  # type: ignore
            update=cls._module_slug_id_url,  # type: ignore
            delete=cls._module_slug_id_url,  # type: ignore
        )
        endpoints.update(cls._get_additional_endpoints())
        return endpoints

    @classmethod
    def get_labels(cls, setting_id: int, setting_field: str) -> List[str]:
        """
        Get the labels for the ComplianceSettings model.

        :param int setting_id: The ID of the compliance setting
        :param str setting_field: The field of the compliance setting
        :return: A list of labels
        :rtype: List[str]
        """
        compliance_setting = None
        response = cls._get_api_handler().get(
            endpoint=cls.get_endpoint("get_by_compliance_id").format(model_slug=cls._module_slug, id=setting_id)
        )
        labels = []
        if response and response.ok:
            compliance_setting = cls(**response.json())
        else:
            return labels
        if not compliance_setting:
            return labels
        if compliance_setting.complianceSettingsFieldGroups:
            for group in compliance_setting.complianceSettingsFieldGroups:
                if group["formFieldId"] == setting_field:
                    for item in group["complianceSettingsList"]:
                        labels.append(item["statusName"])

        return labels

    def get_field_labels(self, setting_field: str) -> List[str]:
        """
        Get the labels for the specified field from this compliance setting.

        :param str setting_field: The field of the compliance setting
        :return: A list of labels
        :rtype: List[str]
        """
        return self.__class__.get_labels(self.id, setting_field)

    @classmethod
    def get_settings_list(cls) -> List[dict]:
        """
        Get all compliance settings list items from settingsList endpoint.

        :return: A list of compliance settings list items
        :rtype: List[dict]
        """
        response = cls._get_api_handler().get(endpoint="/api/compliance/settingsList")
        if response and response.ok:
            return response.json()
        return []

    @classmethod
    def get_default_responsibility_for_compliance_setting(cls, compliance_setting_id: int) -> Optional[str]:
        """
        Get the default responsibility value for a specific compliance setting.

        :param int compliance_setting_id: The compliance setting ID
        :return: The default responsibility value or None if not found
        :rtype: Optional[str]
        """
        settings_list = cls.get_settings_list()
        for setting in settings_list:
            if setting.get("complianceSettingId") == compliance_setting_id and setting.get("isDefault", False):
                return setting.get("statusName")
        return None

    # Status mapping dictionaries for different frameworks using actual RegScale values
    DOD_STATUS_MAPPINGS: ClassVar[Dict[str, str]] = {
        "pass": ControlImplementationStatus.Implemented.value,
        "fail": ControlImplementationStatus.NotImplemented.value,
        NOT_APPLICABLE_KEY: ControlImplementationStatus.NA.value,
        "n/a": ControlImplementationStatus.NA.value,
        "na": ControlImplementationStatus.NA.value,
        "planned": ControlImplementationStatus.Planned.value,
        "alternative": ControlImplementationStatus.Alternative.value,
        "partial": ControlImplementationStatus.PartiallyImplemented.value,
        "unknown": ControlImplementationStatus.Planned.value,
    }

    FEDRAMP_STATUS_MAPPINGS: ClassVar[Dict[str, str]] = {
        "pass": ControlImplementationStatus.Implemented.value,
        "fail": ControlImplementationStatus.InRemediation.value,
        "partial": ControlImplementationStatus.PartiallyImplemented.value,
        NOT_APPLICABLE_KEY: ControlImplementationStatus.NA.value,
        "n/a": ControlImplementationStatus.NA.value,
        "na": ControlImplementationStatus.NA.value,
        "planned": ControlImplementationStatus.Planned.value,
        "alternative": ControlImplementationStatus.Alternative.value,
    }

    NIST_STATUS_MAPPINGS: ClassVar[Dict[str, str]] = {
        "pass": ControlImplementationStatus.FullyImplemented.value,
        "fail": ControlImplementationStatus.NotImplemented.value,
        "partial": ControlImplementationStatus.PartiallyImplemented.value,
        NOT_APPLICABLE_KEY: ControlImplementationStatus.NA.value,
        "n/a": ControlImplementationStatus.NA.value,
        "na": ControlImplementationStatus.NA.value,
        "planned": ControlImplementationStatus.Planned.value,
    }

    DEFAULT_STATUS_MAPPINGS: ClassVar[Dict[str, str]] = {
        "pass": ControlImplementationStatus.FullyImplemented.value,
        "fail": ControlImplementationStatus.InRemediation.value,
        "partial": ControlImplementationStatus.PartiallyImplemented.value,
        NOT_APPLICABLE_KEY: ControlImplementationStatus.NA.value,
        "n/a": ControlImplementationStatus.NA.value,
        "na": ControlImplementationStatus.NA.value,
        "remediation": ControlImplementationStatus.InRemediation.value,
        "planned": ControlImplementationStatus.Planned.value,
        "inherited": ControlImplementationStatus.Inherited.value,
        "risk accepted": ControlImplementationStatus.RiskAccepted.value,
        "archived": ControlImplementationStatus.Archived.value,
    }

    @classmethod
    def get_status_mapping(cls, framework: str, result: str, override: Optional[str] = None) -> str:
        """
        Get the implementation status mapping for a given result and framework.

        :param str framework: The compliance framework (DoD, FedRAMP, NIST, or Default)
        :param str result: The assessment result (Pass, Fail, Not Applicable, etc.)
        :param Optional[str] override: Optional override value to use instead of the mapping
        :return: The mapped implementation status
        :rtype: str
        """
        # Use override if provided
        if override:
            return override

        # Normalize result to lowercase
        result_lower = result.lower().strip()

        # Select the appropriate mapping based on framework
        if framework.upper() in ["DOD", "RMF", "DEFENSE"]:
            mappings = cls.DOD_STATUS_MAPPINGS
            default_fail = ControlImplementationStatus.NotImplemented.value
        elif framework.upper() == "FEDRAMP":
            mappings = cls.FEDRAMP_STATUS_MAPPINGS
            default_fail = ControlImplementationStatus.InRemediation.value
        elif framework.upper() in ["NIST", "800-53", "FISMA"]:
            mappings = cls.NIST_STATUS_MAPPINGS
            default_fail = ControlImplementationStatus.NotImplemented.value
        else:
            mappings = cls.DEFAULT_STATUS_MAPPINGS
            default_fail = ControlImplementationStatus.InRemediation.value

        # Get the mapped status
        if result_lower in mappings:
            return mappings[result_lower]

        # Handle common variations
        if result_lower in ["passed", "passing", "compliant", "success"]:
            return mappings.get("pass", ControlImplementationStatus.FullyImplemented.value)
        elif result_lower in ["failed", "failing", "non-compliant", "failure"]:
            return mappings.get("fail", default_fail)

        # Default to a reasonable value based on result type
        if "pass" in result_lower or "implement" in result_lower:
            return mappings.get("pass", ControlImplementationStatus.FullyImplemented.value)
        elif "fail" in result_lower or "not" in result_lower:
            return mappings.get("fail", default_fail)
        elif "n/a" in result_lower or NOT_APPLICABLE_KEY in result_lower:
            return mappings.get(NOT_APPLICABLE_KEY, ControlImplementationStatus.NA.value)

        # If nothing matches, return a sensible default
        return default_fail

    def _detect_framework_from_title(self) -> str:
        """
        Detect framework type from compliance setting title.

        :return: Framework name ("DoD", "FedRAMP", "NIST", or "Default")
        :rtype: str
        """
        if not self.title:
            return "Default"

        title_lower = self.title.lower()
        if any(kw in title_lower for kw in ["dod", "rmf", "defense"]):
            return "DoD"
        elif "fedramp" in title_lower:
            return "FedRAMP"
        elif any(kw in title_lower for kw in ["nist", "800-53", "fisma"]):
            return "NIST"
        return "Default"

    def _find_compatible_pass_label(self, available_labels: List[str]) -> Optional[str]:
        """
        Find a compatible label for Pass results from available labels.

        :param List[str] available_labels: Available status labels
        :return: Compatible label or None
        :rtype: Optional[str]
        """
        for label in available_labels:
            if any(kw in label.lower() for kw in ["implemented", "complete", "satisfied"]):
                return label
        return None

    def _find_compatible_fail_label(self, available_labels: List[str]) -> Optional[str]:
        """
        Find a compatible label for Fail results from available labels.

        :param List[str] available_labels: Available status labels
        :return: Compatible label or None
        :rtype: Optional[str]
        """
        for label in available_labels:
            if any(kw in label.lower() for kw in ["not implemented", "remediation", "planned"]):
                return label
        return None

    def _find_compatible_na_label(self, available_labels: List[str]) -> Optional[str]:
        """
        Find a compatible label for Not Applicable results from available labels.

        :param List[str] available_labels: Available status labels
        :return: Compatible label or None
        :rtype: Optional[str]
        """
        for label in available_labels:
            if any(kw in label.lower() for kw in [NOT_APPLICABLE_KEY, "n/a"]):
                return label
        return None

    def _find_fallback_status(self, result: str, available_labels: List[str]) -> Optional[str]:
        """
        Find a fallback status based on result type when exact match not found.

        :param str result: The assessment result
        :param List[str] available_labels: Available status labels
        :return: Fallback status or None
        :rtype: Optional[str]
        """
        result_lower = result.lower().strip()

        # For Pass results
        if result_lower in ["pass", "passed", "passing"]:
            return self._find_compatible_pass_label(available_labels)

        # For Fail results
        if result_lower in ["fail", "failed", "failing"]:
            return self._find_compatible_fail_label(available_labels)

        # For Not Applicable
        if result_lower in [NOT_APPLICABLE_KEY, "n/a", "na"]:
            return self._find_compatible_na_label(available_labels)

        return None

    def get_implementation_status_for_result(self, result: str, override: Optional[str] = None) -> str:
        """
        Get the implementation status for a given assessment result based on this compliance setting.

        :param str result: The assessment result (Pass, Fail, Not Applicable, etc.)
        :param Optional[str] override: Optional override value to use instead of the mapping
        :return: The mapped implementation status that exists in this compliance setting
        :rtype: str
        """
        # Detect framework from title
        framework = self._detect_framework_from_title()

        # Get the mapped status
        mapped_status = self.get_status_mapping(framework, result, override)

        # Check if this status exists in the available labels
        available_labels = self.get_field_labels("implementationStatus")
        if available_labels and mapped_status in available_labels:
            return mapped_status

        # If mapped status doesn't exist, try to find a compatible one
        if available_labels:
            fallback_status = self._find_fallback_status(result, available_labels)
            if fallback_status:
                return fallback_status

            # If no match found, return first available
            return available_labels[0]

        # Return the mapped status even if not in labels (fallback)
        return mapped_status
