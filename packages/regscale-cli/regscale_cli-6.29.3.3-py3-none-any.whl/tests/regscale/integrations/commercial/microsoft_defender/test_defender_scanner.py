#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for Microsoft Defender Scanner integration"""
from unittest.mock import MagicMock, patch

from regscale.integrations.commercial.microsoft_defender.defender_api import DefenderApi
from regscale.integrations.commercial.microsoft_defender.defender_scanner import DefenderScanner
from regscale.integrations.scanner_integration import IntegrationAsset, IntegrationFinding
from regscale.models import IssueSeverity
from tests import CLITestFixture

PATH = "regscale.integrations.commercial.microsoft_defender.defender_scanner"


class TestDefenderScanner(CLITestFixture):
    def test_init(self):
        """Test init file and config"""
        self.verify_config(
            [
                "azureCloudSubscriptionId",
            ]
        )

    @patch(f"{PATH}.DefenderApi")
    def test_defender_scanner_init_default_system(self, mock_defender_api_class):
        """Test DefenderScanner initialization with default system"""
        mock_api = MagicMock(spec=DefenderApi)
        mock_defender_api_class.return_value = mock_api

        scanner = DefenderScanner(plan_id=1, is_component=False)

        assert scanner.system == "cloud"
        assert scanner.title == "Microsoft Defender for Cloud"
        assert scanner.asset_identifier_field == "otherTrackingNumber"
        assert scanner.api == mock_api
        mock_defender_api_class.assert_called_once_with(system="cloud")

    @patch(f"{PATH}.DefenderApi")
    def test_defender_scanner_init_custom_system(self, mock_defender_api_class):
        """Test DefenderScanner initialization with custom system"""
        mock_api = MagicMock(spec=DefenderApi)
        mock_defender_api_class.return_value = mock_api

        scanner = DefenderScanner(system="365", plan_id=1, is_component=False)

        assert scanner.system == "365"
        assert scanner.api == mock_api
        mock_defender_api_class.assert_called_once_with(system="365")

    def test_finding_severity_map(self):
        """Test that severity mapping is correctly defined"""
        scanner = DefenderScanner(plan_id=1, is_component=False)

        expected_mapping = {
            "Critical": IssueSeverity.Critical,
            "High": IssueSeverity.High,
            "Medium": IssueSeverity.Moderate,
            "Low": IssueSeverity.Low,
        }

        assert scanner.finding_severity_map == expected_mapping

    @patch(f"{PATH}.DefenderApi")
    def test_fetch_assets(self, mock_defender_api_class):
        """Test fetching assets from Defender"""
        mock_api = MagicMock(spec=DefenderApi)
        mock_api.config = {"azureCloudSubscriptionId": "test-subscription"}
        mock_api.execute_resource_graph_query.return_value = [
            {
                "resourceId": "/subscriptions/test/vm1",
                "resourceName": "test-vm",
                "resourceType": "microsoft.compute/virtualmachines",
                "resourceLocation": "eastus",
                "resourceGroup": "test-rg",
                "ipAddress": "10.0.0.1",
                "properties": {"osProfile": {"computerName": "test-vm"}},
            },
            {
                "resourceId": "/subscriptions/test/storage1",
                "resourceName": "test-storage",
                "resourceType": "microsoft.storage/storageaccounts",
                "resourceLocation": "westus",
                "resourceGroup": "test-rg",
                "ipAddress": "",
                "properties": {"primaryEndpoints": {"blob": "https://test.blob.core.windows.net"}},
            },
        ]
        mock_defender_api_class.return_value = mock_api

        scanner = DefenderScanner(plan_id=1, is_component=False)

        assets = list(scanner.fetch_assets())

        assert len(assets) == 2
        assert scanner.num_assets_to_process == 2

        # Check first asset (VM)
        vm_asset = assets[0]
        assert isinstance(vm_asset, IntegrationAsset)
        assert vm_asset.name == "test-vm"
        assert vm_asset.other_tracking_number == "/subscriptions/test/vm1"
        assert vm_asset.ip_address == "10.0.0.1"

        # Check second asset (Storage)
        storage_asset = assets[1]
        assert isinstance(storage_asset, IntegrationAsset)
        assert storage_asset.name == "test-storage"
        assert storage_asset.other_tracking_number == "/subscriptions/test/storage1"
        assert storage_asset.fqdn == "https://test.blob.core.windows.net"

    @patch(f"{PATH}.DefenderApi")
    def test_fetch_findings(self, mock_defender_api_class):
        """Test fetching findings"""
        mock_api = MagicMock(spec=DefenderApi)
        mock_defender_api_class.return_value = mock_api

        scanner = DefenderScanner(plan_id=1, is_component=False)

        mock_findings = [MagicMock(spec=IntegrationFinding), MagicMock(spec=IntegrationFinding)]

        findings = list(scanner.fetch_findings(integration_findings=mock_findings))

        assert len(findings) == 2
        assert all(isinstance(f, IntegrationFinding) for f in findings)

    @patch(f"{PATH}.DefenderApi")
    def test_parse_asset_vm(self, mock_defender_api_class):
        """Test parsing a virtual machine asset"""
        mock_api = MagicMock(spec=DefenderApi)
        mock_defender_api_class.return_value = mock_api

        scanner = DefenderScanner(plan_id=1, is_component=False)

        defender_asset = {
            "resourceId": "/subscriptions/test/resourceGroups/test-rg/providers/Microsoft.Compute/virtualMachines/test-vm",
            "resourceName": "test-vm",
            "resourceType": "microsoft.compute/virtualmachines",
            "resourceLocation": "eastus",
            "resourceGroup": "test-rg",
            "ipAddress": "10.0.0.1",
            "properties": {
                "osProfile": {"computerName": "test-vm"},
                "networkProfile": {"networkInterfaces": [{"id": "/subscriptions/test/nic1"}]},
            },
        }

        asset = scanner.parse_asset(defender_asset)

        assert isinstance(asset, IntegrationAsset)
        assert asset.name == "test-vm"
        assert (
            asset.other_tracking_number
            == "/subscriptions/test/resourceGroups/test-rg/providers/Microsoft.Compute/virtualMachines/test-vm"
        )
        assert (
            asset.azure_identifier
            == "/subscriptions/test/resourceGroups/test-rg/providers/Microsoft.Compute/virtualMachines/test-vm"
        )
        assert asset.ip_address == "10.0.0.1"
        assert asset.is_virtual is True
        assert asset.baseline_configuration == "Azure Hardening Guide"
        assert "microsoft.compute/virtualmachines" in asset.component_names

    @patch(f"{PATH}.DefenderApi")
    def test_parse_asset_storage_account(self, mock_defender_api_class):
        """Test parsing a storage account asset"""
        mock_api = MagicMock(spec=DefenderApi)
        mock_defender_api_class.return_value = mock_api

        scanner = DefenderScanner(plan_id=1, is_component=False)

        defender_asset = {
            "resourceId": "/subscriptions/test/resourceGroups/test-rg/providers/Microsoft.Storage/storageAccounts/teststorage",
            "resourceName": "teststorage",
            "resourceType": "microsoft.storage/storageaccounts",
            "resourceLocation": "westus",
            "resourceGroup": "test-rg",
            "ipAddress": "",
            "properties": {"primaryEndpoints": {"blob": "https://teststorage.blob.core.windows.net"}},
        }

        asset = scanner.parse_asset(defender_asset)

        assert isinstance(asset, IntegrationAsset)
        assert asset.name == "teststorage"
        assert asset.fqdn == "https://teststorage.blob.core.windows.net"
        assert asset.software_function == "Storage blob to house unstructured files uploaded to the platform"
        assert not asset.is_public_facing  # Storage account is not public facing by default

    @patch(f"{PATH}.DefenderApi")
    def test_parse_asset_cdn_profile(self, mock_defender_api_class):
        """Test parsing a CDN profile asset"""
        mock_api = MagicMock(spec=DefenderApi)
        mock_defender_api_class.return_value = mock_api

        scanner = DefenderScanner(plan_id=1, is_component=False)

        defender_asset = {
            "resourceId": "/subscriptions/test/resourceGroups/test-rg/providers/Microsoft.Cdn/profiles/testcdn",
            "resourceName": "testcdn",
            "resourceType": "microsoft.cdn/profiles",
            "resourceLocation": "global",
            "resourceGroup": "test-rg",
            "ipAddress": "",
            "properties": {},
        }

        asset = scanner.parse_asset(defender_asset)

        assert isinstance(asset, IntegrationAsset)
        assert asset.name == "testcdn"
        assert asset.is_public_facing is True  # CDN profiles are public facing
        assert asset.software_function.startswith("Monitoring and controlling inbound and outbound traffic")

    @patch(f"{PATH}.DefenderApi")
    def test_parse_asset_network_security_group(self, mock_defender_api_class):
        """Test parsing a network security group asset"""
        mock_api = MagicMock(spec=DefenderApi)
        mock_defender_api_class.return_value = mock_api

        scanner = DefenderScanner(plan_id=1, is_component=False)

        defender_asset = {
            "resourceId": "/subscriptions/test/resourceGroups/test-rg/providers/Microsoft.Network/networkSecurityGroups/test-nsg",
            "resourceName": "test-nsg",
            "resourceType": "microsoft.network/networksecuritygroups",
            "resourceLocation": "eastus",
            "resourceGroup": "test-rg",
            "ipAddress": "",
            "properties": {"securityRules": [{"properties": {"destinationAddressPrefix": "10.0.0.0/24"}}]},
        }

        asset = scanner.parse_asset(defender_asset)

        assert isinstance(asset, IntegrationAsset)
        assert asset.name == "test-nsg"
        assert asset.ip_address == "10.0.0.0/24"
        assert asset.software_function == "Network protection for internal communications and load balancing"

    @patch(f"{PATH}.DefenderApi")
    def test_parse_asset_key_vault(self, mock_defender_api_class):
        """Test parsing a key vault asset"""
        mock_api = MagicMock(spec=DefenderApi)
        mock_defender_api_class.return_value = mock_api

        scanner = DefenderScanner(plan_id=1, is_component=False)

        defender_asset = {
            "resourceId": "/subscriptions/test/resourceGroups/test-rg/providers/Microsoft.KeyVault/vaults/testkv",
            "resourceName": "testkv",
            "resourceType": "microsoft.keyvault/vaults",
            "resourceLocation": "eastus",
            "resourceGroup": "test-rg",
            "ipAddress": "",
            "properties": {"vaultUri": "https://testkv.vault.azure.net/"},
        }

        asset = scanner.parse_asset(defender_asset)

        assert isinstance(asset, IntegrationAsset)
        assert asset.name == "testkv"
        assert asset.fqdn == "https://testkv.vault.azure.net/"
        assert asset.software_function == "To securely store API keys, passwords, certificates, or cryptographic keys"

    @patch(f"{PATH}.DefenderApi")
    def test_parse_asset_with_component_parent(self, mock_defender_api_class):
        """Test parsing asset with component as parent"""
        mock_api = MagicMock(spec=DefenderApi)
        mock_defender_api_class.return_value = mock_api

        scanner = DefenderScanner(plan_id=1, is_component=True)

        defender_asset = {
            "resourceId": "/subscriptions/test/vm1",
            "resourceName": "test-vm",
            "resourceType": "microsoft.compute/virtualmachines",
            "resourceLocation": "eastus",
            "resourceGroup": "test-rg",
            "ipAddress": "10.0.0.1",
            "properties": {},
        }

        with patch("regscale.models.regscale_models") as mock_models:
            mock_models.Component.get_module_slug.return_value = "components"
            mock_models.SecurityPlan.get_module_slug.return_value = "securityPlans"

            asset = scanner.parse_asset(defender_asset)

            assert asset.parent_module == "components"
            mock_models.Component.get_module_slug.assert_called_once()

    @patch(f"{PATH}.DefenderApi")
    def test_parse_asset_with_security_plan_parent(self, mock_defender_api_class):
        """Test parsing asset with security plan as parent"""
        mock_api = MagicMock(spec=DefenderApi)
        mock_defender_api_class.return_value = mock_api

        scanner = DefenderScanner(plan_id=1, is_component=False)

        defender_asset = {
            "resourceId": "/subscriptions/test/vm1",
            "resourceName": "test-vm",
            "resourceType": "microsoft.compute/virtualmachines",
            "resourceLocation": "eastus",
            "resourceGroup": "test-rg",
            "ipAddress": "10.0.0.1",
            "properties": {},
        }

        with patch("regscale.models.regscale_models") as mock_models:
            mock_models.Component.get_module_slug.return_value = "components"
            mock_models.SecurityPlan.get_module_slug.return_value = "securityPlans"

            asset = scanner.parse_asset(defender_asset)

            assert asset.parent_module == "securityPlans"
            mock_models.SecurityPlan.get_module_slug.assert_called_once()

    @patch(f"{PATH}.DefenderApi")
    def test_parse_asset_empty_ip_mapping(self, mock_defender_api_class):
        """Test parsing asset when IP mapping fails due to IndexError"""
        mock_api = MagicMock(spec=DefenderApi)
        mock_defender_api_class.return_value = mock_api

        scanner = DefenderScanner(plan_id=1, is_component=False)

        defender_asset = {
            "resourceId": "/subscriptions/test/vm1",
            "resourceName": "test-vm",
            "resourceType": "microsoft.network/networksecuritygroups",
            "resourceLocation": "eastus",
            "resourceGroup": "test-rg",
            "ipAddress": "",
            "properties": {"securityRules": []},  # Empty list will cause IndexError
        }

        asset = scanner.parse_asset(defender_asset)

        assert isinstance(asset, IntegrationAsset)
        assert asset.name == "test-vm"
        assert asset.ip_address is None

    @patch(f"{PATH}.DefenderApi")
    def test_parse_asset_empty_fqdn_mapping(self, mock_defender_api_class):
        """Test parsing asset when FQDN mapping fails due to IndexError"""
        mock_api = MagicMock(spec=DefenderApi)
        mock_defender_api_class.return_value = mock_api

        scanner = DefenderScanner(plan_id=1, is_component=False)

        defender_asset = {
            "resourceId": "/subscriptions/test/app1",
            "resourceName": "test-app",
            "resourceType": "microsoft.app/containerapps",
            "resourceLocation": "eastus",
            "resourceGroup": "test-rg",
            "ipAddress": "",
            "properties": {"configuration": {"ingress": {}}},  # Missing fqdn will cause IndexError in complex mapping
        }

        asset = scanner.parse_asset(defender_asset)

        assert isinstance(asset, IntegrationAsset)
        assert asset.name == "test-app"
        # Should not have fqdn set since mapping failed
        assert not hasattr(asset, "fqdn") or asset.fqdn is None

    @patch(f"{PATH}.DefenderApi")
    def test_parse_asset_with_custom_description(self, mock_defender_api_class):
        """Test parsing asset with custom description from properties"""
        mock_api = MagicMock(spec=DefenderApi)
        mock_defender_api_class.return_value = mock_api

        scanner = DefenderScanner(plan_id=1, is_component=False)

        defender_asset = {
            "resourceId": "/subscriptions/test/custom1",
            "resourceName": "test-custom",
            "resourceType": "custom.provider/resources",  # Unknown type
            "resourceLocation": "eastus",
            "resourceGroup": "test-rg",
            "ipAddress": "",
            "properties": {"description": "Custom resource description"},
        }

        with patch(f"{PATH}.generate_html_table_from_dict") as mock_generate_table:
            mock_generate_table.return_value = "<table>Asset details</table>"

            asset = scanner.parse_asset(defender_asset)

            assert asset.software_function == "Custom resource description"
            mock_generate_table.assert_called_once_with(defender_asset)

    @patch(f"{PATH}.DefenderApi")
    def test_parse_asset_afd_endpoints(self, mock_defender_api_class):
        """Test parsing AFD endpoints asset type"""
        mock_api = MagicMock(spec=DefenderApi)
        mock_defender_api_class.return_value = mock_api

        scanner = DefenderScanner(plan_id=1, is_component=False)

        defender_asset = {
            "resourceId": "/subscriptions/test/afd1",
            "resourceName": "test-afd",
            "resourceType": "microsoft.cdn/profiles/afdendpoints",
            "resourceLocation": "global",
            "resourceGroup": "test-rg",
            "ipAddress": "",
            "properties": {"hostName": "test.azurefd.net"},
        }

        asset = scanner.parse_asset(defender_asset)

        assert isinstance(asset, IntegrationAsset)
        assert asset.name == "test-afd"
        assert asset.is_public_facing is True  # AFD endpoints are public facing
        assert asset.fqdn == "test.azurefd.net"
        assert asset.software_function == "Endpoint that all of the routes attach to"

    @patch(f"{PATH}.DefenderApi")
    def test_parse_asset_action_rules_not_authenticated(self, mock_defender_api_class):
        """Test parsing assets that are not authenticated scans"""
        mock_api = MagicMock(spec=DefenderApi)
        mock_defender_api_class.return_value = mock_api

        scanner = DefenderScanner(plan_id=1, is_component=False)

        # Test action rules
        defender_asset = {
            "resourceId": "/subscriptions/test/action1",
            "resourceName": "test-action",
            "resourceType": "microsoft.alertsmanagement/actionrules",
            "resourceLocation": "global",
            "resourceGroup": "test-rg",
            "ipAddress": "",
            "properties": {},
        }

        asset = scanner.parse_asset(defender_asset)

        assert asset.is_authenticated_scan is False

    @patch(f"{PATH}.DefenderApi")
    def test_parse_asset_smart_detector_not_authenticated(self, mock_defender_api_class):
        """Test parsing smart detector alert rules - not authenticated scans"""
        mock_api = MagicMock(spec=DefenderApi)
        mock_defender_api_class.return_value = mock_api

        scanner = DefenderScanner(plan_id=1, is_component=False)

        defender_asset = {
            "resourceId": "/subscriptions/test/smart1",
            "resourceName": "test-smart",
            "resourceType": "microsoft.alertsmanagement/smartdetectoralertrules",
            "resourceLocation": "global",
            "resourceGroup": "test-rg",
            "ipAddress": "",
            "properties": {},
        }

        asset = scanner.parse_asset(defender_asset)

        assert asset.is_authenticated_scan is False

    @patch(f"{PATH}.DefenderApi")
    def test_parse_asset_dns_zone_name_as_fqdn(self, mock_defender_api_class):
        """Test parsing private DNS zone where name is used as FQDN"""
        mock_api = MagicMock(spec=DefenderApi)
        mock_defender_api_class.return_value = mock_api

        scanner = DefenderScanner(plan_id=1, is_component=False)

        defender_asset = {
            "resourceId": "/subscriptions/test/dns1",
            "resourceName": "test.private.dns",
            "resourceType": "microsoft.network/privatednszones",
            "resourceLocation": "global",
            "resourceGroup": "test-rg",
            "ipAddress": "",
            "properties": {},
        }

        asset = scanner.parse_asset(defender_asset)

        assert asset.fqdn == "test.private.dns"
        assert asset.software_function == "Dns zone that will connect to the private endpoint and network interfaces"
