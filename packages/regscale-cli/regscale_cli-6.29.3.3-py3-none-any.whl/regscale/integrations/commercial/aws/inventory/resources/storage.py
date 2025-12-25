"""AWS storage resource collectors."""

from typing import Dict, List, Any, Optional

from regscale.integrations.commercial.aws.inventory.resources.s3 import S3Collector
from ..base import BaseCollector


class StorageCollector(BaseCollector):
    """Collector for AWS storage resources with filtering support."""

    def __init__(
        self,
        session: Any,
        region: str,
        account_id: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        enabled_services: Optional[Dict[str, bool]] = None,
    ):
        """
        Initialize storage collector with filtering support.

        :param session: AWS session to use for API calls
        :param str region: AWS region to collect from
        :param str account_id: Optional AWS account ID to filter resources
        :param dict tags: Optional tag filters (AND logic)
        :param dict enabled_services: Optional dict of service names to boolean flags for enabling/disabling collection
        """
        super().__init__(session, region, account_id, tags)
        self.enabled_services = enabled_services or {}

    def get_s3_buckets(self) -> List[Dict[str, Any]]:
        """
        Get information about S3 buckets with filtering.

        :return: List of S3 bucket information
        :rtype: List[Dict[str, Any]]
        """
        try:
            s3_collector = S3Collector(self.session, self.region, self.account_id, self.tags)
            result = s3_collector.collect()
            return result.get("Buckets", [])
        except Exception as e:
            self._handle_error(e, "S3 buckets")
            return []

    def get_ebs_volumes(self) -> List[Dict[str, Any]]:
        """
        Get information about EBS volumes with tag filtering.

        :return: List of EBS volume information
        :rtype: List[Dict[str, Any]]
        """
        volumes = []
        try:
            ec2 = self._get_client("ec2")
            paginator = ec2.get_paginator("describe_volumes")

            for page in paginator.paginate():
                for volume in page.get("Volumes", []):
                    # Apply tag filtering
                    if self.tags and not self._matches_tags(volume.get("Tags", [])):
                        continue

                    # Apply account filtering if ARN available
                    volume_arn = (
                        f"arn:aws:ec2:{self.region}:{volume.get('OwnerId', 'unknown')}:volume/{volume.get('VolumeId')}"
                    )
                    if not self._matches_account(volume_arn):
                        continue

                    attachments = volume.get("Attachments", [])
                    volumes.append(
                        {
                            "Region": self.region,
                            "VolumeId": volume.get("VolumeId"),
                            "Size": volume.get("Size"),
                            "VolumeType": volume.get("VolumeType"),
                            "State": volume.get("State"),
                            "CreateTime": str(volume.get("CreateTime")),
                            "Encrypted": volume.get("Encrypted"),
                            "KmsKeyId": volume.get("KmsKeyId"),
                            "Attachments": [
                                {
                                    "InstanceId": att.get("InstanceId"),
                                    "State": att.get("State"),
                                    "Device": att.get("Device"),
                                }
                                for att in attachments
                            ],
                            "Tags": volume.get("Tags", []),
                        }
                    )
        except Exception as e:
            self._handle_error(e, "EBS volumes")
        return volumes

    def get_efs_file_systems(self) -> List[Dict[str, Any]]:
        """
        Get information about EFS file systems.

        :return: List of EFS file system information
        :rtype: List[Dict[str, Any]]
        """
        file_systems = []
        try:
            efs_client = self._get_client("efs")
            paginator = efs_client.get_paginator("describe_file_systems")

            for page in paginator.paginate():
                for fs in page.get("FileSystems", []):
                    fs_arn = fs.get("FileSystemArn", "")

                    if not self._matches_account(fs_arn):
                        continue

                    if not self._matches_tags(fs.get("Tags", [])):
                        continue

                    file_systems.append(
                        {
                            "Region": self.region,
                            "FileSystemId": fs.get("FileSystemId"),
                            "FileSystemArn": fs_arn,
                            "Name": fs.get("Name"),
                            "CreationTime": fs.get("CreationTime"),
                            "LifeCycleState": fs.get("LifeCycleState"),
                            "SizeInBytes": fs.get("SizeInBytes"),
                            "PerformanceMode": fs.get("PerformanceMode"),
                            "ThroughputMode": fs.get("ThroughputMode"),
                            "Encrypted": fs.get("Encrypted"),
                            "KmsKeyId": fs.get("KmsKeyId"),
                            "Tags": fs.get("Tags", []),
                        }
                    )
        except Exception as e:
            self._handle_error(e, "EFS file systems")
        return file_systems

    def get_fsx_file_systems(self) -> List[Dict[str, Any]]:
        """
        Get information about FSx file systems (Windows, Lustre, NetApp ONTAP, OpenZFS).

        :return: List of FSx file system information
        :rtype: List[Dict[str, Any]]
        """
        file_systems = []
        try:
            fsx_client = self._get_client("fsx")
            paginator = fsx_client.get_paginator("describe_file_systems")

            for page in paginator.paginate():
                for fs in page.get("FileSystems", []):
                    fs_arn = fs.get("ResourceARN", "")

                    if not self._matches_account(fs_arn):
                        continue

                    if not self._matches_tags(fs.get("Tags", [])):
                        continue

                    file_systems.append(
                        {
                            "Region": self.region,
                            "FileSystemId": fs.get("FileSystemId"),
                            "FileSystemArn": fs_arn,
                            "FileSystemType": fs.get("FileSystemType"),
                            "Lifecycle": fs.get("Lifecycle"),
                            "StorageCapacity": fs.get("StorageCapacity"),
                            "StorageType": fs.get("StorageType"),
                            "VpcId": fs.get("VpcId"),
                            "SubnetIds": fs.get("SubnetIds", []),
                            "CreationTime": fs.get("CreationTime"),
                            "Tags": fs.get("Tags", []),
                        }
                    )
        except Exception as e:
            self._handle_error(e, "FSx file systems")
        return file_systems

    def get_storage_gateways(self) -> List[Dict[str, Any]]:
        """
        Get information about Storage Gateway gateways.

        :return: List of Storage Gateway information
        :rtype: List[Dict[str, Any]]
        """
        gateways = []
        try:
            sg_client = self._get_client("storagegateway")
            paginator = sg_client.get_paginator("list_gateways")

            for page in paginator.paginate():
                for gateway in page.get("Gateways", []):
                    gateway_arn = gateway.get("GatewayARN", "")

                    if not self._matches_account(gateway_arn):
                        continue

                    try:
                        tags_response = sg_client.list_tags_for_resource(ResourceARN=gateway_arn)
                        gateway_tags = tags_response.get("Tags", [])

                        if not self._matches_tags(gateway_tags):
                            continue

                        gateways.append(
                            {
                                "Region": self.region,
                                "GatewayId": gateway.get("GatewayId"),
                                "GatewayARN": gateway_arn,
                                "GatewayName": gateway.get("GatewayName"),
                                "GatewayType": gateway.get("GatewayType"),
                                "GatewayOperationalState": gateway.get("GatewayOperationalState"),
                                "Tags": gateway_tags,
                            }
                        )
                    except Exception as tag_error:
                        self._handle_error(tag_error, f"Storage Gateway tags for {gateway_arn}")
                        continue

        except Exception as e:
            self._handle_error(e, "Storage Gateways")
        return gateways

    def get_backup_vaults(self) -> List[Dict[str, Any]]:
        """
        Get information about AWS Backup vaults.

        :return: List of Backup vault information
        :rtype: List[Dict[str, Any]]
        """
        vaults = []
        try:
            backup_client = self._get_client("backup")
            paginator = backup_client.get_paginator("list_backup_vaults")

            for page in paginator.paginate():
                for vault in page.get("BackupVaultList", []):
                    vault_arn = vault.get("BackupVaultArn", "")

                    if not self._matches_account(vault_arn):
                        continue

                    try:
                        tags_response = backup_client.list_tags(ResourceArn=vault_arn)
                        vault_tags = tags_response.get("Tags", {})

                        if not self._matches_tags(vault_tags):
                            continue

                        vaults.append(
                            {
                                "Region": self.region,
                                "BackupVaultName": vault.get("BackupVaultName"),
                                "BackupVaultArn": vault_arn,
                                "CreationDate": vault.get("CreationDate"),
                                "EncryptionKeyArn": vault.get("EncryptionKeyArn"),
                                "NumberOfRecoveryPoints": vault.get("NumberOfRecoveryPoints"),
                                "Tags": vault_tags,
                            }
                        )
                    except Exception as tag_error:
                        self._handle_error(tag_error, f"Backup vault tags for {vault_arn}")
                        continue

        except Exception as e:
            self._handle_error(e, "Backup vaults")
        return vaults

    def get_backup_plans(self) -> List[Dict[str, Any]]:
        """
        Get information about AWS Backup plans.

        :return: List of Backup plan information
        :rtype: List[Dict[str, Any]]
        """
        plans = []
        try:
            backup_client = self._get_client("backup")
            paginator = backup_client.get_paginator("list_backup_plans")

            for page in paginator.paginate():
                for plan in page.get("BackupPlansList", []):
                    plan_arn = plan.get("BackupPlanArn", "")

                    if not self._matches_account(plan_arn):
                        continue

                    try:
                        tags_response = backup_client.list_tags(ResourceArn=plan_arn)
                        plan_tags = tags_response.get("Tags", {})

                        if not self._matches_tags(plan_tags):
                            continue

                        plans.append(
                            {
                                "Region": self.region,
                                "BackupPlanId": plan.get("BackupPlanId"),
                                "BackupPlanArn": plan_arn,
                                "BackupPlanName": plan.get("BackupPlanName"),
                                "CreationDate": plan.get("CreationDate"),
                                "VersionId": plan.get("VersionId"),
                                "Tags": plan_tags,
                            }
                        )
                    except Exception as tag_error:
                        self._handle_error(tag_error, f"Backup plan tags for {plan_arn}")
                        continue

        except Exception as e:
            self._handle_error(e, "Backup plans")
        return plans

    def collect(self) -> Dict[str, Any]:
        """
        Collect storage resources based on enabled_services configuration.

        :return: Dictionary containing enabled storage resource information
        :rtype: Dict[str, Any]
        """
        result = {}

        # S3 Buckets
        if self.enabled_services.get("s3", True):
            result["S3Buckets"] = self.get_s3_buckets()

        # EBS Volumes
        if self.enabled_services.get("ebs", True):
            result["EBSVolumes"] = self.get_ebs_volumes()

        # EFS File Systems
        if self.enabled_services.get("efs", True):
            result["EFSFileSystems"] = self.get_efs_file_systems()

        # FSx File Systems
        if self.enabled_services.get("fsx", True):
            result["FSxFileSystems"] = self.get_fsx_file_systems()

        # Storage Gateway
        if self.enabled_services.get("storage_gateway", True):
            result["StorageGateways"] = self.get_storage_gateways()

        # AWS Backup
        if self.enabled_services.get("backup", True):
            result["BackupVaults"] = self.get_backup_vaults()
            result["BackupPlans"] = self.get_backup_plans()

        return result
