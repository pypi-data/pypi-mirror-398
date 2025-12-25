#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for AWS Developer Tools Collector."""

import logging
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from regscale.integrations.commercial.aws.inventory.resources.developer_tools import DeveloperToolsCollector

logger = logging.getLogger("regscale")


class TestDeveloperToolsCollector:
    """Test suite for DeveloperToolsCollector class."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock boto3 session."""
        return MagicMock()

    @pytest.fixture
    def collector(self, mock_session):
        """Create a DeveloperToolsCollector instance."""
        return DeveloperToolsCollector(session=mock_session, region="us-east-1")

    @pytest.fixture
    def collector_with_filters(self, mock_session):
        """Create a DeveloperToolsCollector instance with filters."""
        return DeveloperToolsCollector(
            session=mock_session,
            region="us-east-1",
            account_id="123456789012",
            tags={"Team": "DevOps"},
        )

    # Test initialization
    def test_collector_initialization(self, mock_session):
        """Test collector initialization."""
        collector = DeveloperToolsCollector(session=mock_session, region="us-west-2")
        assert collector.session == mock_session
        assert collector.region == "us-west-2"

    # Test CodePipeline
    def test_get_codepipeline_pipelines_success(self, collector):
        """Test successful CodePipeline pipeline collection."""
        mock_client = MagicMock()
        collector._get_client = MagicMock(return_value=mock_client)

        mock_paginator = MagicMock()
        mock_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [{"pipelines": [{"name": "test-pipeline"}]}]

        mock_client.get_pipeline.return_value = {
            "pipeline": {
                "name": "test-pipeline",
                "pipelineArn": "arn:aws:codepipeline:us-east-1:123456789012:test-pipeline",
                "roleArn": "arn:aws:iam::123456789012:role/CodePipelineRole",
            }
        }

        mock_client.list_tags_for_resource.return_value = {"tags": [{"key": "Environment", "value": "Production"}]}

        pipelines = collector.get_codepipeline_pipelines()
        assert len(pipelines) == 1
        assert pipelines[0]["PipelineName"] == "test-pipeline"

    # Test CodeBuild
    def test_get_codebuild_projects_success(self, collector):
        """Test successful CodeBuild project collection."""
        mock_client = MagicMock()
        collector._get_client = MagicMock(return_value=mock_client)

        mock_paginator = MagicMock()
        mock_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [{"projects": ["test-project"]}]

        mock_client.batch_get_projects.return_value = {
            "projects": [
                {
                    "name": "test-project",
                    "arn": "arn:aws:codebuild:us-east-1:123456789012:project/test-project",
                    "description": "Test project",
                    "serviceRole": "arn:aws:iam::123456789012:role/CodeBuildRole",
                    "tags": [{"key": "Team", "value": "Backend"}],
                }
            ]
        }

        projects = collector.get_codebuild_projects()
        assert len(projects) == 1
        assert projects[0]["ProjectName"] == "test-project"

    # Test CodeDeploy
    def test_get_codedeploy_applications_success(self, collector):
        """Test successful CodeDeploy application collection."""
        mock_client = MagicMock()
        collector._get_client = MagicMock(return_value=mock_client)

        mock_paginator = MagicMock()
        mock_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [{"applications": ["test-app"]}]

        mock_client.get_application.return_value = {
            "application": {
                "applicationName": "test-app",
                "applicationId": "app-123",
                "computePlatform": "Server",
            }
        }

        mock_client.list_tags_for_resource.return_value = {"Tags": [{"Key": "Type", "Value": "WebApp"}]}

        applications = collector.get_codedeploy_applications()
        assert len(applications) == 1
        assert applications[0]["ApplicationName"] == "test-app"

    # Test CodeCommit
    def test_get_codecommit_repositories_success(self, collector):
        """Test successful CodeCommit repository collection."""
        mock_client = MagicMock()
        collector._get_client = MagicMock(return_value=mock_client)

        mock_paginator = MagicMock()
        mock_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [{"repositories": [{"repositoryName": "test-repo"}]}]

        mock_client.get_repository.return_value = {
            "repositoryMetadata": {
                "repositoryName": "test-repo",
                "repositoryId": "repo-123",
                "Arn": "arn:aws:codecommit:us-east-1:123456789012:test-repo",
                "cloneUrlHttp": "https://git-codecommit.us-east-1.amazonaws.com/v1/repos/test-repo",
            }
        }

        mock_client.list_tags_for_resource.return_value = {"tags": {"Project": "Backend"}}

        repositories = collector.get_codecommit_repositories()
        assert len(repositories) == 1
        assert repositories[0]["RepositoryName"] == "test-repo"

    # Test with account filtering
    def test_collection_with_account_filter(self, collector_with_filters):
        """Test collection with account filtering."""
        mock_client = MagicMock()
        collector_with_filters._get_client = MagicMock(return_value=mock_client)

        mock_paginator = MagicMock()
        mock_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [{"pipelines": [{"name": "test"}]}]

        # Wrong account
        mock_client.get_pipeline.return_value = {
            "pipeline": {
                "pipelineArn": "arn:aws:codepipeline:us-east-1:999999999999:test",
            }
        }
        mock_client.list_tags_for_resource.return_value = {"tags": []}

        pipelines = collector_with_filters.get_codepipeline_pipelines()
        assert len(pipelines) == 0

    # Test error handling
    def test_error_handling(self, collector):
        """Test error handling in collectors."""
        mock_client = MagicMock()
        collector._get_client = MagicMock(return_value=mock_client)

        mock_paginator = MagicMock()
        mock_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access denied"}}, "ListPipelines"
        )

        pipelines = collector.get_codepipeline_pipelines()
        assert pipelines == []

    # Test collect method
    def test_collect_all_services(self, collector):
        """Test collecting all developer tools services."""
        with patch.object(collector, "get_codepipeline_pipelines", return_value=[{"Name": "pipeline"}]):
            with patch.object(collector, "get_codebuild_projects", return_value=[]):
                with patch.object(collector, "get_codedeploy_applications", return_value=[]):
                    with patch.object(collector, "get_codecommit_repositories", return_value=[]):
                        result = collector.collect()

        assert "CodePipelinePipelines" in result
        assert len(result["CodePipelinePipelines"]) == 1

    def test_collect_with_disabled_services(self, mock_session):
        """Test collecting with some services disabled."""
        collector = DeveloperToolsCollector(
            session=mock_session, region="us-east-1", enabled_services={"codepipeline": True, "codebuild": False}
        )

        with patch.object(collector, "get_codepipeline_pipelines", return_value=[{"Name": "pipeline"}]):
            result = collector.collect()

        assert "CodePipelinePipelines" in result
        assert "CodeBuildProjects" not in result
