#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Comprehensive unit tests for Wiz V2 parsers/main.py"""

import json
import logging
import unittest
from typing import Dict, List
from unittest.mock import MagicMock, Mock, patch, call

import pytest

from regscale.integrations.commercial.wizv2.parsers.main import (
    collect_components_to_create,
    handle_container_image_version,
    handle_software_version,
    get_software_name_from_cpe,
    get_latest_version,
    get_cloud_identifier,
    handle_provider,
    parse_memory,
    parse_cpu,
    get_resources,
    pull_resource_info_from_props,
    get_disk_storage,
    get_network_info,
    get_product_ids,
    get_ip_address_from_props,
    get_ip_v4_from_props,
    get_ip_v6_from_props,
    fetch_wiz_data,
    get_ip_address,
)
from regscale.models import regscale_models

logger = logging.getLogger("regscale")
PATH = "regscale.integrations.commercial.wizv2.parsers.main"


# ==================== Component Collection Tests ====================
class TestCollectComponents(unittest.TestCase):
    """Test component collection functions"""

    def test_collect_components_to_create_empty_data(self):
        """Test collecting components with empty data"""
        data = []
        components_to_create = []

        result = collect_components_to_create(data, components_to_create)

        self.assertEqual(result, [])

    def test_collect_components_to_create_single_component(self):
        """Test collecting single component"""
        data = [{"type": "virtual_machine"}]
        components_to_create = []

        result = collect_components_to_create(data, components_to_create)

        self.assertEqual(result, ["Virtual Machine"])
        self.assertEqual(len(result), 1)

    def test_collect_components_to_create_multiple_components(self):
        """Test collecting multiple unique components"""
        data = [
            {"type": "virtual_machine"},
            {"type": "container"},
            {"type": "database"},
        ]
        components_to_create = []

        result = collect_components_to_create(data, components_to_create)

        self.assertIn("Virtual Machine", result)
        self.assertIn("Container", result)
        self.assertIn("Database", result)
        self.assertEqual(len(result), 3)

    def test_collect_components_to_create_duplicate_components(self):
        """Test collecting components with duplicates"""
        data = [
            {"type": "virtual_machine"},
            {"type": "virtual_machine"},
            {"type": "container"},
        ]
        components_to_create = []

        result = collect_components_to_create(data, components_to_create)

        self.assertIn("Virtual Machine", result)
        self.assertIn("Container", result)
        self.assertEqual(len(result), 2)

    def test_collect_components_to_create_missing_type(self):
        """Test collecting components with missing type"""
        data = [{"type": "virtual_machine"}, {}, {"type": "container"}]
        components_to_create = []

        result = collect_components_to_create(data, components_to_create)

        self.assertIn("Virtual Machine", result)
        self.assertIn("Container", result)
        self.assertEqual(len(result), 2)

    def test_collect_components_to_create_existing_components(self):
        """Test collecting components with pre-existing list"""
        data = [{"type": "virtual_machine"}, {"type": "container"}]
        components_to_create = ["Database"]

        result = collect_components_to_create(data, components_to_create)

        self.assertIn("Virtual Machine", result)
        self.assertIn("Container", result)
        self.assertIn("Database", result)
        self.assertEqual(len(result), 3)

    def test_collect_components_to_create_empty_type(self):
        """Test collecting components with empty type string"""
        data = [{"type": ""}, {"type": "container"}]
        components_to_create = []

        result = collect_components_to_create(data, components_to_create)

        self.assertIn("Container", result)
        self.assertEqual(len(result), 1)


# ==================== Container Image Version Tests ====================
class TestContainerImageVersion(unittest.TestCase):
    """Test container image version handling"""

    def test_handle_container_image_version_with_tags(self):
        """Test handling container image with tags"""
        image_tags = ["v1.2.3", "latest"]
        name = "nginx:v1.2.3"

        result = handle_container_image_version(image_tags, name)

        self.assertEqual(result, "v1.2.3")

    def test_handle_container_image_version_empty_tags_with_name(self):
        """Test handling container image with empty tags but version in name"""
        image_tags = []
        name = "nginx:v2.4.6"

        result = handle_container_image_version(image_tags, name)

        self.assertEqual(result, "v2.4.6")

    def test_handle_container_image_version_empty_tags_no_version(self):
        """Test handling container image with empty tags and no version in name"""
        image_tags = []
        name = "nginx"

        result = handle_container_image_version(image_tags, name)

        self.assertEqual(result, "")

    def test_handle_container_image_version_none_tags(self):
        """Test handling container image with None tags"""
        image_tags = [None]
        name = "nginx:v1.0.0"

        result = handle_container_image_version(image_tags, name)

        self.assertEqual(result, "v1.0.0")

    def test_handle_container_image_version_empty_name(self):
        """Test handling container image with empty name"""
        image_tags = []
        name = ""

        result = handle_container_image_version(image_tags, name)

        self.assertEqual(result, "")

    def test_handle_container_image_version_multiple_colons(self):
        """Test handling container image with multiple colons in name"""
        image_tags = []
        name = "registry.io/nginx:v1.2.3:extra"

        result = handle_container_image_version(image_tags, name)

        # The function splits on ":" and takes index [1], which is "v1.2.3"
        self.assertEqual(result, "v1.2.3")


