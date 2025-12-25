#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Comprehensive unit tests for Wiz V2 utility functions in utils/main.py"""

import csv
import codecs
import datetime
import json
import logging
import time
import unittest
from io import StringIO
from typing import Dict, List
from unittest.mock import MagicMock, Mock, patch, mock_open, call
from zipfile import ZipFile

import pytest
import requests
from pydantic import ValidationError

from regscale.core.app.utils.app_utils import error_and_exit
from regscale.integrations.commercial.wizv2.utils.main import (
    is_report_expired,
    get_notes_from_wiz_props,
    handle_management_type,
    create_asset_type,
    map_category,
    convert_first_seen_to_days,
    fetch_report_by_id,
    download_file,
    fetch_sbom_report,
    fetch_report_id,
    get_framework_names,
    check_reports_for_frameworks,
    create_report_if_needed,
    fetch_and_process_report_data,
    get_or_create_report_id,
    fetch_report_data,
    process_single_report,
    fetch_framework_report,
    fetch_frameworks,
    query_reports,
    send_request,
    create_compliance_report,
    get_report_url_and_status,
    download_report,
    rerun_expired_report,
    check_compliance,
    create_assessment_from_compliance_report,
    create_report_assessment,
    update_implementation_status,
    get_wiz_compliance_settings,
    report_result_to_implementation_status,
    create_vulnerabilities_from_wiz_findings,
    create_single_vulnerability_from_wiz_data,
    _get_category_from_cpe,
    _get_category_from_hardware_types,
    _get_category_from_asset_type,
    _handle_report_response,
    _handle_rate_limit_error,
    _add_controls_to_controls_to_report_dict,
    _clean_passing_list,
    _create_aggregated_assessment_report,
    _try_get_status_from_settings,
    _match_label_to_result,
    _get_default_status_mapping,
)
from regscale.models import regscale_models
from regscale.models.integration_models.wizv2 import ComplianceReport, ComplianceCheckStatus

logger = logging.getLogger("regscale")
PATH = "regscale.integrations.commercial.wizv2.utils.main"


# ==================== Date and Reporting Tests ====================
class TestDateAndReporting(unittest.TestCase):
    """Test date handling and report validation functions"""

    def test_is_report_expired_not_expired(self):
        """Test report that is not expired"""
        # Report from 5 days ago
        five_days_ago = (datetime.datetime.now() - datetime.timedelta(days=5)).isoformat()
        result = is_report_expired(five_days_ago, max_age_days=10)
        self.assertFalse(result)

    def test_is_report_expired_expired(self):
        """Test report that is expired"""
        # Report from 20 days ago
        twenty_days_ago = (datetime.datetime.now() - datetime.timedelta(days=20)).isoformat()
        result = is_report_expired(twenty_days_ago, max_age_days=15)
        self.assertTrue(result)

    def test_is_report_expired_exact_boundary(self):
        """Test report at exact boundary (should be expired)"""
        # Report from exactly 15 days ago
        fifteen_days_ago = (datetime.datetime.now() - datetime.timedelta(days=15)).isoformat()
        result = is_report_expired(fifteen_days_ago, max_age_days=15)
        self.assertTrue(result)

    def test_is_report_expired_invalid_date(self):
        """Test with invalid date format"""
        result = is_report_expired("invalid-date", max_age_days=15)
        self.assertTrue(result)

    def test_is_report_expired_none_date(self):
        """Test with None date"""
        result = is_report_expired(None, max_age_days=15)
        self.assertTrue(result)

    def test_is_report_expired_empty_string(self):
        """Test with empty string"""
        result = is_report_expired("", max_age_days=15)
        self.assertTrue(result)

    def test_convert_first_seen_to_days_valid_date(self):
        """Test converting a valid first seen date to days"""
        # Date from 10 days ago
        ten_days_ago = (datetime.datetime.now() - datetime.timedelta(days=10)).isoformat()
        result = convert_first_seen_to_days(ten_days_ago)
        self.assertEqual(result, 10)

    def test_convert_first_seen_to_days_today(self):
        """Test converting today's date to days"""
        today = datetime.datetime.now().isoformat()
        result = convert_first_seen_to_days(today)
        self.assertEqual(result, 0)

    def test_convert_first_seen_to_days_invalid_date(self):
        """Test with invalid date format"""
        result = convert_first_seen_to_days("invalid-date")
        self.assertEqual(result, 0)

    def test_convert_first_seen_to_days_none(self):
        """Test with None"""
        result = convert_first_seen_to_days(None)
        self.assertEqual(result, 0)


# ==================== Property and Entity Tests ====================
class TestPropertiesAndEntities(unittest.TestCase):
    """Test property extraction and entity handling functions"""

    def test_get_notes_from_wiz_props_all_properties(self):
        """Test getting notes with all properties present"""
        wiz_properties = {
            "cloudPlatform": "AWS",
            "providerUniqueId": "i-1234567890",
            "cloudProviderURL": "https://console.aws.amazon.com/ec2/v2/home",
            "_vertexID": "vertex-123",
            "severity_name": "High",
            "severity_description": "Critical vulnerability detected",
        }
        external_id = "ext-123"

        result = get_notes_from_wiz_props(wiz_properties, external_id)

        self.assertIn("External ID: ext-123", result)
        self.assertIn("Cloud Platform: AWS", result)
        self.assertIn("Provider Unique ID: i-1234567890", result)
        self.assertIn("cloudProviderURL:", result)
        self.assertIn('target="_blank"', result)
        self.assertIn("Vertex ID: vertex-123", result)
        self.assertIn("Severity Name: High", result)
        self.assertIn("Severity Description: Critical vulnerability detected", result)
        self.assertIn("<br>", result)

    def test_get_notes_from_wiz_props_minimal_properties(self):
        """Test getting notes with minimal properties"""
        wiz_properties = {}
        external_id = "ext-456"

        result = get_notes_from_wiz_props(wiz_properties, external_id)

        self.assertIn("External ID: ext-456", result)
        self.assertNotIn("Cloud Platform:", result)
        self.assertNotIn("Provider Unique ID:", result)

    def test_get_notes_from_wiz_props_with_url(self):
        """Test URL formatting in notes"""
        wiz_properties = {"cloudProviderURL": "https://example.com/resource"}
        external_id = "ext-789"

        result = get_notes_from_wiz_props(wiz_properties, external_id)

        self.assertIn('<a href="https://example.com/resource" target="_blank">', result)

    def test_handle_management_type_managed(self):
        """Test management type for managed resources"""
        wiz_properties = {"isManaged": True}
        result = handle_management_type(wiz_properties)
        self.assertEqual(result, "External/Third Party Managed")

    def test_handle_management_type_internally_managed(self):
        """Test management type for internally managed resources"""
        wiz_properties = {"isManaged": False}
        result = handle_management_type(wiz_properties)
        self.assertEqual(result, "Internally Managed")

    def test_handle_management_type_missing_key(self):
        """Test management type when isManaged key is missing"""
        wiz_properties = {}
        result = handle_management_type(wiz_properties)
        self.assertEqual(result, "Internally Managed")


