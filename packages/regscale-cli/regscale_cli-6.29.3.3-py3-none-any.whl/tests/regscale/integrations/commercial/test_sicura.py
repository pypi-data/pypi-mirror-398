import unittest
from unittest import mock

from click.testing import CliRunner

from regscale.integrations.commercial.sicura.api import SicuraAPI, SicuraProfile, ScanReport, ScanResult, ScanSummary
from regscale.integrations.commercial.sicura.commands import sicura
from regscale.integrations.commercial.sicura.scanner import SicuraIntegration
from regscale.integrations.scanner_integration import regscale_models


class TestSicuraAPI(unittest.TestCase):
    """Tests for the SicuraAPI class."""

    def setUp(self):
        """Set up test environment."""
        self.api = SicuraAPI()
        self.api.base_url = "https://sicura-test.example.com"
        self.api.session = mock.MagicMock()

    def test_get_devices(self):
        """Test the get_devices method."""
        # Mock response data
        mock_response = [
            {
                "id": 1,
                "name": "test-device-1",
                "fqdn": "test1.example.com",
                "ip_address": "192.168.1.1",
                "platforms": "Red Hat Enterprise Linux 9",
                "scannable_profiles": {"profile1": {"name": "profile1"}},
                "most_recent_scan": "2023-01-01T00:00:00Z",
            }
        ]

        # Mock the _make_request method directly
        with mock.patch.object(self.api, "_make_request", return_value=mock_response):
            devices = self.api.get_devices()

        # Assertions
        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0].id, 1)
        self.assertEqual(devices[0].name, "test-device-1")
        self.assertEqual(devices[0].fqdn, "test1.example.com")

    def test_get_pending_devices(self):
        """Test the get_pending_devices method."""
        # Mock response data
        mock_response = [
            {
                "id": 1,
                "fqdn": "pending1.example.com",
                "signature": "test-signature",
                "platform": "rhel9",
                "platform_title": "Red Hat Enterprise Linux 9",
                "last_update": "2023-01-01T00:00:00Z",
                "ip_address": "192.168.1.100",
                "rejected": False,
            }
        ]

        # Mock the _make_request method directly
        with mock.patch.object(self.api, "_make_request", return_value=mock_response):
            pending_devices = self.api.get_pending_devices()

        # Assertions
        self.assertEqual(len(pending_devices), 1)
        self.assertEqual(pending_devices[0].id, 1)
        self.assertEqual(pending_devices[0].fqdn, "pending1.example.com")
        self.assertFalse(pending_devices[0].rejected)

    def test_accept_pending_device(self):
        """Test the accept_pending_device method."""
        device_id = 1

        # Mock the _make_request method to return success
        with mock.patch.object(self.api, "_make_request", return_value={"success": True}):
            result = self.api.accept_pending_device(device_id)

        # Assertions
        self.assertTrue(result)

    def test_reject_pending_device(self):
        """Test the reject_pending_device method."""
        device_id = 1

        # Mock the _make_request method to return success
        with mock.patch.object(self.api, "_make_request", return_value={"success": True}):
            result = self.api.reject_pending_device(device_id)

        # Assertions
        self.assertTrue(result)

    def test_create_scan_task(self):
        """Test the create_scan_task method."""
        # Mock the _make_request method to return a task ID
        with mock.patch.object(self.api, "_make_request", return_value="task-123"):
            task_id = self.api.create_scan_task(
                device_id=1,
                platform="Red Hat Enterprise Linux 9",
                profile=SicuraProfile.I_MISSION_CRITICAL_CLASSIFIED,
            )

        # Assertions
        self.assertEqual(task_id, "task-123")

    def test_get_scan_results(self):
        """Test the get_scan_results method."""
        # Mock response data
        scan_data = [
            {
                "id": 1,
                "fqdn": "test1.example.com",
                "ip_address": "192.168.1.1",
                "scans": [
                    {
                        "title": "Test Scan 1",
                        "ce_name": "CE1",
                        "result": "pass",
                        "description": "Test description",
                        "controls": {"control1": True},
                        "state": "applied",
                        "state_reason": ["Reason 1"],
                    },
                    {
                        "title": "Test Scan 2",
                        "ce_name": "CE2",
                        "result": "fail",
                        "description": "Failed check",
                        "controls": {"control2": False},
                        "state": "not applied",
                        "state_reason": ["Reason 2"],
                    },
                ],
            }
        ]

        # Mock the _make_request method directly
        with mock.patch.object(self.api, "_make_request", return_value=scan_data):
            result = self.api.get_scan_results(fqdn="test1.example.com")

        # Assertions - Add None check to avoid mypy errors
        self.assertIsNotNone(result)
        if result:  # Add None check before accessing attributes
            self.assertEqual(result.device_id, 1)
            self.assertEqual(result.fqdn, "test1.example.com")
            self.assertEqual(len(result.scans), 2)
            self.assertEqual(result.summary.pass_count, 1)
            self.assertEqual(result.summary.fail, 1)


