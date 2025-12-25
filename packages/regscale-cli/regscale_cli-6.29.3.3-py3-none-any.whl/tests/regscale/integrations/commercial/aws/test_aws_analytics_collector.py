#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for AWS Analytics Collector."""

import logging
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from regscale.integrations.commercial.aws.inventory.resources.analytics import AnalyticsCollector

logger = logging.getLogger("regscale")


class TestAnalyticsCollector:
    """Test suite for AnalyticsCollector class."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock boto3 session."""
        return MagicMock()

    @pytest.fixture
    def collector(self, mock_session):
        """Create an AnalyticsCollector instance."""
        return AnalyticsCollector(session=mock_session, region="us-east-1", account_id=None)

    @pytest.fixture
    def collector_with_filters(self, mock_session):
        """Create an AnalyticsCollector instance with filters."""
        return AnalyticsCollector(
            session=mock_session,
            region="us-east-1",
            account_id="123456789012",
            tags={"Environment": "Production"},
        )

    # Test initialization
    def test_collector_initialization(self, mock_session):
        """Test collector initialization."""
        collector = AnalyticsCollector(session=mock_session, region="us-west-2")
        assert collector.session == mock_session
        assert collector.region == "us-west-2"
        assert collector.account_id is None
        assert collector.tags == {}

    def test_collector_initialization_with_filters(self, mock_session):
        """Test collector initialization with filters."""
        collector = AnalyticsCollector(
            session=mock_session,
            region="us-east-1",
            account_id="123456789012",
            tags={"Environment": "Production"},
        )
        assert collector.account_id == "123456789012"
        assert collector.tags == {"Environment": "Production"}

    # Test EMR clusters
    def test_get_emr_clusters_success(self, collector):
        """Test successful EMR cluster collection."""
        mock_client = MagicMock()
        collector._get_client = MagicMock(return_value=mock_client)

        mock_paginator = MagicMock()
        mock_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [{"Clusters": [{"Id": "j-123456", "Name": "test-cluster"}]}]

        mock_client.describe_cluster.return_value = {
            "Cluster": {
                "Id": "j-123456",
                "Name": "test-cluster",
                "ClusterArn": "arn:aws:elasticmapreduce:us-east-1:123456789012:cluster/j-123456",
                "Status": {"State": "RUNNING"},
                "Tags": [{"Key": "Environment", "Value": "Test"}],
            }
        }

        clusters = collector.get_emr_clusters()
        assert len(clusters) == 1
        assert clusters[0]["ClusterId"] == "j-123456"
        assert clusters[0]["Name"] == "test-cluster"

    def test_get_emr_clusters_with_account_filter(self, collector_with_filters):
        """Test EMR cluster collection with account filtering."""
        mock_client = MagicMock()
        collector_with_filters._get_client = MagicMock(return_value=mock_client)

        mock_paginator = MagicMock()
        mock_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [{"Clusters": [{"Id": "j-123456"}]}]

        mock_client.describe_cluster.return_value = {
            "Cluster": {
                "ClusterArn": "arn:aws:elasticmapreduce:us-east-1:999999999999:cluster/j-123456",
                "Tags": [],
            }
        }

        clusters = collector_with_filters.get_emr_clusters()
        assert len(clusters) == 0

    # Test Kinesis Data Streams
    def test_get_kinesis_streams_success(self, collector):
        """Test successful Kinesis stream collection."""
        mock_client = MagicMock()
        collector._get_client = MagicMock(return_value=mock_client)

        mock_paginator = MagicMock()
        mock_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [{"StreamNames": ["test-stream"]}]

        mock_client.describe_stream.return_value = {
            "StreamDescription": {
                "StreamName": "test-stream",
                "StreamARN": "arn:aws:kinesis:us-east-1:123456789012:stream/test-stream",
                "StreamStatus": "ACTIVE",
                "RetentionPeriodHours": 24,
            }
        }

        mock_client.list_tags_for_stream.return_value = {"Tags": [{"Key": "Environment", "Value": "Test"}]}

        streams = collector.get_kinesis_streams()
        assert len(streams) == 1
        assert streams[0]["StreamName"] == "test-stream"
        assert streams[0]["StreamStatus"] == "ACTIVE"

    # Test Kinesis Firehose
    def test_get_kinesis_firehose_streams_success(self, collector):
        """Test successful Kinesis Firehose stream collection."""
        mock_client = MagicMock()
        collector._get_client = MagicMock(return_value=mock_client)

        # Firehose uses direct list_delivery_streams() calls, not paginator
        # Must include HasMoreDeliveryStreams=False to terminate pagination
        mock_client.list_delivery_streams.return_value = {
            "DeliveryStreamNames": ["test-firehose"],
            "HasMoreDeliveryStreams": False,
        }

        mock_client.describe_delivery_stream.return_value = {
            "DeliveryStreamDescription": {
                "DeliveryStreamName": "test-firehose",
                "DeliveryStreamARN": "arn:aws:firehose:us-east-1:123456789012:deliverystream/test-firehose",
                "DeliveryStreamStatus": "ACTIVE",
            }
        }

        mock_client.list_tags_for_delivery_stream.return_value = {"Tags": [{"Key": "Team", "Value": "DataEng"}]}

        streams = collector.get_kinesis_firehose_streams()
        assert len(streams) == 1
        assert streams[0]["DeliveryStreamName"] == "test-firehose"

    # Test Glue Databases
    def test_get_glue_databases_success(self, collector):
        """Test successful Glue database collection."""
        mock_client = MagicMock()
        collector._get_client = MagicMock(return_value=mock_client)

        mock_paginator = MagicMock()
        mock_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [{"DatabaseList": [{"Name": "test-db", "Description": "Test database"}]}]

        mock_client.get_tags.return_value = {"Tags": {"Environment": "Dev"}}

        databases = collector.get_glue_databases()
        assert len(databases) == 1
        assert databases[0]["DatabaseName"] == "test-db"

    # Test Athena Workgroups
    def test_get_athena_workgroups_success(self, collector):
        """Test successful Athena workgroup collection."""
        mock_client = MagicMock()
        collector._get_client = MagicMock(return_value=mock_client)

        # Athena uses direct list_work_groups() calls, not paginator
        # Must include NextToken=None to terminate pagination
        mock_client.list_work_groups.return_value = {
            "WorkGroups": [{"Name": "primary"}],
            "NextToken": None,
        }

        mock_client.get_work_group.return_value = {
            "WorkGroup": {
                "Name": "primary",
                "State": "ENABLED",
                "Description": "Primary workgroup",
            }
        }

        mock_client.list_tags_for_resource.return_value = {"Tags": [{"Key": "Type", "Value": "Analytics"}]}

        workgroups = collector.get_athena_workgroups()
        assert len(workgroups) == 1
        assert workgroups[0]["WorkGroupName"] == "primary"

    # Test MSK Clusters
    def test_get_msk_clusters_success(self, collector):
        """Test successful MSK cluster collection."""
        mock_client = MagicMock()
        collector._get_client = MagicMock(return_value=mock_client)

        mock_paginator = MagicMock()
        mock_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [
            {
                "ClusterInfoList": [
                    {
                        "ClusterName": "test-msk",
                        "ClusterArn": "arn:aws:kafka:us-east-1:123456789012:cluster/test-msk",
                        "State": "ACTIVE",
                        "Tags": {"Environment": "Production"},
                    }
                ]
            }
        ]

        clusters = collector.get_msk_clusters()
        assert len(clusters) == 1
        assert clusters[0]["ClusterName"] == "test-msk"

    # Test error handling
    def test_get_emr_clusters_error_handling(self, collector):
        """Test EMR cluster collection error handling."""
        mock_client = MagicMock()
        collector._get_client = MagicMock(return_value=mock_client)

        mock_paginator = MagicMock()
        mock_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access denied"}}, "ListClusters"
        )

        clusters = collector.get_emr_clusters()
        assert clusters == []

    # Test collect method
    def test_collect_all_services(self, collector):
        """Test collecting all analytics services."""
        with patch.object(collector, "get_emr_clusters", return_value=[{"Id": "j-123"}]):
            with patch.object(collector, "get_kinesis_streams", return_value=[{"Name": "stream"}]):
                with patch.object(collector, "get_kinesis_firehose_streams", return_value=[]):
                    with patch.object(collector, "get_glue_databases", return_value=[]):
                        with patch.object(collector, "get_athena_workgroups", return_value=[]):
                            with patch.object(collector, "get_msk_clusters", return_value=[]):
                                result = collector.collect()

        assert "EMRClusters" in result
        assert "KinesisStreams" in result
        assert len(result["EMRClusters"]) == 1
        assert len(result["KinesisStreams"]) == 1

    def test_collect_with_disabled_services(self, mock_session):
        """Test collecting with some services disabled."""
        # Explicitly disable all services except the one we're testing
        # This prevents pagination issues with unmocked AWS clients
        collector = AnalyticsCollector(
            session=mock_session,
            region="us-east-1",
            enabled_services={
                "emr": False,
                "kinesis_streams": True,
                "kinesis_firehose": False,
                "glue": False,
                "athena": False,
                "msk": False,
            },
        )

        with patch.object(collector, "get_kinesis_streams", return_value=[{"Name": "stream"}]):
            result = collector.collect()

        assert "EMRClusters" not in result
        assert "KinesisStreams" in result