# ==================== Asset Category Mapping Tests ====================
class TestAssetCategoryMapping(unittest.TestCase):
    """Test asset category mapping functions"""

    @patch(f"{PATH}._get_category_from_cpe")
    def test_map_category_from_cpe(self, mock_cpe):
        """Test mapping category from CPE"""
        mock_cpe.return_value = regscale_models.AssetCategory.Hardware
        node = {"type": "VM", "graphEntity": {}}

        result = map_category(node)

        self.assertEqual(result, regscale_models.AssetCategory.Hardware)
        mock_cpe.assert_called_once()

    @patch(f"{PATH}._get_category_from_cpe")
    @patch(f"{PATH}._get_category_from_hardware_types")
    def test_map_category_from_hardware_types(self, mock_hardware, mock_cpe):
        """Test mapping category from hardware types"""
        mock_cpe.return_value = None
        mock_hardware.return_value = regscale_models.AssetCategory.Hardware

        node = {"type": "VM", "graphEntity": {}}

        result = map_category(node)

        self.assertEqual(result, regscale_models.AssetCategory.Hardware)
        mock_hardware.assert_called_once()

    @patch(f"{PATH}._get_category_from_cpe")
    @patch(f"{PATH}._get_category_from_hardware_types")
    @patch(f"{PATH}._get_category_from_asset_type")
    def test_map_category_from_asset_type(self, mock_asset_type, mock_hardware, mock_cpe):
        """Test mapping category from asset type"""
        mock_cpe.return_value = None
        mock_hardware.return_value = None
        mock_asset_type.return_value = regscale_models.AssetCategory.Software

        node = {"type": "Application", "graphEntity": {}}

        result = map_category(node)

        self.assertEqual(result, regscale_models.AssetCategory.Software)
        mock_asset_type.assert_called_once()

    @patch(f"{PATH}._get_category_from_cpe")
    @patch(f"{PATH}._get_category_from_hardware_types")
    @patch(f"{PATH}._get_category_from_asset_type")
    def test_map_category_default_to_software(self, mock_asset_type, mock_hardware, mock_cpe):
        """Test default category is Software"""
        mock_cpe.return_value = None
        mock_hardware.return_value = None
        mock_asset_type.return_value = None

        node = {"type": "Unknown", "graphEntity": {}}

        result = map_category(node)

        self.assertEqual(result, regscale_models.AssetCategory.Software)

    @patch(f"{PATH}.extract_product_name_and_version")
    def test_get_category_from_cpe_valid(self, mock_extract):
        """Test getting category from valid CPE"""
        mock_extract.return_value = {"part": "h"}
        node = {"graphEntity": {"properties": {"cpe": "cpe:2.3:h:vendor:product:*"}}}

        result = _get_category_from_cpe(node)

        self.assertEqual(result, regscale_models.AssetCategory.Hardware)

    @patch(f"{PATH}.extract_product_name_and_version")
    def test_get_category_from_cpe_no_cpe(self, mock_extract):
        """Test getting category when no CPE present"""
        node = {"graphEntity": {"properties": {}}}

        result = _get_category_from_cpe(node)

        self.assertIsNone(result)

    @patch(f"{PATH}.WizVariables")
    def test_get_category_from_hardware_types_matching_type(self, mock_vars):
        """Test getting hardware category from matching type"""
        mock_vars.useWizHardwareAssetTypes = True
        mock_vars.wizHardwareAssetTypes = ["VIRTUAL_MACHINE", "CONTAINER"]

        node = {"type": "VIRTUAL_MACHINE", "graphEntity": {}}

        result = _get_category_from_hardware_types(node, "VIRTUAL_MACHINE")

        self.assertEqual(result, regscale_models.AssetCategory.Hardware)

    @patch(f"{PATH}.WizVariables")
    def test_get_category_from_hardware_types_feature_disabled(self, mock_vars):
        """Test when useWizHardwareAssetTypes is disabled"""
        mock_vars.useWizHardwareAssetTypes = False

        node = {"type": "VIRTUAL_MACHINE", "graphEntity": {}}

        result = _get_category_from_hardware_types(node, "VIRTUAL_MACHINE")

        self.assertIsNone(result)

    def test_get_category_from_asset_type_valid_attribute(self):
        """Test getting category from valid asset type attribute"""
        node = {"type": "Software"}

        result = _get_category_from_asset_type("Software", node)

        self.assertEqual(result, regscale_models.AssetCategory.Software)

    def test_get_category_from_asset_type_invalid_attribute(self):
        """Test getting category from invalid asset type"""
        node = {"type": "Unknown"}

        result = _get_category_from_asset_type("UnknownType", node)

        self.assertIsNone(result)


# ==================== Asset Type Creation Tests ====================
class TestAssetTypeCreation(unittest.TestCase):
    """Test asset type creation and formatting"""

    @patch(f"{PATH}.regscale_models.Metadata.get_metadata_by_module_field")
    @patch(f"{PATH}.regscale_models.Metadata")
    def test_create_asset_type_new_type(self, mock_metadata_class, mock_get_metadata):
        """Test creating a new asset type"""
        mock_get_metadata.return_value = []
        mock_metadata_instance = MagicMock()
        mock_metadata_class.return_value = mock_metadata_instance

        result = create_asset_type("VIRTUAL_MACHINE")

        self.assertEqual(result, "Virtual Machine")
        mock_metadata_instance.create.assert_called_once()

    @patch(f"{PATH}.regscale_models.Metadata.get_metadata_by_module_field")
    def test_create_asset_type_existing_type(self, mock_get_metadata):
        """Test with existing asset type"""
        mock_metadata = MagicMock()
        mock_metadata.value = "Virtual Machine"
        mock_get_metadata.return_value = [mock_metadata]

        result = create_asset_type("virtual_machine")

        self.assertEqual(result, "Virtual Machine")

    @patch(f"{PATH}.regscale_models.Metadata.get_metadata_by_module_field")
    @patch(f"{PATH}.regscale_models.Metadata")
    def test_create_asset_type_formatting(self, mock_metadata_class, mock_get_metadata):
        """Test asset type string formatting"""
        mock_get_metadata.return_value = []
        mock_metadata_instance = MagicMock()
        mock_metadata_class.return_value = mock_metadata_instance

        result = create_asset_type("test_asset_type")

        self.assertEqual(result, "Test Asset Type")


