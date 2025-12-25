"""AWS resource inventory collection module."""

import logging
import os
from typing import Dict, Any, Optional

from regscale.integrations.commercial.aws.inventory.base import BaseCollector
from regscale.integrations.commercial.aws.inventory.resources.analytics import AnalyticsCollector
from regscale.integrations.commercial.aws.inventory.resources.applications import ApplicationCollector
from regscale.integrations.commercial.aws.inventory.resources.compute import ComputeCollector
from regscale.integrations.commercial.aws.inventory.resources.config import ConfigCollector
from regscale.integrations.commercial.aws.inventory.resources.containers import ContainerCollector
from regscale.integrations.commercial.aws.inventory.resources.database import DatabaseCollector
from regscale.integrations.commercial.aws.inventory.resources.developer_tools import DeveloperToolsCollector
from regscale.integrations.commercial.aws.inventory.resources.integration import IntegrationCollector
from regscale.integrations.commercial.aws.inventory.resources.machine_learning import MachineLearningCollector
from regscale.integrations.commercial.aws.inventory.resources.networking import NetworkingCollector
from regscale.integrations.commercial.aws.inventory.resources.security import SecurityCollector
from regscale.integrations.commercial.aws.inventory.resources.storage import StorageCollector

logger = logging.getLogger("regscale")


