"""AWS database resource collectors."""

from typing import Dict, List, Any, Optional

from ..base import BaseCollector


class DatabaseCollector(BaseCollector):
    """Collector for AWS database resources with filtering support."""

    def __init__(
        self,
        session: Any,
        region: str,
        account_id: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        enabled_services: Optional[Dict[str, bool]] = None,
    ):
        """
        Initialize database collector with filtering support.

        :param session: AWS session to use for API calls
        :param str region: AWS region to collect from
        :param str account_id: Optional AWS account ID to filter resources
        :param dict tags: Optional tag filters (AND logic)
        :param dict enabled_services: Optional dict of service names to boolean flags for enabling/disabling collection
        """
        super().__init__(session, region, account_id, tags)
        self.enabled_services = enabled_services or {}

    def get_rds_instances(self) -> List[Dict[str, Any]]:
        """
        Get information about RDS instances with filtering.

        :return: List of RDS instance information
        :rtype: List[Dict[str, Any]]
        """
        instances = []
        try:
            rds = self._get_client("rds")
            paginator = rds.get_paginator("describe_db_instances")

            for page in paginator.paginate():
                for instance in page.get("DBInstances", []):
                    # Apply tag filtering
                    if self.tags and not self._matches_tags(instance.get("TagList", [])):
                        continue

                    # Apply account filtering using DBInstanceArn
                    instance_arn = instance.get("DBInstanceArn", "")
                    if not self._matches_account(instance_arn):
                        continue

                    instances.append(
                        {
                            "Region": self.region,
                            "DBInstanceIdentifier": instance.get("DBInstanceIdentifier"),
                            "DBInstanceArn": instance.get("DBInstanceArn"),
                            "DBInstanceClass": instance.get("DBInstanceClass"),
                            "Engine": instance.get("Engine"),
                            "EngineVersion": instance.get("EngineVersion"),
                            "DBInstanceStatus": instance.get("DBInstanceStatus"),
                            "Endpoint": instance.get("Endpoint", {}),
                            "AllocatedStorage": instance.get("AllocatedStorage"),
                            "InstanceCreateTime": str(instance.get("InstanceCreateTime")),
                            "VpcId": instance.get("DBSubnetGroup", {}).get("VpcId"),
                            "AvailabilityZone": instance.get("AvailabilityZone"),
                            "MultiAZ": instance.get("MultiAZ"),
                            "PubliclyAccessible": instance.get("PubliclyAccessible"),
                            "StorageEncrypted": instance.get("StorageEncrypted"),
                            "KmsKeyId": instance.get("KmsKeyId"),
                            "Tags": instance.get("TagList", []),
                        }
                    )
        except Exception as e:
            self._handle_error(e, "RDS instances")
        return instances

    def _should_include_table(self, dynamodb, table_arn: str, table_name: str) -> bool:
        """
        Check if table should be included based on account and tag filters.

        :param dynamodb: DynamoDB client
        :param str table_arn: Table ARN
        :param str table_name: Table name
        :return: True if table should be included, False otherwise
        :rtype: bool
        """
        if not self._matches_account(table_arn):
            return False

        if self.tags:
            try:
                tags_response = dynamodb.list_tags_of_resource(ResourceArn=table_arn)
                table_tags = tags_response.get("Tags", [])
                return self._matches_tags(table_tags)
            except Exception as e:
                self._handle_error(e, f"DynamoDB table tags for {table_name}")
                return False

        return True

    def _build_table_data(self, table: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build table data dictionary.

        :param table: Raw table data
        :return: Processed table data
        :rtype: Dict[str, Any]
        """
        return {
            "Region": self.region,
            "TableName": table.get("TableName"),
            "TableStatus": table.get("TableStatus"),
            "CreationDateTime": str(table.get("CreationDateTime")),
            "TableSizeBytes": table.get("TableSizeBytes"),
            "ItemCount": table.get("ItemCount"),
            "TableArn": table.get("TableArn"),
            "ProvisionedThroughput": {
                "ReadCapacityUnits": table.get("ProvisionedThroughput", {}).get("ReadCapacityUnits"),
                "WriteCapacityUnits": table.get("ProvisionedThroughput", {}).get("WriteCapacityUnits"),
            },
            "BillingModeSummary": table.get("BillingModeSummary", {}),
            "GlobalSecondaryIndexes": table.get("GlobalSecondaryIndexes", []),
            "LocalSecondaryIndexes": table.get("LocalSecondaryIndexes", []),
            "StreamSpecification": table.get("StreamSpecification", {}),
            "SSEDescription": table.get("SSEDescription", {}),
        }

    def get_dynamodb_tables(self) -> List[Dict[str, Any]]:
        """
        Get information about DynamoDB tables with filtering.

        :return: List of DynamoDB table information
        :rtype: List[Dict[str, Any]]
        """
        tables = []
        try:
            dynamodb = self._get_client("dynamodb")
            paginator = dynamodb.get_paginator("list_tables")

            for page in paginator.paginate():
                for table_name in page.get("TableNames", []):
                    try:
                        table = dynamodb.describe_table(TableName=table_name)["Table"]
                        table_arn = table.get("TableArn", "")

                        if not self._should_include_table(dynamodb, table_arn, table_name):
                            continue

                        table_data = self._build_table_data(table)
                        tables.append(table_data)
                    except Exception as e:
                        self._handle_error(e, f"DynamoDB table {table_name}")
        except Exception as e:
            self._handle_error(e, "DynamoDB tables")
        return tables

    def get_elasticache_clusters(self) -> List[Dict[str, Any]]:
        """
        Get information about ElastiCache clusters (Redis and Memcached).

        :return: List of ElastiCache cluster information
        :rtype: List[Dict[str, Any]]
        """
        clusters = []
        try:
            elasticache = self._get_client("elasticache")
            paginator = elasticache.get_paginator("describe_cache_clusters")

            for page in paginator.paginate(ShowCacheNodeInfo=True):
                for cluster in page.get("CacheClusters", []):
                    cluster_arn = cluster.get("ARN", "")

                    if not self._matches_account(cluster_arn):
                        continue

                    if not self._matches_tags(cluster.get("Tags", [])):
                        continue

                    clusters.append(
                        {
                            "Region": self.region,
                            "CacheClusterId": cluster.get("CacheClusterId"),
                            "CacheClusterArn": cluster_arn,
                            "Engine": cluster.get("Engine"),
                            "EngineVersion": cluster.get("EngineVersion"),
                            "CacheClusterStatus": cluster.get("CacheClusterStatus"),
                            "CacheNodeType": cluster.get("CacheNodeType"),
                            "NumCacheNodes": cluster.get("NumCacheNodes"),
                            "PreferredAvailabilityZone": cluster.get("PreferredAvailabilityZone"),
                            "CacheClusterCreateTime": cluster.get("CacheClusterCreateTime"),
                            "Tags": cluster.get("Tags", []),
                        }
                    )
        except Exception as e:
            self._handle_error(e, "ElastiCache clusters")
        return clusters

    def get_neptune_clusters(self) -> List[Dict[str, Any]]:
        """
        Get information about Neptune graph database clusters.

        :return: List of Neptune cluster information
        :rtype: List[Dict[str, Any]]
        """
        clusters = []
        try:
            neptune = self._get_client("neptune")
            paginator = neptune.get_paginator("describe_db_clusters")

            for page in paginator.paginate():
                for cluster in page.get("DBClusters", []):
                    cluster_arn = cluster.get("DBClusterArn", "")

                    if not self._matches_account(cluster_arn):
                        continue

                    if not self._matches_tags(cluster.get("TagList", [])):
                        continue

                    clusters.append(
                        {
                            "Region": self.region,
                            "DBClusterIdentifier": cluster.get("DBClusterIdentifier"),
                            "DBClusterArn": cluster_arn,
                            "Engine": cluster.get("Engine"),
                            "EngineVersion": cluster.get("EngineVersion"),
                            "Status": cluster.get("Status"),
                            "Endpoint": cluster.get("Endpoint"),
                            "ReaderEndpoint": cluster.get("ReaderEndpoint"),
                            "MultiAZ": cluster.get("MultiAZ"),
                            "StorageEncrypted": cluster.get("StorageEncrypted"),
                            "KmsKeyId": cluster.get("KmsKeyId"),
                            "Tags": cluster.get("TagList", []),
                        }
                    )
        except Exception as e:
            self._handle_error(e, "Neptune clusters")
        return clusters

    def get_docdb_clusters(self) -> List[Dict[str, Any]]:
        """
        Get information about DocumentDB clusters.

        :return: List of DocumentDB cluster information
        :rtype: List[Dict[str, Any]]
        """
        clusters = []
        try:
            docdb = self._get_client("docdb")
            paginator = docdb.get_paginator("describe_db_clusters")

            for page in paginator.paginate():
                for cluster in page.get("DBClusters", []):
                    cluster_arn = cluster.get("DBClusterArn", "")

                    if not self._matches_account(cluster_arn):
                        continue

                    if not self._matches_tags(cluster.get("TagList", [])):
                        continue

                    clusters.append(
                        {
                            "Region": self.region,
                            "DBClusterIdentifier": cluster.get("DBClusterIdentifier"),
                            "DBClusterArn": cluster_arn,
                            "Engine": cluster.get("Engine"),
                            "EngineVersion": cluster.get("EngineVersion"),
                            "Status": cluster.get("Status"),
                            "Endpoint": cluster.get("Endpoint"),
                            "ReaderEndpoint": cluster.get("ReaderEndpoint"),
                            "MultiAZ": cluster.get("MultiAZ"),
                            "StorageEncrypted": cluster.get("StorageEncrypted"),
                            "KmsKeyId": cluster.get("KmsKeyId"),
                            "Tags": cluster.get("TagList", []),
                        }
                    )
        except Exception as e:
            self._handle_error(e, "DocumentDB clusters")
        return clusters

    def get_redshift_clusters(self) -> List[Dict[str, Any]]:
        """
        Get information about Redshift data warehouse clusters.

        :return: List of Redshift cluster information
        :rtype: List[Dict[str, Any]]
        """
        clusters = []
        try:
            redshift = self._get_client("redshift")
            paginator = redshift.get_paginator("describe_clusters")

            for page in paginator.paginate():
                for cluster in page.get("Clusters", []):
                    cluster_arn = (
                        f"arn:aws:redshift:{self.region}:{cluster.get('ClusterNamespaceArn', '').split(':')[4]}:"
                        f"cluster:{cluster.get('ClusterIdentifier')}"
                    )

                    if not self._matches_account(cluster_arn):
                        continue

                    if not self._matches_tags(cluster.get("Tags", [])):
                        continue

                    clusters.append(
                        {
                            "Region": self.region,
                            "ClusterIdentifier": cluster.get("ClusterIdentifier"),
                            "ClusterStatus": cluster.get("ClusterStatus"),
                            "NodeType": cluster.get("NodeType"),
                            "NumberOfNodes": cluster.get("NumberOfNodes"),
                            "DBName": cluster.get("DBName"),
                            "Endpoint": cluster.get("Endpoint"),
                            "ClusterCreateTime": cluster.get("ClusterCreateTime"),
                            "Encrypted": cluster.get("Encrypted"),
                            "KmsKeyId": cluster.get("KmsKeyId"),
                            "VpcId": cluster.get("VpcId"),
                            "PubliclyAccessible": cluster.get("PubliclyAccessible"),
                            "Tags": cluster.get("Tags", []),
                        }
                    )
        except Exception as e:
            self._handle_error(e, "Redshift clusters")
        return clusters

    def get_keyspaces(self) -> List[Dict[str, Any]]:
        """
        Get information about Keyspaces (Apache Cassandra) keyspaces and tables.

        :return: List of Keyspaces keyspace information
        :rtype: List[Dict[str, Any]]
        """
        keyspaces = []
        try:
            keyspaces_client = self._get_client("keyspaces")
            paginator = keyspaces_client.get_paginator("list_keyspaces")

            for page in paginator.paginate():
                for keyspace in page.get("keyspaces", []):
                    keyspace_name = keyspace.get("keyspaceName")
                    keyspace_arn = keyspace.get("resourceArn", "")

                    if not self._matches_account(keyspace_arn):
                        continue

                    try:
                        tags_response = keyspaces_client.list_tags_for_resource(resourceArn=keyspace_arn)
                        keyspace_tags = tags_response.get("tags", [])

                        if not self._matches_tags(keyspace_tags):
                            continue

                        keyspaces.append(
                            {
                                "Region": self.region,
                                "KeyspaceName": keyspace_name,
                                "KeyspaceArn": keyspace_arn,
                                "Tags": keyspace_tags,
                            }
                        )
                    except Exception as tag_error:
                        self._handle_error(tag_error, f"Keyspaces tags for {keyspace_name}")
                        continue

        except Exception as e:
            self._handle_error(e, "Keyspaces")
        return keyspaces

    def _process_timestream_database(self, timestream: Any, database: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process a single Timestream database.

        :param timestream: Timestream client
        :param dict database: Database information
        :return: Database information or None if filtered out
        :rtype: Optional[Dict[str, Any]]
        """
        database_arn = database.get("Arn", "")

        if not self._matches_account(database_arn):
            return None

        try:
            tags_response = timestream.list_tags_for_resource(ResourceARN=database_arn)
            db_tags = tags_response.get("Tags", [])

            if not self._matches_tags(db_tags):
                return None

            return {
                "Region": self.region,
                "DatabaseName": database.get("DatabaseName"),
                "DatabaseArn": database_arn,
                "TableCount": database.get("TableCount"),
                "KmsKeyId": database.get("KmsKeyId"),
                "CreationTime": database.get("CreationTime"),
                "Tags": db_tags,
            }
        except Exception as tag_error:
            self._handle_error(tag_error, f"Timestream database tags for {database_arn}")
            return None

    def get_timestream_databases(self) -> List[Dict[str, Any]]:
        """
        Get information about Timestream databases.

        :return: List of Timestream database information
        :rtype: List[Dict[str, Any]]
        """
        databases = []
        try:
            timestream = self._get_client("timestream-write")
            next_token = None

            while True:
                if next_token:
                    response = timestream.list_databases(NextToken=next_token)
                else:
                    response = timestream.list_databases()

                for database in response.get("Databases", []):
                    db_info = self._process_timestream_database(timestream, database)
                    if db_info:
                        databases.append(db_info)

                next_token = response.get("NextToken")
                if not next_token:
                    break

        except Exception as e:
            self._handle_error(e, "Timestream databases")
        return databases

    def _process_qldb_ledger(self, qldb: Any, ledger_name: str) -> Optional[Dict[str, Any]]:
        """
        Process a single QLDB ledger.

        :param qldb: QLDB client
        :param str ledger_name: Ledger name
        :return: Ledger information or None if filtered out
        :rtype: Optional[Dict[str, Any]]
        """
        try:
            ledger_details = qldb.describe_ledger(Name=ledger_name)
            ledger_arn = ledger_details.get("Arn", "")

            if not self._matches_account(ledger_arn):
                return None

            tags_response = qldb.list_tags_for_resource(ResourceArn=ledger_arn)
            ledger_tags = tags_response.get("Tags", {})

            if not self._matches_tags(ledger_tags):
                return None

            return {
                "Region": self.region,
                "Name": ledger_name,
                "Arn": ledger_arn,
                "State": ledger_details.get("State"),
                "CreationDateTime": ledger_details.get("CreationDateTime"),
                "PermissionsMode": ledger_details.get("PermissionsMode"),
                "DeletionProtection": ledger_details.get("DeletionProtection"),
                "Tags": ledger_tags,
            }
        except Exception as ledger_error:
            self._handle_error(ledger_error, f"QLDB ledger details for {ledger_name}")
            return None

    def get_qldb_ledgers(self) -> List[Dict[str, Any]]:
        """
        Get information about QLDB (Quantum Ledger Database) ledgers.

        :return: List of QLDB ledger information
        :rtype: List[Dict[str, Any]]
        """
        ledgers = []
        try:
            qldb = self._get_client("qldb")
            next_token = None

            while True:
                if next_token:
                    response = qldb.list_ledgers(NextToken=next_token)
                else:
                    response = qldb.list_ledgers()

                for ledger in response.get("Ledgers", []):
                    ledger_name = ledger.get("Name")
                    ledger_info = self._process_qldb_ledger(qldb, ledger_name)
                    if ledger_info:
                        ledgers.append(ledger_info)

                next_token = response.get("NextToken")
                if not next_token:
                    break

        except Exception as e:
            self._handle_error(e, "QLDB ledgers")
        return ledgers

    def collect(self) -> Dict[str, Any]:
        """
        Collect database resources based on enabled_services configuration.

        :return: Dictionary containing enabled database resource information
        :rtype: Dict[str, Any]
        """
        result = {}

        # RDS Instances
        if self.enabled_services.get("rds", True):
            result["RDSInstances"] = self.get_rds_instances()

        # DynamoDB Tables
        if self.enabled_services.get("dynamodb", True):
            result["DynamoDBTables"] = self.get_dynamodb_tables()

        # ElastiCache Clusters
        if self.enabled_services.get("elasticache", True):
            result["ElastiCacheClusters"] = self.get_elasticache_clusters()

        # Neptune Clusters
        if self.enabled_services.get("neptune", True):
            result["NeptuneClusters"] = self.get_neptune_clusters()

        # DocumentDB Clusters
        if self.enabled_services.get("docdb", True):
            result["DocumentDBClusters"] = self.get_docdb_clusters()

        # Redshift Clusters
        if self.enabled_services.get("redshift", True):
            result["RedshiftClusters"] = self.get_redshift_clusters()

        # Keyspaces
        if self.enabled_services.get("keyspaces", True):
            result["Keyspaces"] = self.get_keyspaces()

        # Timestream Databases
        if self.enabled_services.get("timestream", True):
            result["TimestreamDatabases"] = self.get_timestream_databases()

        # QLDB Ledgers
        if self.enabled_services.get("qldb", True):
            result["QLDBLedgers"] = self.get_qldb_ledgers()

        return result