# ==================== Framework and Report Tests ====================
class TestFrameworkAndReports(unittest.TestCase):
    """Test framework and report handling functions"""

    def test_get_framework_names_single(self):
        """Test getting framework names with single framework"""
        wiz_frameworks = [{"name": "NIST SP 800-53 Revision 5"}]

        result = get_framework_names(wiz_frameworks)

        self.assertEqual(result, ["NIST_SP_800-53_Revision_5"])

    def test_get_framework_names_multiple(self):
        """Test getting framework names with multiple frameworks"""
        wiz_frameworks = [{"name": "NIST SP 800-53 Revision 5"}, {"name": "NIST CSF v1.1"}, {"name": "ISO 27001"}]

        result = get_framework_names(wiz_frameworks)

        self.assertEqual(result, ["NIST_SP_800-53_Revision_5", "NIST_CSF_v1.1", "ISO_27001"])

    def test_get_framework_names_empty(self):
        """Test getting framework names with empty list"""
        result = get_framework_names([])
        self.assertEqual(result, [])

    def test_check_reports_for_frameworks_found(self):
        """Test checking reports when framework is found"""
        reports = [
            {"name": "NIST_SP_800-53_Revision_5_project_123"},
            {"name": "ISO_27001_project_456"},
        ]
        frames = ["NIST_SP_800-53_Revision_5"]

        result = check_reports_for_frameworks(reports, frames)

        self.assertTrue(result)

    def test_check_reports_for_frameworks_not_found(self):
        """Test checking reports when framework is not found"""
        reports = [
            {"name": "ISO_27001_project_456"},
        ]
        frames = ["NIST_SP_800-53_Revision_5"]

        result = check_reports_for_frameworks(reports, frames)

        self.assertFalse(result)

    def test_check_reports_for_frameworks_empty_reports(self):
        """Test checking empty reports"""
        result = check_reports_for_frameworks([], ["NIST_SP_800-53_Revision_5"])
        self.assertFalse(result)

    @patch(f"{PATH}.create_compliance_report")
    def test_create_report_if_needed_creates_new(self, mock_create_report):
        """Test creating a new report when needed"""
        mock_create_report.return_value = "new-report-123"

        wiz_project_id = "project-456"
        frames = ["NIST_SP_800-53_Revision_5"]
        wiz_frameworks = [{"id": "framework-1", "name": "NIST SP 800-53 Revision 5"}]
        reports = []
        snake_framework = "NIST_SP_800-53_Revision_5"

        result = create_report_if_needed(wiz_project_id, frames, wiz_frameworks, reports, snake_framework)

        self.assertEqual(result, ["new-report-123"])
        mock_create_report.assert_called_once()

    def test_create_report_if_needed_existing_reports(self):
        """Test when reports already exist"""
        wiz_project_id = "project-456"
        frames = ["NIST_SP_800-53_Revision_5"]
        wiz_frameworks = [{"id": "framework-1", "name": "NIST SP 800-53 Revision 5"}]
        reports = [
            {"id": "existing-report-1", "name": "NIST_SP_800-53_Revision_5_project_123"},
            {"id": "existing-report-2", "name": "other_framework_project_123"},
        ]
        snake_framework = "NIST_SP_800-53_Revision_5"

        result = create_report_if_needed(wiz_project_id, frames, wiz_frameworks, reports, snake_framework)

        self.assertEqual(result, ["existing-report-1"])


# ==================== Report Download and Processing Tests ====================
class TestReportDownloadAndProcessing(unittest.TestCase):
    """Test report download and processing functions"""

    @patch(f"{PATH}.get_report_url_and_status")
    @patch(f"{PATH}.requests.get")
    @patch(f"{PATH}.csv.DictReader")
    def test_fetch_and_process_report_data(self, mock_dict_reader, mock_requests_get, mock_get_url):
        """Test fetching and processing report data"""
        mock_get_url.return_value = "https://example.com/report.csv"

        # Mock response
        mock_response = MagicMock()
        mock_response.iter_lines.return_value = [
            b"col1,col2",
            b"val1,val2",
            b"val3,val4",
        ]
        mock_requests_get.return_value.__enter__.return_value = mock_response

        # Mock CSV reader
        mock_dict_reader.return_value = [
            {"col1": "val1", "col2": "val2"},
            {"col1": "val3", "col2": "val4"},
        ]

        wiz_report_ids = ["report-1"]
        result = fetch_and_process_report_data(wiz_report_ids)

        self.assertEqual(len(result), 2)
        mock_get_url.assert_called_once_with("report-1")

    @patch(f"{PATH}.check_file_path")
    @patch(f"{PATH}.requests.get")
    @patch("builtins.open", new_callable=mock_open)
    def test_download_file_success(self, mock_file, mock_requests_get, mock_check_path):
        """Test successful file download"""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.iter_content.return_value = [b"chunk1", b"chunk2"]
        mock_requests_get.return_value.__enter__.return_value = mock_response

        download_file("https://example.com/file.csv", "artifacts/test.csv")

        mock_check_path.assert_called_once_with("artifacts")
        mock_requests_get.assert_called_once()
        mock_file.assert_called_once()

    @patch(f"{PATH}.check_file_path")
    @patch(f"{PATH}.requests.get")
    def test_download_file_http_error(self, mock_requests_get, mock_check_path):
        """Test file download with HTTP error"""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        mock_requests_get.return_value.__enter__.return_value = mock_response

        with self.assertRaises(requests.HTTPError):
            download_file("https://example.com/file.csv", "artifacts/test.csv")

    @patch(f"{PATH}.WizVariables")
    @patch(f"{PATH}.PaginatedGraphQLClient")
    @patch(f"{PATH}.error_and_exit")
    def test_fetch_report_by_id_no_token(self, mock_error_exit, mock_client, mock_vars):
        """Test fetch_report_by_id with missing token"""
        mock_vars.wizAccessToken = None
        mock_error_exit.side_effect = SystemExit(1)

        with pytest.raises(SystemExit):
            fetch_report_by_id("report-123", 456)

        mock_error_exit.assert_called_once()

    @patch(f"{PATH}.WizVariables")
    @patch(f"{PATH}.PaginatedGraphQLClient")
    @patch(f"{PATH}.download_file")
    @patch(f"{PATH}.Api")
    @patch(f"{PATH}.File")
    def test_fetch_report_by_id_success(self, mock_file, mock_api, mock_download, mock_client, mock_vars):
        """Test successful report fetch"""
        mock_vars.wizAccessToken = "test-token"
        mock_vars.wizUrl = "https://api.wiz.io/graphql"

        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.fetch_results.return_value = {
            "report": {"lastRun": {"url": "https://example.com/report.csv"}}
        }

        mock_api_instance = MagicMock()
        mock_api.return_value = mock_api_instance

        fetch_report_by_id("report-123", 456)

        mock_download.assert_called_once()
        mock_file.upload_file_to_regscale.assert_called_once()

    @patch(f"{PATH}.WizVariables")
    @patch(f"{PATH}.PaginatedGraphQLClient")
    def test_fetch_report_by_id_with_errors(self, mock_client, mock_vars):
        """Test fetch_report_by_id with API errors"""
        mock_vars.wizAccessToken = "test-token"
        mock_vars.wizUrl = "https://api.wiz.io/graphql"

        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.fetch_results.return_value = {"errors": [{"message": "API Error"}]}

        # Should not raise, just log error
        fetch_report_by_id("report-123", 456)


