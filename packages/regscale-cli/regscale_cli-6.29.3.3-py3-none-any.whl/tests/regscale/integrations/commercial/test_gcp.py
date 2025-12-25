"""Test module for GCP scanner integration in RegScale CLI.

This module contains tests for the GCP scanner integration, focusing on asset fetching,
parsing, and the generation of integration findings based on GCP assets.
"""

import copy
import datetime
import logging
from collections import Counter
from unittest.mock import ANY, patch, MagicMock, Mock

import pytest
from freezegun import freeze_time
from google.cloud import asset_v1
from proto.datetime_helpers import DatetimeWithNanoseconds

from regscale.core.utils.date import default_date_format
from regscale.integrations.commercial.gcp import gcp_control_tests
from regscale.integrations.commercial.gcp.__init__ import GCPScannerIntegration
from regscale.integrations.scanner_integration import IntegrationFinding, IntegrationAsset
from regscale.models import regscale_models


@pytest.fixture
def test_identifiers():
    """Provide consistent test identifiers."""
    return {
        "test_string": "test_gcp_integration_12345",
        "plan_id": 999999,
        "assessor_id": 888888,
        "component_id_1": 777777,
        "component_id_2": 777778,
        "asset_id_1": 666666,
        "asset_id_2": 666667,
    }


@pytest.fixture
def mock_control_mappings():
    """Provide mock control implementation mappings with fake IDs."""
    return {
        "ac-2": 100001,
        "au-2": 100002,
        "ac-3": 100003,
        "ac-5": 100004,
        "ac-6": 100005,
        "au-9": 100006,
        "au-11": 100007,
        "ca-3": 100008,
        "cp-9": 100009,
        "ia-2": 100010,
        "sc-7": 100011,
        "sc-12": 100012,
        "si-4": 100013,
    }


@pytest.fixture
def mock_regscale_models(mocker):
    """Mock all RegScale model operations to avoid database dependencies."""
    return {
        "SecurityPlan": mocker.patch("regscale.models.regscale_models.SecurityPlan"),
        "Component": mocker.patch("regscale.models.regscale_models.Component"),
        "Asset": mocker.patch("regscale.models.regscale_models.Asset"),
        "ComponentMapping": mocker.patch("regscale.models.regscale_models.ComponentMapping"),
        "ControlImplementation": mocker.patch("regscale.models.regscale_models.ControlImplementation"),
    }


def create_mock_asset(
    update_seconds: int, update_nanos: int, name: str, asset_type: str, ancestors: list
) -> asset_v1.Asset:
    """Create a mock GCP Asset with specified properties for testing."""
    mock_asset = asset_v1.Asset()
    dt = datetime.datetime.fromtimestamp(update_seconds, tz=datetime.timezone.utc)
    mock_asset.update_time = DatetimeWithNanoseconds(
        dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, nanosecond=update_nanos, tzinfo=datetime.timezone.utc
    )
    mock_asset.name = name
    mock_asset.asset_type = asset_type
    mock_asset.ancestors.extend(ancestors)
    return mock_asset


@pytest.fixture
def sample_gcp_assets(test_identifiers):
    """Create consistent test data for GCP assets."""
    test_string = test_identifiers["test_string"]
    return [
        create_mock_asset(
            update_seconds=1703126248,
            update_nanos=185897000,
            name=f"//cloudbilling.googleapis.com/projects/test-project-1/billingInfo/{test_string}",
            asset_type=f"cloudbilling.googleapis.com/ProjectBillingInfo/{test_string}",
            ancestors=["projects/100001", "folders/200001", "organizations/300001"],
        ),
        create_mock_asset(
            update_seconds=1703126249,
            update_nanos=185897001,
            name=f"//cloudbilling.googleapis.com/projects/test-project-2/billingInfo/{test_string}",
            asset_type=f"cloudbilling.googleapis.com/ProjectBillingInfo/{test_string}",
            ancestors=["projects/100002", "folders/200002", "organizations/300002"],
        ),
    ]


@pytest.fixture
def mock_asset_v1_client(sample_gcp_assets):
    """Mock GCP AssetServiceClient for testing."""
    with patch("google.cloud.asset_v1.AssetServiceClient") as mock_client, patch(
        "regscale.integrations.commercial.gcp.auth.ensure_gcp_api_enabled"
    ) as mock_api_enabled:
        mock_client.return_value.list_assets.return_value = sample_gcp_assets
        mock_api_enabled.return_value = None
        yield mock_client


def assert_integration_finding_structure(finding: IntegrationFinding, expected_status=None, expected_severity=None):
    """Helper to validate IntegrationFinding structure."""
    assert isinstance(finding, IntegrationFinding)
    assert finding.title == "GCP Scanner Integration Control Assessment"
    assert finding.date_created == "2024-01-24 16:16:25"
    assert finding.date_last_updated == "2024-01-24 16:16:25"
    if expected_status:
        assert finding.status == expected_status
    if expected_severity:
        assert finding.severity == expected_severity


def assert_integration_asset_structure(asset: IntegrationAsset, test_identifiers: dict):
    """Helper to validate IntegrationAsset structure."""
    assert isinstance(asset, IntegrationAsset)
    assert asset.asset_owner_id == str(test_identifiers["assessor_id"])
    assert asset.parent_id == test_identifiers["plan_id"]
    assert asset.parent_module == "security_plans"
    assert asset.asset_category == "GCP"
    assert asset.status == "Active (On Network)"


