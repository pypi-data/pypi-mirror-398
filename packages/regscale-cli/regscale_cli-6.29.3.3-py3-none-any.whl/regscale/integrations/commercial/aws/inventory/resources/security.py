"""AWS security resource collectors."""

from typing import Dict, List, Any, Optional

from regscale.integrations.commercial.aws.inventory.resources.audit_manager import AuditManagerCollector
from regscale.integrations.commercial.aws.inventory.resources.cloudtrail import CloudTrailCollector
from regscale.integrations.commercial.aws.inventory.resources.config import ConfigCollector
from regscale.integrations.commercial.aws.inventory.resources.guardduty import GuardDutyCollector
from regscale.integrations.commercial.aws.inventory.resources.iam import IAMCollector
from regscale.integrations.commercial.aws.inventory.resources.inspector import InspectorCollector
from regscale.integrations.commercial.aws.inventory.resources.kms import KMSCollector
from regscale.integrations.commercial.aws.inventory.resources.securityhub import SecurityHubCollector
from ..base import BaseCollector


class SecurityCollector(BaseCollector):
    """Collector for AWS security resources."""

    def __init__(
        self,
        session: Any,
        region: str,
        account_id: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        enabled_services: Optional[Dict[str, bool]] = None,
        collect_findings: bool = True,
    ):
        """
        Initialize security collector.

        :param session: AWS session to use for API calls
        :param str region: AWS region to collect from
        :param str account_id: Optional AWS account ID to filter resources
        :param dict tags: Optional tags to filter resources (key-value pairs)
        :param dict enabled_services: Optional dict of service names to boolean flags for enabling/disabling collection
        :param bool collect_findings: Whether to collect security findings (GuardDuty, Security Hub, Inspector)
        """
        super().__init__(session, region)
        self.account_id = account_id
        self.tags = tags or {}
        self.enabled_services = enabled_services or {}
        self.collect_findings = collect_findings

    def get_cloudtrail_info(self) -> Dict[str, Any]:
        """
        Get information about CloudTrail trails.

        :return: Dictionary containing CloudTrail trail information
        :rtype: Dict[str, Any]
        """
        try:
            cloudtrail_collector = CloudTrailCollector(self.session, self.region, self.account_id)
            return cloudtrail_collector.collect()
        except Exception as e:
            self._handle_error(e, "CloudTrail trails")
            return {"Trails": [], "TrailStatuses": {}}

    def get_config_info(self) -> Dict[str, Any]:
        """
        Get information about AWS Config resources.

        :return: Dictionary containing AWS Config information
        :rtype: Dict[str, Any]
        """
        try:
            config_collector = ConfigCollector(self.session, self.region, self.account_id)
            return config_collector.collect()
        except Exception as e:
            self._handle_error(e, "AWS Config resources")
            return {
                "ConfigurationRecorders": [],
                "RecorderStatuses": [],
                "DeliveryChannels": [],
                "ConfigRules": [],
                "ComplianceSummary": [],
            }

    def get_guardduty_info(self) -> Dict[str, Any]:
        """
        Get information about GuardDuty resources.

        :return: Dictionary containing GuardDuty information
        :rtype: Dict[str, Any]
        """
        try:
            guardduty_collector = GuardDutyCollector(
                self.session, self.region, self.account_id, self.tags, self.collect_findings
            )
            return guardduty_collector.collect()
        except Exception as e:
            self._handle_error(e, "GuardDuty resources")
            return {"Detectors": [], "Findings": [], "Members": []}

    def get_iam_info(self) -> Dict[str, Any]:
        """
        Get information about IAM resources.

        :return: Dictionary containing IAM resource information
        :rtype: Dict[str, Any]
        """
        try:
            iam_collector = IAMCollector(self.session, self.region, self.account_id)
            return iam_collector.collect()
        except Exception as e:
            self._handle_error(e, "IAM resources")
            return {
                "Users": [],
                "Roles": [],
                "Groups": [],
                "Policies": [],
                "AccessKeys": [],
                "MFADevices": [],
                "AccountSummary": {},
                "PasswordPolicy": {},
            }

    def get_kms_keys(self) -> List[Dict[str, Any]]:
        """
        Get information about KMS keys.

        :return: List of KMS key information
        :rtype: List[Dict[str, Any]]
        """
        try:
            kms_collector = KMSCollector(self.session, self.region, self.account_id)
            result = kms_collector.collect()
            return result.get("Keys", [])
        except Exception as e:
            self._handle_error(e, "KMS keys")
            return []

    def get_secrets(self) -> List[Dict[str, Any]]:
        """
        Get information about Secrets Manager secrets.

        :return: List of secret information
        :rtype: List[Dict[str, Any]]
        """
        secrets = []
        try:
            sm = self._get_client("secretsmanager")
            paginator = sm.get_paginator("list_secrets")

            for page in paginator.paginate():
                for secret in page.get("SecretList", []):
                    secrets.append(
                        {
                            "Region": self.region,
                            "Name": secret.get("Name"),
                            "ARN": secret.get("ARN"),
                            "Description": secret.get("Description"),
                            "KmsKeyId": secret.get("KmsKeyId"),
                            "LastChangedDate": str(secret.get("LastChangedDate")),
                            "LastAccessedDate": str(secret.get("LastAccessedDate")),
                            "Tags": secret.get("Tags", []),
                            "SecretVersionsToStages": secret.get("SecretVersionsToStages", {}),
                        }
                    )
        except Exception as e:
            self._handle_error(e, "Secrets Manager secrets")
        return secrets

    def get_waf_info(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get information about WAF configurations.

        :return: Dictionary containing WAF configuration information
        :rtype: Dict[str, List[Dict[str, Any]]]
        """
        waf_info = {"WebACLs": [], "IPSets": [], "RuleGroups": []}
        try:
            wafv2 = self._get_client("wafv2")

            # Get Web ACLs
            web_acls = wafv2.list_web_acls(Scope="REGIONAL")
            for acl in web_acls.get("WebACLs", []):
                try:
                    acl_detail = wafv2.get_web_acl(Name=acl["Name"], Id=acl["Id"], Scope="REGIONAL")
                    waf_info["WebACLs"].append(
                        {
                            "Region": self.region,
                            "Name": acl.get("Name"),
                            "Id": acl.get("Id"),
                            "ARN": acl.get("ARN"),
                            "Description": acl.get("Description"),
                            "Rules": acl_detail.get("WebACL", {}).get("Rules", []),
                        }
                    )
                except Exception as e:
                    self._handle_error(e, f"WAF Web ACL {acl['Name']}")

            # Get IP Sets
            ip_sets = wafv2.list_ip_sets(Scope="REGIONAL")
            for ip_set in ip_sets.get("IPSets", []):
                try:
                    ip_set_detail = wafv2.get_ip_set(Name=ip_set["Name"], Id=ip_set["Id"], Scope="REGIONAL")
                    waf_info["IPSets"].append(
                        {
                            "Region": self.region,
                            "Name": ip_set.get("Name"),
                            "Id": ip_set.get("Id"),
                            "ARN": ip_set.get("ARN"),
                            "Description": ip_set.get("Description"),
                            "Addresses": ip_set_detail.get("IPSet", {}).get("Addresses", []),
                        }
                    )
                except Exception as e:
                    self._handle_error(e, f"WAF IP Set {ip_set['Name']}")

            # Get Rule Groups
            rule_groups = wafv2.list_rule_groups(Scope="REGIONAL")
            for group in rule_groups.get("RuleGroups", []):
                try:
                    group_detail = wafv2.get_rule_group(Name=group["Name"], Id=group["Id"], Scope="REGIONAL")
                    waf_info["RuleGroups"].append(
                        {
                            "Region": self.region,
                            "Name": group.get("Name"),
                            "Id": group.get("Id"),
                            "ARN": group.get("ARN"),
                            "Description": group.get("Description"),
                            "Rules": group_detail.get("RuleGroup", {}).get("Rules", []),
                        }
                    )
                except Exception as e:
                    self._handle_error(e, f"WAF Rule Group {group['Name']}")
        except Exception as e:
            self._handle_error(e, "WAF configurations")
        return waf_info

    def get_acm_certificates(self) -> List[Dict[str, Any]]:
        """
        Get information about ACM certificates.

        :return: List of certificate information
        :rtype: List[Dict[str, Any]]
        """
        certificates = []
        try:
            acm = self._get_client("acm")
            paginator = acm.get_paginator("list_certificates")

            for page in paginator.paginate():
                for cert in page.get("CertificateSummaryList", []):
                    try:
                        cert_detail = acm.describe_certificate(CertificateArn=cert["CertificateArn"])["Certificate"]
                        certificates.append(
                            {
                                "Region": self.region,
                                "DomainName": cert_detail.get("DomainName"),
                                "CertificateArn": cert_detail.get("CertificateArn"),
                                "Status": cert_detail.get("Status"),
                                "Type": cert_detail.get("Type"),
                                "IssueDate": str(cert_detail.get("IssuedAt")) if cert_detail.get("IssuedAt") else None,
                                "ExpiryDate": str(cert_detail.get("NotAfter")) if cert_detail.get("NotAfter") else None,
                                "SubjectAlternativeNames": cert_detail.get("SubjectAlternativeNames", []),
                                "DomainValidationOptions": cert_detail.get("DomainValidationOptions", []),
                                "Tags": cert_detail.get("Tags", []),
                            }
                        )
                    except Exception as e:
                        self._handle_error(e, f"ACM certificate {cert['CertificateArn']}")
        except Exception as e:
            self._handle_error(e, "ACM certificates")
        return certificates

    def get_securityhub_info(self) -> Dict[str, Any]:
        """
        Get information about AWS Security Hub resources.

        :return: Dictionary containing Security Hub information
        :rtype: Dict[str, Any]
        """
        try:
            securityhub_collector = SecurityHubCollector(
                self.session, self.region, self.account_id, self.tags, self.collect_findings
            )
            return securityhub_collector.collect()
        except Exception as e:
            self._handle_error(e, "Security Hub resources")
            return {
                "Findings": [],
                "Standards": [],
                "EnabledStandards": [],
                "SecurityControls": [],
                "HubConfiguration": {},
                "Members": [],
                "Insights": [],
            }

    def get_audit_manager_info(self) -> Dict[str, Any]:
        """
        Get information about AWS Audit Manager resources.

        :return: Dictionary containing Audit Manager information
        :rtype: Dict[str, Any]
        """
        try:
            audit_manager_collector = AuditManagerCollector(self.session, self.region, self.account_id, self.tags)
            return audit_manager_collector.collect()
        except Exception as e:
            self._handle_error(e, "Audit Manager resources")
            return {
                "Assessments": [],
                "AssessmentFrameworks": [],
                "Controls": [],
                "AssessmentReports": [],
                "Evidence": [],
                "Settings": {},
            }

    def get_inspector_info(self) -> Dict[str, Any]:
        """
        Get information about AWS Inspector resources.

        :return: Dictionary containing Inspector information
        :rtype: Dict[str, Any]
        """
        try:
            inspector_collector = InspectorCollector(
                self.session, self.region, self.account_id, self.tags, self.collect_findings
            )
            return inspector_collector.collect()
        except Exception as e:
            self._handle_error(e, "Inspector resources")
            return {"Findings": [], "Coverage": [], "AccountStatus": {}, "Members": [], "CoverageStatistics": {}}

    def _collect_cloudtrail_data(self, result: Dict[str, Any]) -> None:
        """
        Collect CloudTrail data and add to result.

        :param result: Result dictionary to update
        """
        cloudtrail_info = self.get_cloudtrail_info()
        result["CloudTrail"] = cloudtrail_info.get("Trails", [])
        result["CloudTrailStatuses"] = cloudtrail_info.get("TrailStatuses", {})

    def _collect_config_data(self, result: Dict[str, Any]) -> None:
        """
        Collect AWS Config data and add to result.

        :param result: Result dictionary to update
        """
        config_info = self.get_config_info()
        result["ConfigRecorders"] = config_info.get("ConfigurationRecorders", [])
        result["ConfigRecorderStatuses"] = config_info.get("RecorderStatuses", [])
        result["ConfigDeliveryChannels"] = config_info.get("DeliveryChannels", [])
        result["ConfigRules"] = config_info.get("ConfigRules", [])
        result["ConfigComplianceSummary"] = config_info.get("ComplianceSummary", [])

    def _collect_guardduty_data(self, result: Dict[str, Any]) -> None:
        """
        Collect GuardDuty data and add to result.

        :param result: Result dictionary to update
        """
        guardduty_info = self.get_guardduty_info()
        result["GuardDutyDetectors"] = guardduty_info.get("Detectors", [])
        if self.collect_findings:
            result["GuardDutyFindings"] = guardduty_info.get("Findings", [])
        result["GuardDutyMembers"] = guardduty_info.get("Members", [])

    def _collect_securityhub_data(self, result: Dict[str, Any]) -> None:
        """
        Collect Security Hub data and add to result.

        :param result: Result dictionary to update
        """
        securityhub_info = self.get_securityhub_info()
        if self.collect_findings:
            result["SecurityHubFindings"] = securityhub_info.get("Findings", [])
        result["SecurityHubStandards"] = securityhub_info.get("Standards", [])
        result["SecurityHubEnabledStandards"] = securityhub_info.get("EnabledStandards", [])
        result["SecurityHubControls"] = securityhub_info.get("SecurityControls", [])
        result["SecurityHubConfig"] = securityhub_info.get("HubConfiguration", {})
        result["SecurityHubMembers"] = securityhub_info.get("Members", [])
        result["SecurityHubInsights"] = securityhub_info.get("Insights", [])

    def _collect_inspector_data(self, result: Dict[str, Any]) -> None:
        """
        Collect Inspector data and add to result.

        :param result: Result dictionary to update
        """
        inspector_info = self.get_inspector_info()
        if self.collect_findings:
            result["InspectorFindings"] = inspector_info.get("Findings", [])
        result["InspectorCoverage"] = inspector_info.get("Coverage", [])
        result["InspectorAccountStatus"] = inspector_info.get("AccountStatus", {})
        result["InspectorMembers"] = inspector_info.get("Members", [])
        result["InspectorCoverageStats"] = inspector_info.get("CoverageStatistics", {})

    def collect(self) -> Dict[str, Any]:
        """
        Collect security resources based on enabled_services configuration.

        :return: Dictionary containing enabled security resource information
        :rtype: Dict[str, Any]
        """
        result = {}

        if self.enabled_services.get("iam", True):
            result["IAM"] = self.get_iam_info()

        if self.enabled_services.get("kms", True):
            result["KMSKeys"] = self.get_kms_keys()

        if self.enabled_services.get("secrets_manager", True):
            result["Secrets"] = self.get_secrets()

        if self.enabled_services.get("waf", True):
            result["WAF"] = self.get_waf_info()

        if self.enabled_services.get("acm", True):
            result["ACMCertificates"] = self.get_acm_certificates()

        if self.enabled_services.get("cloudtrail", True):
            self._collect_cloudtrail_data(result)

        if self.enabled_services.get("config", True):
            self._collect_config_data(result)

        if self.enabled_services.get("guardduty", True):
            self._collect_guardduty_data(result)

        if self.enabled_services.get("securityhub", True):
            self._collect_securityhub_data(result)

        if self.enabled_services.get("inspector", True):
            self._collect_inspector_data(result)

        if self.enabled_services.get("audit_manager", True):
            audit_manager_info = self.get_audit_manager_info()
            result.update(audit_manager_info)

        return result
