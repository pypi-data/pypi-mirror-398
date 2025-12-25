#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for AWS Applications Collector."""

import logging
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from regscale.integrations.commercial.aws.inventory.resources.applications import ApplicationCollector

logger = logging.getLogger("regscale")


class TestApplicationCollector:
    """Test suite for ApplicationCollector class."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock boto3 session."""
        return MagicMock()

    @pytest.fixture
    def collector(self, mock_session):
        """Create an ApplicationCollector instance."""
        return ApplicationCollector(session=mock_session, region="us-east-1")

    @pytest.fixture
    def collector_with_filters(self, mock_session):
        """Create an ApplicationCollector instance with filters."""
        return ApplicationCollector(
            session=mock_session,
            region="us-east-1",
            account_id="123456789012",
            tags={"Application": "CriticalApp"},
        )

    # Test initialization
    def test_collector_initialization(self, mock_session):
        """Test collector initialization."""
        collector = ApplicationCollector(session=mock_session, region="us-west-2")
        assert collector.session == mock_session
        assert collector.region == "us-west-2"

    # Test Step Functions
    def test_get_step_functions_state_machines_success(self, collector):
        """Test successful Step Functions state machine collection."""
        mock_client = MagicMock()
        collector._get_client = MagicMock(return_value=mock_client)

        mock_paginator = MagicMock()
        mock_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [
            {
                "stateMachines": [
                    {
                        "name": "test-state-machine",
                        "stateMachineArn": "arn:aws:states:us-east-1:123456789012:stateMachine:test-state-machine",
                        "type": "STANDARD",
                    }
                ]
            }
        ]

        mock_client.describe_state_machine.return_value = {
            "status": "ACTIVE",
            "roleArn": "arn:aws:iam::123456789012:role/StepFunctionsRole",
        }

        mock_client.list_tags_for_resource.return_value = {"tags": [{"key": "Environment", "value": "Production"}]}

        state_machines = collector.get_step_functions_state_machines()
        assert len(state_machines) == 1
        assert state_machines[0]["StateMachineName"] == "test-state-machine"

    # Test AppSync
    def test_get_appsync_apis_success(self, collector):
        """Test successful AppSync API collection."""
        mock_client = MagicMock()
        collector._get_client = MagicMock(return_value=mock_client)

        mock_paginator = MagicMock()
        mock_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [
            {
                "graphqlApis": [
                    {
                        "apiId": "test-api-id",
                        "name": "test-api",
                        "arn": "arn:aws:appsync:us-east-1:123456789012:apis/test-api-id",
                        "authenticationType": "API_KEY",
                        "tags": {"Team": "Backend"},
                    }
                ]
            }
        ]

        apis = collector.get_appsync_apis()
        assert len(apis) == 1
        assert apis[0]["ApiId"] == "test-api-id"

    # Test WorkSpaces
    def test_get_workspaces_success(self, collector):
        """Test successful WorkSpaces collection."""
        mock_client = MagicMock()
        collector._get_client = MagicMock(return_value=mock_client)

        mock_paginator = MagicMock()
        mock_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [
            {
                "Workspaces": [
                    {
                        "WorkspaceId": "ws-123456",
                        "DirectoryId": "d-123456",
                        "UserName": "testuser",
                        "State": "AVAILABLE",
                    }
                ]
            }
        ]

        mock_client.describe_tags.return_value = {"TagList": [{"Key": "Department", "Value": "Engineering"}]}

        workspaces = collector.get_workspaces()
        assert len(workspaces) == 1
        assert workspaces[0]["WorkspaceId"] == "ws-123456"

    # Test IoT Things
    def test_get_iot_things_success(self, collector):
        """Test successful IoT thing collection."""
        mock_client = MagicMock()
        collector._get_client = MagicMock(return_value=mock_client)

        mock_paginator = MagicMock()
        mock_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [
            {
                "things": [
                    {
                        "thingName": "test-device",
                        "thingArn": "arn:aws:iot:us-east-1:123456789012:thing/test-device",
                        "thingTypeName": "sensor",
                        "attributes": {"location": "building-1"},
                    }
                ]
            }
        ]

        mock_client.list_tags_for_resource.return_value = {"tags": [{"Key": "DeviceType", "Value": "Sensor"}]}

        things = collector.get_iot_things()
        assert len(things) == 1
        assert things[0]["ThingName"] == "test-device"

    # Test with account filtering
    def test_collection_with_account_filter(self, collector_with_filters):
        """Test collection with account filtering."""
        mock_client = MagicMock()
        collector_with_filters._get_client = MagicMock(return_value=mock_client)

        mock_paginator = MagicMock()
        mock_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [
            {
                "stateMachines": [
                    {
                        "stateMachineArn": "arn:aws:states:us-east-1:999999999999:stateMachine:test",
                    }
                ]
            }
        ]

        state_machines = collector_with_filters.get_step_functions_state_machines()
        assert len(state_machines) == 0

    # Test with tag filtering
    def test_collection_with_tag_filter(self, collector_with_filters):
        """Test collection with tag filtering."""
        mock_client = MagicMock()
        collector_with_filters._get_client = MagicMock(return_value=mock_client)

        mock_paginator = MagicMock()
        mock_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [
            {
                "stateMachines": [
                    {
                        "name": "test",
                        "stateMachineArn": "arn:aws:states:us-east-1:123456789012:stateMachine:test",
                    }
                ]
            }
        ]

        mock_client.describe_state_machine.return_value = {"status": "ACTIVE"}

        # Wrong tags
        mock_client.list_tags_for_resource.return_value = {"tags": [{"key": "Environment", "value": "Dev"}]}

        state_machines = collector_with_filters.get_step_functions_state_machines()
        assert len(state_machines) == 0

    # Test error handling
    def test_error_handling(self, collector):
        """Test error handling in collectors."""
        mock_client = MagicMock()
        collector._get_client = MagicMock(return_value=mock_client)

        mock_paginator = MagicMock()
        mock_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access denied"}}, "ListStateMachines"
        )

        state_machines = collector.get_step_functions_state_machines()
        assert state_machines == []

    # Test collect method
    def test_collect_all_services(self, collector):
        """Test collecting all application services."""
        with patch.object(collector, "get_step_functions_state_machines", return_value=[{"Name": "sm"}]):
            with patch.object(collector, "get_appsync_apis", return_value=[]):
                with patch.object(collector, "get_workspaces", return_value=[]):
                    with patch.object(collector, "get_iot_things", return_value=[]):
                        result = collector.collect()

        assert "StepFunctionsStateMachines" in result
        assert len(result["StepFunctionsStateMachines"]) == 1

    def test_collect_with_disabled_services(self, mock_session):
        """Test collecting with some services disabled."""
        collector = ApplicationCollector(
            session=mock_session, region="us-east-1", enabled_services={"step_functions": True, "workspaces": False}
        )

        with patch.object(collector, "get_step_functions_state_machines", return_value=[{"Name": "sm"}]):
            result = collector.collect()

        assert "StepFunctionsStateMachines" in result
        assert "WorkSpaces" not in result