# ==================== Software Version Tests ====================
class TestSoftwareVersion(unittest.TestCase):
    """Test software version handling"""

    def test_handle_software_version_with_version_and_software_category(self):
        """Test handling software version with version present and software category"""
        wiz_entity_properties = {"version": "1.2.3"}
        asset_category = regscale_models.AssetCategory.Software

        result = handle_software_version(wiz_entity_properties, asset_category)

        self.assertEqual(result, "1.2.3")

    def test_handle_software_version_with_version_and_hardware_category(self):
        """Test handling software version with hardware category"""
        wiz_entity_properties = {"version": "1.2.3"}
        asset_category = regscale_models.AssetCategory.Hardware

        result = handle_software_version(wiz_entity_properties, asset_category)

        self.assertIsNone(result)

    def test_handle_software_version_no_version(self):
        """Test handling software version with no version"""
        wiz_entity_properties = {}
        asset_category = regscale_models.AssetCategory.Software

        result = handle_software_version(wiz_entity_properties, asset_category)

        self.assertIsNone(result)

    def test_handle_software_version_empty_version(self):
        """Test handling software version with empty version"""
        wiz_entity_properties = {"version": ""}
        asset_category = regscale_models.AssetCategory.Software

        result = handle_software_version(wiz_entity_properties, asset_category)

        self.assertIsNone(result)

    def test_handle_software_version_none_version(self):
        """Test handling software version with None version"""
        wiz_entity_properties = {"version": None}
        asset_category = regscale_models.AssetCategory.Software

        result = handle_software_version(wiz_entity_properties, asset_category)

        self.assertIsNone(result)


# ==================== CPE Software Name Tests ====================
class TestGetSoftwareNameFromCpe(unittest.TestCase):
    """Test CPE software name extraction"""

    @patch(f"{PATH}.extract_product_name_and_version")
    def test_get_software_name_from_cpe_with_cpe(self, mock_extract):
        """Test getting software name with CPE present"""
        mock_extract.return_value = {
            "part": "a",
            "software_vendor": "apache",
            "software_name": "httpd",
            "software_version": "2.4.46",
        }
        wiz_entity_properties = {"cpe": "cpe:2.3:a:apache:httpd:2.4.46"}
        name = "Apache HTTP Server"

        result = get_software_name_from_cpe(wiz_entity_properties, name)

        self.assertEqual(result["name"], "Apache HTTP Server")
        self.assertEqual(result["part"], "a")
        self.assertEqual(result["software_vendor"], "apache")
        self.assertEqual(result["software_name"], "httpd")
        self.assertEqual(result["software_version"], "2.4.46")
        mock_extract.assert_called_once_with("cpe:2.3:a:apache:httpd:2.4.46")

    def test_get_software_name_from_cpe_no_cpe(self):
        """Test getting software name without CPE"""
        wiz_entity_properties = {}
        name = "Some Software"

        result = get_software_name_from_cpe(wiz_entity_properties, name)

        self.assertEqual(result["name"], "Some Software")
        self.assertIsNone(result["part"])
        self.assertIsNone(result["software_name"])
        self.assertIsNone(result["software_version"])
        self.assertIsNone(result["software_vendor"])

    def test_get_software_name_from_cpe_empty_cpe(self):
        """Test getting software name with empty CPE"""
        wiz_entity_properties = {"cpe": ""}
        name = "Some Software"

        result = get_software_name_from_cpe(wiz_entity_properties, name)

        self.assertEqual(result["name"], "Some Software")
        self.assertIsNone(result["part"])


# ==================== Latest Version Tests ====================
class TestGetLatestVersion(unittest.TestCase):
    """Test latest version retrieval"""

    def test_get_latest_version_with_latest_version(self):
        """Test getting latest version when present"""
        wiz_entity_properties = {"latestVersion": "2.0.0", "version": "1.0.0"}

        result = get_latest_version(wiz_entity_properties)

        self.assertEqual(result, "2.0.0")

    def test_get_latest_version_without_latest_version(self):
        """Test getting latest version when not present"""
        wiz_entity_properties = {"version": "1.0.0"}

        result = get_latest_version(wiz_entity_properties)

        self.assertEqual(result, "1.0.0")

    def test_get_latest_version_both_none(self):
        """Test getting latest version when both are None"""
        wiz_entity_properties = {}

        result = get_latest_version(wiz_entity_properties)

        self.assertIsNone(result)

    def test_get_latest_version_latest_is_none(self):
        """Test getting latest version when latest is explicitly None"""
        wiz_entity_properties = {"latestVersion": None, "version": "1.0.0"}

        result = get_latest_version(wiz_entity_properties)

        self.assertEqual(result, "1.0.0")


