"""AWS Security Hub resource collection."""

import logging
from typing import Any, Dict, List, Optional

from botocore.exceptions import ClientError

from regscale.integrations.commercial.aws.inventory.base import BaseCollector

logger = logging.getLogger("regscale")


class SecurityHubCollector(BaseCollector):
    """Collector for AWS Security Hub resources."""

    def __init__(
        self,
        session: Any,
        region: str,
        account_id: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        collect_findings: bool = True,
    ):
        """
        Initialize Security Hub collector.

        :param session: AWS session to use for API calls
        :param str region: AWS region to collect from
        :param str account_id: Optional AWS account ID to filter resources
        :param dict tags: Optional tags to filter resources (key-value pairs)
        :param bool collect_findings: Whether to collect Security Hub findings. Default True.
        """
        super().__init__(session, region)
        self.account_id = account_id
        self.tags = tags or {}
        self.collect_findings = collect_findings

    def collect(self) -> Dict[str, Any]:
        """
        Collect AWS Security Hub resources.

        :return: Dictionary containing Security Hub findings and configuration
        :rtype: Dict[str, Any]
        """
        result = {
            "Findings": [],
            "Standards": [],
            "EnabledStandards": [],
            "SecurityControls": [],
            "HubConfiguration": {},
            "Members": [],
            "Insights": [],
        }

        try:
            client = self._get_client("securityhub")

            # Get hub configuration
            hub_config = self._describe_hub(client)
            result["HubConfiguration"] = hub_config

            # Get enabled standards
            enabled_standards = self._get_enabled_standards(client)
            result["EnabledStandards"] = enabled_standards

            # Get standards
            standards = self._describe_standards(client)
            result["Standards"] = standards

            # Get security controls
            controls = self._list_security_controls(client)
            result["SecurityControls"] = controls

            # Get findings only if requested
            if self.collect_findings:
                findings = self._get_findings(client)
                result["Findings"] = findings
            else:
                findings = []
                logger.debug("Skipping Security Hub findings collection (collect_findings=False)")

            # Get insights
            insights = self._get_insights(client)
            result["Insights"] = insights

            # Get member accounts
            members = self._list_members(client)
            result["Members"] = members

            if self.collect_findings:
                logger.info(
                    f"Collected {len(findings)} Security Hub finding(s), "
                    f"{len(enabled_standards)} enabled standard(s) from {self.region}"
                )
            else:
                logger.info(f"Collected {len(enabled_standards)} enabled standard(s) from {self.region}")

        except ClientError as e:
            self._handle_error(e, "AWS Security Hub resources")
        except Exception as e:
            logger.error(f"Unexpected error collecting AWS Security Hub resources: {e}", exc_info=True)

        return result

    def _describe_hub(self, client: Any) -> Dict[str, Any]:
        """
        Describe Security Hub configuration.

        :param client: Security Hub client
        :return: Hub configuration
        :rtype: Dict[str, Any]
        """
        try:
            response = client.describe_hub()
            hub_config = {
                "Region": self.region,
                "HubArn": response.get("HubArn"),
                "SubscribedAt": str(response.get("SubscribedAt")),
                "AutoEnableControls": response.get("AutoEnableControls"),
                "ControlFindingGenerator": response.get("ControlFindingGenerator"),
            }
            return hub_config
        except ClientError as e:
            if e.response["Error"]["Code"] in ["InvalidAccessException", "ResourceNotFoundException"]:
                logger.warning(f"Security Hub not enabled or access denied in {self.region}")
            else:
                logger.error(f"Error describing Security Hub: {e}")
            return {}

    def _get_enabled_standards(self, client: Any) -> List[Dict[str, Any]]:
        """
        Get enabled Security Hub standards.

        :param client: Security Hub client
        :return: List of enabled standards
        :rtype: List[Dict[str, Any]]
        """
        standards = []
        next_token = None

        try:
            while True:
                params = {}
                if next_token:
                    params["NextToken"] = next_token

                response = client.get_enabled_standards(**params)
                standards_subscriptions = response.get("StandardsSubscriptions", [])

                for standard in standards_subscriptions:
                    standard_dict = {
                        "Region": self.region,
                        "StandardsSubscriptionArn": standard.get("StandardsSubscriptionArn"),
                        "StandardsArn": standard.get("StandardsArn"),
                        "StandardsInput": standard.get("StandardsInput", {}),
                        "StandardsStatus": standard.get("StandardsStatus"),
                    }
                    standards.append(standard_dict)

                next_token = response.get("NextToken")
                if not next_token:
                    break

        except ClientError as e:
            if e.response["Error"]["Code"] == "InvalidAccessException":
                logger.warning(f"Access denied to get enabled standards in {self.region}")
            else:
                logger.error(f"Error getting enabled standards: {e}")

        return standards

    def _describe_standards(self, client: Any) -> List[Dict[str, Any]]:
        """
        Describe available Security Hub standards.

        :param client: Security Hub client
        :return: List of available standards
        :rtype: List[Dict[str, Any]]
        """
        standards = []
        next_token = None

        try:
            while True:
                params = {}
                if next_token:
                    params["NextToken"] = next_token

                response = client.describe_standards(**params)
                standards_list = response.get("Standards", [])

                for standard in standards_list:
                    standard_dict = {
                        "Region": self.region,
                        "StandardsArn": standard.get("StandardsArn"),
                        "Name": standard.get("Name"),
                        "Description": standard.get("Description"),
                        "EnabledByDefault": standard.get("EnabledByDefault"),
                    }
                    standards.append(standard_dict)

                next_token = response.get("NextToken")
                if not next_token:
                    break

        except ClientError as e:
            if e.response["Error"]["Code"] == "InvalidAccessException":
                logger.warning(f"Access denied to describe standards in {self.region}")
            else:
                logger.error(f"Error describing standards: {e}")

        return standards

    def _list_security_controls(self, client: Any) -> List[Dict[str, Any]]:
        """
        List Security Hub security controls.

        :param client: Security Hub client
        :return: List of security controls
        :rtype: List[Dict[str, Any]]
        """
        controls = []
        next_token = None

        try:
            while True:
                params = {"MaxResults": 100}
                if next_token:
                    params["NextToken"] = next_token

                response = client.list_security_control_definitions(**params)
                control_list = response.get("SecurityControlDefinitions", [])

                for control in control_list:
                    control_dict = {
                        "Region": self.region,
                        "SecurityControlId": control.get("SecurityControlId"),
                        "Title": control.get("Title"),
                        "Description": control.get("Description"),
                        "RemediationUrl": control.get("RemediationUrl"),
                        "SeverityRating": control.get("SeverityRating"),
                        "CurrentRegionAvailability": control.get("CurrentRegionAvailability"),
                    }
                    controls.append(control_dict)

                next_token = response.get("NextToken")
                if not next_token:
                    break

        except ClientError as e:
            if e.response["Error"]["Code"] == "InvalidAccessException":
                logger.warning(f"Access denied to list security controls in {self.region}")
            else:
                logger.error(f"Error listing security controls: {e}")

        return controls

    def _build_findings_filters(self) -> Dict[str, Any]:
        """
        Build filters for Security Hub findings query.

        :return: Dictionary of filters
        :rtype: Dict[str, Any]
        """
        filters = {}

        if self.account_id:
            filters["AwsAccountId"] = [{"Value": self.account_id, "Comparison": "EQUALS"}]

        if self.tags:
            filters["ResourceTags"] = self._build_tag_filters()

        return filters

    def _build_tag_filters(self) -> List[Dict[str, str]]:
        """
        Build tag filters for Security Hub findings query.

        :return: List of tag filter dictionaries
        :rtype: List[Dict[str, str]]
        """
        tag_filters = []
        for key, value in self.tags.items():
            tag_filters.append({"Key": key, "Value": value, "Comparison": "EQUALS"})
        return tag_filters

    def _add_region_to_findings(self, finding_list: List[Dict[str, Any]]) -> None:
        """
        Add region information to each finding.

        :param finding_list: List of findings to modify
        """
        for finding in finding_list:
            finding["Region"] = self.region

    def _get_findings(self, client: Any, max_results: int = 100) -> List[Dict[str, Any]]:
        """
        Get Security Hub findings with pagination.

        :param client: Security Hub client
        :param int max_results: Maximum number of results per page
        :return: List of findings
        :rtype: List[Dict[str, Any]]
        """
        findings = []
        next_token = None

        try:
            while True:
                params = {"MaxResults": max_results}
                filters = self._build_findings_filters()

                if filters:
                    params["Filters"] = filters

                if next_token:
                    params["NextToken"] = next_token

                response = client.get_findings(**params)
                finding_list = response.get("Findings", [])

                self._add_region_to_findings(finding_list)
                findings.extend(finding_list)

                next_token = response.get("NextToken")
                if not next_token:
                    break

        except ClientError as e:
            self._handle_findings_error(e)

        return findings

    def _handle_findings_error(self, error: ClientError) -> None:
        """
        Handle errors when getting findings.

        :param error: ClientError exception
        """
        if error.response["Error"]["Code"] == "InvalidAccessException":
            logger.warning(f"Access denied to get findings in {self.region}")
        else:
            logger.error(f"Error getting findings: {error}")

    def _get_insights(self, client: Any) -> List[Dict[str, Any]]:
        """
        Get Security Hub insights.

        :param client: Security Hub client
        :return: List of insights
        :rtype: List[Dict[str, Any]]
        """
        insights = []
        next_token = None

        try:
            while True:
                params = {"MaxResults": 100}
                if next_token:
                    params["NextToken"] = next_token

                response = client.get_insights(**params)
                insight_list = response.get("Insights", [])

                for insight in insight_list:
                    insight_dict = {
                        "Region": self.region,
                        "InsightArn": insight.get("InsightArn"),
                        "Name": insight.get("Name"),
                        "Filters": insight.get("Filters", {}),
                        "GroupByAttribute": insight.get("GroupByAttribute"),
                    }
                    insights.append(insight_dict)

                next_token = response.get("NextToken")
                if not next_token:
                    break

        except ClientError as e:
            if e.response["Error"]["Code"] == "InvalidAccessException":
                logger.warning(f"Access denied to get insights in {self.region}")
            else:
                logger.error(f"Error getting insights: {e}")

        return insights

    def _should_include_member(self, member: Dict[str, Any]) -> bool:
        """
        Determine if a member should be included based on account ID filter.

        :param member: Member account dictionary
        :return: True if member should be included, False otherwise
        :rtype: bool
        """
        if not self.account_id:
            return True
        return member.get("AccountId") == self.account_id

    def _format_member_dict(self, member: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format member account data into standardized dictionary.

        :param member: Raw member data from API
        :return: Formatted member dictionary
        :rtype: Dict[str, Any]
        """
        return {
            "Region": self.region,
            "AccountId": member.get("AccountId"),
            "Email": member.get("Email"),
            "MasterId": member.get("MasterId"),
            "AdministratorId": member.get("AdministratorId"),
            "MemberStatus": member.get("MemberStatus"),
            "InvitedAt": str(member.get("InvitedAt")) if member.get("InvitedAt") else None,
            "UpdatedAt": str(member.get("UpdatedAt")) if member.get("UpdatedAt") else None,
        }

    def _process_member_list(self, member_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process and filter member list.

        :param member_list: Raw list of members from API
        :return: Processed and filtered list of members
        :rtype: List[Dict[str, Any]]
        """
        processed_members = []
        for member in member_list:
            if self._should_include_member(member):
                processed_members.append(self._format_member_dict(member))
        return processed_members

    def _list_members(self, client: Any) -> List[Dict[str, Any]]:
        """
        List Security Hub member accounts.

        :param client: Security Hub client
        :return: List of member accounts
        :rtype: List[Dict[str, Any]]
        """
        members = []
        next_token = None

        try:
            while True:
                params = {"MaxResults": 50}
                if next_token:
                    params["NextToken"] = next_token

                response = client.list_members(**params)
                member_list = response.get("Members", [])

                processed_members = self._process_member_list(member_list)
                members.extend(processed_members)

                next_token = response.get("NextToken")
                if not next_token:
                    break

        except ClientError as e:
            self._handle_list_members_error(e)

        return members

    def _handle_list_members_error(self, error: ClientError) -> None:
        """
        Handle errors when listing members.

        :param error: ClientError exception
        """
        if error.response["Error"]["Code"] == "InvalidAccessException":
            logger.debug(f"Access denied to list members in {self.region}")
        else:
            logger.error(f"Error listing members: {error}")