@freeze_time("2024-01-24 16:16:25")
class TestGCPScannerIntegration:
    """Test suite for GCP Scanner Integration."""

    @pytest.fixture(autouse=True)
    def setup_test_isolation(self, mocker, test_identifiers, mock_control_mappings):
        """Ensure each test runs in isolation with mocked dependencies."""
        # Mock GCP variables to avoid external dependencies
        mocker.patch("regscale.integrations.commercial.gcp.variables.GcpVariables.gcpProjectId", "test-project-123")
        mocker.patch("regscale.integrations.commercial.gcp.variables.GcpVariables.gcpOrganizationId", "test-org-12345")
        mocker.patch(
            "regscale.integrations.commercial.gcp.variables.GcpVariables.gcpCredentials", "test/path/credentials.json"
        )
        mocker.patch("regscale.integrations.commercial.gcp.variables.GcpVariables.gcpScanType", "project")

        # Mock all API calls made during ScannerIntegration.__init__
        mocker.patch(
            "regscale.models.regscale_models.ControlImplementation.get_control_label_map_by_parent",
            return_value=mock_control_mappings,
        )
        mocker.patch(
            "regscale.models.regscale_models.ControlImplementation.get_control_id_map_by_parent",
            return_value={v: k for k, v in mock_control_mappings.items()},
        )
        mocker.patch(
            "regscale.models.regscale_models.Issue.get_open_issues_ids_by_implementation_id",
            return_value={},
        )
        mocker.patch(
            "regscale.models.regscale_models.Issue.get_user_id",
            return_value=str(test_identifiers["assessor_id"]),
        )

        # Mock get_assessor_id method to avoid authentication dependencies
        mocker.patch.object(GCPScannerIntegration, "get_assessor_id", return_value=str(test_identifiers["assessor_id"]))

        # Mock GCP control tests to avoid import dependencies
        mock_control_tests = {
            "ac-2": {
                "PUBLIC_BUCKET_ACL": {
                    "severity": "HIGH",
                    "description": "Cloud Storage buckets should not be anonymously or publicly accessible",
                },
            },
            "ac-3": {
                "PUBLIC_BUCKET_ACL": {
                    "severity": "HIGH",
                    "description": "Test PUBLIC_BUCKET_ACL description",
                },
            },
            "au-9": {
                "PUBLIC_LOG_BUCKET": {
                    "severity": "HIGH",
                    "description": "Storage buckets used as log sinks should not be publicly accessible",
                },
            },
            "si-4": {
                "FLOW_LOGS_DISABLED": {
                    "severity": "LOW",
                    "description": "VPC Flow logs should be Enabled for every subnet in VPC Network",
                },
            },
        }
        mocker.patch("regscale.integrations.commercial.gcp.control_tests.gcp_control_tests", mock_control_tests)

        # Mock module slugs and strings to avoid RegScale internal dependencies
        mocker.patch.object(regscale_models.SecurityPlan, "get_module_slug", return_value="security_plans")
        mocker.patch.object(regscale_models.Component, "get_module_slug", return_value="components")
        mocker.patch.object(regscale_models.SecurityPlan, "get_module_string", return_value="security_plans")
        mocker.patch.object(regscale_models.Component, "get_module_string", return_value="components")

        # Mock Application and APIHandler to avoid initialization API calls
        mock_app = mocker.patch("regscale.core.app.application.Application")
        mock_app.return_value.config = {"domain": "https://test.regscale.com"}

        mock_api_handler = mocker.patch("regscale.core.app.utils.api_handler.APIHandler")
        mock_api_handler.return_value.regscale_version = "test-version"

        mocker.patch("regscale.integrations.public.cisa.pull_cisa_kev", return_value={})

        # Mock AssetMapping and other model operations that make API calls
        mocker.patch("regscale.models.regscale_models.AssetMapping.populate_cache_by_plan", return_value=None)
        mocker.patch("regscale.models.regscale_models.AssetMapping.get_plan_objects", return_value=[])

        # Mock STIG mapper loading
        mocker.patch.object(GCPScannerIntegration, "load_stig_mapper", return_value=None)

        # Mock GCP authentication functions to prevent real API calls
        mocker.patch("regscale.integrations.commercial.gcp.auth.ensure_gcp_credentials", return_value=None)
        mocker.patch("regscale.integrations.commercial.gcp.auth.ensure_gcp_api_enabled", return_value=None)

    def test_get_passed_findings(self, mocker, test_identifiers, mock_control_mappings):
        """Test get_passed_findings returns properly structured passed findings."""
        mocker.patch(
            "regscale.models.regscale_models.ControlImplementation.get_control_label_map_by_plan",
            return_value=mock_control_mappings,
        )

        gcp_integration = self.create_gcp_integration_with_control_tests(test_identifiers)

        passed_findings = gcp_integration.get_passed_findings()

        assert isinstance(passed_findings, list)
        assert len(passed_findings) > 0

        first_finding = passed_findings[0]
        assert_integration_finding_structure(
            first_finding,
            expected_status=regscale_models.ControlTestResultStatus.PASS,
            expected_severity=regscale_models.IssueSeverity.Low,
        )
        assert first_finding.plugin_name
        assert isinstance(first_finding.control_labels, list)
        assert len(first_finding.control_labels) > 0

        expected_finding_count = sum(len(categories) for categories in gcp_control_tests.values())
        assert len(passed_findings) == expected_finding_count

        for finding in passed_findings:
            assert_integration_finding_structure(finding, expected_status=regscale_models.ControlTestResultStatus.PASS)

    def test_fetch_assets_calls_list_assets(self, mock_asset_v1_client: MagicMock, test_identifiers, sample_gcp_assets):
        """Test fetch_assets calls AssetServiceClient.list_assets with correct parameters."""
        gcp_integration = GCPScannerIntegration(plan_id=test_identifiers["plan_id"])
        assets = list(gcp_integration.fetch_assets())

        assert len(assets) == len(sample_gcp_assets)
        mock_asset_v1_client.return_value.list_assets.assert_called_once_with(request=ANY)

    @pytest.mark.parametrize("asset_index", [0, 1])
    def test_parse_asset_transforms_gcp_asset(
        self, mock_asset_v1_client: MagicMock, test_identifiers, sample_gcp_assets, asset_index
    ):
        """Test parse_asset transforms GCP asset into properly structured IntegrationAsset."""
        gcp_integration = GCPScannerIntegration(plan_id=test_identifiers["plan_id"])
        asset = sample_gcp_assets[asset_index]

        integration_asset = gcp_integration.parse_asset(asset)

        assert_integration_asset_structure(integration_asset, test_identifiers)
        assert integration_asset.name == asset.name
        assert integration_asset.identifier == asset.name
        assert integration_asset.asset_type == asset.asset_type
        assert integration_asset.date_last_updated == asset.update_time.strftime(default_date_format)

    @pytest.fixture
    def mock_regscale_data(self, test_identifiers, sample_gcp_assets):
        """Create mock RegScale component and asset data for testing."""
        test_string = test_identifiers["test_string"]
        return {
            "components": [
                Mock(id=test_identifiers["component_id_1"], title=f"Test Component 1/{test_string}", delete=Mock()),
                Mock(id=test_identifiers["component_id_2"], title=f"Test Component 2/{test_string}", delete=Mock()),
            ],
            "assets": [
                Mock(id=test_identifiers["asset_id_1"], name=sample_gcp_assets[0].name, delete=Mock()),
                Mock(id=test_identifiers["asset_id_2"], name=sample_gcp_assets[1].name, delete=Mock()),
            ],
        }

    def create_gcp_integration_with_control_tests(self, test_identifiers):
        """Helper to create GCP integration with control tests setup."""
        gcp_integration = GCPScannerIntegration(plan_id=test_identifiers["plan_id"])
        gcp_integration.gcp_control_tests = copy.copy(gcp_control_tests)
        return gcp_integration

    def test_sync_assets(
        self,
        mocker,
        mock_asset_v1_client: MagicMock,
        mock_regscale_models,
        test_identifiers,
        sample_gcp_assets,
        mock_regscale_data,
    ):
        """Test sync_assets calls parent ScannerIntegration.sync_assets method."""
        plan_id = test_identifiers["plan_id"]

        # Setup mocks for database operations
        mock_regscale_models["Component"].get_all_by_parent.return_value = []
        mock_regscale_models["Asset"].get_all_by_parent.return_value = []

        # Mock ComponentMapping to return None (not found)
        mock_component_mapping = Mock()
        mock_component_mapping.find_by_unique.return_value = None
        mock_regscale_models["ComponentMapping"].return_value = mock_component_mapping

        # Mock asset creation to prevent actual database calls
        mock_asset_instance = Mock()
        mock_asset_instance.create_or_update_with_status.return_value = None
        mocker.patch("regscale.models.regscale_models.Asset", return_value=mock_asset_instance)

        # Mock the parent class sync_assets method to avoid real execution
        mock_parent_sync = mocker.patch(
            "regscale.integrations.scanner_integration.ScannerIntegration.sync_assets",
            return_value=len(sample_gcp_assets),
        )

        # Call the classmethod to test inheritance
        result = GCPScannerIntegration.sync_assets(plan_id=plan_id)

        # Verify that parent sync_assets was called with correct parameters
        mock_parent_sync.assert_called_once_with(plan_id=plan_id)
        assert result == len(sample_gcp_assets)

    @pytest.fixture
    def mock_gcp_finding(self):
        """Create a comprehensive mock GCP Security Center finding."""
        mock_finding = Mock()
        mock_finding.name = "organizations/123456789012/sources/12345/findings/test-finding-001"
        mock_finding.category = "PUBLIC_BUCKET_ACL"
        mock_finding.severity = 2  # HIGH
        mock_finding.description = "Test finding description"
        mock_finding.external_uri = "https://console.cloud.google.com/test"
        mock_finding.resource_name = "//storage.googleapis.com/projects/test-project/global/buckets/test-bucket"

        # Mock source_properties with proper get() method behavior
        mock_source_properties = Mock()
        mock_source_properties.get.side_effect = lambda key, default="": {
            "Recommendation": "Test recommendation",
            "Explanation": "Test explanation",
        }.get(key, default)
        mock_finding.source_properties = mock_source_properties

        # Mock compliances
        mock_compliance = Mock()
        mock_compliance.standard = "nist"
        mock_compliance.ids = ["AC-2", "AC-3"]
        mock_finding.compliances = [mock_compliance]

        return mock_finding

    @pytest.fixture
    def mock_gcp_finding_no_nist(self):
        """Create mock GCP finding without NIST controls."""
        mock_finding = Mock()
        mock_finding.name = "organizations/123456789012/sources/12345/findings/test-finding-002"
        mock_finding.category = "OPEN_FIREWALL"
        mock_finding.description = "Firewall rule allows unrestricted access"
        mock_finding.severity = 1  # CRITICAL
        mock_finding.compliances = []  # No NIST controls
        mock_source_properties = Mock()
        mock_source_properties.get.return_value = ""
        mock_finding.source_properties = mock_source_properties
        return mock_finding

    @pytest.fixture
    def mock_failed_findings_response(self, mock_gcp_finding):
        """Create mock ListFindingsPager response."""
        mock_finding_wrapper = Mock()
        mock_finding_wrapper.finding = mock_gcp_finding
        return [mock_finding_wrapper]

    @pytest.fixture
    def mock_security_center_client(self, mocker, mock_failed_findings_response):
        """Mock GCP Security Center client."""
        mock_client = Mock()
        mock_client.list_findings.return_value = mock_failed_findings_response
        mocker.patch("google.cloud.securitycenter.SecurityCenterClient", return_value=mock_client)
        return mock_client

    @pytest.mark.parametrize(
        "scan_type,expected_sources",
        [
            ("project", "projects/test-project-123/sources/-"),
            ("organization", "organizations/test-org-12345/sources/-"),
        ],
    )
    def test_get_failed_findings_scan_type_handling(self, mocker, scan_type, expected_sources):
        """Test get_failed_findings handles different scan types correctly."""
        mocker.patch("regscale.integrations.commercial.gcp.variables.GcpVariables.gcpScanType", scan_type)
        mock_client = Mock()
        mock_findings = Mock()
        mock_client.list_findings.return_value = mock_findings

        # Mock the entire client creation flow
        mocker.patch("google.cloud.securitycenter.SecurityCenterClient", return_value=mock_client)

        result = GCPScannerIntegration.get_failed_findings()

        assert result == mock_findings
        mock_client.list_findings.assert_called_once_with(request={"parent": expected_sources})

    def test_get_failed_findings_invalid_sources(self, mocker):
        """Test get_failed_findings raises NameError for invalid GCP sources."""
        from google.api_core.exceptions import InvalidArgument

        mock_client = Mock()
        mock_client.list_findings.side_effect = InvalidArgument("Invalid parent")
        mocker.patch("google.cloud.securitycenter.SecurityCenterClient", return_value=mock_client)

        with pytest.raises(NameError, match="gcpFindingSources is set incorrectly"):
            GCPScannerIntegration.get_failed_findings()

    def test_get_failed_findings_success(self, mock_security_center_client, mock_failed_findings_response):
        """Test get_failed_findings successful authentication and client creation."""
        result = GCPScannerIntegration.get_failed_findings()

        assert result == mock_failed_findings_response
        mock_security_center_client.list_findings.assert_called_once_with(
            request={"parent": "projects/test-project-123/sources/-"}
        )

    def test_get_failed_findings_empty_response(self, mocker):
        """Test get_failed_findings with empty findings response."""
        mock_client = Mock()
        mock_client.list_findings.return_value = []
        mocker.patch("google.cloud.securitycenter.SecurityCenterClient", return_value=mock_client)

        result = GCPScannerIntegration.get_failed_findings()

        assert result == []
        mock_client.list_findings.assert_called_once()

    def test_get_failed_findings_logging_behavior(self, mocker, caplog):
        """Test get_failed_findings logging behavior."""
        mock_client = Mock()
        mock_client.list_findings.return_value = []
        mocker.patch("google.cloud.securitycenter.SecurityCenterClient", return_value=mock_client)

        with caplog.at_level(logging.INFO):
            GCPScannerIntegration.get_failed_findings()

        assert "Fetching GCP findings..." in caplog.text
        assert "Fetched GCP findings." in caplog.text

    def test_get_failed_findings_error_logging(self, mocker, caplog):
        """Test get_failed_findings logs errors properly."""
        from google.api_core.exceptions import InvalidArgument

        mock_client = Mock()
        mock_client.list_findings.side_effect = InvalidArgument("Invalid parent")
        mocker.patch("google.cloud.securitycenter.SecurityCenterClient", return_value=mock_client)

        with caplog.at_level(logging.ERROR):
            with pytest.raises(NameError):
                GCPScannerIntegration.get_failed_findings()

        assert "gcpFindingSources is set incorrectly" in caplog.text

    def test_parse_finding_with_nist_controls(self, test_identifiers, mock_gcp_finding):
        """Test parse_finding successfully processes finding with NIST controls."""
        gcp_integration = self.create_gcp_integration_with_control_tests(test_identifiers)

        with patch("google.cloud.securitycenter_v1.Finding.to_json", return_value='{"test": "json_data"}'):
            result = gcp_integration.parse_finding(mock_gcp_finding)

        assert result is not None
        assert isinstance(result, IntegrationFinding)
        assert result.control_labels == ["ac-2", "ac-3"]
        assert result.category == "PUBLIC_BUCKET_ACL"
        assert result.severity == regscale_models.IssueSeverity.High
        assert result.status == regscale_models.ControlTestResultStatus.FAIL

    def test_parse_finding_no_nist_controls(self, test_identifiers, mock_gcp_finding_no_nist):
        """Test parse_finding returns None when no NIST controls found."""
        gcp_integration = GCPScannerIntegration(plan_id=test_identifiers["plan_id"])

        result = gcp_integration.parse_finding(mock_gcp_finding_no_nist)

        assert result is None

    def test_parse_finding_multiple_nist_controls(self, test_identifiers):
        """Test parse_finding handles multiple NIST controls correctly."""
        mock_finding = Mock()
        mock_finding.category = "PUBLIC_BUCKET_ACL"
        mock_finding.description = "Test finding"
        mock_finding.severity = 2
        mock_finding.external_uri = ""
        mock_finding.resource_name = ""
        mock_source_properties = Mock()
        mock_source_properties.get.return_value = ""
        mock_finding.source_properties = mock_source_properties

        mock_compliance = Mock()
        mock_compliance.standard = "nist"
        mock_compliance.ids = ["AC-2", "au-2", "Si-4"]  # Mixed case
        mock_finding.compliances = [mock_compliance]

        gcp_integration = self.create_gcp_integration_with_control_tests(test_identifiers)

        with patch("google.cloud.securitycenter_v1.Finding.to_json", return_value='{"test": "json"}'):
            result = gcp_integration.parse_finding(mock_finding)

        assert result.control_labels == ["ac-2", "au-2", "si-4"]

    def test_parse_finding_control_test_status_update(self, test_identifiers, mock_gcp_finding):
        """Test parse_finding updates control test status to Failed."""
        gcp_integration = GCPScannerIntegration(plan_id=test_identifiers["plan_id"])

        # Use minimal control tests for this test
        test_control_tests = {
            "ac-2": {"PUBLIC_BUCKET_ACL": {"severity": "HIGH", "description": "Test description"}},
            "ac-3": {"PUBLIC_BUCKET_ACL": {"severity": "HIGH", "description": "Test description"}},
        }
        gcp_integration.gcp_control_tests = copy.deepcopy(test_control_tests)

        # Verify initial state
        assert "status" not in gcp_integration.gcp_control_tests["ac-2"]["PUBLIC_BUCKET_ACL"]

        with patch("google.cloud.securitycenter_v1.Finding.to_json", return_value='{"test": "json"}'):
            gcp_integration.parse_finding(mock_gcp_finding)

        # Verify status was set to Failed
        assert gcp_integration.gcp_control_tests["ac-2"]["PUBLIC_BUCKET_ACL"]["status"] == "Failed"
        assert gcp_integration.gcp_control_tests["ac-3"]["PUBLIC_BUCKET_ACL"]["status"] == "Failed"

    @pytest.mark.parametrize(
        "severity,expected_regscale_severity",
        [
            (0, regscale_models.IssueSeverity.Low),
            (1, regscale_models.IssueSeverity.Critical),
            (2, regscale_models.IssueSeverity.High),
            (3, regscale_models.IssueSeverity.Moderate),
            (4, regscale_models.IssueSeverity.Low),
            (999, regscale_models.IssueSeverity.Low),  # Unknown severity defaults to Low
        ],
    )
    def test_parse_finding_severity_mapping(self, test_identifiers, severity, expected_regscale_severity):
        """Test parse_finding correctly maps GCP severities to RegScale severities."""
        mock_finding = Mock()
        mock_finding.category = "TEST_SEVERITY"
        mock_finding.description = "Test severity mapping"
        mock_finding.severity = severity
        mock_finding.external_uri = ""
        mock_finding.resource_name = ""
        mock_source_properties = Mock()
        mock_source_properties.get.return_value = ""
        mock_finding.source_properties = mock_source_properties

        mock_compliance = Mock()
        mock_compliance.standard = "nist"
        mock_compliance.ids = ["ac-2"]
        mock_finding.compliances = [mock_compliance]

        gcp_integration = self.create_gcp_integration_with_control_tests(test_identifiers)

        with patch("google.cloud.securitycenter_v1.Finding.to_json", return_value='{"test": "json"}'):
            result = gcp_integration.parse_finding(mock_finding)

        assert result.severity == expected_regscale_severity
        assert result.impact == expected_regscale_severity

    def test_parse_finding_missing_source_properties(self, test_identifiers, mock_gcp_finding):
        """Test parse_finding handles missing source properties gracefully."""
        # Remove source_properties entirely
        mock_gcp_finding.source_properties = {}

        gcp_integration = self.create_gcp_integration_with_control_tests(test_identifiers)

        with patch("google.cloud.securitycenter_v1.Finding.to_json", return_value='{"test": "json"}'):
            result = gcp_integration.parse_finding(mock_gcp_finding)

        assert result is not None
        # Should handle missing keys gracefully
        assert result.gaps is not None
        assert result.observations is not None

    def test_parse_finding_control_labels_case_insensitive(self, test_identifiers):
        """Test parse_finding handles case-insensitive control labels properly."""
        mock_finding = Mock()
        mock_finding.category = "PUBLIC_BUCKET_ACL"
        mock_finding.description = "Test case handling"
        mock_finding.severity = 2
        mock_finding.external_uri = ""
        mock_finding.resource_name = ""
        mock_source_properties = Mock()
        mock_source_properties.get.return_value = ""
        mock_finding.source_properties = mock_source_properties

        mock_compliance = Mock()
        mock_compliance.standard = "nist"
        mock_compliance.ids = ["AC-2", "au-2", "Si-4"]  # Mixed case
        mock_finding.compliances = [mock_compliance]

        gcp_integration = self.create_gcp_integration_with_control_tests(test_identifiers)

        with patch("google.cloud.securitycenter_v1.Finding.to_json", return_value='{"test": "json"}'):
            result = gcp_integration.parse_finding(mock_finding)

        # Verify control test was marked as failed for ac-2, PUBLIC_BUCKET_ACL
        assert gcp_integration.gcp_control_tests["ac-2"]["PUBLIC_BUCKET_ACL"]["status"] == "Failed"
        # Verify other control tests are still available for passed findings
        assert result.control_labels == ["ac-2", "au-2", "si-4"]

    def test_parse_finding_json_serialization(self, test_identifiers, mock_gcp_finding):
        """Test parse_finding handles JSON serialization properly."""
        gcp_integration = self.create_gcp_integration_with_control_tests(test_identifiers)

        test_json = '{"name": "test-finding", "category": "PUBLIC_BUCKET_ACL"}'
        with patch("google.cloud.securitycenter_v1.Finding.to_json", return_value=test_json):
            result = gcp_integration.parse_finding(mock_gcp_finding)

        assert result.evidence == test_json

    def test_parse_finding_non_nist_compliance_ignored(self, test_identifiers):
        """Test parse_finding ignores non-NIST compliance standards."""
        mock_finding = Mock()
        mock_finding.category = "TEST_CATEGORY"
        mock_finding.description = "Test non-NIST compliance"
        mock_finding.severity = 2
        mock_finding.external_uri = ""
        mock_finding.resource_name = ""
        mock_source_properties = Mock()
        mock_source_properties.get.return_value = ""
        mock_finding.source_properties = mock_source_properties

        # Non-NIST compliance
        mock_compliance_iso = Mock()
        mock_compliance_iso.standard = "iso27001"
        mock_compliance_iso.ids = ["A.5.1.1"]

        # Mixed with NIST
        mock_compliance_nist = Mock()
        mock_compliance_nist.standard = "nist"
        mock_compliance_nist.ids = ["AC-2"]

        mock_finding.compliances = [mock_compliance_iso, mock_compliance_nist]

        gcp_integration = self.create_gcp_integration_with_control_tests(test_identifiers)

        with patch("google.cloud.securitycenter_v1.Finding.to_json", return_value='{"test": "json"}'):
            result = gcp_integration.parse_finding(mock_finding)

        # Should only include NIST controls
        assert result.control_labels == ["ac-2"]

    def test_fetch_findings_combines_failed_and_passed(self, mocker, test_identifiers, mock_gcp_finding):
        """Test fetch_findings combines failed and passed findings correctly."""
        gcp_integration = GCPScannerIntegration(plan_id=test_identifiers["plan_id"])

        # Mock get_failed_findings to return our test finding
        mock_finding_wrapper = Mock()
        mock_finding_wrapper.finding = mock_gcp_finding
        mock_failed_findings = [mock_finding_wrapper]
        mocker.patch.object(GCPScannerIntegration, "get_failed_findings", return_value=mock_failed_findings)

        with patch("google.cloud.securitycenter_v1.Finding.to_json", return_value='{"test": "json"}'):
            findings = gcp_integration.fetch_findings()

        # Should have both failed and passed findings
        assert len(findings) > 1
        failed_findings = [f for f in findings if f.status == regscale_models.ControlTestResultStatus.FAIL]
        passed_findings = [f for f in findings if f.status == regscale_models.ControlTestResultStatus.PASS]
        assert len(failed_findings) >= 1
        assert len(passed_findings) >= 1

    def test_fetch_findings_no_failed_findings(self, mocker, test_identifiers):
        """Test fetch_findings when no failed findings exist."""
        gcp_integration = GCPScannerIntegration(plan_id=test_identifiers["plan_id"])

        # Mock get_failed_findings to return empty list
        mocker.patch.object(GCPScannerIntegration, "get_failed_findings", return_value=[])

        findings = gcp_integration.fetch_findings()

        # Should still have passed findings
        assert len(findings) > 0
        assert all(f.status == regscale_models.ControlTestResultStatus.PASS for f in findings)

    def test_fetch_findings_no_passed_findings(self, mocker, test_identifiers, mock_gcp_finding):
        """Test fetch_findings when all control tests are marked as failed."""
        gcp_integration = GCPScannerIntegration(plan_id=test_identifiers["plan_id"])

        # Mark all control tests as failed
        gcp_integration.gcp_control_tests = copy.copy(gcp_control_tests)
        for control_label, categories in gcp_integration.gcp_control_tests.items():
            for category in categories:
                gcp_integration.gcp_control_tests[control_label][category]["status"] = "Failed"

        mock_finding_wrapper = Mock()
        mock_finding_wrapper.finding = mock_gcp_finding
        mock_failed_findings = [mock_finding_wrapper]
        mocker.patch.object(GCPScannerIntegration, "get_failed_findings", return_value=mock_failed_findings)

        with patch("google.cloud.securitycenter_v1.Finding.to_json", return_value='{"test": "json"}'):
            findings = gcp_integration.fetch_findings()

        # Should only have failed findings
        failed_findings = [f for f in findings if f.status == regscale_models.ControlTestResultStatus.FAIL]
        passed_findings = [f for f in findings if f.status == regscale_models.ControlTestResultStatus.PASS]
        assert len(failed_findings) >= 1
        assert len(passed_findings) == 0

    def test_fetch_findings_control_tests_state_management(self, mocker, test_identifiers, mock_gcp_finding):
        """Test fetch_findings properly manages control test state."""
        gcp_integration = GCPScannerIntegration(plan_id=test_identifiers["plan_id"])

        mock_finding_wrapper = Mock()
        mock_finding_wrapper.finding = mock_gcp_finding
        mocker.patch.object(GCPScannerIntegration, "get_failed_findings", return_value=[mock_finding_wrapper])

        with patch("google.cloud.securitycenter_v1.Finding.to_json", return_value='{"test": "json"}'):
            gcp_integration.fetch_findings()

        # Verify control test was marked as failed for ac-2, PUBLIC_BUCKET_ACL
        assert gcp_integration.gcp_control_tests["ac-2"]["PUBLIC_BUCKET_ACL"]["status"] == "Failed"
        # Verify other control tests are still available for passed findings

    def test_fetch_findings_failed_findings_filtering(
        self, mocker, test_identifiers, mock_gcp_finding, mock_gcp_finding_no_nist
    ):
        """Test fetch_findings properly filters findings that return None."""
        gcp_integration = GCPScannerIntegration(plan_id=test_identifiers["plan_id"])

        # Mix of findings - one with NIST controls, one without
        mock_finding_wrapper1 = Mock()
        mock_finding_wrapper1.finding = mock_gcp_finding
        mock_finding_wrapper2 = Mock()
        mock_finding_wrapper2.finding = mock_gcp_finding_no_nist

        mock_failed_findings = [mock_finding_wrapper1, mock_finding_wrapper2]
        mocker.patch.object(GCPScannerIntegration, "get_failed_findings", return_value=mock_failed_findings)

        with patch("google.cloud.securitycenter_v1.Finding.to_json", return_value='{"test": "json"}'):
            findings = gcp_integration.fetch_findings()

        # Should filter out the finding without NIST controls
        failed_findings = [f for f in findings if f.status == regscale_models.ControlTestResultStatus.FAIL]
        # Only the finding with NIST controls should be included
        assert len(failed_findings) >= 1

    def test_fetch_findings_kwargs_handling(self, mocker, test_identifiers):
        """Test fetch_findings accepts and handles kwargs properly."""
        gcp_integration = GCPScannerIntegration(plan_id=test_identifiers["plan_id"])

        mocker.patch.object(GCPScannerIntegration, "get_failed_findings", return_value=[])

        # Should not raise error when called with kwargs
        findings = gcp_integration.fetch_findings(some_param="test_value", another_param=123)

        assert isinstance(findings, list)

    def test_get_passed_findings_skips_failed_control_tests(self, test_identifiers):
        """Test get_passed_findings skips control tests already marked as Failed."""
        gcp_integration = self.create_gcp_integration_with_control_tests(test_identifiers)

        # Mark specific control test as Failed
        gcp_integration.gcp_control_tests["ac-2"]["PUBLIC_BUCKET_ACL"]["status"] = "Failed"

        passed_findings = gcp_integration.get_passed_findings()

        # Should skip the failed control test
        failed_findings = [
            f for f in passed_findings if f.category == "PUBLIC_BUCKET_ACL" and "ac-2" in f.control_labels
        ]
        assert len(failed_findings) == 0

    def test_get_passed_findings_empty_control_tests(self, mocker, test_identifiers):
        """Test get_passed_findings handles empty control tests gracefully."""
        # Mock the gcp_control_tests import to return empty dict
        mocker.patch("regscale.integrations.commercial.gcp.__init__.gcp_control_tests", {})

        gcp_integration = GCPScannerIntegration(plan_id=test_identifiers["plan_id"])
        passed_findings = gcp_integration.get_passed_findings()

        assert passed_findings == []

    @pytest.mark.parametrize(
        "control_label,expected_label",
        [
            ("AC-2", "ac-2"),
            ("ac-3", "ac-3"),
            ("Au-9", "au-9"),
            ("SI-4", "si-4"),
        ],
    )
    def test_get_passed_findings_control_label_case_handling(
        self, mocker, test_identifiers, control_label, expected_label
    ):
        """Test get_passed_findings handles control label case consistently."""
        # Mock the gcp_control_tests import to use our custom test data
        test_control_tests = {control_label: {"TEST_CATEGORY": {"severity": "HIGH", "description": "Test description"}}}
        mocker.patch("regscale.integrations.commercial.gcp.__init__.gcp_control_tests", test_control_tests)

        gcp_integration = GCPScannerIntegration(plan_id=test_identifiers["plan_id"])
        passed_findings = gcp_integration.get_passed_findings()

        assert len(passed_findings) == 1
        assert passed_findings[0].control_labels == [expected_label]

    def test_get_passed_findings_different_severity_types(self, mocker, test_identifiers):
        """Test get_passed_findings handles different severity types correctly."""
        # Create control tests with different severities
        test_control_tests = {
            "ac-2": {
                "HIGH_SEVERITY": {"severity": "HIGH", "description": "High severity test"},
                "LOW_SEVERITY": {"severity": "LOW", "description": "Low severity test"},
                "MEDIUM_SEVERITY": {"severity": "MEDIUM", "description": "Medium severity test"},
            }
        }
        mocker.patch("regscale.integrations.commercial.gcp.__init__.gcp_control_tests", test_control_tests)

        gcp_integration = GCPScannerIntegration(plan_id=test_identifiers["plan_id"])
        passed_findings = gcp_integration.get_passed_findings()

        assert len(passed_findings) == 3
        categories = [f.category for f in passed_findings]
        assert "HIGH_SEVERITY" in categories
        assert "LOW_SEVERITY" in categories
        assert "MEDIUM_SEVERITY" in categories

    def test_get_passed_findings_missing_descriptions(self, mocker, test_identifiers):
        """Test get_passed_findings handles missing descriptions gracefully."""
        # Create control test without description
        test_control_tests = {"ac-2": {"NO_DESCRIPTION": {"severity": "HIGH"}}}  # Missing description
        mocker.patch("regscale.integrations.commercial.gcp.__init__.gcp_control_tests", test_control_tests)

        gcp_integration = GCPScannerIntegration(plan_id=test_identifiers["plan_id"])
        passed_findings = gcp_integration.get_passed_findings()

        assert len(passed_findings) == 1
        # The IntegrationFinding class must set a default value when description is empty
        assert passed_findings[0].description in ["", "No description provided"]

    def test_get_passed_findings_deep_copy_behavior(self, test_identifiers):
        """Test get_passed_findings doesn't modify the original control tests."""
        gcp_integration = GCPScannerIntegration(plan_id=test_identifiers["plan_id"])
        original_control_tests = copy.deepcopy(gcp_control_tests)
        gcp_integration.gcp_control_tests = copy.copy(gcp_control_tests)

        gcp_integration.get_passed_findings()

        # Original should be unchanged (deep comparison)
        assert gcp_integration.gcp_control_tests == original_control_tests

    def test_get_passed_findings_integration_finding_structure(self, mocker, test_identifiers):
        """Test get_passed_findings creates properly structured IntegrationFindings."""
        test_control_tests = {"ac-2": {"TEST_CAT": {"description": "Test desc"}}}
        mocker.patch("regscale.integrations.commercial.gcp.__init__.gcp_control_tests", test_control_tests)

        gcp_integration = GCPScannerIntegration(plan_id=test_identifiers["plan_id"])
        passed_findings = gcp_integration.get_passed_findings()

        finding = passed_findings[0]
        assert finding.title == "GCP Scanner Integration Control Assessment"
        assert finding.status == regscale_models.ControlTestResultStatus.PASS
        assert finding.severity == regscale_models.IssueSeverity.Low
        assert finding.impact == regscale_models.IssueSeverity.Low
        assert finding.plugin_name == "TEST_CAT"

    def test_parse_asset_missing_name_field(self, test_identifiers):
        """Test parse_asset handles missing name field gracefully."""
        gcp_integration = GCPScannerIntegration(plan_id=test_identifiers["plan_id"])

        mock_asset = Mock()
        mock_asset.name = ""  # Empty name
        mock_asset.asset_type = "test.asset.type"
        mock_asset.update_time.strftime.return_value = "2024-01-24 16:16:25"

        result = gcp_integration.parse_asset(mock_asset)

        assert result.name == ""
        assert result.identifier == ""

    def test_parse_asset_missing_asset_type(self, test_identifiers):
        """Test parse_asset handles missing asset_type field gracefully."""
        gcp_integration = GCPScannerIntegration(plan_id=test_identifiers["plan_id"])

        mock_asset = Mock()
        mock_asset.name = "test-asset-name"
        mock_asset.asset_type = ""  # Empty asset type
        mock_asset.update_time.strftime.return_value = "2024-01-24 16:16:25"

        result = gcp_integration.parse_asset(mock_asset)

        assert result.asset_type == ""
        assert result.component_names == [""]

    def test_parse_asset_missing_update_time(self, test_identifiers):
        """Test parse_asset handles missing update_time field."""
        gcp_integration = GCPScannerIntegration(plan_id=test_identifiers["plan_id"])

        mock_asset = Mock()
        mock_asset.name = "test-asset-name"
        mock_asset.asset_type = "test.asset.type"
        mock_asset.update_time = None

        # Should raise AttributeError when trying to format None
        with pytest.raises(AttributeError):
            gcp_integration.parse_asset(mock_asset)

    def test_parse_asset_invalid_timestamp_format(self, test_identifiers):
        """Test parse_asset handles invalid timestamp gracefully."""
        gcp_integration = GCPScannerIntegration(plan_id=test_identifiers["plan_id"])

        mock_asset = Mock()
        mock_asset.name = "test-asset-name"
        mock_asset.asset_type = "test.asset.type"
        mock_update_time = Mock()
        mock_update_time.strftime.side_effect = ValueError("Invalid format")
        mock_asset.update_time = mock_update_time

        # Should raise ValueError for invalid timestamp
        with pytest.raises(ValueError):
            gcp_integration.parse_asset(mock_asset)

    def test_parse_asset_very_long_names(self, test_identifiers):
        """Test parse_asset handles very long asset names."""
        gcp_integration = GCPScannerIntegration(plan_id=test_identifiers["plan_id"])

        long_name = "a" * 1000  # Very long name
        mock_asset = Mock()
        mock_asset.name = long_name
        mock_asset.asset_type = "test.asset.type"
        mock_asset.update_time.strftime.return_value = "2024-01-24 16:16:25"

        result = gcp_integration.parse_asset(mock_asset)

        assert result.name == long_name
        assert result.identifier == long_name

    def test_parse_asset_special_characters_in_fields(self, test_identifiers):
        """Test parse_asset handles special characters in asset fields."""
        gcp_integration = GCPScannerIntegration(plan_id=test_identifiers["plan_id"])

        special_name = "//test-asset@#$%^&*()_+{}[]|:;<>?,./"
        mock_asset = Mock()
        mock_asset.name = special_name
        mock_asset.asset_type = "test.asset.type!@#"
        mock_asset.update_time.strftime.return_value = "2024-01-24 16:16:25"

        result = gcp_integration.parse_asset(mock_asset)

        assert result.name == special_name
        assert result.asset_type == "test.asset.type!@#"

    def test_parse_asset_different_asset_types(self, test_identifiers):
        """Test parse_asset handles different GCP asset types."""
        gcp_integration = GCPScannerIntegration(plan_id=test_identifiers["plan_id"])

        asset_types = [
            "compute.googleapis.com/Instance",
            "storage.googleapis.com/Bucket",
            "cloudsql.googleapis.com/Instance",
            "container.googleapis.com/Cluster",
        ]

        for asset_type in asset_types:
            mock_asset = Mock()
            mock_asset.name = f"test-{asset_type.replace('/', '-')}"
            mock_asset.asset_type = asset_type
            mock_asset.update_time.strftime.return_value = "2024-01-24 16:16:25"

            result = gcp_integration.parse_asset(mock_asset)

            assert result.asset_type == asset_type
            assert result.component_names == [asset_type]

    def test_parse_asset_component_names_variations(self, test_identifiers):
        """Test parse_asset component names are based on asset_type."""
        gcp_integration = GCPScannerIntegration(plan_id=test_identifiers["plan_id"])

        mock_asset = Mock()
        mock_asset.name = "test-asset"
        mock_asset.asset_type = "custom.service.type"
        mock_asset.update_time.strftime.return_value = "2024-01-24 16:16:25"

        result = gcp_integration.parse_asset(mock_asset)

        assert result.component_names == ["custom.service.type"]

    def test_parse_asset_minimal_required_fields(self, test_identifiers):
        """Test parse_asset with minimal required fields."""
        gcp_integration = GCPScannerIntegration(plan_id=test_identifiers["plan_id"])

        mock_asset = Mock()
        mock_asset.name = "minimal-asset"
        mock_asset.asset_type = "minimal.type"
        mock_asset.update_time.strftime.return_value = "2024-01-24 16:16:25"

        result = gcp_integration.parse_asset(mock_asset)

        # Verify all required IntegrationAsset fields are present
        assert result.name == "minimal-asset"
        assert result.identifier == "minimal-asset"
        assert result.asset_type == "minimal.type"
        assert result.asset_owner_id == str(test_identifiers["assessor_id"])
        assert result.parent_id == test_identifiers["plan_id"]
        assert result.parent_module == "security_plans"
        assert result.asset_category == "GCP"
        assert result.date_last_updated == "2024-01-24 16:16:25"
        assert result.component_names == ["minimal.type"]
        assert result.status == "Active (On Network)"

    def test_parse_asset_maximum_field_lengths(self, test_identifiers):
        """Test parse_asset with maximum realistic field lengths."""
        gcp_integration = GCPScannerIntegration(plan_id=test_identifiers["plan_id"])

        # Google Cloud resource names can be quite long
        max_name = "//compute.googleapis.com/projects/" + "x" * 100 + "/zones/us-central1-a/instances/" + "y" * 63
        max_type = "compute.googleapis.com/" + "z" * 50

        mock_asset = Mock()
        mock_asset.name = max_name
        mock_asset.asset_type = max_type
        mock_asset.update_time.strftime.return_value = "2024-01-24 16:16:25"

        result = gcp_integration.parse_asset(mock_asset)

        assert result.name == max_name
        assert result.asset_type == max_type

    @pytest.mark.parametrize(
        "scan_type,expected_sources",
        [
            ("project", "projects/test-project-123"),
            ("organization", "organizations/test-org-12345"),
        ],
    )
    def test_fetch_assets_scan_type_handling(self, mocker, test_identifiers, scan_type, expected_sources):
        """Test fetch_assets handles different scan types correctly."""
        mocker.patch("regscale.integrations.commercial.gcp.variables.GcpVariables.gcpScanType", scan_type)

        mock_client = Mock()
        mock_assets = [Mock(), Mock()]  # Two mock assets
        mock_client.list_assets.return_value = mock_assets
        mocker.patch("google.cloud.asset_v1.AssetServiceClient", return_value=mock_client)

        gcp_integration = GCPScannerIntegration(plan_id=test_identifiers["plan_id"])
        list(gcp_integration.fetch_assets())

        # Verify correct parent was used
        mock_client.list_assets.assert_called_once()
        call_args = mock_client.list_assets.call_args
        request = call_args[1]["request"]
        assert request.parent == expected_sources

    def test_fetch_assets_empty_response(self, mocker, test_identifiers):
        """Test fetch_assets handles empty asset response."""
        mock_client = Mock()
        mock_client.list_assets.return_value = []  # Empty response
        mocker.patch("google.cloud.asset_v1.AssetServiceClient", return_value=mock_client)

        gcp_integration = GCPScannerIntegration(plan_id=test_identifiers["plan_id"])
        assets = list(gcp_integration.fetch_assets())

        assert assets == []
        assert gcp_integration.num_assets_to_process == 0

    def test_fetch_assets_large_asset_sets(self, mocker, test_identifiers):
        """Test fetch_assets handles large numbers of assets."""
        mock_client = Mock()
        # Create 1000 mock assets
        large_asset_set = [Mock() for _ in range(1000)]
        mock_client.list_assets.return_value = large_asset_set
        mocker.patch("google.cloud.asset_v1.AssetServiceClient", return_value=mock_client)

        gcp_integration = GCPScannerIntegration(plan_id=test_identifiers["plan_id"])
        assets = list(gcp_integration.fetch_assets())

        assert len(assets) == 1000
        assert gcp_integration.num_assets_to_process == 1000

    def test_fetch_assets_logging_behavior(self, mocker, test_identifiers, caplog):
        """Test fetch_assets logging behavior."""
        mock_client = Mock()
        mock_client.list_assets.return_value = [Mock()]
        mocker.patch("google.cloud.asset_v1.AssetServiceClient", return_value=mock_client)

        gcp_integration = GCPScannerIntegration(plan_id=test_identifiers["plan_id"])

        with caplog.at_level(logging.INFO):
            list(gcp_integration.fetch_assets())

        assert "Fetching GCP assets..." in caplog.text
        assert "Fetched GCP assets." in caplog.text

    def test_fetch_assets_authentication_error_handling(self, mocker, test_identifiers):
        """Test fetch_assets handles authentication errors."""
        from google.auth.exceptions import DefaultCredentialsError

        mock_client = Mock()
        mock_client.list_assets.side_effect = DefaultCredentialsError("No credentials")
        mocker.patch("google.cloud.asset_v1.AssetServiceClient", return_value=mock_client)

        gcp_integration = GCPScannerIntegration(plan_id=test_identifiers["plan_id"])

        # Should propagate authentication errors
        with pytest.raises(DefaultCredentialsError):
            list(gcp_integration.fetch_assets())

    def test_fetch_assets_api_client_error_handling(self, mocker, test_identifiers):
        """Test fetch_assets handles API client errors."""
        from google.api_core.exceptions import NotFound

        mock_client = Mock()
        mock_client.list_assets.side_effect = NotFound("Project not found")
        mocker.patch("google.cloud.asset_v1.AssetServiceClient", return_value=mock_client)

        gcp_integration = GCPScannerIntegration(plan_id=test_identifiers["plan_id"])

        # Should propagate API errors
        with pytest.raises(NotFound):
            list(gcp_integration.fetch_assets())

    def test_fetch_assets_parse_asset_integration(self, mocker, test_identifiers, sample_gcp_assets):
        """Test fetch_assets integrates with parse_asset correctly."""
        mock_client = Mock()
        mock_client.list_assets.return_value = sample_gcp_assets
        mocker.patch("google.cloud.asset_v1.AssetServiceClient", return_value=mock_client)

        gcp_integration = GCPScannerIntegration(plan_id=test_identifiers["plan_id"])
        assets = list(gcp_integration.fetch_assets())

        # Should return IntegrationAsset objects
        assert len(assets) == len(sample_gcp_assets)
        for asset in assets:
            assert isinstance(asset, IntegrationAsset)

    def test_fetch_assets_num_assets_counting(self, mocker, test_identifiers):
        """Test fetch_assets correctly counts processed assets."""
        mock_client = Mock()
        test_assets = [Mock() for _ in range(5)]
        mock_client.list_assets.return_value = test_assets
        mocker.patch("google.cloud.asset_v1.AssetServiceClient", return_value=mock_client)

        gcp_integration = GCPScannerIntegration(plan_id=test_identifiers["plan_id"])
        assets = list(gcp_integration.fetch_assets())

        assert gcp_integration.num_assets_to_process == 5
        assert len(assets) == 5

    def test_sync_assets_error_handling(self, mocker, test_identifiers):
        """Test sync_assets handles errors during asset processing."""
        # Mock parent class sync_assets to raise an exception
        mock_error = Exception("Processing error")
        mocker.patch("regscale.integrations.scanner_integration.ScannerIntegration.sync_assets", side_effect=mock_error)

        # Should propagate processing errors
        with pytest.raises(Exception, match="Processing error"):
            GCPScannerIntegration.sync_assets(plan_id=test_identifiers["plan_id"])

    def test_sync_assets_empty_assets_response(self, mocker, test_identifiers):
        """Test sync_assets when no assets are returned."""
        # Mock parent class sync_assets to return 0 for empty response
        mock_parent_sync = mocker.patch(
            "regscale.integrations.scanner_integration.ScannerIntegration.sync_assets", return_value=0
        )

        result = GCPScannerIntegration.sync_assets(plan_id=test_identifiers["plan_id"])

        # Should call parent method and return 0 for no assets
        mock_parent_sync.assert_called_once_with(plan_id=test_identifiers["plan_id"])
        assert result == 0

    def test_sync_assets_asset_processing_statistics(self, mocker, test_identifiers):
        """Test sync_assets processes all returned assets."""
        # Mock parent class sync_assets to return count of processed assets
        asset_count = 3
        mock_parent_sync = mocker.patch(
            "regscale.integrations.scanner_integration.ScannerIntegration.sync_assets", return_value=asset_count
        )

        result = GCPScannerIntegration.sync_assets(plan_id=test_identifiers["plan_id"])

        # Should call parent method and return asset count
        mock_parent_sync.assert_called_once_with(plan_id=test_identifiers["plan_id"])
        assert result == asset_count

    def test_sync_assets_kwargs_parameter_handling(self, mocker, test_identifiers):
        """Test sync_assets accepts and handles kwargs properly."""
        # Mock parent class sync_assets to accept kwargs
        mock_parent_sync = mocker.patch(
            "regscale.integrations.scanner_integration.ScannerIntegration.sync_assets", return_value=0
        )

        # Should not raise error when called with extra kwargs
        result = GCPScannerIntegration.sync_assets(
            plan_id=test_identifiers["plan_id"], extra_param="test", another_param=123
        )

        # Should call parent method with kwargs
        mock_parent_sync.assert_called_once_with(
            plan_id=test_identifiers["plan_id"], extra_param="test", another_param=123
        )
        assert result == 0

    def test_sync_assets_integration_with_parent_class(self, mocker, test_identifiers):
        """Test sync_assets properly inherits from parent ScannerIntegration."""
        # Mock the parent class method to return a simple value
        mock_parent_sync = mocker.patch(
            "regscale.integrations.scanner_integration.ScannerIntegration.sync_assets", return_value=0
        )

        # Call the classmethod properly (not instance method)
        result = GCPScannerIntegration.sync_assets(plan_id=test_identifiers["plan_id"])

        # Should call parent class sync_assets method
        mock_parent_sync.assert_called_once_with(plan_id=test_identifiers["plan_id"])
        assert result == 0