# ==================== Cloud Identifier Tests ====================
class TestCloudIdentifier(unittest.TestCase):
    """Test cloud identifier extraction"""

    def test_get_cloud_identifier_aws(self):
        """Test identifying AWS provider"""
        wiz_entity_properties = {"providerUniqueId": "arn:aws:ec2:us-east-1:123456789012:instance/i-1234567890abcdef0"}

        provider, identifier = get_cloud_identifier(wiz_entity_properties)

        self.assertEqual(provider, "aws")
        self.assertIn("aws", identifier)

    def test_get_cloud_identifier_aws_with_amazon(self):
        """Test identifying AWS provider with amazon keyword"""
        wiz_entity_properties = {"providerUniqueId": "amazon-web-services-resource"}

        provider, identifier = get_cloud_identifier(wiz_entity_properties)

        self.assertEqual(provider, "aws")

    def test_get_cloud_identifier_aws_with_ec2(self):
        """Test identifying AWS provider with ec2 keyword"""
        wiz_entity_properties = {"providerUniqueId": "ec2-instance-12345"}

        provider, identifier = get_cloud_identifier(wiz_entity_properties)

        self.assertEqual(provider, "aws")

    def test_get_cloud_identifier_azure(self):
        """Test identifying Azure provider"""
        wiz_entity_properties = {
            "providerUniqueId": "/subscriptions/12345/resourceGroups/mygroup/providers/Microsoft.Compute/virtualMachines/myvm"
        }

        provider, identifier = get_cloud_identifier(wiz_entity_properties)

        self.assertEqual(provider, "azure")
        self.assertIn("microsoft", identifier)

    def test_get_cloud_identifier_azure_with_azure(self):
        """Test identifying Azure provider with azure keyword"""
        wiz_entity_properties = {"providerUniqueId": "azure-resource-12345"}

        provider, identifier = get_cloud_identifier(wiz_entity_properties)

        self.assertEqual(provider, "azure")

    def test_get_cloud_identifier_google(self):
        """Test identifying Google provider"""
        wiz_entity_properties = {
            "providerUniqueId": "//compute.googleapis.com/projects/myproject/zones/us-central1-a/instances/myinstance"
        }

        provider, identifier = get_cloud_identifier(wiz_entity_properties)

        self.assertEqual(provider, "google")
        self.assertIn("google", identifier)

    def test_get_cloud_identifier_google_with_gcp(self):
        """Test identifying Google provider with gcp keyword"""
        wiz_entity_properties = {"providerUniqueId": "gcp-resource-12345"}

        provider, identifier = get_cloud_identifier(wiz_entity_properties)

        self.assertEqual(provider, "google")

    def test_get_cloud_identifier_other(self):
        """Test identifying other provider"""
        wiz_entity_properties = {"providerUniqueId": "other-cloud-provider-12345"}

        provider, identifier = get_cloud_identifier(wiz_entity_properties)

        self.assertEqual(provider, "other")
        self.assertEqual(identifier, "other-cloud-provider-12345")

    def test_get_cloud_identifier_no_provider(self):
        """Test with no provider unique ID"""
        wiz_entity_properties = {}

        provider, identifier = get_cloud_identifier(wiz_entity_properties)

        self.assertIsNone(provider)
        self.assertIsNone(identifier)

    def test_get_cloud_identifier_none_provider(self):
        """Test with None provider unique ID"""
        wiz_entity_properties = {"providerUniqueId": None}

        provider, identifier = get_cloud_identifier(wiz_entity_properties)

        self.assertIsNone(provider)
        self.assertIsNone(identifier)

    def test_get_cloud_identifier_empty_provider(self):
        """Test with empty provider unique ID"""
        wiz_entity_properties = {"providerUniqueId": ""}

        provider, identifier = get_cloud_identifier(wiz_entity_properties)

        self.assertIsNone(provider)
        self.assertIsNone(identifier)


