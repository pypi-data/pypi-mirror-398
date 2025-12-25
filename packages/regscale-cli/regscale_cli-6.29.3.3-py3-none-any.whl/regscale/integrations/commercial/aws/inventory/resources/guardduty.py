"""AWS GuardDuty resource collection."""

import logging
from typing import Any, Dict, List, Optional

from botocore.exceptions import ClientError

from regscale.integrations.commercial.aws.inventory.base import BaseCollector

logger = logging.getLogger("regscale")


class GuardDutyCollector(BaseCollector):
    """Collector for AWS GuardDuty resources."""

    def __init__(
        self,
        session: Any,
        region: str,
        account_id: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        collect_findings: bool = True,
    ):
        """
        Initialize GuardDuty collector.

        :param session: AWS session to use for API calls
        :param str region: AWS region to collect from
        :param str account_id: Optional AWS account ID to filter resources
        :param dict tags: Optional tags to filter resources (key-value pairs)
        :param bool collect_findings: Whether to collect GuardDuty findings. Default True.
        """
        super().__init__(session, region)
        self.account_id = account_id
        self.tags = tags or {}
        self.collect_findings = collect_findings

    def collect(self) -> Dict[str, Any]:
        """
        Collect GuardDuty resources.

        :return: Dictionary containing GuardDuty detectors, findings, and members
        :rtype: Dict[str, Any]
        """
        result = {"Detectors": [], "Findings": [], "Members": []}

        try:
            client = self._get_client("guardduty")
            detector_ids = self._list_detectors(client)

            for detector_id in detector_ids:
                self._process_detector(client, detector_id, result)

            if self.collect_findings:
                logger.info(
                    f"Collected {len(result['Detectors'])} GuardDuty detector(s), "
                    f"{len(result['Findings'])} finding(s) from {self.region}"
                )
            else:
                logger.info(f"Collected {len(result['Detectors'])} GuardDuty detector(s) from {self.region}")

        except ClientError as e:
            self._handle_error(e, "GuardDuty resources")
        except Exception as e:
            logger.error(f"Unexpected error collecting GuardDuty resources: {e}", exc_info=True)

        return result

    def _process_detector(self, client: Any, detector_id: str, result: Dict[str, Any]) -> None:
        """
        Process a single detector and add its details to result.

        :param client: GuardDuty client
        :param str detector_id: Detector ID to process
        :param dict result: Result dictionary to populate
        """
        detector_info = self._get_detector(client, detector_id)
        if not detector_info:
            return

        if not self._should_include_detector(detector_info, detector_id):
            return

        detector_info = self._enrich_detector_info(client, detector_id, detector_info)
        result["Detectors"].append(detector_info)

        if self.collect_findings:
            findings = self._list_and_get_findings(client, detector_id)
            result["Findings"].extend(findings)
        else:
            logger.debug(f"Skipping GuardDuty findings collection for detector {detector_id} (collect_findings=False)")

        members = self._list_members(client, detector_id)
        result["Members"].extend(members)

    def _should_include_detector(self, detector_info: Dict[str, Any], detector_id: str) -> bool:
        """
        Check if detector should be included based on filters.

        :param dict detector_info: Detector information
        :param str detector_id: Detector ID
        :return: True if detector should be included
        :rtype: bool
        """
        if self.account_id and not self._matches_account_id(detector_info.get("AccountId", "")):
            logger.debug(f"Skipping detector {detector_id} - does not match account ID {self.account_id}")
            return False

        if self.tags:
            detector_tags = self._get_detector_tags(
                self._get_client("guardduty"), detector_id, detector_info.get("AccountId", "")
            )
            if not self._matches_tags(detector_tags):
                logger.debug(f"Skipping detector {detector_id} - does not match tag filters")
                return False

        return True

    def _enrich_detector_info(self, client: Any, detector_id: str, detector_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich detector info with additional metadata.

        :param client: GuardDuty client
        :param str detector_id: Detector ID
        :param dict detector_info: Detector information to enrich
        :return: Enriched detector information
        :rtype: Dict[str, Any]
        """
        if self.tags:
            detector_tags = self._get_detector_tags(client, detector_id, detector_info.get("AccountId", ""))
            detector_info["Tags"] = detector_tags

        detector_info["DetectorId"] = detector_id
        detector_info["Region"] = self.region
        return detector_info

    def _list_detectors(self, client: Any) -> List[str]:
        """
        List GuardDuty detectors.

        :param client: GuardDuty client
        :return: List of detector IDs
        :rtype: List[str]
        """
        try:
            response = client.list_detectors()
            return response.get("DetectorIds", [])
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDeniedException":
                logger.warning(f"Access denied to list GuardDuty detectors in {self.region}")
                return []
            raise

    def _get_detector(self, client: Any, detector_id: str) -> Optional[Dict[str, Any]]:
        """
        Get details about a specific GuardDuty detector.

        :param client: GuardDuty client
        :param str detector_id: Detector ID
        :return: Detector details or None
        :rtype: Optional[Dict[str, Any]]
        """
        try:
            response = client.get_detector(DetectorId=detector_id)
            # Remove ResponseMetadata
            response.pop("ResponseMetadata", None)
            return response
        except ClientError as e:
            logger.error(f"Error getting detector {detector_id}: {e}")
            return None

    def _list_and_get_findings(self, client: Any, detector_id: str, max_findings: int = 50) -> List[Dict[str, Any]]:
        """
        List and get detailed information about GuardDuty findings.

        :param client: GuardDuty client
        :param str detector_id: Detector ID
        :param int max_findings: Maximum number of findings to retrieve
        :return: List of findings with details
        :rtype: List[Dict[str, Any]]
        """
        findings = []

        try:
            # List finding IDs
            list_response = client.list_findings(DetectorId=detector_id, MaxResults=max_findings)
            finding_ids = list_response.get("FindingIds", [])

            if not finding_ids:
                return findings

            # Get detailed information for findings
            get_response = client.get_findings(DetectorId=detector_id, FindingIds=finding_ids)
            findings = get_response.get("Findings", [])

            # Add region information
            for finding in findings:
                finding["Region"] = self.region
                finding["DetectorId"] = detector_id

        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDeniedException":
                logger.warning(f"Access denied to list findings for detector {detector_id}")
            else:
                logger.error(f"Error listing findings for detector {detector_id}: {e}")

        return findings

    def _list_members(self, client: Any, detector_id: str) -> List[Dict[str, Any]]:
        """
        List member accounts for a GuardDuty detector.

        :param client: GuardDuty client
        :param str detector_id: Detector ID
        :return: List of member accounts
        :rtype: List[Dict[str, Any]]
        """
        members = []

        try:
            response = client.list_members(DetectorId=detector_id)
            members = response.get("Members", [])

            # Add region and detector information
            for member in members:
                member["Region"] = self.region
                member["DetectorId"] = detector_id

        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDeniedException":
                logger.debug(f"Access denied to list members for detector {detector_id}")
            else:
                logger.error(f"Error listing members for detector {detector_id}: {e}")

        return members

    def _matches_account_id(self, detector_account_id: str) -> bool:
        """
        Check if detector account ID matches the specified account ID.

        :param str detector_account_id: Account ID from detector
        :return: True if matches or no account_id filter specified
        :rtype: bool
        """
        if not self.account_id:
            return True

        return detector_account_id == self.account_id

    def _get_detector_tags(self, client: Any, detector_id: str, account_id: str) -> Dict[str, str]:
        """
        Get tags for a GuardDuty detector.

        :param client: GuardDuty client
        :param str detector_id: Detector ID
        :param str account_id: AWS account ID
        :return: Dictionary of tags (TagKey -> TagValue)
        :rtype: Dict[str, str]
        """
        try:
            # Construct the detector ARN
            detector_arn = f"arn:aws:guardduty:{self.region}:{account_id}:detector/{detector_id}"
            response = client.list_tags_for_resource(ResourceArn=detector_arn)
            tags = response.get("Tags", {})
            return tags
        except ClientError as e:
            logger.debug(f"Error getting tags for detector {detector_id}: {e}")
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