# ==================== SBOM Report Tests ====================
class TestSBOMReports(unittest.TestCase):
    """Test SBOM report fetching and processing"""

    @patch(f"{PATH}.WizVariables")
    @patch(f"{PATH}.error_and_exit")
    def test_fetch_sbom_report_no_token(self, mock_error_exit, mock_vars):
        """Test fetch_sbom_report with missing token"""
        mock_vars.wizAccessToken = None
        mock_error_exit.side_effect = SystemExit(1)

        with pytest.raises(SystemExit):
            fetch_sbom_report("report-123", "456")

        mock_error_exit.assert_called_once()

    @patch(f"{PATH}.WizVariables")
    @patch(f"{PATH}.PaginatedGraphQLClient")
    @patch(f"{PATH}.download_file")
    @patch(f"{PATH}.ZipFile")
    @patch(f"{PATH}.Sbom")
    def test_fetch_sbom_report_success(self, mock_sbom, mock_zipfile, mock_download, mock_client, mock_vars):
        """Test successful SBOM report fetch"""
        mock_vars.wizAccessToken = "test-token"
        mock_vars.wizUrl = "https://api.wiz.io/graphql"

        # Mock client response
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.fetch_results.return_value = {
            "report": {"lastRun": {"url": "https://example.com/sbom.zip"}}
        }

        # Mock zip file
        mock_zip_instance = MagicMock()
        mock_zipfile.return_value.__enter__.return_value = mock_zip_instance
        mock_zip_instance.namelist.return_value = ["sbom.json"]

        # Mock JSON file inside zip
        mock_json_file = MagicMock()
        mock_json_file.__enter__.return_value = mock_json_file
        sbom_data = {"bomFormat": "CycloneDX", "specVersion": "1.5", "components": []}
        mock_json_file.read.return_value = json.dumps(sbom_data).encode()
        mock_zip_instance.open.return_value = mock_json_file

        # Mock Sbom model
        mock_sbom_instance = MagicMock()
        mock_sbom.return_value = mock_sbom_instance

        fetch_sbom_report("report-123", "456")

        mock_download.assert_called_once()
        mock_sbom.assert_called_once()
        mock_sbom_instance.create_or_update.assert_called_once()


# ==================== GraphQL Request Tests ====================
class TestGraphQLRequests(unittest.TestCase):
    """Test GraphQL request functions"""

    @patch(f"{PATH}.WizVariables")
    @patch(f"{PATH}.Api")
    def test_send_request_success(self, mock_api, mock_vars):
        """Test successful send_request"""
        mock_vars.wizUrl = "https://api.wiz.io/graphql"
        mock_vars.wizAccessToken = "test-token"

        mock_api_instance = MagicMock()
        mock_api.return_value = mock_api_instance

        mock_response = MagicMock()
        mock_api_instance.post.return_value = mock_response

        query = "query { test }"
        variables = {"var1": "value1"}

        result = send_request(query, variables)

        self.assertEqual(result, mock_response)
        mock_api_instance.post.assert_called_once()

    @patch(f"{PATH}.WizVariables")
    @patch(f"{PATH}.Api")
    def test_send_request_no_token(self, mock_api, mock_vars):
        """Test send_request with missing token"""
        mock_vars.wizAccessToken = None

        query = "query { test }"
        variables = {"var1": "value1"}

        with self.assertRaises(ValueError) as context:
            send_request(query, variables)

        self.assertIn("access token is missing", str(context.exception))

    @patch(f"{PATH}.send_request")
    def test_fetch_frameworks_success(self, mock_send_request):
        """Test successful fetch_frameworks"""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "data": {
                "securityFrameworks": {
                    "nodes": [
                        {"id": "framework-1", "name": "NIST SP 800-53 Revision 5"},
                        {"id": "framework-2", "name": "ISO 27001"},
                    ]
                }
            }
        }
        mock_send_request.return_value = mock_response

        result = fetch_frameworks()

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["name"], "NIST SP 800-53 Revision 5")

    @patch(f"{PATH}.send_request")
    @patch(f"{PATH}.error_and_exit")
    def test_fetch_frameworks_error(self, mock_error_exit, mock_send_request):
        """Test fetch_frameworks with API error"""
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_send_request.return_value = mock_response
        mock_error_exit.side_effect = SystemExit(1)

        with pytest.raises(SystemExit):
            fetch_frameworks()

        mock_error_exit.assert_called_once()

    @patch(f"{PATH}.send_request")
    def test_query_reports_success(self, mock_send_request):
        """Test successful query_reports"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "reports": {
                    "nodes": [
                        {"id": "report-1", "name": "Test Report 1"},
                        {"id": "report-2", "name": "Test Report 2"},
                    ]
                }
            }
        }
        mock_send_request.return_value = mock_response

        result = query_reports("project-123")

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["id"], "report-1")

    @patch(f"{PATH}.send_request")
    @patch(f"{PATH}.error_and_exit")
    def test_query_reports_with_errors(self, mock_error_exit, mock_send_request):
        """Test query_reports with API errors"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"errors": [{"message": "API Error"}]}
        mock_send_request.return_value = mock_response
        mock_error_exit.side_effect = SystemExit(1)

        with pytest.raises(SystemExit):
            query_reports("project-123")

        mock_error_exit.assert_called_once()

    @patch(f"{PATH}.send_request")
    @patch(f"{PATH}.error_and_exit")
    def test_query_reports_json_decode_error(self, mock_error_exit, mock_send_request):
        """Test query_reports with JSON decode error"""
        mock_response = MagicMock()
        mock_response.json.side_effect = requests.JSONDecodeError("msg", "doc", 0)
        mock_response.status_code = 500
        mock_response.reason = "Internal Server Error"
        mock_send_request.return_value = mock_response
        mock_error_exit.side_effect = SystemExit(1)

        with pytest.raises(SystemExit):
            query_reports("project-123")

        mock_error_exit.assert_called_once()


