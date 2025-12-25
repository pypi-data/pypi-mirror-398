"""AWS VPC resource collection."""

import logging
from typing import Any, Dict, List, Optional

from botocore.exceptions import ClientError

from regscale.integrations.commercial.aws.inventory.base import BaseCollector

logger = logging.getLogger("regscale")


class VPCCollector(BaseCollector):
    """Collector for AWS VPC resources."""

    def __init__(
        self, session: Any, region: str, account_id: Optional[str] = None, tags: Optional[Dict[str, str]] = None
    ):
        """
        Initialize VPC collector.

        :param session: AWS session to use for API calls
        :param str region: AWS region to collect from
        :param str account_id: Optional AWS account ID to filter resources
        :param dict tags: Optional tags to filter resources (key-value pairs)
        """
        super().__init__(session, region)
        self.account_id = account_id
        self.tags = tags or {}

    def collect(self) -> Dict[str, Any]:
        """
        Collect AWS VPC resources.

        :return: Dictionary containing VPC information
        :rtype: Dict[str, Any]
        """
        result = {
            "VPCs": [],
            "Subnets": [],
            "SecurityGroups": [],
            "NetworkACLs": [],
            "RouteTables": [],
            "InternetGateways": [],
            "NATGateways": [],
            "VPCEndpoints": [],
            "VPCPeeringConnections": [],
        }

        try:
            client = self._get_client("ec2")

            # Get all VPCs
            vpcs = self._list_vpcs(client)
            result["VPCs"] = vpcs

            # Get subnets
            subnets = self._list_subnets(client)
            result["Subnets"] = subnets

            # Get security groups
            security_groups = self._list_security_groups(client)
            result["SecurityGroups"] = security_groups

            # Get network ACLs
            network_acls = self._list_network_acls(client)
            result["NetworkACLs"] = network_acls

            # Get route tables
            route_tables = self._list_route_tables(client)
            result["RouteTables"] = route_tables

            # Get internet gateways
            internet_gateways = self._list_internet_gateways(client)
            result["InternetGateways"] = internet_gateways

            # Get NAT gateways
            nat_gateways = self._list_nat_gateways(client)
            result["NATGateways"] = nat_gateways

            # Get VPC endpoints
            vpc_endpoints = self._list_vpc_endpoints(client)
            result["VPCEndpoints"] = vpc_endpoints

            # Get VPC peering connections
            vpc_peering = self._list_vpc_peering_connections(client)
            result["VPCPeeringConnections"] = vpc_peering

            logger.info(
                f"Collected {len(vpcs)} VPC(s), {len(subnets)} subnet(s), "
                f"{len(security_groups)} security group(s) from {self.region}"
            )

        except ClientError as e:
            self._handle_error(e, "VPC resources")
        except Exception as e:
            logger.error(f"Unexpected error collecting VPC resources: {e}", exc_info=True)

        return result

    def _list_vpcs(self, client: Any) -> List[Dict[str, Any]]:
        """
        List VPCs with enhanced details.

        :param client: EC2 client
        :return: List of VPC information
        :rtype: List[Dict[str, Any]]
        """
        vpcs = []
        try:
            paginator = client.get_paginator("describe_vpcs")

            for page in paginator.paginate():
                for vpc in page.get("Vpcs", []):
                    # Filter by account ID if specified
                    if self.account_id and not self._matches_account_id(vpc.get("OwnerId", "")):
                        continue

                    # Filter by tags if specified
                    vpc_tags = self._convert_tags_to_dict(vpc.get("Tags", []))
                    if self.tags and not self._matches_tags(vpc_tags):
                        logger.debug(f"Skipping VPC {vpc.get('VpcId')} - does not match tag filters")
                        continue

                    vpc_dict = {
                        "Region": self.region,
                        "VpcId": vpc.get("VpcId"),
                        "OwnerId": vpc.get("OwnerId"),
                        "CidrBlock": vpc.get("CidrBlock"),
                        "CidrBlockAssociationSet": vpc.get("CidrBlockAssociationSet", []),
                        "Ipv6CidrBlockAssociationSet": vpc.get("Ipv6CidrBlockAssociationSet", []),
                        "State": vpc.get("State"),
                        "IsDefault": vpc.get("IsDefault", False),
                        "DhcpOptionsId": vpc.get("DhcpOptionsId"),
                        "InstanceTenancy": vpc.get("InstanceTenancy"),
                        "Tags": vpc.get("Tags", []),
                    }

                    # Get VPC attributes
                    vpc_attributes = self._get_vpc_attributes(client, vpc["VpcId"])
                    vpc_dict.update(vpc_attributes)

                    vpcs.append(vpc_dict)

        except ClientError as e:
            if e.response["Error"]["Code"] == "UnauthorizedOperation":
                logger.warning(f"Unauthorized to list VPCs in {self.region}")
            else:
                logger.error(f"Error listing VPCs: {e}")

        return vpcs

    def _get_vpc_attributes(self, client: Any, vpc_id: str) -> Dict[str, Any]:
        """
        Get VPC attributes.

        :param client: EC2 client
        :param str vpc_id: VPC ID
        :return: VPC attributes
        :rtype: Dict[str, Any]
        """
        attributes = {}
        try:
            # Get DNS support
            dns_support = client.describe_vpc_attribute(VpcId=vpc_id, Attribute="enableDnsSupport")
            attributes["EnableDnsSupport"] = dns_support.get("EnableDnsSupport", {}).get("Value", False)

            # Get DNS hostnames
            dns_hostnames = client.describe_vpc_attribute(VpcId=vpc_id, Attribute="enableDnsHostnames")
            attributes["EnableDnsHostnames"] = dns_hostnames.get("EnableDnsHostnames", {}).get("Value", False)

        except ClientError as e:
            if e.response["Error"]["Code"] not in ["UnauthorizedOperation", "InvalidVpcID.NotFound"]:
                logger.debug(f"Error getting attributes for VPC {vpc_id}: {e}")

        return attributes

    def _list_subnets(self, client: Any) -> List[Dict[str, Any]]:
        """
        List subnets.

        :param client: EC2 client
        :return: List of subnet information
        :rtype: List[Dict[str, Any]]
        """
        subnets = []
        try:
            paginator = client.get_paginator("describe_subnets")

            for page in paginator.paginate():
                for subnet in page.get("Subnets", []):
                    # Filter by account ID if specified
                    if self.account_id and not self._matches_account_id(subnet.get("OwnerId", "")):
                        continue

                    # Filter by tags if specified
                    subnet_tags = self._convert_tags_to_dict(subnet.get("Tags", []))
                    if self.tags and not self._matches_tags(subnet_tags):
                        logger.debug(f"Skipping subnet {subnet.get('SubnetId')} - does not match tag filters")
                        continue

                    subnets.append(
                        {
                            "Region": self.region,
                            "SubnetId": subnet.get("SubnetId"),
                            "VpcId": subnet.get("VpcId"),
                            "OwnerId": subnet.get("OwnerId"),
                            "AvailabilityZone": subnet.get("AvailabilityZone"),
                            "AvailabilityZoneId": subnet.get("AvailabilityZoneId"),
                            "CidrBlock": subnet.get("CidrBlock"),
                            "Ipv6CidrBlockAssociationSet": subnet.get("Ipv6CidrBlockAssociationSet", []),
                            "State": subnet.get("State"),
                            "AvailableIpAddressCount": subnet.get("AvailableIpAddressCount"),
                            "DefaultForAz": subnet.get("DefaultForAz", False),
                            "MapPublicIpOnLaunch": subnet.get("MapPublicIpOnLaunch", False),
                            "AssignIpv6AddressOnCreation": subnet.get("AssignIpv6AddressOnCreation", False),
                            "Tags": subnet.get("Tags", []),
                        }
                    )

        except ClientError as e:
            if e.response["Error"]["Code"] == "UnauthorizedOperation":
                logger.warning(f"Unauthorized to list subnets in {self.region}")
            else:
                logger.error(f"Error listing subnets: {e}")

        return subnets

    def _list_security_groups(self, client: Any) -> List[Dict[str, Any]]:
        """
        List security groups.

        :param client: EC2 client
        :return: List of security group information
        :rtype: List[Dict[str, Any]]
        """
        security_groups = []
        try:
            paginator = client.get_paginator("describe_security_groups")

            for page in paginator.paginate():
                for sg in page.get("SecurityGroups", []):
                    # Filter by account ID if specified
                    if self.account_id and not self._matches_account_id(sg.get("OwnerId", "")):
                        continue

                    # Filter by tags if specified
                    sg_tags = self._convert_tags_to_dict(sg.get("Tags", []))
                    if self.tags and not self._matches_tags(sg_tags):
                        logger.debug(f"Skipping security group {sg.get('GroupId')} - does not match tag filters")
                        continue

                    security_groups.append(
                        {
                            "Region": self.region,
                            "GroupId": sg.get("GroupId"),
                            "GroupName": sg.get("GroupName"),
                            "VpcId": sg.get("VpcId"),
                            "OwnerId": sg.get("OwnerId"),
                            "Description": sg.get("Description"),
                            "IpPermissions": sg.get("IpPermissions", []),
                            "IpPermissionsEgress": sg.get("IpPermissionsEgress", []),
                            "Tags": sg.get("Tags", []),
                        }
                    )

        except ClientError as e:
            if e.response["Error"]["Code"] == "UnauthorizedOperation":
                logger.warning(f"Unauthorized to list security groups in {self.region}")
            else:
                logger.error(f"Error listing security groups: {e}")

        return security_groups

    def _list_network_acls(self, client: Any) -> List[Dict[str, Any]]:
        """
        List network ACLs.

        :param client: EC2 client
        :return: List of network ACL information
        :rtype: List[Dict[str, Any]]
        """
        network_acls = []
        try:
            paginator = client.get_paginator("describe_network_acls")

            for page in paginator.paginate():
                for acl in page.get("NetworkAcls", []):
                    # Filter by account ID if specified
                    if self.account_id and not self._matches_account_id(acl.get("OwnerId", "")):
                        continue

                    # Filter by tags if specified
                    acl_tags = self._convert_tags_to_dict(acl.get("Tags", []))
                    if self.tags and not self._matches_tags(acl_tags):
                        logger.debug(f"Skipping network ACL {acl.get('NetworkAclId')} - does not match tag filters")
                        continue

                    network_acls.append(
                        {
                            "Region": self.region,
                            "NetworkAclId": acl.get("NetworkAclId"),
                            "VpcId": acl.get("VpcId"),
                            "OwnerId": acl.get("OwnerId"),
                            "IsDefault": acl.get("IsDefault", False),
                            "Entries": acl.get("Entries", []),
                            "Associations": acl.get("Associations", []),
                            "Tags": acl.get("Tags", []),
                        }
                    )

        except ClientError as e:
            if e.response["Error"]["Code"] == "UnauthorizedOperation":
                logger.warning(f"Unauthorized to list network ACLs in {self.region}")
            else:
                logger.error(f"Error listing network ACLs: {e}")

        return network_acls

    def _list_route_tables(self, client: Any) -> List[Dict[str, Any]]:
        """
        List route tables.

        :param client: EC2 client
        :return: List of route table information
        :rtype: List[Dict[str, Any]]
        """
        route_tables = []
        try:
            paginator = client.get_paginator("describe_route_tables")

            for page in paginator.paginate():
                for rt in page.get("RouteTables", []):
                    # Filter by account ID if specified
                    if self.account_id and not self._matches_account_id(rt.get("OwnerId", "")):
                        continue

                    # Filter by tags if specified
                    rt_tags = self._convert_tags_to_dict(rt.get("Tags", []))
                    if self.tags and not self._matches_tags(rt_tags):
                        logger.debug(f"Skipping route table {rt.get('RouteTableId')} - does not match tag filters")
                        continue

                    route_tables.append(
                        {
                            "Region": self.region,
                            "RouteTableId": rt.get("RouteTableId"),
                            "VpcId": rt.get("VpcId"),
                            "OwnerId": rt.get("OwnerId"),
                            "Routes": rt.get("Routes", []),
                            "Associations": rt.get("Associations", []),
                            "PropagatingVgws": rt.get("PropagatingVgws", []),
                            "Tags": rt.get("Tags", []),
                        }
                    )

        except ClientError as e:
            if e.response["Error"]["Code"] == "UnauthorizedOperation":
                logger.warning(f"Unauthorized to list route tables in {self.region}")
            else:
                logger.error(f"Error listing route tables: {e}")

        return route_tables

    def _list_internet_gateways(self, client: Any) -> List[Dict[str, Any]]:
        """
        List internet gateways.

        :param client: EC2 client
        :return: List of internet gateway information
        :rtype: List[Dict[str, Any]]
        """
        internet_gateways = []
        try:
            paginator = client.get_paginator("describe_internet_gateways")

            for page in paginator.paginate():
                for igw in page.get("InternetGateways", []):
                    # Filter by account ID if specified
                    if self.account_id and not self._matches_account_id(igw.get("OwnerId", "")):
                        continue

                    # Filter by tags if specified
                    igw_tags = self._convert_tags_to_dict(igw.get("Tags", []))
                    if self.tags and not self._matches_tags(igw_tags):
                        logger.debug(
                            f"Skipping internet gateway {igw.get('InternetGatewayId')} - does not match tag filters"
                        )
                        continue

                    internet_gateways.append(
                        {
                            "Region": self.region,
                            "InternetGatewayId": igw.get("InternetGatewayId"),
                            "OwnerId": igw.get("OwnerId"),
                            "Attachments": igw.get("Attachments", []),
                            "Tags": igw.get("Tags", []),
                        }
                    )

        except ClientError as e:
            if e.response["Error"]["Code"] == "UnauthorizedOperation":
                logger.warning(f"Unauthorized to list internet gateways in {self.region}")
            else:
                logger.error(f"Error listing internet gateways: {e}")

        return internet_gateways

    def _list_nat_gateways(self, client: Any) -> List[Dict[str, Any]]:
        """
        List NAT gateways.

        :param client: EC2 client
        :return: List of NAT gateway information
        :rtype: List[Dict[str, Any]]
        """
        nat_gateways = []
        try:
            paginator = client.get_paginator("describe_nat_gateways")

            for page in paginator.paginate():
                for nat in page.get("NatGateways", []):
                    # Filter by tags if specified
                    nat_tags = self._convert_tags_to_dict(nat.get("Tags", []))
                    if self.tags and not self._matches_tags(nat_tags):
                        logger.debug(f"Skipping NAT gateway {nat.get('NatGatewayId')} - does not match tag filters")
                        continue

                    nat_gateways.append(
                        {
                            "Region": self.region,
                            "NatGatewayId": nat.get("NatGatewayId"),
                            "VpcId": nat.get("VpcId"),
                            "SubnetId": nat.get("SubnetId"),
                            "State": nat.get("State"),
                            "ConnectivityType": nat.get("ConnectivityType"),
                            "NatGatewayAddresses": nat.get("NatGatewayAddresses", []),
                            "CreateTime": str(nat.get("CreateTime")),
                            "DeleteTime": str(nat.get("DeleteTime")) if nat.get("DeleteTime") else None,
                            "Tags": nat.get("Tags", []),
                        }
                    )

        except ClientError as e:
            if e.response["Error"]["Code"] == "UnauthorizedOperation":
                logger.warning(f"Unauthorized to list NAT gateways in {self.region}")
            else:
                logger.error(f"Error listing NAT gateways: {e}")

        return nat_gateways

    def _list_vpc_endpoints(self, client: Any) -> List[Dict[str, Any]]:
        """
        List VPC endpoints.

        :param client: EC2 client
        :return: List of VPC endpoint information
        :rtype: List[Dict[str, Any]]
        """
        vpc_endpoints = []
        try:
            paginator = client.get_paginator("describe_vpc_endpoints")

            for page in paginator.paginate():
                for endpoint in page.get("VpcEndpoints", []):
                    # Filter by account ID if specified
                    if self.account_id and not self._matches_account_id(endpoint.get("OwnerId", "")):
                        continue

                    # Filter by tags if specified
                    endpoint_tags = self._convert_tags_to_dict(endpoint.get("Tags", []))
                    if self.tags and not self._matches_tags(endpoint_tags):
                        logger.debug(
                            f"Skipping VPC endpoint {endpoint.get('VpcEndpointId')} - does not match tag filters"
                        )
                        continue

                    vpc_endpoints.append(
                        {
                            "Region": self.region,
                            "VpcEndpointId": endpoint.get("VpcEndpointId"),
                            "VpcId": endpoint.get("VpcId"),
                            "OwnerId": endpoint.get("OwnerId"),
                            "ServiceName": endpoint.get("ServiceName"),
                            "VpcEndpointType": endpoint.get("VpcEndpointType"),
                            "State": endpoint.get("State"),
                            "PolicyDocument": endpoint.get("PolicyDocument"),
                            "SubnetIds": endpoint.get("SubnetIds", []),
                            "RouteTableIds": endpoint.get("RouteTableIds", []),
                            "Groups": endpoint.get("Groups", []),
                            "PrivateDnsEnabled": endpoint.get("PrivateDnsEnabled", False),
                            "DnsEntries": endpoint.get("DnsEntries", []),
                            "CreationTimestamp": str(endpoint.get("CreationTimestamp")),
                            "Tags": endpoint.get("Tags", []),
                        }
                    )

        except ClientError as e:
            if e.response["Error"]["Code"] == "UnauthorizedOperation":
                logger.warning(f"Unauthorized to list VPC endpoints in {self.region}")
            else:
                logger.error(f"Error listing VPC endpoints: {e}")

        return vpc_endpoints

    def _list_vpc_peering_connections(self, client: Any) -> List[Dict[str, Any]]:
        """
        List VPC peering connections.

        :param client: EC2 client
        :return: List of VPC peering connection information
        :rtype: List[Dict[str, Any]]
        """
        vpc_peering = []
        try:
            paginator = client.get_paginator("describe_vpc_peering_connections")

            for page in paginator.paginate():
                for peering in page.get("VpcPeeringConnections", []):
                    if self._should_skip_peering_connection(peering):
                        continue

                    peering_dict = self._build_peering_connection_dict(peering)
                    vpc_peering.append(peering_dict)

        except ClientError as e:
            if e.response["Error"]["Code"] == "UnauthorizedOperation":
                logger.warning(f"Unauthorized to list VPC peering connections in {self.region}")
            else:
                logger.error(f"Error listing VPC peering connections: {e}")

        return vpc_peering

    def _should_skip_peering_connection(self, peering: Dict[str, Any]) -> bool:
        """
        Check if peering connection should be skipped based on filters.

        :param dict peering: Peering connection data
        :return: True if should be skipped
        :rtype: bool
        """
        if not self._matches_peering_account_filter(peering):
            return True

        if not self._matches_peering_tag_filter(peering):
            return True

        return False

    def _matches_peering_account_filter(self, peering: Dict[str, Any]) -> bool:
        """
        Check if peering connection matches account ID filter.

        :param dict peering: Peering connection data
        :return: True if matches or no filter specified
        :rtype: bool
        """
        if not self.account_id:
            return True

        requester_owner = peering.get("RequesterVpcInfo", {}).get("OwnerId", "")
        accepter_owner = peering.get("AccepterVpcInfo", {}).get("OwnerId", "")
        return self._matches_account_id(requester_owner) or self._matches_account_id(accepter_owner)

    def _matches_peering_tag_filter(self, peering: Dict[str, Any]) -> bool:
        """
        Check if peering connection matches tag filter.

        :param dict peering: Peering connection data
        :return: True if matches or no filter specified
        :rtype: bool
        """
        if not self.tags:
            return True

        peering_tags = self._convert_tags_to_dict(peering.get("Tags", []))
        matches = self._matches_tags(peering_tags)

        if not matches:
            logger.debug(f"Skipping VPC peering {peering.get('VpcPeeringConnectionId')} - does not match tag filters")

        return matches

    def _build_peering_connection_dict(self, peering: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build dictionary representation of peering connection.

        :param dict peering: Peering connection data
        :return: Formatted peering connection dictionary
        :rtype: Dict[str, Any]
        """
        requester_info = peering.get("RequesterVpcInfo", {})
        accepter_info = peering.get("AccepterVpcInfo", {})
        status_info = peering.get("Status", {})

        return {
            "Region": self.region,
            "VpcPeeringConnectionId": peering.get("VpcPeeringConnectionId"),
            "RequesterVpcInfo": {
                "VpcId": requester_info.get("VpcId"),
                "OwnerId": requester_info.get("OwnerId"),
                "CidrBlock": requester_info.get("CidrBlock"),
                "Region": requester_info.get("Region"),
            },
            "AccepterVpcInfo": {
                "VpcId": accepter_info.get("VpcId"),
                "OwnerId": accepter_info.get("OwnerId"),
                "CidrBlock": accepter_info.get("CidrBlock"),
                "Region": accepter_info.get("Region"),
            },
            "Status": status_info.get("Code"),
            "StatusMessage": status_info.get("Message"),
            "ExpirationTime": str(peering.get("ExpirationTime")) if peering.get("ExpirationTime") else None,
            "Tags": peering.get("Tags", []),
        }

    def _matches_account_id(self, owner_id: str) -> bool:
        """
        Check if owner ID matches the specified account ID.

        :param str owner_id: Owner ID to check
        :return: True if matches or no account_id filter specified
        :rtype: bool
        """
        if not self.account_id:
            return True
        return owner_id == self.account_id

    def _convert_tags_to_dict(self, tags_list: List[Dict[str, str]]) -> Dict[str, str]:
        """
        Convert AWS tags list format to dictionary.

        :param list tags_list: List of tags in format [{"Key": "k", "Value": "v"}]
        :return: Dictionary of tags {key: value}
        :rtype: Dict[str, str]
        """
        return {tag.get("Key", ""): tag.get("Value", "") for tag in tags_list}

    def _matches_tags(self, resource_tags: Dict[str, str]) -> bool:
        """
        Check if resource tags match the specified filter tags.

        :param dict resource_tags: Tags on the resource
        :return: True if all filter tags match
        :rtype: bool
        """
        if not self.tags:
            return True

        # All filter tags must match
        for key, value in self.tags.items():
            if resource_tags.get(key) != value:
                return False

        return True
