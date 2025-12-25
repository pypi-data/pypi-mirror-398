"""AWS Systems Manager resource collection."""

import logging
from typing import Any, Dict, List, Optional

from botocore.exceptions import ClientError

from regscale.integrations.commercial.aws.inventory.base import BaseCollector

logger = logging.getLogger("regscale")


class SystemsManagerCollector(BaseCollector):
    """Collector for AWS Systems Manager resources."""

    def __init__(
        self, session: Any, region: str, account_id: Optional[str] = None, tags: Optional[Dict[str, str]] = None
    ):
        """
        Initialize Systems Manager collector.

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
        Collect AWS Systems Manager resources.

        :return: Dictionary containing Systems Manager information
        :rtype: Dict[str, Any]
        """
        result = {
            "ManagedInstances": [],
            "Parameters": [],
            "Documents": [],
            "PatchBaselines": [],
            "MaintenanceWindows": [],
            "Associations": [],
            "InventoryEntries": [],
            "ComplianceSummary": {},
        }

        try:
            client = self._get_client("ssm")

            # Get managed instances
            managed_instances = self._list_managed_instances(client)
            result["ManagedInstances"] = managed_instances

            # Get parameters
            parameters = self._list_parameters(client)
            result["Parameters"] = parameters

            # Get documents
            documents = self._list_documents(client)
            result["Documents"] = documents

            # Get patch baselines
            patch_baselines = self._list_patch_baselines(client)
            result["PatchBaselines"] = patch_baselines

            # Get maintenance windows
            maintenance_windows = self._list_maintenance_windows(client)
            result["MaintenanceWindows"] = maintenance_windows

            # Get associations
            associations = self._list_associations(client)
            result["Associations"] = associations

            # Get compliance summary
            compliance_summary = self._get_compliance_summary(client)
            result["ComplianceSummary"] = compliance_summary

            logger.info(
                f"Collected {len(managed_instances)} managed instance(s), "
                f"{len(parameters)} parameter(s) from {self.region}"
            )

        except ClientError as e:
            self._handle_error(e, "Systems Manager resources")
        except Exception as e:
            logger.error(f"Unexpected error collecting Systems Manager resources: {e}", exc_info=True)

        return result

    def _list_managed_instances(self, client: Any) -> List[Dict[str, Any]]:
        """
        List managed instances.

        :param client: SSM client
        :return: List of managed instance information
        :rtype: List[Dict[str, Any]]
        """
        instances = []
        try:
            paginator = client.get_paginator("describe_instance_information")

            for page in paginator.paginate():
                for instance in page.get("InstanceInformationList", []):
                    instance_dict = {
                        "Region": self.region,
                        "InstanceId": instance.get("InstanceId"),
                        "PingStatus": instance.get("PingStatus"),
                        "LastPingDateTime": str(instance.get("LastPingDateTime")),
                        "AgentVersion": instance.get("AgentVersion"),
                        "IsLatestVersion": instance.get("IsLatestVersion", False),
                        "PlatformType": instance.get("PlatformType"),
                        "PlatformName": instance.get("PlatformName"),
                        "PlatformVersion": instance.get("PlatformVersion"),
                        "ResourceType": instance.get("ResourceType"),
                        "IPAddress": instance.get("IPAddress"),
                        "ComputerName": instance.get("ComputerName"),
                        "AssociationStatus": instance.get("AssociationStatus"),
                        "LastAssociationExecutionDate": (
                            str(instance.get("LastAssociationExecutionDate"))
                            if instance.get("LastAssociationExecutionDate")
                            else None
                        ),
                        "LastSuccessfulAssociationExecutionDate": (
                            str(instance.get("LastSuccessfulAssociationExecutionDate"))
                            if instance.get("LastSuccessfulAssociationExecutionDate")
                            else None
                        ),
                    }

                    # Get instance patches
                    patches = self._get_instance_patches(client, instance["InstanceId"])
                    instance_dict["PatchSummary"] = patches

                    instances.append(instance_dict)

        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDeniedException":
                logger.warning(f"Access denied to list managed instances in {self.region}")
            else:
                logger.error(f"Error listing managed instances: {e}")

        return instances

    def _get_instance_patches(self, client: Any, instance_id: str) -> Dict[str, Any]:
        """
        Get patch summary for an instance.

        :param client: SSM client
        :param str instance_id: Instance ID
        :return: Patch summary
        :rtype: Dict[str, Any]
        """
        try:
            response = client.describe_instance_patches(InstanceId=instance_id, MaxResults=50)
            patches = response.get("Patches", [])

            summary = {
                "TotalPatches": len(patches),
                "Installed": sum(1 for p in patches if p.get("State") == "Installed"),
                "InstalledOther": sum(1 for p in patches if p.get("State") == "InstalledOther"),
                "Missing": sum(1 for p in patches if p.get("State") == "Missing"),
                "Failed": sum(1 for p in patches if p.get("State") == "Failed"),
                "NotApplicable": sum(1 for p in patches if p.get("State") == "NotApplicable"),
            }
            return summary
        except ClientError as e:
            if e.response["Error"]["Code"] not in ["AccessDeniedException", "InvalidInstanceId"]:
                logger.debug(f"Error getting patches for instance {instance_id}: {e}")
            return {}

    def _list_parameters(self, client: Any) -> List[Dict[str, Any]]:
        """
        List SSM parameters.

        :param client: SSM client
        :return: List of parameter information
        :rtype: List[Dict[str, Any]]
        """
        parameters = []
        try:
            paginator = client.get_paginator("describe_parameters")

            for page in paginator.paginate():
                for param in page.get("Parameters", []):
                    param_name = param.get("Name")

                    # Get tags for filtering
                    param_tags = self._get_resource_tags(client, "Parameter", param_name)

                    # Filter by tags if specified
                    if self.tags and not self._matches_tags(param_tags):
                        logger.debug(f"Skipping parameter {param_name} - does not match tag filters")
                        continue

                    parameters.append(
                        {
                            "Region": self.region,
                            "Name": param_name,
                            "Type": param.get("Type"),
                            "KeyId": param.get("KeyId"),
                            "LastModifiedDate": str(param.get("LastModifiedDate")),
                            "Description": param.get("Description"),
                            "Version": param.get("Version"),
                            "Tier": param.get("Tier"),
                            "Policies": param.get("Policies", []),
                            "DataType": param.get("DataType"),
                            "Tags": param_tags,
                        }
                    )

        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDeniedException":
                logger.warning(f"Access denied to list parameters in {self.region}")
            else:
                logger.error(f"Error listing parameters: {e}")

        return parameters

    def _list_documents(self, client: Any) -> List[Dict[str, Any]]:
        """
        List SSM documents.

        :param client: SSM client
        :return: List of document information
        :rtype: List[Dict[str, Any]]
        """
        documents = []
        try:
            filters = self._build_document_filters()
            paginator = client.get_paginator("list_documents")

            for page in paginator.paginate(Filters=filters):
                for doc in page.get("DocumentIdentifiers", []):
                    if not self._should_include_document(doc):
                        continue

                    document_dict = self._build_document_dict(doc)
                    documents.append(document_dict)

        except ClientError as e:
            self._handle_document_error(e)

        return documents

    def _build_document_filters(self) -> List[Dict[str, Any]]:
        """
        Build filters for listing documents.

        :return: List of filters for document pagination
        :rtype: List[Dict[str, Any]]
        """
        filters = []
        if self.account_id:
            filters.append({"Key": "Owner", "Values": [self.account_id]})
        return filters

    def _should_include_document(self, doc: Dict[str, Any]) -> bool:
        """
        Check if document should be included based on filters.

        :param dict doc: Document information from AWS API
        :return: True if document should be included
        :rtype: bool
        """
        if not self._matches_account_filter(doc):
            return False

        doc_tags = self._extract_document_tags(doc)
        if not self._matches_tag_filter(doc, doc_tags):
            return False

        return True

    def _matches_account_filter(self, doc: Dict[str, Any]) -> bool:
        """
        Check if document matches account filter.

        :param dict doc: Document information from AWS API
        :return: True if document matches account filter
        :rtype: bool
        """
        if not self.account_id:
            return True

        owner = doc.get("Owner", "")
        if not owner:
            return True

        is_amazon_document = owner.startswith("Amazon")
        is_account_owner = owner == self.account_id
        return is_amazon_document or is_account_owner

    def _extract_document_tags(self, doc: Dict[str, Any]) -> Dict[str, str]:
        """
        Extract tags from document as a dictionary.

        :param dict doc: Document information from AWS API
        :return: Dictionary of tags (Key -> Value)
        :rtype: Dict[str, str]
        """
        doc_tags_list = doc.get("Tags", [])
        return {tag["Key"]: tag["Value"] for tag in doc_tags_list}

    def _matches_tag_filter(self, doc: Dict[str, Any], doc_tags: Dict[str, str]) -> bool:
        """
        Check if document matches tag filters.

        :param dict doc: Document information from AWS API
        :param dict doc_tags: Extracted document tags
        :return: True if document matches tag filters
        :rtype: bool
        """
        if not self.tags:
            return True

        if not self._matches_tags(doc_tags):
            doc_name = doc.get("Name")
            logger.debug(f"Skipping document {doc_name} - does not match tag filters")
            return False

        return True

    def _build_document_dict(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build document dictionary for output.

        :param dict doc: Document information from AWS API
        :return: Formatted document dictionary
        :rtype: Dict[str, Any]
        """
        doc_tags_list = doc.get("Tags", [])
        return {
            "Region": self.region,
            "Name": doc.get("Name"),
            "Owner": doc.get("Owner"),
            "VersionName": doc.get("VersionName"),
            "PlatformTypes": doc.get("PlatformTypes", []),
            "DocumentVersion": doc.get("DocumentVersion"),
            "DocumentType": doc.get("DocumentType"),
            "SchemaVersion": doc.get("SchemaVersion"),
            "DocumentFormat": doc.get("DocumentFormat"),
            "TargetType": doc.get("TargetType"),
            "Tags": doc_tags_list,
        }

    def _handle_document_error(self, error: ClientError) -> None:
        """
        Handle errors when listing documents.

        :param ClientError error: The client error to handle
        """
        if error.response["Error"]["Code"] == "AccessDeniedException":
            logger.warning(f"Access denied to list documents in {self.region}")
        else:
            logger.error(f"Error listing documents: {error}")

    def _list_patch_baselines(self, client: Any) -> List[Dict[str, Any]]:
        """
        List patch baselines.

        :param client: SSM client
        :return: List of patch baseline information
        :rtype: List[Dict[str, Any]]
        """
        baselines = []
        try:
            filters = self._build_baseline_filters()
            paginator = client.get_paginator("describe_patch_baselines")

            for page in paginator.paginate(Filters=filters):
                for baseline in page.get("BaselineIdentities", []):
                    baseline_dict = self._process_baseline(client, baseline)
                    if baseline_dict:
                        baselines.append(baseline_dict)

        except ClientError as e:
            self._handle_baseline_error(e)

        return baselines

    def _build_baseline_filters(self) -> List[Dict[str, Any]]:
        """
        Build filters for listing patch baselines.

        :return: List of filters for baseline pagination
        :rtype: List[Dict[str, Any]]
        """
        filters = []
        if self.account_id:
            filters.append({"Key": "OWNER", "Values": [self.account_id]})
        return filters

    def _process_baseline(self, client: Any, baseline: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process a single patch baseline.

        :param client: SSM client
        :param dict baseline: Baseline information from AWS API
        :return: Formatted baseline dictionary or None if filtered out
        :rtype: Optional[Dict[str, Any]]
        """
        try:
            baseline_id = baseline["BaselineId"]
            baseline_detail = client.get_patch_baseline(BaselineId=baseline_id)
            baseline_tags = self._get_resource_tags(client, "PatchBaseline", baseline_id)

            if not self._should_include_baseline(baseline_id, baseline_tags):
                return None

            return self._build_baseline_dict(baseline, baseline_detail, baseline_tags)

        except ClientError as e:
            self._handle_baseline_processing_error(e, baseline)
            return None

    def _should_include_baseline(self, baseline_id: str, baseline_tags: Dict[str, str]) -> bool:
        """
        Check if baseline should be included based on tag filters.

        :param str baseline_id: Baseline identifier
        :param dict baseline_tags: Baseline tags
        :return: True if baseline should be included
        :rtype: bool
        """
        if not self.tags:
            return True

        if not self._matches_tags(baseline_tags):
            logger.debug(f"Skipping patch baseline {baseline_id} - does not match tag filters")
            return False

        return True

    def _build_baseline_dict(
        self, baseline: Dict[str, Any], baseline_detail: Dict[str, Any], baseline_tags: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Build baseline dictionary for output.

        :param dict baseline: Baseline identity from AWS API
        :param dict baseline_detail: Detailed baseline information from AWS API
        :param dict baseline_tags: Baseline tags
        :return: Formatted baseline dictionary
        :rtype: Dict[str, Any]
        """
        return {
            "Region": self.region,
            "BaselineId": baseline["BaselineId"],
            "BaselineName": baseline.get("BaselineName"),
            "OperatingSystem": baseline.get("OperatingSystem"),
            "DefaultBaseline": baseline.get("DefaultBaseline", False),
            "Description": baseline_detail.get("BaselineDescription"),
            "ApprovalRules": baseline_detail.get("ApprovalRules", {}),
            "ApprovedPatches": baseline_detail.get("ApprovedPatches", []),
            "RejectedPatches": baseline_detail.get("RejectedPatches", []),
            "CreatedDate": self._format_date(baseline_detail.get("CreatedDate")),
            "ModifiedDate": self._format_date(baseline_detail.get("ModifiedDate")),
            "Tags": baseline_tags,
        }

    def _format_date(self, date_value: Any) -> Optional[str]:
        """
        Format date value to string.

        :param date_value: Date value to format
        :return: Formatted date string or None
        :rtype: Optional[str]
        """
        if date_value:
            return str(date_value)
        return None

    def _handle_baseline_processing_error(self, error: ClientError, baseline: Dict[str, Any]) -> None:
        """
        Handle errors when processing individual baseline.

        :param ClientError error: The client error to handle
        :param dict baseline: The baseline being processed
        """
        error_code = error.response["Error"]["Code"]
        if error_code not in ["AccessDeniedException", "DoesNotExistException"]:
            baseline_id = baseline.get("BaselineId", "unknown")
            logger.error(f"Error getting baseline {baseline_id}: {error}")

    def _handle_baseline_error(self, error: ClientError) -> None:
        """
        Handle errors when listing patch baselines.

        :param ClientError error: The client error to handle
        """
        if error.response["Error"]["Code"] == "AccessDeniedException":
            logger.warning(f"Access denied to list patch baselines in {self.region}")
        else:
            logger.error(f"Error listing patch baselines: {error}")

    def _list_maintenance_windows(self, client: Any) -> List[Dict[str, Any]]:
        """
        List maintenance windows.

        :param client: SSM client
        :return: List of maintenance window information
        :rtype: List[Dict[str, Any]]
        """
        windows = []
        try:
            paginator = client.get_paginator("describe_maintenance_windows")

            for page in paginator.paginate():
                for window in page.get("WindowIdentities", []):
                    window_id = window.get("WindowId")

                    # Get tags for filtering
                    window_tags = self._get_resource_tags(client, "MaintenanceWindow", window_id)

                    # Filter by tags if specified
                    if self.tags and not self._matches_tags(window_tags):
                        logger.debug(f"Skipping maintenance window {window_id} - does not match tag filters")
                        continue

                    windows.append(
                        {
                            "Region": self.region,
                            "WindowId": window_id,
                            "Name": window.get("Name"),
                            "Description": window.get("Description"),
                            "Enabled": window.get("Enabled", False),
                            "Duration": window.get("Duration"),
                            "Cutoff": window.get("Cutoff"),
                            "Schedule": window.get("Schedule"),
                            "ScheduleTimezone": window.get("ScheduleTimezone"),
                            "NextExecutionTime": window.get("NextExecutionTime"),
                            "Tags": window_tags,
                        }
                    )

        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDeniedException":
                logger.warning(f"Access denied to list maintenance windows in {self.region}")
            else:
                logger.error(f"Error listing maintenance windows: {e}")

        return windows

    def _list_associations(self, client: Any) -> List[Dict[str, Any]]:
        """
        List associations.

        :param client: SSM client
        :return: List of association information
        :rtype: List[Dict[str, Any]]
        """
        associations = []
        try:
            paginator = client.get_paginator("list_associations")

            for page in paginator.paginate():
                for assoc in page.get("Associations", []):
                    associations.append(
                        {
                            "Region": self.region,
                            "AssociationId": assoc.get("AssociationId"),
                            "AssociationName": assoc.get("AssociationName"),
                            "InstanceId": assoc.get("InstanceId"),
                            "DocumentVersion": assoc.get("DocumentVersion"),
                            "Targets": assoc.get("Targets", []),
                            "LastExecutionDate": (
                                str(assoc.get("LastExecutionDate")) if assoc.get("LastExecutionDate") else None
                            ),
                            "ScheduleExpression": assoc.get("ScheduleExpression"),
                            "AssociationVersion": assoc.get("AssociationVersion"),
                        }
                    )

        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDeniedException":
                logger.warning(f"Access denied to list associations in {self.region}")
            else:
                logger.error(f"Error listing associations: {e}")

        return associations

    def _get_compliance_summary(self, client: Any) -> Dict[str, Any]:
        """
        Get compliance summary.

        :param client: SSM client
        :return: Compliance summary
        :rtype: Dict[str, Any]
        """
        try:
            response = client.list_compliance_summaries(MaxResults=50)
            summaries = response.get("ComplianceSummaryItems", [])

            if not summaries:
                return {}

            # Aggregate compliance data
            total_compliant = sum(item.get("CompliantCount", 0) for item in summaries)
            total_non_compliant = sum(item.get("NonCompliantCount", 0) for item in summaries)

            return {
                "TotalCompliant": total_compliant,
                "TotalNonCompliant": total_non_compliant,
                "ComplianceTypes": [
                    {
                        "ComplianceType": item.get("ComplianceType"),
                        "CompliantCount": item.get("CompliantCount", 0),
                        "NonCompliantCount": item.get("NonCompliantCount", 0),
                    }
                    for item in summaries
                ],
            }
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDeniedException":
                logger.warning(f"Access denied to get compliance summary in {self.region}")
            else:
                logger.debug(f"Error getting compliance summary: {e}")
            return {}

    def _get_resource_tags(self, client: Any, resource_type: str, resource_id: str) -> Dict[str, str]:
        """
        Get tags for a Systems Manager resource.

        :param client: SSM client
        :param str resource_type: Resource type (e.g., 'Parameter', 'Document', 'PatchBaseline', 'MaintenanceWindow')
        :param str resource_id: Resource identifier (name, ID, or ARN)
        :return: Dictionary of tags (Key -> Value)
        :rtype: Dict[str, str]
        """
        try:
            response = client.list_tags_for_resource(ResourceType=resource_type, ResourceId=resource_id)
            tags_list = response.get("TagList", [])
            return {tag["Key"]: tag["Value"] for tag in tags_list}
        except ClientError as e:
            if e.response["Error"]["Code"] not in ["AccessDeniedException", "InvalidResourceId"]:
                logger.debug(f"Error getting tags for {resource_type} {resource_id}: {e}")
            return {}

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