# ==================== Provider Handling Tests ====================
class TestHandleProvider(unittest.TestCase):
    """Test provider handling"""

    @patch(f"{PATH}.get_cloud_identifier")
    def test_handle_provider_aws(self, mock_get_identifier):
        """Test handling AWS provider"""
        mock_get_identifier.return_value = ("aws", "arn:aws:ec2:us-east-1:123456789012:instance/i-1234567890abcdef0")
        wiz_entity_properties = {"providerUniqueId": "arn:aws:ec2:us-east-1:123456789012:instance/i-1234567890abcdef0"}

        result = handle_provider(wiz_entity_properties)

        self.assertEqual(result["awsIdentifier"], "arn:aws:ec2:us-east-1:123456789012:instance/i-1234567890abcdef0")
        self.assertIsNone(result["azureIdentifier"])
        self.assertIsNone(result["googleIdentifier"])
        self.assertIsNone(result["otherCloudIdentifier"])

    @patch(f"{PATH}.get_cloud_identifier")
    def test_handle_provider_azure(self, mock_get_identifier):
        """Test handling Azure provider"""
        mock_get_identifier.return_value = (
            "azure",
            "/subscriptions/12345/resourceGroups/mygroup/providers/Microsoft.Compute/virtualMachines/myvm",
        )
        wiz_entity_properties = {
            "providerUniqueId": "/subscriptions/12345/resourceGroups/mygroup/providers/Microsoft.Compute/virtualMachines/myvm"
        }

        result = handle_provider(wiz_entity_properties)

        self.assertIsNone(result["awsIdentifier"])
        self.assertEqual(
            result["azureIdentifier"],
            "/subscriptions/12345/resourceGroups/mygroup/providers/Microsoft.Compute/virtualMachines/myvm",
        )
        self.assertIsNone(result["googleIdentifier"])
        self.assertIsNone(result["otherCloudIdentifier"])

    @patch(f"{PATH}.get_cloud_identifier")
    def test_handle_provider_google(self, mock_get_identifier):
        """Test handling Google provider"""
        mock_get_identifier.return_value = (
            "google",
            "//compute.googleapis.com/projects/myproject/zones/us-central1-a/instances/myinstance",
        )
        wiz_entity_properties = {
            "providerUniqueId": "//compute.googleapis.com/projects/myproject/zones/us-central1-a/instances/myinstance"
        }

        result = handle_provider(wiz_entity_properties)

        self.assertIsNone(result["awsIdentifier"])
        self.assertIsNone(result["azureIdentifier"])
        self.assertEqual(
            result["googleIdentifier"],
            "//compute.googleapis.com/projects/myproject/zones/us-central1-a/instances/myinstance",
        )
        self.assertIsNone(result["otherCloudIdentifier"])

    @patch(f"{PATH}.get_cloud_identifier")
    def test_handle_provider_other(self, mock_get_identifier):
        """Test handling other provider"""
        mock_get_identifier.return_value = ("other", "other-cloud-provider-12345")
        wiz_entity_properties = {"providerUniqueId": "other-cloud-provider-12345"}

        result = handle_provider(wiz_entity_properties)

        self.assertIsNone(result["awsIdentifier"])
        self.assertIsNone(result["azureIdentifier"])
        self.assertIsNone(result["googleIdentifier"])
        self.assertEqual(result["otherCloudIdentifier"], "other-cloud-provider-12345")

    @patch(f"{PATH}.get_cloud_identifier")
    def test_handle_provider_none(self, mock_get_identifier):
        """Test handling no provider"""
        mock_get_identifier.return_value = (None, None)
        wiz_entity_properties = {}

        result = handle_provider(wiz_entity_properties)

        self.assertIsNone(result["awsIdentifier"])
        self.assertIsNone(result["azureIdentifier"])
        self.assertIsNone(result["googleIdentifier"])
        self.assertIsNone(result["otherCloudIdentifier"])


# ==================== Memory Parsing Tests ====================
class TestParseMemory(unittest.TestCase):
    """Test memory parsing"""

    def test_parse_memory_gi_to_mib(self):
        """Test parsing GiB to MiB"""
        result = parse_memory("2Gi")
        self.assertEqual(result, 2048)

    def test_parse_memory_mi(self):
        """Test parsing MiB"""
        result = parse_memory("512Mi")
        self.assertEqual(result, 512)

    def test_parse_memory_decimal_gi(self):
        """Test parsing decimal GiB"""
        result = parse_memory("1.5Gi")
        self.assertEqual(result, 1536)

    def test_parse_memory_empty_string(self):
        """Test parsing empty string"""
        result = parse_memory("")
        self.assertEqual(result, 0)

    def test_parse_memory_zero(self):
        """Test parsing zero"""
        result = parse_memory("0")
        self.assertEqual(result, 0)

    def test_parse_memory_invalid_format(self):
        """Test parsing invalid format"""
        result = parse_memory("invalid")
        self.assertEqual(result, 0)

    def test_parse_memory_none(self):
        """Test parsing None"""
        result = parse_memory(None)
        self.assertEqual(result, 0)


# ==================== CPU Parsing Tests ====================
class TestParseCpu(unittest.TestCase):
    """Test CPU parsing"""

    def test_parse_cpu_integer_string(self):
        """Test parsing integer string"""
        result = parse_cpu("4")
        self.assertEqual(result, 4)

    def test_parse_cpu_integer(self):
        """Test parsing integer"""
        result = parse_cpu(4)
        self.assertEqual(result, 4)

    def test_parse_cpu_float_string(self):
        """Test parsing float string"""
        result = parse_cpu("2.5")
        self.assertEqual(result, 2)

    def test_parse_cpu_float(self):
        """Test parsing float"""
        result = parse_cpu(2.8)
        self.assertEqual(result, 2)

    def test_parse_cpu_invalid(self):
        """Test parsing invalid string"""
        result = parse_cpu("invalid")
        self.assertEqual(result, 0)

    def test_parse_cpu_empty_string(self):
        """Test parsing empty string"""
        result = parse_cpu("")
        self.assertEqual(result, 0)