# ==================== Report Creation and Download Tests ====================
class TestReportCreationAndDownload(unittest.TestCase):
    """Test report creation and download functions"""

    @patch(f"{PATH}.fetch_report_id")
    def test_create_compliance_report(self, mock_fetch_report_id):
        """Test creating compliance report"""
        mock_fetch_report_id.return_value = "new-report-789"

        result = create_compliance_report(
            report_name="Test_Report", wiz_project_id="project-123", framework_id="framework-456"
        )

        self.assertEqual(result, "new-report-789")
        mock_fetch_report_id.assert_called_once()

    @patch(f"{PATH}.send_request")
    def test_download_report(self, mock_send_request):
        """Test download_report"""
        mock_response = MagicMock()
        mock_send_request.return_value = mock_response

        variables = {"reportId": "report-123"}
        result = download_report(variables)

        self.assertEqual(result, mock_response)
        mock_send_request.assert_called_once()

    @patch(f"{PATH}.send_request")
    def test_rerun_expired_report(self, mock_send_request):
        """Test rerun_expired_report"""
        mock_response = MagicMock()
        mock_send_request.return_value = mock_response

        variables = {"reportId": "report-123"}
        result = rerun_expired_report(variables)

        self.assertEqual(result, mock_response)
        mock_send_request.assert_called_once()

    @patch(f"{PATH}.time.sleep")
    @patch(f"{PATH}.download_report")
    def test_get_report_url_and_status_completed(self, mock_download_report, mock_sleep):
        """Test get_report_url_and_status with completed status"""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "data": {"report": {"lastRun": {"status": "COMPLETED", "url": "https://example.com/report.csv"}}}
        }
        mock_download_report.return_value = mock_response

        result = get_report_url_and_status("report-123")

        self.assertEqual(result, "https://example.com/report.csv")
        mock_download_report.assert_called_once()

    @patch(f"{PATH}.time.sleep")
    @patch(f"{PATH}.download_report")
    def test_get_report_url_and_status_failed_response(self, mock_download_report, mock_sleep):
        """Test get_report_url_and_status with failed response"""
        mock_response = MagicMock()
        mock_response.ok = False
        mock_download_report.return_value = mock_response

        with self.assertRaises(requests.RequestException) as context:
            get_report_url_and_status("report-123")

        self.assertIn("Failed to download report", str(context.exception))

    def test_handle_rate_limit_error_with_rate_limit(self):
        """Test handling rate limit error"""
        errors = [{"message": "Rate limit exceeded", "extensions": {"retryAfter": 0.001}}]

        with patch(f"{PATH}.time.sleep") as mock_sleep:
            result = _handle_rate_limit_error(errors)

            self.assertTrue(result)
            mock_sleep.assert_called_once_with(0.001)

    def test_handle_rate_limit_error_without_rate_limit(self):
        """Test handling non-rate-limit error"""
        errors = [{"message": "Some other error"}]

        result = _handle_rate_limit_error(errors)

        self.assertFalse(result)

    def test_handle_report_response_completed(self):
        """Test handling completed report response"""
        response_json = {"data": {"report": {"lastRun": {"status": "COMPLETED", "url": "https://example.com/report"}}}}

        result = _handle_report_response(response_json, "report-123")

        self.assertEqual(result, "https://example.com/report")

    @patch(f"{PATH}.rerun_expired_report")
    @patch(f"{PATH}.get_report_url_and_status")
    def test_handle_report_response_expired(self, mock_get_url, mock_rerun):
        """Test handling expired report response"""
        response_json = {"data": {"report": {"lastRun": {"status": "EXPIRED"}}}}
        mock_get_url.return_value = "https://example.com/new-report"

        result = _handle_report_response(response_json, "report-123")

        self.assertEqual(result, "https://example.com/new-report")
        mock_rerun.assert_called_once()

    def test_handle_report_response_with_errors(self):
        """Test handling response with errors"""
        response_json = {"errors": [{"message": "API Error"}]}

        result = _handle_report_response(response_json, "report-123")

        self.assertIsNone(result)


# ==================== Compliance Check Tests ====================
class TestComplianceChecks(unittest.TestCase):
    """Test compliance checking and assessment creation"""

    def test_check_compliance_passing_control(self):
        """Test checking compliance for passing control"""
        cr_dict = {
            "Framework": "NIST SP 800-53 Revision 5",
            "Compliance Check Name (Wiz Subcategory)": "ac-1 access control policy",
            "Result": "Pass",
            "Resource Name": "test-resource",
            "Resource ID": "res-123",
            "Cloud Provider": "AWS",
            "Cloud Provider ID": "cloud-123",
            "Object Type": "VM",
            "Native Type": "Virtual Machine",
            "Subscription": "sub-123",
            "Policy ID": "policy-123",
            "Policy Short Name": "AC-1",
            "Severity": "Medium",
            "Assessed At": "2023-07-15T14:37:55.450532Z",
        }
        cr = ComplianceReport(**cr_dict)

        controls = [{"controlId": "AC-1", "id": 1}]
        passing = {}
        failing = {}
        controls_to_reports = {}

        check_compliance(cr, controls, passing, failing, controls_to_reports)

        self.assertIn("ac-1", passing)
        self.assertIn("ac-1", controls_to_reports)
        self.assertEqual(len(controls_to_reports["ac-1"]), 1)

    def test_check_compliance_failing_control(self):
        """Test checking compliance for failing control"""
        cr_dict = {
            "Framework": "NIST SP 800-53 Revision 5",
            "Compliance Check Name (Wiz Subcategory)": "ac-2 account management",
            "Result": "Fail",
            "Resource Name": "test-resource",
            "Resource ID": "res-456",
            "Cloud Provider": "Azure",
            "Cloud Provider ID": "cloud-456",
            "Object Type": "VM",
            "Native Type": "Virtual Machine",
            "Subscription": "sub-456",
            "Policy ID": "policy-456",
            "Policy Short Name": "AC-2",
            "Severity": "High",
            "Assessed At": "2023-07-15T14:37:55.450532Z",
        }
        cr = ComplianceReport(**cr_dict)

        controls = [{"controlId": "AC-2", "id": 2}]
        passing = {}
        failing = {}
        controls_to_reports = {}

        check_compliance(cr, controls, passing, failing, controls_to_reports)

        self.assertIn("ac-2", failing)
        self.assertNotIn("ac-2", passing)

    def test_add_controls_to_controls_to_report_dict_new(self):
        """Test adding control to report dict for first time"""
        control = {"controlId": "AC-1", "id": 1}
        controls_to_reports = {}
        cr = MagicMock()

        _add_controls_to_controls_to_report_dict(control, controls_to_reports, cr)

        self.assertIn("ac-1", controls_to_reports)
        self.assertEqual(len(controls_to_reports["ac-1"]), 1)

    def test_add_controls_to_controls_to_report_dict_existing(self):
        """Test adding control to report dict when already exists"""
        control = {"controlId": "AC-1", "id": 1}
        cr1 = MagicMock()
        controls_to_reports = {"ac-1": [cr1]}
        cr2 = MagicMock()

        _add_controls_to_controls_to_report_dict(control, controls_to_reports, cr2)

        self.assertEqual(len(controls_to_reports["ac-1"]), 2)

    def test_clean_passing_list(self):
        """Test cleaning passing list removes failing controls"""
        passing = {"ac-1": {"controlId": "AC-1"}, "ac-2": {"controlId": "AC-2"}}
        failing = {"ac-2": {"controlId": "AC-2"}}

        _clean_passing_list(passing, failing)

        self.assertIn("ac-1", passing)
        self.assertNotIn("ac-2", passing)


