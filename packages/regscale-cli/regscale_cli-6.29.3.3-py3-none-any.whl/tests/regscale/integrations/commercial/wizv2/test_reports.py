"""Tests for Wiz Report Management."""

import unittest
from unittest.mock import patch, MagicMock, mock_open
import requests

from regscale.integrations.commercial.wizv2.reports import WizReportManager


@patch("time.sleep", return_value=None)
class TestWizReportManager(unittest.TestCase):
    """Test cases for WizReportManager."""

    def setUp(self):
        """Set up test fixtures."""
        self.api_url = "https://api.wiz.io/graphql"
        self.access_token = "test_token_123"
        self.manager = WizReportManager(self.api_url, self.access_token)
        self.project_id = "proj-123"
        self.report_id = "report-456"

    def test_init(self, mock_sleep):
        """Test WizReportManager initialization."""
        self.assertEqual(self.manager.api_url, self.api_url)
        self.assertEqual(self.manager.access_token, self.access_token)
        self.assertIn("Authorization", self.manager.headers)
        self.assertEqual(self.manager.headers["Authorization"], f"Bearer {self.access_token}")

    @patch("requests.post")
    def test_create_compliance_report_success(self, mock_post, mock_sleep):
        """Test successful compliance report creation."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": {"createReport": {"report": {"id": "report-789"}}}}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = self.manager.create_compliance_report(self.project_id)

        self.assertEqual(result, "report-789")
        mock_post.assert_called_once()

    @patch("requests.post")
    def test_create_compliance_report_with_run_starts_at(self, mock_post, mock_sleep):
        """Test compliance report creation with run_starts_at."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": {"createReport": {"report": {"id": "report-789"}}}}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        run_starts_at = "2024-01-01T00:00:00Z"
        result = self.manager.create_compliance_report(self.project_id, run_starts_at)

        self.assertEqual(result, "report-789")
        mock_post.assert_called_once()

    @patch("requests.post")
    def test_create_compliance_report_graphql_errors(self, mock_post, mock_sleep):
        """Test compliance report creation with GraphQL errors."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"errors": [{"message": "Project not found"}]}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = self.manager.create_compliance_report(self.project_id)

        self.assertIsNone(result)

    @patch("requests.post")
    def test_create_compliance_report_no_report_id(self, mock_post, mock_sleep):
        """Test compliance report creation when no report ID is returned."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": {"createReport": {"report": {}}}}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = self.manager.create_compliance_report(self.project_id)

        self.assertIsNone(result)

    @patch("requests.post")
    def test_create_compliance_report_request_exception(self, mock_post, mock_sleep):
        """Test compliance report creation with request exception."""
        mock_post.side_effect = requests.exceptions.RequestException("Network error")

        result = self.manager.create_compliance_report(self.project_id)

        self.assertIsNone(result)

    @patch("requests.post")
    def test_create_compliance_report_key_error(self, mock_post, mock_sleep):
        """Test compliance report creation with KeyError."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": {}}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = self.manager.create_compliance_report(self.project_id)

        self.assertIsNone(result)

    @patch("requests.post")
    def test_create_compliance_report_value_error(self, mock_post, mock_sleep):
        """Test compliance report creation with ValueError."""
        mock_response = MagicMock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = self.manager.create_compliance_report(self.project_id)

        self.assertIsNone(result)

    @patch("requests.post")
    def test_get_report_status_success(self, mock_post, mock_sleep):
        """Test successful report status retrieval."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "report": {
                    "id": "report-456",
                    "lastRun": {"status": "SUCCESS", "url": "https://download.url/report.csv"},
                }
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = self.manager.get_report_status(self.report_id)

        self.assertEqual(result["status"], "SUCCESS")
        self.assertEqual(result["url"], "https://download.url/report.csv")
        self.assertIn("report_data", result)

    @patch("requests.post")
    def test_get_report_status_graphql_errors(self, mock_post, mock_sleep):
        """Test report status retrieval with GraphQL errors."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"errors": [{"message": "Report not found"}]}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = self.manager.get_report_status(self.report_id)

        self.assertEqual(result, {})

    @patch("requests.post")
    def test_get_report_status_request_exception(self, mock_post, mock_sleep):
        """Test report status retrieval with request exception."""
        mock_post.side_effect = requests.exceptions.RequestException("Network error")

        result = self.manager.get_report_status(self.report_id)

        self.assertEqual(result, {})

    @patch("requests.post")
    def test_get_report_status_key_error(self, mock_post, mock_sleep):
        """Test report status retrieval with KeyError."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": {}}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = self.manager.get_report_status(self.report_id)

        self.assertEqual(result["status"], "UNKNOWN")
        self.assertEqual(result["url"], "")

    @patch("requests.post")
    def test_get_report_status_value_error(self, mock_post, mock_sleep):
        """Test report status retrieval with ValueError."""
        mock_response = MagicMock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = self.manager.get_report_status(self.report_id)

        self.assertEqual(result, {})

    @patch("regscale.integrations.commercial.wizv2.reports.WizReportManager.get_report_status")
    def test_wait_for_report_completion_success(self, mock_get_status, mock_sleep):
        """Test waiting for report completion - success case."""
        mock_get_status.return_value = {"status": "SUCCESS", "url": "https://download.url/report.csv"}

        result = self.manager.wait_for_report_completion(self.report_id)

        self.assertEqual(result, "https://download.url/report.csv")

    @patch("regscale.integrations.commercial.wizv2.reports.WizReportManager.get_report_status")
    def test_wait_for_report_completion_completed_status(self, mock_get_status, mock_sleep):
        """Test waiting for report completion - COMPLETED status."""
        mock_get_status.return_value = {"status": "COMPLETED", "url": "https://download.url/report.csv"}

        result = self.manager.wait_for_report_completion(self.report_id)

        self.assertEqual(result, "https://download.url/report.csv")

    @patch("regscale.integrations.commercial.wizv2.reports.WizReportManager.get_report_status")
    def test_wait_for_report_completion_no_url(self, mock_get_status, mock_sleep):
        """Test waiting for report completion - no download URL."""
        mock_get_status.return_value = {"status": "SUCCESS", "url": ""}

        result = self.manager.wait_for_report_completion(self.report_id)

        self.assertIsNone(result)

    @patch("regscale.integrations.commercial.wizv2.reports.WizReportManager.get_report_status")
    def test_wait_for_report_completion_failed(self, mock_get_status, mock_sleep):
        """Test waiting for report completion - FAILED status."""
        mock_get_status.return_value = {"status": "FAILED", "url": ""}

        result = self.manager.wait_for_report_completion(self.report_id)

        self.assertIsNone(result)

    @patch("regscale.integrations.commercial.wizv2.reports.WizReportManager.get_report_status")
    def test_wait_for_report_completion_cancelled(self, mock_get_status, mock_sleep):
        """Test waiting for report completion - CANCELLED status."""
        mock_get_status.return_value = {"status": "CANCELLED", "url": ""}

        result = self.manager.wait_for_report_completion(self.report_id)

        self.assertIsNone(result)

    @patch("regscale.integrations.commercial.wizv2.reports.WizReportManager.get_report_status")
    def test_wait_for_report_completion_timeout_status(self, mock_get_status, mock_sleep):
        """Test waiting for report completion - TIMEOUT status."""
        mock_get_status.return_value = {"status": "TIMEOUT", "url": ""}

        result = self.manager.wait_for_report_completion(self.report_id)

        self.assertIsNone(result)

    @patch("time.sleep")
    @patch("regscale.integrations.commercial.wizv2.reports.WizReportManager.get_report_status")
    def test_wait_for_report_completion_pending_then_success(self, mock_get_status, mock_sleep_method, mock_sleep):
        """Test waiting for report completion - PENDING then SUCCESS."""
        mock_get_status.side_effect = [
            {"status": "PENDING", "url": ""},
            {"status": "SUCCESS", "url": "https://download.url/report.csv"},
        ]

        result = self.manager.wait_for_report_completion(self.report_id)

        self.assertEqual(result, "https://download.url/report.csv")
        # Class-level mock takes precedence, so we don't check the method-level mock

    @patch("time.sleep")
    @patch("regscale.integrations.commercial.wizv2.reports.WizReportManager.get_report_status")
    def test_wait_for_report_completion_running_then_success(self, mock_get_status, mock_sleep_method, mock_sleep):
        """Test waiting for report completion - RUNNING then SUCCESS."""
        mock_get_status.side_effect = [
            {"status": "RUNNING", "url": ""},
            {"status": "SUCCESS", "url": "https://download.url/report.csv"},
        ]

        result = self.manager.wait_for_report_completion(self.report_id)

        self.assertEqual(result, "https://download.url/report.csv")
        # Class-level mock takes precedence, so we don't check the method-level mock

    @patch("time.sleep")
    @patch("regscale.integrations.commercial.wizv2.reports.WizReportManager.get_report_status")
    def test_wait_for_report_completion_in_progress_then_success(self, mock_get_status, mock_sleep_method, mock_sleep):
        """Test waiting for report completion - IN_PROGRESS then SUCCESS."""
        mock_get_status.side_effect = [
            {"status": "IN_PROGRESS", "url": ""},
            {"status": "SUCCESS", "url": "https://download.url/report.csv"},
        ]

        result = self.manager.wait_for_report_completion(self.report_id)

        self.assertEqual(result, "https://download.url/report.csv")
        # Class-level mock takes precedence, so we don't check the method-level mock

    @patch("time.sleep")
    @patch("regscale.integrations.commercial.wizv2.reports.WizReportManager.get_report_status")
    def test_wait_for_report_completion_unknown_then_success(self, mock_get_status, mock_sleep_method, mock_sleep):
        """Test waiting for report completion - UNKNOWN then SUCCESS."""
        mock_get_status.side_effect = [
            {"status": "UNKNOWN", "url": ""},
            {"status": "SUCCESS", "url": "https://download.url/report.csv"},
        ]

        result = self.manager.wait_for_report_completion(self.report_id)

        self.assertEqual(result, "https://download.url/report.csv")
        # Class-level mock takes precedence, so we don't check the method-level mock

    @patch("time.sleep")
    @patch("regscale.integrations.commercial.wizv2.reports.WizReportManager.get_report_status")
    def test_wait_for_report_completion_weird_status(self, mock_get_status, mock_sleep_method, mock_sleep):
        """Test waiting for report completion - unrecognized status then SUCCESS."""
        mock_get_status.side_effect = [
            {"status": "WEIRD_STATUS", "url": ""},
            {"status": "SUCCESS", "url": "https://download.url/report.csv"},
        ]

        result = self.manager.wait_for_report_completion(self.report_id)

        self.assertEqual(result, "https://download.url/report.csv")
        # Class-level mock takes precedence, so we don't check the method-level mock

    @patch("time.sleep")
    @patch("regscale.integrations.commercial.wizv2.reports.WizReportManager.get_report_status")
    @patch("regscale.integrations.commercial.wizv2.reports.MAX_RETRIES", 3)
    def test_wait_for_report_completion_max_retries(self, mock_get_status, mock_sleep_method, mock_sleep):
        """Test waiting for report completion - max retries exceeded."""
        mock_get_status.return_value = {"status": "PENDING", "url": ""}

        result = self.manager.wait_for_report_completion(self.report_id)

        self.assertIsNone(result)
        self.assertEqual(mock_get_status.call_count, 3)

    @patch("builtins.open", new_callable=mock_open)
    @patch("requests.get")
    def test_download_report_success(self, mock_get, mock_file, mock_sleep):
        """Test successful report download."""
        mock_response = MagicMock()
        mock_response.content = b"report,data\n1,2\n"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = self.manager.download_report("https://download.url/report.csv", "/tmp/report.csv")

        self.assertTrue(result)
        mock_get.assert_called_once_with("https://download.url/report.csv", timeout=300)
        mock_file.assert_called_once_with("/tmp/report.csv", "wb")

    @patch("requests.get")
    def test_download_report_request_exception(self, mock_get, mock_sleep):
        """Test report download with request exception."""
        mock_get.side_effect = requests.exceptions.RequestException("Network error")

        result = self.manager.download_report("https://download.url/report.csv", "/tmp/report.csv")

        self.assertFalse(result)

    @patch("builtins.open", new_callable=mock_open)
    @patch("requests.get")
    def test_download_report_io_error(self, mock_get, mock_file, mock_sleep):
        """Test report download with IO error."""
        mock_response = MagicMock()
        mock_response.content = b"report,data\n1,2\n"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        mock_file.side_effect = IOError("Permission denied")

        result = self.manager.download_report("https://download.url/report.csv", "/tmp/report.csv")

        self.assertFalse(result)

    @patch("regscale.integrations.commercial.wizv2.reports.WizReportManager.wait_for_report_completion")
    @patch("requests.post")
    def test_rerun_report_success(self, mock_post, mock_wait, mock_sleep):
        """Test successful report rerun."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": {"rerunReport": {"success": True}}}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        mock_wait.return_value = "https://download.url/report.csv"

        result = self.manager.rerun_report(self.report_id)

        self.assertEqual(result, "https://download.url/report.csv")
        mock_post.assert_called_once()
        mock_wait.assert_called_once_with(self.report_id)

    @patch("requests.post")
    def test_rerun_report_graphql_errors(self, mock_post, mock_sleep):
        """Test report rerun with GraphQL errors."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"errors": [{"message": "Report not found"}]}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = self.manager.rerun_report(self.report_id)

        self.assertIsNone(result)

    @patch("requests.post")
    def test_rerun_report_request_exception(self, mock_post, mock_sleep):
        """Test report rerun with request exception."""
        mock_post.side_effect = requests.exceptions.RequestException("Network error")

        result = self.manager.rerun_report(self.report_id)

        self.assertIsNone(result)

    @patch("regscale.integrations.commercial.wizv2.reports.WizReportManager.wait_for_report_completion")
    @patch("requests.post")
    def test_rerun_report_key_error(self, mock_post, mock_wait, mock_sleep):
        """Test report rerun with KeyError."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": {}}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        mock_wait.return_value = "https://download.url/report.csv"

        result = self.manager.rerun_report(self.report_id)

        # Should still try to wait for completion
        self.assertIsNotNone(result)

    @patch("requests.post")
    def test_rerun_report_value_error(self, mock_post, mock_sleep):
        """Test report rerun with ValueError."""
        mock_response = MagicMock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = self.manager.rerun_report(self.report_id)

        self.assertIsNone(result)

    @patch("requests.post")
    def test_list_reports_success(self, mock_post, mock_sleep):
        """Test successful report listing."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "reports": {"nodes": [{"id": "report-1", "name": "Report 1"}, {"id": "report-2", "name": "Report 2"}]}
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = self.manager.list_reports()

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["id"], "report-1")
        self.assertEqual(result[1]["id"], "report-2")

    @patch("requests.post")
    def test_list_reports_with_filter(self, mock_post, mock_sleep):
        """Test report listing with filter."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": {"reports": {"nodes": [{"id": "report-1", "name": "Report 1"}]}}}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        filter_by = {"name": {"equals": "Report 1"}}
        result = self.manager.list_reports(filter_by)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "report-1")

    @patch("requests.post")
    def test_list_reports_graphql_errors(self, mock_post, mock_sleep):
        """Test report listing with GraphQL errors."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"errors": [{"message": "Unauthorized"}]}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = self.manager.list_reports()

        self.assertEqual(result, [])

    @patch("requests.post")
    def test_list_reports_request_exception(self, mock_post, mock_sleep):
        """Test report listing with request exception."""
        mock_post.side_effect = requests.exceptions.RequestException("Network error")

        result = self.manager.list_reports()

        self.assertEqual(result, [])

    @patch("requests.post")
    def test_list_reports_key_error(self, mock_post, mock_sleep):
        """Test report listing with KeyError."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": {}}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = self.manager.list_reports()

        self.assertEqual(result, [])

    @patch("requests.post")
    def test_list_reports_value_error(self, mock_post, mock_sleep):
        """Test report listing with ValueError."""
        mock_response = MagicMock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = self.manager.list_reports()

        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