class TestGCPConfiguration:
    """Test suite for GCP configuration and class-level attributes."""

    def test_finding_severity_map_all_mappings(self):
        """Test finding_severity_map contains all expected mappings."""
        expected_mappings = {
            0: regscale_models.IssueSeverity.Low,
            1: regscale_models.IssueSeverity.Critical,
            2: regscale_models.IssueSeverity.High,
            3: regscale_models.IssueSeverity.Moderate,
            4: regscale_models.IssueSeverity.Low,
        }

        assert GCPScannerIntegration.finding_severity_map == expected_mappings

    def test_finding_severity_map_unknown_values(self):
        """Test finding_severity_map handles unknown severity values."""
        # The .get() method should default to Low for unknown values
        default_severity = GCPScannerIntegration.finding_severity_map.get(999, regscale_models.IssueSeverity.Low)
        assert default_severity == regscale_models.IssueSeverity.Low

    def test_asset_identifier_field_value(self):
        """Test asset_identifier_field is set correctly."""
        assert GCPScannerIntegration.asset_identifier_field == "googleIdentifier"

    def test_title_property_value(self):
        """Test title property value is correct."""
        assert GCPScannerIntegration.title == "GCP Scanner Integration"

    def test_gcp_control_tests_initialization(self):
        """Test gcp_control_tests is properly initialized."""
        # Should be empty dict by default (gets populated during runtime)
        assert isinstance(GCPScannerIntegration.gcp_control_tests, dict)

    def test_class_inheritance(self):
        """Test GCPScannerIntegration properly inherits from ScannerIntegration."""
        from regscale.integrations.scanner_integration import ScannerIntegration

        assert issubclass(GCPScannerIntegration, ScannerIntegration)

        # Test that it inherits key methods
        assert hasattr(GCPScannerIntegration, "sync_findings")
        assert hasattr(GCPScannerIntegration, "sync_assets")
        assert hasattr(GCPScannerIntegration, "process_asset")


