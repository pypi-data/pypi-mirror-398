#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for Microsoft Defender integration in RegScale CLI"""
# standard python imports
import contextlib
import os
import shutil
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from pathlib import Path
from regscale.integrations.commercial.microsoft_defender.defender import (
    authenticate,
    change_issue_status,
    collect_and_upload_entra_evidence,
    collect_specific_evidence_type,
    compare_defender_and_regscale,
    create_html_table,
    create_payload,
    evaluate_open_issues,
    export_resources,
    fetch_save_and_upload_query,
    format_description,
    get_control_implementations_map,
    get_defender_url,
    get_due_date,
    import_defender_alerts,
    map_365_alert_to_issue,
    map_365_recommendation_to_issue,
    map_cloud_alert_to_issue,
    map_cloud_recommendation_to_issue,
    prep_issues_for_creation,
    process_list_value,
    prompt_user_for_query_selection,
    show_entra_mappings,
    sync_defender_and_regscale,
    upload_evidence_files,
    upload_evidence_to_controls,
)
from regscale.integrations.commercial.microsoft_defender.defender_api import DefenderApi

from regscale.core.app.application import Application
from regscale.models import Issue, IssueSeverity
from regscale.models.integration_models.defender_data import DefenderData
from tests import CLITestFixture

PATH = "regscale.integrations.commercial.microsoft_defender.defender"


