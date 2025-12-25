"""Module for AWS resource inventory scanning integration."""

import json
import logging
import os
import time
from typing import Any, Dict, Iterator, List, Optional, Tuple

from regscale.core.utils.date import date_str, datetime_str
from regscale.integrations.commercial.aws.common import (
    check_finding_severity,
    determine_status_and_results,
    fetch_aws_findings,
    get_comments,
    get_due_date,
)
from regscale.integrations.scanner_integration import (
    IntegrationAsset,
    IntegrationFinding,
    ScannerIntegration,
    ScannerIntegrationType,
)
from regscale.models import IssueStatus, regscale_models
from .inventory import AWSInventoryCollector

logger = logging.getLogger("regscale")

# Constants for file paths:
INVENTORY_FILE_PATH = os.path.join("artifacts", "aws", "inventory.json")
FINDINGS_FILE_PATH = os.path.join("artifacts", "aws", "findings.json")
CACHE_TTL_SECONDS = 8 * 60 * 60  # 8 hours in seconds
EC_INSTANCES = "EC2 Instances"


class AWSInventoryIntegration(ScannerIntegration):
    """Integration class for AWS resource inventory scanning."""

    title = "AWS"
    asset_identifier_field = "awsIdentifier"
    issue_identifier_field = ""  # Use default otherIdentifier - awsIdentifier doesn't exist on Issue model
    suppress_asset_not_found_errors = True  # Suppress asset not found errors for AWS findings
    enable_cci_mapping = False  # AWS findings don't use CCI references
    finding_severity_map = {
        "CRITICAL": regscale_models.IssueSeverity.High,
        "HIGH": regscale_models.IssueSeverity.High,
        "MEDIUM": regscale_models.IssueSeverity.Moderate,
        "LOW": regscale_models.IssueSeverity.Low,
        "INFORMATIONAL": regscale_models.IssueSeverity.NotAssigned,
    }
    checklist_status_map = {
        "Pass": regscale_models.ChecklistStatus.PASS,
        "Fail": regscale_models.ChecklistStatus.FAIL,
    }
    type = ScannerIntegrationType.CHECKLIST

    def __init__(self, plan_id: int, **kwargs):
        """
        Initialize the AWS inventory integration.

        :param int plan_id: The RegScale plan ID
        """
        super().__init__(plan_id=plan_id, kwargs=kwargs)
        # Override parent's default - suppress asset not found errors for AWS
        self.suppress_asset_not_found_errors = True
        self.collector: Optional[AWSInventoryCollector] = None
        self.discovered_assets: List[IntegrationAsset] = []
        self.processed_asset_identifiers: set = set()  # Track processed assets to avoid duplicates
        self.finding_progress = None  # Initialize progress object as None

    def authenticate(
        self,
        aws_access_key_id: Optional[str],
        aws_secret_access_key: Optional[str],
        region: str = os.getenv("AWS_REGION", "us-east-1"),
        aws_session_token: Optional[str] = os.getenv("AWS_SESSION_TOKEN"),
        profile: Optional[str] = None,
        account_id: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Authenticate with AWS and initialize the inventory collector.

        :param str aws_access_key_id: Optional AWS access key ID (overrides profile)
        :param str aws_secret_access_key: Optional AWS secret access key (overrides profile)
        :param str region: AWS region to collect inventory from
        :param str aws_session_token: Optional AWS session token (overrides profile)
        :param str profile: Optional AWS profile name from ~/.aws/credentials
        :param str account_id: Optional AWS account ID to filter resources
        :param dict tags: Optional dictionary of tag key-value pairs to filter resources
        """
        self.collector = AWSInventoryCollector(
            region=region,
            profile=profile,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token,
            account_id=account_id,
            tags=tags,
            collect_findings=False,  # Disable findings collection for asset-only sync
        )

    def _get_aws_config(self, key: str, default=None):
        """
        Get AWS configuration value with backward compatibility.
        Checks 'aws' first, falls back to 'amazon' for legacy configs.

        :param str key: Configuration key to retrieve
        :param default: Default value if key not found
        :return: Configuration value or default
        """
        issues_config = self.app.config.get("issues", {})
        # Try new 'aws' key first
        if "aws" in issues_config and key in issues_config["aws"]:
            return issues_config["aws"][key]
        # Fall back to legacy 'amazon' key
        if "amazon" in issues_config and key in issues_config["amazon"]:
            return issues_config["amazon"][key]
        # Return default if neither exists
        return default

    def _get_default_days(self, severity: str) -> int:
        """
        Get default SLA days for a severity level.

        :param str severity: Severity level
        :return: Default number of days
        :rtype: int
        """
        defaults = {"critical": 30, "high": 60, "moderate": 120, "low": 364}
        return defaults.get(severity.lower(), 364)

    def fetch_aws_data_if_needed(
        self,
        region: str,
        aws_access_key_id: Optional[str],
        aws_secret_access_key: Optional[str],
        aws_session_token: Optional[str] = None,
        profile: Optional[str] = None,
        account_id: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        force_refresh: bool = False,
    ) -> Dict[str, Any]:
        """
        Fetch AWS inventory data, using cached data if available and not expired.

        :param str region: AWS region to collect inventory from
        :param str aws_access_key_id: Optional AWS access key ID (overrides profile)
        :param str aws_secret_access_key: Optional AWS secret access key (overrides profile)
        :param str aws_session_token: Optional AWS session token (overrides profile)
        :param str profile: Optional AWS profile name from ~/.aws/credentials
        :param str account_id: Optional AWS account ID to filter resources
        :param dict tags: Optional dictionary of tag key-value pairs to filter resources
        :param bool force_refresh: Force refresh inventory data, ignoring cache
        :return: Dictionary containing AWS inventory data
        :rtype: Dict[str, Any]
        """
        from regscale.models import DateTimeEncoder

        # Check if we have cached data that's still valid (unless force_refresh is True)
        if not force_refresh and os.path.exists(INVENTORY_FILE_PATH):
            file_age = time.time() - os.path.getmtime(INVENTORY_FILE_PATH)
            if file_age < CACHE_TTL_SECONDS:
                logger.info(f"Using cached AWS inventory data (age: {int(file_age / 60)} minutes)")
                with open(INVENTORY_FILE_PATH, "r", encoding="utf-8") as file:
                    return json.load(file)

        if force_refresh and os.path.exists(INVENTORY_FILE_PATH):
            logger.info("Force refresh enabled - ignoring cached inventory data")

        # No valid cache, need to fetch new data
        if not self.collector:
            self.authenticate(
                aws_access_key_id, aws_secret_access_key, region, aws_session_token, profile, account_id, tags
            )

        if not self.collector:
            raise RuntimeError("Failed to initialize AWS inventory collector")

        inventory = self.collector.collect_all()

        # Ensure the artifacts directory exists
        os.makedirs(os.path.dirname(INVENTORY_FILE_PATH), exist_ok=True)

        with open(INVENTORY_FILE_PATH, "w", encoding="utf-8") as file:
            json.dump(inventory, file, cls=DateTimeEncoder, indent=2)

        return inventory

    def _process_asset_collection(
        self, assets: List[Dict[str, Any]], asset_type: str, parser_method
    ) -> Iterator[IntegrationAsset]:
        """
        Process a collection of assets using the specified parser method.

        :param List[Dict[str, Any]] assets: List of assets to process
        :param str asset_type: Type of asset being processed
        :param callable parser_method: Method to parse the asset
        :yield: Iterator[IntegrationAsset]
        """
        for asset in assets:
            if not isinstance(asset, dict):
                logger.warning(f"Skipping {asset_type} due to invalid data format: {asset}")
                continue
            try:
                yield parser_method(asset)
            except Exception as e:
                logger.error(f"Error parsing {asset_type} {asset}: {str(e)}", exc_info=True)

    def _process_inventory_section(
        self, inventory: Dict[str, Any], section_key: str, asset_type: str, parser_method
    ) -> Iterator[IntegrationAsset]:
        """
        Process a section of the inventory.

        :param Dict[str, Any] inventory: The complete inventory data
        :param str section_key: Key for the section in the inventory
        :param str asset_type: Type of asset being processed
        :param callable parser_method: Method to parse the asset
        :yield: Iterator[IntegrationAsset]
        """
        section_data = inventory.get(section_key, [])

        # Handle special case for IAM - need to extract Roles list from IAM dict
        if section_key == "IAM" and isinstance(section_data, dict):
            assets = section_data.get(asset_type, [])
        else:
            assets = section_data

        yield from self._process_asset_collection(assets, asset_type, parser_method)

    def get_asset_configs(self) -> List[Tuple[str, str, callable]]:
        """
        Get the asset configurations for parsing.

        :return: List of asset configurations
        :rtype: List[Tuple[str, str, callable]]
        """
        return [
            ("IAM", "Roles", self.parse_aws_account),
            ("EC2Instances", "EC2 instance", self.parse_ec2_instance),
            ("LambdaFunctions", "Lambda function", self.parse_lambda_function),
            ("S3Buckets", "S3 bucket", self.parse_s3_bucket),
            ("RDSInstances", "RDS instance", self.parse_rds_instance),
            ("DynamoDBTables", "DynamoDB table", self.parse_dynamodb_table),
            ("VPCs", "VPC", self.parse_vpc),
            ("LoadBalancers", "Load Balancer", self.parse_load_balancer),
            ("ECRRepositories", "ECR repository", self.parse_ecr_repository),
        ]

    def fetch_assets(
        self,
        region: str,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        aws_session_token: Optional[str] = None,
        profile: Optional[str] = None,
        account_id: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        force_refresh: bool = False,
    ) -> Iterator[IntegrationAsset]:
        """
        Fetch AWS assets from the inventory.

        :param str region: AWS region to collect inventory from
        :param str aws_access_key_id: Optional AWS access key ID (overrides profile)
        :param str aws_secret_access_key: Optional AWS secret access key (overrides profile)
        :param str aws_session_token: Optional AWS session token (overrides profile)
        :param str profile: Optional AWS profile name from ~/.aws/credentials
        :param str account_id: Optional AWS account ID to filter resources
        :param dict tags: Optional dictionary of tag key-value pairs to filter resources
        :param bool force_refresh: Force refresh inventory data, ignoring cache
        :yield: Iterator[IntegrationAsset]
        """
        inventory = self.fetch_aws_data_if_needed(
            region,
            aws_access_key_id,
            aws_secret_access_key,
            aws_session_token,
            profile,
            account_id,
            tags,
            force_refresh,
        )
        # Process each asset type using the corresponding parser
        asset_configs = self.get_asset_configs()

        self.num_assets_to_process = 0

        for section_key, asset_type, parser_method in asset_configs:
            yield from self._process_inventory_section(inventory, section_key, asset_type, parser_method)

    def _calculate_ec2_storage(self, instance: Dict[str, Any]) -> int:
        """
        Calculate total storage from EC2 block devices.

        :param Dict[str, Any] instance: The EC2 instance data
        :return: Total storage in GB
        :rtype: int
        """
        total_storage = 0
        for device in instance.get("BlockDeviceMappings", []):
            if "Ebs" in device:
                # Note: We need to add a call to describe_volumes to get actual size
                total_storage += 8  # Default to 8 GB if size unknown
        return total_storage

    def _determine_ec2_asset_type(
        self, image_name: str, platform: Optional[str]
    ) -> tuple[Any, Any, Any, Any, list[str]]:
        """
        Determine EC2 asset type, category, component type, and names based on image and platform.

        :param str image_name: Lowercase image name
        :param Optional[str] platform: Platform type (e.g., 'windows')
        :return: Tuple of (operating_system, asset_type, asset_category, component_type, component_names)
        :rtype: tuple
        """
        # Check for Palo Alto device first
        if "pa-vm-aws" in image_name:
            return (
                regscale_models.AssetOperatingSystem.PaloAlto,
                regscale_models.AssetType.Appliance,
                regscale_models.AssetCategory.Hardware,
                regscale_models.ComponentType.Hardware,
                ["Palo Alto Networks IDPS"],
            )

        # Check for Windows platform
        if platform == "windows":
            return (
                regscale_models.AssetOperatingSystem.WindowsServer,
                regscale_models.AssetType.VM,
                regscale_models.AssetCategory.Hardware,
                regscale_models.ComponentType.Hardware,
                [EC_INSTANCES],
            )

        # Default to Linux
        return (
            regscale_models.AssetOperatingSystem.Linux,
            regscale_models.AssetType.VM,
            regscale_models.AssetCategory.Hardware,
            regscale_models.ComponentType.Hardware,
            [EC_INSTANCES],
        )

    def _build_ec2_notes(
        self, description: str, instance: Dict[str, Any], image_info: Dict[str, Any], cpu_count: int, ram: int
    ) -> str:
        """
        Build detailed notes for EC2 instance.

        :param str description: Instance description
        :param Dict[str, Any] instance: The EC2 instance data
        :param Dict[str, Any] image_info: AMI image information
        :param int cpu_count: Number of vCPUs
        :param int ram: RAM in GB
        :return: Formatted notes string
        :rtype: str
        """
        return f"""Description: {description}
AMI ID: {instance.get('ImageId', '')}
AMI Description: {image_info.get('Description', '')}
Architecture: {instance.get('Architecture', '')}
Root Device Type: {image_info.get('RootDeviceType', '')}
Virtualization: {image_info.get('VirtualizationType', '')}
Instance Type: {instance.get('InstanceType', '')}
vCPUs: {cpu_count}
RAM: {ram}GB
State: {instance.get('State')}
Platform Details: {instance.get('PlatformDetails', 'Linux')}
Private IP: {instance.get('PrivateIpAddress', 'N/A')}
Public IP: {instance.get('PublicIpAddress', 'N/A')}
VPC ID: {instance.get('VpcId', 'N/A')}
Subnet ID: {instance.get('SubnetId', 'N/A')}"""

    def parse_ec2_instance(self, instance: Dict[str, Any]) -> IntegrationAsset:
        """Parse EC2 instance data into an IntegrationAsset.

        :param Dict[str, Any] instance: The EC2 instance data
        :return: The parsed IntegrationAsset
        :rtype: IntegrationAsset
        """
        # Get instance name from tags
        instance_name = next(
            (tag["Value"] for tag in instance.get("Tags", []) if tag["Key"] == "Name"), instance.get("InstanceId", "")
        )
        name = instance_name

        # Calculate resources
        total_storage = self._calculate_ec2_storage(instance)
        ram = 16  # Default to 16 GB for c5.2xlarge

        # Get CPU info
        cpu_options = instance.get("CpuOptions", {})
        cpu_count = int(cpu_options.get("CoreCount", 0) * cpu_options.get("ThreadsPerCore", 0))

        # Determine if instance is public facing
        is_public_facing = bool(instance.get("PublicIpAddress"))

        # Get OS details from platform and image info
        image_info = instance.get("ImageInfo", {})
        image_name = image_info.get("Name", "").lower()

        # Determine asset type and OS
        operating_system, asset_type, asset_category, component_type, component_names = self._determine_ec2_asset_type(
            image_name, instance.get("Platform")
        )

        os_version = image_info.get("Description", "")

        # Get FQDN - use public DNS name, private DNS name, or instance name
        fqdn = (
            instance.get("PublicDnsName")
            or instance.get("PrivateDnsName")
            or instance_name
            or instance.get("InstanceId", "")
        )

        # Create description
        description = f"{instance_name} - {instance.get('PlatformDetails', 'Linux')} instance running on {instance.get('InstanceType', '')} with {cpu_count} vCPUs and {ram}GB RAM"

        # Build notes
        notes = self._build_ec2_notes(description, instance, image_info, cpu_count, ram)

        # Build full ARN for EC2 instance: arn:aws:ec2:region:account-id:instance/instance-id
        instance_id = instance.get("InstanceId", "")
        region = instance.get("Region", "us-east-1")
        account_id = instance.get("OwnerId", "")
        instance_arn = f"arn:aws:ec2:{region}:{account_id}:instance/{instance_id}"

        # Create URI for AWS Console link
        uri = f"https://console.aws.amazon.com/ec2/v2/home?region={region}#InstanceDetails:instanceId={instance_id}"

        return IntegrationAsset(
            name=name,
            identifier=instance_arn,
            asset_type=asset_type,
            asset_category=asset_category,
            component_type=component_type,
            component_names=component_names,
            parent_id=self.plan_id,
            parent_module="securityplans",
            status=(
                regscale_models.AssetStatus.Active
                if instance.get("State") == "running"
                else regscale_models.AssetStatus.Inactive
            ),
            ip_address=instance.get("PrivateIpAddress") or instance.get("PublicIpAddress", ""),
            mac_address=None,  # Would need to get from network interfaces
            fqdn=fqdn,
            disk_storage=total_storage,
            cpu=cpu_count,
            ram=ram,
            operating_system=operating_system,
            os_version=os_version,
            location=region,
            notes=notes,
            model=instance.get("InstanceType"),
            manufacturer="AWS",
            is_public_facing=is_public_facing,
            aws_identifier=instance_arn,  # Use full ARN for asset matching with findings
            vlan_id=instance.get("SubnetId"),
            uri=uri,
            source_data=instance,
            description=description,
            is_virtual=True,  # EC2 instances are always virtual
        )

    def parse_lambda_function(self, function: Dict[str, Any]) -> IntegrationAsset:
        """
        Parse Lambda function data into RegScale asset format.

        :param Dict[str, Any] function: Lambda function data
        :return: RegScale asset
        :rtype: IntegrationAsset
        """
        name = function.get("FunctionName", "")
        notes: str = ""  # Initialize notes with type hint

        # Handle description - only slice if it's a string
        description = function.get("Description")
        if isinstance(description, str) and description:
            # Move description to notes instead
            notes = f"Description: {description}\n{notes}"

        # Create full description
        full_description = f"AWS Lambda function {function.get('FunctionName', '')} running {function.get('Runtime', 'unknown runtime')} with {function.get('MemorySize', 0)}MB memory"
        if isinstance(description, str) and description:
            full_description += f"\nFunction description: {description}"

        # Build notes with additional details
        notes = f"""Function Name: {function.get('FunctionName', '')}
Runtime: {function.get('Runtime', 'unknown')}
Memory Size: {function.get('MemorySize', 0)} MB
Timeout: {function.get('Timeout', 0)} seconds
Handler: {function.get('Handler', '')}
Description: {description if isinstance(description, str) else ''}"""

        return IntegrationAsset(
            # Required fields
            name=name,
            identifier=str(function.get("FunctionArn", "")),
            asset_type=regscale_models.AssetType.Other,
            asset_category=regscale_models.AssetCategory.Software,
            component_type=regscale_models.ComponentType.Software,
            component_names=["Lambda Functions"],
            # Parent information
            parent_id=self.plan_id,
            parent_module="securityplans",
            # Status and location
            status=regscale_models.AssetStatus.Active,  # Lambda functions are always available
            location=function.get("Region"),
            # Software details
            software_name=function.get("Runtime"),
            software_version=function.get("Runtime", "").split(".")[-1] if function.get("Runtime") else None,
            ram=function.get("MemorySize"),
            # Cloud identifiers
            external_id=function.get("FunctionName"),
            aws_identifier=function.get("FunctionArn"),
            uri=function.get("FunctionUrl"),
            # Additional metadata
            manufacturer="AWS",
            source_data=function,
            notes=notes,
            description=full_description,
            is_virtual=True,  # Lambda functions are serverless/virtual
        )

    def parse_aws_account(self, iam: Dict[str, Any]) -> IntegrationAsset:
        """
        Parse IAM data to an AWS Account RegScale asset.

        :param Dict[str, Any] iam: iam data
        :return: RegScale asset
        :rtype: IntegrationAsset
        """

        def get_aws_account_id(arn: str) -> str:
            """
            Get the AWS account ID from an ARN.

            :param str arn: The ARN to extract the account ID from
            :return: The AWS account ID
            :rtype: str
            """
            return arn.split(":")[4]

        name = get_aws_account_id(iam.get("Arn", ""))

        return IntegrationAsset(
            # Required fields
            name=name,
            identifier=f"AWS::::Account:{name}",
            asset_type=regscale_models.AssetType.Other,
            asset_category=regscale_models.AssetCategory.Hardware,
            component_type=regscale_models.ComponentType.Software,
            component_names=["AWS Account"],
            # Parent information
            parent_id=self.plan_id,
            parent_module="securityplans",
            # Status and location
            status=regscale_models.AssetStatus.Active,
            location="Unknown",
            # Cloud identifiers
            external_id=name,
            aws_identifier=f"AWS::::Account:{name}",
            # Additional metadata
            manufacturer="AWS",
            source_data=iam,
        )

    def parse_s3_bucket(self, bucket: Dict[str, Any]) -> IntegrationAsset:
        """
        Parse S3 bucket data into RegScale asset format.

        :param Dict[str, Any] bucket: S3 bucket data
        :return: RegScale asset
        :rtype: IntegrationAsset
        """
        name = bucket.get("Name", "")
        arn = f"arn:aws:s3:::{bucket.get('Name')}"
        return IntegrationAsset(
            # Required fields
            name=name,
            identifier=arn,
            asset_type=regscale_models.AssetType.Other,
            asset_category=regscale_models.AssetCategory.Hardware,
            component_type=regscale_models.ComponentType.Hardware,
            component_names=["S3 Buckets"],
            # Parent information
            parent_id=self.plan_id,
            parent_module="securityplans",
            # Status and location
            status=regscale_models.AssetStatus.Active,
            location=bucket.get("Region"),
            # Cloud identifiers
            external_id=bucket.get("Name"),
            aws_identifier=arn,
            uri=f"https://{bucket.get('Name')}.s3.amazonaws.com",
            # Additional metadata
            manufacturer="AWS",
            is_public_facing=any(
                grant.get("Grantee", {}).get("URI") == "http://acs.amazonaws.com/groups/global/AllUsers"
                for grant in bucket.get("Grants", [])
            ),
            source_data=bucket,
        )

    def parse_rds_instance(self, db: Dict[str, Any]) -> IntegrationAsset:
        """
        Parse RDS instance data into RegScale asset format.

        :param Dict[str, Any] db: RDS instance data
        :return: RegScale asset
        :rtype: IntegrationAsset
        """
        name = db.get("DBInstanceIdentifier", "")
        if db.get("EngineVersion"):
            name += f" {db.get('EngineVersion')}"
        name += f") - {db.get('DBInstanceClass', '')}"

        return IntegrationAsset(
            # Required fields
            name=name,
            identifier=str(db.get("DBInstanceArn", "")),
            asset_type=regscale_models.AssetType.VM,
            asset_category=regscale_models.AssetCategory.Hardware,
            component_type=regscale_models.ComponentType.Hardware,
            component_names=["RDS Instances"],
            # Parent information
            parent_id=self.plan_id,
            parent_module="securityplans",
            # Network information
            fqdn=db.get("Endpoint", {}).get("Address"),
            vlan_id=db.get("VpcId"),
            # Status and location
            status=(
                regscale_models.AssetStatus.Active
                if db.get("DBInstanceStatus") == "available"
                else regscale_models.AssetStatus.Inactive
            ),
            location=db.get("AvailabilityZone"),
            # Hardware details
            model=db.get("DBInstanceClass"),
            manufacturer="AWS",
            disk_storage=db.get("AllocatedStorage"),
            # Software details
            software_name=db.get("Engine"),
            software_version=db.get("EngineVersion"),
            # Cloud identifiers
            external_id=db.get("DBInstanceIdentifier"),
            aws_identifier=db.get("DBInstanceArn"),
            # Additional metadata
            is_public_facing=db.get("PubliclyAccessible", False),
            source_data=db,
        )

    def parse_dynamodb_table(self, table: Dict[str, Any]) -> IntegrationAsset:
        """
        Parse DynamoDB table data into RegScale asset format.

        :param Dict[str, Any] table: DynamoDB table data
        :return: RegScale asset
        :rtype: IntegrationAsset
        """
        name = table.get("TableName", "")
        if table.get("TableStatus"):
            name += f" ({table.get('TableStatus')})"

        return IntegrationAsset(
            # Required fields
            name=name,
            identifier=str(table.get("TableArn", "")),
            asset_type=regscale_models.AssetType.Other,
            asset_category=regscale_models.AssetCategory.Software,
            component_type=regscale_models.ComponentType.Software,
            component_names=["DynamoDB Tables"],
            # Parent information
            parent_id=self.plan_id,
            parent_module="securityplans",
            # Status and location
            status=(
                regscale_models.AssetStatus.Active
                if table.get("TableStatus") == "ACTIVE"
                else regscale_models.AssetStatus.Inactive
            ),
            location=table.get("Region"),
            # Hardware details
            disk_storage=table.get("TableSizeBytes"),
            # Cloud identifiers
            external_id=table.get("TableName"),
            aws_identifier=table.get("TableArn"),
            # Additional metadata
            manufacturer="AWS",
            source_data=table,
        )

    def parse_vpc(self, vpc: Dict[str, Any]) -> IntegrationAsset:
        """
        Parse VPC data into RegScale asset format.

        :param Dict[str, Any] vpc: VPC data
        :return: RegScale asset
        :rtype: IntegrationAsset
        """
        # Get VPC name from tags
        name = next((tag["Value"] for tag in vpc.get("Tags", []) if tag["Key"] == "Name"), vpc.get("VpcId", ""))
        notes: str = ""  # Initialize notes with type hint
        if vpc.get("IsDefault"):
            notes = "Default VPC\n" + notes

        # Build full ARN for VPC: arn:aws:ec2:region:account-id:vpc/vpc-id
        vpc_id = vpc.get("VpcId", "")
        region = vpc.get("Region", "us-east-1")
        account_id = vpc.get("OwnerId", "")
        vpc_arn = f"arn:aws:ec2:{region}:{account_id}:vpc/{vpc_id}"

        return IntegrationAsset(
            # Required fields
            name=name,
            identifier=vpc_arn,
            asset_type=regscale_models.AssetType.NetworkRouter,
            asset_category=regscale_models.AssetCategory.Hardware,
            component_type=regscale_models.ComponentType.Hardware,
            component_names=["VPCs"],
            # Parent information
            parent_id=self.plan_id,
            parent_module="securityplans",
            # Status and location
            status=(
                regscale_models.AssetStatus.Active
                if vpc.get("State") == "available"
                else regscale_models.AssetStatus.Inactive
            ),
            location=region,
            # Network information
            vlan_id=vpc_id,
            # Cloud identifiers
            external_id=vpc_id,
            aws_identifier=vpc_arn,  # Use full ARN for asset matching with findings
            # Additional metadata
            manufacturer="AWS",
            notes=f"CIDR: {vpc.get('CidrBlock')}",
            source_data=vpc,
        )

    def parse_load_balancer(self, lb: Dict[str, Any]) -> IntegrationAsset:
        """
        Parse Load Balancer data into RegScale asset format.

        :param Dict[str, Any] lb: Load Balancer data
        :return: RegScale asset
        :rtype: IntegrationAsset
        """
        name = lb.get("LoadBalancerName", "")
        notes: str = ""  # Initialize notes with type hint
        if lb.get("Scheme"):
            notes = f"Scheme: {lb.get('Scheme')}\n{notes}"

        return IntegrationAsset(
            # Required fields
            name=name,
            identifier=lb.get("LoadBalancerArn"),
            asset_type=regscale_models.AssetType.NetworkRouter,
            asset_category=regscale_models.AssetCategory.Hardware,
            component_type=regscale_models.ComponentType.Hardware,
            component_names=["Load Balancers"],
            # Parent information
            parent_id=self.plan_id,
            parent_module="securityplans",
            # Network information
            fqdn=lb.get("DNSName"),
            vlan_id=lb.get("VpcId"),
            # Status and location
            status=(
                regscale_models.AssetStatus.Active
                if lb.get("State") == "active"
                else regscale_models.AssetStatus.Inactive
            ),
            location=lb.get("Region"),
            # Cloud identifiers
            external_id=lb.get("LoadBalancerName"),
            aws_identifier=lb.get("LoadBalancerArn"),
            # Additional metadata
            manufacturer="AWS",
            is_public_facing=lb.get("Scheme") == "internet-facing",
            source_data=lb,
            # Ports and protocols
            ports_and_protocols=[
                {"port": listener.get("Port"), "protocol": listener.get("Protocol")}
                for listener in lb.get("Listeners", [])
            ],
        )

    def parse_ecr_repository(self, repo: Dict[str, Any]) -> IntegrationAsset:
        """
        Parse ECR repository data into RegScale asset format.

        :param Dict[str, Any] repo: ECR repository data
        :return: RegScale asset
        :rtype: IntegrationAsset
        """
        name = repo.get("RepositoryName", "")
        notes: str = ""  # Initialize notes with type hint
        if repo.get("ImageTagMutability"):
            notes = f"Image Tag Mutability: {repo.get('ImageTagMutability')}\n{notes}"
        if repo.get("ImageScanningConfiguration", {}).get("ScanOnPush"):
            notes = "Scan on Push enabled\n" + notes

        return IntegrationAsset(
            # Required fields
            name=name,
            identifier=str(repo.get("RepositoryArn", "")),
            asset_type=regscale_models.AssetType.Other,
            asset_category=regscale_models.AssetCategory.Software,
            component_type=regscale_models.ComponentType.Software,
            component_names=["ECR Repositories"],
            # Parent information
            parent_id=self.plan_id,
            parent_module="securityplans",
            # Status and location
            status=regscale_models.AssetStatus.Active,
            location=repo.get("Region"),
            # Cloud identifiers
            external_id=repo.get("RepositoryName"),
            aws_identifier=repo.get("RepositoryArn"),
            uri=repo.get("RepositoryUri"),
            # Additional metadata
            manufacturer="AWS",
            source_data=repo,
        )

    def _validate_aws_credentials(
        self,
        profile: Optional[str],
        aws_secret_key_id: Optional[str],
        aws_secret_access_key: Optional[str],
        region: Optional[str],
    ) -> None:
        """
        Validate AWS credentials and region are provided.

        :param profile: AWS profile name
        :param aws_secret_key_id: AWS access key ID
        :param aws_secret_access_key: AWS secret access key
        :param region: AWS region
        :raises ValueError: If credentials are not provided
        """
        if not profile and (not aws_secret_key_id or not aws_secret_access_key):
            raise ValueError(
                "AWS Profile or Access Credentials are required.\nPlease provide --profile or set environment "
                "variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY) or pass as arguments."
            )
        if not region:
            logger.warning("AWS region not provided. Defaulting to 'us-east-1'.")

    def _get_severity_config(self) -> Optional[str]:
        """
        Get minimum severity from config.

        :return: Minimum severity or None
        :rtype: Optional[str]
        """
        try:
            minimum_severity = self.app.config.get("issues", {}).get("amazon", {}).get("minimumSeverity")
            if minimum_severity:
                logger.info(f"Using minimumSeverity from config: {minimum_severity}")
            return minimum_severity
        except (KeyError, AttributeError):
            logger.debug("No minimumSeverity configured, fetching all findings")
            return None

    def _get_posture_management_config(self) -> bool:
        """
        Get posture management only setting from config.

        :return: Posture management only setting (defaults to False)
        :rtype: bool
        """
        try:
            posture_management_only = (
                self.app.config.get("issues", {}).get("amazon", {}).get("postureManagementOnly", False)
            )
            if posture_management_only:
                logger.info("Fetching posture management findings only (security standards compliance checks)")
            else:
                logger.info("Fetching all Security Hub findings (CVEs from Inspector + compliance checks)")
            return posture_management_only
        except (KeyError, AttributeError):
            logger.debug("No postureManagementOnly configured, defaulting to False (includes CVEs)")
            return False

    def _create_aws_session(
        self,
        aws_secret_key_id: Optional[str],
        aws_secret_access_key: Optional[str],
        region: str,
        profile: Optional[str],
        **kwargs,
    ):
        """
        Create AWS session with profile or explicit credentials.

        :param aws_secret_key_id: AWS access key ID
        :param aws_secret_access_key: AWS secret access key
        :param region: AWS region
        :param profile: AWS profile name
        :return: Boto3 session
        """
        import boto3

        if aws_secret_key_id or aws_secret_access_key:
            return boto3.Session(
                region_name=region,
                aws_access_key_id=aws_secret_key_id,
                aws_secret_access_key=aws_secret_access_key,
                aws_session_token=kwargs.get("aws_session_token"),
            )
        return boto3.Session(profile_name=profile, region_name=region)

    def fetch_findings(self, *args, **kwargs) -> Iterator[IntegrationFinding]:
        """
        Fetch security findings from AWS Security Hub.
        Also discovers assets from the finding resources during processing.

        :yield: Iterator[IntegrationFinding]
        """
        aws_secret_key_id = kwargs.get("aws_access_key_id") or os.getenv("AWS_ACCESS_KEY_ID")
        aws_secret_access_key = kwargs.get("aws_secret_access_key") or os.getenv("AWS_SECRET_ACCESS_KEY")
        region = kwargs.get("region") or os.getenv("AWS_REGION", "us-east-1")
        profile = kwargs.get("profile")

        self._validate_aws_credentials(profile, aws_secret_key_id, aws_secret_access_key, region)

        minimum_severity = self._get_severity_config()
        posture_management_only = self._get_posture_management_config()

        # Create a copy of kwargs excluding parameters we're passing explicitly
        session_kwargs = {
            k: v
            for k, v in kwargs.items()
            if k not in ("aws_access_key_id", "aws_secret_access_key", "region", "profile")
        }
        session = self._create_aws_session(aws_secret_key_id, aws_secret_access_key, region, profile, **session_kwargs)
        client = session.client("securityhub")

        aws_findings = fetch_aws_findings(
            aws_client=client, minimum_severity=minimum_severity, posture_management_only=posture_management_only
        )

        self.discovered_assets.clear()
        self.processed_asset_identifiers.clear()

        for finding in aws_findings:
            yield from iter(self.parse_finding(finding))

        if self.discovered_assets:
            logger.info(f"Discovered {len(self.discovered_assets)} assets from Security Hub findings")

    def get_discovered_assets(self) -> Iterator[IntegrationAsset]:
        """
        Get assets discovered from Security Hub findings.

        :return: Iterator of discovered assets
        :rtype: Iterator[IntegrationAsset]
        """
        logger.info(f"Yielding {len(self.discovered_assets)} discovered assets from findings")
        for asset in self.discovered_assets:
            yield asset

    def sync_findings_and_assets(self, **kwargs) -> tuple[int, int]:
        """
        Sync both findings and discovered assets from AWS Security Hub.
        First discovers assets from findings, creates them, then processes findings.

        :return: Tuple of (findings_processed, assets_processed)
        :rtype: tuple[int, int]
        """
        from regscale.core.app.utils.app_utils import create_progress_object

        logger.info("Starting AWS Security Hub findings and assets sync...")

        # Create progress bar context for the entire operation
        with create_progress_object() as progress:
            # Store progress object for use by nested methods
            self.finding_progress = progress

            # First, fetch findings to discover assets (but don't sync findings yet)
            logger.info("Discovering assets from AWS Security Hub findings...")

            # Reset discovered assets for this run
            self.discovered_assets.clear()
            self.processed_asset_identifiers.clear()

            # Fetch findings to discover assets - store them to avoid re-fetching
            findings_list = list(self.fetch_findings(**kwargs))

            # Sync the discovered assets first
            if self.discovered_assets:
                logger.info(f"Creating {len(self.discovered_assets)} assets discovered from findings...")
                self.num_assets_to_process = len(self.discovered_assets)
                assets_processed = self.update_regscale_assets(self.get_discovered_assets())
                logger.info(f"Successfully created {assets_processed} assets")
            else:
                logger.info("No assets discovered from findings")
                assets_processed = 0

            # Now process the findings we already fetched (avoid double-fetching)
            logger.info("Now syncing findings with created assets...")
            findings_processed = self.update_regscale_findings(findings_list)

            # Log completion summary
            logger.info(
                f"AWS Security Hub sync completed successfully: {findings_processed} findings processed, {assets_processed} assets created"
            )

        return findings_processed, assets_processed

    @classmethod
    def sync_findings(cls, plan_id: int, **kwargs) -> int:
        """
        Sync AWS Security Hub findings to RegScale.

        :param int plan_id: The RegScale plan ID
        :param kwargs: Additional keyword arguments including:
            - region (str): AWS region
            - profile (Optional[str]): AWS profile name
            - aws_access_key_id (Optional[str]): AWS access key ID
            - aws_secret_access_key (Optional[str]): AWS secret access key
            - aws_session_token (Optional[str]): AWS session token
            - account_id (Optional[str]): AWS account ID to filter by
            - tags (Optional[Dict[str, str]]): Tags to filter by
            - import_all_findings (bool): Import all findings even without matching assets
        :return: Number of findings processed
        :rtype: int
        """
        # Extract parameters from kwargs
        region = kwargs.get("region", "us-east-1")
        profile = kwargs.get("profile")
        aws_access_key_id = kwargs.get("aws_access_key_id")
        aws_secret_access_key = kwargs.get("aws_secret_access_key")
        aws_session_token = kwargs.get("aws_session_token")
        account_id = kwargs.get("account_id")
        tags = kwargs.get("tags")
        import_all_findings = kwargs.get("import_all_findings", False)

        instance = cls(plan_id=plan_id, import_all_findings=import_all_findings)
        instance.authenticate(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region=region,
            aws_session_token=aws_session_token,
            profile=profile,
            account_id=account_id,
            tags=tags,
        )

        # Load assets first
        logger.info("Loading asset map from RegScale...")
        instance.asset_map_by_identifier.update(instance.get_asset_map())

        # Fetch and sync findings
        logger.info("Fetching and syncing AWS Security Hub findings...")
        findings = list(
            instance.fetch_findings(
                profile=profile,
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                aws_session_token=aws_session_token,
                region=region,
                account_id=account_id,
                tags=tags,
            )
        )

        # Process findings - progress bar will be created inside update_regscale_findings if needed
        findings_processed = instance.update_regscale_findings(findings)

        return findings_processed

    def get_configured_issue_status(self) -> IssueStatus:
        """
        Get the configured issue status from the configuration.

        :return: The configured issue status
        :rtype: IssueStatus
        """
        configured_status = self._get_aws_config("status", default="Open")
        if configured_status.lower() == "open":
            return IssueStatus.Open
        elif configured_status.lower() == "closed":
            return IssueStatus.Closed
        else:
            logger.warning(f"Unknown configured status '{configured_status}', defaulting to Open")
            return IssueStatus.Open

    def should_process_finding_by_severity(self, severity: str) -> bool:
        """
        Check if a finding should be processed based on the configured minimum severity.

        :param str severity: The severity level of the finding
        :return: True if the finding should be processed, False otherwise
        :rtype: bool
        """
        min_severity = self._get_aws_config("minimumSeverity", default="LOW").upper()

        # Define severity hierarchy (higher number = more severe)
        severity_levels = {
            "INFORMATIONAL": 0,
            "INFO": 0,
            "LOW": 1,
            "MEDIUM": 2,
            "MODERATE": 2,
            "HIGH": 3,
            "CRITICAL": 4,
        }

        finding_severity_level = severity_levels.get(severity.upper(), 0)
        min_severity_level = severity_levels.get(min_severity, 1)  # Default to LOW if not found

        should_process = finding_severity_level >= min_severity_level

        if not should_process:
            logger.debug(
                f"Filtering out finding with severity '{severity}' (level {finding_severity_level}) - below minimum '{min_severity}' (level {min_severity_level})"
            )

        return should_process

    def is_service_enabled_for_resource(self, resource_type: str) -> bool:
        """
        Check if the AWS service for a given resource type is enabled in config.

        :param str resource_type: AWS resource type (e.g., 'AwsEc2Instance', 'AwsS3Bucket')
        :return: True if the service is enabled or config not found, False otherwise
        :rtype: bool
        """
        # Map resource types to service configuration keys
        resource_to_service_map = {
            "AwsEc2Instance": ("compute", "ec2"),
            "AwsEc2SecurityGroup": ("security", "securityhub"),
            "AwsEc2Subnet": ("networking", "vpc"),
            "AwsS3Bucket": ("storage", "s3"),
            "AwsRdsDbInstance": ("database", "rds"),
            "AwsLambdaFunction": ("compute", "lambda"),
            "AwsEcrRepository": ("containers", "ecr"),
            "AwsIamUser": ("security", "iam"),
            "AwsIamRole": ("security", "iam"),
            "AwsDynamoDbTable": ("database", "dynamodb"),
            "AwsKmsKey": ("security", "kms"),
            "AwsSecretsManagerSecret": ("security", "secrets_manager"),
            "AwsCloudTrailTrail": ("security", "cloudtrail"),
            "AwsConfigConfigurationRecorder": ("security", "config"),
            "AwsGuardDutyDetector": ("security", "guardduty"),
            "AwsInspector2": ("security", "inspector"),
            "AwsAuditManagerAssessment": ("security", "audit_manager"),
        }

        try:
            # Get the service category and service name for this resource type
            service_info = resource_to_service_map.get(resource_type)
            if not service_info:
                # If resource type not in map, allow it by default (don't filter unknowns)
                logger.debug(f"Resource type '{resource_type}' not in service map, allowing by default")
                return True

            category, service_name = service_info

            # Check if the service is enabled in config
            enabled_services = self.app.config.get("aws", {}).get("inventory", {}).get("enabled_services", {})

            # Check if category is enabled
            category_config = enabled_services.get(category, {})
            if not category_config.get("enabled", True):
                logger.debug(f"Service category '{category}' is disabled, filtering resource type '{resource_type}'")
                return False

            # Check if specific service is enabled
            services = category_config.get("services", {})
            is_enabled = services.get(service_name, True)

            if not is_enabled:
                logger.debug(
                    f"Service '{service_name}' in category '{category}' is disabled, filtering resource type '{resource_type}'"
                )

            return is_enabled

        except (KeyError, AttributeError) as e:
            # If config not found or malformed, allow by default (don't filter)
            logger.debug(f"Could not check service enablement for '{resource_type}': {e}. Allowing by default.")
            return True

    @staticmethod
    def get_baseline(resource: dict) -> str:
        """
        Get Baseline

        :param dict resource: AWS Resource
        :return: AWS Baseline string
        :rtype: str
        """
        baseline = resource.get("Type", "")
        baseline_map = {
            "AwsAccount": "AWS Account",
            "AwsS3Bucket": "S3 Bucket",
            "AwsIamRole": "IAM Role",
            "AwsEc2Instance": "EC2 Instance",
        }
        return baseline_map.get(baseline, baseline)

    @staticmethod
    def extract_name_from_arn(arn: str) -> Optional[str]:
        """
        Extract the name from an ARN.

        :param str arn: The ARN to extract the name from
        :return: The extracted name, or None if not found
        :rtype: Optional[str]
        """
        # Get the last part after the last '/'
        try:
            return arn.split("/")[-1]
        except IndexError:
            # For ARNs without '/', try getting the last part after ':'
            try:
                return arn.split(":")[-1]
            except IndexError:
                return None

    def _discover_asset_from_resource(self, resource: dict, finding: dict) -> None:
        """
        Discover and track asset from finding resource.

        :param dict resource: AWS Security Hub resource
        :param dict finding: AWS Security Hub finding
        """
        asset = self.parse_resource_to_asset(resource, finding)
        if asset and asset.identifier not in self.processed_asset_identifiers:
            self.discovered_assets.append(asset)
            self.processed_asset_identifiers.add(asset.identifier)
            logger.debug(f"Discovered asset from finding: {asset.name} ({asset.identifier})")

    def _get_friendly_severity(self, severity: str) -> str:
        """
        Convert severity level to friendly name.

        :param str severity: Raw severity level
        :return: Friendly severity name (low, moderate, high)
        :rtype: str
        """
        if severity in ["CRITICAL", "HIGH"]:
            return "high"
        elif severity in ["MEDIUM", "MODERATE"]:
            return "moderate"
        return "low"

    def _get_due_date_for_finding(self, finding: dict, friendly_sev: str) -> str:
        """
        Calculate due date for finding based on severity.

        :param dict finding: AWS Security Hub finding
        :param str friendly_sev: Friendly severity name
        :return: Due date string
        :rtype: str
        """
        days = self._get_aws_config(friendly_sev, default=self._get_default_days(friendly_sev))
        return datetime_str(get_due_date(date_str(finding["CreatedAt"]), days))

    def _construct_plugin_id(self, finding: dict, resource: dict = None) -> tuple[str, str]:
        """
        Construct plugin name and ID from finding.

        For consolidated mode: Uses GeneratorId to create ONE plugin_id per control type
        For per-asset mode: Uses Finding ID to create unique plugin_id per finding

        :param dict finding: AWS Security Hub finding
        :param dict resource: Optional resource dict for per-resource plugin ID
        :return: Tuple of (plugin_name, plugin_id)
        :rtype: tuple[str, str]
        """
        from regscale.integrations.scanner_integration import ScannerVariables

        plugin_name = next(iter(finding.get("Types", [])), "Unknown")
        issue_creation_mode = ScannerVariables.issueCreation.lower()

        # DEBUG: Log the mode being used (only log first few times to avoid spam)
        if not hasattr(self, "_mode_logged"):
            logger.info(f"[PLUGIN_ID_DEBUG] issueCreation mode: '{issue_creation_mode}'")
            self._mode_logged = True

        # In consolidated mode, use GeneratorId to group findings by their finding type
        # This consolidates all findings of the same type (e.g., all SSH brute force attacks)
        # regardless of which specific resources or IPs are involved
        if issue_creation_mode == "consolidated":
            # Use GeneratorId as the consolidation key - this groups by finding type
            # Examples:
            #   - GuardDuty: "aws-guardduty" (for all Guard Duty findings of same type)
            #   - Security Hub: "security-control/IAM.19" (for all IAM.19 findings)
            #   - Inspector: "arn:aws:inspector:..." (for all findings from same rule)
            generator_id = finding.get("GeneratorId", "Unknown")

            # Sanitize GeneratorId for use in plugin_id
            # Replace special characters with underscores
            sanitized_generator = generator_id.replace("/", "_").replace(":", "_").replace(" ", "_")
            sanitized_generator = sanitized_generator.replace(".", "_").replace("-", "_")

            # Create plugin_id from sanitized GeneratorId
            plugin_id = f"AWS_Security_Hub_{sanitized_generator}"
        else:
            # Per-asset mode: use finding UUID for unique identification
            finding_id = finding.get("Id", "")

            # Extract UUID from ARN or full ID
            if "/" in finding_id:
                finding_uuid = finding_id.split("/")[-1]
            else:
                finding_uuid = finding_id.split(":")[-1]

            # Sanitize plugin name for ID
            sanitized_name = plugin_name.replace(" ", "_").replace("/", "_").replace(":", "_")

            # If we have multiple resources for this finding, include resource identifier
            # This ensures proper deduplication when a finding affects multiple resources
            if resource and len(finding.get("Resources", [])) > 1:
                resource_id = resource.get("Id", "")
                # Extract just the resource identifier part from ARN
                if "/" in resource_id:
                    resource_suffix = resource_id.split("/")[-1]
                elif ":" in resource_id:
                    resource_suffix = resource_id.split(":")[-1]
                else:
                    resource_suffix = resource_id

                # Sanitize and append resource suffix
                resource_suffix = resource_suffix.replace(" ", "_").replace("/", "_").replace(":", "_")
                plugin_id = f"{sanitized_name}_{finding_uuid}_{resource_suffix}"
            else:
                plugin_id = f"{sanitized_name}_{finding_uuid}"

        return plugin_name, plugin_id

    def _extract_cvss_scores(self, cvss_list: list) -> list:
        """
        Extract CVSS scores from vulnerability data.

        :param list cvss_list: List of CVSS data
        :return: List of formatted CVSS score strings
        :rtype: list
        """
        cvss_scores = []
        for cvss in cvss_list:
            cvss_version = cvss.get("Version", "")
            cvss_score = cvss.get("BaseScore", 0)
            cvss_vector = cvss.get("BaseVector", "")
            if cvss_score:
                score_parts = [f"CVSS{cvss_version}: {cvss_score}"]
                if cvss_vector:
                    score_parts.append(f"({cvss_vector})")
                cvss_scores.append(" ".join(score_parts))
        return cvss_scores

    def _extract_vendor_info(self, vendor: dict) -> str:
        """
        Extract vendor information from vulnerability data.

        :param dict vendor: Vendor data
        :return: Formatted vendor info string
        :rtype: str
        """
        vendor_name = vendor.get("Name", "")
        vendor_url = vendor.get("Url", "")
        if not vendor_name:
            return ""
        return f"{vendor_name}: {vendor_url}" if vendor_url else vendor_name

    def _build_package_version_string(self, pkg: dict) -> str:
        """
        Build version string from package data.

        :param dict pkg: Package data
        :return: Formatted version string
        :rtype: str
        """
        pkg_version = pkg.get("Version", "")
        if not pkg_version:
            return ""

        version_str = pkg_version
        if pkg_epoch := pkg.get("Epoch", ""):
            version_str = f"{pkg_epoch}:{version_str}"
        if pkg_release := pkg.get("Release", ""):
            version_str = f"{version_str}-{pkg_release}"
        if pkg_arch := pkg.get("Architecture", ""):
            version_str = f"{version_str}.{pkg_arch}"
        return version_str

    def _extract_package_details(self, pkg: dict) -> str:
        """
        Extract package details from vulnerable package data.

        :param dict pkg: Package data
        :return: Formatted package details string
        :rtype: str
        """
        pkg_details = []

        if pkg_name := pkg.get("Name", ""):
            pkg_details.append(f"Package: {pkg_name}")

        if version_str := self._build_package_version_string(pkg):
            pkg_details.append(f"Installed Version: {version_str}")

        if fixed_version := pkg.get("FixedInVersion", ""):
            pkg_details.append(f"Fixed In: {fixed_version}")

        return " | ".join(pkg_details) if pkg_details else ""

    def _process_vulnerability(self, vuln: dict, cve_data: dict) -> None:
        """
        Process a single vulnerability and update CVE data dictionary.

        :param dict vuln: Vulnerability data
        :param dict cve_data: CVE data dictionary to update
        """
        if cve_id := vuln.get("Id", ""):
            cve_data["cve_ids"].append(cve_id)

        if cvss_list := vuln.get("Cvss", []):
            cve_data["cvss_scores"].extend(self._extract_cvss_scores(cvss_list))

        if vendor := vuln.get("Vendor", {}):
            if vendor_info := self._extract_vendor_info(vendor):
                cve_data["vendor_info"].append(vendor_info)

        if ref_urls := vuln.get("ReferenceUrls", []):
            cve_data["reference_urls"].extend(ref_urls)

        for pkg in vuln.get("VulnerablePackages", []):
            if pkg_details := self._extract_package_details(pkg):
                cve_data["vulnerability_details"].append(pkg_details)

    def _process_vulnerability_enhanced(self, vuln: dict, cve_data: dict) -> None:
        """
        Process a single vulnerability with enhanced structured data extraction.

        :param dict vuln: Vulnerability data
        :param dict cve_data: CVE data dictionary to update with structured fields
        """
        self._extract_cve_id(vuln, cve_data)
        self._extract_cvss_scores(vuln, cve_data)
        self._extract_vendor_info_from_vuln(vuln, cve_data)
        self._extract_reference_urls(vuln, cve_data)
        self._extract_exploit_availability(vuln, cve_data)
        self._extract_package_details_from_vuln(vuln, cve_data)

    def _extract_cve_id(self, vuln: dict, cve_data: dict) -> None:
        """
        Extract CVE ID from vulnerability data.

        :param dict vuln: Vulnerability data
        :param dict cve_data: CVE data dictionary to update
        :rtype: None
        """
        if cve_id := vuln.get("Id", ""):
            cve_data["cve_ids"].append(cve_id)

    def _extract_cvss_scores(self, vuln: dict, cve_data: dict) -> None:
        """
        Extract and parse CVSS scores from vulnerability data.

        :param dict vuln: Vulnerability data
        :param dict cve_data: CVE data dictionary to update
        :rtype: None
        """
        cvss_list = vuln.get("Cvss", [])
        if not cvss_list:
            return

        for cvss in cvss_list:
            self._process_single_cvss_score(cvss, cve_data)

    def _process_single_cvss_score(self, cvss: dict, cve_data: dict) -> None:
        """
        Process a single CVSS score entry.

        :param dict cvss: CVSS score data
        :param dict cve_data: CVE data dictionary to update
        :rtype: None
        """
        version = cvss.get("Version", "")
        score = cvss.get("BaseScore", 0)
        vector = cvss.get("BaseVector", "")

        if not score:
            return

        self._add_cvss_score_string(version, score, vector, cve_data)
        self._update_cvss_structured_data(version, score, vector, cve_data)

    def _add_cvss_score_string(self, version: str, score: float, vector: str, cve_data: dict) -> None:
        """
        Add formatted CVSS score string to CVE data.

        :param str version: CVSS version
        :param float score: CVSS score
        :param str vector: CVSS vector
        :param dict cve_data: CVE data dictionary to update
        :rtype: None
        """
        score_str = f"CVSS{version}: {score}"
        if vector:
            score_str += f" ({vector})"
        cve_data["cvss_scores"].append(score_str)

    def _update_cvss_structured_data(self, version: str, score: float, vector: str, cve_data: dict) -> None:
        """
        Update structured CVSS data fields based on version.

        :param str version: CVSS version
        :param float score: CVSS score
        :param str vector: CVSS vector
        :param dict cve_data: CVE data dictionary to update
        :rtype: None
        """
        if version in ("3.0", "3.1"):
            self._update_cvss_v3_data(score, vector, cve_data)
        elif version == "2.0":
            self._update_cvss_v2_data(score, vector, cve_data)

    def _update_cvss_v3_data(self, score: float, vector: str, cve_data: dict) -> None:
        """
        Update CVSS v3 data with highest score.

        :param float score: CVSS score
        :param str vector: CVSS vector
        :param dict cve_data: CVE data dictionary to update
        :rtype: None
        """
        if cve_data["cvss_v3_score"] is None or score > cve_data["cvss_v3_score"]:
            cve_data["cvss_v3_score"] = float(score)
            if vector:
                cve_data["cvss_v3_vector"] = vector

    def _update_cvss_v2_data(self, score: float, vector: str, cve_data: dict) -> None:
        """
        Update CVSS v2 data with highest score.

        :param float score: CVSS score
        :param str vector: CVSS vector
        :param dict cve_data: CVE data dictionary to update
        :rtype: None
        """
        if cve_data["cvss_v2_score"] is None or score > cve_data["cvss_v2_score"]:
            cve_data["cvss_v2_score"] = float(score)
            if vector:
                cve_data["cvss_v2_vector"] = vector

    def _extract_vendor_info_from_vuln(self, vuln: dict, cve_data: dict) -> None:
        """
        Extract vendor information from vulnerability data.

        :param dict vuln: Vulnerability data
        :param dict cve_data: CVE data dictionary to update
        :rtype: None
        """
        if vendor := vuln.get("Vendor", {}):
            if vendor_info := self._extract_vendor_info(vendor):
                cve_data["vendor_info"].append(vendor_info)

    def _extract_reference_urls(self, vuln: dict, cve_data: dict) -> None:
        """
        Extract reference URLs from vulnerability data.

        :param dict vuln: Vulnerability data
        :param dict cve_data: CVE data dictionary to update
        :rtype: None
        """
        if ref_urls := vuln.get("ReferenceUrls", []):
            cve_data["reference_urls"].extend(ref_urls)

    def _extract_exploit_availability(self, vuln: dict, cve_data: dict) -> None:
        """
        Check and set exploit availability flag.

        :param dict vuln: Vulnerability data
        :param dict cve_data: CVE data dictionary to update
        :rtype: None
        """
        if vuln.get("ExploitAvailable"):
            cve_data["exploit_available"] = True

    def _extract_package_details_from_vuln(self, vuln: dict, cve_data: dict) -> None:
        """
        Extract package details from vulnerability data.

        :param dict vuln: Vulnerability data
        :param dict cve_data: CVE data dictionary to update
        :rtype: None
        """
        for pkg in vuln.get("VulnerablePackages", []):
            self._process_vulnerable_package(pkg, cve_data)

    def _process_vulnerable_package(self, pkg: dict, cve_data: dict) -> None:
        """
        Process a single vulnerable package.

        :param dict pkg: Package data
        :param dict cve_data: CVE data dictionary to update
        :rtype: None
        """
        if pkg_name := pkg.get("Name", ""):
            cve_data["affected_packages"].append(pkg_name)

        if version_str := self._build_package_version_string(pkg):
            cve_data["installed_versions"].append(version_str)

        if fixed_version := pkg.get("FixedInVersion", ""):
            cve_data["fixed_versions"].append(fixed_version)

        if pkg_details := self._extract_package_details(pkg):
            cve_data["vulnerability_details"].append(pkg_details)

    def _extract_cve_data(self, finding: dict) -> dict:
        """
        Extract CVE and vulnerability data from AWS Security Hub finding with structured CVSS data.

        :param dict finding: AWS Security Hub finding
        :return: Dictionary with CVE data including structured CVSS scores
        :rtype: dict
        """
        cve_data: dict = {
            "cve_ids": [],
            "cvss_scores": [],
            "vulnerability_details": [],
            "vendor_info": [],
            "reference_urls": [],
            # New structured fields
            "cvss_v3_score": None,
            "cvss_v2_score": None,
            "cvss_v3_vector": None,
            "cvss_v2_vector": None,
            "affected_packages": [],
            "installed_versions": [],
            "fixed_versions": [],
            "exploit_available": False,
        }

        vulnerabilities = finding.get("Vulnerabilities", [])
        if not vulnerabilities:
            return cve_data

        for vuln in vulnerabilities:
            self._process_vulnerability_enhanced(vuln, cve_data)

        # Convert lists to comma-separated strings for model fields
        if cve_data["affected_packages"]:
            cve_data["affected_packages_str"] = ", ".join(cve_data["affected_packages"])
        if cve_data["installed_versions"]:
            cve_data["installed_versions_str"] = ", ".join(cve_data["installed_versions"])
        if cve_data["fixed_versions"]:
            cve_data["fixed_versions_str"] = ", ".join(cve_data["fixed_versions"])

        return cve_data

    def _create_integration_finding(
        self,
        resource: dict,
        finding: dict,
        severity: str,
        comments: str,
        status: str,
        results: str,
        due_date: str,
        plugin_name: str,
        plugin_id: str,
    ) -> IntegrationFinding:
        """
        Create IntegrationFinding from processed finding data.

        :param dict resource: AWS resource from finding
        :param dict finding: AWS Security Hub finding
        :param str severity: Severity level
        :param str comments: Finding comments
        :param str status: Compliance status
        :param str results: Test results
        :param str due_date: Due date string
        :param str plugin_name: Plugin name
        :param str plugin_id: Plugin ID
        :return: Integration finding
        :rtype: IntegrationFinding
        """
        # Extract CVE data from finding
        cve_data = self._extract_cve_data(finding)

        # Build enhanced comments with CVE information
        enhanced_comments = comments
        if cve_data["cve_ids"]:
            enhanced_comments += f"\n\nCVE IDs: {', '.join(cve_data['cve_ids'])}"
        if cve_data["cvss_scores"]:
            enhanced_comments += f"\nCVSS Scores: {'; '.join(cve_data['cvss_scores'])}"
        if cve_data["vulnerability_details"]:
            enhanced_comments += "\n\nVulnerable Packages:\n" + "\n".join(
                f"- {detail}" for detail in cve_data["vulnerability_details"]
            )
        if cve_data["vendor_info"]:
            enhanced_comments += f"\n\nVendor Info: {'; '.join(cve_data['vendor_info'])}"
        if cve_data["reference_urls"]:
            enhanced_comments += "\n\nReferences:\n" + "\n".join(
                f"- {url}" for url in cve_data["reference_urls"][:5]  # Limit to first 5 URLs
            )

        # Build observations with CVE details
        observations = enhanced_comments

        # Build gaps field with vulnerability details
        gaps = ""
        if cve_data["vulnerability_details"]:
            gaps = "Vulnerable packages identified:\n" + "\n".join(cve_data["vulnerability_details"])

        # Build evidence field with reference URLs
        evidence = ""
        if cve_data["reference_urls"]:
            evidence = "Reference URLs:\n" + "\n".join(cve_data["reference_urls"])

        # Determine vulnerability number and plugin_id (primary CVE ID if available)
        vulnerability_number = cve_data["cve_ids"][0] if cve_data["cve_ids"] else ""
        primary_cve = cve_data["cve_ids"][0] if cve_data["cve_ids"] else None

        # Use CVE as plugin_id if available, otherwise use constructed plugin_id
        if primary_cve:
            plugin_id = primary_cve

        # Extract first/last seen dates from finding
        first_seen_date = date_str(finding.get("FirstObservedAt", finding.get("CreatedAt")))
        last_seen_date = date_str(finding.get("LastObservedAt", finding.get("UpdatedAt", finding.get("CreatedAt"))))

        return IntegrationFinding(
            asset_identifier=resource["Id"],
            external_id=finding.get("Id", ""),
            control_labels=[],
            title=finding["Title"],
            category="SecurityHub",
            issue_title=finding["Title"],
            severity=self.finding_severity_map.get(severity),
            description=finding["Description"],
            status=self.get_configured_issue_status(),
            checklist_status=self.get_checklist_status(status),
            vulnerability_number=vulnerability_number,
            results=results,
            recommendation_for_mitigation=finding.get("Remediation", {}).get("Recommendation", {}).get("Text", ""),
            comments=enhanced_comments,
            poam_comments=enhanced_comments,
            date_created=date_str(finding["CreatedAt"]),
            due_date=due_date,
            plugin_name=plugin_name,
            plugin_id=plugin_id,
            baseline=self.get_baseline(resource),
            observations=observations,
            gaps=gaps,
            evidence=evidence,
            impact="",
            vulnerability_type="Vulnerability Scan",
            # Vulnerability-specific fields
            cve=primary_cve,
            cvss_v3_score=cve_data.get("cvss_v3_score"),
            cvss_v2_score=cve_data.get("cvss_v2_score"),
            cvss_v3_vector=cve_data.get("cvss_v3_vector"),
            cvss_v2_vector=cve_data.get("cvss_v2_vector"),
            first_seen=first_seen_date,
            last_seen=last_seen_date,
            affected_packages=cve_data.get("affected_packages_str"),
            installed_versions=cve_data.get("installed_versions_str"),
            fixed_versions=cve_data.get("fixed_versions_str"),
        )

    def parse_finding(self, finding: dict) -> list[IntegrationFinding]:
        """
        Parse AWS Security Hub to RegScale IntegrationFinding format.
        Also collects assets from the finding resources for later processing.

        :param dict finding: AWS Security Hub finding
        :return: RegScale IntegrationFinding
        :rtype: list[IntegrationFinding]
        """
        findings = []
        try:
            for resource in finding["Resources"]:
                # Check if the service for this resource type is enabled
                resource_type = resource.get("Type", "")
                if not self.is_service_enabled_for_resource(resource_type):
                    logger.debug(f"Skipping finding for disabled service resource type '{resource_type}'")
                    continue

                # Discover asset from resource
                self._discover_asset_from_resource(resource, finding)

                # Determine status and severity
                status, results = determine_status_and_results(finding)
                comments = get_comments(finding)
                severity = check_finding_severity(finding, comments)
                friendly_sev = self._get_friendly_severity(severity)

                # Filter by minimum severity
                if not self.should_process_finding_by_severity(severity):
                    logger.debug(f"Skipping finding with severity '{severity}' - below minimum threshold")
                    continue

                # Calculate due date and construct IDs
                due_date = self._get_due_date_for_finding(finding, friendly_sev)
                plugin_name, plugin_id = self._construct_plugin_id(finding, resource)

                # Create finding object
                integration_finding = self._create_integration_finding(
                    resource, finding, severity, comments, status, results, due_date, plugin_name, plugin_id
                )
                findings.append(integration_finding)

        except Exception as e:
            logger.error(f"Error parsing AWS Security Hub finding: {str(e)}", exc_info=True)

        return findings

    def _parse_and_track_findings(self, findings: List[dict]) -> tuple[List[IntegrationFinding], dict]:
        """Parse findings and track plugin_id usage for deduplication metrics."""
        integration_findings = []
        plugin_id_counter = {}

        for finding in findings:
            parsed_findings = self.parse_finding(finding)
            for parsed_finding in parsed_findings:
                plugin_id = parsed_finding.plugin_id
                plugin_id_counter[plugin_id] = plugin_id_counter.get(plugin_id, 0) + 1
            integration_findings.extend(parsed_findings)

        return integration_findings, plugin_id_counter

    def _log_deduplication_stats(self, integration_findings: List[IntegrationFinding], plugin_id_counter: dict) -> None:
        """Log deduplication statistics for findings."""
        if not integration_findings:
            return

        total_findings = len(integration_findings)
        unique_plugin_ids = len(plugin_id_counter)
        deduplication_ratio = total_findings / unique_plugin_ids if unique_plugin_ids > 0 else 0

        logger.info(
            f"[DEDUPLICATION STATS] Processed {total_findings} findings -> "
            f"{unique_plugin_ids} unique plugin_ids "
            f"(deduplication ratio: {deduplication_ratio:.2f}x)"
        )

        if len(plugin_id_counter) > 0:
            top_duplicated = sorted(plugin_id_counter.items(), key=lambda x: x[1], reverse=True)[:10]
            logger.info("[DEDUPLICATION STATS] Top 10 most consolidated controls:")
            for plugin_id, count in top_duplicated:
                control_id = plugin_id.split("_")[-1] if "_" in plugin_id else plugin_id
                logger.info(f"  {control_id}: {count} findings consolidated")

    def _generate_ocsf_data(self, findings: List[dict], service_name: str) -> Optional[List[dict]]:
        """Generate OCSF formatted data for findings."""
        from regscale.integrations.commercial.aws.ocsf.mapper import AWSOCSFMapper

        mapper = AWSOCSFMapper()
        if service_name == "SecurityHub":
            return [mapper.securityhub_to_ocsf(f) for f in findings]
        elif service_name == "GuardDuty":
            return [mapper.guardduty_to_ocsf(f) for f in findings]
        elif service_name == "CloudTrail":
            return [mapper.cloudtrail_event_to_ocsf(f) for f in findings]
        return None

    def _generate_evidence_record(
        self,
        findings: List[dict],
        service_name: str,
        ssp_id: Optional[int],
        control_ids: Optional[List[int]],
        ocsf_data: Optional[List[dict]],
    ) -> Optional[Any]:
        """Generate evidence record from findings."""
        from regscale.core.app.api import Api
        from regscale.integrations.commercial.aws.evidence_generator import AWSEvidenceGenerator

        evidence_gen = AWSEvidenceGenerator(api=Api(), ssp_id=ssp_id)
        return evidence_gen.create_evidence_from_scan(
            service_name=service_name, findings=findings, ocsf_data=ocsf_data, control_ids=control_ids
        )

    def process_findings_with_evidence(
        self,
        findings: List[dict],
        service_name: str,
        generate_evidence: bool = False,
        ssp_id: Optional[int] = None,
        control_ids: Optional[List[int]] = None,
        ocsf_format: bool = False,
    ) -> tuple[List[IntegrationFinding], Optional[Any]]:
        """
        Process findings and optionally generate evidence

        :param List[dict] findings: Raw AWS findings
        :param str service_name: AWS service name
        :param bool generate_evidence: Whether to generate evidence record
        :param Optional[int] ssp_id: SSP ID to link evidence
        :param Optional[List[int]] control_ids: Control IDs to link
        :param bool ocsf_format: Whether to generate OCSF format
        :return: Tuple of (parsed findings, evidence record)
        :rtype: tuple[List[IntegrationFinding], Optional[Any]]
        """
        # Parse findings and track plugin_id usage
        integration_findings, plugin_id_counter = self._parse_and_track_findings(findings)

        # Log deduplication statistics
        self._log_deduplication_stats(integration_findings, plugin_id_counter)

        # Generate OCSF data if requested
        ocsf_data = self._generate_ocsf_data(findings, service_name) if ocsf_format else None

        # Generate evidence if requested
        evidence_record = None
        if generate_evidence:
            evidence_record = self._generate_evidence_record(findings, service_name, ssp_id, control_ids, ocsf_data)

        return integration_findings, evidence_record

    def _group_findings_by_plugin_id(self, findings: List[IntegrationFinding]) -> dict:
        """Group findings by their plugin_id."""
        findings_by_plugin: dict = {}
        for finding in findings:
            plugin_id = finding.plugin_id or "no_plugin_id"
            if not finding.plugin_id:
                logger.warning(f"Finding without plugin_id: {finding.title}")
            if plugin_id not in findings_by_plugin:
                findings_by_plugin[plugin_id] = []
            findings_by_plugin[plugin_id].append(finding)
        return findings_by_plugin

    def _merge_grouped_findings(self, grouped_findings: List[IntegrationFinding]) -> IntegrationFinding:
        """Merge multiple findings with same plugin_id into a single finding."""
        base_finding = grouped_findings[0]

        # Collect unique affected resources/assets and external IDs
        affected_resources = set()
        asset_identifiers = set()
        all_external_ids = set()

        for finding in grouped_findings:
            if finding.asset_identifier:
                affected_resources.add(finding.asset_identifier)
                asset_identifiers.add(finding.asset_identifier)
            if finding.external_id:
                all_external_ids.add(finding.external_id)

        # Update base finding with consolidated information
        base_finding.issue_asset_identifier_value = ", ".join(sorted(affected_resources))
        base_finding.asset_identifier = ", ".join(sorted(asset_identifiers))

        # Add consolidated finding IDs to comments
        if all_external_ids:
            finding_ids_text = f"\n\n<strong>Consolidated Finding IDs ({len(all_external_ids)}):</strong><br/>"
            finding_ids_text += "<br/>".join(sorted(all_external_ids)[:50])
            if len(all_external_ids) > 50:
                finding_ids_text += f"<br/>...and {len(all_external_ids) - 50} more"
            base_finding.comments = (base_finding.comments or "") + finding_ids_text

        # Update title with resource count
        resource_count = len(affected_resources)
        if resource_count > 1:
            base_finding.title = f"{base_finding.title} ({resource_count} resources affected)"

        return base_finding

    def consolidate_findings_by_plugin_id(self, findings: List[IntegrationFinding]) -> List[IntegrationFinding]:
        """
        Consolidate findings with the same plugin_id into single findings.

        In consolidated mode, multiple findings with the same plugin_id represent
        the same security control failure across different resources. This method
        groups them together and merges their information.

        :param List[IntegrationFinding] findings: List of integration findings
        :return: Consolidated list of findings (one per unique plugin_id)
        :rtype: List[IntegrationFinding]
        """
        from regscale.integrations.scanner_integration import ScannerVariables

        # Check if we're in consolidated mode
        issue_creation_mode = ScannerVariables.issueCreation.lower()
        if issue_creation_mode != "consolidated":
            logger.info("Not in consolidated mode, skipping finding consolidation")
            return findings

        logger.info(f"Consolidating {len(findings)} findings by plugin_id...")

        # Group findings by plugin_id
        findings_by_plugin = self._group_findings_by_plugin_id(findings)

        # Consolidate findings with same plugin_id
        consolidated_findings = []
        for plugin_id, grouped_findings in findings_by_plugin.items():
            if plugin_id == "no_plugin_id":
                consolidated_findings.extend(grouped_findings)
            elif len(grouped_findings) == 1:
                consolidated_findings.append(grouped_findings[0])
            else:
                consolidated_findings.append(self._merge_grouped_findings(grouped_findings))

        if consolidated_findings:
            logger.info(
                f"Consolidated {len(findings)} findings down to {len(consolidated_findings)} "
                f"(consolidation ratio: {len(findings) / len(consolidated_findings):.2f}x)"
            )
        else:
            logger.info("No findings to consolidate")

        return consolidated_findings

    def parse_resource_to_asset(self, resource: dict, finding: dict) -> Optional[IntegrationAsset]:
        """
        Parse AWS Security Hub resource to RegScale IntegrationAsset format.

        :param dict resource: AWS Security Hub resource from finding
        :param dict finding: AWS Security Hub finding for additional context
        :return: RegScale IntegrationAsset or None if resource type not supported
        :rtype: Optional[IntegrationAsset]
        """
        try:
            resource_type = resource.get("Type", "")
            resource_id = resource.get("Id", "")

            if not resource_type or not resource_id:
                logger.warning("Resource missing Type or Id, skipping asset creation")
                return None

            # Map resource types to parser methods
            parser_map = {
                "AwsEc2SecurityGroup": self._parse_security_group_resource,
                "AwsEc2Subnet": self._parse_subnet_resource,
                "AwsIamUser": self._parse_iam_user_resource,
                "AwsEc2Instance": self._parse_ec2_instance_resource,
                "AwsS3Bucket": self._parse_s3_bucket_resource,
                "AwsRdsDbInstance": self._parse_rds_instance_resource,
                "AwsLambdaFunction": self._parse_lambda_function_resource,
                "AwsEcrRepository": self._parse_ecr_repository_resource,
            }

            parser_method = parser_map.get(resource_type)
            if parser_method:
                return parser_method(resource, finding)
            else:
                # Create a generic asset for unsupported resource types
                return self._parse_generic_resource(resource)

        except Exception as e:
            logger.error(f"Error parsing resource to asset: {str(e)}", exc_info=True)
            return None

    def _parse_security_group_resource(self, resource: dict, finding: dict) -> IntegrationAsset:
        """Parse AWS EC2 Security Group resource to IntegrationAsset."""
        details = resource.get("Details", {}).get("AwsEc2SecurityGroup", {})
        resource_id = resource.get("Id", "")
        region = resource.get("Region", "us-east-1")
        # Tags also available in details

        # Extract security group ID from ARN
        sg_id = self.extract_name_from_arn(resource_id) or details.get("GroupId", "")
        group_name = details.get("GroupName", sg_id)

        name = f"Security Group: {group_name}"
        description = f"AWS EC2 Security Group {group_name} ({sg_id})"

        # Build notes with security group rules
        notes_parts = []
        if ingress_rules := details.get("IpPermissions", []):
            notes_parts.append(f"Ingress Rules: {len(ingress_rules)}")
        if egress_rules := details.get("IpPermissionsEgress", []):
            notes_parts.append(f"Egress Rules: {len(egress_rules)}")
        if vpc_id := details.get("VpcId"):
            notes_parts.append(f"VPC: {vpc_id}")

        notes = "; ".join(notes_parts) if notes_parts else "AWS Security Group"

        # Create console URI
        uri = f"https://console.aws.amazon.com/ec2/v2/home?region={region}#SecurityGroups:groupId={sg_id}"

        return IntegrationAsset(
            name=name,
            identifier=resource_id,
            asset_type=regscale_models.AssetType.Firewall,  # Security groups act like firewalls
            asset_category=regscale_models.AssetCategory.Software,
            component_type=regscale_models.ComponentType.Software,
            component_names=["Security Groups"],
            parent_id=self.plan_id,
            parent_module="securityplans",
            status=regscale_models.AssetStatus.Active,
            description=description,
            location=region,
            notes=notes,
            manufacturer="AWS",
            aws_identifier=resource_id,  # Use full ARN for asset matching
            vlan_id=details.get("VpcId"),
            uri=uri,
            source_data=resource,
            is_virtual=True,
        )

    def _parse_subnet_resource(self, resource: dict, finding: dict) -> IntegrationAsset:
        """Parse AWS EC2 Subnet resource to IntegrationAsset."""
        details = resource.get("Details", {}).get("AwsEc2Subnet", {})
        resource_id = resource.get("Id", "")
        region = resource.get("Region", "us-east-1")

        subnet_id = self.extract_name_from_arn(resource_id) or details.get("SubnetId", "")
        cidr_block = details.get("CidrBlock", "")
        az = details.get("AvailabilityZone", "")

        name = f"Subnet: {subnet_id}"
        if cidr_block:
            name += f" ({cidr_block})"

        description = f"AWS EC2 Subnet {subnet_id} in {az}"

        # Build notes with subnet details
        notes_parts = []
        if cidr_block:
            notes_parts.append(f"CIDR: {cidr_block}")
        if az:
            notes_parts.append(f"AZ: {az}")
        if available_ips := details.get("AvailableIpAddressCount"):
            notes_parts.append(f"Available IPs: {available_ips}")
        if details.get("MapPublicIpOnLaunch"):
            notes_parts.append("Auto-assigns public IP")

        notes = "; ".join(notes_parts) if notes_parts else "AWS Subnet"

        # Create console URI
        uri = f"https://console.aws.amazon.com/vpc/home?region={region}#SubnetDetails:subnetId={subnet_id}"

        return IntegrationAsset(
            name=name,
            identifier=resource_id,
            asset_type=regscale_models.AssetType.NetworkRouter,  # Subnets are network infrastructure
            asset_category=regscale_models.AssetCategory.Hardware,
            component_type=regscale_models.ComponentType.Hardware,
            component_names=["Subnets"],
            parent_id=self.plan_id,
            parent_module="securityplans",
            status=regscale_models.AssetStatus.Active,
            description=description,
            location=region,
            notes=notes,
            manufacturer="AWS",
            aws_identifier=resource_id,  # Use full ARN for asset matching
            vlan_id=details.get("VpcId"),
            uri=uri,
            source_data=resource,
            is_virtual=True,
            is_public_facing=details.get("MapPublicIpOnLaunch", False),
        )

    def _parse_iam_user_resource(self, resource: dict, finding: dict) -> IntegrationAsset:
        """Parse AWS IAM User resource to IntegrationAsset."""
        resource_id = resource.get("Id", "")
        region = resource.get("Region", "us-east-1")

        # Extract username from ARN
        username = self.extract_name_from_arn(resource_id) or "Unknown User"

        name = f"IAM User: {username}"
        description = f"AWS IAM User {username}"

        # Create console URI
        uri = f"https://console.aws.amazon.com/iam/home?region={region}#/users/{username}"

        return IntegrationAsset(
            name=name,
            identifier=resource_id,
            asset_type=regscale_models.AssetType.Other,  # IAM users don't fit standard asset types
            asset_category=regscale_models.AssetCategory.Software,
            component_type=regscale_models.ComponentType.Software,
            component_names=["IAM Users"],
            parent_id=self.plan_id,
            parent_module="securityplans",
            status=regscale_models.AssetStatus.Active,
            description=description,
            location=region,
            notes="AWS IAM User Account",
            manufacturer="AWS",
            aws_identifier=resource_id,  # Use full ARN for asset matching
            uri=uri,
            source_data=resource,
            is_virtual=True,
        )

    def _parse_ec2_instance_resource(self, resource: dict, finding: dict) -> IntegrationAsset:
        """Parse AWS EC2 Instance resource to IntegrationAsset."""
        details = resource.get("Details", {}).get("AwsEc2Instance", {})
        resource_id = resource.get("Id", "")
        region = resource.get("Region", "us-east-1")
        tags = resource.get("Tags", {})

        instance_id = self.extract_name_from_arn(resource_id) or details.get("InstanceId", "")
        instance_type = details.get("Type", "")

        # Try to get a friendly name from tags
        friendly_name = tags.get("Name", instance_id)
        name = f"EC2: {friendly_name}"
        if instance_type:
            name += f" ({instance_type})"

        description = f"AWS EC2 Instance {instance_id}"

        # Create console URI
        uri = f"https://console.aws.amazon.com/ec2/v2/home?region={region}#InstanceDetails:instanceId={instance_id}"

        return IntegrationAsset(
            name=name,
            identifier=resource_id,
            asset_type=regscale_models.AssetType.VM,
            asset_category=regscale_models.AssetCategory.Hardware,
            component_type=regscale_models.ComponentType.Hardware,
            component_names=[EC_INSTANCES],
            parent_id=self.plan_id,
            parent_module="securityplans",
            status=regscale_models.AssetStatus.Active,
            description=description,
            location=region,
            notes=f"AWS EC2 Instance - {instance_type}",
            model=instance_type,
            manufacturer="AWS",
            aws_identifier=resource_id,  # Use full ARN for asset matching
            vlan_id=details.get("SubnetId"),
            uri=uri,
            source_data=resource,
            is_virtual=True,
        )

    def _parse_s3_bucket_resource(self, resource: dict, finding: dict) -> IntegrationAsset:
        """Parse AWS S3 Bucket resource to IntegrationAsset."""
        details = resource.get("Details", {}).get("AwsS3Bucket", {})
        resource_id = resource.get("Id", "")
        region = resource.get("Region", "us-east-1")

        bucket_name = self.extract_name_from_arn(resource_id) or details.get("Name", "")

        name = f"S3 Bucket: {bucket_name}"
        description = f"AWS S3 Bucket {bucket_name}"

        # Create console URI
        uri = f"https://s3.console.aws.amazon.com/s3/buckets/{bucket_name}?region={region}"

        return IntegrationAsset(
            name=name,
            identifier=resource_id,
            asset_type=regscale_models.AssetType.Other,  # S3 buckets are storage, closest to Other
            asset_category=regscale_models.AssetCategory.Software,
            component_type=regscale_models.ComponentType.Software,
            component_names=["S3 Buckets"],
            parent_id=self.plan_id,
            parent_module="securityplans",
            status=regscale_models.AssetStatus.Active,
            description=description,
            location=region,
            notes="AWS S3 Storage Bucket",
            manufacturer="AWS",
            aws_identifier=resource_id,  # Use full ARN for asset matching
            uri=uri,
            source_data=resource,
            is_virtual=True,
        )

    def _parse_rds_instance_resource(self, resource: dict, finding: dict) -> IntegrationAsset:
        """Parse AWS RDS Instance resource to IntegrationAsset."""
        details = resource.get("Details", {}).get("AwsRdsDbInstance", {})
        resource_id = resource.get("Id", "")
        region = resource.get("Region", "us-east-1")

        db_identifier = self.extract_name_from_arn(resource_id) or details.get("DbInstanceIdentifier", "")
        db_class = details.get("DbInstanceClass", "")
        engine = details.get("Engine", "")

        name = f"RDS: {db_identifier}"
        if engine:
            name += f" ({engine})"

        description = f"AWS RDS Database Instance {db_identifier}"

        # Create console URI
        uri = f"https://console.aws.amazon.com/rds/home?region={region}#database:id={db_identifier}"

        return IntegrationAsset(
            name=name,
            identifier=resource_id,
            asset_type=regscale_models.AssetType.VM,  # RDS instances are virtual database servers
            asset_category=regscale_models.AssetCategory.Software,
            component_type=regscale_models.ComponentType.Software,
            component_names=["RDS Instances"],
            parent_id=self.plan_id,
            parent_module="securityplans",
            status=regscale_models.AssetStatus.Active,
            description=description,
            location=region,
            notes=f"AWS RDS Database - {engine} {db_class}",
            model=db_class,
            software_name=engine,
            manufacturer="AWS",
            aws_identifier=resource_id,  # Use full ARN for asset matching
            uri=uri,
            source_data=resource,
            is_virtual=True,
        )

    def _parse_lambda_function_resource(self, resource: dict, finding: dict) -> IntegrationAsset:
        """Parse AWS Lambda Function resource to IntegrationAsset."""
        details = resource.get("Details", {}).get("AwsLambdaFunction", {})
        resource_id = resource.get("Id", "")
        region = resource.get("Region", "us-east-1")

        function_name = self.extract_name_from_arn(resource_id) or details.get("FunctionName", "")
        runtime = details.get("Runtime", "")

        name = f"Lambda: {function_name}"
        if runtime:
            name += f" ({runtime})"

        description = f"AWS Lambda Function {function_name}"

        # Create console URI
        uri = f"https://console.aws.amazon.com/lambda/home?region={region}#/functions/{function_name}"

        return IntegrationAsset(
            name=name,
            identifier=resource_id,
            asset_type=regscale_models.AssetType.Other,  # Lambda functions are serverless, closest to Other
            asset_category=regscale_models.AssetCategory.Software,
            component_type=regscale_models.ComponentType.Software,
            component_names=["Lambda Functions"],
            parent_id=self.plan_id,
            parent_module="securityplans",
            status=regscale_models.AssetStatus.Active,
            description=description,
            location=region,
            notes=f"AWS Lambda Function - {runtime}",
            software_name=runtime,
            manufacturer="AWS",
            aws_identifier=resource_id,  # Use full ARN for asset matching
            uri=uri,
            source_data=resource,
            is_virtual=True,
        )

    def _parse_ecr_repository_resource(self, resource: dict, finding: dict) -> IntegrationAsset:
        """Parse AWS ECR Repository resource to IntegrationAsset."""
        details = resource.get("Details", {}).get("AwsEcrRepository", {})
        resource_id = resource.get("Id", "")
        region = resource.get("Region", "us-east-1")

        repo_name = self.extract_name_from_arn(resource_id) or details.get("RepositoryName", "")

        name = f"ECR Repository: {repo_name}"
        description = f"AWS ECR Container Repository {repo_name}"

        # Create console URI
        uri = f"https://console.aws.amazon.com/ecr/repositories/{repo_name}?region={region}"

        return IntegrationAsset(
            name=name,
            identifier=resource_id,
            asset_type=regscale_models.AssetType.Other,  # ECR repositories are container registries
            asset_category=regscale_models.AssetCategory.Software,
            component_type=regscale_models.ComponentType.Software,
            component_names=["ECR Repositories"],
            parent_id=self.plan_id,
            parent_module="securityplans",
            status=regscale_models.AssetStatus.Active,
            description=description,
            location=region,
            notes="AWS ECR Container Repository",
            manufacturer="AWS",
            aws_identifier=resource_id,  # Use full ARN for asset matching
            uri=uri,
            source_data=resource,
            is_virtual=True,
        )

    def _parse_generic_resource(self, resource: dict) -> IntegrationAsset:
        """Parse generic AWS resource to IntegrationAsset."""
        resource_type = resource.get("Type", "Unknown")
        resource_id = resource.get("Id", "")
        region = resource.get("Region", "us-east-1")

        identifier = self.extract_name_from_arn(resource_id) or resource_id

        name = f"{resource_type}: {identifier}"
        description = f"AWS {resource_type} {identifier}"

        return IntegrationAsset(
            name=name,
            identifier=resource_id,
            asset_type=regscale_models.AssetType.Other,
            asset_category=regscale_models.AssetCategory.Software,
            component_type=regscale_models.ComponentType.Software,
            component_names=[f"{resource_type}s"],
            parent_id=self.plan_id,
            parent_module="securityplans",
            status=regscale_models.AssetStatus.Active,
            description=description,
            location=region,
            notes=f"AWS {resource_type}",
            manufacturer="AWS",
            aws_identifier=resource_id,  # Use full ARN for asset matching
            source_data=resource,
            is_virtual=True,
        )
