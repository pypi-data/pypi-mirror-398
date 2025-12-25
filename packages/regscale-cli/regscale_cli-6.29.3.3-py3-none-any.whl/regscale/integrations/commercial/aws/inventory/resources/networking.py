"""AWS networking resource collectors."""

from typing import Dict, List, Any, Optional

from regscale.integrations.commercial.aws.inventory.resources.vpc import VPCCollector
from ..base import BaseCollector


class NetworkingCollector(BaseCollector):
    """Collector for AWS networking resources."""

    def __init__(
        self,
        session: Any,
        region: str,
        account_id: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        enabled_services: Optional[Dict[str, bool]] = None,
    ):
        """
        Initialize networking collector.

        :param session: AWS session to use for API calls
        :param str region: AWS region to collect from
        :param str account_id: Optional AWS account ID to filter resources
        :param dict tags: Optional tags to filter resources (key-value pairs)
        :param dict enabled_services: Optional dict of service names to boolean flags for enabling/disabling collection
        """
        super().__init__(session, region)
        self.account_id = account_id
        self.tags = tags or {}
        self.enabled_services = enabled_services or {}

    def get_vpcs(self) -> Dict[str, Any]:
        """
        Get information about VPC resources.

        :return: Dictionary containing VPC resource information
        :rtype: Dict[str, Any]
        """
        try:
            vpc_collector = VPCCollector(self.session, self.region, self.account_id, self.tags)
            return vpc_collector.collect()
        except Exception as e:
            self._handle_error(e, "VPC resources")
            return {
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

    def get_elastic_ips(self) -> List[Dict[str, Any]]:
        """
        Get information about Elastic IPs.

        :return: List of Elastic IP information
        :rtype: List[Dict[str, Any]]
        """
        eips = []
        try:
            ec2 = self._get_client("ec2")
            addresses = ec2.describe_addresses().get("Addresses", [])

            for addr in addresses:
                # Filter by tags if specified
                eip_tags = self._convert_tags_to_dict(addr.get("Tags", []))
                if self.tags and not self._matches_tags(eip_tags):
                    continue

                eips.append(
                    {
                        "Region": self.region,
                        "PublicIp": addr.get("PublicIp"),
                        "AllocationId": addr.get("AllocationId"),
                        "InstanceId": addr.get("InstanceId"),
                        "NetworkInterfaceId": addr.get("NetworkInterfaceId"),
                        "NetworkInterfaceOwner": addr.get("NetworkInterfaceOwnerId"),
                        "PrivateIpAddress": addr.get("PrivateIpAddress"),
                        "Tags": addr.get("Tags", []),
                    }
                )
        except Exception as e:
            self._handle_error(e, "Elastic IPs")
        return eips

    def get_load_balancers(self) -> List[Dict[str, Any]]:
        """
        Get information about Load Balancers (ALB/NLB).

        :return: List of Load Balancer information
        :rtype: List[Dict[str, Any]]
        """
        lbs = []
        try:
            elb = self._get_client("elbv2")
            paginator = elb.get_paginator("describe_load_balancers")

            for page in paginator.paginate():
                for lb in page.get("LoadBalancers", []):
                    # Get target groups for this LB
                    target_groups = []
                    tg_paginator = elb.get_paginator("describe_target_groups")
                    for tg_page in tg_paginator.paginate(LoadBalancerArn=lb["LoadBalancerArn"]):
                        target_groups.extend(tg_page.get("TargetGroups", []))

                    lbs.append(
                        {
                            "Region": self.region,
                            "LoadBalancerName": lb.get("LoadBalancerName"),
                            "LoadBalancerArn": lb.get("LoadBalancerArn"),
                            "DNSName": lb.get("DNSName"),
                            "Type": lb.get("Type"),
                            "Scheme": lb.get("Scheme"),
                            "VpcId": lb.get("VpcId"),
                            "State": lb.get("State", {}).get("Code"),
                            "AvailabilityZones": lb.get("AvailabilityZones", []),
                            "SecurityGroups": lb.get("SecurityGroups", []),
                            "Listeners": lb.get("Listeners", []),
                            "TargetGroups": [
                                {
                                    "TargetGroupName": tg.get("TargetGroupName"),
                                    "TargetGroupArn": tg.get("TargetGroupArn"),
                                    "Protocol": tg.get("Protocol"),
                                    "Port": tg.get("Port"),
                                    "HealthCheckProtocol": tg.get("HealthCheckProtocol"),
                                    "HealthCheckPort": tg.get("HealthCheckPort"),
                                    "HealthCheckPath": tg.get("HealthCheckPath"),
                                }
                                for tg in target_groups
                            ],
                        }
                    )
        except Exception as e:
            self._handle_error(e, "Load Balancers")
        return lbs

    def get_cloudfront_distributions(self) -> List[Dict[str, Any]]:
        """
        Get information about CloudFront distributions.

        :return: List of CloudFront distribution information
        :rtype: List[Dict[str, Any]]
        """
        distributions = []
        try:
            cloudfront = self._get_client("cloudfront")
            paginator = cloudfront.get_paginator("list_distributions")

            for page in paginator.paginate():
                for dist in page.get("DistributionList", {}).get("Items", []):
                    distributions.append(
                        {
                            "Region": self.region,
                            "Id": dist.get("Id"),
                            "DomainName": dist.get("DomainName"),
                            "Status": dist.get("Status"),
                            "Enabled": dist.get("Enabled"),
                            "Origins": dist.get("Origins", {}).get("Items", []),
                            "DefaultCacheBehavior": dist.get("DefaultCacheBehavior", {}),
                            "CacheBehaviors": dist.get("CacheBehaviors", {}).get("Items", []),
                            "CustomErrorResponses": dist.get("CustomErrorResponses", {}).get("Items", []),
                            "Comment": dist.get("Comment"),
                            "PriceClass": dist.get("PriceClass"),
                            "LastModifiedTime": str(dist.get("LastModifiedTime")),
                            "WebACLId": dist.get("WebACLId"),
                        }
                    )
        except Exception as e:
            self._handle_error(e, "CloudFront distributions")
        return distributions

    def get_route53_info(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get information about Route53 hosted zones and records.

        :return: Dictionary containing Route53 information
        :rtype: Dict[str, List[Dict[str, Any]]]
        """
        route53_info = {"HostedZones": [], "Records": []}
        try:
            route53 = self._get_client("route53")

            # Get hosted zones
            paginator = route53.get_paginator("list_hosted_zones")
            for page in paginator.paginate():
                for zone in page.get("HostedZones", []):
                    try:
                        # Get records for this zone
                        records = []
                        record_paginator = route53.get_paginator("list_resource_record_sets")
                        for record_page in record_paginator.paginate(HostedZoneId=zone["Id"]):
                            for record in record_page.get("ResourceRecordSets", []):
                                records.append(
                                    {
                                        "Name": record.get("Name"),
                                        "Type": record.get("Type"),
                                        "TTL": record.get("TTL"),
                                        "ResourceRecords": record.get("ResourceRecords", []),
                                        "AliasTarget": record.get("AliasTarget"),
                                        "Weight": record.get("Weight"),
                                        "Region": record.get("Region"),
                                        "GeoLocation": record.get("GeoLocation"),
                                        "Failover": record.get("Failover"),
                                        "MultiValueAnswer": record.get("MultiValueAnswer"),
                                        "HealthCheckId": record.get("HealthCheckId"),
                                    }
                                )

                        route53_info["HostedZones"].append(
                            {
                                "Id": zone.get("Id"),
                                "Name": zone.get("Name"),
                                "CallerReference": zone.get("CallerReference"),
                                "Config": zone.get("Config", {}),
                                "ResourceRecordSetCount": zone.get("ResourceRecordSetCount"),
                                "Records": records,
                            }
                        )
                    except Exception as e:
                        self._handle_error(e, f"Route53 zone {zone['Name']}")
        except Exception as e:
            self._handle_error(e, "Route53 zones")
        return route53_info

    def get_direct_connect_connections(self) -> List[Dict[str, Any]]:
        """
        Get information about AWS Direct Connect connections.

        :return: List of Direct Connect connection information
        :rtype: List[Dict[str, Any]]
        """
        connections = []
        try:
            dx_client = self._get_client("directconnect")
            response = dx_client.describe_connections()

            for conn in response.get("connections", []):
                conn_arn = (
                    f"arn:aws:directconnect:{self.region}:{conn.get('ownerAccount', '')}:"
                    f"dxcon/{conn.get('connectionId')}"
                )

                if not self._matches_account(conn_arn):
                    continue

                if not self._matches_tags(conn.get("tags", [])):
                    continue

                connections.append(
                    {
                        "Region": self.region,
                        "ConnectionId": conn.get("connectionId"),
                        "ConnectionName": conn.get("connectionName"),
                        "ConnectionState": conn.get("connectionState"),
                        "Bandwidth": conn.get("bandwidth"),
                        "Location": conn.get("location"),
                        "OwnerAccount": conn.get("ownerAccount"),
                        "Tags": conn.get("tags", []),
                    }
                )
        except Exception as e:
            self._handle_error(e, "Direct Connect connections")
        return connections

    def get_transit_gateways(self) -> List[Dict[str, Any]]:
        """
        Get information about Transit Gateways.

        :return: List of Transit Gateway information
        :rtype: List[Dict[str, Any]]
        """
        gateways = []
        try:
            ec2_client = self._get_client("ec2")
            paginator = ec2_client.get_paginator("describe_transit_gateways")

            for page in paginator.paginate():
                for tgw in page.get("TransitGateways", []):
                    tgw_arn = tgw.get("TransitGatewayArn", "")

                    if not self._matches_account(tgw_arn):
                        continue

                    if not self._matches_tags(tgw.get("Tags", [])):
                        continue

                    gateways.append(
                        {
                            "Region": self.region,
                            "TransitGatewayId": tgw.get("TransitGatewayId"),
                            "TransitGatewayArn": tgw_arn,
                            "State": tgw.get("State"),
                            "OwnerId": tgw.get("OwnerId"),
                            "Description": tgw.get("Description"),
                            "CreationTime": tgw.get("CreationTime"),
                            "Tags": tgw.get("Tags", []),
                        }
                    )
        except Exception as e:
            self._handle_error(e, "Transit Gateways")
        return gateways

    def get_vpn_connections(self) -> List[Dict[str, Any]]:
        """
        Get information about VPN connections.

        :return: List of VPN connection information
        :rtype: List[Dict[str, Any]]
        """
        connections = []
        try:
            ec2_client = self._get_client("ec2")
            response = ec2_client.describe_vpn_connections()

            for vpn in response.get("VpnConnections", []):
                vpn_arn = (
                    f"arn:aws:ec2:{self.region}:{vpn.get('CustomerGatewayConfiguration', {}).get('OwnerId', '')}:"
                    f"vpn-connection/{vpn.get('VpnConnectionId')}"
                )

                if not self._matches_account(vpn_arn):
                    continue

                if not self._matches_tags(vpn.get("Tags", [])):
                    continue

                connections.append(
                    {
                        "Region": self.region,
                        "VpnConnectionId": vpn.get("VpnConnectionId"),
                        "State": vpn.get("State"),
                        "Type": vpn.get("Type"),
                        "VpnGatewayId": vpn.get("VpnGatewayId"),
                        "CustomerGatewayId": vpn.get("CustomerGatewayId"),
                        "TransitGatewayId": vpn.get("TransitGatewayId"),
                        "Tags": vpn.get("Tags", []),
                    }
                )
        except Exception as e:
            self._handle_error(e, "VPN connections")
        return connections

    def get_global_accelerators(self) -> List[Dict[str, Any]]:
        """
        Get information about Global Accelerator accelerators.
        Note: Global Accelerator is a global service that only operates in us-west-2.

        :return: List of Global Accelerator information
        :rtype: List[Dict[str, Any]]
        """
        accelerators = []
        try:
            # Global Accelerator only operates in us-west-2 region
            ga_client = self.session.client("globalaccelerator", region_name="us-west-2")
            paginator = ga_client.get_paginator("list_accelerators")

            for page in paginator.paginate():
                for accel in page.get("Accelerators", []):
                    accel_arn = accel.get("AcceleratorArn", "")

                    if not self._matches_account(accel_arn):
                        continue

                    try:
                        tags_response = ga_client.list_tags_for_resource(ResourceArn=accel_arn)
                        accel_tags = tags_response.get("Tags", [])

                        if not self._matches_tags(accel_tags):
                            continue

                        accelerators.append(
                            {
                                "Region": "us-west-2",
                                "AcceleratorArn": accel_arn,
                                "Name": accel.get("Name"),
                                "Status": accel.get("Status"),
                                "Enabled": accel.get("Enabled"),
                                "IpAddressType": accel.get("IpAddressType"),
                                "DnsName": accel.get("DnsName"),
                                "CreatedTime": accel.get("CreatedTime"),
                                "Tags": accel_tags,
                            }
                        )
                    except Exception as tag_error:
                        self._handle_error(tag_error, f"Global Accelerator tags for {accel_arn}")
                        continue

        except Exception as e:
            self._handle_error(e, "Global Accelerators")
        return accelerators

    def get_network_firewalls(self) -> List[Dict[str, Any]]:
        """
        Get information about AWS Network Firewalls.

        :return: List of Network Firewall information
        :rtype: List[Dict[str, Any]]
        """
        firewalls = []
        try:
            nfw_client = self._get_client("network-firewall")
            paginator = nfw_client.get_paginator("list_firewalls")

            for page in paginator.paginate():
                for fw_metadata in page.get("Firewalls", []):
                    fw_arn = fw_metadata.get("FirewallArn", "")

                    if not self._matches_account(fw_arn):
                        continue

                    try:
                        fw_response = nfw_client.describe_firewall(FirewallArn=fw_arn)
                        firewall = fw_response.get("Firewall", {})
                        fw_tags = firewall.get("Tags", [])

                        if not self._matches_tags(fw_tags):
                            continue

                        firewalls.append(
                            {
                                "Region": self.region,
                                "FirewallName": firewall.get("FirewallName"),
                                "FirewallArn": fw_arn,
                                "FirewallPolicyArn": firewall.get("FirewallPolicyArn"),
                                "VpcId": firewall.get("VpcId"),
                                "SubnetMappings": firewall.get("SubnetMappings", []),
                                "FirewallPolicyChangeProtection": firewall.get("FirewallPolicyChangeProtection"),
                                "DeleteProtection": firewall.get("DeleteProtection"),
                                "Tags": fw_tags,
                            }
                        )
                    except Exception as fw_error:
                        self._handle_error(fw_error, f"Network Firewall details for {fw_arn}")
                        continue

        except Exception as e:
            self._handle_error(e, "Network Firewalls")
        return firewalls

    def get_route53_resolver_endpoints(self) -> List[Dict[str, Any]]:
        """
        Get information about Route53 Resolver endpoints.

        :return: List of Route53 Resolver endpoint information
        :rtype: List[Dict[str, Any]]
        """
        endpoints = []
        try:
            r53_resolver = self._get_client("route53resolver")
            paginator = r53_resolver.get_paginator("list_resolver_endpoints")

            for page in paginator.paginate():
                for endpoint in page.get("ResolverEndpoints", []):
                    endpoint_arn = endpoint.get("Arn", "")

                    if not self._matches_account(endpoint_arn):
                        continue

                    try:
                        tags_response = r53_resolver.list_tags_for_resource(ResourceArn=endpoint_arn)
                        endpoint_tags = tags_response.get("Tags", [])

                        if not self._matches_tags(endpoint_tags):
                            continue

                        endpoints.append(
                            {
                                "Region": self.region,
                                "Id": endpoint.get("Id"),
                                "Arn": endpoint_arn,
                                "Name": endpoint.get("Name"),
                                "Direction": endpoint.get("Direction"),
                                "Status": endpoint.get("Status"),
                                "IpAddressCount": endpoint.get("IpAddressCount"),
                                "HostVPCId": endpoint.get("HostVPCId"),
                                "CreationTime": endpoint.get("CreationTime"),
                                "Tags": endpoint_tags,
                            }
                        )
                    except Exception as tag_error:
                        self._handle_error(tag_error, f"Route53 Resolver endpoint tags for {endpoint_arn}")
                        continue

        except Exception as e:
            self._handle_error(e, "Route53 Resolver endpoints")
        return endpoints

    def collect(self) -> Dict[str, Any]:
        """
        Collect networking resources based on enabled_services configuration.

        :return: Dictionary containing enabled networking resource information
        :rtype: Dict[str, Any]
        """
        result = {}

        # VPC Resources
        if self.enabled_services.get("vpc", True):
            vpc_info = self.get_vpcs()
            result.update(vpc_info)

        # Elastic IPs
        if self.enabled_services.get("elastic_ips", True):
            result["ElasticIPs"] = self.get_elastic_ips()

        # Load Balancers
        if self.enabled_services.get("load_balancers", True):
            result["LoadBalancers"] = self.get_load_balancers()

        # CloudFront Distributions
        if self.enabled_services.get("cloudfront", True):
            result["CloudFrontDistributions"] = self.get_cloudfront_distributions()

        # Route53
        if self.enabled_services.get("route53", True):
            result["Route53"] = self.get_route53_info()

        # Direct Connect
        if self.enabled_services.get("direct_connect", True):
            result["DirectConnectConnections"] = self.get_direct_connect_connections()

        # Transit Gateways
        if self.enabled_services.get("transit_gateway", True):
            result["TransitGateways"] = self.get_transit_gateways()

        # VPN Connections
        if self.enabled_services.get("vpn", True):
            result["VPNConnections"] = self.get_vpn_connections()

        # Global Accelerators
        if self.enabled_services.get("global_accelerator", True):
            result["GlobalAccelerators"] = self.get_global_accelerators()

        # Network Firewalls
        if self.enabled_services.get("network_firewall", True):
            result["NetworkFirewalls"] = self.get_network_firewalls()

        # Route53 Resolver
        if self.enabled_services.get("route53_resolver", True):
            result["Route53ResolverEndpoints"] = self.get_route53_resolver_endpoints()

        return result

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
