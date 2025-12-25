"""AWS machine learning resource collectors."""

import logging
from typing import Dict, List, Any, Optional

from ..base import BaseCollector

logger = logging.getLogger("regscale")


class MachineLearningCollector(BaseCollector):
    """Collector for AWS machine learning resources with filtering support."""

    def __init__(
        self,
        session: Any,
        region: str,
        account_id: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        enabled_services: Optional[Dict[str, bool]] = None,
    ):
        """
        Initialize machine learning collector with filtering support.

        :param session: AWS session to use for API calls
        :param str region: AWS region to collect from
        :param str account_id: Optional AWS account ID to filter resources
        :param dict tags: Optional tag filters (AND logic)
        :param dict enabled_services: Optional dict of service names to boolean flags for enabling/disabling collection
        """
        super().__init__(session, region, account_id, tags)
        self.enabled_services = enabled_services or {}

    def get_sagemaker_endpoints(self) -> List[Dict[str, Any]]:
        """
        Get information about SageMaker inference endpoints.

        :return: List of SageMaker endpoint information
        :rtype: List[Dict[str, Any]]
        """
        endpoints = []
        try:
            sagemaker_client = self._get_client("sagemaker")
            paginator = sagemaker_client.get_paginator("list_endpoints")

            for page in paginator.paginate():
                for endpoint_summary in page.get("Endpoints", []):
                    endpoint_name = endpoint_summary.get("EndpointName")

                    try:
                        endpoint_detail = sagemaker_client.describe_endpoint(EndpointName=endpoint_name)
                        endpoint_arn = endpoint_detail.get("EndpointArn", "")

                        if not self._matches_account(endpoint_arn):
                            continue

                        tags_response = sagemaker_client.list_tags(ResourceArn=endpoint_arn)
                        endpoint_tags = tags_response.get("Tags", [])

                        if not self._matches_tags(endpoint_tags):
                            continue

                        endpoints.append(
                            {
                                "Region": self.region,
                                "EndpointName": endpoint_name,
                                "EndpointArn": endpoint_arn,
                                "EndpointStatus": endpoint_detail.get("EndpointStatus"),
                                "EndpointConfigName": endpoint_detail.get("EndpointConfigName"),
                                "CreationTime": endpoint_detail.get("CreationTime"),
                                "LastModifiedTime": endpoint_detail.get("LastModifiedTime"),
                                "Tags": endpoint_tags,
                            }
                        )
                    except Exception as endpoint_error:
                        logger.debug(
                            "Error getting SageMaker endpoint details for %s: %s", endpoint_name, endpoint_error
                        )
                        continue

        except Exception as e:
            self._handle_error(e, "SageMaker endpoints")
        return endpoints

    def get_sagemaker_models(self) -> List[Dict[str, Any]]:
        """
        Get information about SageMaker models.

        :return: List of SageMaker model information
        :rtype: List[Dict[str, Any]]
        """
        models = []
        try:
            sagemaker_client = self._get_client("sagemaker")
            paginator = sagemaker_client.get_paginator("list_models")

            for page in paginator.paginate():
                for model_summary in page.get("Models", []):
                    model_name = model_summary.get("ModelName")

                    try:
                        model_detail = sagemaker_client.describe_model(ModelName=model_name)
                        model_arn = model_detail.get("ModelArn", "")

                        if not self._matches_account(model_arn):
                            continue

                        tags_response = sagemaker_client.list_tags(ResourceArn=model_arn)
                        model_tags = tags_response.get("Tags", [])

                        if not self._matches_tags(model_tags):
                            continue

                        models.append(
                            {
                                "Region": self.region,
                                "ModelName": model_name,
                                "ModelArn": model_arn,
                                "CreationTime": model_detail.get("CreationTime"),
                                "ExecutionRoleArn": model_detail.get("ExecutionRoleArn"),
                                "PrimaryContainer": model_detail.get("PrimaryContainer"),
                                "Tags": model_tags,
                            }
                        )
                    except Exception as model_error:
                        logger.debug("Error getting SageMaker model details for %s: %s", model_name, model_error)
                        continue

        except Exception as e:
            self._handle_error(e, "SageMaker models")
        return models

    def get_sagemaker_notebooks(self) -> List[Dict[str, Any]]:
        """
        Get information about SageMaker notebook instances.

        :return: List of SageMaker notebook instance information
        :rtype: List[Dict[str, Any]]
        """
        notebooks = []
        try:
            sagemaker_client = self._get_client("sagemaker")
            paginator = sagemaker_client.get_paginator("list_notebook_instances")

            for page in paginator.paginate():
                for notebook_summary in page.get("NotebookInstances", []):
                    notebook_name = notebook_summary.get("NotebookInstanceName")

                    try:
                        notebook_detail = sagemaker_client.describe_notebook_instance(
                            NotebookInstanceName=notebook_name
                        )
                        notebook_arn = notebook_detail.get("NotebookInstanceArn", "")

                        if not self._matches_account(notebook_arn):
                            continue

                        tags_response = sagemaker_client.list_tags(ResourceArn=notebook_arn)
                        notebook_tags = tags_response.get("Tags", [])

                        if not self._matches_tags(notebook_tags):
                            continue

                        notebooks.append(
                            {
                                "Region": self.region,
                                "NotebookInstanceName": notebook_name,
                                "NotebookInstanceArn": notebook_arn,
                                "NotebookInstanceStatus": notebook_detail.get("NotebookInstanceStatus"),
                                "InstanceType": notebook_detail.get("InstanceType"),
                                "CreationTime": notebook_detail.get("CreationTime"),
                                "LastModifiedTime": notebook_detail.get("LastModifiedTime"),
                                "Url": notebook_detail.get("Url"),
                                "Tags": notebook_tags,
                            }
                        )
                    except Exception as notebook_error:
                        logger.debug(
                            "Error getting SageMaker notebook details for %s: %s", notebook_name, notebook_error
                        )
                        continue

        except Exception as e:
            self._handle_error(e, "SageMaker notebook instances")
        return notebooks

    def get_sagemaker_training_jobs(self) -> List[Dict[str, Any]]:
        """
        Get information about SageMaker training jobs.

        :return: List of SageMaker training job information
        :rtype: List[Dict[str, Any]]
        """
        training_jobs = []
        try:
            sagemaker_client = self._get_client("sagemaker")
            paginator = sagemaker_client.get_paginator("list_training_jobs")

            for page in paginator.paginate():
                for job_summary in page.get("TrainingJobSummaries", []):
                    job_name = job_summary.get("TrainingJobName")

                    try:
                        job_detail = sagemaker_client.describe_training_job(TrainingJobName=job_name)
                        job_arn = job_detail.get("TrainingJobArn", "")

                        if not self._matches_account(job_arn):
                            continue

                        tags_response = sagemaker_client.list_tags(ResourceArn=job_arn)
                        job_tags = tags_response.get("Tags", [])

                        if not self._matches_tags(job_tags):
                            continue

                        training_jobs.append(
                            {
                                "Region": self.region,
                                "TrainingJobName": job_name,
                                "TrainingJobArn": job_arn,
                                "TrainingJobStatus": job_detail.get("TrainingJobStatus"),
                                "CreationTime": job_detail.get("CreationTime"),
                                "TrainingStartTime": job_detail.get("TrainingStartTime"),
                                "TrainingEndTime": job_detail.get("TrainingEndTime"),
                                "AlgorithmSpecification": job_detail.get("AlgorithmSpecification"),
                                "Tags": job_tags,
                            }
                        )
                    except Exception as job_error:
                        logger.debug("Error getting SageMaker training job details for %s: %s", job_name, job_error)
                        continue

        except Exception as e:
            self._handle_error(e, "SageMaker training jobs")
        return training_jobs

    def get_rekognition_collections(self) -> List[Dict[str, Any]]:
        """
        Get information about Rekognition face collections.

        :return: List of Rekognition collection information
        :rtype: List[Dict[str, Any]]
        """
        collections = []
        try:
            rekognition_client = self._get_client("rekognition")
            paginator = rekognition_client.get_paginator("list_collections")

            for page in paginator.paginate():
                for collection_id in page.get("CollectionIds", []):
                    try:
                        collection_detail = rekognition_client.describe_collection(CollectionId=collection_id)
                        collection_arn = collection_detail.get("CollectionARN", "")

                        if not self._matches_account(collection_arn):
                            continue

                        collections.append(
                            {
                                "Region": self.region,
                                "CollectionId": collection_id,
                                "CollectionARN": collection_arn,
                                "FaceCount": collection_detail.get("FaceCount"),
                                "FaceModelVersion": collection_detail.get("FaceModelVersion"),
                                "CreationTimestamp": collection_detail.get("CreationTimestamp"),
                            }
                        )
                    except Exception as collection_error:
                        logger.debug(
                            "Error getting Rekognition collection details for %s: %s", collection_id, collection_error
                        )
                        continue

        except Exception as e:
            self._handle_error(e, "Rekognition collections")
        return collections

    def get_comprehend_endpoints(self) -> List[Dict[str, Any]]:
        """
        Get information about Comprehend custom model endpoints.

        :return: List of Comprehend endpoint information
        :rtype: List[Dict[str, Any]]
        """
        endpoints = []
        try:
            comprehend_client = self._get_client("comprehend")
            paginator = comprehend_client.get_paginator("list_endpoints")

            for page in paginator.paginate():
                for endpoint_props in page.get("EndpointPropertiesList", []):
                    endpoint_arn = endpoint_props.get("EndpointArn", "")

                    if not self._matches_account(endpoint_arn):
                        continue

                    try:
                        tags_response = comprehend_client.list_tags_for_resource(ResourceArn=endpoint_arn)
                        endpoint_tags = tags_response.get("Tags", [])

                        if not self._matches_tags(endpoint_tags):
                            continue

                        endpoints.append(
                            {
                                "Region": self.region,
                                "EndpointArn": endpoint_arn,
                                "Status": endpoint_props.get("Status"),
                                "ModelArn": endpoint_props.get("ModelArn"),
                                "DesiredInferenceUnits": endpoint_props.get("DesiredInferenceUnits"),
                                "CurrentInferenceUnits": endpoint_props.get("CurrentInferenceUnits"),
                                "CreationTime": endpoint_props.get("CreationTime"),
                                "LastModifiedTime": endpoint_props.get("LastModifiedTime"),
                                "Tags": endpoint_tags,
                            }
                        )
                    except Exception as tag_error:
                        logger.debug("Error getting Comprehend endpoint tags for %s: %s", endpoint_arn, tag_error)
                        continue

        except Exception as e:
            self._handle_error(e, "Comprehend endpoints")
        return endpoints

    def collect(self) -> Dict[str, Any]:
        """
        Collect machine learning resources based on enabled_services configuration.

        :return: Dictionary containing enabled ML resource information
        :rtype: Dict[str, Any]
        """
        result = {}

        # SageMaker Endpoints
        if self.enabled_services.get("sagemaker_endpoints", True):
            result["SageMakerEndpoints"] = self.get_sagemaker_endpoints()

        # SageMaker Models
        if self.enabled_services.get("sagemaker_models", True):
            result["SageMakerModels"] = self.get_sagemaker_models()

        # SageMaker Notebook Instances
        if self.enabled_services.get("sagemaker_notebooks", True):
            result["SageMakerNotebooks"] = self.get_sagemaker_notebooks()

        # SageMaker Training Jobs
        if self.enabled_services.get("sagemaker_training_jobs", True):
            result["SageMakerTrainingJobs"] = self.get_sagemaker_training_jobs()

        # Rekognition Collections
        if self.enabled_services.get("rekognition", True):
            result["RekognitionCollections"] = self.get_rekognition_collections()

        # Comprehend Endpoints
        if self.enabled_services.get("comprehend", True):
            result["ComprehendEndpoints"] = self.get_comprehend_endpoints()

        return result
