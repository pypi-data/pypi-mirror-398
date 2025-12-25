#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for Wiz V2 utility functions."""

import logging
import unittest
from unittest.mock import patch, MagicMock

from regscale.integrations.commercial.wizv2.utils import get_report_url_and_status, get_or_create_report_id

logger = logging.getLogger("regscale")


class TestWizUtils(unittest.TestCase):
    """Test cases for Wiz utility functions."""

    @patch("regscale.integrations.commercial.wizv2.utils.main.time.sleep")
    @patch("regscale.integrations.commercial.wizv2.utils.main.download_report")
    @patch("regscale.integrations.commercial.wizv2.utils.main.rerun_expired_report")
    @patch("regscale.integrations.commercial.wizv2.utils.main.CHECK_INTERVAL_FOR_DOWNLOAD_REPORT", 0.001)
    @patch("regscale.integrations.commercial.wizv2.utils.main.MAX_RETRIES", 3)
    def test_get_report_url_and_status_completed(self, mock_rerun_report, mock_download_report, mock_sleep):
        """Test get_report_url_and_status with COMPLETED status."""
        # Mock response for completed report
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "data": {"report": {"lastRun": {"status": "COMPLETED", "url": "https://example.com/report.csv"}}}
        }
        mock_download_report.return_value = mock_response

        # Call the function
        result = get_report_url_and_status("test-report-id")

        # Verify the result
        self.assertEqual(result, "https://example.com/report.csv")
        mock_download_report.assert_called_once_with({"reportId": "test-report-id"})
        mock_rerun_report.assert_not_called()
        mock_sleep.assert_not_called()  # Should not sleep on first success

    @patch("regscale.integrations.commercial.wizv2.utils.main.time.sleep")
    @patch("regscale.integrations.commercial.wizv2.utils.main.download_report")
    @patch("regscale.integrations.commercial.wizv2.utils.main.rerun_expired_report")
    @patch("regscale.integrations.commercial.wizv2.utils.main.get_report_url_and_status")
    @patch("regscale.integrations.commercial.wizv2.utils.main.CHECK_INTERVAL_FOR_DOWNLOAD_REPORT", 0.001)
    @patch("regscale.integrations.commercial.wizv2.utils.main.MAX_RETRIES", 3)
    def test_get_report_url_and_status_expired(
        self, mock_recursive_call, mock_rerun_report, mock_download_report, mock_sleep
    ):
        """Test get_report_url_and_status with EXPIRED status."""
        # Mock response for expired report
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {"data": {"report": {"lastRun": {"status": "EXPIRED"}}}}
        mock_download_report.return_value = mock_response

        # Mock rerun response
        mock_rerun_response = MagicMock()
        mock_rerun_response.ok = True
        mock_rerun_report.return_value = mock_rerun_response

        # Mock recursive call to return final URL
        mock_recursive_call.return_value = "https://example.com/new-report.csv"

        # Call the function
        result = get_report_url_and_status("test-report-id")

        # Verify the result
        self.assertEqual(result, "https://example.com/new-report.csv")
        mock_download_report.assert_called_once_with({"reportId": "test-report-id"})
        mock_rerun_report.assert_called_once_with({"reportId": "test-report-id"})
        mock_recursive_call.assert_called_once_with("test-report-id")
        mock_sleep.assert_not_called()  # Should not sleep on first call before recursion

    @patch("regscale.integrations.commercial.wizv2.utils.main.time.sleep")
    @patch("regscale.integrations.commercial.wizv2.utils.main.download_report")
    @patch("regscale.integrations.commercial.wizv2.utils.main.rerun_expired_report")
    @patch("regscale.integrations.commercial.wizv2.utils.main.CHECK_INTERVAL_FOR_DOWNLOAD_REPORT", 0.001)
    @patch("regscale.integrations.commercial.wizv2.utils.main.MAX_RETRIES", 5)
    def test_get_report_url_and_status_rate_limit(self, mock_rerun_report, mock_download_report, mock_sleep):
        """Test get_report_url_and_status with rate limit error."""
        from regscale.integrations.commercial.wizv2.core.constants import RATE_LIMIT_MSG

        # Mock response with rate limit error
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "errors": [
                {"message": "Rate limit exceeded", "extensions": {"retryAfter": 0.001}}  # Reduced to milliseconds
            ]
        }
        mock_download_report.return_value = mock_response

        # Mock second response for successful completion
        mock_response2 = MagicMock()
        mock_response2.ok = True
        mock_response2.json.return_value = {
            "data": {"report": {"lastRun": {"status": "COMPLETED", "url": "https://example.com/report.csv"}}}
        }

        # Configure mock to return different responses on subsequent calls
        mock_download_report.side_effect = [mock_response, mock_response2]

        # Call the function
        result = get_report_url_and_status("test-report-id")

        # Verify the result
        self.assertEqual(result, "https://example.com/report.csv")
        self.assertEqual(mock_download_report.call_count, 2)
        mock_rerun_report.assert_not_called()
        # Sleep is called twice: once for rate limit, once for retry interval
        self.assertEqual(mock_sleep.call_count, 2)

    @patch("regscale.integrations.commercial.wizv2.utils.main.time.sleep")
    @patch("regscale.integrations.commercial.wizv2.utils.main.download_report")
    @patch("regscale.integrations.commercial.wizv2.utils.main.rerun_expired_report")
    @patch("regscale.integrations.commercial.wizv2.utils.main.CHECK_INTERVAL_FOR_DOWNLOAD_REPORT", 0.001)
    @patch("regscale.integrations.commercial.wizv2.utils.main.MAX_RETRIES", 3)
    def test_get_report_url_and_status_failed_response(self, mock_rerun_report, mock_download_report, mock_sleep):
        """Test get_report_url_and_status with failed response."""
        # Mock failed response
        mock_response = MagicMock()
        mock_response.ok = False
        mock_download_report.return_value = mock_response

        # Call the function and expect exception
        with self.assertRaises(Exception) as context:
            get_report_url_and_status("test-report-id")

        self.assertIn("Failed to download report", str(context.exception))
        mock_download_report.assert_called_once_with({"reportId": "test-report-id"})
        mock_rerun_report.assert_not_called()

    @patch("regscale.integrations.commercial.wizv2.utils.main.time.sleep")
    @patch("regscale.integrations.commercial.wizv2.utils.main.download_report")
    @patch("regscale.integrations.commercial.wizv2.utils.main.rerun_expired_report")
    @patch("regscale.integrations.commercial.wizv2.utils.main.CHECK_INTERVAL_FOR_DOWNLOAD_REPORT", 0.001)
    @patch("regscale.integrations.commercial.wizv2.utils.main.MAX_RETRIES", 3)
    def test_get_report_url_and_status_none_response(self, mock_rerun_report, mock_download_report, mock_sleep):
        """Test get_report_url_and_status with None response."""
        # Mock None response
        mock_download_report.return_value = None

        # Call the function and expect exception
        with self.assertRaises(Exception) as context:
            get_report_url_and_status("test-report-id")

        self.assertIn("Failed to download report", str(context.exception))
        mock_download_report.assert_called_once_with({"reportId": "test-report-id"})
        mock_rerun_report.assert_not_called()

    @patch("regscale.integrations.commercial.wizv2.utils.main.time.sleep")
    @patch("regscale.integrations.commercial.wizv2.utils.main.download_report")
    @patch("regscale.integrations.commercial.wizv2.utils.main.rerun_expired_report")
    @patch("regscale.integrations.commercial.wizv2.utils.main.CHECK_INTERVAL_FOR_DOWNLOAD_REPORT", 0.001)
    @patch("regscale.integrations.commercial.wizv2.utils.main.MAX_RETRIES", 3)  # Reduce retries for faster testing
    def test_get_report_url_and_status_other_error(self, mock_rerun_report, mock_download_report, mock_sleep):
        """Test get_report_url_and_status with other error in response."""
        # Mock response with other error
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {"errors": [{"message": "Some other error occurred"}]}
        mock_download_report.return_value = mock_response

        # Call the function and expect exception after max retries
        with self.assertRaises(Exception) as context:
            get_report_url_and_status("test-report-id")

        self.assertIn("Download failed, exceeding the maximum number of retries", str(context.exception))
        # Should be called MAX_RETRIES times (now 3)
        self.assertEqual(mock_download_report.call_count, 3)
        mock_rerun_report.assert_not_called()

    @patch("regscale.integrations.commercial.wizv2.utils.main.time.sleep")
    @patch("regscale.integrations.commercial.wizv2.utils.main.download_report")
    @patch("regscale.integrations.commercial.wizv2.utils.main.rerun_expired_report")
    @patch("regscale.integrations.commercial.wizv2.utils.main.CHECK_INTERVAL_FOR_DOWNLOAD_REPORT", 0.001)
    @patch("regscale.integrations.commercial.wizv2.utils.main.MAX_RETRIES", 3)  # Reduce retries for faster testing
    def test_get_report_url_and_status_unknown_status(self, mock_rerun_report, mock_download_report, mock_sleep):
        """Test get_report_url_and_status with unknown status."""
        # Mock response with unknown status
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {"data": {"report": {"lastRun": {"status": "UNKNOWN_STATUS"}}}}
        mock_download_report.return_value = mock_response

        # Call the function and expect exception after max retries
        with self.assertRaises(Exception) as context:
            get_report_url_and_status("test-report-id")

        self.assertIn("Download failed, exceeding the maximum number of retries", str(context.exception))
        # Should be called MAX_RETRIES times (now 3)
        self.assertEqual(mock_download_report.call_count, 3)
        mock_rerun_report.assert_not_called()

    @patch("regscale.integrations.commercial.wizv2.utils.main.time.sleep")
    @patch("regscale.integrations.commercial.wizv2.utils.main.download_report")
    @patch("regscale.integrations.commercial.wizv2.utils.main.rerun_expired_report")
    @patch("regscale.integrations.commercial.wizv2.utils.main.CHECK_INTERVAL_FOR_DOWNLOAD_REPORT", 0.001)
    @patch("regscale.integrations.commercial.wizv2.utils.main.MAX_RETRIES", 3)  # Reduce retries for faster testing
    def test_get_report_url_and_status_missing_status(self, mock_rerun_report, mock_download_report, mock_sleep):
        """Test get_report_url_and_status with missing status in response."""
        # Mock response with missing status
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {"data": {"report": {"lastRun": {}}}}
        mock_download_report.return_value = mock_response

        # Call the function and expect exception after max retries
        with self.assertRaises(Exception) as context:
            get_report_url_and_status("test-report-id")

        self.assertIn("Download failed, exceeding the maximum number of retries", str(context.exception))
        # Should be called MAX_RETRIES times (now 3)
        self.assertEqual(mock_download_report.call_count, 3)
        mock_rerun_report.assert_not_called()

    @patch("regscale.integrations.commercial.wizv2.utils.main.time.sleep")
    @patch("regscale.integrations.commercial.wizv2.utils.main.download_report")
    @patch("regscale.integrations.commercial.wizv2.utils.main.rerun_expired_report")
    @patch("regscale.integrations.commercial.wizv2.utils.main.CHECK_INTERVAL_FOR_DOWNLOAD_REPORT", 0.001)
    @patch("regscale.integrations.commercial.wizv2.utils.main.MAX_RETRIES", 3)
    def test_get_report_url_and_status_multiple_attempts_before_completion(
        self, mock_rerun_report, mock_download_report, mock_sleep
    ):
        """Test get_report_url_and_status with multiple attempts before completion."""
        # Mock responses: first two with unknown status, third with completed
        mock_response1 = MagicMock()
        mock_response1.ok = True
        mock_response1.json.return_value = {"data": {"report": {"lastRun": {"status": "PROCESSING"}}}}

        mock_response2 = MagicMock()
        mock_response2.ok = True
        mock_response2.json.return_value = {"data": {"report": {"lastRun": {"status": "PROCESSING"}}}}

        mock_response3 = MagicMock()
        mock_response3.ok = True
        mock_response3.json.return_value = {
            "data": {"report": {"lastRun": {"status": "COMPLETED", "url": "https://example.com/report.csv"}}}
        }

        # Configure mock to return different responses on subsequent calls
        mock_download_report.side_effect = [mock_response1, mock_response2, mock_response3]

        # Call the function
        result = get_report_url_and_status("test-report-id")

        # Verify the result
        self.assertEqual(result, "https://example.com/report.csv")
        self.assertEqual(mock_download_report.call_count, 3)
        # Should sleep twice (after first and second attempts)
        self.assertEqual(mock_sleep.call_count, 2)
        mock_rerun_report.assert_not_called()


