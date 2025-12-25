import json
import pytest

from regscale.models.regscale_models import Asset, Component
from tests.fixtures.test_fixture import CLITestFixture


class TestWizInventory(CLITestFixture):
    """
    Unit tests for the WizInventory class methods.
    """

    SSP_ID = 51
    SSP_MODULE = "securityplans"

    wiz_projects = [
        "e4cf6809-734e-4b7c-8456-3eb7bd179bc8",
        "abeabc53-8774-4edf-91c0-61f228bedb1b",
    ]
    filter_by = {
        "projectId": wiz_projects,
    }
    full_inventory = True
    wiz_url = "https://api.us27.app.wiz.io/graphql"

    @pytest.fixture
    def test_wiz_data(self):
        """
        Load the test Wiz inventory data.
        """
        nodes = json.loads(
            """[
      {
        "id": "23035da6-a1bd-4779-ab04-e3adbdec5947",
        "name": "Mock Software Asset Linux Alpine",
        "type": "HOSTED_TECHNOLOGY",
        "subscriptionId": "c558b4cf-e0d7-49f5-a916-da8d8cd1b116",
        "subscriptionExternalId": "23035da6-a1bd-4779-ab04-e3adbdec5947",
        "graphEntity": {
          "id": "23035da6-a1bd-4779-ab04-e3adbdec5947",
          "providerUniqueId": "/subscriptions/23035da6-a1bd-4779-ab04-e3adbdec5947/resourcegroups/rg_tenantapp_test/providers/microsoft.storage/storageaccounts/dummystorage/blobservices/default/containers/1-test-asset-1",
          "name": "Mock Software Asset Linux Alpine",
          "type": "HOSTED_TECHNOLOGY",
          "projects": [
            {
              "id": "608016f5-742b-4ea8-a70a-c95ba6eb6c29"
            }
          ],
          "properties": {
            "_environments": "test",
            "_productIDs": "78e7e216-34c5-4871-a301-48e9322c9b89",
            "_techIDs": "5555",
            "_vertexID": "23d89702-28a7-4988-9864-bb3dc795b735",
            "alternativeRegions": "westus",
            "azurePublicAccess": false,
            "cloudPlatform": "Azure",
            "cloudProviderURL": "https://dummy-domain.com/#@domain.com/resource//subscriptions/23035da6-a1bd-4779-ab04-e3adbdec5947/resourcegroups/rg_tenantapp_test/providers/microsoft.storage/storageaccounts/dummystorage/blobservices/default/containers/1-test-asset-1",
            "creationDate": "2023-01-10T23:30:36.8921214Z",
            "encrypted": true,
            "encryptionInTransit": true,
            "externalId": "/subscriptions/23035da6-a1bd-4779-ab04-e3adbdec5947/resourcegroups/rg_tenantapp_test/providers/microsoft.storage/storageaccounts/dummytorage/blobservices/default/containers/1-test-asset-1",
            "isPublic": false,
            "loggingEnabled": true,
            "name": "test-fixture-assets-1",
            "nativeType": "Microsoft.Storage/storageAccounts/blobServices/containers",
            "providerUniqueId": "/subscriptions/23035da6-a1bd-4779-ab04-e3adbdec5947/resourcegroups/rg_tenantapp_test/providers/microsoft.storage/storageaccounts/dummytorage/blobservices/default/containers/1-test-asset-1",
            "publicExposure": "PublicExposureInvalid",
            "region": "eastus",
            "regionLocation": "US",
            "regionType": "BucketRegionTypeDualRegion",
            "resourceGroupExternalId": "/subscriptions/23035da6-a1bd-4779-ab04-e3adbdec5947/resourcegroups/rg_tenantapp_test",
            "retentionPeriod": 2592000,
            "status": "Active",
            "subscriptionExternalId": "23035da6-a1bd-4779-ab04-e3adbdec5947",
            "uniformACL": true,
            "updateDate": "2023-12-08T00:39:54Z",
            "updatedAt": "2024-01-09T17:40:12Z",
            "versioningEnabled": true,
            "webHostingEnabled": false,
            "zone": null,
            "port": 80,
            "portEnd": 80,
            "portRange": false,
            "portStart": 80,
            "portValidationResult": "Open",
            "protocol": null,
            "protocols": "HTTP",
            "cpe": "cpe:/o:alpinelinux:alpine_linux:3.18.6",
            "installedPackages": [
              "alpine-baselayout (3.4.3-r1)",
              "alpine-baselayout-data (3.4.3-r1)",
              "alpine-keys (2.4-r1)"
            ],
            "techId": "1121",
            "techName": "Linux Alpine",
            "latestVersion": "3.18.6"
          },
          "firstSeen": "2024-02-01T06:15:10Z",
          "lastSeen": "2024-02-15T13:04:10Z"
        }
      },
      {
        "id": "3056dce6-f1ae-4b94-a448-9de591e6f8a5",
        "name": "Mock Software Asset Linux Alpine 2",
        "type": "HOSTED_TECHNOLOGY",
        "subscriptionId": "c558b4cf-e0d7-49f5-a916-da8d8cd1b116",
        "subscriptionExternalId": "23035da6-a1bd-4779-ab04-e3adbdec5947",
        "graphEntity": {
          "id": "23035da6-a1bd-4779-ab04-e3adbdec5947",
          "providerUniqueId": "/subscriptions/23035da6-a1bd-4779-ab04-e3adbdec5947/resourcegroups/rg_tenantapp_test/providers/microsoft.storage/storageaccounts/dummystorage/blobservices/default/containers/1-test-asset-1",
          "name": "Mock Software Asset Linux Alpine",
          "type": "HOSTED_TECHNOLOGY",
          "projects": [
            {
              "id": "608016f5-742b-4ea8-a70a-c95ba6eb6c29"
            }
          ],
          "properties": {
            "_environments": "test",
            "_productIDs": "78e7e216-34c5-4871-a301-48e9322c9b89",
            "_techIDs": "5555",
            "_vertexID": "23d89702-28a7-4988-9864-bb3dc795b735",
            "alternativeRegions": "westus",
            "azurePublicAccess": false,
            "cloudPlatform": "Azure",
            "cloudProviderURL": "https://dummy-domain.com/#@domain.com/resource//subscriptions/23035da6-a1bd-4779-ab04-e3adbdec5947/resourcegroups/rg_tenantapp_test/providers/microsoft.storage/storageaccounts/dummystorage/blobservices/default/containers/1-test-asset-1",
            "creationDate": "2023-01-10T23:30:36.8921214Z",
            "encrypted": true,
            "encryptionInTransit": true,
            "externalId": "/subscriptions/23035da6-a1bd-4779-ab04-e3adbdec5947/resourcegroups/rg_tenantapp_test/providers/microsoft.storage/storageaccounts/dummytorage/blobservices/default/containers/1-test-asset-1",
            "isPublic": false,
            "loggingEnabled": true,
            "name": "test-fixture-assets-1",
            "nativeType": "Microsoft.Storage/storageAccounts/blobServices/containers",
            "providerUniqueId": "/subscriptions/23035da6-a1bd-4779-ab04-e3adbdec5947/resourcegroups/rg_tenantapp_test/providers/microsoft.storage/storageaccounts/dummytorage/blobservices/default/containers/1-test-asset-1",
            "publicExposure": "PublicExposureInvalid",
            "region": "eastus",
            "regionLocation": "US",
            "regionType": "BucketRegionTypeDualRegion",
            "resourceGroupExternalId": "/subscriptions/23035da6-a1bd-4779-ab04-e3adbdec5947/resourcegroups/rg_tenantapp_test",
            "retentionPeriod": 2592000,
            "status": "Active",
            "subscriptionExternalId": "23035da6-a1bd-4779-ab04-e3adbdec5947",
            "uniformACL": true,
            "updateDate": "2023-12-08T00:39:54Z",
            "updatedAt": "2024-01-09T17:40:12Z",
            "versioningEnabled": true,
            "webHostingEnabled": false,
            "zone": null,
            "port": 80,
            "portEnd": 80,
            "portRange": false,
            "portStart": 80,
            "portValidationResult": "Open",
            "protocol": null,
            "protocols": "HTTP",
            "cpe": "cpe:/o:alpinelinux:alpine_linux:3.18.6",
            "installedPackages": [
              "alpine-baselayout (3.4.3-r1)",
              "alpine-baselayout-data (3.4.3-r1)",
              "alpine-keys (2.4-r1)"
            ],
            "techId": "1121",
            "techName": "Linux Alpine",
            "latestVersion": "3.18.6"
          },
          "firstSeen": "2024-02-01T06:15:10Z",
          "lastSeen": "2024-02-15T13:04:10Z"
        }
      },
      {
        "id": "d31f37cc-61e8-4b2a-be64-c078b9abdfa6",
        "name": "Mock Software Asset Linux Alpine 3",
        "type": "HOSTED_TECHNOLOGY",
        "subscriptionId": "c558b4cf-e0d7-49f5-a916-da8d8cd1b116",
        "subscriptionExternalId": "23035da6-a1bd-4779-ab04-e3adbdec5947",
        "graphEntity": {
          "id": "23035da6-a1bd-4779-ab04-e3adbdec5947",
          "providerUniqueId": "/subscriptions/23035da6-a1bd-4779-ab04-e3adbdec5947/resourcegroups/rg_tenantapp_test/providers/microsoft.storage/storageaccounts/dummystorage/blobservices/default/containers/1-test-asset-1",
          "name": "Mock Software Asset Linux Alpine",
          "type": "HOSTED_TECHNOLOGY",
          "projects": [
            {
              "id": "608016f5-742b-4ea8-a70a-c95ba6eb6c29"
            }
          ],
          "properties": {
            "_environments": "test",
            "_productIDs": "78e7e216-34c5-4871-a301-48e9322c9b89",
            "_techIDs": "5555",
            "_vertexID": "23d89702-28a7-4988-9864-bb3dc795b735",
            "alternativeRegions": "westus",
            "azurePublicAccess": false,
            "cloudPlatform": "Azure",
            "cloudProviderURL": "https://dummy-domain.com/#@domain.com/resource//subscriptions/23035da6-a1bd-4779-ab04-e3adbdec5947/resourcegroups/rg_tenantapp_test/providers/microsoft.storage/storageaccounts/dummystorage/blobservices/default/containers/1-test-asset-1",
            "creationDate": "2023-01-10T23:30:36.8921214Z",
            "encrypted": true,
            "encryptionInTransit": true,
            "externalId": "/subscriptions/23035da6-a1bd-4779-ab04-e3adbdec5947/resourcegroups/rg_tenantapp_test/providers/microsoft.storage/storageaccounts/dummytorage/blobservices/default/containers/1-test-asset-1",
            "isPublic": false,
            "loggingEnabled": true,
            "name": "test-fixture-assets-1",
            "nativeType": "Microsoft.Storage/storageAccounts/blobServices/containers",
            "providerUniqueId": "/subscriptions/23035da6-a1bd-4779-ab04-e3adbdec5947/resourcegroups/rg_tenantapp_test/providers/microsoft.storage/storageaccounts/dummytorage/blobservices/default/containers/1-test-asset-1",
            "publicExposure": "PublicExposureInvalid",
            "region": "eastus",
            "regionLocation": "US",
            "regionType": "BucketRegionTypeDualRegion",
            "resourceGroupExternalId": "/subscriptions/23035da6-a1bd-4779-ab04-e3adbdec5947/resourcegroups/rg_tenantapp_test",
            "retentionPeriod": 2592000,
            "status": "Active",
            "subscriptionExternalId": "23035da6-a1bd-4779-ab04-e3adbdec5947",
            "uniformACL": true,
            "updateDate": "2023-12-08T00:39:54Z",
            "updatedAt": "2024-01-09T17:40:12Z",
            "versioningEnabled": true,
            "webHostingEnabled": false,
            "zone": null,
            "port": 80,
            "portEnd": 80,
            "portRange": false,
            "portStart": 80,
            "portValidationResult": "Open",
            "protocol": null,
            "protocols": "HTTP",
            "cpe": "cpe:/o:alpinelinux:alpine_linux:3.18.6",
            "installedPackages": [
              "alpine-baselayout (3.4.3-r1)",
              "alpine-baselayout-data (3.4.3-r1)",
              "alpine-keys (2.4-r1)"
            ],
            "techId": "1121",
            "techName": "Linux Alpine",
            "latestVersion": "3.18.6"
          },
          "firstSeen": "2024-02-01T06:15:10Z",
          "lastSeen": "2024-02-15T13:04:10Z"
        }
      }
    ]"""
        )
        return nodes

    def test_cleanup_inventory(self, test_wiz_data):
        """
        Test the cleanup_inventory method to ensure it removes any inventory items that are no longer present in Wiz.
        """

        assets = Asset.get_all_by_parent(parent_id=self.SSP_ID, parent_module=self.SSP_MODULE)
        components = Component.get_all_by_parent(parent_id=self.SSP_ID, parent_module=self.SSP_MODULE)
        for asset in assets:
            if asset.wizId != "23035da6-a1bd-4779-ab04-e3adbdec5947":
                asset.delete()
            asset.delete()
        for component in components:
            component.delete()
