"""AWS Audit Manager resource collection."""

import logging
from typing import Any, Dict, List, Optional

from botocore.exceptions import ClientError

from regscale.integrations.commercial.aws.inventory.base import BaseCollector

logger = logging.getLogger("regscale")


class AuditManagerCollector(BaseCollector):
    """Collector for AWS Audit Manager resources."""

    def __init__(
        self, session: Any, region: str, account_id: Optional[str] = None, tags: Optional[Dict[str, str]] = None
    ):
        """
        Initialize Audit Manager collector.

        :param session: AWS session to use for API calls
        :param str region: AWS region to collect from
        :param str account_id: Optional AWS account ID to filter resources
        :param dict tags: Optional tags to filter resources (key-value pairs)
        """
        super().__init__(session, region)
        self.account_id = account_id
        self.tags = tags or {}

    def collect(self) -> Dict[str, Any]:
        """
        Collect AWS Audit Manager resources.

        :return: Dictionary containing Audit Manager information
        :rtype: Dict[str, Any]
        """
        result = {
            "Assessments": [],
            "AssessmentFrameworks": [],
            "Controls": [],
            "AssessmentReports": [],
            "Evidence": [],
            "Settings": {},
        }

        try:
            client = self._get_client("auditmanager")

            # Get assessments
            assessments = self._list_assessments(client)
            result["Assessments"] = assessments

            # Get assessment frameworks
            frameworks = self._list_assessment_frameworks(client)
            result["AssessmentFrameworks"] = frameworks

            # Get controls
            controls = self._list_controls(client)
            result["Controls"] = controls

            # Get account settings
            settings = self._get_settings(client)
            result["Settings"] = settings

            logger.info(
                f"Collected {len(assessments)} assessment(s), {len(frameworks)} framework(s) from {self.region}"
            )

        except ClientError as e:
            self._handle_error(e, "Audit Manager resources")
        except Exception as e:
            logger.error(f"Unexpected error collecting Audit Manager resources: {e}", exc_info=True)

        return result

    def _list_assessments(self, client: Any) -> List[Dict[str, Any]]:
        """
        List audit assessments.

        :param client: Audit Manager client
        :return: List of assessment information
        :rtype: List[Dict[str, Any]]
        """
        assessments = []
        try:
            # Note: list_assessments does not support pagination
            response = client.list_assessments()

            for assessment_metadata in response.get("assessmentMetadata", []):
                assessment_id = assessment_metadata.get("id")
                assessment_dict = self._fetch_and_process_assessment(client, assessment_id)
                if assessment_dict:
                    assessments.append(assessment_dict)

        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDeniedException":
                logger.warning(f"Access denied to list assessments in {self.region}")
            else:
                logger.error(f"Error listing assessments: {e}")

        return assessments

    def _fetch_and_process_assessment(self, client: Any, assessment_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch and process a single assessment if it passes filters.

        :param client: Audit Manager client
        :param str assessment_id: Assessment ID
        :return: Assessment dictionary or None if filtered out or error
        :rtype: Optional[Dict[str, Any]]
        """
        try:
            # Get full assessment details
            assessment_response = client.get_assessment(assessmentId=assessment_id)
            assessment = assessment_response.get("assessment", {})

            # Filter by account ID if specified
            if self.account_id:
                aws_account = assessment.get("awsAccount", {})
                if not self._matches_account_id(aws_account.get("id", "")):
                    return None

            # Filter by tags if specified
            if self.tags and not self._matches_tags(assessment.get("tags", {})):
                return None

            return self._build_assessment_dict(assessment)

        except ClientError as e:
            if e.response["Error"]["Code"] not in ["ResourceNotFoundException", "AccessDeniedException"]:
                logger.error(f"Error getting assessment {assessment_id}: {e}")
            return None

    def _build_assessment_dict(self, assessment: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build assessment dictionary from assessment data.

        :param dict assessment: Assessment data
        :return: Formatted assessment dictionary
        :rtype: Dict[str, Any]
        """
        metadata = assessment.get("metadata", {})
        framework = assessment.get("framework", {})

        return {
            "Region": self.region,
            "AssessmentId": assessment.get("arn"),
            "Name": metadata.get("name"),
            "Description": metadata.get("description"),
            "ComplianceType": metadata.get("complianceType"),
            "Status": metadata.get("status"),
            "AwsAccount": assessment.get("awsAccount", {}),
            "Framework": {
                "Id": framework.get("id"),
                "Type": framework.get("type"),
                "Arn": framework.get("arn"),
                "Metadata": framework.get("metadata", {}),
            },
            "Scope": metadata.get("scope", {}),
            "Roles": metadata.get("roles", []),
            "CreationTime": str(metadata.get("creationTime")) if metadata.get("creationTime") else None,
            "LastUpdated": str(metadata.get("lastUpdated")) if metadata.get("lastUpdated") else None,
            "Tags": assessment.get("tags", {}),
        }

    def _list_assessment_frameworks(self, client: Any) -> List[Dict[str, Any]]:
        """
        List assessment frameworks.

        :param client: Audit Manager client
        :return: List of framework information
        :rtype: List[Dict[str, Any]]
        """
        frameworks = []
        try:
            # Get standard and custom frameworks
            frameworks.extend(self._list_frameworks_by_type(client, "Standard"))
            frameworks.extend(self._list_frameworks_by_type(client, "Custom"))

        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDeniedException":
                logger.warning(f"Access denied to list assessment frameworks in {self.region}")
            else:
                logger.error(f"Error listing assessment frameworks: {e}")

        return frameworks

    def _list_frameworks_by_type(self, client: Any, framework_type: str) -> List[Dict[str, Any]]:
        """
        List assessment frameworks of a specific type with pagination.

        :param client: Audit Manager client
        :param str framework_type: Framework type (Standard or Custom)
        :return: List of framework information
        :rtype: List[Dict[str, Any]]
        """
        frameworks = []
        next_token = None

        while True:
            params = {"frameworkType": framework_type}
            if next_token:
                params["nextToken"] = next_token

            response = client.list_assessment_frameworks(**params)

            for framework in response.get("frameworkMetadataList", []):
                framework_dict = self._process_framework(client, framework, framework_type)
                if framework_dict:
                    frameworks.append(framework_dict)

            next_token = response.get("nextToken")
            if not next_token:
                break

        return frameworks

    def _process_framework(
        self, client: Any, framework: Dict[str, Any], framework_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        Process a single framework and return its dictionary if it passes filters.

        :param client: Audit Manager client
        :param dict framework: Framework metadata
        :param str framework_type: Framework type (Standard or Custom)
        :return: Framework dictionary or None if filtered out
        :rtype: Optional[Dict[str, Any]]
        """
        framework_arn = framework.get("arn")

        # Get tags if filtering is enabled
        framework_tags = {}
        if self.tags and framework_arn:
            framework_tags = self._get_resource_tags(client, framework_arn)

        # Filter by tags if specified
        if self.tags and not self._matches_tags(framework_tags):
            return None

        return {
            "Region": self.region,
            "Id": framework.get("id"),
            "Arn": framework_arn,
            "Name": framework.get("name"),
            "Type": framework_type,
            "Description": framework.get("description"),
            "ComplianceType": framework.get("complianceType"),
            "ControlsCount": framework.get("controlsCount"),
            "ControlSetsCount": framework.get("controlSetsCount"),
            "CreatedAt": str(framework.get("createdAt")) if framework.get("createdAt") else None,
            "LastUpdatedAt": str(framework.get("lastUpdatedAt")) if framework.get("lastUpdatedAt") else None,
            "Tags": framework_tags,
        }

    def _list_controls(self, client: Any) -> List[Dict[str, Any]]:
        """
        List controls.

        :param client: Audit Manager client
        :return: List of control information
        :rtype: List[Dict[str, Any]]
        """
        controls = []
        try:
            # Get standard and custom controls
            controls.extend(self._list_controls_by_type(client, "Standard"))
            controls.extend(self._list_controls_by_type(client, "Custom"))

        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDeniedException":
                logger.warning(f"Access denied to list controls in {self.region}")
            else:
                logger.error(f"Error listing controls: {e}")

        return controls

    def _list_controls_by_type(self, client: Any, control_type: str) -> List[Dict[str, Any]]:
        """
        List controls of a specific type with pagination.

        :param client: Audit Manager client
        :param str control_type: Control type (Standard or Custom)
        :return: List of control information
        :rtype: List[Dict[str, Any]]
        """
        controls = []
        next_token = None

        while True:
            params = {"controlType": control_type}
            if next_token:
                params["nextToken"] = next_token

            response = client.list_controls(**params)

            for control in response.get("controlMetadataList", []):
                control_dict = self._process_control(client, control, control_type)
                if control_dict:
                    controls.append(control_dict)

            next_token = response.get("nextToken")
            if not next_token:
                break

        return controls

    def _process_control(self, client: Any, control: Dict[str, Any], control_type: str) -> Optional[Dict[str, Any]]:
        """
        Process a single control and return its dictionary if it passes filters.

        :param client: Audit Manager client
        :param dict control: Control metadata
        :param str control_type: Control type (Standard or Custom)
        :return: Control dictionary or None if filtered out
        :rtype: Optional[Dict[str, Any]]
        """
        control_arn = control.get("arn")

        # Get tags if filtering is enabled
        control_tags = {}
        if self.tags and control_arn:
            control_tags = self._get_resource_tags(client, control_arn)

        # Filter by tags if specified
        if self.tags and not self._matches_tags(control_tags):
            return None

        return {
            "Region": self.region,
            "Id": control.get("id"),
            "Arn": control_arn,
            "Name": control.get("name"),
            "Type": control_type,
            "ControlSources": control.get("controlSources"),
            "CreatedAt": str(control.get("createdAt")) if control.get("createdAt") else None,
            "LastUpdatedAt": str(control.get("lastUpdatedAt")) if control.get("lastUpdatedAt") else None,
            "Tags": control_tags,
        }

    def _get_settings(self, client: Any) -> Dict[str, Any]:
        """
        Get account settings.

        :param client: Audit Manager client
        :return: Settings information
        :rtype: Dict[str, Any]
        """
        try:
            response = client.get_settings(attribute="ALL")
            settings = response.get("settings", {})

            return {
                "IsAwsOrgEnabled": settings.get("isAwsOrgEnabled", False),
                "SnsTopic": settings.get("snsTopic"),
                "DefaultAssessmentReportsDestination": settings.get("defaultAssessmentReportsDestination", {}),
                "DefaultProcessOwners": settings.get("defaultProcessOwners", []),
                "KmsKey": settings.get("kmsKey"),
                "EvidenceFinderEnabled": settings.get("evidenceFinderEnablement", {}).get("enablementStatus")
                == "ENABLED",
            }
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDeniedException":
                logger.warning(f"Access denied to get settings in {self.region}")
            else:
                logger.debug(f"Error getting settings: {e}")
            return {}

    def _get_resource_tags(self, client: Any, resource_arn: str) -> Dict[str, str]:
        """
        Retrieve tags for a resource.

        :param client: Audit Manager client
        :param str resource_arn: ARN of the resource
        :return: Dictionary of tags
        :rtype: Dict[str, str]
        """
        try:
            response = client.list_tags_for_resource(resourceArn=resource_arn)
            return response.get("tags", {})
        except ClientError as e:
            if e.response["Error"]["Code"] not in ["ResourceNotFoundException", "AccessDeniedException"]:
                logger.debug(f"Error getting tags for resource {resource_arn}: {e}")
            return {}

    def _matches_account_id(self, account_id: str) -> bool:
        """
        Check if account ID matches the specified filter.

        :param str account_id: Account ID to check
        :return: True if matches or no account_id filter specified
        :rtype: bool
        """
        if not self.account_id:
            return True
        return account_id == self.account_id

    def _matches_tags(self, resource_tags: Dict[str, str]) -> bool:
        """
        Check if resource tags match the specified filter tags.

        :param dict resource_tags: Tags on the resource
        :return: True if all filter tags match
        :rtype: bool
        """
        if not self.tags:
            return True

        # All filter tags must match
        for key, value in self.tags.items():
            if resource_tags.get(key) != value:
                return False

        return True

    def get_assessment_evidence(self, assessment_id: str, control_set_id: str, control_id: str) -> List[Dict[str, Any]]:
        """
        Get evidence for a specific control in an assessment.

        :param str assessment_id: Assessment ID
        :param str control_set_id: Control set ID
        :param str control_id: Control ID
        :return: List of evidence items
        :rtype: List[Dict[str, Any]]
        """
        evidence_items = []
        try:
            client = self._get_client("auditmanager")

            paginator = client.get_paginator("get_evidence_by_evidence_folder")
            pages = paginator.paginate(
                assessmentId=assessment_id, controlSetId=control_set_id, evidenceFolderId=control_id
            )

            for page in pages:
                evidence_items.extend(page.get("evidence", []))

            logger.debug(f"Retrieved {len(evidence_items)} evidence items for control {control_id}")

        except ClientError as e:
            if e.response["Error"]["Code"] not in ["ResourceNotFoundException", "AccessDeniedException"]:
                logger.error(f"Error getting evidence for control {control_id}: {e}")

        return evidence_items

    def get_control_assessment_results(
        self, assessment_id: str, control_set_id: str, control_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get assessment results for a specific control.

        :param str assessment_id: Assessment ID
        :param str control_set_id: Control set ID
        :param str control_id: Control ID
        :return: Control assessment result or None
        :rtype: Optional[Dict[str, Any]]
        """
        try:
            client = self._get_client("auditmanager")

            response = client.get_change_logs(
                assessmentId=assessment_id, controlSetId=control_set_id, controlId=control_id
            )

            change_logs = response.get("changeLogs", [])
            if not change_logs:
                return None

            latest_change = max(change_logs, key=lambda x: x.get("createdAt", ""))

            return {
                "controlId": control_id,
                "status": latest_change.get("objectType", "UNDER_REVIEW"),
                "createdAt": latest_change.get("createdAt"),
                "createdBy": latest_change.get("createdBy"),
                "action": latest_change.get("action"),
            }

        except ClientError as e:
            if e.response["Error"]["Code"] not in ["ResourceNotFoundException", "AccessDeniedException"]:
                logger.error(f"Error getting control assessment results for {control_id}: {e}")
            return None

    def get_assessment_framework_details(self, framework_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a framework.

        :param str framework_id: Framework ID
        :return: Framework details or None
        :rtype: Optional[Dict[str, Any]]
        """
        try:
            client = self._get_client("auditmanager")

            response = client.get_assessment_framework(frameworkId=framework_id)
            framework = response.get("framework", {})

            return {
                "id": framework.get("id"),
                "arn": framework.get("arn"),
                "name": framework.get("name"),
                "type": framework.get("type"),
                "complianceType": framework.get("complianceType"),
                "description": framework.get("description"),
                "controlSets": framework.get("controlSets", []),
                "createdAt": str(framework.get("createdAt")) if framework.get("createdAt") else None,
            }

        except ClientError as e:
            if e.response["Error"]["Code"] not in ["ResourceNotFoundException", "AccessDeniedException"]:
                logger.error(f"Error getting framework details for {framework_id}: {e}")
            return None