class TestGetOrCreateReportId(unittest.TestCase):
    """Test cases for get_or_create_report_id function."""

    def setUp(self):
        """Set up test fixtures."""
        self.project_id = "test-project-123"
        self.frameworks = ["NIST_SP_800-53_Revision_5", "NIST_CSF_v1.1"]
        self.wiz_frameworks = [
            {"id": "framework-1", "name": "NIST SP 800-53 Revision 5"},
            {"id": "framework-2", "name": "NIST CSF v1.1"},
        ]
        self.target_framework = "NIST_SP_800-53_Revision_5"

    @patch("regscale.integrations.commercial.wizv2.utils.main.Application")
    @patch("regscale.integrations.commercial.wizv2.utils.main.is_report_expired")
    def test_get_or_create_report_id_existing_valid_report(self, mock_is_expired, mock_application):
        """Test returning existing report ID when report is valid (not expired)."""
        # Mock Application
        mock_app = MagicMock()
        mock_app.config.get.return_value = 15
        mock_application.return_value = mock_app

        # Mock is_report_expired to return False (not expired)
        mock_is_expired.return_value = False

        # Mock existing reports with a valid report
        existing_reports = [
            {
                "id": "existing-report-123",
                "name": "NIST_SP_800-53_Revision_5_project_test-project-123",
                "lastRun": {"runAt": "2023-07-15T14:37:55.450532Z"},
            }
        ]

        result = get_or_create_report_id(
            self.project_id, self.frameworks, self.wiz_frameworks, existing_reports, self.target_framework
        )

        self.assertEqual(result, "existing-report-123")
        mock_app.config.get.assert_called_once_with("wizReportAge", 15)
        mock_is_expired.assert_called_once_with("2023-07-15T14:37:55.450532Z", 15)

    @patch("regscale.integrations.commercial.wizv2.utils.main.Application")
    @patch("regscale.integrations.commercial.wizv2.utils.main.is_report_expired")
    @patch("regscale.integrations.commercial.wizv2.utils.main.create_compliance_report")
    def test_get_or_create_report_id_existing_expired_report(
        self, mock_create_report, mock_is_expired, mock_application
    ):
        """Test creating new report when existing report is expired."""
        # Mock Application
        mock_app = MagicMock()
        mock_app.config.get.return_value = 15
        mock_application.return_value = mock_app

        # Mock is_report_expired to return True (expired)
        mock_is_expired.return_value = True

        # Mock create_compliance_report to return new report ID
        mock_create_report.return_value = "new-report-456"

        # Mock existing reports with an expired report
        existing_reports = [
            {
                "id": "existing-report-123",
                "name": "NIST_SP_800-53_Revision_5_project_test-project-123",
                "lastRun": {"runAt": "2023-06-01T14:37:55.450532Z"},  # Old date
            }
        ]

        result = get_or_create_report_id(
            self.project_id, self.frameworks, self.wiz_frameworks, existing_reports, self.target_framework
        )

        self.assertEqual(result, "new-report-456")
        mock_app.config.get.assert_called_once_with("wizReportAge", 15)
        mock_is_expired.assert_called_once_with("2023-06-01T14:37:55.450532Z", 15)
        mock_create_report.assert_called_once_with(
            wiz_project_id=self.project_id,
            report_name="NIST_SP_800-53_Revision_5_project_test-project-123",
            framework_id="framework-1",
        )

    @patch("regscale.integrations.commercial.wizv2.utils.main.Application")
    @patch("regscale.integrations.commercial.wizv2.utils.main.create_compliance_report")
    def test_get_or_create_report_id_no_existing_report(self, mock_create_report, mock_application):
        """Test creating new report when no existing report is found."""
        # Mock Application
        mock_app = MagicMock()
        mock_app.config.get.return_value = 15
        mock_application.return_value = mock_app

        # Mock create_compliance_report to return new report ID
        mock_create_report.return_value = "new-report-789"

        # Empty existing reports list
        existing_reports = []

        result = get_or_create_report_id(
            self.project_id, self.frameworks, self.wiz_frameworks, existing_reports, self.target_framework
        )

        self.assertEqual(result, "new-report-789")
        mock_app.config.get.assert_called_once_with("wizReportAge", 15)
        mock_create_report.assert_called_once_with(
            wiz_project_id=self.project_id,
            report_name="NIST_SP_800-53_Revision_5_project_test-project-123",
            framework_id="framework-1",
        )

    @patch("regscale.integrations.commercial.wizv2.utils.main.Application")
    @patch("regscale.integrations.commercial.wizv2.utils.main.is_report_expired")
    def test_get_or_create_report_id_missing_run_at(self, mock_is_expired, mock_application):
        """Test behavior when existing report has no runAt timestamp."""
        # Mock Application
        mock_app = MagicMock()
        mock_app.config.get.return_value = 15
        mock_application.return_value = mock_app

        # Mock existing reports with missing runAt
        existing_reports = [
            {
                "id": "existing-report-123",
                "name": "NIST_SP_800-53_Revision_5_project_test-project-123",
                "lastRun": {},  # No runAt timestamp
            }
        ]

        result = get_or_create_report_id(
            self.project_id, self.frameworks, self.wiz_frameworks, existing_reports, self.target_framework
        )

        # When runAt is missing, the method returns the existing report
        # because the condition `if run_at and is_report_expired(run_at, report_age_days):`
        # is False when run_at is None/missing
        self.assertEqual(result, "existing-report-123")
        mock_app.config.get.assert_called_once_with("wizReportAge", 15)
        # is_report_expired should not be called when runAt is missing
        mock_is_expired.assert_not_called()

    @patch("regscale.integrations.commercial.wizv2.utils.main.Application")
    def test_get_or_create_report_id_framework_not_found(self, mock_application):
        """Test ValueError when target framework is not in frameworks list."""
        # Mock Application
        mock_app = MagicMock()
        mock_app.config.get.return_value = 15
        mock_application.return_value = mock_app

        # Use a framework not in the frameworks list
        invalid_framework = "INVALID_FRAMEWORK"

        existing_reports = []

        with self.assertRaises(ValueError) as context:
            get_or_create_report_id(
                self.project_id, self.frameworks, self.wiz_frameworks, existing_reports, invalid_framework
            )

        # The actual error message from list.index() is different
        self.assertIn("is not in list", str(context.exception))

    @patch("regscale.integrations.commercial.wizv2.utils.main.Application")
    @patch("regscale.integrations.commercial.wizv2.utils.main.is_report_expired")
    def test_get_or_create_report_id_custom_report_age(self, mock_is_expired, mock_application):
        """Test using custom wizReportAge configuration."""
        # Mock Application with custom age
        mock_app = MagicMock()
        mock_app.config.get.return_value = 30  # 30 days instead of default 15
        mock_application.return_value = mock_app

        # Mock is_report_expired to return False
        mock_is_expired.return_value = False

        # Mock existing reports with a valid report
        existing_reports = [
            {
                "id": "existing-report-123",
                "name": "NIST_SP_800-53_Revision_5_project_test-project-123",
                "lastRun": {"runAt": "2023-07-15T14:37:55.450532Z"},
            }
        ]

        result = get_or_create_report_id(
            self.project_id, self.frameworks, self.wiz_frameworks, existing_reports, self.target_framework
        )

        self.assertEqual(result, "existing-report-123")
        mock_app.config.get.assert_called_once_with("wizReportAge", 15)
        mock_is_expired.assert_called_once_with("2023-07-15T14:37:55.450532Z", 30)

    @patch("regscale.integrations.commercial.wizv2.utils.main.Application")
    @patch("regscale.integrations.commercial.wizv2.utils.main.is_report_expired")
    @patch("regscale.integrations.commercial.wizv2.utils.main.create_compliance_report")
    def test_get_or_create_report_id_multiple_reports_first_match(
        self, mock_create_report, mock_is_expired, mock_application
    ):
        """Test behavior when multiple reports exist, should use first matching report."""
        # Mock Application
        mock_app = MagicMock()
        mock_app.config.get.return_value = 15
        mock_application.return_value = mock_app

        # Mock is_report_expired to return False for first call
        mock_is_expired.return_value = False

        # Mock existing reports with multiple matching reports
        existing_reports = [
            {
                "id": "first-report-123",
                "name": "NIST_SP_800-53_Revision_5_project_test-project-123",
                "lastRun": {"runAt": "2023-07-15T14:37:55.450532Z"},
            },
            {
                "id": "second-report-456",
                "name": "NIST_SP_800-53_Revision_5_project_test-project-123",
                "lastRun": {"runAt": "2023-07-16T14:37:55.450532Z"},
            },
        ]

        result = get_or_create_report_id(
            self.project_id, self.frameworks, self.wiz_frameworks, existing_reports, self.target_framework
        )

        # Should return the first matching report
        self.assertEqual(result, "first-report-123")
        mock_is_expired.assert_called_once_with("2023-07-15T14:37:55.450532Z", 15)
        mock_create_report.assert_not_called()

    @patch("regscale.integrations.commercial.wizv2.utils.main.Application")
    @patch("regscale.integrations.commercial.wizv2.utils.main.is_report_expired")
    @patch("regscale.integrations.commercial.wizv2.utils.main.create_compliance_report")
    def test_get_or_create_report_id_different_report_names(
        self, mock_create_report, mock_is_expired, mock_application
    ):
        """Test creating new report when existing reports have different names."""
        # Mock Application
        mock_app = MagicMock()
        mock_app.config.get.return_value = 15
        mock_application.return_value = mock_app

        # Mock create_compliance_report to return new report ID
        mock_create_report.return_value = "new-report-999"

        # Mock existing reports with different names
        existing_reports = [
            {
                "id": "other-report-123",
                "name": "OTHER_FRAMEWORK_project_test-project-123",
                "lastRun": {"runAt": "2023-07-15T14:37:55.450532Z"},
            }
        ]

        result = get_or_create_report_id(
            self.project_id, self.frameworks, self.wiz_frameworks, existing_reports, self.target_framework
        )

        self.assertEqual(result, "new-report-999")
        mock_app.config.get.assert_called_once_with("wizReportAge", 15)
        # is_report_expired should not be called since no matching report name
        mock_is_expired.assert_not_called()
        mock_create_report.assert_called_once()


if __name__ == "__main__":
    unittest.main()