@pytest.mark.no_parallel
class TestDefender(CLITestFixture):
    security_plan = None

    @pytest.fixture(scope="class")
    def create_security_plan(self, request, generate_uuid):
        """Mock create_security_plan fixture to avoid real API calls in parallel tests"""
        # Create a mock security plan that doesn't require API calls
        mock_security_plan = MagicMock()
        mock_security_plan.id = 12345  # Mock ID
        mock_security_plan.get_module_string.return_value = "security_plans"  # Mock module
        yield mock_security_plan

    @pytest.fixture(autouse=True)
    def setup_ssp(self, create_security_plan):
        self.security_plan = create_security_plan

    @property
    def PARENT_ID(self):
        """Get the parent ID from the existing SSP"""
        return self.security_plan.id

    @property
    def PARENT_MODULE(self):
        """Get the parent module from the existing SSP"""
        return self.security_plan.get_module_string()

    def test_init(self):
        """Test init file and config"""
        self.verify_config(
            [
                "azure365TenantId",
                "azure365ClientId",
                "azure365Secret",
                "azureCloudTenantId",
                "azureCloudClientId",
                "azureCloudSecret",
                "azureCloudSubscriptionId",
            ]
        )

    @patch(f"{PATH}.check_license", return_value=MagicMock(spec=Application))
    @patch(f"{PATH}.DefenderApi")
    def test_authenticate_365(self, mock_defender_api, mock_check_license):
        """Test authenticating with Microsoft Defender 365"""
        mock_api_instance = MagicMock()
        mock_defender_api.return_value = mock_api_instance

        authenticate(system="365")

        mock_check_license.assert_called_once()
        mock_defender_api.assert_called_once_with(system="365")
        mock_api_instance.get_token.assert_called_once()

    @patch(f"{PATH}.check_license", return_value=MagicMock(spec=Application))
    @patch(f"{PATH}.DefenderApi")
    def test_authenticate_cloud(self, mock_defender_api, mock_check_license):
        """Test authenticating with Microsoft Defender for Cloud"""
        mock_api_instance = MagicMock()
        mock_defender_api.return_value = mock_api_instance

        authenticate(system="cloud")

        mock_check_license.assert_called_once()
        mock_defender_api.assert_called_once_with(system="cloud")
        mock_api_instance.get_token.assert_called_once()

    @pytest.mark.parametrize(
        "score,expected_days",
        [
            (9, 7),  # high score
            (5, 14),  # moderate score
            (2, 30),  # low score
            (None, 30),  # None score
            ("high", 7),  # string high
            ("medium", 14),  # string medium
            ("low", 30),  # string low
            ("unknown", 30),  # unknown string
        ],
    )
    def test_get_due_date(self, score, expected_days):
        """Test getting due date based on severity score"""
        config = {"issues": {"defender365": {"high": 7, "moderate": 14, "low": 30}}}

        result = get_due_date(score=score, config=config, key="defender365")

        # Parse the result date and calculate expected date
        today = datetime.now().strftime("%m/%d/%y")
        expected_date = datetime.strptime(today, "%m/%d/%y") + timedelta(days=expected_days)
        expected_date_str = expected_date.strftime("%Y-%m-%dT%H:%M:%S")

        assert result == expected_date_str

    def test_format_description(self):
        """Test formatting description with HTML table"""
        defender_data = {
            "id": "test-id",
            "properties": {"alertUri": "https://example.com/alert", "name": "Test Alert", "severity": "High"},
        }
        tenant_id = "test-tenant-id"

        result = format_description(defender_data=defender_data, tenant_id=tenant_id)

        assert '<table style="border: 1px solid;">' in result
        assert "test-id" in result
        assert "Test Alert" in result
        assert "High" in result
        assert "https://example.com/alert" in result

    def test_get_defender_url_with_alert_uri(self):
        """Test getting defender URL when alertUri is present"""
        rec = {"properties": {"alertUri": "https://security.microsoft.com/alerts/test-alert"}}
        tenant_id = "test-tenant-id"

        result = get_defender_url(rec=rec, tenant_id=tenant_id)

        expected = '<a href="https://security.microsoft.com/alerts/test-alert">https://security.microsoft.com/alerts/test-alert</a>'
        assert result == expected

    def test_get_defender_url_without_alert_uri(self):
        """Test getting defender URL when alertUri is not present"""
        rec = {"properties": {}}
        tenant_id = "test-tenant-id"

        result = get_defender_url(rec=rec, tenant_id=tenant_id)

        expected_url = f"https://security.microsoft.com/security-recommendations?tid={tenant_id}"
        expected = f'<a href="{expected_url}">{expected_url}</a>'
        assert result == expected

    def test_create_payload(self):
        """Test creating payload from defender data"""
        rec = {
            "name": "Test Alert",
            "severity": "High",
            "alertUri": "https://example.com",
            "associatedThreats": ["threat1"],  # should be skipped
            "propertiesExtendedPropertiesCustomField": {"customField": "customValue"},
        }

        result = create_payload(rec=rec)

        assert "Name" in result
        assert "Severity" in result
        assert "Custom Field" in result  # uncamel_case applied
        assert "customField" in result["Custom Field"]
        assert "Associated Threats" not in result  # should be skipped
        assert "Alert Uri" not in result  # should be skipped

    def test_process_list_value_with_dict_list(self):
        """Test processing list value with dictionary items"""
        value = [{"key1": "value1", "key2": "value2"}, {"key3": "value3"}]

        result = process_list_value(value=value)

        assert "</br>key1: value1</br>key2: value2</br>key3: value3" == result

    def test_process_list_value_with_nested_list(self):
        """Test processing list value with nested lists"""
        value = [["item1", "item2"], ["item3", "item4"]]

        result = process_list_value(value=value)

        assert "item1</br>item2item3</br>item4" == result

    def test_process_list_value_with_string_list(self):
        """Test processing list value with string items"""
        value = ["item1", "item2", "item3"]

        result = process_list_value(value=value)

        assert "item1</br>item2</br>item3" == result

    def test_create_html_table(self):
        """Test creating HTML table"""
        payload = {
            "name": "Test Alert",
            "severity": "High",
            "created_time": "2023-01-01T12:00:00Z",
            "empty_field": None,
        }
        url = '<a href="https://example.com">https://example.com</a>'

        result = create_html_table(payload=payload, url=url)

        assert '<table style="border: 1px solid;">' in result
        assert "Test Alert" in result
        assert "High" in result
        assert "Jan 01, 2023" in result  # time formatted
        assert "empty_field" not in result  # empty fields excluded
        assert "View in Defender" in result
        assert "</table>" in result

    def test_compare_defender_and_regscale_new_recommendation(self):
        """Test comparing when defender has new recommendation"""
        def_data = DefenderData(
            id="test-id", data={"id": "test-id", "name": "Test Rec"}, system="365", object="recommendations"
        )
        issues = []

        # Mock global variables
        with patch(f"{PATH}.unique_recs", []) as mock_unique_recs, patch(f"{PATH}.job_progress") as mock_job_progress:
            mock_task = MagicMock()
            args = (MagicMock(), issues, "id", mock_task)

            compare_defender_and_regscale(def_data=def_data, args=args)

            assert def_data.analyzed is True
            assert len(mock_unique_recs) == 1
            mock_job_progress.update.assert_called_once_with(mock_task, advance=1)

    def test_compare_defender_and_regscale_existing_open_issue(self):
        """Test comparing when issue exists and is open"""
        def_data = DefenderData(
            id="test-id", data={"id": "test-id", "name": "Test Rec"}, system="365", object="recommendations"
        )
        mock_issue = DefenderData(
            id="test-id",
            data={"status": "Open", def_data.integration_field: "test-id"},
            system="365",
            object="recommendations",
        )
        issues = [mock_issue]

        with patch(f"{PATH}.unique_recs", []) as mock_unique_recs, patch(f"{PATH}.job_progress") as mock_job_progress:
            mock_task = MagicMock()
            args = (MagicMock(), issues, "id", mock_task)

            compare_defender_and_regscale(def_data=def_data, args=args)

            assert def_data.analyzed is True
            assert len(mock_unique_recs) == 0  # Should be empty as it's a duplicate
            mock_job_progress.update.assert_called_once_with(mock_task, advance=1)

    @patch(f"{PATH}.change_issue_status")
    def test_compare_defender_and_regscale_closed_issue_reopen(self, mock_change_status):
        """Test comparing when issue exists but is closed - should reopen"""
        def_data = DefenderData(
            id="test-id", data={"id": "test-id", "name": "Test Rec"}, system="365", object="recommendations"
        )
        mock_issue = DefenderData(
            id="test-id",
            data={"status": "Closed", def_data.integration_field: "test-id"},
            system="365",
            object="recommendations",
        )
        issues = [mock_issue]
        api = MagicMock()
        api.config = {"issues": {mock_issue.init_key: {"status": "Open"}}}

        with patch(f"{PATH}.unique_recs", []), patch(f"{PATH}.job_progress"):
            mock_task = MagicMock()
            args = (api, issues, "id", mock_task)

            compare_defender_and_regscale(def_data=def_data, args=args)

            mock_change_status.assert_called_once_with(
                api=api, status="Open", issue=mock_issue.data, rec=def_data, rec_type=mock_issue.init_key
            )

    @patch(f"{PATH}.change_issue_status")
    def test_evaluate_open_issues_close_outdated(self, mock_change_status):
        """Test evaluating open issues - close when no longer in defender"""
        issue = DefenderData(
            id="outdated-id",
            data={"status": "Open", "defender365Id": "outdated-id"},
            system="365",
            object="recommendations",
        )
        defender_data = []  # Empty list means issue not in current recommendations

        with patch(f"{PATH}.job_progress") as mock_job_progress:
            mock_task = MagicMock()
            args = (MagicMock(), defender_data, mock_task)

            evaluate_open_issues(issue=issue, args=args)

            assert issue.analyzed is True
            mock_change_status.assert_called_once_with(
                api=args[0], status="Closed", issue=issue.data, rec=None, rec_type=issue.init_key
            )
            mock_job_progress.update.assert_called_once_with(mock_task, advance=1)

    def test_evaluate_open_issues_skip_closed(self):
        """Test evaluating issues that are already closed"""
        issue = DefenderData(
            id="closed-id",
            data={"status": "Closed", "defender365Id": "closed-id"},
            system="365",
            object="recommendations",
        )
        defender_data = []

        with patch(f"{PATH}.job_progress"), patch(f"{PATH}.change_issue_status") as mock_change_status:
            mock_task = MagicMock()
            args = (MagicMock(), defender_data, mock_task)

            evaluate_open_issues(issue=issue, args=args)

            # Should not call change_issue_status for already closed issues
            mock_change_status.assert_not_called()

    @patch(f"{PATH}.Issue")
    def test_change_issue_status_close_365(self, mock_issue_class):
        """Test changing issue status to closed for Defender 365"""
        api = MagicMock()
        api.config = {**self.config, **{"userId": "test-user"}}

        issue = {"id": 1, "status": "Open"}
        rec = DefenderData(
            id="test-id",
            data={"recommendationName": "Test Recommendation", "severityScore": 8},
            system="365",
            object="recommendations",
        )

        mock_issue_instance = MagicMock()
        mock_issue_class.return_value = mock_issue_instance

        with patch(f"{PATH}.get_current_datetime") as mock_datetime, patch(
            f"{PATH}.format_description"
        ) as mock_format_desc, patch(f"{PATH}.closed", []) as mock_closed:
            mock_datetime.return_value = "2023-01-01 12:00:00"
            mock_format_desc.return_value = "Test description"

            change_issue_status(api=api, status="Closed", issue=issue, rec=rec, rec_type="defender365")

            assert issue["status"] == "Closed"
            assert issue["lastUpdatedById"] == "test-user"
            assert "No longer reported via Microsoft 365 Defender" in issue["description"]
            assert len(mock_closed) == 1
            mock_issue_instance.save.assert_called_once()

    @patch(f"{PATH}.Issue")
    def test_change_issue_status_reopen(self, mock_issue_class):
        """Test changing issue status to reopen"""
        api = MagicMock()
        api.config = {**self.config, **{"userId": "test-user"}}

        issue = {"id": 1, "status": "Closed"}
        rec = DefenderData(
            id="test-id",
            data={"recommendationName": "Test Recommendation", "severityScore": 8},
            system="365",
            object="recommendations",
        )

        mock_issue_instance = MagicMock()
        mock_issue_class.return_value = mock_issue_instance

        with patch(f"{PATH}.get_current_datetime") as mock_datetime, patch(
            f"{PATH}.format_description"
        ) as mock_format_desc, patch(f"{PATH}.updated", []) as mock_updated:
            mock_datetime.return_value = "2023-01-01 12:00:00"
            mock_format_desc.return_value = "Test description"

            change_issue_status(api=api, status="Open", issue=issue, rec=rec, rec_type="defender365")

            assert issue["status"] == "Open"
            assert issue["dateCompleted"] == ""
            assert len(mock_updated) == 1
            mock_issue_instance.save.assert_called_once()

    def test_change_issue_status_no_rec(self):
        """Test changing issue status with no recommendation data"""
        api = MagicMock()
        api.config = {"userId": "test-user"}

        issue = {"id": 1, "status": "Open"}

        with patch(f"{PATH}.get_current_datetime") as mock_datetime:
            mock_datetime.return_value = "2023-01-01 12:00:00"

            result = change_issue_status(api=api, status="Closed", issue=issue, rec=None, rec_type="defender365")

            # Should return early when rec is None
            assert result is None
            assert issue["lastUpdatedById"] == "test-user"
            assert issue["status"] == "Closed"

    @patch(f"{PATH}.issues_to_create")
    def test_prep_issues_for_creation(self, mock_issues_to_create):
        """Test preparing issues for creation"""
        mock_issues_to_create.return_value = []
        def_data = DefenderData(
            id="test-id", data={"id": "test-id", "name": "Test Alert"}, system="365", object="alerts"
        )

        mapping_func = MagicMock()
        mock_issue = MagicMock()
        mapping_func.return_value = mock_issue

        with patch(f"{PATH}.job_progress") as mock_job_progress, patch(
            f"{PATH}.format_description"
        ) as mock_format_desc:
            mock_format_desc.return_value = "Test description"
            mock_task = MagicMock()
            args = (mapping_func, self.config, "id", 1, "issues", mock_task)

            prep_issues_for_creation(def_data=def_data, args=args)

            assert def_data.created is True
            mapping_func.assert_called_once_with(data=def_data, config=self.config, description="Test description")
            assert mock_issue.parentId == 1
            assert mock_issue.parentModule == "issues"
            mock_job_progress.update.assert_called_once_with(mock_task, advance=1)

    def test_map_365_alert_to_issue(self):
        """Test mapping 365 alert to RegScale issue"""
        data = DefenderData(
            id="test-id",
            data={
                "title": "Test Alert",
                "severity": "High",
                "machineId": "machine-123",
                "computerDnsName": "test.example.com",
            },
            system="365",
            object="alerts",
        )
        description = "Test alert description"

        result = map_365_alert_to_issue(data=data, config=self.config, description=description)

        assert isinstance(result, Issue)
        assert result.title == "Test Alert"
        assert result.description == description
        assert result.severityLevel == IssueSeverity.High
        assert result.status == "Open"
        assert "Machine ID:machine-123" in result.assetIdentifier
        assert "test.example.com" in result.assetIdentifier
        assert result.sourceReport == "Microsoft Defender 365 Alert"

    def test_map_365_recommendation_to_issue(self):
        """Test mapping 365 recommendation to RegScale issue"""
        data = DefenderData(
            id="test-id",
            data={"recommendationName": "Test Recommendation", "severityScore": 8, "vendor": "Microsoft"},
            system="365",
            object="recommendations",
        )
        description = "Test recommendation description"

        result = map_365_recommendation_to_issue(data=data, config=self.config, description=description)

        assert isinstance(result, Issue)
        assert result.title == "Test Recommendation"
        assert result.description == description
        assert result.vendorName == "Microsoft"
        assert result.sourceReport == "Microsoft Defender 365 Recommendation"

    def test_map_cloud_alert_to_issue(self):
        """Test mapping cloud alert to RegScale issue"""
        data = DefenderData(
            id="test-id",
            data={
                "id": "alert-id-123",
                "properties": {
                    "productName": "Microsoft Defender",
                    "compromisedEntity": "test-server",
                    "severity": "High",
                    "vendorName": "Microsoft",
                    "resourceIdentifiers": [
                        {"azureResourceId": "/subscriptions/test/resource1"},
                        {"azureResourceId": "/subscriptions/test/resource2"},
                    ],
                    "remediationSteps": ["Step 1", "Step 2"],
                },
            },
            system="cloud",
            object="alerts",
        )
        description = "Test alert description"

        result = map_cloud_alert_to_issue(data=data, config=self.config, description=description)

        assert isinstance(result, Issue)
        assert result.title == "Microsoft Defender Alert - test-server"
        assert result.description == description
        assert result.vendorName == "Microsoft"
        assert "/subscriptions/test/resource1" in result.assetIdentifier
        assert "Step 1" in result.recommendedActions
        assert result.otherIdentifier == "alert-id-123"
        assert result.sourceReport == "Microsoft Defender for Cloud Alert"

    def test_map_cloud_recommendation_to_issue(self):
        """Test mapping cloud recommendation to RegScale issue"""
        data = DefenderData(
            id="test-id",
            data={
                "id": "rec-id-123",
                "properties": {
                    "metadata": {
                        "displayName": "Test Recommendation",
                        "severity": "Medium",
                        "remediationDescription": "Fix this issue",
                    },
                    "resourceDetails": {
                        "ResourceProvider": "Microsoft.Compute",
                        "ResourceType": "virtualMachines",
                        "ResourceName": "test-vm",
                        "Id": "/subscriptions/test/vm1",
                    },
                },
            },
            system="cloud",
            object="recommendations",
        )
        description = "Test recommendation description"

        result = map_cloud_recommendation_to_issue(data=data, config=self.config, description=description)

        assert isinstance(result, Issue)
        assert result.title == "Test Recommendation on Microsoft.Compute/virtualMachines/test-vm"
        assert result.description == description
        assert result.recommendedActions == "Fix this issue"
        assert result.assetIdentifier == "/subscriptions/test/vm1"
        assert result.otherIdentifier == "rec-id-123"
        assert result.manualDetectionId == data.id
        assert "Microsoft Defender for Cloud Recommendation" in result.sourceReport

    @patch(f"{PATH}.File.upload_file_to_regscale")
    @patch(f"{PATH}.save_data_to")
    def test_fetch_save_and_upload_query(self, mock_save_data, mock_upload_file):
        """Test fetching, saving and uploading query results"""
        mock_defender_api = MagicMock(spec=DefenderApi)
        mock_defender_api.fetch_and_run_query.return_value = [{"data": "test"}]
        mock_defender_api.api = MagicMock()

        query = {"name": "test-query"}
        parent_id = 1
        parent_module = "issues"
        no_upload = False

        mock_upload_file.return_value = True

        with patch(f"{PATH}.get_current_datetime") as mock_datetime:
            mock_datetime.return_value = "20230101"

            fetch_save_and_upload_query(
                defender_api=mock_defender_api,
                query=query,
                parent_id=parent_id,
                parent_module=parent_module,
                no_upload=no_upload,
            )

            mock_defender_api.fetch_and_run_query.assert_called_once_with(query=query)
            mock_save_data.assert_called_once()
            mock_upload_file.assert_called_once()

    @patch(f"{PATH}.File.upload_file_to_regscale")
    @patch(f"{PATH}.save_data_to")
    def test_fetch_save_and_upload_query_no_upload(self, mock_save_data, mock_upload_file):
        """Test fetching and saving query results without uploading"""
        mock_defender_api = MagicMock(spec=DefenderApi)
        mock_defender_api.fetch_and_run_query.return_value = [{"data": "test"}]

        query = {"name": "test-query"}
        parent_id = 1
        parent_module = "issues"
        no_upload = True

        with patch(f"{PATH}.get_current_datetime") as mock_datetime:
            mock_datetime.return_value = "20230101"

            fetch_save_and_upload_query(
                defender_api=mock_defender_api,
                query=query,
                parent_id=parent_id,
                parent_module=parent_module,
                no_upload=no_upload,
            )

            mock_defender_api.fetch_and_run_query.assert_called_once_with(query=query)
            mock_save_data.assert_called_once()
            mock_upload_file.assert_not_called()

    def test_prompt_user_for_query_selection_by_name(self):
        """Test prompting user for query selection when name matches"""
        queries = [{"name": "Query1", "id": "1"}, {"name": "Query2", "id": "2"}, {"name": "Query3", "id": "3"}]
        query_name = "query2"  # Case insensitive

        result = prompt_user_for_query_selection(queries=queries, query_name=query_name)

        assert result["name"] == "Query2"
        assert result["id"] == "2"

    @patch(f"{PATH}.click.prompt")
    def test_prompt_user_for_query_selection_interactive(self, mock_click_prompt):
        """Test prompting user for query selection interactively"""
        queries = [{"name": "Query1", "id": "1"}, {"name": "Query2", "id": "2"}]
        mock_click_prompt.return_value = "Query1"

        result = prompt_user_for_query_selection(queries=queries)

        assert result["name"] == "Query1"
        assert result["id"] == "1"
        mock_click_prompt.assert_called_once()

    @patch(f"{PATH}.FlatFileImporter.import_files")
    def test_import_defender_alerts(self, mock_import_files):
        """Test importing defender alerts from CSV"""
        from regscale.models.integration_models.defenderimport import DefenderImport

        folder_path = "/path/to/files"
        regscale_ssp_id = 1
        scan_date = datetime(2023, 1, 1)
        mappings_path = Path("/path/to/mappings")
        disable_mapping = False
        s3_bucket = "test-bucket"
        s3_prefix = "test-prefix"
        aws_profile = "test-profile"
        upload_file = True

        import_defender_alerts(
            folder_path=folder_path,
            regscale_ssp_id=regscale_ssp_id,
            scan_date=scan_date,
            mappings_path=mappings_path,
            disable_mapping=disable_mapping,
            s3_bucket=s3_bucket,
            s3_prefix=s3_prefix,
            aws_profile=aws_profile,
            upload_file=upload_file,
        )

        mock_import_files.assert_called_once_with(
            import_type=DefenderImport,
            import_name="Defender",
            file_types=".csv",
            folder_path=folder_path,
            object_id=regscale_ssp_id,
            scan_date=scan_date,
            mappings_path=mappings_path,
            disable_mapping=disable_mapping,
            s3_bucket=s3_bucket,
            s3_prefix=s3_prefix,
            aws_profile=aws_profile,
            upload_file=upload_file,
        )

    @patch(f"{PATH}.fetch_save_and_upload_query")
    @patch(f"{PATH}.DefenderApi")
    @patch(f"{PATH}.is_valid")
    @patch(f"{PATH}.check_license")
    def test_export_resources_all_queries(self, mock_check_license, mock_is_valid, mock_defender_api, mock_fetch_save):
        """Test exporting all queries from Defender for Cloud"""
        mock_app = MagicMock(spec=Application)
        mock_check_license.return_value = mock_app
        mock_is_valid.return_value = True

        mock_api_instance = MagicMock()
        mock_defender_api.return_value = mock_api_instance
        mock_api_instance.fetch_queries_from_azure.return_value = [{"name": "Query1"}, {"name": "Query2"}]

        export_resources(
            parent_id=1, parent_module="issues", query_name="Test Query", no_upload=False, all_queries=True
        )

        mock_defender_api.assert_called_once_with(system="cloud")
        mock_api_instance.fetch_queries_from_azure.assert_called_once()
        assert mock_fetch_save.call_count == 2

    @patch(f"{PATH}.fetch_save_and_upload_query")
    @patch(f"{PATH}.prompt_user_for_query_selection")
    @patch(f"{PATH}.DefenderApi")
    @patch(f"{PATH}.is_valid")
    @patch(f"{PATH}.check_license")
    def test_export_resources_single_query(
        self, mock_check_license, mock_is_valid, mock_defender_api, mock_prompt, mock_fetch_save
    ):
        """Test exporting single query from Defender for Cloud"""
        mock_app = MagicMock(spec=Application)
        mock_check_license.return_value = mock_app
        mock_is_valid.return_value = True

        mock_api_instance = MagicMock()
        mock_defender_api.return_value = mock_api_instance
        mock_api_instance.fetch_queries_from_azure.return_value = [{"name": "Query1"}]

        mock_prompt.return_value = {"name": "Query1"}

        export_resources(parent_id=1, parent_module="issues", query_name="Query1", no_upload=False, all_queries=False)

        mock_prompt.assert_called_once_with(queries=[{"name": "Query1"}], query_name="Query1")
        mock_fetch_save.assert_called_once()

    @patch(f"{PATH}.logger")
    @patch(f"{PATH}.DefenderApi")
    @patch(f"{PATH}.is_valid")
    @patch(f"{PATH}.check_license")
    def test_export_resources_no_queries(self, mock_check_license, mock_is_valid, mock_defender_api, mock_logger):
        """Test exporting when no queries exist"""
        mock_app = MagicMock(spec=Application)
        mock_check_license.return_value = mock_app
        mock_is_valid.return_value = True

        mock_api_instance = MagicMock()
        mock_defender_api.return_value = mock_api_instance
        mock_api_instance.fetch_queries_from_azure.return_value = []

        export_resources(parent_id=1, parent_module="issues", query_name="None", no_upload=False, all_queries=True)

        mock_logger.warning.assert_called_once_with(
            "No saved queries found in Azure. Please create at least one query to use this export function."
        )

    @patch(f"{PATH}.error_and_exit")
    @patch(f"{PATH}.is_valid")
    @patch(f"{PATH}.check_license")
    def test_export_resources_invalid_login(self, mock_check_license, mock_is_valid, mock_error_exit):
        """Test exporting with invalid RegScale login"""
        mock_app = MagicMock(spec=Application)
        mock_check_license.return_value = mock_app
        mock_is_valid.return_value = False

        export_resources(
            parent_id=1, parent_module="issues", query_name="Invalid Login", no_upload=False, all_queries=True
        )

        mock_error_exit.assert_called_once_with("Login Invalid RegScale Credentials, please login for a new token.")

    # ==============================
    # NEW TESTS FOR ENTRA FUNCTIONALITY
    # ==============================

    @patch(f"{PATH}.check_license", return_value=MagicMock(spec=Application))
    @patch(f"{PATH}.DefenderApi")
    def test_authenticate_entra(self, mock_defender_api, mock_check_license):
        """Test authenticating with Azure Entra"""
        mock_api_instance = MagicMock()
        mock_defender_api.return_value = mock_api_instance

        authenticate(system="entra")

        mock_check_license.assert_called_once()
        mock_defender_api.assert_called_once_with(system="entra")
        mock_api_instance.get_token.assert_called_once()

    @patch(f"{PATH}.upload_evidence_files")
    @patch(f"{PATH}.collect_specific_evidence_type")
    @patch(f"{PATH}.DefenderApi")
    @patch(f"{PATH}.is_valid")
    @patch(f"{PATH}.Api")
    @patch(f"{PATH}.check_license")
    def test_collect_and_upload_entra_evidence_all(
        self,
        mock_check_license,
        mock_api_class,
        mock_is_valid,
        mock_defender_api,
        mock_collect_specific,
        mock_upload_evidence,
    ):
        """Test collect_and_upload_entra_evidence with all evidence types"""
        mock_app = MagicMock(spec=Application)
        mock_check_license.return_value = mock_app
        mock_is_valid.return_value = True

        mock_api = MagicMock()
        mock_api_class.return_value = mock_api

        mock_defender_api_instance = MagicMock()
        mock_defender_api.return_value = mock_defender_api_instance
        mock_defender_api_instance.collect_all_entra_evidence.return_value = {
            "users": [Path("/test/users.csv")],
            "sign_in_logs": [Path("/test/logs.csv")],
        }

        collect_and_upload_entra_evidence(parent_id=1, parent_module="securityplans", days_back=30, evidence_type="all")

        mock_defender_api.assert_called_once_with(system="entra")
        mock_defender_api_instance.collect_all_entra_evidence.assert_called_once_with(days_back=30)
        mock_upload_evidence.assert_called_once()

    @patch(f"{PATH}.upload_evidence_files")
    @patch(f"{PATH}.collect_specific_evidence_type")
    @patch(f"{PATH}.DefenderApi")
    @patch(f"{PATH}.is_valid")
    @patch(f"{PATH}.Api")
    @patch(f"{PATH}.check_license")
    def test_collect_and_upload_entra_evidence_specific_type(
        self,
        mock_check_license,
        mock_api_class,
        mock_is_valid,
        mock_defender_api,
        mock_collect_specific,
        mock_upload_evidence,
    ):
        """Test collect_and_upload_entra_evidence with specific evidence type"""
        mock_app = MagicMock(spec=Application)
        mock_check_license.return_value = mock_app
        mock_is_valid.return_value = True

        mock_api = MagicMock()
        mock_api_class.return_value = mock_api

        mock_defender_api_instance = MagicMock()
        mock_defender_api.return_value = mock_defender_api_instance

        mock_collect_specific.return_value = {"users": [Path("/test/users.csv")]}

        collect_and_upload_entra_evidence(
            parent_id=1, parent_module="securityplans", days_back=30, evidence_type="users_groups"
        )

        mock_defender_api.assert_called_once_with(system="entra")
        mock_collect_specific.assert_called_once_with(mock_defender_api_instance, "users_groups", 30)
        mock_upload_evidence.assert_called_once()

    @patch(f"{PATH}.error_and_exit")
    @patch(f"{PATH}.is_valid")
    @patch(f"{PATH}.Api")
    @patch(f"{PATH}.check_license")
    def test_collect_and_upload_entra_evidence_invalid_login(
        self, mock_check_license, mock_api_class, mock_is_valid, mock_error_exit
    ):
        """Test collect_and_upload_entra_evidence with invalid login"""
        mock_error_exit.side_effect = SystemExit(1)
        mock_app = MagicMock(spec=Application)
        mock_check_license.return_value = mock_app
        mock_is_valid.return_value = False

        with pytest.raises(SystemExit):
            collect_and_upload_entra_evidence(
                parent_id=1, parent_module="securityplans", days_back=30, evidence_type="all"
            )

        mock_error_exit.assert_called_once_with("Login Invalid RegScale Credentials, please login for a new token.")

    @patch(f"{PATH}.error_and_exit")
    @patch(f"{PATH}.DefenderApi")
    @patch(f"{PATH}.is_valid")
    @patch(f"{PATH}.Api")
    @patch(f"{PATH}.check_license")
    def test_collect_and_upload_entra_evidence_with_exception(
        self, mock_check_license, mock_api_class, mock_is_valid, mock_defender_api, mock_error_exit
    ):
        """Test collect_and_upload_entra_evidence with exception"""
        mock_error_exit.side_effect = SystemExit(1)
        mock_app = MagicMock(spec=Application)
        mock_check_license.return_value = mock_app
        mock_is_valid.return_value = True

        mock_api = MagicMock()
        mock_api_class.return_value = mock_api

        mock_defender_api_instance = MagicMock()
        mock_defender_api.return_value = mock_defender_api_instance
        mock_defender_api_instance.collect_all_entra_evidence.side_effect = Exception("API Error")

        with pytest.raises(SystemExit):
            collect_and_upload_entra_evidence(
                parent_id=1, parent_module="securityplans", days_back=30, evidence_type="all"
            )

        mock_error_exit.assert_called_once_with("Error collecting Azure Entra evidence: API Error")

    def test_collect_specific_evidence_type_users_groups(self):
        """Test collect_specific_evidence_type for users_groups"""
        mock_defender_api = MagicMock()
        mock_defender_api.get_and_save_entra_evidence.return_value = [Path("/test/file.csv")]

        result = collect_specific_evidence_type(mock_defender_api, "users_groups", 30)

        expected_calls = [
            ("users",),
            ("guest_users",),
            ("groups_and_members",),
            ("security_groups",),
        ]
        actual_calls = [call[0] for call in mock_defender_api.get_and_save_entra_evidence.call_args_list]
        for expected_call in expected_calls:
            assert expected_call in actual_calls

        assert "users" in result
        assert "guest_users" in result
        assert "security_groups" in result
        assert "groups_and_members" in result

    def test_collect_specific_evidence_type_rbac_pim(self):
        """Test collect_specific_evidence_type for rbac_pim"""
        mock_defender_api = MagicMock()
        mock_defender_api.get_and_save_entra_evidence.return_value = [Path("/test/file.csv")]

        result = collect_specific_evidence_type(mock_defender_api, "rbac_pim", 30)

        expected_calls = [
            ("role_assignments",),
            ("role_definitions",),
            ("pim_assignments",),
            ("pim_eligibility",),
        ]
        actual_calls = [call[0] for call in mock_defender_api.get_and_save_entra_evidence.call_args_list]
        for expected_call in expected_calls:
            assert expected_call in actual_calls

        assert "role_assignments" in result
        assert "role_definitions" in result
        assert "pim_assignments" in result
        assert "pim_eligibility" in result

    def test_collect_specific_evidence_type_audit_logs(self):
        """Test collect_specific_evidence_type for audit_logs"""
        mock_defender_api = MagicMock()
        mock_defender_api.get_and_save_entra_evidence.return_value = [Path("/test/file.csv")]

        result = collect_specific_evidence_type(mock_defender_api, "audit_logs", 30)

        # Verify start_date parameter is passed for audit log endpoints
        expected_calls_with_start_date = [
            "sign_in_logs",
            "directory_audits",
            "provisioning_logs",
        ]
        for call in mock_defender_api.get_and_save_entra_evidence.call_args_list:
            endpoint_key = call[0][0]
            if endpoint_key in expected_calls_with_start_date:
                assert "start_date" in call[1]

        assert "sign_in_logs" in result
        assert "directory_audits" in result
        assert "provisioning_logs" in result

    def test_collect_specific_evidence_type_access_reviews(self):
        """Test collect_specific_evidence_type for access_reviews"""
        mock_defender_api = MagicMock()
        mock_defender_api.collect_entra_access_reviews.return_value = [Path("/test/file.csv")]

        result = collect_specific_evidence_type(mock_defender_api, "access_reviews", 30)

        mock_defender_api.collect_entra_access_reviews.assert_called_once()
        assert "access_review_definitions" in result

    @patch("regscale.models.ControlImplementation.get_list_by_parent")
    def test_get_control_implementations_map_success(self, mock_get_list):
        """Test get_control_implementations_map with successful result"""
        from regscale.integrations.commercial.microsoft_defender.defender import get_control_implementations_map

        # Mock control implementations
        mock_controls = [
            {"id": 1, "controlId": "AC-1"},
            {"id": 2, "controlId": "AC-2"},
            {"id": 3, "controlId": "IA-2"},
        ]
        mock_get_list.return_value = mock_controls

        result = get_control_implementations_map(parent_id=1, parent_module="securityplans")

        mock_get_list.assert_called_once_with(1, "securityplans")
        expected = {"AC-1": 1, "AC-2": 2, "IA-2": 3}
        assert result == expected

    @patch("regscale.models.ControlImplementation.get_list_by_parent")
    def test_get_control_implementations_map_empty(self, mock_get_list):
        """Test get_control_implementations_map with empty result"""
        from regscale.integrations.commercial.microsoft_defender.defender import get_control_implementations_map

        mock_get_list.return_value = []

        result = get_control_implementations_map(parent_id=1, parent_module="securityplans")

        assert result == {}

    @patch("regscale.models.ControlImplementation.get_list_by_parent")
    def test_get_control_implementations_map_with_exception(self, mock_get_list):
        """Test get_control_implementations_map with exception"""
        from regscale.integrations.commercial.microsoft_defender.defender import get_control_implementations_map

        mock_get_list.side_effect = Exception("Database error")

        result = get_control_implementations_map(parent_id=1, parent_module="securityplans")

        assert result == {}

    @patch(f"{PATH}.File.upload_file_to_regscale")
    def test_upload_evidence_to_controls_success(self, mock_upload_file):
        """Test upload_evidence_to_controls with successful uploads"""
        from regscale.integrations.commercial.microsoft_defender.defender import upload_evidence_to_controls

        mock_upload_file.return_value = True
        evidence_files = [Path("/test/users.csv"), Path("/test/logs.csv")]
        control_map = {"AC-1": 1, "AC-2": 2, "IA-2": 3}
        mock_api = MagicMock()

        result = upload_evidence_to_controls(
            evidence_key="users",
            evidence_file_list=evidence_files,
            control_implementations_map=control_map,
            api=mock_api,
        )

        # For users evidence, it should upload to AC-1, AC-2, and other user-related controls
        # Each file should be uploaded to multiple controls
        assert mock_upload_file.call_count > 0
        assert result > 0

    @patch(f"{PATH}.File.upload_file_to_regscale")
    def test_upload_evidence_to_controls_no_mapping(self, mock_upload_file):
        """Test upload_evidence_to_controls with unknown evidence key"""
        from regscale.integrations.commercial.microsoft_defender.defender import upload_evidence_to_controls

        evidence_files = [Path("/test/unknown.csv")]
        control_map = {"AC-1": 1}
        mock_api = MagicMock()

        result = upload_evidence_to_controls(
            evidence_key="unknown_evidence",
            evidence_file_list=evidence_files,
            control_implementations_map=control_map,
            api=mock_api,
        )

        mock_upload_file.assert_not_called()
        assert result == 0

    @patch(f"{PATH}.File.upload_file_to_regscale")
    def test_upload_evidence_to_controls_upload_failure(self, mock_upload_file):
        """Test upload_evidence_to_controls with upload failures"""
        from regscale.integrations.commercial.microsoft_defender.defender import upload_evidence_to_controls

        mock_upload_file.return_value = False
        evidence_files = [Path("/test/users.csv")]
        control_map = {"AC-1": 1, "AC-2": 2}
        mock_api = MagicMock()

        result = upload_evidence_to_controls(
            evidence_key="users",
            evidence_file_list=evidence_files,
            control_implementations_map=control_map,
            api=mock_api,
        )

        assert mock_upload_file.call_count > 0
        assert result == 0

    @patch(f"{PATH}.get_control_implementations_map")
    @patch(f"{PATH}.upload_evidence_to_controls")
    def test_upload_evidence_files_success(self, mock_upload_to_controls, mock_get_control_map):
        """Test upload_evidence_files with successful uploads"""
        from regscale.integrations.commercial.microsoft_defender.defender import upload_evidence_files

        mock_get_control_map.return_value = {"AC-1": 1, "AC-2": 2}
        mock_upload_to_controls.return_value = 3

        evidence_data = {
            "users": [Path("/test/users.csv")],
            "sign_in_logs": [Path("/test/logs.csv")],
        }
        mock_api = MagicMock()

        upload_evidence_files(
            evidence_data=evidence_data, parent_id=1, parent_module="securityplans", api=mock_api, evidence_type="all"
        )

        mock_get_control_map.assert_called_once_with(1, "securityplans")
        assert mock_upload_to_controls.call_count == 2  # Called for each evidence type

    @patch(f"{PATH}.get_control_implementations_map")
    def test_upload_evidence_files_no_controls(self, mock_get_control_map):
        """Test upload_evidence_files with no control implementations"""
        from regscale.integrations.commercial.microsoft_defender.defender import upload_evidence_files

        mock_get_control_map.return_value = {}

        evidence_data = {"users": [Path("/test/users.csv")]}
        mock_api = MagicMock()

        # Should return early when no control implementations are found
        upload_evidence_files(
            evidence_data=evidence_data, parent_id=1, parent_module="securityplans", api=mock_api, evidence_type="all"
        )

        mock_get_control_map.assert_called_once()

    @patch(f"{PATH}.console")
    def test_show_entra_mappings_all(self, mock_console):
        """Test show_entra_mappings displaying all mappings"""
        from click.testing import CliRunner
        from regscale.integrations.commercial.microsoft_defender.defender import show_entra_mappings

        # Mock the console.print calls
        mock_console.print.return_value = None

        # Use Click's test runner to invoke the command
        runner = CliRunner()
        result = runner.invoke(show_entra_mappings, ["--evidence_type", "all"])

        # Verify the command executed successfully
        assert result.exit_code == 0
        # Verify console.print was called (table creation and final message)
        assert mock_console.print.call_count == 2

    @patch(f"{PATH}.console")
    def test_show_entra_mappings_specific_type(self, mock_console):
        """Test show_entra_mappings displaying specific type"""
        from click.testing import CliRunner
        from regscale.integrations.commercial.microsoft_defender.defender import show_entra_mappings

        mock_console.print.return_value = None

        # Use Click's test runner to invoke the command
        runner = CliRunner()
        result = runner.invoke(show_entra_mappings, ["--evidence_type", "users_groups"])

        # Verify the command executed successfully
        assert result.exit_code == 0
        # Verify console.print was called
        assert mock_console.print.call_count == 2

    # ==============================
    # COMPREHENSIVE ENTRA FUNCTIONALITY TESTS
    # ==============================

    @patch(f"{PATH}.check_license", return_value=MagicMock(spec=Application))
    @patch(f"{PATH}.DefenderApi")
    def test_authenticate_entra(self, mock_defender_api, mock_check_license):
        """Test authenticating with Azure Entra"""
        mock_api_instance = MagicMock()
        mock_defender_api.return_value = mock_api_instance

        authenticate(system="entra")

        mock_check_license.assert_called_once()
        mock_defender_api.assert_called_once_with(system="entra")
        mock_api_instance.get_token.assert_called_once()

    @patch(f"{PATH}.error_and_exit")
    @patch(f"{PATH}.is_valid")
    @patch(f"{PATH}.check_license")
    @patch(f"{PATH}.Api")
    @patch(f"{PATH}.DefenderApi")
    def test_collect_and_upload_entra_evidence_invalid_auth(
        self, mock_defender_api, mock_api, mock_check_license, mock_is_valid, mock_error_exit
    ):
        """Test collect_and_upload_entra_evidence with invalid authentication"""
        mock_error_exit.side_effect = SystemExit(1)
        mock_check_license.return_value = MagicMock()
        mock_is_valid.return_value = False

        with pytest.raises(SystemExit):
            collect_and_upload_entra_evidence(parent_id=1, parent_module="securityplans")

        mock_error_exit.assert_called_once()

    @patch(f"{PATH}.upload_evidence_files")
    @patch(f"{PATH}.collect_specific_evidence_type")
    @patch(f"{PATH}.is_valid")
    @patch(f"{PATH}.check_license")
    @patch(f"{PATH}.Api")
    @patch(f"{PATH}.DefenderApi")
    def test_collect_and_upload_entra_evidence_specific_type(
        self, mock_defender_api, mock_api, mock_check_license, mock_is_valid, mock_collect_specific, mock_upload
    ):
        """Test collect_and_upload_entra_evidence with specific evidence type"""
        # Setup mocks
        mock_check_license.return_value = MagicMock()
        mock_is_valid.return_value = True
        mock_collect_specific.return_value = {"users": [Path("/test/users.csv")]}
        mock_upload.return_value = None

        # Call function with specific evidence type
        collect_and_upload_entra_evidence(
            parent_id=1, parent_module="securityplans", days_back=30, evidence_type="users_groups"
        )

        # Verify specific evidence collection was called
        mock_collect_specific.assert_called_once_with(mock_defender_api.return_value, "users_groups", 30)
        mock_upload.assert_called_once()

    @patch(f"{PATH}.upload_evidence_files")
    @patch(f"{PATH}.is_valid")
    @patch(f"{PATH}.check_license")
    @patch(f"{PATH}.Api")
    @patch(f"{PATH}.DefenderApi")
    def test_collect_and_upload_entra_evidence_all(
        self, mock_defender_api, mock_api, mock_check_license, mock_is_valid, mock_upload
    ):
        """Test collect_and_upload_entra_evidence collecting all evidence"""
        # Setup mocks
        mock_check_license.return_value = MagicMock()
        mock_is_valid.return_value = True
        mock_api_instance = MagicMock()
        mock_defender_api.return_value = mock_api_instance
        mock_api_instance.collect_all_entra_evidence.return_value = {
            "users": [Path("/test/users.csv")],
            "sign_in_logs": [Path("/test/signin.csv")],
        }
        mock_upload.return_value = None

        # Call function with evidence_type="all"
        collect_and_upload_entra_evidence(parent_id=1, parent_module="securityplans", evidence_type="all")

        # Verify all evidence collection was called
        mock_api_instance.collect_all_entra_evidence.assert_called_once_with(days_back=30)
        mock_upload.assert_called_once()

    @patch(f"{PATH}.error_and_exit")
    @patch(f"{PATH}.is_valid")
    @patch(f"{PATH}.check_license")
    @patch(f"{PATH}.Api")
    @patch(f"{PATH}.DefenderApi")
    def test_collect_and_upload_entra_evidence_exception(
        self, mock_defender_api, mock_api, mock_check_license, mock_is_valid, mock_error_exit
    ):
        """Test collect_and_upload_entra_evidence handles exceptions"""
        mock_error_exit.side_effect = SystemExit(1)
        mock_check_license.return_value = MagicMock()
        mock_is_valid.return_value = True
        mock_api_instance = MagicMock()
        mock_defender_api.return_value = mock_api_instance
        mock_api_instance.collect_all_entra_evidence.side_effect = Exception("API Error")

        with pytest.raises(SystemExit):
            collect_and_upload_entra_evidence(parent_id=1, parent_module="securityplans")

        mock_error_exit.assert_called_once()
        error_message = mock_error_exit.call_args[0][0]
        assert "Error collecting Azure Entra evidence" in error_message

    def test_collect_specific_evidence_type_users_groups(self):
        """Test collect_specific_evidence_type for users_groups"""
        mock_defender_api = MagicMock()
        mock_defender_api.get_and_save_entra_evidence.return_value = [Path("/test/file.csv")]

        result = collect_specific_evidence_type(mock_defender_api, "users_groups", 30)

        # Verify all expected user/group endpoints were called
        expected_calls = ["users", "guest_users", "groups_and_members", "security_groups"]
        assert len(mock_defender_api.get_and_save_entra_evidence.call_args_list) == len(expected_calls)

        for call in mock_defender_api.get_and_save_entra_evidence.call_args_list:
            endpoint = call[0][0]  # First positional argument
            assert endpoint in expected_calls

        # Verify all evidence types are in result
        for expected_type in expected_calls:
            assert expected_type in result

    def test_collect_specific_evidence_type_rbac_pim(self):
        """Test collect_specific_evidence_type for rbac_pim"""
        mock_defender_api = MagicMock()
        mock_defender_api.get_and_save_entra_evidence.return_value = [Path("/test/file.csv")]

        result = collect_specific_evidence_type(mock_defender_api, "rbac_pim", 30)

        expected_calls = ["role_assignments", "role_definitions", "pim_assignments", "pim_eligibility"]
        assert len(mock_defender_api.get_and_save_entra_evidence.call_args_list) == len(expected_calls)

        for expected_type in expected_calls:
            assert expected_type in result

    def test_collect_specific_evidence_type_conditional_access(self):
        """Test collect_specific_evidence_type for conditional_access"""
        mock_defender_api = MagicMock()
        mock_defender_api.get_and_save_entra_evidence.return_value = [Path("/test/file.csv")]

        result = collect_specific_evidence_type(mock_defender_api, "conditional_access", 30)

        mock_defender_api.get_and_save_entra_evidence.assert_called_once_with("conditional_access")
        assert "conditional_access" in result

    def test_collect_specific_evidence_type_authentication(self):
        """Test collect_specific_evidence_type for authentication"""
        mock_defender_api = MagicMock()
        mock_defender_api.get_and_save_entra_evidence.return_value = [Path("/test/file.csv")]

        result = collect_specific_evidence_type(mock_defender_api, "authentication", 30)

        expected_calls = ["auth_methods_policy", "user_mfa_registration", "mfa_registered_users"]
        assert len(mock_defender_api.get_and_save_entra_evidence.call_args_list) == len(expected_calls)

        for expected_type in expected_calls:
            assert expected_type in result

    def test_collect_specific_evidence_type_audit_logs(self):
        """Test collect_specific_evidence_type for audit_logs with start_date"""
        mock_defender_api = MagicMock()
        mock_defender_api.get_and_save_entra_evidence.return_value = [Path("/test/file.csv")]

        result = collect_specific_evidence_type(mock_defender_api, "audit_logs", 60)

        expected_calls = ["sign_in_logs", "directory_audits", "provisioning_logs"]
        assert len(mock_defender_api.get_and_save_entra_evidence.call_args_list) == len(expected_calls)

        # Verify start_date parameter was passed for audit logs
        for call in mock_defender_api.get_and_save_entra_evidence.call_args_list:
            kwargs = call[1]  # Keyword arguments
            assert "start_date" in kwargs
            # Verify it's a valid date string for 60 days back
            start_date = kwargs["start_date"]
            assert start_date.endswith("T00:00:00Z")

        for expected_type in expected_calls:
            assert expected_type in result

    def test_collect_specific_evidence_type_access_reviews(self):
        """Test collect_specific_evidence_type for access_reviews"""
        mock_defender_api = MagicMock()
        mock_defender_api.collect_entra_access_reviews.return_value = [Path("/test/file.csv")]

        result = collect_specific_evidence_type(mock_defender_api, "access_reviews", 30)

        mock_defender_api.collect_entra_access_reviews.assert_called_once()
        assert "access_review_definitions" in result

    @patch("regscale.models.ControlImplementation")
    def test_get_control_implementations_map_success(self, mock_control_impl):
        """Test get_control_implementations_map with successful retrieval"""
        from regscale.integrations.commercial.microsoft_defender.defender import get_control_implementations_map

        # Mock control implementations
        mock_controls = [
            {"id": 1, "controlId": "AC-2"},
            {"id": 2, "controlId": "AU-3"},
            {"id": 3, "controlId": "IA-2"},
        ]
        mock_control_impl.get_list_by_parent.return_value = mock_controls

        result = get_control_implementations_map(parent_id=1, parent_module="securityplans")

        expected = {"AC-2": 1, "AU-3": 2, "IA-2": 3}
        assert result == expected
        mock_control_impl.get_list_by_parent.assert_called_once_with(1, "securityplans")

    @patch("regscale.models.ControlImplementation")
    def test_get_control_implementations_map_empty(self, mock_control_impl):
        """Test get_control_implementations_map with no control implementations"""
        from regscale.integrations.commercial.microsoft_defender.defender import get_control_implementations_map

        mock_control_impl.get_list_by_parent.return_value = []

        result = get_control_implementations_map(parent_id=1, parent_module="securityplans")

        assert result == {}

    @patch("regscale.models.ControlImplementation")
    def test_get_control_implementations_map_exception(self, mock_control_impl):
        """Test get_control_implementations_map handles exceptions"""
        from regscale.integrations.commercial.microsoft_defender.defender import get_control_implementations_map

        mock_control_impl.get_list_by_parent.side_effect = Exception("API Error")

        result = get_control_implementations_map(parent_id=1, parent_module="securityplans")

        assert result == {}

    @patch(f"{PATH}.File.upload_file_to_regscale")
    def test_upload_evidence_to_controls_success(self, mock_upload):
        """Test upload_evidence_to_controls with successful uploads"""
        from regscale.integrations.commercial.microsoft_defender.defender import upload_evidence_to_controls

        mock_upload.return_value = True
        evidence_files = [Path("/test/users.csv"), Path("/test/users2.csv")]
        # users evidence maps to: [AC_1, AC_2, AC_2_1, AC_2_3, AC_2_5, AC_2_7, AC_2_12]
        control_map = {"AC-1": 1, "AC-2": 2, "AC-2(1)": 3, "AC-2(3)": 4, "AC-2(5)": 5, "AC-2(7)": 6, "AC-2(12)": 7}
        api = MagicMock()

        result = upload_evidence_to_controls("users", evidence_files, control_map, api)

        # users evidence maps to 7 controls × 2 files = 14 expected uploads
        assert result == 14
        assert mock_upload.call_count == 14

    @patch(f"{PATH}.File.upload_file_to_regscale")
    def test_upload_evidence_to_controls_no_mapping(self, mock_upload):
        """Test upload_evidence_to_controls with no control mapping"""
        from regscale.integrations.commercial.microsoft_defender.defender import upload_evidence_to_controls

        evidence_files = [Path("/test/unknown.csv")]
        control_map = {"AC-2": 1}
        api = MagicMock()

        result = upload_evidence_to_controls("unknown_evidence", evidence_files, control_map, api)

        assert result == 0
        mock_upload.assert_not_called()

    @patch(f"{PATH}.File.upload_file_to_regscale")
    def test_upload_evidence_to_controls_partial_failure(self, mock_upload):
        """Test upload_evidence_to_controls with partial upload failures"""
        from regscale.integrations.commercial.microsoft_defender.defender import upload_evidence_to_controls

        # Mock alternating success/failure
        mock_upload.side_effect = [True, False, True, False, True, False, True]
        evidence_files = [Path("/test/users.csv")]
        control_map = {"AC-2": 1, "AC-2(1)": 2, "AC-2(3)": 3, "AC-2(5)": 4, "AC-2(7)": 5, "AC-2(12)": 6, "AC-1": 7}
        api = MagicMock()

        result = upload_evidence_to_controls("users", evidence_files, control_map, api)

        # Should return count of successful uploads (4 out of 7)
        assert result == 4

    @patch(f"{PATH}.upload_evidence_to_controls")
    @patch(f"{PATH}.get_control_implementations_map")
    @patch(f"{PATH}.Path")
    def test_upload_evidence_files_success(self, mock_path, mock_get_control_map, mock_upload_evidence):
        """Test upload_evidence_files with successful uploads"""
        from regscale.integrations.commercial.microsoft_defender.defender import upload_evidence_files

        mock_get_control_map.return_value = {"AC-2": 1, "AU-3": 2}
        mock_upload_evidence.return_value = 5
        mock_path.return_value.mkdir.return_value = None

        evidence_data = {
            "users": [Path("/test/users.csv")],
            "sign_in_logs": [Path("/test/signin.csv")],
        }
        api = MagicMock()

        upload_evidence_files(evidence_data, 1, "securityplans", api, "all")

        # Verify evidence upload was called for each evidence type
        assert mock_upload_evidence.call_count == 2
        mock_get_control_map.assert_called_once_with(1, "securityplans")

    @patch(f"{PATH}.get_control_implementations_map")
    def test_upload_evidence_files_no_control_implementations(self, mock_get_control_map):
        """Test upload_evidence_files when no control implementations exist"""
        from regscale.integrations.commercial.microsoft_defender.defender import upload_evidence_files

        mock_get_control_map.return_value = {}

        evidence_data = {"users": [Path("/test/users.csv")]}
        api = MagicMock()

        # Should return early when no control implementations are found
        upload_evidence_files(evidence_data, 1, "securityplans", api, "all")

        mock_get_control_map.assert_called_once()

    @patch(f"{PATH}.upload_evidence_to_controls")
    @patch(f"{PATH}.get_control_implementations_map")
    @patch(f"{PATH}.Path")
    def test_upload_evidence_files_empty_evidence_lists(self, mock_path, mock_get_control_map, mock_upload_evidence):
        """Test upload_evidence_files handles empty evidence lists"""
        from regscale.integrations.commercial.microsoft_defender.defender import upload_evidence_files

        mock_get_control_map.return_value = {"AC-2": 1}
        mock_path.return_value.mkdir.return_value = None

        evidence_data = {
            "users": [],  # Empty list
            "guest_users": [Path("/test/guests.csv")],  # Non-empty list
        }
        api = MagicMock()

        upload_evidence_files(evidence_data, 1, "securityplans", api, "users_groups")

        # Should only call upload_evidence_to_controls for non-empty evidence lists
        mock_upload_evidence.assert_called_once()

    @staticmethod
    def teardown_class(cls):
        """Remove test data"""
        with contextlib.suppress(FileNotFoundError):
            shutil.rmtree("./artifacts")