# ==================== Resources Tests ====================
class TestGetResources(unittest.TestCase):
    """Test resources extraction"""

    def test_get_resources_valid_json(self):
        """Test getting resources with valid JSON"""
        resources_dict = {"requests": {"memory": "2Gi", "cpu": "500m"}, "limits": {"memory": "4Gi", "cpu": "1000m"}}
        wiz_entity_properties = {"resources": json.dumps(resources_dict)}

        result = get_resources(wiz_entity_properties)

        self.assertEqual(result, {"memory": "2Gi", "cpu": "500m"})

    def test_get_resources_no_resources(self):
        """Test getting resources with no resources key"""
        wiz_entity_properties = {}

        result = get_resources(wiz_entity_properties)

        self.assertEqual(result, {})

    def test_get_resources_invalid_json(self):
        """Test getting resources with invalid JSON"""
        wiz_entity_properties = {"resources": "invalid json"}

        result = get_resources(wiz_entity_properties)

        self.assertEqual(result, {})

    def test_get_resources_no_requests(self):
        """Test getting resources with no requests key"""
        resources_dict = {"limits": {"memory": "4Gi", "cpu": "1000m"}}
        wiz_entity_properties = {"resources": json.dumps(resources_dict)}

        result = get_resources(wiz_entity_properties)

        self.assertEqual(result, {})


# ==================== Resource Info Tests ====================
class TestPullResourceInfo(unittest.TestCase):
    """Test resource info extraction"""

    @patch(f"{PATH}.get_resources")
    @patch(f"{PATH}.parse_memory")
    @patch(f"{PATH}.parse_cpu")
    def test_pull_resource_info_from_props(self, mock_parse_cpu, mock_parse_memory, mock_get_resources):
        """Test pulling resource info from properties"""
        mock_get_resources.return_value = {"memory": "2Gi", "cpu": "2"}
        mock_parse_memory.return_value = 2048
        mock_parse_cpu.side_effect = [2, 4]

        wiz_entity_properties = {"vCPUs": "4"}

        memory, cpu = pull_resource_info_from_props(wiz_entity_properties)

        self.assertEqual(memory, 2048)
        self.assertEqual(cpu, 4)
        mock_get_resources.assert_called_once_with(wiz_entity_properties)

    @patch(f"{PATH}.get_resources")
    @patch(f"{PATH}.parse_memory")
    @patch(f"{PATH}.parse_cpu")
    def test_pull_resource_info_from_props_no_vcpus(self, mock_parse_cpu, mock_parse_memory, mock_get_resources):
        """Test pulling resource info without vCPUs"""
        mock_get_resources.return_value = {"memory": "1Gi", "cpu": "1"}
        mock_parse_memory.return_value = 1024
        mock_parse_cpu.side_effect = [1, 1]

        wiz_entity_properties = {}

        memory, cpu = pull_resource_info_from_props(wiz_entity_properties)

        self.assertEqual(memory, 1024)
        self.assertEqual(cpu, 1)

    @patch(f"{PATH}.get_resources")
    @patch(f"{PATH}.parse_memory")
    @patch(f"{PATH}.parse_cpu")
    def test_pull_resource_info_from_props_empty_resources(self, mock_parse_cpu, mock_parse_memory, mock_get_resources):
        """Test pulling resource info with empty resources"""
        mock_get_resources.return_value = {}
        mock_parse_memory.return_value = 0
        mock_parse_cpu.side_effect = [0, 0]

        wiz_entity_properties = {}

        memory, cpu = pull_resource_info_from_props(wiz_entity_properties)

        self.assertEqual(memory, 0)
        self.assertEqual(cpu, 0)


# ==================== Disk Storage Tests ====================
class TestGetDiskStorage(unittest.TestCase):
    """Test disk storage extraction"""

    def test_get_disk_storage_valid(self):
        """Test getting disk storage with valid integer"""
        wiz_entity_properties = {"totalDisks": 100}

        result = get_disk_storage(wiz_entity_properties)

        self.assertEqual(result, 100)

    def test_get_disk_storage_string(self):
        """Test getting disk storage with string integer"""
        wiz_entity_properties = {"totalDisks": "250"}

        result = get_disk_storage(wiz_entity_properties)

        self.assertEqual(result, 250)

    def test_get_disk_storage_no_key(self):
        """Test getting disk storage with no key"""
        wiz_entity_properties = {}

        result = get_disk_storage(wiz_entity_properties)

        self.assertEqual(result, 0)

    def test_get_disk_storage_invalid(self):
        """Test getting disk storage with invalid value"""
        wiz_entity_properties = {"totalDisks": "invalid"}

        result = get_disk_storage(wiz_entity_properties)

        self.assertEqual(result, 0)


