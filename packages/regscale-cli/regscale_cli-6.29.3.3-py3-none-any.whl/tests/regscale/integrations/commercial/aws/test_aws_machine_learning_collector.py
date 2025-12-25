#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for AWS Machine Learning Collector."""

import logging
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from regscale.integrations.commercial.aws.inventory.resources.machine_learning import MachineLearningCollector

logger = logging.getLogger("regscale")


class TestMachineLearningCollector:
    """Test suite for MachineLearningCollector class."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock boto3 session."""
        return MagicMock()

    @pytest.fixture
    def collector(self, mock_session):
        """Create a MachineLearningCollector instance."""
        return MachineLearningCollector(session=mock_session, region="us-east-1")

    @pytest.fixture
    def collector_with_filters(self, mock_session):
        """Create a MachineLearningCollector instance with filters."""
        return MachineLearningCollector(
            session=mock_session,
            region="us-east-1",
            account_id="123456789012",
            tags={"Team": "MLOps"},
        )

    # Test initialization
    def test_collector_initialization(self, mock_session):
        """Test collector initialization."""
        collector = MachineLearningCollector(session=mock_session, region="us-west-2")
        assert collector.session == mock_session
        assert collector.region == "us-west-2"

    # Test SageMaker Endpoints
    def test_get_sagemaker_endpoints_success(self, collector):
        """Test successful SageMaker endpoint collection."""
        mock_client = MagicMock()
        collector._get_client = MagicMock(return_value=mock_client)

        mock_paginator = MagicMock()
        mock_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [{"Endpoints": [{"EndpointName": "test-endpoint"}]}]

        mock_client.describe_endpoint.return_value = {
            "EndpointArn": "arn:aws:sagemaker:us-east-1:123456789012:endpoint/test-endpoint",
            "EndpointStatus": "InService",
            "EndpointConfigName": "test-config",
        }

        mock_client.list_tags.return_value = {"Tags": [{"Key": "Environment", "Value": "Production"}]}

        endpoints = collector.get_sagemaker_endpoints()
        assert len(endpoints) == 1
        assert endpoints[0]["EndpointName"] == "test-endpoint"
        assert endpoints[0]["EndpointStatus"] == "InService"

    # Test SageMaker Models
    def test_get_sagemaker_models_success(self, collector):
        """Test successful SageMaker model collection."""
        mock_client = MagicMock()
        collector._get_client = MagicMock(return_value=mock_client)

        mock_paginator = MagicMock()
        mock_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [{"Models": [{"ModelName": "test-model"}]}]

        mock_client.describe_model.return_value = {
            "ModelArn": "arn:aws:sagemaker:us-east-1:123456789012:model/test-model",
            "ExecutionRoleArn": "arn:aws:iam::123456789012:role/SageMakerRole",
        }

        mock_client.list_tags.return_value = {"Tags": []}

        models = collector.get_sagemaker_models()
        assert len(models) == 1
        assert models[0]["ModelName"] == "test-model"

    # Test SageMaker Notebooks
    def test_get_sagemaker_notebooks_success(self, collector):
        """Test successful SageMaker notebook instance collection."""
        mock_client = MagicMock()
        collector._get_client = MagicMock(return_value=mock_client)

        mock_paginator = MagicMock()
        mock_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [{"NotebookInstances": [{"NotebookInstanceName": "test-notebook"}]}]

        mock_client.describe_notebook_instance.return_value = {
            "NotebookInstanceArn": "arn:aws:sagemaker:us-east-1:123456789012:notebook-instance/test-notebook",
            "NotebookInstanceStatus": "InService",
            "InstanceType": "ml.t3.medium",
        }

        mock_client.list_tags.return_value = {"Tags": []}

        notebooks = collector.get_sagemaker_notebooks()
        assert len(notebooks) == 1
        assert notebooks[0]["NotebookInstanceName"] == "test-notebook"

    # Test SageMaker Training Jobs
    def test_get_sagemaker_training_jobs_success(self, collector):
        """Test successful SageMaker training job collection."""
        mock_client = MagicMock()
        collector._get_client = MagicMock(return_value=mock_client)

        mock_paginator = MagicMock()
        mock_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [{"TrainingJobSummaries": [{"TrainingJobName": "test-job"}]}]

        mock_client.describe_training_job.return_value = {
            "TrainingJobArn": "arn:aws:sagemaker:us-east-1:123456789012:training-job/test-job",
            "TrainingJobStatus": "Completed",
        }

        mock_client.list_tags.return_value = {"Tags": []}

        jobs = collector.get_sagemaker_training_jobs()
        assert len(jobs) == 1
        assert jobs[0]["TrainingJobName"] == "test-job"

    # Test Rekognition Collections
    def test_get_rekognition_collections_success(self, collector):
        """Test successful Rekognition collection retrieval."""
        mock_client = MagicMock()
        collector._get_client = MagicMock(return_value=mock_client)

        mock_paginator = MagicMock()
        mock_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [{"CollectionIds": ["test-collection"]}]

        mock_client.describe_collection.return_value = {
            "CollectionARN": "arn:aws:rekognition:us-east-1:123456789012:collection/test-collection",
            "FaceCount": 100,
            "FaceModelVersion": "6.0",
        }

        collections = collector.get_rekognition_collections()
        assert len(collections) == 1
        assert collections[0]["CollectionId"] == "test-collection"

    # Test Comprehend Endpoints
    def test_get_comprehend_endpoints_success(self, collector):
        """Test successful Comprehend endpoint collection."""
        mock_client = MagicMock()
        collector._get_client = MagicMock(return_value=mock_client)

        mock_paginator = MagicMock()
        mock_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [
            {
                "EndpointPropertiesList": [
                    {
                        "EndpointArn": "arn:aws:comprehend:us-east-1:123456789012:endpoint/test-endpoint",
                        "Status": "IN_SERVICE",
                    }
                ]
            }
        ]

        mock_client.list_tags_for_resource.return_value = {"Tags": []}

        endpoints = collector.get_comprehend_endpoints()
        assert len(endpoints) == 1

    # Test with account filtering
    def test_collection_with_account_filter(self, collector_with_filters):
        """Test collection with account filtering."""
        mock_client = MagicMock()
        collector_with_filters._get_client = MagicMock(return_value=mock_client)

        mock_paginator = MagicMock()
        mock_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [{"Endpoints": [{"EndpointName": "test"}]}]

        # Wrong account ID
        mock_client.describe_endpoint.return_value = {
            "EndpointArn": "arn:aws:sagemaker:us-east-1:999999999999:endpoint/test",
        }
        mock_client.list_tags.return_value = {"Tags": []}

        endpoints = collector_with_filters.get_sagemaker_endpoints()
        assert len(endpoints) == 0

    # Test error handling
    def test_error_handling(self, collector):
        """Test error handling in collectors."""
        mock_client = MagicMock()
        collector._get_client = MagicMock(return_value=mock_client)

        mock_paginator = MagicMock()
        mock_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access denied"}}, "ListEndpoints"
        )

        endpoints = collector.get_sagemaker_endpoints()
        assert endpoints == []

    # Test collect method
    def test_collect_all_services(self, collector):
        """Test collecting all ML services."""
        with patch.object(collector, "get_sagemaker_endpoints", return_value=[{"Name": "ep"}]):
            with patch.object(collector, "get_sagemaker_models", return_value=[]):
                with patch.object(collector, "get_sagemaker_notebooks", return_value=[]):
                    with patch.object(collector, "get_sagemaker_training_jobs", return_value=[]):
                        with patch.object(collector, "get_rekognition_collections", return_value=[]):
                            with patch.object(collector, "get_comprehend_endpoints", return_value=[]):
                                result = collector.collect()

        assert "SageMakerEndpoints" in result
        assert len(result["SageMakerEndpoints"]) == 1

    def test_collect_with_disabled_services(self, mock_session):
        """Test collecting with some services disabled."""
        collector = MachineLearningCollector(
            session=mock_session,
            region="us-east-1",
            enabled_services={"sagemaker_endpoints": True, "rekognition": False},
        )

        with patch.object(collector, "get_sagemaker_endpoints", return_value=[{"Name": "ep"}]):
            result = collector.collect()

        assert "SageMakerEndpoints" in result
        assert "RekognitionCollections" not in result