# ==================== Assessment Creation Tests ====================
class TestAssessmentCreation(unittest.TestCase):
    """Test assessment creation from compliance reports"""

    def test_create_aggregated_assessment_report_with_failures(self):
        """Test creating aggregated assessment report with failures"""
        asset_details = [
            {
                "resource_name": "resource1",
                "resource_id": "id1",
                "cloud_provider": "AWS",
                "subscription": "sub1",
                "result": "Fail",
                "policy_short_name": "AC-1",
                "compliance_check": "access control",
                "severity": "High",
                "assessed_at": "2023-07-15",
            },
            {
                "resource_name": "resource2",
                "resource_id": "id2",
                "cloud_provider": "Azure",
                "subscription": "sub2",
                "result": "Pass",
                "policy_short_name": "AC-2",
                "compliance_check": "account management",
                "severity": "Medium",
                "assessed_at": "2023-07-15",
            },
        ]

        result = _create_aggregated_assessment_report(
            control_id="AC-1",
            overall_result="Fail",
            pass_count=1,
            fail_count=1,
            asset_details=asset_details,
            total_assets=2,
        )

        self.assertIn("AC-1", result)
        self.assertIn("Fail", result)
        self.assertIn("resource1", result)
        self.assertIn("resource2", result)
        self.assertIn("Total Assets Assessed:", result)

    def test_create_aggregated_assessment_report_all_pass(self):
        """Test creating aggregated assessment report with all passing"""
        asset_details = [
            {
                "resource_name": "resource1",
                "resource_id": "id1",
                "cloud_provider": "AWS",
                "subscription": "sub1",
                "result": "Pass",
                "policy_short_name": "AC-1",
                "compliance_check": "access control",
                "severity": "Low",
                "assessed_at": "2023-07-15",
            }
        ]

        result = _create_aggregated_assessment_report(
            control_id="AC-1",
            overall_result="Pass",
            pass_count=1,
            fail_count=0,
            asset_details=asset_details,
            total_assets=1,
        )

        self.assertIn("AC-1", result)
        self.assertIn("Pass", result)
        self.assertIn("#2e7d32", result)  # Green color for pass

    @patch(f"{PATH}.Assessment")
    @patch(f"{PATH}.update_implementation_status")
    def test_create_report_assessment_with_failures(self, mock_update_status, mock_assessment):
        """Test creating report assessment with failures"""
        implementation = MagicMock()
        implementation.id = 123
        implementation.createdById = 456

        reports = [
            MagicMock(
                result="Fail",
                resource_name="res1",
                resource_id="id1",
                cloud_provider="AWS",
                subscription="sub1",
                policy_short_name="AC-1",
                compliance_check="access control",
                severity="High",
                assessed_at="2023-07-15",
            )
        ]

        mock_assessment_instance = MagicMock()
        mock_assessment_instance.id = 789
        mock_assessment.return_value = mock_assessment_instance
        mock_assessment_instance.create.return_value = mock_assessment_instance

        create_report_assessment([implementation], reports, "AC-1", update_control_status=True)

        mock_assessment.assert_called_once()
        mock_assessment_instance.create.assert_called_once()
        mock_update_status.assert_called_once()

    @patch(f"{PATH}.Assessment")
    def test_create_report_assessment_no_implementation(self, mock_assessment):
        """Test creating report assessment with no implementation"""
        create_report_assessment([], [], "AC-1")

        mock_assessment.assert_not_called()

    @patch(f"{PATH}.Assessment")
    @patch(f"{PATH}.update_implementation_status")
    def test_create_report_assessment_update_status_disabled(self, mock_update_status, mock_assessment):
        """Test creating report assessment with status update disabled"""
        implementation = MagicMock()
        implementation.id = 123
        implementation.createdById = 456

        reports = [
            MagicMock(
                result="Pass",
                resource_name="res1",
                resource_id="id1",
                cloud_provider="AWS",
                subscription="sub1",
                policy_short_name="AC-1",
                compliance_check="access control",
                severity="Low",
                assessed_at="2023-07-15",
            )
        ]

        mock_assessment_instance = MagicMock()
        mock_assessment.return_value = mock_assessment_instance
        mock_assessment_instance.create.return_value = mock_assessment_instance

        create_report_assessment([implementation], reports, "AC-1", update_control_status=False)

        mock_update_status.assert_not_called()


# ==================== Status Mapping Tests ====================
class TestStatusMapping(unittest.TestCase):
    """Test compliance status to implementation status mapping"""

    def test_get_default_status_mapping_pass(self):
        """Test default status mapping for Pass"""
        result = _get_default_status_mapping(ComplianceCheckStatus.PASS.value)
        self.assertEqual(result, "Implemented")

    def test_get_default_status_mapping_fail(self):
        """Test default status mapping for Fail"""
        result = _get_default_status_mapping(ComplianceCheckStatus.FAIL.value)
        self.assertEqual(result, "In Remediation")

    def test_get_default_status_mapping_other(self):
        """Test default status mapping for other status"""
        result = _get_default_status_mapping("Unknown")
        self.assertEqual(result, "Not Implemented")

    def test_match_label_to_result_pass(self):
        """Test matching label to Pass result"""
        result = _match_label_to_result("Implemented", ComplianceCheckStatus.PASS.value.lower())
        self.assertEqual(result, "Implemented")

        result = _match_label_to_result("Complete", ComplianceCheckStatus.PASS.value.lower())
        self.assertEqual(result, "Complete")

    def test_match_label_to_result_fail(self):
        """Test matching label to Fail result"""
        result = _match_label_to_result("InRemediation", ComplianceCheckStatus.FAIL.value.lower())
        self.assertEqual(result, "InRemediation")

        result = _match_label_to_result("Failed", ComplianceCheckStatus.FAIL.value.lower())
        self.assertEqual(result, "Failed")

    def test_match_label_to_result_no_match(self):
        """Test matching label with no match"""
        result = _match_label_to_result("SomeOtherLabel", ComplianceCheckStatus.PASS.value.lower())
        self.assertIsNone(result)

    @patch(f"{PATH}.get_wiz_compliance_settings")
    def test_report_result_to_implementation_status_with_settings(self, mock_get_settings):
        """Test converting report result with compliance settings"""
        mock_settings = MagicMock()
        mock_settings.get_field_labels.return_value = ["Implemented", "InRemediation", "NotImplemented"]
        mock_get_settings.return_value = mock_settings

        result = report_result_to_implementation_status("Pass")

        self.assertEqual(result, "Implemented")

    @patch(f"{PATH}.get_wiz_compliance_settings")
    def test_report_result_to_implementation_status_no_settings(self, mock_get_settings):
        """Test converting report result without compliance settings"""
        mock_get_settings.return_value = None

        result = report_result_to_implementation_status("Pass")

        self.assertEqual(result, "Implemented")

    @patch(f"{PATH}.ComplianceSettings")
    def test_get_wiz_compliance_settings_found(self, mock_compliance_settings):
        """Test getting Wiz compliance settings when found"""
        mock_setting = MagicMock()
        mock_setting.title = "Wiz Compliance Setting"
        mock_compliance_settings.get_by_current_tenant.return_value = [mock_setting]

        result = get_wiz_compliance_settings()

        self.assertEqual(result, mock_setting)

    @patch(f"{PATH}.ComplianceSettings")
    def test_get_wiz_compliance_settings_not_found(self, mock_compliance_settings):
        """Test getting Wiz compliance settings when not found"""
        mock_other_setting = MagicMock()
        mock_other_setting.title = "Other Setting"
        mock_compliance_settings.get_by_current_tenant.return_value = [mock_other_setting]

        result = get_wiz_compliance_settings()

        self.assertIsNone(result)

    @patch(f"{PATH}.ComplianceSettings")
    def test_get_wiz_compliance_settings_exception(self, mock_compliance_settings):
        """Test getting Wiz compliance settings with exception"""
        mock_compliance_settings.get_by_current_tenant.side_effect = Exception("API Error")

        result = get_wiz_compliance_settings()

        self.assertIsNone(result)

    @patch(f"{PATH}.ImplementationObjective")
    def test_update_implementation_status_with_objectives(self, mock_objective):
        """Test updating implementation status with objectives"""
        implementation = MagicMock()
        implementation.id = 123
        implementation.get_module_slug.return_value = "controls"

        objective = MagicMock()
        objective.id = 456
        mock_objective.get_all_by_parent.return_value = [objective]

        update_implementation_status(implementation, "Pass")

        objective.save.assert_called_once()
        implementation.save.assert_called_once()

    @patch(f"{PATH}.ImplementationObjective")
    def test_update_implementation_status_no_objectives(self, mock_objective):
        """Test updating implementation status without objectives"""
        implementation = MagicMock()
        implementation.id = 123
        implementation.get_module_slug.return_value = "controls"

        mock_objective.get_all_by_parent.return_value = []

        update_implementation_status(implementation, "Pass")

        self.assertEqual(implementation.objectives, [])
        implementation.save.assert_called_once()


