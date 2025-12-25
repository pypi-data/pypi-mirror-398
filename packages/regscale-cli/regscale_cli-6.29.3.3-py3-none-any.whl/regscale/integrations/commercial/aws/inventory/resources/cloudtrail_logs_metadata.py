"""AWS CloudTrail S3 Logs Metadata Collector.

This collector retrieves metadata about CloudTrail log files stored in S3
WITHOUT downloading or unzipping the files. It collects:
- File names
- File sizes
- Last modified dates
- S3 keys/paths

This metadata can then be saved as evidence in RegScale.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from botocore.exceptions import ClientError

from regscale.integrations.commercial.aws.inventory.base import BaseCollector

logger = logging.getLogger("regscale")


class CloudTrailLogsMetadataCollector(BaseCollector):
    """Collector for CloudTrail log file metadata from S3."""

    def __init__(
        self,
        session: Any,
        region: str,
        account_id: Optional[str] = None,
        days_back: int = 30,
        max_files: Optional[int] = None,
        tags: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize CloudTrail logs metadata collector.

        :param session: AWS session to use for API calls
        :param str region: AWS region to collect from
        :param str account_id: Optional AWS account ID to filter resources
        :param int days_back: Number of days back to collect logs (default: 30)
        :param int max_files: Optional maximum number of files to collect metadata for
        :param dict tags: Optional tags to filter trails (key-value pairs)
        """
        super().__init__(session, region)
        self.account_id = account_id
        self.days_back = days_back
        self.max_files = max_files
        self.tags = tags or {}

    def collect(self) -> Dict[str, Any]:
        """
        Collect CloudTrail log file metadata from S3 buckets.

        :return: Dictionary containing log file metadata
        :rtype: Dict[str, Any]
        """
        result = {
            "SnapshotDate": datetime.now(timezone.utc).isoformat(),
            "Region": self.region,
            "AccountId": self.account_id,
            "Trails": [],
            "TotalFiles": 0,
            "TotalSize": 0,
            "CollectionPeriodDays": self.days_back,
        }

        try:
            # First, get all CloudTrail trails to find S3 buckets
            cloudtrail_client = self._get_client("cloudtrail")
            trails = self._list_trails(cloudtrail_client)

            for trail in trails:
                trail_arn = trail.get("TrailARN", "")
                trail_name = trail.get("Name", "")

                # Get detailed trail information to find S3 bucket
                trail_details = self._describe_trail(cloudtrail_client, trail_arn)
                if not trail_details:
                    continue

                # Filter by tags if specified
                if self.tags:
                    trail_tags = self._get_trail_tags(cloudtrail_client, trail_arn)
                    if not self._matches_tags(trail_tags):
                        logger.debug(f"Skipping trail {trail_name} - does not match tag filters")
                        continue

                s3_bucket_name = trail_details.get("S3BucketName")
                s3_prefix = trail_details.get("S3KeyPrefix", "")

                if not s3_bucket_name:
                    logger.warning(f"Trail {trail_name} does not have an S3 bucket configured")
                    continue

                logger.info(f"Collecting log metadata from S3 bucket: {s3_bucket_name} for trail: {trail_name}")

                # Collect metadata for this trail's logs
                trail_log_metadata = self._collect_s3_log_metadata(
                    s3_bucket_name=s3_bucket_name,
                    s3_prefix=s3_prefix,
                    trail_name=trail_name,
                    trail_arn=trail_arn,
                )

                result["Trails"].append(trail_log_metadata)
                result["TotalFiles"] += trail_log_metadata["FileCount"]
                result["TotalSize"] += trail_log_metadata["TotalSize"]

            logger.info(
                f"Collected metadata for {result['TotalFiles']} CloudTrail log files "
                f"({self._format_size(result['TotalSize'])}) from {len(result['Trails'])} trail(s)"
            )

        except ClientError as e:
            self._handle_error(e, "CloudTrail logs metadata")
        except Exception as e:
            logger.error(f"Unexpected error collecting CloudTrail logs metadata: {e}", exc_info=True)

        return result

    def _list_trails(self, client: Any) -> List[Dict[str, Any]]:
        """
        List all CloudTrail trails.

        :param client: CloudTrail client
        :return: List of trail summaries
        :rtype: List[Dict[str, Any]]
        """
        try:
            response = client.list_trails()
            return response.get("Trails", [])
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDeniedException":
                logger.warning(f"Access denied to list CloudTrail trails in {self.region}")
                return []
            raise

    def _describe_trail(self, client: Any, trail_arn: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific trail.

        :param client: CloudTrail client
        :param str trail_arn: Trail ARN
        :return: Trail details or None if not found
        :rtype: Optional[Dict[str, Any]]
        """
        try:
            response = client.describe_trails(trailNameList=[trail_arn])
            trails = response.get("trailList", [])
            if trails:
                trail = trails[0]
                # Remove AWS response metadata for consistency
                trail.pop("ResponseMetadata", None)
                return trail
            return None
        except ClientError as e:
            logger.error(f"Error describing trail {trail_arn}: {e}")
            return None

    def _collect_s3_log_metadata(
        self, s3_bucket_name: str, s3_prefix: str, trail_name: str, trail_arn: str
    ) -> Dict[str, Any]:
        """
        Collect metadata for CloudTrail log files in an S3 bucket.

        This recursively collects ALL log files across all regions and dates
        within the CloudTrail folder structure.

        :param str s3_bucket_name: Name of the S3 bucket
        :param str s3_prefix: S3 key prefix for the trail logs
        :param str trail_name: Name of the CloudTrail trail
        :param str trail_arn: ARN of the CloudTrail trail
        :return: Dictionary containing log file metadata
        :rtype: Dict[str, Any]
        """
        s3_client = self._get_client("s3")
        full_prefix = self._build_s3_prefix(s3_prefix)
        trail_metadata = self._initialize_trail_metadata(trail_name, trail_arn, s3_bucket_name, s3_prefix, full_prefix)

        try:
            logger.info(f"Scanning S3 bucket {s3_bucket_name} with prefix: {full_prefix}")
            self._scan_s3_objects(s3_client, s3_bucket_name, full_prefix, trail_metadata)
            self._finalize_trail_metadata(trail_metadata, trail_name)

        except ClientError as e:
            self._handle_s3_client_error(e, s3_bucket_name)
        except Exception as e:
            logger.error(f"Unexpected error collecting S3 log metadata: {e}", exc_info=True)

        return trail_metadata

    def _build_s3_prefix(self, s3_prefix: str) -> str:
        """
        Build the full S3 prefix for CloudTrail log files.

        :param str s3_prefix: S3 key prefix for the trail logs
        :return: Full S3 prefix
        :rtype: str
        """
        full_prefix = f"{s3_prefix}/AWSLogs/" if s3_prefix else "AWSLogs/"

        if self.account_id:
            full_prefix = f"{full_prefix}{self.account_id}/CloudTrail/"
        else:
            full_prefix = f"{full_prefix}*/CloudTrail/"

        return full_prefix

    def _initialize_trail_metadata(
        self, trail_name: str, trail_arn: str, s3_bucket_name: str, s3_prefix: str, full_prefix: str
    ) -> Dict[str, Any]:
        """
        Initialize the trail metadata dictionary.

        :param str trail_name: Name of the CloudTrail trail
        :param str trail_arn: ARN of the CloudTrail trail
        :param str s3_bucket_name: Name of the S3 bucket
        :param str s3_prefix: S3 key prefix for the trail logs
        :param str full_prefix: Full S3 prefix for log files
        :return: Initialized trail metadata dictionary
        :rtype: Dict[str, Any]
        """
        return {
            "TrailName": trail_name,
            "TrailARN": trail_arn,
            "S3BucketName": s3_bucket_name,
            "S3Prefix": s3_prefix,
            "FullLogPrefix": full_prefix,
            "FileCount": 0,
            "TotalSize": 0,
            "Files": [],
            "FilesByRegion": {},
            "FilesByDate": {},
        }

    def _scan_s3_objects(
        self, s3_client: Any, s3_bucket_name: str, full_prefix: str, trail_metadata: Dict[str, Any]
    ) -> None:
        """
        Scan S3 objects and collect metadata for CloudTrail log files.

        :param s3_client: S3 client
        :param str s3_bucket_name: Name of the S3 bucket
        :param str full_prefix: Full S3 prefix for log files
        :param dict trail_metadata: Trail metadata dictionary to populate
        """
        paginator = s3_client.get_paginator("list_objects_v2")
        file_count = 0

        for page in paginator.paginate(Bucket=s3_bucket_name, Prefix=full_prefix):
            if "Contents" not in page:
                logger.info(f"No log files found in S3 bucket {s3_bucket_name} with prefix {full_prefix}")
                break

            for obj in page["Contents"]:
                if not obj["Key"].endswith(".json.gz"):
                    continue

                if self._max_files_reached(file_count):
                    return

                self._process_s3_object(obj, trail_metadata)
                file_count += 1

            if self._max_files_reached(file_count):
                break

    def _max_files_reached(self, file_count: int) -> bool:
        """
        Check if the maximum file limit has been reached.

        :param int file_count: Current file count
        :return: True if max files reached
        :rtype: bool
        """
        if self.max_files and file_count >= self.max_files:
            logger.info(f"Reached maximum file limit: {self.max_files}")
            return True
        return False

    def _process_s3_object(self, obj: Dict[str, Any], trail_metadata: Dict[str, Any]) -> None:
        """
        Process a single S3 object and add its metadata to the trail metadata.

        :param dict obj: S3 object metadata
        :param dict trail_metadata: Trail metadata dictionary to update
        """
        key = obj["Key"]
        file_region, file_date = self._extract_region_and_date(key)

        file_metadata = {
            "Key": key,
            "FileName": key.split("/")[-1],
            "Region": file_region,
            "Date": file_date,
            "Size": obj["Size"],
            "SizeFormatted": self._format_size(obj["Size"]),
            "LastModified": obj["LastModified"].isoformat(),
            "LastModifiedTimestamp": obj["LastModified"].timestamp(),
            "ETag": obj.get("ETag", "").strip('"'),
            "StorageClass": obj.get("StorageClass", "STANDARD"),
        }

        trail_metadata["Files"].append(file_metadata)
        trail_metadata["TotalSize"] += obj["Size"]

        self._organize_by_region(trail_metadata, file_region, obj["Size"], file_metadata["FileName"])
        self._organize_by_date(trail_metadata, file_date, obj["Size"], file_metadata["FileName"])

    def _extract_region_and_date(self, key: str) -> tuple:
        """
        Extract region and date from S3 key.

        :param str key: S3 object key
        :return: Tuple of (region, date)
        :rtype: tuple
        """
        key_parts = key.split("/")
        try:
            ct_index = key_parts.index("CloudTrail")
            file_region = key_parts[ct_index + 1] if len(key_parts) > ct_index + 1 else "unknown"
            file_year = key_parts[ct_index + 2] if len(key_parts) > ct_index + 2 else ""
            file_month = key_parts[ct_index + 3] if len(key_parts) > ct_index + 3 else ""
            file_day = key_parts[ct_index + 4] if len(key_parts) > ct_index + 4 else ""
            file_date = f"{file_year}-{file_month}-{file_day}" if file_year else "unknown"
        except (ValueError, IndexError):
            file_region = "unknown"
            file_date = "unknown"

        return file_region, file_date

    def _organize_by_region(
        self, trail_metadata: Dict[str, Any], file_region: str, file_size: int, file_name: str
    ) -> None:
        """
        Organize file metadata by region.

        :param dict trail_metadata: Trail metadata dictionary to update
        :param str file_region: AWS region
        :param int file_size: File size in bytes
        :param str file_name: File name
        """
        if file_region not in trail_metadata["FilesByRegion"]:
            trail_metadata["FilesByRegion"][file_region] = {"Count": 0, "TotalSize": 0, "Files": []}

        trail_metadata["FilesByRegion"][file_region]["Count"] += 1
        trail_metadata["FilesByRegion"][file_region]["TotalSize"] += file_size
        trail_metadata["FilesByRegion"][file_region]["Files"].append(file_name)

    def _organize_by_date(self, trail_metadata: Dict[str, Any], file_date: str, file_size: int, file_name: str) -> None:
        """
        Organize file metadata by date.

        :param dict trail_metadata: Trail metadata dictionary to update
        :param str file_date: File date (YYYY-MM-DD)
        :param int file_size: File size in bytes
        :param str file_name: File name
        """
        if file_date not in trail_metadata["FilesByDate"]:
            trail_metadata["FilesByDate"][file_date] = {"Count": 0, "TotalSize": 0, "Files": []}

        trail_metadata["FilesByDate"][file_date]["Count"] += 1
        trail_metadata["FilesByDate"][file_date]["TotalSize"] += file_size
        trail_metadata["FilesByDate"][file_date]["Files"].append(file_name)

    def _finalize_trail_metadata(self, trail_metadata: Dict[str, Any], trail_name: str) -> None:
        """
        Finalize trail metadata by calculating date ranges and logging results.

        :param dict trail_metadata: Trail metadata dictionary to finalize
        :param str trail_name: Name of the CloudTrail trail
        """
        trail_metadata["FileCount"] = len(trail_metadata["Files"])

        if trail_metadata["Files"]:
            timestamps = [f["LastModifiedTimestamp"] for f in trail_metadata["Files"]]
            trail_metadata["OldestLogDate"] = datetime.fromtimestamp(min(timestamps)).isoformat()
            trail_metadata["NewestLogDate"] = datetime.fromtimestamp(max(timestamps)).isoformat()

        logger.info(
            f"Found {trail_metadata['FileCount']} log files "
            f"({self._format_size(trail_metadata['TotalSize'])}) for trail {trail_name}"
        )

    def _handle_s3_client_error(self, error: ClientError, s3_bucket_name: str) -> None:
        """
        Handle S3 client errors.

        :param ClientError error: The client error
        :param str s3_bucket_name: Name of the S3 bucket
        """
        error_code = error.response["Error"]["Code"]
        if error_code == "NoSuchBucket":
            logger.error(f"S3 bucket does not exist: {s3_bucket_name}")
        elif error_code == "AccessDenied":
            logger.error(f"Access denied to S3 bucket: {s3_bucket_name}")
        else:
            logger.error(f"Error accessing S3 bucket {s3_bucket_name}: {error}")

    def _get_trail_tags(self, client: Any, trail_arn: str) -> Dict[str, str]:
        """
        Get tags for a CloudTrail trail.

        :param client: CloudTrail client
        :param str trail_arn: Trail ARN
        :return: Dictionary of tags (Key -> Value)
        :rtype: Dict[str, str]
        """
        try:
            response = client.list_tags(ResourceIdList=[trail_arn])
            resource_tag_list = response.get("ResourceTagList", [])
            if resource_tag_list and "TagsList" in resource_tag_list[0]:
                tags_list = resource_tag_list[0]["TagsList"]
                # Convert list of {"Key": "k", "Value": "v"} to {"k": "v"}
                return {tag.get("Key", ""): tag.get("Value", "") for tag in tags_list}
            return {}
        except ClientError as e:
            logger.debug(f"Error getting tags for trail {trail_arn}: {e}")
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

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """
        Format bytes into human-readable size.

        :param int size_bytes: Size in bytes
        :return: Formatted size string (e.g., "1.5 MB")
        :rtype: str
        """
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"

    def export_to_json(self, output_file: str = "cloudtrail_logs_metadata.json") -> str:
        """
        Collect metadata and export to JSON file.

        :param str output_file: Path to output JSON file
        :return: Path to the created JSON file
        :rtype: str
        """
        metadata = self.collect()

        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

            logger.info(f"CloudTrail logs metadata exported to: {output_file}")
            return output_file

        except Exception as e:
            logger.error(f"Error exporting metadata to JSON: {e}")
            raise
