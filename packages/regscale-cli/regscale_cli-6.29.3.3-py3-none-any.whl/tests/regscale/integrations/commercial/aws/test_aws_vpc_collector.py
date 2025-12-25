#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for AWS VPC collector."""

import logging
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from regscale.integrations.commercial.aws.inventory.resources.vpc import VPCCollector

logger = logging.getLogger("regscale")


class TestVPCCollector:
    """Test suite for VPCCollector."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock boto3 session."""
        session = MagicMock()
        return session

    @pytest.fixture
    def mock_ec2_client(self):
        """Create a mock EC2 client."""
        client = MagicMock()
        return client

    @pytest.fixture
    def vpc_collector(self, mock_session):
        """Create a VPCCollector instance with mock session."""
        return VPCCollector(session=mock_session, region="us-east-1", account_id="123456789012")

    @pytest.fixture
    def vpc_collector_no_filter(self, mock_session):
        """Create a VPCCollector instance without account filtering."""
        return VPCCollector(session=mock_session, region="us-east-1", account_id=None)

    # Test initialization

    def test_vpc_collector_initialization(self, vpc_collector):
        """Test VPCCollector initialization with account_id."""
        assert vpc_collector.region == "us-east-1"
        assert vpc_collector.account_id == "123456789012"

    def test_vpc_collector_initialization_no_filter(self, vpc_collector_no_filter):
        """Test VPCCollector initialization without account_id."""
        assert vpc_collector_no_filter.region == "us-east-1"
        assert vpc_collector_no_filter.account_id is None

    # Test _matches_account_id

    def test_matches_account_id_with_matching_owner(self, vpc_collector):
        """Test _matches_account_id with matching owner ID."""
        assert vpc_collector._matches_account_id("123456789012") is True

    def test_matches_account_id_with_non_matching_owner(self, vpc_collector):
        """Test _matches_account_id with non-matching owner ID."""
        assert vpc_collector._matches_account_id("999999999999") is False

    def test_matches_account_id_no_filter(self, vpc_collector_no_filter):
        """Test _matches_account_id when no account_id filter is set."""
        assert vpc_collector_no_filter._matches_account_id("123456789012") is True
        assert vpc_collector_no_filter._matches_account_id("999999999999") is True

    # Test _get_vpc_attributes

    def test_get_vpc_attributes_success(self, vpc_collector, mock_ec2_client):
        """Test _get_vpc_attributes with successful API calls."""
        mock_ec2_client.describe_vpc_attribute.side_effect = [
            {"EnableDnsSupport": {"Value": True}},
            {"EnableDnsHostnames": {"Value": False}},
        ]

        result = vpc_collector._get_vpc_attributes(mock_ec2_client, "vpc-12345")

        assert result["EnableDnsSupport"] is True
        assert result["EnableDnsHostnames"] is False
        assert mock_ec2_client.describe_vpc_attribute.call_count == 2

    def test_get_vpc_attributes_unauthorized(self, vpc_collector, mock_ec2_client):
        """Test _get_vpc_attributes with UnauthorizedOperation error."""
        error_response = {"Error": {"Code": "UnauthorizedOperation"}}
        mock_ec2_client.describe_vpc_attribute.side_effect = ClientError(error_response, "describe_vpc_attribute")

        result = vpc_collector._get_vpc_attributes(mock_ec2_client, "vpc-12345")

        assert result == {}

    def test_get_vpc_attributes_vpc_not_found(self, vpc_collector, mock_ec2_client):
        """Test _get_vpc_attributes with InvalidVpcID.NotFound error."""
        error_response = {"Error": {"Code": "InvalidVpcID.NotFound"}}
        mock_ec2_client.describe_vpc_attribute.side_effect = ClientError(error_response, "describe_vpc_attribute")

        result = vpc_collector._get_vpc_attributes(mock_ec2_client, "vpc-invalid")

        assert result == {}

    def test_get_vpc_attributes_other_error(self, vpc_collector, mock_ec2_client):
        """Test _get_vpc_attributes with other ClientError."""
        error_response = {"Error": {"Code": "InternalError"}}
        mock_ec2_client.describe_vpc_attribute.side_effect = ClientError(error_response, "describe_vpc_attribute")

        result = vpc_collector._get_vpc_attributes(mock_ec2_client, "vpc-12345")

        # Should return empty dict but log the error
        assert result == {}

    # Test _list_vpcs

    def test_list_vpcs_success(self, vpc_collector, mock_ec2_client):
        """Test _list_vpcs with successful API call."""
        mock_paginator = MagicMock()
        mock_ec2_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [
            {
                "Vpcs": [
                    {
                        "VpcId": "vpc-12345",
                        "OwnerId": "123456789012",
                        "CidrBlock": "10.0.0.0/16",
                        "CidrBlockAssociationSet": [],
                        "Ipv6CidrBlockAssociationSet": [],
                        "State": "available",
                        "IsDefault": False,
                        "DhcpOptionsId": "dopt-12345",
                        "InstanceTenancy": "default",
                        "Tags": [{"Key": "Name", "Value": "Test VPC"}],
                    }
                ]
            }
        ]

        # Mock _get_vpc_attributes
        with patch.object(vpc_collector, "_get_vpc_attributes") as mock_get_attributes:
            mock_get_attributes.return_value = {"EnableDnsSupport": True, "EnableDnsHostnames": True}

            result = vpc_collector._list_vpcs(mock_ec2_client)

        assert len(result) == 1
        assert result[0]["VpcId"] == "vpc-12345"
        assert result[0]["Region"] == "us-east-1"
        assert result[0]["EnableDnsSupport"] is True

    def test_list_vpcs_with_pagination(self, vpc_collector, mock_ec2_client):
        """Test _list_vpcs with multiple pages."""
        mock_paginator = MagicMock()
        mock_ec2_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [
            {"Vpcs": [{"VpcId": "vpc-1", "OwnerId": "123456789012", "CidrBlock": "10.0.0.0/16", "State": "available"}]},
            {"Vpcs": [{"VpcId": "vpc-2", "OwnerId": "123456789012", "CidrBlock": "10.1.0.0/16", "State": "available"}]},
        ]

        with patch.object(vpc_collector, "_get_vpc_attributes") as mock_get_attributes:
            mock_get_attributes.return_value = {}

            result = vpc_collector._list_vpcs(mock_ec2_client)

        assert len(result) == 2
        assert result[0]["VpcId"] == "vpc-1"
        assert result[1]["VpcId"] == "vpc-2"

    def test_list_vpcs_account_filtering(self, vpc_collector, mock_ec2_client):
        """Test _list_vpcs filters by account ID."""
        mock_paginator = MagicMock()
        mock_ec2_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [
            {
                "Vpcs": [
                    {"VpcId": "vpc-1", "OwnerId": "123456789012", "CidrBlock": "10.0.0.0/16", "State": "available"},
                    {"VpcId": "vpc-2", "OwnerId": "999999999999", "CidrBlock": "10.1.0.0/16", "State": "available"},
                ]
            }
        ]

        with patch.object(vpc_collector, "_get_vpc_attributes") as mock_get_attributes:
            mock_get_attributes.return_value = {}

            result = vpc_collector._list_vpcs(mock_ec2_client)

        # Should only include vpc-1 (matching account ID)
        assert len(result) == 1
        assert result[0]["VpcId"] == "vpc-1"

    def test_list_vpcs_unauthorized(self, vpc_collector, mock_ec2_client):
        """Test _list_vpcs with UnauthorizedOperation error."""
        mock_paginator = MagicMock()
        mock_ec2_client.get_paginator.return_value = mock_paginator
        error_response = {"Error": {"Code": "UnauthorizedOperation"}}
        mock_paginator.paginate.side_effect = ClientError(error_response, "describe_vpcs")

        result = vpc_collector._list_vpcs(mock_ec2_client)

        assert result == []

    def test_list_vpcs_other_error(self, vpc_collector, mock_ec2_client):
        """Test _list_vpcs with other ClientError."""
        mock_paginator = MagicMock()
        mock_ec2_client.get_paginator.return_value = mock_paginator
        error_response = {"Error": {"Code": "InternalError"}}
        mock_paginator.paginate.side_effect = ClientError(error_response, "describe_vpcs")

        result = vpc_collector._list_vpcs(mock_ec2_client)

        assert result == []

    # Test _list_subnets

    def test_list_subnets_success(self, vpc_collector, mock_ec2_client):
        """Test _list_subnets with successful API call."""
        mock_paginator = MagicMock()
        mock_ec2_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [
            {
                "Subnets": [
                    {
                        "SubnetId": "subnet-12345",
                        "VpcId": "vpc-12345",
                        "OwnerId": "123456789012",
                        "AvailabilityZone": "us-east-1a",
                        "AvailabilityZoneId": "use1-az1",
                        "CidrBlock": "10.0.1.0/24",
                        "Ipv6CidrBlockAssociationSet": [],
                        "State": "available",
                        "AvailableIpAddressCount": 251,
                        "DefaultForAz": False,
                        "MapPublicIpOnLaunch": True,
                        "AssignIpv6AddressOnCreation": False,
                        "Tags": [{"Key": "Name", "Value": "Public Subnet"}],
                    }
                ]
            }
        ]

        result = vpc_collector._list_subnets(mock_ec2_client)

        assert len(result) == 1
        assert result[0]["SubnetId"] == "subnet-12345"
        assert result[0]["Region"] == "us-east-1"

    def test_list_subnets_account_filtering(self, vpc_collector, mock_ec2_client):
        """Test _list_subnets filters by account ID."""
        mock_paginator = MagicMock()
        mock_ec2_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [
            {
                "Subnets": [
                    {"SubnetId": "subnet-1", "VpcId": "vpc-1", "OwnerId": "123456789012", "CidrBlock": "10.0.1.0/24"},
                    {"SubnetId": "subnet-2", "VpcId": "vpc-2", "OwnerId": "999999999999", "CidrBlock": "10.1.1.0/24"},
                ]
            }
        ]

        result = vpc_collector._list_subnets(mock_ec2_client)

        assert len(result) == 1
        assert result[0]["SubnetId"] == "subnet-1"

    def test_list_subnets_unauthorized(self, vpc_collector, mock_ec2_client):
        """Test _list_subnets with UnauthorizedOperation error."""
        mock_paginator = MagicMock()
        mock_ec2_client.get_paginator.return_value = mock_paginator
        error_response = {"Error": {"Code": "UnauthorizedOperation"}}
        mock_paginator.paginate.side_effect = ClientError(error_response, "describe_subnets")

        result = vpc_collector._list_subnets(mock_ec2_client)

        assert result == []

    def test_list_subnets_other_error(self, vpc_collector, mock_ec2_client):
        """Test _list_subnets with other ClientError."""
        mock_paginator = MagicMock()
        mock_ec2_client.get_paginator.return_value = mock_paginator
        error_response = {"Error": {"Code": "InternalError"}}
        mock_paginator.paginate.side_effect = ClientError(error_response, "describe_subnets")

        result = vpc_collector._list_subnets(mock_ec2_client)

        assert result == []

    # Test _list_security_groups

    def test_list_security_groups_success(self, vpc_collector, mock_ec2_client):
        """Test _list_security_groups with successful API call."""
        mock_paginator = MagicMock()
        mock_ec2_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [
            {
                "SecurityGroups": [
                    {
                        "GroupId": "sg-12345",
                        "GroupName": "default",
                        "VpcId": "vpc-12345",
                        "OwnerId": "123456789012",
                        "Description": "Default security group",
                        "IpPermissions": [],
                        "IpPermissionsEgress": [],
                        "Tags": [],
                    }
                ]
            }
        ]

        result = vpc_collector._list_security_groups(mock_ec2_client)

        assert len(result) == 1
        assert result[0]["GroupId"] == "sg-12345"
        assert result[0]["Region"] == "us-east-1"

    def test_list_security_groups_account_filtering(self, vpc_collector, mock_ec2_client):
        """Test _list_security_groups filters by account ID."""
        mock_paginator = MagicMock()
        mock_ec2_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [
            {
                "SecurityGroups": [
                    {"GroupId": "sg-1", "GroupName": "sg1", "OwnerId": "123456789012", "Description": "SG 1"},
                    {"GroupId": "sg-2", "GroupName": "sg2", "OwnerId": "999999999999", "Description": "SG 2"},
                ]
            }
        ]

        result = vpc_collector._list_security_groups(mock_ec2_client)

        assert len(result) == 1
        assert result[0]["GroupId"] == "sg-1"

    def test_list_security_groups_unauthorized(self, vpc_collector, mock_ec2_client):
        """Test _list_security_groups with UnauthorizedOperation error."""
        mock_paginator = MagicMock()
        mock_ec2_client.get_paginator.return_value = mock_paginator
        error_response = {"Error": {"Code": "UnauthorizedOperation"}}
        mock_paginator.paginate.side_effect = ClientError(error_response, "describe_security_groups")

        result = vpc_collector._list_security_groups(mock_ec2_client)

        assert result == []

    def test_list_security_groups_other_error(self, vpc_collector, mock_ec2_client):
        """Test _list_security_groups with other ClientError."""
        mock_paginator = MagicMock()
        mock_ec2_client.get_paginator.return_value = mock_paginator
        error_response = {"Error": {"Code": "InternalError"}}
        mock_paginator.paginate.side_effect = ClientError(error_response, "describe_security_groups")

        result = vpc_collector._list_security_groups(mock_ec2_client)

        assert result == []

    # Test _list_network_acls

    def test_list_network_acls_success(self, vpc_collector, mock_ec2_client):
        """Test _list_network_acls with successful API call."""
        mock_paginator = MagicMock()
        mock_ec2_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [
            {
                "NetworkAcls": [
                    {
                        "NetworkAclId": "acl-12345",
                        "VpcId": "vpc-12345",
                        "OwnerId": "123456789012",
                        "IsDefault": True,
                        "Entries": [],
                        "Associations": [],
                        "Tags": [],
                    }
                ]
            }
        ]

        result = vpc_collector._list_network_acls(mock_ec2_client)

        assert len(result) == 1
        assert result[0]["NetworkAclId"] == "acl-12345"
        assert result[0]["Region"] == "us-east-1"

    def test_list_network_acls_account_filtering(self, vpc_collector, mock_ec2_client):
        """Test _list_network_acls filters by account ID."""
        mock_paginator = MagicMock()
        mock_ec2_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [
            {
                "NetworkAcls": [
                    {"NetworkAclId": "acl-1", "VpcId": "vpc-1", "OwnerId": "123456789012", "IsDefault": True},
                    {"NetworkAclId": "acl-2", "VpcId": "vpc-2", "OwnerId": "999999999999", "IsDefault": False},
                ]
            }
        ]

        result = vpc_collector._list_network_acls(mock_ec2_client)

        assert len(result) == 1
        assert result[0]["NetworkAclId"] == "acl-1"

    def test_list_network_acls_unauthorized(self, vpc_collector, mock_ec2_client):
        """Test _list_network_acls with UnauthorizedOperation error."""
        mock_paginator = MagicMock()
        mock_ec2_client.get_paginator.return_value = mock_paginator
        error_response = {"Error": {"Code": "UnauthorizedOperation"}}
        mock_paginator.paginate.side_effect = ClientError(error_response, "describe_network_acls")

        result = vpc_collector._list_network_acls(mock_ec2_client)

        assert result == []

    def test_list_network_acls_other_error(self, vpc_collector, mock_ec2_client):
        """Test _list_network_acls with other ClientError."""
        mock_paginator = MagicMock()
        mock_ec2_client.get_paginator.return_value = mock_paginator
        error_response = {"Error": {"Code": "InternalError"}}
        mock_paginator.paginate.side_effect = ClientError(error_response, "describe_network_acls")

        result = vpc_collector._list_network_acls(mock_ec2_client)

        assert result == []

    # Test _list_route_tables

    def test_list_route_tables_success(self, vpc_collector, mock_ec2_client):
        """Test _list_route_tables with successful API call."""
        mock_paginator = MagicMock()
        mock_ec2_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [
            {
                "RouteTables": [
                    {
                        "RouteTableId": "rtb-12345",
                        "VpcId": "vpc-12345",
                        "OwnerId": "123456789012",
                        "Routes": [],
                        "Associations": [],
                        "PropagatingVgws": [],
                        "Tags": [],
                    }
                ]
            }
        ]

        result = vpc_collector._list_route_tables(mock_ec2_client)

        assert len(result) == 1
        assert result[0]["RouteTableId"] == "rtb-12345"
        assert result[0]["Region"] == "us-east-1"

    def test_list_route_tables_account_filtering(self, vpc_collector, mock_ec2_client):
        """Test _list_route_tables filters by account ID."""
        mock_paginator = MagicMock()
        mock_ec2_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [
            {
                "RouteTables": [
                    {"RouteTableId": "rtb-1", "VpcId": "vpc-1", "OwnerId": "123456789012"},
                    {"RouteTableId": "rtb-2", "VpcId": "vpc-2", "OwnerId": "999999999999"},
                ]
            }
        ]

        result = vpc_collector._list_route_tables(mock_ec2_client)

        assert len(result) == 1
        assert result[0]["RouteTableId"] == "rtb-1"

    def test_list_route_tables_unauthorized(self, vpc_collector, mock_ec2_client):
        """Test _list_route_tables with UnauthorizedOperation error."""
        mock_paginator = MagicMock()
        mock_ec2_client.get_paginator.return_value = mock_paginator
        error_response = {"Error": {"Code": "UnauthorizedOperation"}}
        mock_paginator.paginate.side_effect = ClientError(error_response, "describe_route_tables")

        result = vpc_collector._list_route_tables(mock_ec2_client)

        assert result == []

    def test_list_route_tables_other_error(self, vpc_collector, mock_ec2_client):
        """Test _list_route_tables with other ClientError."""
        mock_paginator = MagicMock()
        mock_ec2_client.get_paginator.return_value = mock_paginator
        error_response = {"Error": {"Code": "InternalError"}}
        mock_paginator.paginate.side_effect = ClientError(error_response, "describe_route_tables")

        result = vpc_collector._list_route_tables(mock_ec2_client)

        assert result == []

    # Test _list_internet_gateways

    def test_list_internet_gateways_success(self, vpc_collector, mock_ec2_client):
        """Test _list_internet_gateways with successful API call."""
        mock_paginator = MagicMock()
        mock_ec2_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [
            {
                "InternetGateways": [
                    {
                        "InternetGatewayId": "igw-12345",
                        "OwnerId": "123456789012",
                        "Attachments": [{"State": "available", "VpcId": "vpc-12345"}],
                        "Tags": [],
                    }
                ]
            }
        ]

        result = vpc_collector._list_internet_gateways(mock_ec2_client)

        assert len(result) == 1
        assert result[0]["InternetGatewayId"] == "igw-12345"
        assert result[0]["Region"] == "us-east-1"

    def test_list_internet_gateways_account_filtering(self, vpc_collector, mock_ec2_client):
        """Test _list_internet_gateways filters by account ID."""
        mock_paginator = MagicMock()
        mock_ec2_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [
            {
                "InternetGateways": [
                    {"InternetGatewayId": "igw-1", "OwnerId": "123456789012", "Attachments": []},
                    {"InternetGatewayId": "igw-2", "OwnerId": "999999999999", "Attachments": []},
                ]
            }
        ]

        result = vpc_collector._list_internet_gateways(mock_ec2_client)

        assert len(result) == 1
        assert result[0]["InternetGatewayId"] == "igw-1"

    def test_list_internet_gateways_unauthorized(self, vpc_collector, mock_ec2_client):
        """Test _list_internet_gateways with UnauthorizedOperation error."""
        mock_paginator = MagicMock()
        mock_ec2_client.get_paginator.return_value = mock_paginator
        error_response = {"Error": {"Code": "UnauthorizedOperation"}}
        mock_paginator.paginate.side_effect = ClientError(error_response, "describe_internet_gateways")

        result = vpc_collector._list_internet_gateways(mock_ec2_client)

        assert result == []

    def test_list_internet_gateways_other_error(self, vpc_collector, mock_ec2_client):
        """Test _list_internet_gateways with other ClientError."""
        mock_paginator = MagicMock()
        mock_ec2_client.get_paginator.return_value = mock_paginator
        error_response = {"Error": {"Code": "InternalError"}}
        mock_paginator.paginate.side_effect = ClientError(error_response, "describe_internet_gateways")

        result = vpc_collector._list_internet_gateways(mock_ec2_client)

        assert result == []

    # Test _list_nat_gateways

    def test_list_nat_gateways_success(self, vpc_collector, mock_ec2_client):
        """Test _list_nat_gateways with successful API call."""
        mock_paginator = MagicMock()
        mock_ec2_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [
            {
                "NatGateways": [
                    {
                        "NatGatewayId": "nat-12345",
                        "VpcId": "vpc-12345",
                        "SubnetId": "subnet-12345",
                        "State": "available",
                        "ConnectivityType": "public",
                        "NatGatewayAddresses": [],
                        "CreateTime": datetime(2024, 1, 1),
                        "DeleteTime": None,
                        "Tags": [],
                    }
                ]
            }
        ]

        result = vpc_collector._list_nat_gateways(mock_ec2_client)

        assert len(result) == 1
        assert result[0]["NatGatewayId"] == "nat-12345"
        assert result[0]["Region"] == "us-east-1"

    def test_list_nat_gateways_with_delete_time(self, vpc_collector, mock_ec2_client):
        """Test _list_nat_gateways with DeleteTime present."""
        mock_paginator = MagicMock()
        mock_ec2_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [
            {
                "NatGateways": [
                    {
                        "NatGatewayId": "nat-12345",
                        "VpcId": "vpc-12345",
                        "SubnetId": "subnet-12345",
                        "State": "deleted",
                        "ConnectivityType": "public",
                        "NatGatewayAddresses": [],
                        "CreateTime": datetime(2024, 1, 1),
                        "DeleteTime": datetime(2024, 1, 2),
                        "Tags": [],
                    }
                ]
            }
        ]

        result = vpc_collector._list_nat_gateways(mock_ec2_client)

        assert len(result) == 1
        assert result[0]["DeleteTime"] is not None

    def test_list_nat_gateways_unauthorized(self, vpc_collector, mock_ec2_client):
        """Test _list_nat_gateways with UnauthorizedOperation error."""
        mock_paginator = MagicMock()
        mock_ec2_client.get_paginator.return_value = mock_paginator
        error_response = {"Error": {"Code": "UnauthorizedOperation"}}
        mock_paginator.paginate.side_effect = ClientError(error_response, "describe_nat_gateways")

        result = vpc_collector._list_nat_gateways(mock_ec2_client)

        assert result == []

    def test_list_nat_gateways_other_error(self, vpc_collector, mock_ec2_client):
        """Test _list_nat_gateways with other ClientError."""
        mock_paginator = MagicMock()
        mock_ec2_client.get_paginator.return_value = mock_paginator
        error_response = {"Error": {"Code": "InternalError"}}
        mock_paginator.paginate.side_effect = ClientError(error_response, "describe_nat_gateways")

        result = vpc_collector._list_nat_gateways(mock_ec2_client)

        assert result == []

    # Test _list_vpc_endpoints

    def test_list_vpc_endpoints_success(self, vpc_collector, mock_ec2_client):
        """Test _list_vpc_endpoints with successful API call."""
        mock_paginator = MagicMock()
        mock_ec2_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [
            {
                "VpcEndpoints": [
                    {
                        "VpcEndpointId": "vpce-12345",
                        "VpcId": "vpc-12345",
                        "OwnerId": "123456789012",
                        "ServiceName": "com.amazonaws.us-east-1.s3",
                        "VpcEndpointType": "Gateway",
                        "State": "available",
                        "PolicyDocument": '{"Version": "2012-10-17"}',
                        "SubnetIds": [],
                        "RouteTableIds": ["rtb-12345"],
                        "Groups": [],
                        "PrivateDnsEnabled": False,
                        "DnsEntries": [],
                        "CreationTimestamp": datetime(2024, 1, 1),
                        "Tags": [],
                    }
                ]
            }
        ]

        result = vpc_collector._list_vpc_endpoints(mock_ec2_client)

        assert len(result) == 1
        assert result[0]["VpcEndpointId"] == "vpce-12345"
        assert result[0]["Region"] == "us-east-1"

    def test_list_vpc_endpoints_account_filtering(self, vpc_collector, mock_ec2_client):
        """Test _list_vpc_endpoints filters by account ID."""
        mock_paginator = MagicMock()
        mock_ec2_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [
            {
                "VpcEndpoints": [
                    {
                        "VpcEndpointId": "vpce-1",
                        "VpcId": "vpc-1",
                        "OwnerId": "123456789012",
                        "ServiceName": "com.amazonaws.us-east-1.s3",
                        "VpcEndpointType": "Gateway",
                        "State": "available",
                        "CreationTimestamp": datetime(2024, 1, 1),
                    },
                    {
                        "VpcEndpointId": "vpce-2",
                        "VpcId": "vpc-2",
                        "OwnerId": "999999999999",
                        "ServiceName": "com.amazonaws.us-east-1.ec2",
                        "VpcEndpointType": "Interface",
                        "State": "available",
                        "CreationTimestamp": datetime(2024, 1, 1),
                    },
                ]
            }
        ]

        result = vpc_collector._list_vpc_endpoints(mock_ec2_client)

        assert len(result) == 1
        assert result[0]["VpcEndpointId"] == "vpce-1"

    def test_list_vpc_endpoints_unauthorized(self, vpc_collector, mock_ec2_client):
        """Test _list_vpc_endpoints with UnauthorizedOperation error."""
        mock_paginator = MagicMock()
        mock_ec2_client.get_paginator.return_value = mock_paginator
        error_response = {"Error": {"Code": "UnauthorizedOperation"}}
        mock_paginator.paginate.side_effect = ClientError(error_response, "describe_vpc_endpoints")

        result = vpc_collector._list_vpc_endpoints(mock_ec2_client)

        assert result == []

    def test_list_vpc_endpoints_other_error(self, vpc_collector, mock_ec2_client):
        """Test _list_vpc_endpoints with other ClientError."""
        mock_paginator = MagicMock()
        mock_ec2_client.get_paginator.return_value = mock_paginator
        error_response = {"Error": {"Code": "InternalError"}}
        mock_paginator.paginate.side_effect = ClientError(error_response, "describe_vpc_endpoints")

        result = vpc_collector._list_vpc_endpoints(mock_ec2_client)

        assert result == []

    # Test _list_vpc_peering_connections

    def test_list_vpc_peering_connections_success(self, vpc_collector, mock_ec2_client):
        """Test _list_vpc_peering_connections with successful API call."""
        mock_paginator = MagicMock()
        mock_ec2_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [
            {
                "VpcPeeringConnections": [
                    {
                        "VpcPeeringConnectionId": "pcx-12345",
                        "RequesterVpcInfo": {
                            "VpcId": "vpc-12345",
                            "OwnerId": "123456789012",
                            "CidrBlock": "10.0.0.0/16",
                            "Region": "us-east-1",
                        },
                        "AccepterVpcInfo": {
                            "VpcId": "vpc-67890",
                            "OwnerId": "999999999999",
                            "CidrBlock": "10.1.0.0/16",
                            "Region": "us-west-2",
                        },
                        "Status": {"Code": "active"},
                        "ExpirationTime": None,
                        "Tags": [],
                    }
                ]
            }
        ]

        result = vpc_collector._list_vpc_peering_connections(mock_ec2_client)

        assert len(result) == 1
        assert result[0]["VpcPeeringConnectionId"] == "pcx-12345"
        assert result[0]["Region"] == "us-east-1"

    def test_list_vpc_peering_connections_requester_filter(self, vpc_collector, mock_ec2_client):
        """Test _list_vpc_peering_connections filters by requester account ID."""
        mock_paginator = MagicMock()
        mock_ec2_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [
            {
                "VpcPeeringConnections": [
                    {
                        "VpcPeeringConnectionId": "pcx-1",
                        "RequesterVpcInfo": {"VpcId": "vpc-1", "OwnerId": "123456789012"},
                        "AccepterVpcInfo": {"VpcId": "vpc-2", "OwnerId": "999999999999"},
                        "Status": {"Code": "active"},
                    },
                    {
                        "VpcPeeringConnectionId": "pcx-2",
                        "RequesterVpcInfo": {"VpcId": "vpc-3", "OwnerId": "888888888888"},
                        "AccepterVpcInfo": {"VpcId": "vpc-4", "OwnerId": "777777777777"},
                        "Status": {"Code": "active"},
                    },
                ]
            }
        ]

        result = vpc_collector._list_vpc_peering_connections(mock_ec2_client)

        # Should include pcx-1 (requester matches account_id)
        assert len(result) == 1
        assert result[0]["VpcPeeringConnectionId"] == "pcx-1"

    def test_list_vpc_peering_connections_accepter_filter(self, vpc_collector, mock_ec2_client):
        """Test _list_vpc_peering_connections filters by accepter account ID."""
        mock_paginator = MagicMock()
        mock_ec2_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [
            {
                "VpcPeeringConnections": [
                    {
                        "VpcPeeringConnectionId": "pcx-1",
                        "RequesterVpcInfo": {"VpcId": "vpc-1", "OwnerId": "999999999999"},
                        "AccepterVpcInfo": {"VpcId": "vpc-2", "OwnerId": "123456789012"},
                        "Status": {"Code": "active"},
                    }
                ]
            }
        ]

        result = vpc_collector._list_vpc_peering_connections(mock_ec2_client)

        # Should include pcx-1 (accepter matches account_id)
        assert len(result) == 1
        assert result[0]["VpcPeeringConnectionId"] == "pcx-1"

    def test_list_vpc_peering_connections_with_expiration(self, vpc_collector, mock_ec2_client):
        """Test _list_vpc_peering_connections with ExpirationTime."""
        mock_paginator = MagicMock()
        mock_ec2_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [
            {
                "VpcPeeringConnections": [
                    {
                        "VpcPeeringConnectionId": "pcx-1",
                        "RequesterVpcInfo": {"VpcId": "vpc-1", "OwnerId": "123456789012"},
                        "AccepterVpcInfo": {"VpcId": "vpc-2", "OwnerId": "999999999999"},
                        "Status": {"Code": "expired", "Message": "Expired"},
                        "ExpirationTime": datetime(2024, 1, 1),
                        "Tags": [],
                    }
                ]
            }
        ]

        result = vpc_collector._list_vpc_peering_connections(mock_ec2_client)

        assert len(result) == 1
        assert result[0]["ExpirationTime"] is not None
        assert result[0]["StatusMessage"] == "Expired"

    def test_list_vpc_peering_connections_unauthorized(self, vpc_collector, mock_ec2_client):
        """Test _list_vpc_peering_connections with UnauthorizedOperation error."""
        mock_paginator = MagicMock()
        mock_ec2_client.get_paginator.return_value = mock_paginator
        error_response = {"Error": {"Code": "UnauthorizedOperation"}}
        mock_paginator.paginate.side_effect = ClientError(error_response, "describe_vpc_peering_connections")

        result = vpc_collector._list_vpc_peering_connections(mock_ec2_client)

        assert result == []

    def test_list_vpc_peering_connections_other_error(self, vpc_collector, mock_ec2_client):
        """Test _list_vpc_peering_connections with other ClientError."""
        mock_paginator = MagicMock()
        mock_ec2_client.get_paginator.return_value = mock_paginator
        error_response = {"Error": {"Code": "InternalError"}}
        mock_paginator.paginate.side_effect = ClientError(error_response, "describe_vpc_peering_connections")

        result = vpc_collector._list_vpc_peering_connections(mock_ec2_client)

        assert result == []

    def test_list_vpc_peering_connections_no_match_filter(self, vpc_collector, mock_ec2_client):
        """Test _list_vpc_peering_connections filters out non-matching peering connections."""
        mock_paginator = MagicMock()
        mock_ec2_client.get_paginator.return_value = mock_paginator
        mock_paginator.paginate.return_value = [
            {
                "VpcPeeringConnections": [
                    {
                        "VpcPeeringConnectionId": "pcx-1",
                        "RequesterVpcInfo": {"VpcId": "vpc-1", "OwnerId": "888888888888"},
                        "AccepterVpcInfo": {"VpcId": "vpc-2", "OwnerId": "999999999999"},
                        "Status": {"Code": "active"},
                    }
                ]
            }
        ]

        result = vpc_collector._list_vpc_peering_connections(mock_ec2_client)

        # Should not include pcx-1 (neither requester nor accepter matches account_id)
        assert len(result) == 0

    # Test collect method

    def test_collect_success(self, vpc_collector, mock_session):
        """Test collect method with successful API calls."""
        mock_ec2_client = MagicMock()
        mock_session.client.return_value = mock_ec2_client

        # Mock all list methods
        with patch.object(vpc_collector, "_list_vpcs") as mock_vpcs, patch.object(
            vpc_collector, "_list_subnets"
        ) as mock_subnets, patch.object(vpc_collector, "_list_security_groups") as mock_sgs, patch.object(
            vpc_collector, "_list_network_acls"
        ) as mock_acls, patch.object(
            vpc_collector, "_list_route_tables"
        ) as mock_route_tables, patch.object(
            vpc_collector, "_list_internet_gateways"
        ) as mock_igws, patch.object(
            vpc_collector, "_list_nat_gateways"
        ) as mock_nats, patch.object(
            vpc_collector, "_list_vpc_endpoints"
        ) as mock_endpoints, patch.object(
            vpc_collector, "_list_vpc_peering_connections"
        ) as mock_peering:
            mock_vpcs.return_value = [{"VpcId": "vpc-1"}]
            mock_subnets.return_value = [{"SubnetId": "subnet-1"}]
            mock_sgs.return_value = [{"GroupId": "sg-1"}]
            mock_acls.return_value = [{"NetworkAclId": "acl-1"}]
            mock_route_tables.return_value = [{"RouteTableId": "rtb-1"}]
            mock_igws.return_value = [{"InternetGatewayId": "igw-1"}]
            mock_nats.return_value = [{"NatGatewayId": "nat-1"}]
            mock_endpoints.return_value = [{"VpcEndpointId": "vpce-1"}]
            mock_peering.return_value = [{"VpcPeeringConnectionId": "pcx-1"}]

            result = vpc_collector.collect()

        assert len(result["VPCs"]) == 1
        assert len(result["Subnets"]) == 1
        assert len(result["SecurityGroups"]) == 1
        assert len(result["NetworkACLs"]) == 1
        assert len(result["RouteTables"]) == 1
        assert len(result["InternetGateways"]) == 1
        assert len(result["NATGateways"]) == 1
        assert len(result["VPCEndpoints"]) == 1
        assert len(result["VPCPeeringConnections"]) == 1

    def test_collect_with_client_error(self, vpc_collector, mock_session):
        """Test collect method with ClientError."""
        mock_ec2_client = MagicMock()
        mock_session.client.return_value = mock_ec2_client

        error_response = {"Error": {"Code": "AccessDeniedException"}}

        with patch.object(vpc_collector, "_list_vpcs") as mock_vpcs:
            mock_vpcs.side_effect = ClientError(error_response, "describe_vpcs")

            result = vpc_collector.collect()

        # Should return empty structure but not crash
        assert result["VPCs"] == []

    def test_collect_with_unexpected_error(self, vpc_collector, mock_session):
        """Test collect method with unexpected error."""
        mock_ec2_client = MagicMock()
        mock_session.client.return_value = mock_ec2_client

        with patch.object(vpc_collector, "_list_vpcs") as mock_vpcs:
            mock_vpcs.side_effect = Exception("Unexpected error")

            result = vpc_collector.collect()

        # Should return empty structure but not crash
        assert result["VPCs"] == []

    def test_collect_empty_results(self, vpc_collector, mock_session):
        """Test collect method with no VPC resources."""
        mock_ec2_client = MagicMock()
        mock_session.client.return_value = mock_ec2_client

        # Mock all list methods to return empty lists
        with patch.object(vpc_collector, "_list_vpcs") as mock_vpcs, patch.object(
            vpc_collector, "_list_subnets"
        ) as mock_subnets, patch.object(vpc_collector, "_list_security_groups") as mock_sgs, patch.object(
            vpc_collector, "_list_network_acls"
        ) as mock_acls, patch.object(
            vpc_collector, "_list_route_tables"
        ) as mock_route_tables, patch.object(
            vpc_collector, "_list_internet_gateways"
        ) as mock_igws, patch.object(
            vpc_collector, "_list_nat_gateways"
        ) as mock_nats, patch.object(
            vpc_collector, "_list_vpc_endpoints"
        ) as mock_endpoints, patch.object(
            vpc_collector, "_list_vpc_peering_connections"
        ) as mock_peering:
            mock_vpcs.return_value = []
            mock_subnets.return_value = []
            mock_sgs.return_value = []
            mock_acls.return_value = []
            mock_route_tables.return_value = []
            mock_igws.return_value = []
            mock_nats.return_value = []
            mock_endpoints.return_value = []
            mock_peering.return_value = []

            result = vpc_collector.collect()

        assert result["VPCs"] == []
        assert result["Subnets"] == []
        assert result["SecurityGroups"] == []
        assert result["NetworkACLs"] == []
        assert result["RouteTables"] == []
        assert result["InternetGateways"] == []
        assert result["NATGateways"] == []
        assert result["VPCEndpoints"] == []
        assert result["VPCPeeringConnections"] == []