# ==================== Vulnerability Creation Tests ====================
class TestVulnerabilityCreation(unittest.TestCase):
    """Test vulnerability creation from Wiz findings"""

    @patch(f"{PATH}.WizVariables")
    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration")
    def test_create_vulnerabilities_from_wiz_findings_success(self, mock_wiz_integration_class, mock_vars):
        """Test successful vulnerability creation"""
        mock_vars.wizAccessToken = "test-token"

        mock_integration = MagicMock()
        mock_wiz_integration_class.return_value = mock_integration
        mock_wiz_integration_class.sync_findings.return_value = 10

        result = create_vulnerabilities_from_wiz_findings(
            wiz_project_id="project-123", regscale_plan_id=456, client_id="client-id", client_secret="client-secret"
        )

        self.assertEqual(result, 10)
        mock_integration.authenticate.assert_called_once_with(client_id="client-id", client_secret="client-secret")

    @patch(f"{PATH}.WizVariables")
    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration")
    def test_create_vulnerabilities_from_wiz_findings_with_filter(self, mock_wiz_integration_class, mock_vars):
        """Test vulnerability creation with filter override"""
        mock_vars.wizAccessToken = "test-token"

        mock_integration = MagicMock()
        mock_wiz_integration_class.return_value = mock_integration
        mock_wiz_integration_class.sync_findings.return_value = 5

        filter_override = '{"severity": "HIGH"}'
        result = create_vulnerabilities_from_wiz_findings(
            wiz_project_id="project-123", regscale_plan_id=456, filter_by_override=filter_override
        )

        self.assertEqual(result, 5)

    @patch(f"{PATH}.WizVariables")
    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration")
    def test_create_vulnerabilities_from_wiz_findings_error(self, mock_wiz_integration_class, mock_vars):
        """Test vulnerability creation with error"""
        mock_vars.wizAccessToken = "test-token"

        mock_wiz_integration_class.side_effect = Exception("Integration Error")

        with self.assertRaises(Exception):
            create_vulnerabilities_from_wiz_findings(wiz_project_id="project-123", regscale_plan_id=456)

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration")
    def test_create_single_vulnerability_from_wiz_data_success(self, mock_wiz_integration_class):
        """Test creating single vulnerability successfully"""
        mock_integration = MagicMock()
        mock_wiz_integration_class.return_value = mock_integration

        # Mock scan history with RegScaleModel-like behavior
        mock_scan_history_instance = MagicMock()
        mock_scan_history_instance.id = 456

        # Create a mock ScanHistory class that returns the instance from get_by_id
        with patch(f"{PATH}.regscale_models.ScanHistory") as mock_scan_history_class:
            mock_scan_history_class.get_by_id.return_value = mock_scan_history_instance

            mock_finding = MagicMock()
            mock_integration.parse_finding.return_value = mock_finding

            mock_asset = MagicMock()
            mock_integration.get_asset_by_identifier.return_value = mock_asset

            mock_integration.handle_vulnerability.return_value = 789

            # Mock Vulnerability class with get_by_id
            mock_vuln = MagicMock()
            mock_vuln.id = 789
            with patch(f"{PATH}.regscale_models.Vulnerability") as mock_vuln_class:
                mock_vuln_class.get_by_id.return_value = mock_vuln

                wiz_finding_data = {"id": "finding-123", "severity": "HIGH"}
                result = create_single_vulnerability_from_wiz_data(
                    wiz_finding_data=wiz_finding_data, asset_id="asset-456", regscale_plan_id=123, scan_history_id=456
                )

                self.assertIsNotNone(result)
                # The mock returns a MagicMock with id = 789
                self.assertEqual(result, mock_vuln)

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration")
    def test_create_single_vulnerability_from_wiz_data_no_scan_history(self, mock_wiz_integration_class):
        """Test creating single vulnerability without scan history"""
        mock_integration = MagicMock()
        mock_wiz_integration_class.return_value = mock_integration

        mock_scan_history = MagicMock()
        mock_integration.create_scan_history.return_value = mock_scan_history

        mock_finding = MagicMock()
        mock_integration.parse_finding.return_value = mock_finding

        mock_asset = MagicMock()
        mock_integration.get_asset_by_identifier.return_value = mock_asset

        mock_integration.handle_vulnerability.return_value = 789

        mock_vuln = MagicMock()
        mock_vuln.id = 789
        with patch(f"{PATH}.regscale_models.Vulnerability") as mock_vuln_class:
            mock_vuln_class.get_by_id.return_value = mock_vuln

            wiz_finding_data = {"id": "finding-123", "severity": "HIGH"}
            result = create_single_vulnerability_from_wiz_data(
                wiz_finding_data=wiz_finding_data, asset_id="asset-456", regscale_plan_id=123
            )

            self.assertIsNotNone(result)
            mock_integration.create_scan_history.assert_called_once()

    @patch("regscale.integrations.commercial.wizv2.scanner.WizVulnerabilityIntegration")
    def test_create_single_vulnerability_from_wiz_data_parse_failure(self, mock_wiz_integration_class):
        """Test creating single vulnerability with parse failure"""
        mock_integration = MagicMock()
        mock_wiz_integration_class.return_value = mock_integration

        mock_scan_history = MagicMock()
        mock_integration.create_scan_history.return_value = mock_scan_history

        mock_integration.parse_finding.return_value = None

        wiz_finding_data = {"id": "finding-123"}
        result = create_single_vulnerability_from_wiz_data(
            wiz_finding_data=wiz_finding_data, asset_id="asset-456", regscale_plan_id=123
        )

        self.assertIsNone(result)