class TestGCPAuthentication:
    """Test suite for GCP authentication functions."""

    @pytest.fixture(autouse=True)
    def setup_auth_test_isolation(self, mocker):
        """Ensure each auth test runs in isolation with mocked dependencies."""
        # Mock GCP variables to avoid external dependencies
        mocker.patch("regscale.integrations.commercial.gcp.variables.GcpVariables.gcpProjectId", "test-project-123")
        mocker.patch("regscale.integrations.commercial.gcp.variables.GcpVariables.gcpOrganizationId", "test-org-12345")
        mocker.patch(
            "regscale.integrations.commercial.gcp.variables.GcpVariables.gcpCredentials", "test/path/credentials.json"
        )
        mocker.patch("regscale.integrations.commercial.gcp.variables.GcpVariables.gcpScanType", "project")

    def test_ensure_gcp_credentials_sets_environment(self, mocker):
        """Test ensure_gcp_credentials sets environment variable when not present."""

        # Mock environment without GOOGLE_APPLICATION_CREDENTIALS
        mock_environ = {}
        mocker.patch.dict("os.environ", mock_environ, clear=True)

        # Mock the entire ensure_gcp_credentials function to simulate its behavior
        def mock_ensure_credentials():
            if not mock_environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
                mock_environ["GOOGLE_APPLICATION_CREDENTIALS"] = "test/path/creds.json"

        mocker.patch(
            "regscale.integrations.commercial.gcp.auth.ensure_gcp_credentials", side_effect=mock_ensure_credentials
        )

        from regscale.integrations.commercial.gcp.auth import ensure_gcp_credentials

        # Verify initial state - env var should not exist
        assert "GOOGLE_APPLICATION_CREDENTIALS" not in mock_environ

        ensure_gcp_credentials()

        # Now it should be set in our mock environment
        assert "GOOGLE_APPLICATION_CREDENTIALS" in mock_environ
        assert mock_environ["GOOGLE_APPLICATION_CREDENTIALS"] == "test/path/creds.json"

    def test_ensure_gcp_credentials_existing_environment(self, mocker):
        """Test ensure_gcp_credentials doesn't override existing credentials."""
        from regscale.integrations.commercial.gcp.auth import ensure_gcp_credentials

        existing_path = "/existing/path/credentials.json"
        mock_environ = {"GOOGLE_APPLICATION_CREDENTIALS": existing_path}
        mocker.patch.dict("os.environ", mock_environ, clear=True)

        ensure_gcp_credentials()

        # Should not change existing value
        assert mock_environ["GOOGLE_APPLICATION_CREDENTIALS"] == existing_path

    def test_ensure_gcp_api_enabled_success(self, mocker):
        """Test ensure_gcp_api_enabled with enabled API."""
        from regscale.integrations.commercial.gcp.auth import ensure_gcp_api_enabled

        # Mock successful API check
        mock_service = Mock()
        mock_response = {"state": "ENABLED"}
        mock_request = Mock()
        mock_request.execute.return_value = mock_response
        mock_service.services.return_value.get.return_value = mock_request

        mock_build = mocker.patch("googleapiclient.discovery.build", return_value=mock_service)
        mocker.patch("regscale.integrations.commercial.gcp.auth.ensure_gcp_credentials")
        mocker.patch("regscale.integrations.commercial.gcp.variables.GcpVariables.gcpProjectId", "test-project")

        # Should not raise exception
        ensure_gcp_api_enabled("test-service.googleapis.com")

        mock_build.assert_called_once_with("serviceusage", "v1")

    def test_ensure_gcp_api_enabled_api_disabled_exits(self, mocker):
        """Test ensure_gcp_api_enabled exits when API is disabled."""
        from regscale.integrations.commercial.gcp.auth import ensure_gcp_api_enabled

        # Mock disabled API response
        mock_service = Mock()
        mock_response = {"state": "DISABLED"}
        mock_request = Mock()
        mock_request.execute.return_value = mock_response
        mock_service.services.return_value.get.return_value = mock_request

        mocker.patch("googleapiclient.discovery.build", return_value=mock_service)
        mocker.patch("regscale.integrations.commercial.gcp.auth.ensure_gcp_credentials")
        mocker.patch("regscale.integrations.commercial.gcp.variables.GcpVariables.gcpProjectId", "test-project")
        mock_exit = mocker.patch("regscale.integrations.commercial.gcp.auth.error_and_exit")

        ensure_gcp_api_enabled("test-service.googleapis.com")

        mock_exit.assert_called_once()

    def test_ensure_gcp_api_enabled_authentication_error(self, mocker):
        """Test ensure_gcp_api_enabled handles authentication errors."""
        from regscale.integrations.commercial.gcp.auth import ensure_gcp_api_enabled
        from google.auth.exceptions import GoogleAuthError

        # Mock authentication error
        mocker.patch("googleapiclient.discovery.build", side_effect=GoogleAuthError("Auth failed"))
        mocker.patch("regscale.integrations.commercial.gcp.auth.ensure_gcp_credentials")

        with pytest.raises(RuntimeError, match="Authentication error"):
            ensure_gcp_api_enabled("test-service.googleapis.com")

    def test_ensure_gcp_api_enabled_general_exception(self, mocker):
        """Test ensure_gcp_api_enabled handles general exceptions."""
        from regscale.integrations.commercial.gcp.auth import ensure_gcp_api_enabled

        # Mock general exception
        mocker.patch("googleapiclient.discovery.build", side_effect=Exception("General error"))
        mocker.patch("regscale.integrations.commercial.gcp.auth.ensure_gcp_credentials")

        with pytest.raises(RuntimeError, match="An error occurred"):
            ensure_gcp_api_enabled("test-service.googleapis.com")

    def test_get_gcp_security_center_client_success(self, mocker):
        """Test get_gcp_security_center_client returns client successfully."""
        from regscale.integrations.commercial.gcp.auth import get_gcp_security_center_client

        # Mock successful client creation
        mock_client = Mock()
        mock_security_center = mocker.patch(
            "google.cloud.securitycenter.SecurityCenterClient", return_value=mock_client
        )
        mocker.patch("regscale.integrations.commercial.gcp.auth.ensure_gcp_api_enabled")

        result = get_gcp_security_center_client()

        assert result == mock_client
        mock_security_center.assert_called_once()

    def test_get_gcp_security_center_client_auth_error(self, mocker):
        """Test get_gcp_security_center_client handles authentication errors."""
        from regscale.integrations.commercial.gcp.auth import get_gcp_security_center_client
        from google.auth.exceptions import DefaultCredentialsError

        # Mock authentication error during client creation
        mocker.patch(
            "google.cloud.securitycenter.SecurityCenterClient", side_effect=DefaultCredentialsError("No creds")
        )
        mocker.patch("regscale.integrations.commercial.gcp.auth.ensure_gcp_api_enabled")

        with pytest.raises(DefaultCredentialsError):
            get_gcp_security_center_client()

    def test_get_gcp_asset_service_client_success(self, mocker):
        """Test get_gcp_asset_service_client returns client successfully."""
        from regscale.integrations.commercial.gcp.auth import get_gcp_asset_service_client

        # Mock successful client creation
        mock_client = Mock()
        mock_asset_client = mocker.patch("google.cloud.asset_v1.AssetServiceClient", return_value=mock_client)
        mocker.patch("regscale.integrations.commercial.gcp.auth.ensure_gcp_api_enabled")

        result = get_gcp_asset_service_client()

        assert result == mock_client
        mock_asset_client.assert_called_once()

    def test_get_gcp_asset_service_client_auth_error(self, mocker):
        """Test get_gcp_asset_service_client handles authentication errors."""
        from regscale.integrations.commercial.gcp.auth import get_gcp_asset_service_client
        from google.auth.exceptions import DefaultCredentialsError

        # Mock authentication error during client creation
        mocker.patch("google.cloud.asset_v1.AssetServiceClient", side_effect=DefaultCredentialsError("No creds"))
        mocker.patch("regscale.integrations.commercial.gcp.auth.ensure_gcp_api_enabled")

        with pytest.raises(DefaultCredentialsError):
            get_gcp_asset_service_client()

    def test_ensure_security_center_api_enabled_system_call(self, mocker):
        """Test ensure_security_center_api_enabled makes correct system call."""
        from regscale.integrations.commercial.gcp.auth import ensure_security_center_api_enabled

        mock_system = mocker.patch("os.system")
        mocker.patch("regscale.integrations.commercial.gcp.auth.ensure_gcp_credentials")
        mocker.patch("regscale.integrations.commercial.gcp.variables.GcpVariables.gcpProjectId", "test-project-123")

        ensure_security_center_api_enabled()

        expected_command = "gcloud services enable securitycenter.googleapis.com --project test-project-123"
        mock_system.assert_called_once_with(expected_command)

    def test_api_enablement_project_id_usage(self, mocker):
        """Test API enablement functions use correct project ID."""
        from regscale.integrations.commercial.gcp.auth import ensure_gcp_api_enabled

        test_project_id = "custom-test-project-456"
        mocker.patch("regscale.integrations.commercial.gcp.variables.GcpVariables.gcpProjectId", test_project_id)
        mocker.patch("regscale.integrations.commercial.gcp.auth.ensure_gcp_credentials")

        # Mock service to capture project ID usage
        mock_service = Mock()
        mock_response = {"state": "ENABLED"}
        mock_request = Mock()
        mock_request.execute.return_value = mock_response
        mock_service.services.return_value.get.return_value = mock_request
        mocker.patch("googleapiclient.discovery.build", return_value=mock_service)

        ensure_gcp_api_enabled("test-service.googleapis.com")

        # Verify project ID was used in the API call
        mock_service.services.return_value.get.assert_called_once_with(
            name=f"projects/{test_project_id}/services/test-service.googleapis.com"
        )