class AWSInventoryCollector:
    """Collects inventory of AWS resources."""

    def __init__(
        self,
        region: str = os.getenv("AWS_REGION", "us-east-1"),
        profile: Optional[str] = None,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        aws_session_token: Optional[str] = None,
        account_id: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        enabled_services: Optional[Dict[str, bool]] = None,
        collect_findings: bool = True,
    ):
        """
        Initialize the AWS inventory collector.

        :param str region: AWS region to collect inventory from
        :param str profile: Optional AWS profile name from ~/.aws/credentials
        :param str aws_access_key_id: Optional AWS access key ID (overrides profile)
        :param str aws_secret_access_key: Optional AWS secret access key (overrides profile)
        :param str aws_session_token: Optional AWS session token (overrides profile)
        :param str account_id: Optional AWS account ID to filter resources
        :param dict tags: Optional dictionary of tag key-value pairs to filter resources
        :param dict enabled_services: Optional dictionary of service names to boolean flags for enabling/disabling collection
        :param bool collect_findings: Whether to collect security findings (GuardDuty, Security Hub, Inspector). Default True.
        """
        import boto3

        self.region = region
        self.account_id = account_id
        self.tags = tags
        self.enabled_services = self._get_enabled_services(enabled_services)

        # If explicit credentials are provided, use them; otherwise use profile
        if aws_access_key_id or aws_secret_access_key:
            self.session = boto3.Session(
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                region_name=region,
                aws_session_token=aws_session_token,
            )
        else:
            # Use profile or default credential chain
            self.session = boto3.Session(
                profile_name=profile,
                region_name=region,
            )

        # Initialize collectors based on enabled services
        compute_config = self.enabled_services.get("compute", {"enabled": True, "services": {}})
        self.compute = (
            ComputeCollector(self.session, self.region, account_id, tags, compute_config.get("services", {}))
            if compute_config.get("enabled", True)
            else None
        )

        storage_config = self.enabled_services.get("storage", {"enabled": True, "services": {}})
        self.storage = (
            StorageCollector(self.session, self.region, account_id, tags, storage_config.get("services", {}))
            if storage_config.get("enabled", True)
            else None
        )

        database_config = self.enabled_services.get("database", {"enabled": True, "services": {}})
        self.database = (
            DatabaseCollector(self.session, self.region, account_id, tags, database_config.get("services", {}))
            if database_config.get("enabled", True)
            else None
        )

        networking_config = self.enabled_services.get("networking", {"enabled": True, "services": {}})
        self.networking = (
            NetworkingCollector(self.session, self.region, account_id, tags, networking_config.get("services", {}))
            if networking_config.get("enabled", True)
            else None
        )

        security_config = self.enabled_services.get("security", {"enabled": True, "services": {}})
        self.security = (
            SecurityCollector(
                self.session, self.region, account_id, tags, security_config.get("services", {}), collect_findings
            )
            if security_config.get("enabled", True)
            else None
        )

        integration_config = self.enabled_services.get("integration", {"enabled": True, "services": {}})
        self.integration = (
            IntegrationCollector(self.session, self.region, account_id, tags, integration_config.get("services", {}))
            if integration_config.get("enabled", True)
            else None
        )

        containers_config = self.enabled_services.get("containers", {"enabled": True, "services": {}})
        self.containers = (
            ContainerCollector(self.session, self.region, account_id, tags, containers_config.get("services", {}))
            if containers_config.get("enabled", True)
            else None
        )

        config_config = self.enabled_services.get("config", {"enabled": True, "services": {}})
        self.config = (
            ConfigCollector(self.session, self.region, account_id, tags) if config_config.get("enabled", True) else None
        )

        # New collectors for analytics, ML, developer tools, and applications
        analytics_config = self.enabled_services.get("analytics", {"enabled": True, "services": {}})
        self.analytics = (
            AnalyticsCollector(self.session, self.region, account_id, tags, analytics_config.get("services", {}))
            if analytics_config.get("enabled", True)
            else None
        )

        ml_config = self.enabled_services.get("machine_learning", {"enabled": True, "services": {}})
        self.machine_learning = (
            MachineLearningCollector(self.session, self.region, account_id, tags, ml_config.get("services", {}))
            if ml_config.get("enabled", True)
            else None
        )

        devtools_config = self.enabled_services.get("developer_tools", {"enabled": True, "services": {}})
        self.developer_tools = (
            DeveloperToolsCollector(self.session, self.region, account_id, tags, devtools_config.get("services", {}))
            if devtools_config.get("enabled", True)
            else None
        )

        applications_config = self.enabled_services.get("applications", {"enabled": True, "services": {}})
        self.applications = (
            ApplicationCollector(self.session, self.region, account_id, tags, applications_config.get("services", {}))
            if applications_config.get("enabled", True)
            else None
        )

    def _get_enabled_services(self, enabled_services: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get enabled services configuration with support for nested structure.
        Supports both simple (category: bool) and nested (category: {enabled: bool, services: {...}}) formats.

        :param dict enabled_services: Optional dictionary of service names to boolean flags or nested config
        :return: Dictionary of service configurations
        :rtype: Dict[str, Any]
        """
        # Default all services to enabled with all sub-services enabled
        default_services = {
            "compute": {
                "enabled": True,
                "services": {
                    "ec2": True,
                    "lambda": True,
                    "ecs": True,
                    "systems_manager": True,
                    "batch": True,
                    "app_runner": True,
                    "elastic_beanstalk": True,
                    "lightsail": True,
                },
            },
            "storage": {
                "enabled": True,
                "services": {
                    "s3": True,
                    "ebs": True,
                    "efs": True,
                    "fsx": True,
                    "storage_gateway": True,
                    "backup": True,
                },
            },
            "database": {
                "enabled": True,
                "services": {
                    "rds": True,
                    "dynamodb": True,
                    "elasticache": True,
                    "neptune": True,
                    "docdb": True,
                    "redshift": True,
                    "keyspaces": True,
                    "timestream": True,
                    "qldb": True,
                },
            },
            "networking": {
                "enabled": True,
                "services": {
                    "vpc": True,
                    "elastic_ips": True,
                    "load_balancers": True,
                    "cloudfront": True,
                    "route53": True,
                    "direct_connect": True,
                    "transit_gateway": True,
                    "vpn": True,
                    "global_accelerator": True,
                    "network_firewall": True,
                    "route53_resolver": True,
                },
            },
            "security": {
                "enabled": True,
                "services": {
                    "iam": True,
                    "kms": True,
                    "secrets_manager": True,
                    "waf": True,
                    "acm": True,
                    "cloudtrail": True,
                    "config": True,
                    "guardduty": True,
                    "securityhub": True,
                    "inspector": True,
                    "audit_manager": True,
                },
            },
            "integration": {
                "enabled": True,
                "services": {"api_gateway": True, "sns": True, "sqs": True, "eventbridge": True},
            },
            "containers": {"enabled": True, "services": {"ecr": True}},
            "config": {"enabled": True, "services": {}},
            "analytics": {
                "enabled": True,
                "services": {
                    "emr": True,
                    "kinesis_streams": True,
                    "kinesis_firehose": True,
                    "glue": True,
                    "athena": True,
                    "msk": True,
                },
            },
            "machine_learning": {
                "enabled": True,
                "services": {
                    "sagemaker_endpoints": True,
                    "sagemaker_models": True,
                    "sagemaker_notebooks": True,
                    "sagemaker_training_jobs": True,
                    "rekognition": True,
                    "comprehend": True,
                },
            },
            "developer_tools": {
                "enabled": True,
                "services": {
                    "codepipeline": True,
                    "codebuild": True,
                    "codedeploy": True,
                    "codecommit": True,
                },
            },
            "applications": {
                "enabled": True,
                "services": {
                    "step_functions": True,
                    "appsync": True,
                    "workspaces": True,
                    "iot": True,
                },
            },
        }

        # If no config provided, return defaults
        if enabled_services is None:
            return default_services

        # Process configuration - support both simple and nested formats
        merged_config = {}
        for category, default_value in default_services.items():
            if category not in enabled_services:
                # Category not specified, use default
                merged_config[category] = default_value
            elif isinstance(enabled_services[category], bool):
                # Simple format: security: true/false
                # Convert to nested format with all services matching the category setting
                merged_config[category] = {
                    "enabled": enabled_services[category],
                    "services": {
                        service: enabled_services[category] for service in default_value.get("services", {}).keys()
                    },
                }
            elif isinstance(enabled_services[category], dict):
                # Nested format: security: {enabled: true, services: {...}}
                category_config = enabled_services[category]
                enabled_flag = category_config.get("enabled", True)
                provided_services = category_config.get("services", {})

                # Merge provided services with defaults
                merged_services = default_value.get("services", {}).copy()
                merged_services.update(provided_services)

                merged_config[category] = {"enabled": enabled_flag, "services": merged_services}
            else:
                # Invalid format, use default
                logger.warning(f"Invalid configuration format for category '{category}', using defaults")
                merged_config[category] = default_value

        # Log disabled categories and services
        disabled_categories = [name for name, config in merged_config.items() if not config.get("enabled", True)]
        if disabled_categories:
            logger.info(f"AWS inventory collection disabled for categories: {', '.join(disabled_categories)}")

        for category, config in merged_config.items():
            if config.get("enabled", True):
                disabled_services = [service for service, enabled in config.get("services", {}).items() if not enabled]
                if disabled_services:
                    logger.info(
                        f"AWS inventory collection disabled for {category} services: {', '.join(disabled_services)}"
                    )

        return merged_config

    def collect_all(self) -> Dict[str, Any]:
        """
        Collect all AWS resources from enabled collectors.

        :return: Dictionary containing all AWS resource information
        :rtype: Dict[str, Any]
        """
        inventory = {}
        collectors = [
            self.compute,
            self.storage,
            self.database,
            self.networking,
            self.security,
            self.integration,
            self.containers,
            self.config,
            self.analytics,
            self.machine_learning,
            self.developer_tools,
            self.applications,
        ]

        # Filter out None collectors (disabled services)
        active_collectors = [c for c in collectors if c is not None]

        logger.info(f"Collecting AWS inventory from {len(active_collectors)} enabled service(s)")

        for collector in active_collectors:
            try:
                resources = collector.collect()
                inventory.update(resources)
            except Exception as e:
                from regscale.core.app.utils.app_utils import create_logger

                # Handle or log the exception as needed
                create_logger().error(f"Error collecting resource(s) from {collector.__class__.__name__}: {e}")

        return inventory


def collect_all_inventory(
    region: str = os.getenv("AWS_REGION", "us-east-1"),
    profile: Optional[str] = None,
    aws_access_key_id: Optional[str] = None,
    aws_secret_access_key: Optional[str] = None,
    aws_session_token: Optional[str] = None,
    account_id: Optional[str] = None,
    tags: Optional[Dict[str, str]] = None,
    enabled_services: Optional[Dict[str, bool]] = None,
    collect_findings: bool = True,
) -> Dict[str, Any]:
    """
    Collect inventory of all AWS resources.

    :param str region: AWS region to collect inventory from
    :param str profile: Optional AWS profile name from ~/.aws/credentials
    :param str aws_access_key_id: Optional AWS access key ID (overrides profile)
    :param str aws_secret_access_key: Optional AWS secret access key (overrides profile)
    :param str aws_session_token: Optional AWS session token (overrides profile)
    :param str account_id: Optional AWS account ID to filter resources
    :param dict tags: Optional dictionary of tag key-value pairs to filter resources
    :param dict enabled_services: Optional dictionary of service names to boolean flags for enabling/disabling collection
    :param bool collect_findings: Whether to collect security findings (GuardDuty, Security Hub, Inspector). Default True.
    :return: Dictionary containing all AWS resource information
    :rtype: Dict[str, Any]
    """
    collector = AWSInventoryCollector(
        region,
        profile,
        aws_access_key_id,
        aws_secret_access_key,
        aws_session_token,
        account_id,
        tags,
        enabled_services,
        collect_findings,
    )
    return collector.collect_all()


if __name__ == "__main__":
    collect_all_inventory(
        region="us-east-1",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        aws_session_token=os.getenv("AWS_SESSION_TOKEN"),
    )
