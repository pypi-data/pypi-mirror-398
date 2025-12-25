"""
Module to handle API calls to Microsoft Defender for Cloud
"""

import os.path
from json import JSONDecodeError
from logging import getLogger
from typing import Any, Literal, Optional
from pathlib import Path

from requests import Response

from regscale.core.app.api import Api
from regscale.core.app.utils.app_utils import error_and_exit, get_current_datetime, check_file_path, save_data_to
from urllib.parse import urljoin
from .defender_constants import APP_JSON, DATA_TYPE, GRAPH_BASE_URL, ENTRA_ENDPOINTS, ENTRA_SAVE_DIR

logger = getLogger("regscale")


class DefenderApi:
    """
    Class to handle API calls to Microsoft Defender 365 or Microsoft Defender for Cloud

    :param Literal["cloud", "365"] system: Which system to make API calls to, either cloud or 365
    """

    def __init__(self, system: Literal["cloud", "365", "entra"]):
        self.api: Api = Api()
        self.config: dict = self.api.config
        self.system: Literal["cloud", "365", "entra"] = system
        self.headers: dict = self.set_headers()
        self.decode_error: str = "JSON Decode error"
        self.skip_token_key: str = "$skipToken"

    def set_headers(self) -> dict:
        """
        Function to set the headers for the API calls
        """
        token = self.check_token()
        return {"Content-Type": APP_JSON, "Authorization": token}

    def get_token(self) -> str:
        """
        Function to get a token from Microsoft Azure and saves it to init.yaml

        :return: JWT from Azure
        :rtype: str
        """
        # set the url and body for request
        if self.system == "365":
            url = f'https://login.windows.net/{self.config["azure365TenantId"]}/oauth2/token'
            client_id = self.config["azure365ClientId"]
            client_secret = self.config["azure365Secret"]
            resource = "https://api.securitycenter.windows.com"
            key = "azure365AccessToken"
        elif self.system == "cloud":
            url = f'https://login.microsoftonline.com/{self.config["azureCloudTenantId"]}/oauth2/token'
            client_id = self.config["azureCloudClientId"]
            client_secret = self.config["azureCloudSecret"]
            resource = "https://management.azure.com"
            key = "azureCloudAccessToken"
        elif self.system == "entra":
            url = f'https://login.microsoftonline.com/{self.config["azureEntraTenantId"]}/oauth2/v2.0/token'
            client_id = self.config["azureEntraClientId"]
            client_secret = self.config["azureEntraSecret"]
            resource = "https://graph.microsoft.com/.default"
            key = "azureEntraAccessToken"
        if self.system == "entra":
            data = {
                "scope": resource,
                "client_id": client_id,
                "client_secret": client_secret,
                "grant_type": "client_credentials",
            }
        else:
            data = {
                "resource": resource,
                "client_id": client_id,
                "client_secret": client_secret,
                "grant_type": "client_credentials",
            }
        # get the data
        response = self.api.post(
            url=url,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data=data,
        )
        try:
            return self._parse_and_save_token(response, key)
        except KeyError as ex:
            # notify user we weren't able to get a token and exit
            error_and_exit(f"Didn't receive token from Azure.\n{ex}\n{response.text}")
        except JSONDecodeError as ex:
            # notify user we weren't able to get a token and exit
            error_and_exit(f"Unable to authenticate with Azure.\n{ex}\n{response.text}")

    def check_token(self, url: Optional[str] = None) -> str:
        """
        Function to check if current Azure token from init.yaml is valid, if not replace it

        :param str url: The URL to use for authentication, defaults to None
        :return: returns JWT for Microsoft 365 Defender or Microsoft Defender for Cloud depending on system provided
        :rtype: str
        """
        # set up variables for the provided system
        if self.system == "cloud":
            key = "azureCloudAccessToken"
        elif self.system.lower() == "365":
            key = "azure365AccessToken"
        elif self.system == "entra":
            key = "azureEntraAccessToken"
        else:
            error_and_exit(
                f"{self.system.title()} is not supported, only Microsoft 365 Defender, Microsoft Defender for Cloud, and Azure Entra."
            )
        current_token = self.config[key]
        # check the token if it isn't blank
        if current_token and url:
            # set the headers
            header = {"Content-Type": APP_JSON, "Authorization": current_token}
            # test current token by getting recommendations
            token_pass = self.api.get(url=url, headers=header)
            # check the status code
            if getattr(token_pass, "status_code", 0) == 200:
                # token still valid, return it
                token = self.config[key]
                logger.info(
                    "Current token for %s is still valid and will be used for future requests.",
                    self.system.title(),
                )
            elif getattr(token_pass, "status_code", 0) == 403:
                # token doesn't have permissions, notify user and exit
                error_and_exit(
                    "Incorrect permissions set for application. Cannot retrieve recommendations.\n"
                    + f"{token_pass.status_code}: {token_pass.reason}\n{token_pass.text}"
                )
            else:
                # token is no longer valid, get a new one
                token = self.get_token()
        # token is empty, get a new token
        else:
            token = self.get_token()
        return token

    def _parse_and_save_token(self, response: Response, key: str) -> str:
        """
        Function to parse the token from the response and save it to init.yaml

        :param Response response: Response from API call
        :param str key: Key to use for init.yaml token update
        :return: JWT from Azure for the provided system
        :rtype: str
        """
        # try to read the response and parse the token
        res = response.json()
        token = res["access_token"]

        # add the token to init.yaml
        self.config[key] = f"Bearer {token}"

        # write the changes back to file
        self.api.app.save_config(self.api.config)  # type: ignore

        # notify the user we were successful
        logger.info(
            f"Azure {self.system.title()} Login Successful! Init.yaml file was updated with the new access token."
        )
        # return the token string
        return self.config[key]

    def execute_resource_graph_query(
        self, query: str = None, skip_token: Optional[str] = None, record_count: int = 0
    ) -> list[dict]:
        """
        Function to fetch Microsoft Defender resources from Azure

        :param str query: Query to use for the API call
        :param Optional[str] skip_token: Token to skip results, used during pagination, defaults to None
        :param int record_count: Number of records fetched, defaults to 0, used for logging during pagination
        :return: list of Microsoft Defender resources
        :rtype: list[dict]
        """
        url = "https://management.azure.com/providers/Microsoft.ResourceGraph/resources?api-version=2024-04-01"
        if query:
            payload: dict[str, Any] = {"query": query}
        else:
            payload: dict[str, Any] = {
                "query": query,
                "subscriptions": [self.config["azureCloudSubscriptionId"]],
            }
        if skip_token:
            payload["options"] = {self.skip_token_key: skip_token}
            logger.info("Retrieving more Microsoft Defender resources from Azure...")
        else:
            logger.info("Retrieving Microsoft Defender resources from Azure...")
        response = self.api.post(url=url, headers=self.headers, json=payload)
        if response.status_code != 200:
            error_and_exit(
                f"Received unexpected response from Microsoft Defender.\n{response.status_code}:{response.reason}"
                + f"\n{response.text}",
            )
        try:
            response_data = response.json()
            total_records = response_data.get("totalRecords", 0)
            count = response_data.get("count", len(response_data.get("data", [])))
            logger.info(f"Received {count + record_count}/{total_records} items from Microsoft Defender.")
            # try to get the values from the api response
            defender_data = response_data["data"]
        except JSONDecodeError:
            # notify user if there was a json decode error from API response and exit
            error_and_exit(self.decode_error)
        except KeyError:
            # notify user there was no data from API response and exit
            error_and_exit(
                f"Received unexpected response from Microsoft Defender.\n{response.status_code}: {response.reason}\n"
                + f"{response.text}"
            )
        # check if pagination is required to fetch all data from Microsoft Defender
        skip_token = response_data.get(self.skip_token_key)
        if response.status_code == 200 and skip_token:
            # get the rest of the data
            defender_data.extend(
                self.execute_resource_graph_query(query=query, skip_token=skip_token, record_count=count + record_count)
            )
        # return the defender recommendations
        return defender_data

    def get_items_from_azure(self, url: str, parse_value: Optional[bool] = True) -> list:
        """
        Function to get data from Microsoft Defender returns the data as a list while handling pagination

        :param str url: URL to use for the API call
        :param Optional[bool] parse_value: Whether to parse the value from the API response, defaults to True
        :return: list of recommendations
        :rtype: list
        """
        # get the data via api call
        response = self.api.get(url=url, headers=self.headers)
        if response.status_code != 200:
            error_and_exit(
                f"Received unexpected response from Microsoft Defender.\n{response.status_code}:{response.reason}"
                + f"\n{response.text}",
            )
        # try to read the response
        try:
            response_data = response.json()
            # try to get the values from the api response
            if parse_value:
                defender_data = response_data["value"]
            else:
                defender_data = response_data
        except JSONDecodeError:
            # notify user if there was a json decode error from API response and exit
            error_and_exit(self.decode_error)
        except KeyError:
            # notify user there was no data from API response and exit
            error_and_exit(
                f"Received unexpected response from Microsoft Defender.\n{response.status_code}: {response.text}"
            )
        # check if pagination is required to fetch all data from Microsoft Defender
        if next_link := (response_data.get("nextLink") or response_data.get("@odata.nextLink")):
            # get the rest of the data
            defender_data.extend(self.get_items_from_azure(url=next_link))
        # return the defender recommendations
        return defender_data

    def fetch_queries_from_azure(self) -> list[dict]:
        """
        Function to fetch queries from Microsoft Defender for Cloud
        """
        url = (
            f"https://management.azure.com/subscriptions/{self.config['azureCloudSubscriptionId']}/"
            "providers/Microsoft.ResourceGraph/queries?api-version=2024-04-01"
        )
        logger.info("Fetching saved queries from Azure Resource Graph...")
        response = self.api.get(url=url, headers=self.headers)
        logger.debug(f"Azure API response status: {response.status_code}")
        if response.raise_for_status():
            error_and_exit(
                f"Received unexpected response from Microsoft Defender.\n{response.status_code}:{response.reason}"
                + f"\n{response.text}",
            )
        logger.debug("Parsing Azure API response...")
        cloud_queries = response.json().get("value", [])
        logger.info(f"Found {len(cloud_queries)} saved queries in Azure Resource Graph.")
        return cloud_queries

    def fetch_and_run_query(self, query: dict) -> list[dict]:
        """
        Function to fetch and run a query from Microsoft Defender for Cloud

        :param dict query: Query to run in Azure Resource Graph
        :return: Results from the query
        :rtype: list[dict]
        """
        url = (
            f"https://management.azure.com/subscriptions/{query['subscriptionId']}/resourceGroups/"
            f"{query['resourceGroup']}/providers/Microsoft.ResourceGraph/queries/{query['name']}"
            "?api-version=2024-04-01"
        )
        response = self.api.get(url=url, headers=self.headers)
        if response.raise_for_status():
            error_and_exit(
                f"Received unexpected response from Microsoft Defender.\n{response.status_code}:{response.reason}"
                + f"\n{response.text}",
            )
        query_string = response.json().get("properties", {}).get("query")
        return self.execute_resource_graph_query(query=query_string)

    def get_and_save_entra_evidence(self, endpoint_key: str, **kwargs) -> list[Path]:
        """
        Function to get Azure Entra evidence data from Microsoft Graph API and saves it to a csv file

        :param str endpoint_key: Key from ENTRA_ENDPOINTS to specify which endpoint to call
        :param kwargs: Additional parameters for URL formatting
        :return: List of Paths to the saved csv files
        :rtype: list[Path]
        """
        if self.system != "entra":
            error_and_exit("This method can only be used with system='entra'")

        if endpoint_key not in ENTRA_ENDPOINTS:
            error_and_exit(f"Unknown endpoint key: {endpoint_key}")

        endpoint = ENTRA_ENDPOINTS[endpoint_key]

        # Handle URL parameter substitution
        if "{start_date}" in endpoint:
            start_date = kwargs.get("start_date", get_current_datetime("%Y-%m-%dT00:00:00Z"))
            endpoint = endpoint.replace("{start_date}", start_date)

        if "{group-id}" in endpoint:
            group_id = kwargs.get("group_id")
            if not group_id:
                error_and_exit("group_id parameter is required for this endpoint")
            endpoint = endpoint.replace("{group-id}", group_id)

        if "{def_id}" in endpoint:
            def_id = kwargs.get("def_id")
            if not def_id:
                error_and_exit("def_id parameter is required for this endpoint")
            endpoint = endpoint.replace("{def_id}", def_id)

        if "{instance_id}" in endpoint:
            instance_id = kwargs.get("instance_id")
            if not instance_id:
                error_and_exit("instance_id parameter is required for this endpoint")
            endpoint = endpoint.replace("{instance_id}", instance_id)

        url = f"{GRAPH_BASE_URL}{endpoint}"
        logger.info(f"Retrieving Azure Entra evidence from: {endpoint_key}")

        data = self.get_items_from_azure(url=url, parse_value=kwargs.get("parse_value", True))
        save_path = Path(
            os.path.join(ENTRA_SAVE_DIR, f"azure_entra_{endpoint_key}_{get_current_datetime('%Y%m%d')}.xlsx")
        )
        save_data_to(file=save_path, data=data, transpose_data=False)
        return [save_path]

    def collect_all_entra_evidence(self, days_back: int = 30) -> dict[str, list[Path]]:
        """
        Function to collect all Azure Entra evidence data for FedRAMP compliance

        :param int days_back: Number of days back to collect audit logs, defaults to 30
        :return: Dict containing all evidence data categorized by type and list of Paths to the saved csv evidence files
        :rtype: dict[str, list[Path]]
        """
        from datetime import datetime, timedelta

        evidence_data = {}
        start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%dT00:00:00Z")

        check_file_path(ENTRA_SAVE_DIR)

        # Users and Groups
        try:
            evidence_data["users"] = self.get_and_save_entra_evidence("users")
            evidence_data["users_delta"] = self.get_and_save_entra_evidence("users_delta")
            evidence_data["guest_users"] = self.get_and_save_entra_evidence("guest_users")
            evidence_data["groups_and_members"] = self.get_and_save_entra_evidence("groups_and_members")
            evidence_data["security_groups"] = self.get_and_save_entra_evidence("security_groups")
            logger.info("Successfully collected user and group evidence")
        except Exception as e:
            logger.error(f"Error collecting user/group evidence: {e}")
            evidence_data["users"] = []
            evidence_data["users_delta"] = []
            evidence_data["guest_users"] = []
            evidence_data["groups_and_members"] = []
            evidence_data["security_groups"] = []

        # RBAC and PIM
        try:
            evidence_data["role_assignments"] = self.get_and_save_entra_evidence("role_assignments")
            evidence_data["role_definitions"] = self.get_and_save_entra_evidence("role_definitions")
            evidence_data["pim_assignments"] = self.get_and_save_entra_evidence("pim_assignments")
            evidence_data["pim_eligibility"] = self.get_and_save_entra_evidence("pim_eligibility")
            logger.info("Successfully collected RBAC and PIM evidence")
        except Exception as e:
            logger.error(f"Error collecting RBAC/PIM evidence: {e}")
            evidence_data["role_assignments"] = []
            evidence_data["role_definitions"] = []
            evidence_data["pim_assignments"] = []
            evidence_data["pim_eligibility"] = []

        # Conditional Access
        try:
            evidence_data["conditional_access"] = self.get_and_save_entra_evidence("conditional_access")
            logger.info("Successfully collected conditional access evidence")
        except Exception as e:
            logger.error(f"Error collecting conditional access evidence: {e}")
            evidence_data["conditional_access"] = []

        # Authentication Methods
        try:
            evidence_data["auth_methods_policy"] = self.get_and_save_entra_evidence(
                "auth_methods_policy", parse_value=False
            )
            evidence_data["user_mfa_registration"] = self.get_and_save_entra_evidence("user_mfa_registration")
            evidence_data["mfa_registered_users"] = self.get_and_save_entra_evidence("mfa_registered_users")
            logger.info("Successfully collected authentication methods evidence")
        except Exception as e:
            logger.error(f"Error collecting authentication methods evidence: {e}")
            evidence_data["auth_methods_policy"] = []
            evidence_data["user_mfa_registration"] = []
            evidence_data["mfa_registered_users"] = []

        # Audit Logs (may require additional permissions)
        try:
            evidence_data["sign_in_logs"] = self.get_and_save_entra_evidence("sign_in_logs", start_date=start_date)
            evidence_data["directory_audits"] = self.get_and_save_entra_evidence(
                "directory_audits", start_date=start_date
            )
            evidence_data["provisioning_logs"] = self.get_and_save_entra_evidence(
                "provisioning_logs", start_date=start_date
            )
            logger.info("Successfully collected audit log evidence")
        except Exception as e:
            logger.error(f"Error collecting audit log evidence (may require additional permissions): {e}")
            evidence_data["sign_in_logs"] = []
            evidence_data["directory_audits"] = []
            evidence_data["provisioning_logs"] = []

        # Access Reviews
        try:
            evidence_data["access_review_definitions"] = self.collect_entra_access_reviews()
            logger.info("Successfully collected access review evidence")
        except Exception as e:
            logger.error(f"Error collecting access review evidence: {e}")
            evidence_data["access_review_definitions"] = []

        return evidence_data

    def collect_entra_access_reviews(self) -> list[Path]:
        """
        Function to collect access reviews from Microsoft Graph API

        :return: List of paths to the saved csv files
        :rtype: list[Path]
        """
        file_paths = []
        url = GRAPH_BASE_URL + ENTRA_ENDPOINTS["access_review_definitions"]
        definitions = self.get_items_from_azure(url=url)
        current_date = get_current_datetime("%Y-%m-%d")

        for definition in definitions:
            definition_name = definition["displayName"].replace("/", "_").replace(" ", "_")

            # Save flattened definition data
            definition_path = Path(
                os.path.join(ENTRA_SAVE_DIR, f"access_reviews_definitions_{definition_name}_{current_date}.csv")
            )
            flattened_definition = self._flatten_access_review_definition(definition)
            save_data_to(file=definition_path, data=[flattened_definition], transpose_data=False)
            file_paths.append(definition_path)

            # Get instances and decisions
            instance_url = GRAPH_BASE_URL + ENTRA_ENDPOINTS["access_review_instances"].format(def_id=definition["id"])
            instances = self.get_items_from_azure(url=instance_url)

            # Save flattened instances data
            instances_path = Path(
                os.path.join(ENTRA_SAVE_DIR, f"access_reviews_instances_{definition_name}_{current_date}.csv")
            )
            flattened_instances = []
            for instance in instances:
                flattened_instance = self._flatten_access_review_instance(definition["id"], instance)
                flattened_instances.append(flattened_instance)

            if flattened_instances:
                save_data_to(file=instances_path, data=flattened_instances, transpose_data=False)
                file_paths.append(instances_path)

            # Save flattened decisions data
            decisions_path = Path(
                os.path.join(ENTRA_SAVE_DIR, f"access_reviews_decisions_{definition_name}_{current_date}.csv")
            )
            all_decisions = []
            for instance in instances:
                decision_url = GRAPH_BASE_URL + ENTRA_ENDPOINTS["access_review_decisions"].format(
                    def_id=definition["id"], instance_id=instance["id"]
                )
                decisions = self.get_items_from_azure(url=decision_url)
                for decision in decisions:
                    flattened_decision = self._flatten_access_review_decision(
                        definition["id"], instance["id"], decision
                    )
                    all_decisions.append(flattened_decision)

            if all_decisions:
                save_data_to(file=decisions_path, data=all_decisions, transpose_data=False)
                file_paths.append(decisions_path)

        return file_paths

    @staticmethod
    def _flatten_access_review_definition(definition: dict) -> dict:
        """
        Flatten access review definition for CSV export

        :param dict definition: Definition data
        :return: Flattened definition data
        :rtype: dict
        """
        return {
            "id": definition.get("id"),
            "displayName": definition.get("displayName"),
            "status": definition.get("status"),
            "createdDateTime": definition.get("createdDateTime"),
            "lastModifiedDateTime": definition.get("lastModifiedDateTime"),
            "descriptionForAdmins": definition.get("descriptionForAdmins"),
            "descriptionForReviewers": definition.get("descriptionForReviewers"),
            "createdBy_displayName": definition.get("createdBy", {}).get("displayName"),
            "createdBy_id": definition.get("createdBy", {}).get("id"),
            "createdBy_userPrincipalName": definition.get("createdBy", {}).get("userPrincipalName"),
            "scope_type": definition.get("scope", {}).get(DATA_TYPE),
            "scope_query": definition.get("scope", {}).get("query"),
            "scope_inactiveDuration": definition.get("scope", {}).get("inactiveDuration"),
            "instanceEnumerationScope_type": definition.get("instanceEnumerationScope", {}).get(DATA_TYPE),
            "instanceEnumerationScope_query": definition.get("instanceEnumerationScope", {}).get("query"),
            "settings_defaultDecision": definition.get("settings", {}).get("defaultDecision"),
            "settings_autoApplyDecisionsEnabled": definition.get("settings", {}).get("autoApplyDecisionsEnabled"),
            "settings_instanceDurationInDays": definition.get("settings", {}).get("instanceDurationInDays"),
            "settings_justificationRequiredOnApproval": definition.get("settings", {}).get(
                "justificationRequiredOnApproval"
            ),
            "settings_mailNotificationsEnabled": definition.get("settings", {}).get("mailNotificationsEnabled"),
            "settings_recommendationsEnabled": definition.get("settings", {}).get("recommendationsEnabled"),
            "settings_recurrence_type": definition.get("settings", {})
            .get("recurrence", {})
            .get("pattern", {})
            .get("type"),
            "settings_recurrence_interval": definition.get("settings", {})
            .get("recurrence", {})
            .get("pattern", {})
            .get("interval"),
        }

    @staticmethod
    def _flatten_access_review_instance(definition_id: str, instance: dict) -> dict:
        """
        Flatten access review instance for CSV export

        :param str definition_id: ID of the access review definition
        :param dict instance: Instance data
        :return: Flattened instance data
        :rtype: dict
        """
        return {
            "definition_id": definition_id,
            "id": instance.get("id"),
            "status": instance.get("status"),
            "startDateTime": instance.get("startDateTime"),
            "endDateTime": instance.get("endDateTime"),
            "scope_type": instance.get("scope", {}).get(DATA_TYPE),
            "scope_query": instance.get("scope", {}).get("query"),
            "scope_inactiveDuration": instance.get("scope", {}).get("inactiveDuration"),
            "reviewers_count": len(instance.get("reviewers", [])),
            "fallbackReviewers_count": len(instance.get("fallbackReviewers", [])),
        }

    @staticmethod
    def _flatten_access_review_decision(definition_id: str, instance_id: str, decision: dict) -> dict:
        """
        Flatten access review decision for CSV export

        :param str definition_id: ID of the access review definition
        :param str instance_id: ID of the access review instance
        :param dict decision: Decision data
        :return: Flattened decision data
        :rtype: dict
        """
        return {
            "definition_id": definition_id,
            "instance_id": instance_id,
            "decision_id": decision.get("id"),
            "accessReviewId": decision.get("accessReviewId"),
            "decision": decision.get("decision"),
            "recommendation": decision.get("recommendation"),
            "justification": decision.get("justification"),
            "reviewedDateTime": decision.get("reviewedDateTime"),
            "appliedDateTime": decision.get("appliedDateTime"),
            "applyResult": decision.get("applyResult"),
            "principalLink": decision.get("principalLink"),
            "resourceLink": decision.get("resourceLink"),
            "reviewedBy_id": decision.get("reviewedBy", {}).get("id"),
            "reviewedBy_displayName": decision.get("reviewedBy", {}).get("displayName"),
            "reviewedBy_userPrincipalName": decision.get("reviewedBy", {}).get("userPrincipalName"),
            "appliedBy_id": decision.get("appliedBy", {}).get("id"),
            "appliedBy_displayName": decision.get("appliedBy", {}).get("displayName"),
            "appliedBy_userPrincipalName": decision.get("appliedBy", {}).get("userPrincipalName"),
            "target_type": decision.get("target", {}).get(DATA_TYPE),
            "target_userId": decision.get("target", {}).get("userId"),
            "target_userDisplayName": decision.get("target", {}).get("userDisplayName"),
            "target_userPrincipalName": decision.get("target", {}).get("userPrincipalName"),
            "principal_type": decision.get("principal", {}).get(DATA_TYPE),
            "principal_id": decision.get("principal", {}).get("id"),
            "principal_displayName": decision.get("principal", {}).get("displayName"),
            "principal_userPrincipalName": decision.get("principal", {}).get("userPrincipalName"),
        }