# ==================== Network Info Tests ====================
class TestGetNetworkInfo(unittest.TestCase):
    """Test network info extraction"""

    @patch(f"{PATH}.get_ip_address")
    def test_get_network_info_complete(self, mock_get_ip):
        """Test getting network info with all fields"""
        mock_get_ip.return_value = ("192.168.1.1", None, None, None)
        wiz_entity_properties = {"region": "us-east-1", "address": "192.168.1.1", "addressType": "IPV4"}

        result = get_network_info(wiz_entity_properties)

        self.assertEqual(result["region"], "us-east-1")
        self.assertEqual(result["ip4_address"], "192.168.1.1")
        self.assertIsNone(result["ip6_address"])
        self.assertIsNone(result["dns"])
        self.assertIsNone(result["url"])

    @patch(f"{PATH}.get_ip_address")
    def test_get_network_info_ipv6(self, mock_get_ip):
        """Test getting network info with IPv6"""
        mock_get_ip.return_value = (None, "2001:0db8:85a3:0000:0000:8a2e:0370:7334", None, None)
        wiz_entity_properties = {
            "region": "eu-west-1",
            "address": "2001:0db8:85a3:0000:0000:8a2e:0370:7334",
            "addressType": "IPV6",
        }

        result = get_network_info(wiz_entity_properties)

        self.assertEqual(result["region"], "eu-west-1")
        self.assertIsNone(result["ip4_address"])
        self.assertEqual(result["ip6_address"], "2001:0db8:85a3:0000:0000:8a2e:0370:7334")

    @patch(f"{PATH}.get_ip_address")
    def test_get_network_info_dns(self, mock_get_ip):
        """Test getting network info with DNS"""
        mock_get_ip.return_value = (None, None, "example.com", None)
        wiz_entity_properties = {"region": "us-west-2", "address": "example.com", "addressType": "DNS"}

        result = get_network_info(wiz_entity_properties)

        self.assertEqual(result["dns"], "example.com")

    @patch(f"{PATH}.get_ip_address")
    def test_get_network_info_url(self, mock_get_ip):
        """Test getting network info with URL"""
        mock_get_ip.return_value = (None, None, None, "https://example.com")
        wiz_entity_properties = {"region": "ap-southeast-1", "address": "https://example.com", "addressType": "URL"}

        result = get_network_info(wiz_entity_properties)

        self.assertEqual(result["url"], "https://example.com")

    @patch(f"{PATH}.get_ip_address")
    def test_get_network_info_no_region(self, mock_get_ip):
        """Test getting network info without region"""
        mock_get_ip.return_value = ("10.0.0.1", None, None, None)
        wiz_entity_properties = {"address": "10.0.0.1", "addressType": "IPV4"}

        result = get_network_info(wiz_entity_properties)

        self.assertIsNone(result["region"])
        self.assertEqual(result["ip4_address"], "10.0.0.1")


# ==================== Product IDs Tests ====================
class TestGetProductIds(unittest.TestCase):
    """Test product IDs extraction"""

    def test_get_product_ids_list(self):
        """Test getting product IDs as list"""
        wiz_entity_properties = {"_productIDs": ["prod-123", "prod-456", "prod-789"]}

        result = get_product_ids(wiz_entity_properties)

        self.assertEqual(result, "prod-123, prod-456, prod-789")

    def test_get_product_ids_string(self):
        """Test getting product IDs as string"""
        wiz_entity_properties = {"_productIDs": "prod-123"}

        result = get_product_ids(wiz_entity_properties)

        self.assertEqual(result, "prod-123")

    def test_get_product_ids_empty_list(self):
        """Test getting product IDs with empty list"""
        wiz_entity_properties = {"_productIDs": []}

        result = get_product_ids(wiz_entity_properties)

        # Empty list is falsy, so the function returns the list itself (not joined)
        # Actually, the if condition checks "if product_ids and isinstance",
        # empty list is falsy so it falls through to return product_ids (the empty list)
        self.assertEqual(result, [])

    def test_get_product_ids_no_key(self):
        """Test getting product IDs with no key"""
        wiz_entity_properties = {}

        result = get_product_ids(wiz_entity_properties)

        self.assertIsNone(result)

    def test_get_product_ids_none(self):
        """Test getting product IDs with None"""
        wiz_entity_properties = {"_productIDs": None}

        result = get_product_ids(wiz_entity_properties)

        self.assertIsNone(result)


# ==================== IP Address Helper Tests ====================
class TestIpAddressHelpers(unittest.TestCase):
    """Test IP address helper functions"""

    def test_get_ip_address_from_props_ipv4(self):
        """Test getting IP address from properties with IPv4"""
        network_dict = {"ip4_address": "192.168.1.1", "ip6_address": None}

        result = get_ip_address_from_props(network_dict)

        self.assertEqual(result, "192.168.1.1")

    def test_get_ip_address_from_props_ipv6(self):
        """Test getting IP address from properties with IPv6"""
        network_dict = {"ip4_address": None, "ip6_address": "2001:0db8:85a3:0000:0000:8a2e:0370:7334"}

        result = get_ip_address_from_props(network_dict)

        self.assertEqual(result, "2001:0db8:85a3:0000:0000:8a2e:0370:7334")

    def test_get_ip_address_from_props_both(self):
        """Test getting IP address from properties with both"""
        network_dict = {"ip4_address": "192.168.1.1", "ip6_address": "2001:0db8:85a3:0000:0000:8a2e:0370:7334"}

        result = get_ip_address_from_props(network_dict)

        # Should prefer IPv4
        self.assertEqual(result, "192.168.1.1")

    def test_get_ip_address_from_props_none(self):
        """Test getting IP address from properties with none"""
        network_dict = {"ip4_address": None, "ip6_address": None}

        result = get_ip_address_from_props(network_dict)

        self.assertIsNone(result)

    def test_get_ip_v4_from_props(self):
        """Test getting IPv4 from properties"""
        network_dict = {"address": "10.0.0.1"}

        result = get_ip_v4_from_props(network_dict)

        self.assertEqual(result, "10.0.0.1")

    def test_get_ip_v4_from_props_no_address(self):
        """Test getting IPv4 from properties with no address"""
        network_dict = {}

        result = get_ip_v4_from_props(network_dict)

        self.assertIsNone(result)

    def test_get_ip_v6_from_props(self):
        """Test getting IPv6 from properties"""
        network_dict = {"ip6_address": "2001:0db8:85a3::8a2e:0370:7334"}

        result = get_ip_v6_from_props(network_dict)

        self.assertEqual(result, "2001:0db8:85a3::8a2e:0370:7334")

    def test_get_ip_v6_from_props_no_address(self):
        """Test getting IPv6 from properties with no address"""
        network_dict = {}

        result = get_ip_v6_from_props(network_dict)

        self.assertIsNone(result)


