"""AWS application service resource collectors."""

import logging
from typing import Dict, List, Any, Optional

from ..base import BaseCollector

logger = logging.getLogger("regscale")


class ApplicationCollector(BaseCollector):
    """Collector for AWS application service resources with filtering support."""

    def __init__(
        self,
        session: Any,
        region: str,
        account_id: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        enabled_services: Optional[Dict[str, bool]] = None,
    ):
        """
        Initialize application collector with filtering support.

        :param session: AWS session to use for API calls
        :param str region: AWS region to collect from
        :param str account_id: Optional AWS account ID to filter resources
        :param dict tags: Optional tag filters (AND logic)
        :param dict enabled_services: Optional dict of service names to boolean flags for enabling/disabling collection
        """
        super().__init__(session, region, account_id, tags)
        self.enabled_services = enabled_services or {}

    def get_step_functions_state_machines(self) -> List[Dict[str, Any]]:
        """
        Get information about Step Functions state machines.

        :return: List of Step Functions state machine information
        :rtype: List[Dict[str, Any]]
        """
        state_machines = []
        try:
            sfn_client = self._get_client("stepfunctions")
            paginator = sfn_client.get_paginator("list_state_machines")

            for page in paginator.paginate():
                for sm_item in page.get("stateMachines", []):
                    sm_arn = sm_item.get("stateMachineArn", "")

                    if not self._matches_account(sm_arn):
                        continue

                    try:
                        sm_detail = sfn_client.describe_state_machine(stateMachineArn=sm_arn)
                        tags_response = sfn_client.list_tags_for_resource(resourceArn=sm_arn)
                        sm_tags = tags_response.get("tags", [])

                        if not self._matches_tags(sm_tags):
                            continue

                        state_machines.append(
                            {
                                "Region": self.region,
                                "StateMachineName": sm_item.get("name"),
                                "StateMachineArn": sm_arn,
                                "Type": sm_item.get("type"),
                                "Status": sm_detail.get("status"),
                                "RoleArn": sm_detail.get("roleArn"),
                                "CreationDate": sm_item.get("creationDate"),
                                "Tags": sm_tags,
                            }
                        )
                    except Exception as sm_error:
                        logger.debug("Error getting Step Functions state machine details for %s: %s", sm_arn, sm_error)
                        continue

        except Exception as e:
            self._handle_error(e, "Step Functions state machines")
        return state_machines

    def get_appsync_apis(self) -> List[Dict[str, Any]]:
        """
        Get information about AppSync GraphQL APIs.

        :return: List of AppSync API information
        :rtype: List[Dict[str, Any]]
        """
        apis = []
        try:
            appsync_client = self._get_client("appsync")
            paginator = appsync_client.get_paginator("list_graphql_apis")

            for page in paginator.paginate():
                for api in page.get("graphqlApis", []):
                    api_arn = api.get("arn", "")

                    if not self._matches_account(api_arn):
                        continue

                    if not self._matches_tags(api.get("tags", {})):
                        continue

                    apis.append(
                        {
                            "Region": self.region,
                            "ApiId": api.get("apiId"),
                            "ApiArn": api_arn,
                            "Name": api.get("name"),
                            "AuthenticationType": api.get("authenticationType"),
                            "Uris": api.get("uris"),
                            "Tags": api.get("tags", {}),
                        }
                    )
        except Exception as e:
            self._handle_error(e, "AppSync GraphQL APIs")
        return apis

    def get_workspaces(self) -> List[Dict[str, Any]]:
        """
        Get information about WorkSpaces virtual desktops.

        :return: List of WorkSpaces information
        :rtype: List[Dict[str, Any]]
        """
        workspaces = []
        try:
            workspaces_client = self._get_client("workspaces")
            paginator = workspaces_client.get_paginator("describe_workspaces")

            for page in paginator.paginate():
                for workspace in page.get("Workspaces", []):
                    workspace_id = workspace.get("WorkspaceId")

                    try:
                        tags_response = workspaces_client.describe_tags(ResourceId=workspace_id)
                        workspace_tags = tags_response.get("TagList", [])

                        if not self._matches_tags(workspace_tags):
                            continue

                        workspaces.append(
                            {
                                "Region": self.region,
                                "WorkspaceId": workspace_id,
                                "DirectoryId": workspace.get("DirectoryId"),
                                "UserName": workspace.get("UserName"),
                                "IpAddress": workspace.get("IpAddress"),
                                "State": workspace.get("State"),
                                "BundleId": workspace.get("BundleId"),
                                "SubnetId": workspace.get("SubnetId"),
                                "ComputerName": workspace.get("ComputerName"),
                                "Tags": workspace_tags,
                            }
                        )
                    except Exception as tag_error:
                        logger.debug("Error getting WorkSpaces tags for %s: %s", workspace_id, tag_error)
                        continue

        except Exception as e:
            self._handle_error(e, "WorkSpaces")
        return workspaces

    def get_iot_things(self) -> List[Dict[str, Any]]:
        """
        Get information about IoT Core things.

        :return: List of IoT thing information
        :rtype: List[Dict[str, Any]]
        """
        things = []
        try:
            iot_client = self._get_client("iot")
            paginator = iot_client.get_paginator("list_things")

            for page in paginator.paginate():
                for thing in page.get("things", []):
                    thing_name = thing.get("thingName")
                    thing_arn = thing.get("thingArn", "")

                    if not self._matches_account(thing_arn):
                        continue

                    try:
                        tags_response = iot_client.list_tags_for_resource(resourceArn=thing_arn)
                        thing_tags = tags_response.get("tags", [])

                        if not self._matches_tags(thing_tags):
                            continue

                        things.append(
                            {
                                "Region": self.region,
                                "ThingName": thing_name,
                                "ThingArn": thing_arn,
                                "ThingTypeName": thing.get("thingTypeName"),
                                "Attributes": thing.get("attributes", {}),
                                "Version": thing.get("version"),
                                "Tags": thing_tags,
                            }
                        )
                    except Exception as tag_error:
                        logger.debug("Error getting IoT thing tags for %s: %s", thing_name, tag_error)
                        continue

        except Exception as e:
            self._handle_error(e, "IoT things")
        return things

    def collect(self) -> Dict[str, Any]:
        """
        Collect application service resources based on enabled_services configuration.

        :return: Dictionary containing enabled application resource information
        :rtype: Dict[str, Any]
        """
        result = {}

        # Step Functions State Machines
        if self.enabled_services.get("step_functions", True):
            result["StepFunctionsStateMachines"] = self.get_step_functions_state_machines()

        # AppSync GraphQL APIs
        if self.enabled_services.get("appsync", True):
            result["AppSyncAPIs"] = self.get_appsync_apis()

        # WorkSpaces
        if self.enabled_services.get("workspaces", True):
            result["WorkSpaces"] = self.get_workspaces()

        # IoT Things
        if self.enabled_services.get("iot", True):
            result["IoTThings"] = self.get_iot_things()

        return result
