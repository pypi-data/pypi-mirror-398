import unittest
from datetime import datetime
from unittest.mock import ANY, call, patch, MagicMock

import pytest

from regscale.integrations.commercial.sqlserver import (
    build_connection_string,
    create_and_save_assessment,
    calculate_finish_date,
    create_assessment_object,
    upload_files_to_assessment,
)


@pytest.skip(reason="Manual test", allow_module_level=True)
class TestSqlServer(unittest.TestCase):
    @patch("regscale.core.app.utils.app_utils.check_license")
    @patch("regscale.core.app.utils.regscale_utils.verify_provided_module")
    @patch("regscale.integrations.commercial.sqlserver.build_connection_string")
    @patch("pyodbc.connect")
    @patch("pandas.DataFrame.from_records")
    @patch("os.makedirs")
    @patch("regscale.integrations.commercial.sqlserver.create_and_save_assessment")
    @patch("regscale.core.app.internal.workflow.create_regscale_workflow_from_template")
    def test_generate_and_save_report(
        self,
        mock_check_license,
        mock_verify_provided_module,
        mock_build_connection_string,
        mock_pyodbc_connect,
        mock_df_from_records,
        mock_os_makedirs,
        mock_create_and_save_assessment,
        mock_create_regscale_workflow_from_template,
    ):
        # Add your assertions here
        pass

    def test_build_connection_string_with_username_and_password(self):
        result = build_connection_string("server", "database", 1433, "username", "password")
        expected = (
            r"DRIVER={ODBC Driver 17 for SQL Server};"
            r"SERVER=server;"
            r"DATABASE=database;"
            r"PORT=port;"
            r"UID=username;"
            r"PWD=password;"
            r"TrustServerCertificate=yes;"
            r"TIMEOUT=30;"
        )
        self.assertEqual(result, expected)

    def test_build_connection_string_with_trusted_connection(self):
        result = build_connection_string("server", "database", 1433, None, None)
        expected = (
            r"DRIVER={ODBC Driver 17 for SQL Server};"
            r"SERVER=server;"
            r"DATABASE=database;"
            r"PORT=port;"
            r"Trusted_Connection=yes;"
        )
        self.assertEqual(result, expected)

    @patch("regscale.integrations.commercial.sqlserver.calculate_finish_date")
    @patch("regscale.integrations.commercial.sqlserver.get_current_datetime")
    @patch("regscale.integrations.commercial.sqlserver.Assessment")
    def test_create_assessment_object(self, mock_assessment, mock_get_current_datetime, mock_calculate_finish_date):
        mock_app = MagicMock()
        mock_app.config = {
            "userId": "904efb0a-c3ee-4819-ba4e-df1f4554d843",
            "assessmentDays": 7,
        }
        mock_get_current_datetime.return_value = "2023-07-23T12:00:00"
        mock_calculate_finish_date.return_value = "2023-08-23T12:00:00"

        create_assessment_object(
            app=mock_app,
            report="report",
            regscale_id=1,
            regscale_module="module",
            title="title",
            description="description",
        )

        mock_assessment.assert_called_once_with(
            leadAssessorId=mock_app.config["userId"],
            title="title",
            assessmentType="Control Testing",
            plannedStart=mock_get_current_datetime.return_value,
            plannedFinish=mock_calculate_finish_date.return_value,
            assessmentReport="report",
            assessmentPlan="description",
            createdById=mock_app.config["userId"],
            dateCreated=mock_get_current_datetime.return_value,
            lastUpdatedById=mock_app.config["userId"],
            dateLastUpdated=mock_get_current_datetime.return_value,
            parentModule="module",
            parentId=1,
            status="Scheduled",
        )

    @patch("regscale.integrations.commercial.sqlserver.File.upload_file_to_regscale")
    @patch("regscale.integrations.commercial.sqlserver.job_progress")
    def test_upload_files_to_assessment(self, mock_job_progress, mock_upload_file_to_regscale):
        mock_api = MagicMock()
        mock_upload_file_to_regscale.return_value = True
        mock_job_progress.add_task.return_value = "task_id"

        upload_files_to_assessment(api=mock_api, assessment_id=1, files=["file1", "file2"])

        mock_job_progress.add_task.assert_called_once_with(
            "[#0866b4]Uploading files to the new RegScale Assessment...", total=2
        )
        mock_upload_file_to_regscale.assert_has_calls(
            [
                call(
                    file_name="file1",
                    parent_id=1,
                    parent_module="assessments",
                    api=mock_api,
                ),
                call(
                    file_name="file2",
                    parent_id=1,
                    parent_module="assessments",
                    api=mock_api,
                ),
            ]
        )
        mock_job_progress.update.assert_has_calls(
            [
                call("task_id", advance=1),
                call("task_id", advance=1),
            ]
        )

    @patch("regscale.integrations.commercial.sqlserver.upload_files_to_assessment")
    @patch("regscale.integrations.commercial.sqlserver.create_assessment_object")
    @patch("regscale.integrations.commercial.sqlserver.job_progress")
    @patch("regscale.integrations.commercial.sqlserver.Api")
    def test_create_and_save_assessment(
        self,
        mock_api_object,
        mock_job_progress,
        mock_create_assessment_object,
        mock_upload_files_to_assessment,
    ):
        mock_api = MagicMock()
        mock_api_object.return_value = mock_api
        mock_assessment = MagicMock()
        mock_assessment.id = 1
        mock_assessment.insert_assessment.return_value = mock_assessment
        mock_create_assessment_object.return_value = mock_assessment
        mock_job_progress.add_task.return_value = "task_id"
        mock_app = MagicMock()
        result = create_and_save_assessment(
            report="report",
            files=["file1", "file2"],
            regscale_id=1,
            regscale_module="module",
            title="title",
            description="description",
            app=mock_app,
        )

        self.assertIsNotNone(result)
        mock_api_object.assert_called_once()
        mock_create_assessment_object.assert_called_once_with(
            ANY,
            "report",
            1,
            "module",
            "title",
            "description",
        )
        mock_job_progress.add_task.assert_called_once_with("[#21a5bb]Creating assessment in RegScale...", total=1)
        mock_assessment.insert_assessment.assert_called_once_with(app=ANY)
        mock_upload_files_to_assessment.assert_called_once_with(ANY, 1, ["file1", "file2"])

    def test_calculate_finish_date(self):
        current_date = datetime(2023, 7, 23, 12, 0, 0)
        days = 7
        result = calculate_finish_date(current_date, days)
        expected = "2023-07-30T12:00:00"
        self.assertEqual(result, expected)