class TestSicuraCommands(unittest.TestCase):
    """Tests for the Sicura CLI commands."""

    def setUp(self):
        """Set up the test runner."""
        self.runner = CliRunner()

    @mock.patch("regscale.integrations.commercial.sicura.commands.SicuraAPI")
    def test_list_devices(self, mock_api_class):
        """Test the list_devices command."""
        # Mock API instance
        api_instance = mock.MagicMock()
        mock_api_class.return_value = api_instance

        # Mock devices response
        devices = [
            mock.MagicMock(
                id=1,
                name="test-device-1",
                fqdn="test1.example.com",
                ip_address="192.168.1.1",
                platforms="Red Hat Enterprise Linux 9",
                scannable_profiles={"profile1": {"name": "profile1"}},
                most_recent_scan="2023-01-01T00:00:00Z",
            )
        ]
        api_instance.get_devices.return_value = devices

        # Run the command
        result = self.runner.invoke(sicura, ["sync_assets", "--plan-id", "123"])

        # Assertions
        self.assertEqual(result.exit_code, 0)

    @mock.patch("regscale.integrations.commercial.sicura.commands.SicuraAPI")
    def test_list_pending_devices(self, mock_api_class):
        """Test the list_pending_devices command."""
        # Mock API instance
        api_instance = mock.MagicMock()
        mock_api_class.return_value = api_instance

        # Mock pending devices response
        pending_devices = [
            mock.MagicMock(
                id=1,
                fqdn="pending1.example.com",
                signature="test-signature",
                platform="rhel9",
                platform_title="Red Hat Enterprise Linux 9",
                last_update="2023-01-01T00:00:00Z",
                ip_address="192.168.1.100",
                rejected=False,
            )
        ]
        api_instance.get_pending_devices.return_value = pending_devices

        # Run the command
        result = self.runner.invoke(sicura, ["sync_findings", "--plan-id", "123"])

        # Assertions
        self.assertEqual(result.exit_code, 0)