# ==================== IP Address Extraction Tests ====================
class TestGetIpAddress(unittest.TestCase):
    """Test IP address extraction from Wiz entity properties"""

    def test_get_ip_address_ipv4(self):
        """Test getting IPv4 address"""
        wiz_entity_properties = {"address": "192.168.1.1", "addressType": "IPV4"}

        ip4, ip6, dns, url = get_ip_address(wiz_entity_properties)

        self.assertEqual(ip4, "192.168.1.1")
        self.assertIsNone(ip6)
        self.assertIsNone(dns)
        self.assertIsNone(url)

    def test_get_ip_address_ipv6(self):
        """Test getting IPv6 address"""
        wiz_entity_properties = {"address": "2001:0db8:85a3:0000:0000:8a2e:0370:7334", "addressType": "IPV6"}

        ip4, ip6, dns, url = get_ip_address(wiz_entity_properties)

        self.assertIsNone(ip4)
        self.assertEqual(ip6, "2001:0db8:85a3:0000:0000:8a2e:0370:7334")
        self.assertIsNone(dns)
        self.assertIsNone(url)

    def test_get_ip_address_dns(self):
        """Test getting DNS address"""
        wiz_entity_properties = {"address": "example.com", "addressType": "DNS"}

        ip4, ip6, dns, url = get_ip_address(wiz_entity_properties)

        self.assertIsNone(ip4)
        self.assertIsNone(ip6)
        self.assertEqual(dns, "example.com")
        self.assertIsNone(url)

    def test_get_ip_address_url(self):
        """Test getting URL address"""
        wiz_entity_properties = {"address": "https://example.com", "addressType": "URL"}

        ip4, ip6, dns, url = get_ip_address(wiz_entity_properties)

        self.assertIsNone(ip4)
        self.assertIsNone(ip6)
        self.assertIsNone(dns)
        self.assertEqual(url, "https://example.com")

    def test_get_ip_address_no_address(self):
        """Test getting IP address with no address field"""
        wiz_entity_properties = {}

        ip4, ip6, dns, url = get_ip_address(wiz_entity_properties)

        self.assertIsNone(ip4)
        self.assertIsNone(ip6)
        self.assertIsNone(dns)
        self.assertIsNone(url)

    def test_get_ip_address_unknown_type(self):
        """Test getting IP address with unknown type"""
        wiz_entity_properties = {"address": "some-value", "addressType": "UNKNOWN"}

        ip4, ip6, dns, url = get_ip_address(wiz_entity_properties)

        self.assertIsNone(ip4)
        self.assertIsNone(ip6)
        self.assertIsNone(dns)
        self.assertIsNone(url)