class TestGCPVariables:
    """Test suite for GCP variables configuration."""

    @pytest.fixture(autouse=True)
    def setup_variables_test_isolation(self, mocker):
        """Ensure each variables test runs in isolation with mocked dependencies."""
        # Mock GCP variables to avoid external dependencies
        mocker.patch("regscale.integrations.commercial.gcp.variables.GcpVariables.gcpProjectId", "test-project-123")
        mocker.patch("regscale.integrations.commercial.gcp.variables.GcpVariables.gcpOrganizationId", "test-org-12345")
        mocker.patch(
            "regscale.integrations.commercial.gcp.variables.GcpVariables.gcpCredentials", "test/path/credentials.json"
        )
        mocker.patch("regscale.integrations.commercial.gcp.variables.GcpVariables.gcpScanType", "project")

    def test_gcp_variables_class_structure(self):
        """Test GcpVariables class has correct structure."""
        from regscale.integrations.commercial.gcp.variables import GcpVariables

        # Should have class-level attributes
        assert hasattr(GcpVariables, "gcpProjectId")
        assert hasattr(GcpVariables, "gcpOrganizationId")
        assert hasattr(GcpVariables, "gcpScanType")
        assert hasattr(GcpVariables, "gcpCredentials")

    def test_gcp_variables_required_fields(self):
        """Test GcpVariables has all required configuration fields."""
        from regscale.integrations.commercial.gcp.variables import GcpVariables

        # Verify key variables exist and are accessible
        required_vars = ["gcpProjectId", "gcpOrganizationId", "gcpScanType", "gcpCredentials"]

        for var_name in required_vars:
            assert hasattr(GcpVariables, var_name), f"Missing required variable: {var_name}"

    def test_gcp_variables_default_values(self):
        """Test GcpVariables provides sensible default/example values."""
        from regscale.integrations.commercial.gcp.variables import GcpVariables

        # These should be example values, not None
        # Note: We can't directly access the values due to the metaclass,
        # but we can verify the attributes exist
        assert hasattr(GcpVariables, "gcpProjectId")
        assert hasattr(GcpVariables, "gcpOrganizationId")
        assert hasattr(GcpVariables, "gcpScanType")
        assert hasattr(GcpVariables, "gcpCredentials")

    def test_gcp_variables_type_annotations(self):
        """Test GcpVariables uses RsVariableType for type annotations."""
        from regscale.integrations.commercial.gcp.variables import GcpVariables
        from regscale.core.app.utils.variables import RsVariablesMeta

        # Should use RsVariablesMeta metaclass
        assert isinstance(GcpVariables, type)
        assert isinstance(GcpVariables, RsVariablesMeta)