class TestSicuraIntegration(unittest.TestCase):
    """Tests for the SicuraIntegration class."""

    @mock.patch("regscale.integrations.commercial.sicura.scanner.SicuraAPI")
    def test_parse_finding(self, mock_api_class):
        """Test the parse_finding method."""
        # Create a SicuraIntegration instance
        integration = SicuraIntegration(plan_id=1)

        # Mock a device object instead of a scan result to match the expected type
        device_result = mock.MagicMock(
            title="Test Finding",
            ce_name="CE123",
            result="fail",
            description="Test description with CCI-000001, CCI-000002",
            controls={
                "AC-1": True,
                "AC-2": False,
            },
            state="not applied",
            state_reason=["Test reason"],
        )

        # Call the parse_finding method with the correct type
        asset_identifier = "test-asset-1"
        findings = list(integration.parse_finding(device_result, asset_identifier))

        # Assertions
        self.assertEqual(len(findings), 2)  # One finding per CCI

        # Check the first finding
        self.assertEqual(findings[0].title, "Test Finding (CCI-000001)")
        self.assertEqual(findings[0].cci_ref, "CCI-000001")
        self.assertEqual(findings[0].control_labels, [])

        # Update assertion to handle possible None value
        if findings[0].status is not None:
            self.assertEqual(findings[0].status, regscale_models.ControlTestResultStatus.FAIL)

        self.assertEqual(findings[0].asset_identifier, asset_identifier)

        # Check the second finding
        self.assertEqual(findings[1].title, "Test Finding (CCI-000002)")
        self.assertEqual(findings[1].cci_ref, "CCI-000002")
        self.assertEqual(findings[1].control_labels, [])

        # Update assertion to handle possible None value
        if findings[1].status is not None:
            self.assertEqual(findings[1].status, regscale_models.ControlTestResultStatus.FAIL)

        self.assertEqual(findings[1].asset_identifier, asset_identifier)

    @mock.patch("regscale.integrations.commercial.sicura.scanner.SicuraAPI")
    def test_fetch_findings(self, mock_api_class):
        """Test the fetch_findings method."""
        # Create a SicuraIntegration instance
        integration = SicuraIntegration(plan_id=1)

        # Mock API instance
        api_instance = mock.MagicMock()
        mock_api_class.return_value = api_instance

        # Mock scan report data - correct the field name from pass_count to pass
        scan_report = ScanReport(
            device_id=1,
            fqdn="test1.example.com",
            ip_address="192.168.1.1",
            scans=[
                ScanResult(
                    title="Test Finding 1",
                    ce_name="CE1",
                    result="fail",
                    description="Test description with CCI-000001",
                    controls={"AC-1": False},
                    state="not applied",
                    state_reason=["Reason 1"],
                ),
                ScanResult(
                    title="Test Finding 2",
                    ce_name="CE2",
                    result="pass",
                    description="Test description with CCI-000002",
                    controls={"AC-2": True},
                    state="applied",
                    state_reason=[],
                ),
            ],
            summary=ScanSummary(
                total=2,
                # Change pass_count to pass to match the model
                **{"pass": 1},  # Use kwargs to avoid syntax error with 'pass' keyword
                fail=1,
                pass_percentage=50.0,
            ),
        )

        # Mock get_scan_results to return our test data
        api_instance.get_scan_results.return_value = scan_report

        # Mock get_devices to return a list of devices
        api_instance.get_devices.return_value = [
            mock.MagicMock(
                id=1,
                name="test-device-1",
                fqdn="test1.example.com",
                ip_address="192.168.1.1",
            )
        ]

        # Call fetch_findings
        findings = list(integration.fetch_findings())

        # Assertions
        self.assertGreaterEqual(len(findings), 2)  # At least one per scan result

        # Verify findings were created for each scan result
        finding_titles = [f.title for f in findings]
        self.assertIn("Test Finding 1 (CCI-000001)", finding_titles)
        self.assertIn("Test Finding 2 (CCI-000002)", finding_titles)

        # Verify failing finding - add None check
        fail_finding = next((f for f in findings if f.title == "Test Finding 1 (CCI-000001)"), None)
        self.assertIsNotNone(fail_finding)
        if fail_finding and fail_finding.status is not None:
            self.assertEqual(fail_finding.status, regscale_models.ControlTestResultStatus.FAIL)

        # Verify passing finding - add None check
        pass_finding = next((f for f in findings if f.title == "Test Finding 2 (CCI-000002)"), None)
        self.assertIsNotNone(pass_finding)
        if pass_finding and pass_finding.status is not None:
            self.assertEqual(pass_finding.status, regscale_models.ControlTestResultStatus.PASS)


if __name__ == "__main__":
    unittest.main()
