"""AWS compute resource collectors."""

import logging
from typing import Dict, List, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    import boto3

from regscale.integrations.commercial.aws.inventory.resources.systems_manager import SystemsManagerCollector
from regscale.integrations.commercial.aws.inventory.base import BaseCollector

logger = logging.getLogger("regscale")


class ComputeCollector(BaseCollector):
    """Collector for AWS compute resources."""

    def __init__(
        self,
        session: "boto3.Session",
        region: str,
        account_id: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        enabled_services: Optional[Dict[str, bool]] = None,
    ):
        """
        Initialize the compute collector.

        :param boto3.Session session: AWS session
        :param str region: AWS region
        :param str account_id: Optional AWS account ID to filter resources
        :param dict tags: Optional tags to filter resources (key-value pairs)
        :param dict enabled_services: Optional dict of service names to boolean flags for enabling/disabling collection
        """
        super().__init__(session, region)
        self.account_id = account_id
        self.tags = tags or {}
        self.enabled_services = enabled_services or {}
        self.ec2_client = self._get_client("ec2")
        self.logger = logging.getLogger("regscale")

    @staticmethod
    def _collect_instance_ami_mapping(paginator) -> Dict[str, str]:
        """
        Collect mapping of instance IDs to their AMI IDs.

        :param paginator: EC2 describe_instances paginator
        :return: Dictionary mapping instance IDs to AMI IDs
        :rtype: Dict[str, str]
        """
        instance_ami_map = {}
        for page in paginator.paginate():
            for reservation in page.get("Reservations", []):
                for instance in reservation.get("Instances", []):
                    if image_id := instance.get("ImageId"):
                        instance_ami_map[instance["InstanceId"]] = image_id
        return instance_ami_map

    def _get_ami_details(self, ami_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Get details for a list of AMI IDs.

        :param ami_ids: List of AMI IDs to describe
        :return: Dictionary of AMI details keyed by AMI ID
        :rtype: Dict[str, Dict[str, Any]]
        """
        ami_details = {}
        for i in range(0, len(ami_ids), 100):
            batch = ami_ids[i : i + 100]
            try:
                ami_response = self.ec2_client.describe_images(ImageIds=batch)
                for image in ami_response.get("Images", []):
                    ami_details[image["ImageId"]] = {
                        "Name": image.get("Name"),
                        "Description": image.get("Description"),
                        "Architecture": image.get("Architecture"),
                        "RootDeviceType": image.get("RootDeviceType"),
                        "VirtualizationType": image.get("VirtualizationType"),
                        "PlatformDetails": image.get("PlatformDetails"),
                        "UsageOperation": image.get("UsageOperation"),
                    }
            except Exception as e:
                self.logger.warning(f"Error describing AMIs {batch}: {str(e)}")
        return ami_details

    def _build_instance_data(self, instance: Dict[str, Any], ami_details: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Build instance data dictionary with AMI details.

        :param instance: Raw instance data
        :param ami_details: Dictionary of AMI details
        :return: Processed instance data
        :rtype: Dict[str, Any]
        """
        instance_data = {
            "Region": self.region,
            "InstanceId": instance.get("InstanceId"),
            "InstanceType": instance.get("InstanceType"),
            "LaunchTime": instance.get("LaunchTime"),
            "State": instance.get("State", {}).get("Name"),
            "Platform": instance.get("Platform"),
            "PlatformDetails": instance.get("PlatformDetails"),
            "PrivateIpAddress": instance.get("PrivateIpAddress"),
            "PublicIpAddress": instance.get("PublicIpAddress"),
            "Tags": instance.get("Tags", []),
            "VpcId": instance.get("VpcId"),
            "SubnetId": instance.get("SubnetId"),
            "ImageId": instance.get("ImageId"),
            "Architecture": instance.get("Architecture"),
            "CpuOptions": instance.get("CpuOptions", {}),
            "BlockDeviceMappings": instance.get("BlockDeviceMappings", []),
        }

        if image_id := instance.get("ImageId"):
            if ami_info := ami_details.get(image_id):
                instance_data["ImageInfo"] = ami_info

        return instance_data

    def get_ec2_instances(self) -> List[Dict[str, Any]]:
        """
        Get information about EC2 instances in the region.

        :return: List of EC2 instance information
        :rtype: List[Dict[str, Any]]
        """
        instances = []
        try:
            paginator = self.ec2_client.get_paginator("describe_instances")

            # Collect instance to AMI mapping
            instance_ami_map = self._collect_instance_ami_mapping(paginator)

            # Get AMI details
            unique_amis = list(set(instance_ami_map.values()))
            ami_details = self._get_ami_details(unique_amis) if unique_amis else {}

            # Collect instance information
            for page in paginator.paginate():
                for reservation in page.get("Reservations", []):
                    # Get account ID from reservation
                    owner_id = reservation.get("OwnerId", "")
                    for instance in reservation.get("Instances", []):
                        instance_data = self._build_instance_data(instance, ami_details)
                        # Add owner ID for ARN construction
                        instance_data["OwnerId"] = owner_id
                        instances.append(instance_data)

        except Exception as e:
            self.logger.error(f"Error getting EC2 instances in region {self.region}: {str(e)}")
            self.logger.error(f"{str(e)}", exc_info=True)

        return instances

    def get_lambda_functions(self) -> List[Dict[str, Any]]:
        """
        Get information about Lambda functions.

        :return: List of Lambda function information
        :rtype: List[Dict[str, Any]]
        """
        functions = []
        try:
            lambda_client = self._get_client("lambda")
            paginator = lambda_client.get_paginator("list_functions")

            for page in paginator.paginate():
                for function in page.get("Functions", []):
                    functions.append(
                        {
                            "Region": self.region,
                            "FunctionName": function.get("FunctionName"),
                            "FunctionArn": function.get("FunctionArn"),
                            "Runtime": function.get("Runtime"),
                            "Handler": function.get("Handler"),
                            "CodeSize": function.get("CodeSize"),
                            "Description": function.get("Description"),
                            "Timeout": function.get("Timeout"),
                            "MemorySize": function.get("MemorySize"),
                            "LastModified": function.get("LastModified"),
                            "Role": function.get("Role"),
                        }
                    )
        except Exception as e:
            self._handle_error(e, "Lambda functions")
        return functions

    def get_ecs_clusters(self) -> List[Dict[str, Any]]:
        """
        Get information about ECS clusters and services.

        :return: List of ECS cluster information
        :rtype: List[Dict[str, Any]]
        """
        clusters = []
        try:
            ecs = self._get_client("ecs")
            cluster_arns = ecs.list_clusters().get("clusterArns", [])

            for cluster_arn in cluster_arns:
                cluster_info = ecs.describe_clusters(clusters=[cluster_arn])["clusters"][0]
                services = []

                # Get services for each cluster
                service_paginator = ecs.get_paginator("list_services")
                for service_page in service_paginator.paginate(cluster=cluster_arn):
                    service_arns = service_page.get("serviceArns", [])
                    if service_arns:
                        service_details = ecs.describe_services(cluster=cluster_arn, services=service_arns).get(
                            "services", []
                        )
                        services.extend(service_details)

                clusters.append(
                    {
                        "Region": self.region,
                        "ClusterName": cluster_info.get("clusterName"),
                        "ClusterArn": cluster_info.get("clusterArn"),
                        "Status": cluster_info.get("status"),
                        "RegisteredContainerInstancesCount": cluster_info.get("registeredContainerInstancesCount"),
                        "RunningTasksCount": cluster_info.get("runningTasksCount"),
                        "PendingTasksCount": cluster_info.get("pendingTasksCount"),
                        "ActiveServicesCount": cluster_info.get("activeServicesCount"),
                        "Services": [
                            {
                                "ServiceName": service.get("serviceName"),
                                "ServiceArn": service.get("serviceArn"),
                                "Status": service.get("status"),
                                "DesiredCount": service.get("desiredCount"),
                                "RunningCount": service.get("runningCount"),
                                "PendingCount": service.get("pendingCount"),
                                "LaunchType": service.get("launchType"),
                            }
                            for service in services
                        ],
                    }
                )
        except Exception as e:
            self._handle_error(e, "ECS clusters")
        return clusters

    def get_systems_manager_info(self) -> Dict[str, Any]:
        """
        Get information about Systems Manager resources.

        :return: Dictionary containing Systems Manager information
        :rtype: Dict[str, Any]
        """
        try:
            ssm_collector = SystemsManagerCollector(self.session, self.region, self.account_id, self.tags)
            return ssm_collector.collect()
        except Exception as e:
            self._handle_error(e, "Systems Manager resources")
            return {
                "ManagedInstances": [],
                "Parameters": [],
                "Documents": [],
                "PatchBaselines": [],
                "MaintenanceWindows": [],
                "Associations": [],
                "InventoryEntries": [],
                "ComplianceSummary": {},
            }

    def get_batch_compute_environments(self) -> List[Dict[str, Any]]:
        """
        Get information about AWS Batch compute environments.

        :return: List of Batch compute environment information
        :rtype: List[Dict[str, Any]]
        """
        environments = []
        try:
            batch_client = self._get_client("batch")
            paginator = batch_client.get_paginator("describe_compute_environments")

            for page in paginator.paginate():
                for env in page.get("computeEnvironments", []):
                    if not self._matches_account(env.get("computeEnvironmentArn", "")):
                        continue

                    if not self._matches_tags(env.get("tags", {})):
                        continue

                    environments.append(
                        {
                            "Region": self.region,
                            "ComputeEnvironmentName": env.get("computeEnvironmentName"),
                            "ComputeEnvironmentArn": env.get("computeEnvironmentArn"),
                            "State": env.get("state"),
                            "Status": env.get("status"),
                            "Type": env.get("type"),
                            "ServiceRole": env.get("serviceRole"),
                            "Tags": env.get("tags", {}),
                        }
                    )
        except Exception as e:
            self._handle_error(e, "Batch compute environments")
        return environments

    def get_batch_job_queues(self) -> List[Dict[str, Any]]:
        """
        Get information about AWS Batch job queues.

        :return: List of Batch job queue information
        :rtype: List[Dict[str, Any]]
        """
        queues = []
        try:
            batch_client = self._get_client("batch")
            paginator = batch_client.get_paginator("describe_job_queues")

            for page in paginator.paginate():
                for queue in page.get("jobQueues", []):
                    if not self._matches_account(queue.get("jobQueueArn", "")):
                        continue

                    if not self._matches_tags(queue.get("tags", {})):
                        continue

                    queues.append(
                        {
                            "Region": self.region,
                            "JobQueueName": queue.get("jobQueueName"),
                            "JobQueueArn": queue.get("jobQueueArn"),
                            "State": queue.get("state"),
                            "Status": queue.get("status"),
                            "Priority": queue.get("priority"),
                            "Tags": queue.get("tags", {}),
                        }
                    )
        except Exception as e:
            self._handle_error(e, "Batch job queues")
        return queues

    def _process_app_runner_service(self, apprunner_client: Any, service_arn: str) -> Optional[Dict[str, Any]]:
        """
        Process a single App Runner service.

        :param apprunner_client: App Runner client
        :param str service_arn: Service ARN
        :return: Service information or None if filtered out
        :rtype: Optional[Dict[str, Any]]
        """
        if not self._matches_account(service_arn):
            return None

        try:
            service_detail = apprunner_client.describe_service(ServiceArn=service_arn)
            service = service_detail.get("Service", {})

            if not self._matches_tags(service.get("Tags", [])):
                return None

            return {
                "Region": self.region,
                "ServiceName": service.get("ServiceName"),
                "ServiceArn": service.get("ServiceArn"),
                "ServiceId": service.get("ServiceId"),
                "Status": service.get("Status"),
                "ServiceUrl": service.get("ServiceUrl"),
                "CreatedAt": service.get("CreatedAt"),
                "UpdatedAt": service.get("UpdatedAt"),
                "Tags": service.get("Tags", []),
            }
        except Exception as detail_error:
            logger.debug("Error getting App Runner service details for %s: %s", service_arn, detail_error)
            return None

    def get_app_runner_services(self) -> List[Dict[str, Any]]:
        """
        Get information about AWS App Runner services.

        :return: List of App Runner service information
        :rtype: List[Dict[str, Any]]
        """
        services = []
        try:
            apprunner_client = self._get_client("apprunner")
            next_token = None

            while True:
                if next_token:
                    response = apprunner_client.list_services(NextToken=next_token)
                else:
                    response = apprunner_client.list_services()

                for service_summary in response.get("ServiceSummaryList", []):
                    service_arn = service_summary.get("ServiceArn", "")
                    service_info = self._process_app_runner_service(apprunner_client, service_arn)
                    if service_info:
                        services.append(service_info)

                next_token = response.get("NextToken")
                if not next_token:
                    break

        except Exception as e:
            self._handle_error(e, "App Runner services")
        return services

    def get_elastic_beanstalk_applications(self) -> List[Dict[str, Any]]:
        """
        Get information about Elastic Beanstalk applications and environments.

        :return: List of Elastic Beanstalk application information
        :rtype: List[Dict[str, Any]]
        """
        applications = []
        try:
            eb_client = self._get_client("elasticbeanstalk")

            app_response = eb_client.describe_applications()
            for app in app_response.get("Applications", []):
                app_name = app.get("ApplicationName")

                env_response = eb_client.describe_environments(ApplicationName=app_name)
                environments = []

                for env in env_response.get("Environments", []):
                    env_arn = env.get("EnvironmentArn", "")

                    if not self._matches_account(env_arn):
                        continue

                    try:
                        tags_response = eb_client.list_tags_for_resource(ResourceArn=env_arn)
                        env_tags = tags_response.get("ResourceTags", [])

                        if not self._matches_tags(env_tags):
                            continue

                        environments.append(
                            {
                                "EnvironmentName": env.get("EnvironmentName"),
                                "EnvironmentId": env.get("EnvironmentId"),
                                "EnvironmentArn": env_arn,
                                "Status": env.get("Status"),
                                "Health": env.get("Health"),
                                "SolutionStackName": env.get("SolutionStackName"),
                                "PlatformArn": env.get("PlatformArn"),
                                "EndpointURL": env.get("EndpointURL"),
                                "CNAME": env.get("CNAME"),
                                "Tags": env_tags,
                            }
                        )
                    except Exception as env_error:
                        logger.debug("Error getting Elastic Beanstalk environment tags for %s: %s", env_arn, env_error)
                        continue

                if environments:
                    applications.append(
                        {
                            "Region": self.region,
                            "ApplicationName": app_name,
                            "ApplicationArn": app.get("ApplicationArn"),
                            "Description": app.get("Description"),
                            "DateCreated": app.get("DateCreated"),
                            "DateUpdated": app.get("DateUpdated"),
                            "Environments": environments,
                        }
                    )

        except Exception as e:
            self._handle_error(e, "Elastic Beanstalk applications")
        return applications

    def get_lightsail_instances(self) -> List[Dict[str, Any]]:
        """
        Get information about Amazon Lightsail instances.

        :return: List of Lightsail instance information
        :rtype: List[Dict[str, Any]]
        """
        instances = []
        try:
            lightsail_client = self._get_client("lightsail")
            paginator = lightsail_client.get_paginator("get_instances")

            for page in paginator.paginate():
                for instance in page.get("instances", []):
                    instance_arn = instance.get("arn", "")

                    if not self._matches_account(instance_arn):
                        continue

                    if not self._matches_tags(instance.get("tags", [])):
                        continue

                    instances.append(
                        {
                            "Region": self.region,
                            "InstanceName": instance.get("name"),
                            "InstanceArn": instance_arn,
                            "BlueprintId": instance.get("blueprintId"),
                            "BlueprintName": instance.get("blueprintName"),
                            "BundleId": instance.get("bundleId"),
                            "State": instance.get("state", {}).get("name"),
                            "PrivateIpAddress": instance.get("privateIpAddress"),
                            "PublicIpAddress": instance.get("publicIpAddress"),
                            "IsStaticIp": instance.get("isStaticIp"),
                            "CreatedAt": instance.get("createdAt"),
                            "Tags": instance.get("tags", []),
                        }
                    )
        except Exception as e:
            self._handle_error(e, "Lightsail instances")
        return instances

    def collect(self) -> Dict[str, Any]:
        """
        Collect compute resources based on enabled_services configuration.

        :return: Dictionary containing enabled compute resource information
        :rtype: Dict[str, Any]
        """
        result = {}

        # EC2 Instances
        if self.enabled_services.get("ec2", True):
            result["EC2Instances"] = self.get_ec2_instances()

        # Lambda Functions
        if self.enabled_services.get("lambda", True):
            result["LambdaFunctions"] = self.get_lambda_functions()

        # ECS Clusters
        if self.enabled_services.get("ecs", True):
            result["ECSClusters"] = self.get_ecs_clusters()

        # Systems Manager
        if self.enabled_services.get("systems_manager", True):
            ssm_info = self.get_systems_manager_info()
            result.update(ssm_info)

        # AWS Batch
        if self.enabled_services.get("batch", True):
            result["BatchComputeEnvironments"] = self.get_batch_compute_environments()
            result["BatchJobQueues"] = self.get_batch_job_queues()

        # App Runner
        if self.enabled_services.get("app_runner", True):
            result["AppRunnerServices"] = self.get_app_runner_services()

        # Elastic Beanstalk
        if self.enabled_services.get("elastic_beanstalk", True):
            result["ElasticBeanstalkApplications"] = self.get_elastic_beanstalk_applications()

        # Lightsail
        if self.enabled_services.get("lightsail", True):
            result["LightsailInstances"] = self.get_lightsail_instances()

        return result
