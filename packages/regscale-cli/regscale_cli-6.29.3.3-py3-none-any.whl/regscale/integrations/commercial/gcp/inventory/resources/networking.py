#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GCP Networking resource collectors.

This module provides collectors for GCP networking resources including:
- VPC Networks
- Subnetworks
- Firewall Rules
- Cloud Routers
- IP Addresses
- Forwarding Rules (Load Balancers)
- Cloud DNS Managed Zones
"""

import logging
from typing import Any, Dict, List, Optional

from regscale.integrations.commercial.gcp.inventory.base import BaseCollector

logger = logging.getLogger("regscale")


class NetworkingCollector(BaseCollector):
    """Collector for GCP networking resources."""

    # GCP asset types for networking resources
    supported_asset_types: List[str] = [
        "compute.googleapis.com/Network",
        "compute.googleapis.com/Subnetwork",
        "compute.googleapis.com/Firewall",
        "compute.googleapis.com/Router",
        "compute.googleapis.com/Address",
        "compute.googleapis.com/ForwardingRule",
        "dns.googleapis.com/ManagedZone",
    ]

    def __init__(
        self,
        parent: str,
        credentials_path: Optional[str] = None,
        project_id: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
        enabled_services: Optional[Dict[str, bool]] = None,
    ) -> None:
        """Initialize the networking collector.

        :param str parent: GCP parent resource path
        :param Optional[str] credentials_path: Path to service account JSON key file
        :param Optional[str] project_id: GCP project ID for filtering
        :param Optional[Dict[str, str]] labels: Labels to filter resources
        :param Optional[Dict[str, bool]] enabled_services: Service enablement flags
        """
        super().__init__(parent, credentials_path, project_id, labels)
        self.enabled_services = enabled_services or {}

    def get_vpc_networks(self) -> List[Dict[str, Any]]:
        """Get information about VPC networks.

        :return: List of VPC network information
        :rtype: List[Dict[str, Any]]
        """
        networks = []
        try:
            from google.cloud import compute_v1

            client = compute_v1.NetworksClient()
            project = self._get_scope_id() if self._get_scope_type() == "project" else self.project_id

            if not project:
                logger.warning("No project ID available for VPC networks collection")
                return networks

            # List all networks in the project
            request = compute_v1.ListNetworksRequest(project=project)

            for network in client.list(request=request):
                networks.append(self._parse_vpc_network(network))

        except Exception as e:
            self._handle_error(e, "VPC networks")

        return networks

    def _parse_vpc_network(self, network: Any) -> Dict[str, Any]:
        """Parse a VPC network to a dictionary.

        :param network: VPC network object
        :return: Parsed network data
        :rtype: Dict[str, Any]
        """
        return {
            "name": network.name,
            "id": str(network.id) if network.id else None,
            "description": network.description,
            "self_link": network.self_link,
            "creation_timestamp": network.creation_timestamp,
            "auto_create_subnetworks": network.auto_create_subnetworks,
            "routing_mode": network.routing_config.routing_mode if network.routing_config else None,
            "mtu": network.mtu,
            "subnetworks": list(network.subnetworks) if network.subnetworks else [],
            "peerings": [
                {
                    "name": peering.name,
                    "network": peering.network,
                    "state": peering.state,
                    "state_details": peering.state_details,
                    "auto_create_routes": peering.auto_create_routes,
                    "export_custom_routes": peering.export_custom_routes,
                    "import_custom_routes": peering.import_custom_routes,
                }
                for peering in (network.peerings or [])
            ],
        }

    def get_subnets(self) -> List[Dict[str, Any]]:
        """Get information about subnetworks.

        :return: List of subnetwork information
        :rtype: List[Dict[str, Any]]
        """
        subnets = []
        try:
            from google.cloud import compute_v1

            client = compute_v1.SubnetworksClient()
            project = self._get_scope_id() if self._get_scope_type() == "project" else self.project_id

            if not project:
                logger.warning("No project ID available for subnetworks collection")
                return subnets

            # List subnetworks for all regions using aggregated list
            aggregated_list = client.aggregated_list(project=project)

            for _region, response in aggregated_list:
                if response.subnetworks:
                    for subnet in response.subnetworks:
                        subnets.append(self._parse_subnet(subnet))

        except Exception as e:
            self._handle_error(e, "Subnetworks")

        return subnets

    def _parse_subnet(self, subnet: Any) -> Dict[str, Any]:
        """Parse a subnetwork to a dictionary.

        :param subnet: Subnetwork object
        :return: Parsed subnet data
        :rtype: Dict[str, Any]
        """
        return {
            "name": subnet.name,
            "id": str(subnet.id) if subnet.id else None,
            "description": subnet.description,
            "self_link": subnet.self_link,
            "region": subnet.region,
            "network": subnet.network,
            "ip_cidr_range": subnet.ip_cidr_range,
            "gateway_address": subnet.gateway_address,
            "creation_timestamp": subnet.creation_timestamp,
            "private_ip_google_access": subnet.private_ip_google_access,
            "private_ipv6_google_access": subnet.private_ipv6_google_access,
            "purpose": subnet.purpose,
            "role": subnet.role,
            "stack_type": subnet.stack_type,
            "secondary_ip_ranges": [
                {
                    "range_name": sir.range_name,
                    "ip_cidr_range": sir.ip_cidr_range,
                }
                for sir in (subnet.secondary_ip_ranges or [])
            ],
            "log_config": self._parse_subnet_log_config(subnet.log_config),
        }

    def _parse_subnet_log_config(self, log_config: Any) -> Dict[str, Any]:
        """Parse subnet log configuration.

        :param log_config: Log config object from subnet
        :return: Parsed log config dictionary
        :rtype: Dict[str, Any]
        """
        if not log_config:
            return {}
        return {
            "enable": log_config.enable,
            "aggregation_interval": log_config.aggregation_interval,
            "flow_sampling": log_config.flow_sampling,
            "metadata": log_config.metadata,
        }

    def get_firewall_rules(self) -> List[Dict[str, Any]]:
        """Get information about firewall rules.

        :return: List of firewall rule information
        :rtype: List[Dict[str, Any]]
        """
        firewall_rules = []
        try:
            from google.cloud import compute_v1

            client = compute_v1.FirewallsClient()
            project = self._get_scope_id() if self._get_scope_type() == "project" else self.project_id

            if not project:
                logger.warning("No project ID available for firewall rules collection")
                return firewall_rules

            # List all firewall rules in the project
            request = compute_v1.ListFirewallsRequest(project=project)

            for firewall in client.list(request=request):
                firewall_rules.append(self._parse_firewall_rule(firewall))

        except Exception as e:
            self._handle_error(e, "Firewall rules")

        return firewall_rules

    def _parse_firewall_rule(self, firewall: Any) -> Dict[str, Any]:
        """Parse a firewall rule to a dictionary.

        :param firewall: Firewall rule object
        :return: Parsed firewall data
        :rtype: Dict[str, Any]
        """
        return {
            "name": firewall.name,
            "id": str(firewall.id) if firewall.id else None,
            "description": firewall.description,
            "self_link": firewall.self_link,
            "network": firewall.network,
            "direction": firewall.direction,
            "priority": firewall.priority,
            "creation_timestamp": firewall.creation_timestamp,
            "disabled": firewall.disabled,
            "source_ranges": list(firewall.source_ranges or []),
            "destination_ranges": list(firewall.destination_ranges or []),
            "source_tags": list(firewall.source_tags or []),
            "target_tags": list(firewall.target_tags or []),
            "source_service_accounts": list(firewall.source_service_accounts or []),
            "target_service_accounts": list(firewall.target_service_accounts or []),
            "allowed": self._parse_firewall_rules_list(firewall.allowed),
            "denied": self._parse_firewall_rules_list(firewall.denied),
            "log_config": self._parse_firewall_log_config(firewall.log_config),
        }

    def _parse_firewall_rules_list(self, rules: Any) -> List[Dict[str, Any]]:
        """Parse allowed or denied firewall rules list.

        :param rules: List of allowed/denied rule objects
        :return: List of parsed rule dictionaries
        :rtype: List[Dict[str, Any]]
        """
        return [
            {
                "ip_protocol": rule.I_p_protocol,
                "ports": list(rule.ports or []),
            }
            for rule in (rules or [])
        ]

    def _parse_firewall_log_config(self, log_config: Any) -> Dict[str, Any]:
        """Parse firewall log configuration.

        :param log_config: Log config object from firewall
        :return: Parsed log config dictionary
        :rtype: Dict[str, Any]
        """
        if not log_config:
            return {}
        return {
            "enable": log_config.enable,
            "metadata": log_config.metadata,
        }

    def get_cloud_routers(self) -> List[Dict[str, Any]]:
        """Get information about Cloud Routers.

        :return: List of Cloud Router information
        :rtype: List[Dict[str, Any]]
        """
        routers = []
        try:
            from google.cloud import compute_v1

            client = compute_v1.RoutersClient()
            project = self._get_scope_id() if self._get_scope_type() == "project" else self.project_id

            if not project:
                logger.warning("No project ID available for Cloud Routers collection")
                return routers

            # List routers for all regions using aggregated list
            aggregated_list = client.aggregated_list(project=project)

            for _region, response in aggregated_list:
                if response.routers:
                    for router in response.routers:
                        routers.append(self._parse_cloud_router(router))

        except Exception as e:
            self._handle_error(e, "Cloud Routers")

        return routers

    def _parse_cloud_router(self, router: Any) -> Dict[str, Any]:
        """Parse a Cloud Router to a dictionary.

        :param router: Cloud Router object
        :return: Parsed router data
        :rtype: Dict[str, Any]
        """
        return {
            "name": router.name,
            "id": str(router.id) if router.id else None,
            "description": router.description,
            "self_link": router.self_link,
            "region": router.region,
            "network": router.network,
            "creation_timestamp": router.creation_timestamp,
            "bgp": self._parse_router_bgp(router.bgp),
            "nats": [
                {
                    "name": nat.name,
                    "source_subnetwork_ip_ranges_to_nat": nat.source_subnetwork_ip_ranges_to_nat,
                    "nat_ip_allocate_option": nat.nat_ip_allocate_option,
                    "min_ports_per_vm": nat.min_ports_per_vm,
                    "enable_endpoint_independent_mapping": nat.enable_endpoint_independent_mapping,
                }
                for nat in (router.nats or [])
            ],
            "interfaces": [
                {
                    "name": interface.name,
                    "linked_vpn_tunnel": interface.linked_vpn_tunnel,
                    "ip_range": interface.ip_range,
                }
                for interface in (router.interfaces or [])
            ],
        }

    def _parse_router_bgp(self, bgp: Any) -> Dict[str, Any]:
        """Parse router BGP configuration.

        :param bgp: BGP config object from router
        :return: Parsed BGP config dictionary
        :rtype: Dict[str, Any]
        """
        if not bgp:
            return {}
        return {
            "asn": bgp.asn,
            "advertise_mode": bgp.advertise_mode,
            "advertised_groups": list(bgp.advertised_groups or []),
        }

    def get_ip_addresses(self) -> List[Dict[str, Any]]:
        """Get information about reserved IP addresses.

        :return: List of IP address information
        :rtype: List[Dict[str, Any]]
        """
        addresses = []
        try:
            from google.cloud import compute_v1

            client = compute_v1.AddressesClient()
            project = self._get_scope_id() if self._get_scope_type() == "project" else self.project_id

            if not project:
                logger.warning("No project ID available for IP addresses collection")
                return addresses

            # List addresses for all regions using aggregated list
            aggregated_list = client.aggregated_list(project=project)

            for _region, response in aggregated_list:
                if response.addresses:
                    for address in response.addresses:
                        addresses.append(self._parse_ip_address(address))

        except Exception as e:
            self._handle_error(e, "IP addresses")

        return addresses

    def _parse_ip_address(self, address: Any) -> Dict[str, Any]:
        """Parse an IP address to a dictionary.

        :param address: Address object
        :return: Parsed address data
        :rtype: Dict[str, Any]
        """
        return {
            "name": address.name,
            "id": str(address.id) if address.id else None,
            "description": address.description,
            "self_link": address.self_link,
            "region": address.region,
            "address": address.address,
            "address_type": address.address_type,
            "ip_version": address.ip_version,
            "status": address.status,
            "creation_timestamp": address.creation_timestamp,
            "network_tier": address.network_tier,
            "purpose": address.purpose,
            "subnetwork": address.subnetwork,
            "network": address.network,
            "users": list(address.users) if address.users else [],
        }

    def get_load_balancers(self) -> List[Dict[str, Any]]:
        """Get information about load balancers (forwarding rules).

        :return: List of forwarding rule information
        :rtype: List[Dict[str, Any]]
        """
        forwarding_rules = []
        try:
            from google.cloud import compute_v1

            client = compute_v1.ForwardingRulesClient()
            project = self._get_scope_id() if self._get_scope_type() == "project" else self.project_id

            if not project:
                logger.warning("No project ID available for load balancers collection")
                return forwarding_rules

            # List forwarding rules for all regions using aggregated list
            aggregated_list = client.aggregated_list(project=project)

            for _region, response in aggregated_list:
                if response.forwarding_rules:
                    for rule in response.forwarding_rules:
                        forwarding_rules.append(self._parse_forwarding_rule(rule))

        except Exception as e:
            self._handle_error(e, "Load balancers (forwarding rules)")

        return forwarding_rules

    def _parse_forwarding_rule(self, rule: Any) -> Dict[str, Any]:
        """Parse a forwarding rule to a dictionary.

        :param rule: Forwarding rule object
        :return: Parsed forwarding rule data
        :rtype: Dict[str, Any]
        """
        return {
            "name": rule.name,
            "id": str(rule.id) if rule.id else None,
            "description": rule.description,
            "self_link": rule.self_link,
            "region": rule.region,
            "creation_timestamp": rule.creation_timestamp,
            "ip_address": rule.I_p_address,
            "ip_protocol": rule.I_p_protocol,
            "port_range": rule.port_range,
            "ports": list(rule.ports) if rule.ports else [],
            "target": rule.target,
            "load_balancing_scheme": rule.load_balancing_scheme,
            "network": rule.network,
            "subnetwork": rule.subnetwork,
            "backend_service": rule.backend_service,
            "network_tier": rule.network_tier,
            "labels": dict(rule.labels) if rule.labels else {},
            "all_ports": rule.all_ports,
            "allow_global_access": rule.allow_global_access,
        }

    def get_dns_zones(self) -> List[Dict[str, Any]]:
        """Get information about Cloud DNS managed zones.

        :return: List of DNS managed zone information
        :rtype: List[Dict[str, Any]]
        """
        dns_zones = []
        try:
            from google.cloud import dns_v1

            client = dns_v1.ManagedZonesClient()
            project = self._get_scope_id() if self._get_scope_type() == "project" else self.project_id

            if not project:
                logger.warning("No project ID available for DNS zones collection")
                return dns_zones

            # List all managed zones in the project
            request = dns_v1.ListManagedZonesRequest(project=project)

            for zone in client.list(request=request):
                dns_zones.append(self._parse_dns_zone(zone))

        except Exception as e:
            self._handle_error(e, "DNS managed zones")

        return dns_zones

    def _parse_dns_zone(self, zone: Any) -> Dict[str, Any]:
        """Parse a DNS managed zone to a dictionary.

        :param zone: Managed zone object
        :return: Parsed DNS zone data
        :rtype: Dict[str, Any]
        """
        return {
            "name": zone.name,
            "id": str(zone.id) if zone.id else None,
            "dns_name": zone.dns_name,
            "description": zone.description,
            "name_servers": list(zone.name_servers or []),
            "visibility": zone.visibility,
            "creation_time": zone.creation_time,
            "labels": dict(zone.labels) if zone.labels else {},
            "dnssec_config": self._parse_dnssec_config(zone.dnssec_config),
            "private_visibility_config": self._parse_private_visibility_config(zone.private_visibility_config),
        }

    def _parse_dnssec_config(self, dnssec_config: Any) -> Dict[str, Any]:
        """Parse DNSSEC configuration.

        :param dnssec_config: DNSSEC config object from zone
        :return: Parsed DNSSEC config dictionary
        :rtype: Dict[str, Any]
        """
        if not dnssec_config:
            return {}
        return {
            "state": dnssec_config.state,
            "non_existence": dnssec_config.non_existence,
        }

    def _parse_private_visibility_config(self, config: Any) -> Dict[str, Any]:
        """Parse private visibility configuration.

        :param config: Private visibility config object from zone
        :return: Parsed private visibility config dictionary
        :rtype: Dict[str, Any]
        """
        if not config:
            return {}
        return {
            "networks": [{"network_url": net.network_url} for net in (config.networks or [])],
        }

    def collect(self) -> Dict[str, Any]:
        """Collect networking resources based on enabled_services configuration.

        :return: Dictionary containing enabled networking resource information
        :rtype: Dict[str, Any]
        """
        result = {}

        # VPC Networks
        if self.enabled_services.get("vpc_networks", True):
            result["VPCNetworks"] = self.get_vpc_networks()

        # Subnetworks
        if self.enabled_services.get("subnets", True):
            result["Subnets"] = self.get_subnets()

        # Firewall Rules
        if self.enabled_services.get("firewall_rules", True):
            result["FirewallRules"] = self.get_firewall_rules()

        # Cloud Routers
        if self.enabled_services.get("cloud_routers", True):
            result["CloudRouters"] = self.get_cloud_routers()

        # IP Addresses
        if self.enabled_services.get("ip_addresses", True):
            result["IPAddresses"] = self.get_ip_addresses()

        # Load Balancers (Forwarding Rules)
        if self.enabled_services.get("load_balancers", True):
            result["LoadBalancers"] = self.get_load_balancers()

        # DNS Zones
        if self.enabled_services.get("dns_zones", True):
            result["DNSZones"] = self.get_dns_zones()

        return result
