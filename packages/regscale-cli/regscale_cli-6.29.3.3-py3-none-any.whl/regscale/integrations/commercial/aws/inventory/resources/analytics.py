"""AWS analytics resource collectors."""

import logging
from typing import Dict, List, Any, Optional

from ..base import BaseCollector

logger = logging.getLogger("regscale")


class AnalyticsCollector(BaseCollector):
    """Collector for AWS analytics resources with filtering support."""

    def __init__(
        self,
        session: Any,
        region: str,
        account_id: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        enabled_services: Optional[Dict[str, bool]] = None,
    ):
        """
        Initialize analytics collector with filtering support.

        :param session: AWS session to use for API calls
        :param str region: AWS region to collect from
        :param str account_id: Optional AWS account ID to filter resources
        :param dict tags: Optional tag filters (AND logic)
        :param dict enabled_services: Optional dict of service names to boolean flags for enabling/disabling collection
        """
        super().__init__(session, region, account_id, tags)
        self.enabled_services = enabled_services or {}

    def get_emr_clusters(self) -> List[Dict[str, Any]]:
        """
        Get information about EMR clusters.

        :return: List of EMR cluster information
        :rtype: List[Dict[str, Any]]
        """
        clusters = []
        try:
            emr_client = self._get_client("emr")
            paginator = emr_client.get_paginator("list_clusters")

            for page in paginator.paginate(ClusterStates=["STARTING", "BOOTSTRAPPING", "RUNNING", "WAITING"]):
                for cluster_summary in page.get("Clusters", []):
                    cluster_id = cluster_summary.get("Id")

                    try:
                        cluster_detail = emr_client.describe_cluster(ClusterId=cluster_id)
                        cluster = cluster_detail.get("Cluster", {})
                        cluster_arn = cluster.get("ClusterArn", "")

                        if not self._matches_account(cluster_arn):
                            continue

                        if not self._matches_tags(cluster.get("Tags", [])):
                            continue

                        clusters.append(
                            {
                                "Region": self.region,
                                "ClusterId": cluster_id,
                                "ClusterArn": cluster_arn,
                                "Name": cluster.get("Name"),
                                "Status": cluster.get("Status", {}).get("State"),
                                "NormalizedInstanceHours": cluster.get("NormalizedInstanceHours"),
                                "MasterPublicDnsName": cluster.get("MasterPublicDnsName"),
                                "ReleaseLabel": cluster.get("ReleaseLabel"),
                                "AutoTerminate": cluster.get("AutoTerminate"),
                                "Tags": cluster.get("Tags", []),
                            }
                        )
                    except Exception as detail_error:
                        logger.debug("Error getting EMR cluster details for %s: %s", cluster_id, detail_error)
                        continue

        except Exception as e:
            self._handle_error(e, "EMR clusters")
        return clusters

    def get_kinesis_streams(self) -> List[Dict[str, Any]]:
        """
        Get information about Kinesis Data Streams.

        :return: List of Kinesis stream information
        :rtype: List[Dict[str, Any]]
        """
        streams = []
        try:
            kinesis_client = self._get_client("kinesis")
            paginator = kinesis_client.get_paginator("list_streams")

            for page in paginator.paginate():
                for stream_name in page.get("StreamNames", []):
                    try:
                        stream_detail = kinesis_client.describe_stream(StreamName=stream_name)
                        stream = stream_detail.get("StreamDescription", {})
                        stream_arn = stream.get("StreamARN", "")

                        if not self._matches_account(stream_arn):
                            continue

                        tags_response = kinesis_client.list_tags_for_stream(StreamName=stream_name)
                        stream_tags = tags_response.get("Tags", [])

                        if not self._matches_tags(stream_tags):
                            continue

                        streams.append(
                            {
                                "Region": self.region,
                                "StreamName": stream_name,
                                "StreamARN": stream_arn,
                                "StreamStatus": stream.get("StreamStatus"),
                                "RetentionPeriodHours": stream.get("RetentionPeriodHours"),
                                "StreamCreationTimestamp": stream.get("StreamCreationTimestamp"),
                                "EnhancedMonitoring": stream.get("EnhancedMonitoring", []),
                                "EncryptionType": stream.get("EncryptionType"),
                                "Tags": stream_tags,
                            }
                        )
                    except Exception as stream_error:
                        logger.debug("Error getting Kinesis stream details for %s: %s", stream_name, stream_error)
                        continue

        except Exception as e:
            self._handle_error(e, "Kinesis Data Streams")
        return streams

    def _process_firehose_stream(self, firehose_client: Any, stream_name: str) -> Optional[Dict[str, Any]]:
        """
        Process a single Firehose delivery stream.

        :param firehose_client: Firehose client
        :param str stream_name: Stream name
        :return: Stream information or None if filtered out
        :rtype: Optional[Dict[str, Any]]
        """
        try:
            stream_detail = firehose_client.describe_delivery_stream(DeliveryStreamName=stream_name)
            stream = stream_detail.get("DeliveryStreamDescription", {})
            stream_arn = stream.get("DeliveryStreamARN", "")

            if not self._matches_account(stream_arn):
                return None

            tags_response = firehose_client.list_tags_for_delivery_stream(DeliveryStreamName=stream_name)
            stream_tags = tags_response.get("Tags", [])

            if not self._matches_tags(stream_tags):
                return None

            return {
                "Region": self.region,
                "DeliveryStreamName": stream_name,
                "DeliveryStreamARN": stream_arn,
                "DeliveryStreamStatus": stream.get("DeliveryStreamStatus"),
                "DeliveryStreamType": stream.get("DeliveryStreamType"),
                "VersionId": stream.get("VersionId"),
                "CreateTimestamp": stream.get("CreateTimestamp"),
                "Tags": stream_tags,
            }
        except Exception as stream_error:
            logger.debug("Error getting Firehose stream details for %s: %s", stream_name, stream_error)
            return None

    def get_kinesis_firehose_streams(self) -> List[Dict[str, Any]]:
        """
        Get information about Kinesis Firehose delivery streams.

        :return: List of Kinesis Firehose stream information
        :rtype: List[Dict[str, Any]]
        """
        streams = []
        try:
            firehose_client = self._get_client("firehose")
            has_more = True
            exclusive_start_stream_name = None

            while has_more:
                if exclusive_start_stream_name:
                    response = firehose_client.list_delivery_streams(
                        ExclusiveStartDeliveryStreamName=exclusive_start_stream_name
                    )
                else:
                    response = firehose_client.list_delivery_streams()

                for stream_name in response.get("DeliveryStreamNames", []):
                    stream_info = self._process_firehose_stream(firehose_client, stream_name)
                    if stream_info:
                        streams.append(stream_info)

                has_more = response.get("HasMoreDeliveryStreams", False)
                if has_more and response.get("DeliveryStreamNames"):
                    exclusive_start_stream_name = response["DeliveryStreamNames"][-1]
                else:
                    has_more = False

        except Exception as e:
            self._handle_error(e, "Kinesis Firehose delivery streams")
        return streams

    def get_glue_databases(self) -> List[Dict[str, Any]]:
        """
        Get information about AWS Glue databases.

        :return: List of Glue database information
        :rtype: List[Dict[str, Any]]
        """
        databases = []
        try:
            glue_client = self._get_client("glue")
            paginator = glue_client.get_paginator("get_databases")

            for page in paginator.paginate():
                for database in page.get("DatabaseList", []):
                    database_name = database.get("Name")
                    database_arn = f"arn:aws:glue:{self.region}:{self.account_id or '*'}:database/{database_name}"

                    if not self._matches_account(database_arn):
                        continue

                    try:
                        tags_response = glue_client.get_tags(ResourceArn=database_arn)
                        database_tags = tags_response.get("Tags", {})

                        if not self._matches_tags(database_tags):
                            continue

                        databases.append(
                            {
                                "Region": self.region,
                                "DatabaseName": database_name,
                                "Description": database.get("Description"),
                                "LocationUri": database.get("LocationUri"),
                                "CreateTime": database.get("CreateTime"),
                                "Tags": database_tags,
                            }
                        )
                    except Exception as tag_error:
                        logger.debug("Error getting Glue database tags for %s: %s", database_name, tag_error)
                        continue

        except Exception as e:
            self._handle_error(e, "Glue databases")
        return databases

    def _process_athena_workgroup(self, athena_client: Any, wg_name: str) -> Optional[Dict[str, Any]]:
        """
        Process a single Athena workgroup.

        :param athena_client: Athena client
        :param str wg_name: Workgroup name
        :return: Workgroup information or None if filtered out
        :rtype: Optional[Dict[str, Any]]
        """
        try:
            wg_detail = athena_client.get_work_group(WorkGroup=wg_name)
            workgroup = wg_detail.get("WorkGroup", {})

            wg_arn = f"arn:aws:athena:{self.region}:{self.account_id or '*'}:workgroup/{wg_name}"

            if not self._matches_account(wg_arn):
                return None

            tags_response = athena_client.list_tags_for_resource(ResourceARN=wg_arn)
            wg_tags = tags_response.get("Tags", [])

            if not self._matches_tags(wg_tags):
                return None

            return {
                "Region": self.region,
                "WorkGroupName": wg_name,
                "State": workgroup.get("State"),
                "Description": workgroup.get("Description"),
                "CreationTime": workgroup.get("CreationTime"),
                "Tags": wg_tags,
            }
        except Exception as wg_error:
            logger.debug("Error getting Athena workgroup details for %s: %s", wg_name, wg_error)
            return None

    def get_athena_workgroups(self) -> List[Dict[str, Any]]:
        """
        Get information about Athena workgroups.

        :return: List of Athena workgroup information
        :rtype: List[Dict[str, Any]]
        """
        workgroups = []
        try:
            athena_client = self._get_client("athena")
            next_token = None

            while True:
                if next_token:
                    response = athena_client.list_work_groups(NextToken=next_token)
                else:
                    response = athena_client.list_work_groups()

                for wg_summary in response.get("WorkGroups", []):
                    wg_name = wg_summary.get("Name")
                    wg_info = self._process_athena_workgroup(athena_client, wg_name)
                    if wg_info:
                        workgroups.append(wg_info)

                next_token = response.get("NextToken")
                if not next_token:
                    break

        except Exception as e:
            self._handle_error(e, "Athena workgroups")
        return workgroups

    def get_msk_clusters(self) -> List[Dict[str, Any]]:
        """
        Get information about MSK (Managed Streaming for Kafka) clusters.

        :return: List of MSK cluster information
        :rtype: List[Dict[str, Any]]
        """
        clusters = []
        try:
            msk_client = self._get_client("kafka")
            paginator = msk_client.get_paginator("list_clusters")

            for page in paginator.paginate():
                for cluster_info in page.get("ClusterInfoList", []):
                    cluster_arn = cluster_info.get("ClusterArn", "")

                    if not self._matches_account(cluster_arn):
                        continue

                    if not self._matches_tags(cluster_info.get("Tags", {})):
                        continue

                    clusters.append(
                        {
                            "Region": self.region,
                            "ClusterName": cluster_info.get("ClusterName"),
                            "ClusterArn": cluster_arn,
                            "State": cluster_info.get("State"),
                            "ClusterType": cluster_info.get("ClusterType"),
                            "CurrentVersion": cluster_info.get("CurrentVersion"),
                            "CreationTime": cluster_info.get("CreationTime"),
                            "NumberOfBrokerNodes": cluster_info.get("NumberOfBrokerNodes"),
                            "Tags": cluster_info.get("Tags", {}),
                        }
                    )
        except Exception as e:
            self._handle_error(e, "MSK clusters")
        return clusters

    def collect(self) -> Dict[str, Any]:
        """
        Collect analytics resources based on enabled_services configuration.

        :return: Dictionary containing enabled analytics resource information
        :rtype: Dict[str, Any]
        """
        result = {}

        # EMR Clusters
        if self.enabled_services.get("emr", True):
            result["EMRClusters"] = self.get_emr_clusters()

        # Kinesis Data Streams
        if self.enabled_services.get("kinesis_streams", True):
            result["KinesisStreams"] = self.get_kinesis_streams()

        # Kinesis Firehose
        if self.enabled_services.get("kinesis_firehose", True):
            result["KinesisFirehoseStreams"] = self.get_kinesis_firehose_streams()

        # Glue Databases
        if self.enabled_services.get("glue", True):
            result["GlueDatabases"] = self.get_glue_databases()

        # Athena Workgroups
        if self.enabled_services.get("athena", True):
            result["AthenaWorkgroups"] = self.get_athena_workgroups()

        # MSK Clusters
        if self.enabled_services.get("msk", True):
            result["MSKClusters"] = self.get_msk_clusters()

        return result