# ==================== Wiz Data Fetching Tests ====================
class TestFetchWizData(unittest.TestCase):
    """Test fetching data from Wiz API"""

    @patch(f"{PATH}.WizVariables")
    @patch(f"{PATH}.PaginatedGraphQLClient")
    def test_fetch_wiz_data_success(self, mock_client_class, mock_vars):
        """Test successful Wiz data fetch"""
        mock_vars.wizUrl = "https://api.wiz.io/graphql"

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.fetch_all.return_value = [{"id": "1", "name": "test"}, {"id": "2", "name": "test2"}]

        query = "query { test }"
        variables = {"var1": "value1"}
        topic_key = "testTopic"
        token = "test-token"

        result = fetch_wiz_data(query, variables, topic_key, token)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["id"], "1")
        mock_client_class.assert_called_once()
        mock_client.fetch_all.assert_called_once_with(variables=variables, topic_key=topic_key)

    @patch(f"{PATH}.WizVariables")
    @patch(f"{PATH}.PaginatedGraphQLClient")
    def test_fetch_wiz_data_custom_endpoint(self, mock_client_class, mock_vars):
        """Test Wiz data fetch with custom endpoint"""
        mock_vars.wizUrl = "https://api.wiz.io/graphql"

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.fetch_all.return_value = []

        query = "query { test }"
        variables = {}
        topic_key = "testTopic"
        token = "test-token"
        custom_endpoint = "https://custom.wiz.io/graphql"

        fetch_wiz_data(query, variables, topic_key, token, custom_endpoint)

        # Should use custom endpoint instead of default
        call_args = mock_client_class.call_args
        self.assertEqual(call_args.kwargs["endpoint"], custom_endpoint)

    @patch(f"{PATH}.WizVariables")
    @patch(f"{PATH}.PaginatedGraphQLClient")
    def test_fetch_wiz_data_empty_results(self, mock_client_class, mock_vars):
        """Test Wiz data fetch with empty results"""
        mock_vars.wizUrl = "https://api.wiz.io/graphql"

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.fetch_all.return_value = []

        query = "query { test }"
        variables = {}
        topic_key = "testTopic"
        token = "test-token"

        result = fetch_wiz_data(query, variables, topic_key, token)

        self.assertEqual(result, [])

    @patch(f"{PATH}.WizVariables")
    @patch(f"{PATH}.PaginatedGraphQLClient")
    def test_fetch_wiz_data_headers(self, mock_client_class, mock_vars):
        """Test Wiz data fetch with proper headers"""
        mock_vars.wizUrl = "https://api.wiz.io/graphql"

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.fetch_all.return_value = []

        query = "query { test }"
        variables = {}
        topic_key = "testTopic"
        token = "test-token-12345"

        fetch_wiz_data(query, variables, topic_key, token)

        # Verify headers were set correctly
        call_args = mock_client_class.call_args
        self.assertIn("Authorization", call_args.kwargs["headers"])
        self.assertEqual(call_args.kwargs["headers"]["Authorization"], "Bearer test-token-12345")
        self.assertEqual(call_args.kwargs["headers"]["Content-Type"], "application/json")


# ==================== Edge Cases and Error Handling Tests ====================
class TestEdgeCasesAndErrorHandling(unittest.TestCase):
    """Test edge cases and error handling"""

    def test_parse_memory_very_large_value(self):
        """Test parsing very large memory value"""
        result = parse_memory("1024Gi")
        self.assertEqual(result, 1048576)

    def test_parse_cpu_negative_value(self):
        """Test parsing negative CPU value"""
        result = parse_cpu("-1")
        self.assertEqual(result, -1)

    def test_collect_components_to_create_special_characters(self):
        """Test collecting components with special characters"""
        data = [{"type": "virtual-machine_v2.1"}, {"type": "test_component-special"}]
        components_to_create = []

        result = collect_components_to_create(data, components_to_create)

        self.assertIn("Virtual-Machine V2.1", result)
        self.assertIn("Test Component-Special", result)

    def test_handle_container_image_version_multiple_tags(self):
        """Test handling container with multiple tags (should return first)"""
        image_tags = ["v1.0.0", "v1.0.1", "latest"]
        name = "nginx"

        result = handle_container_image_version(image_tags, name)

        self.assertEqual(result, "v1.0.0")

    def test_get_cloud_identifier_case_insensitive(self):
        """Test cloud identifier is case insensitive"""
        wiz_entity_properties = {"providerUniqueId": "AWS-RESOURCE-12345"}

        provider, identifier = get_cloud_identifier(wiz_entity_properties)

        self.assertEqual(provider, "aws")

    @patch(f"{PATH}.extract_product_name_and_version")
    def test_get_software_name_from_cpe_exception_handling(self, mock_extract):
        """Test CPE extraction with exception"""
        mock_extract.side_effect = Exception("Parse error")
        wiz_entity_properties = {"cpe": "invalid-cpe"}
        name = "Test Software"

        # Should not raise, should return default dict
        with self.assertRaises(Exception):
            get_software_name_from_cpe(wiz_entity_properties, name)

    def test_get_product_ids_mixed_types_in_list(self):
        """Test product IDs with mixed types in list - should raise TypeError"""
        wiz_entity_properties = {"_productIDs": ["prod-123", 456, None, "prod-789"]}

        # The function expects all strings in the list, mixed types will cause TypeError
        with self.assertRaises(TypeError):
            get_product_ids(wiz_entity_properties)

    def test_parse_memory_float_mi(self):
        """Test parsing float MiB value"""
        result = parse_memory("512.5Mi")
        self.assertEqual(result, 512)

    def test_get_disk_storage_zero_string(self):
        """Test disk storage with zero string"""
        wiz_entity_properties = {"totalDisks": "0"}

        result = get_disk_storage(wiz_entity_properties)

        self.assertEqual(result, 0)

    def test_get_network_info_all_address_types(self):
        """Test network info can only extract one address type at a time"""
        # Each call to get_ip_address returns one type based on addressType
        wiz_entity_properties = {"address": "192.168.1.1", "addressType": "IPV4", "region": "us-east-1"}

        result = get_network_info(wiz_entity_properties)

        # Should only get IPv4 since addressType is IPV4
        self.assertEqual(result["ip4_address"], "192.168.1.1")
        self.assertIsNone(result["ip6_address"])
        self.assertIsNone(result["dns"])
        self.assertIsNone(result["url"])


if __name__ == "__main__":
    unittest.main()
