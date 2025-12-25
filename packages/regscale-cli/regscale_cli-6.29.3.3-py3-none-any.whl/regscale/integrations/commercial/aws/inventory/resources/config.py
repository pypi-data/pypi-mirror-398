"""AWS Config resource collection."""

import logging
from typing import Any, Dict, List, Optional

from botocore.exceptions import ClientError

from regscale.integrations.commercial.aws.inventory.base import BaseCollector

logger = logging.getLogger("regscale")


class ConfigCollector(BaseCollector):
    """Collector for AWS Config resources."""

    def __init__(
        self, session: Any, region: str, account_id: Optional[str] = None, tags: Optional[Dict[str, str]] = None
    ):
        """
        Initialize Config collector with filtering support.

        :param session: AWS session to use for API calls
        :param str region: AWS region to collect from
        :param str account_id: Optional AWS account ID to filter resources
        :param dict tags: Optional tags to filter resources (key-value pairs)
        """
        super().__init__(session, region, account_id, tags)

    def collect(self) -> Dict[str, Any]:
        """
        Collect AWS Config resources.

        :return: Dictionary containing Config recorders, rules, and compliance information
        :rtype: Dict[str, Any]
        """
        result = {
            "ConfigurationRecorders": [],
            "RecorderStatuses": [],
            "DeliveryChannels": [],
            "ConfigRules": [],
            "ComplianceSummary": [],
        }

        try:
            client = self._get_client("config")

            # Collect basic Config resources
            result["ConfigurationRecorders"] = self._describe_configuration_recorders(client)
            result["RecorderStatuses"] = self._describe_configuration_recorder_status(client)
            result["DeliveryChannels"] = self._describe_delivery_channels(client)

            # Get and filter config rules
            config_rules = self._describe_config_rules(client)
            filtered_rules = self._filter_config_rules(client, config_rules)
            result["ConfigRules"] = filtered_rules

            # Get compliance information
            result["ComplianceSummary"] = self._collect_compliance_summary(client, filtered_rules)

            logger.info(
                f"Collected {len(result['ConfigurationRecorders'])} Config recorder(s), "
                f"{len(filtered_rules)} rule(s) from {self.region}"
            )

        except ClientError as e:
            self._handle_error(e, "AWS Config resources")
        except Exception as e:
            logger.error(f"Unexpected error collecting AWS Config resources: {e}", exc_info=True)

        return result

    def _filter_config_rules(self, client: Any, config_rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter config rules by account ID and tags if specified.

        :param client: Config client
        :param List[Dict[str, Any]] config_rules: List of config rules to filter
        :return: Filtered list of config rules
        :rtype: List[Dict[str, Any]]
        """
        filtered_rules = []
        for rule in config_rules:
            if self._should_include_rule(client, rule):
                filtered_rules.append(rule)
        return filtered_rules

    def _should_include_rule(self, client: Any, rule: Dict[str, Any]) -> bool:
        """
        Determine if a config rule should be included based on filters.

        :param client: Config client
        :param Dict[str, Any] rule: Config rule to check
        :return: True if rule should be included, False otherwise
        :rtype: bool
        """
        rule_arn = rule.get("ConfigRuleArn", "")

        # Filter by account ID if specified using BaseCollector method
        if not self._matches_account(rule_arn):
            logger.debug(f"Skipping rule {rule_arn} - does not match account ID {self.account_id}")
            return False

        # Get tags for filtering using BaseCollector method
        if self.tags:
            rule_tags = self._get_rule_tags(client, rule_arn)
            if not self._matches_tags(rule_tags):
                logger.debug(f"Skipping rule {rule_arn} - does not match tag filters")
                return False
            rule["Tags"] = rule_tags

        return True

    def _collect_compliance_summary(self, client: Any, filtered_rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Collect compliance information for filtered rules.

        :param client: Config client
        :param List[Dict[str, Any]] filtered_rules: List of filtered config rules
        :return: List of compliance summaries
        :rtype: List[Dict[str, Any]]
        """
        compliance_summary = []
        for rule in filtered_rules:
            rule_name = rule.get("ConfigRuleName")
            if rule_name:
                compliance = self._describe_compliance_by_config_rule(client, rule_name)
                if compliance:
                    compliance_summary.append(compliance)
        return compliance_summary

    def _describe_configuration_recorders(self, client: Any) -> List[Dict[str, Any]]:
        """
        Describe configuration recorders.

        :param client: Config client
        :return: List of configuration recorders
        :rtype: List[Dict[str, Any]]
        """
        try:
            response = client.describe_configuration_recorders()
            recorders = response.get("ConfigurationRecorders", [])

            # Add region information
            for recorder in recorders:
                recorder["Region"] = self.region

            return recorders
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDeniedException":
                logger.warning(f"Access denied to describe configuration recorders in {self.region}")
                return []
            raise

    def _describe_configuration_recorder_status(self, client: Any) -> List[Dict[str, Any]]:
        """
        Describe configuration recorder status.

        :param client: Config client
        :return: List of recorder statuses
        :rtype: List[Dict[str, Any]]
        """
        try:
            response = client.describe_configuration_recorder_status()
            statuses = response.get("ConfigurationRecordersStatus", [])

            # Add region information
            for status in statuses:
                status["Region"] = self.region

            return statuses
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDeniedException":
                logger.warning(f"Access denied to describe configuration recorder status in {self.region}")
                return []
            logger.error(f"Error describing configuration recorder status: {e}")
            return []

    def _describe_delivery_channels(self, client: Any) -> List[Dict[str, Any]]:
        """
        Describe delivery channels.

        :param client: Config client
        :return: List of delivery channels
        :rtype: List[Dict[str, Any]]
        """
        try:
            response = client.describe_delivery_channels()
            channels = response.get("DeliveryChannels", [])

            # Add region information
            for channel in channels:
                channel["Region"] = self.region

            return channels
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDeniedException":
                logger.warning(f"Access denied to describe delivery channels in {self.region}")
                return []
            logger.error(f"Error describing delivery channels: {e}")
            return []

    def _describe_config_rules(self, client: Any) -> List[Dict[str, Any]]:
        """
        Describe AWS Config rules with pagination support.

        :param client: Config client
        :return: List of config rules
        :rtype: List[Dict[str, Any]]
        """
        rules = []
        next_token = None

        try:
            while True:
                params = {}
                if next_token:
                    params["NextToken"] = next_token

                response = client.describe_config_rules(**params)
                rules.extend(response.get("ConfigRules", []))

                next_token = response.get("NextToken")
                if not next_token:
                    break

            # Add region information
            for rule in rules:
                rule["Region"] = self.region

        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDeniedException":
                logger.warning(f"Access denied to describe config rules in {self.region}")
            else:
                logger.error(f"Error describing config rules: {e}")

        return rules

    def _describe_compliance_by_config_rule(self, client: Any, rule_name: str) -> Optional[Dict[str, Any]]:
        """
        Get compliance information for a specific config rule.

        :param client: Config client
        :param str rule_name: Name of the config rule
        :return: Compliance information or None
        :rtype: Optional[Dict[str, Any]]
        """
        try:
            response = client.describe_compliance_by_config_rule(ConfigRuleNames=[rule_name])
            compliance_by_rules = response.get("ComplianceByConfigRules", [])

            if compliance_by_rules:
                compliance = compliance_by_rules[0]
                compliance["Region"] = self.region
                return compliance

            return None
        except ClientError as e:
            if e.response["Error"]["Code"] != "AccessDeniedException":
                logger.error(f"Error getting compliance for rule {rule_name}: {e}")
            return None

    def get_compliance_details(
        self, rule_name: str, compliance_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get detailed compliance information for a config rule.

        :param str rule_name: Name of the config rule
        :param List[str] compliance_types: Optional list of compliance types to filter
        :return: List of compliance details
        :rtype: List[Dict[str, Any]]
        """
        details = []
        next_token = None

        try:
            client = self._get_client("config")

            while True:
                params = {"ConfigRuleName": rule_name}

                if compliance_types:
                    params["ComplianceTypes"] = compliance_types

                if next_token:
                    params["NextToken"] = next_token

                response = client.get_compliance_details_by_config_rule(**params)
                evaluation_results = response.get("EvaluationResults", [])

                for result in evaluation_results:
                    result["Region"] = self.region

                details.extend(evaluation_results)

                next_token = response.get("NextToken")
                if not next_token:
                    break

        except ClientError as e:
            self._handle_error(e, f"compliance details for rule {rule_name}")

        return details

    def _get_rule_tags(self, client: Any, rule_arn: str) -> Dict[str, str]:
        """
        Get tags for an AWS Config rule.

        :param client: Config client
        :param str rule_arn: Config rule ARN
        :return: Dictionary of tags (TagKey -> TagValue)
        :rtype: Dict[str, str]
        """
        try:
            response = client.list_tags_for_resource(ResourceArn=rule_arn)
            tags_list = response.get("Tags", [])
            return {tag["Key"]: tag["Value"] for tag in tags_list}
        except ClientError as e:
            logger.debug(f"Error getting tags for config rule {rule_arn}: {e}")
            return {}

    def get_conformance_packs(self) -> List[Dict[str, Any]]:
        """
        Get deployed conformance packs.

        :return: List of conformance packs
        :rtype: List[Dict[str, Any]]
        """
        packs = []
        next_token = None

        try:
            client = self._get_client("config")

            while True:
                params = {}
                if next_token:
                    params["NextToken"] = next_token

                response = client.describe_conformance_packs(**params)
                pack_details = response.get("ConformancePackDetails", [])

                for pack in pack_details:
                    pack["Region"] = self.region

                packs.extend(pack_details)

                next_token = response.get("NextToken")
                if not next_token:
                    break

        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDeniedException":
                logger.warning(f"Access denied to describe conformance packs in {self.region}")
            else:
                logger.error(f"Error describing conformance packs: {e}")

        return packs

    def get_conformance_pack_compliance(self, pack_name: str) -> Dict[str, Any]:
        """
        Get compliance status for a conformance pack.

        :param str pack_name: Name of the conformance pack
        :return: Conformance pack compliance status
        :rtype: Dict[str, Any]
        """
        try:
            client = self._get_client("config")
            response = client.describe_conformance_pack_status(ConformancePackNames=[pack_name])
            statuses = response.get("ConformancePackStatusDetails", [])

            if statuses:
                status = statuses[0]
                status["Region"] = self.region
                return status

            return {}
        except ClientError as e:
            if e.response["Error"]["Code"] != "AccessDeniedException":
                logger.error(f"Error getting conformance pack compliance for {pack_name}: {e}")
            return {}

    def get_conformance_pack_compliance_details(self, pack_name: str) -> List[Dict[str, Any]]:
        """
        Get detailed compliance information for all rules in a conformance pack.

        :param str pack_name: Name of the conformance pack
        :return: List of rule compliance details
        :rtype: List[Dict[str, Any]]
        """
        details = []
        next_token = None

        try:
            client = self._get_client("config")

            while True:
                params = {"ConformancePackName": pack_name}

                if next_token:
                    params["NextToken"] = next_token

                response = client.get_conformance_pack_compliance_details(**params)
                rule_details = response.get("ConformancePackRuleCompliances", [])

                for rule in rule_details:
                    rule["Region"] = self.region
                    rule["ConformancePackName"] = pack_name

                details.extend(rule_details)

                next_token = response.get("NextToken")
                if not next_token:
                    break

        except ClientError as e:
            self._handle_error(e, f"conformance pack compliance details for {pack_name}")

        return details

    def get_aggregate_compliance_by_control(
        self, control_mappings: Dict[str, List[str]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Aggregate Config rule compliance by control ID.

        :param Dict[str, List[str]] control_mappings: Map of control_id -> list of rule names
        :return: Dictionary mapping control_id to list of rule evaluation results
        :rtype: Dict[str, List[Dict[str, Any]]]
        """
        control_compliance = {}

        try:
            client = self._get_client("config")

            for control_id, rule_names in control_mappings.items():
                control_compliance[control_id] = []

                for rule_name in rule_names:
                    # Get compliance summary for this rule
                    compliance = self._describe_compliance_by_config_rule(client, rule_name)

                    if compliance:
                        # Get detailed evaluation results
                        details = self.get_compliance_details(rule_name)

                        evaluation_result = {
                            "control_id": control_id,
                            "rule_name": rule_name,
                            "compliance_type": compliance.get("Compliance", {}).get("ComplianceType", ""),
                            "compliance_summary": compliance.get("Compliance", {}),
                            "evaluation_details": details,
                            "non_compliant_resource_count": sum(
                                1 for d in details if d.get("ComplianceType") == "NON_COMPLIANT"
                            ),
                        }

                        control_compliance[control_id].append(evaluation_result)

        except Exception as e:
            logger.error(f"Error aggregating compliance by control: {e}", exc_info=True)

        return control_compliance