# ==================== Deprecated and Legacy Function Tests ====================
class TestDeprecatedFunctions(unittest.TestCase):
    """Test deprecated and legacy functions"""

    @patch(f"{PATH}.send_request")
    def test_fetch_report_id_success(self, mock_send_request):
        """Test deprecated fetch_report_id success"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": {"createReport": {"report": {"id": "report-123"}}}}
        mock_send_request.return_value = mock_response

        result = fetch_report_id(query="query { test }", variables={}, url="https://api.wiz.io/graphql")

        self.assertEqual(result, "report-123")

    @patch(f"{PATH}.send_request")
    @patch(f"{PATH}.error_and_exit")
    def test_fetch_report_id_with_error(self, mock_error_exit, mock_send_request):
        """Test deprecated fetch_report_id with error"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"error": "API Error"}
        mock_send_request.return_value = mock_response
        mock_error_exit.side_effect = SystemExit(1)

        with pytest.raises(SystemExit):
            fetch_report_id(query="query { test }", variables={}, url="https://api.wiz.io/graphql")

        mock_error_exit.assert_called_once()

    @patch(f"{PATH}.send_request")
    def test_fetch_report_id_request_exception(self, mock_send_request):
        """Test deprecated fetch_report_id with request exception"""
        mock_send_request.side_effect = requests.RequestException("Connection Error")

        result = fetch_report_id(query="query { test }", variables={}, url="https://api.wiz.io/graphql")

        self.assertEqual(result, "")


# ==================== Integration Tests ====================
class TestReportProcessingIntegration(unittest.TestCase):
    """Integration tests for report processing workflow"""

    @patch(f"{PATH}.get_or_create_report_id")
    @patch(f"{PATH}.fetch_report_data")
    def test_process_single_report_workflow(self, mock_fetch_data, mock_get_report_id):
        """Test complete single report processing workflow"""
        mock_get_report_id.return_value = "report-123"
        mock_fetch_data.return_value = [{"col1": "val1"}, {"col1": "val2"}]

        project_id = "project-456"
        frameworks = ["NIST_SP_800-53_Revision_5"]
        wiz_frameworks = [{"id": "framework-1", "name": "NIST SP 800-53 Revision 5"}]
        existing_reports = []
        target_framework = "NIST_SP_800-53_Revision_5"

        result = process_single_report(project_id, frameworks, wiz_frameworks, existing_reports, target_framework)

        self.assertEqual(len(result), 2)
        mock_get_report_id.assert_called_once()
        mock_fetch_data.assert_called_once_with("report-123")

    @patch(f"{PATH}.get_report_url_and_status")
    @patch(f"{PATH}.requests.get")
    @patch(f"{PATH}.error_and_exit")
    def test_fetch_report_data_success(self, mock_error_exit, mock_requests_get, mock_get_url):
        """Test successful report data fetching"""
        mock_get_url.return_value = "https://example.com/report.csv"

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.iter_lines.return_value = iter([b"col1,col2", b"val1,val2", b"val3,val4"])
        mock_requests_get.return_value.__enter__.return_value = mock_response

        result = fetch_report_data("report-123")

        self.assertIsNotNone(result)
        mock_get_url.assert_called_once_with("report-123")

    @patch(f"{PATH}.get_report_url_and_status")
    @patch(f"{PATH}.requests.get")
    @patch(f"{PATH}.error_and_exit")
    def test_fetch_report_data_request_error(self, mock_error_exit, mock_requests_get, mock_get_url):
        """Test report data fetching with request error"""
        mock_get_url.return_value = "https://example.com/report.csv"
        mock_requests_get.side_effect = requests.RequestException("Connection Error")
        mock_error_exit.side_effect = SystemExit(1)

        with pytest.raises(SystemExit):
            fetch_report_data("report-123")

        mock_error_exit.assert_called_once()

    @patch(f"{PATH}.fetch_frameworks")
    @patch(f"{PATH}.get_framework_names")
    @patch(f"{PATH}.query_reports")
    @patch(f"{PATH}.process_single_report")
    def test_fetch_framework_report_workflow(
        self, mock_process_report, mock_query_reports, mock_get_names, mock_fetch_frameworks
    ):
        """Test complete framework report fetching workflow"""
        mock_fetch_frameworks.return_value = [{"id": "framework-1", "name": "NIST SP 800-53 Revision 5"}]
        mock_get_names.return_value = ["NIST_SP_800-53_Revision_5"]
        mock_query_reports.return_value = []
        mock_process_report.return_value = [{"data": "report_data"}]

        result = fetch_framework_report("project-123", "NIST_SP_800-53_Revision_5")

        self.assertEqual(len(result), 1)
        mock_fetch_frameworks.assert_called_once()
        mock_query_reports.assert_called_once_with("project-123")


# ==================== Edge Cases and Error Handling Tests ====================
class TestEdgeCasesAndErrorHandling(unittest.TestCase):
    """Test edge cases and error handling"""

    def test_get_notes_from_wiz_props_empty_values(self):
        """Test getting notes with empty string values"""
        wiz_properties = {"cloudPlatform": "", "providerUniqueId": ""}
        external_id = ""

        result = get_notes_from_wiz_props(wiz_properties, external_id)

        # With all empty values, result should be empty string
        # The function only includes values if they are truthy
        self.assertEqual(result, "")

    @patch(f"{PATH}.regscale_models.Metadata.get_metadata_by_module_field")
    @patch(f"{PATH}.regscale_models.Metadata")
    def test_create_asset_type_with_special_characters(self, mock_metadata_class, mock_get_metadata):
        """Test creating asset type with special characters"""
        mock_get_metadata.return_value = []
        mock_metadata_instance = MagicMock()
        mock_metadata_class.return_value = mock_metadata_instance

        result = create_asset_type("test-asset_TYPE_123")

        # Should handle title case and underscore replacement
        self.assertIn("Test-Asset", result)
        self.assertIn("Type", result)

    @patch(f"{PATH}.time.sleep")
    @patch(f"{PATH}.download_report")
    @patch(f"{PATH}.MAX_RETRIES", 2)
    def test_get_report_url_and_status_max_retries_exceeded(self, mock_download_report, mock_sleep):
        """Test exceeding max retries for report download"""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {"data": {"report": {"lastRun": {"status": "PROCESSING"}}}}
        mock_download_report.return_value = mock_response

        with self.assertRaises(requests.RequestException) as context:
            get_report_url_and_status("report-123")

        self.assertIn("exceeding the maximum number of retries", str(context.exception))


if __name__ == "__main__":
    unittest.main()
