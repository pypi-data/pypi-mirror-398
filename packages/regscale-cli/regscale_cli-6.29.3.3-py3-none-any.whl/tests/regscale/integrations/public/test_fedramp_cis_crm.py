from concurrent.futures import ThreadPoolExecutor
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, Mock, mock_open, patch

import numpy as np
import pandas as pd
import pytest

from regscale.integrations.public.fedramp.fedramp_cis_crm import (
    ALT_IMPLEMENTATION,
    CAN_BE_INHERITED_CSP,
    CONFIGURED_BY_CUSTOMER,
    CONTROL_ID,
    INHERITED,
    PROVIDED_BY_CUSTOMER,
    SERVICE_PROVIDER_CORPORATE,
    SERVICE_PROVIDER_HYBRID,
    SERVICE_PROVIDER_SYSTEM_SPECIFIC,
    SHARED,
    map_implementation_status,
    map_origination,
    parse_cis_worksheet,
    parse_crm_worksheet,
    transform_control,
)
from regscale.models.regscale_models.control_implementation import ControlImplementation, ControlImplementationStatus
from regscale.models.regscale_models.security_control import SecurityControl


@pytest.fixture()
def mock_cis_dataframe():
    """Create a mock DataFrame that simulates the CIS worksheet structure"""
    # Define the column structure
    columns = [
        CONTROL_ID,
        "Implemented",
        ControlImplementationStatus.PartiallyImplemented,
        "Planned",
        ALT_IMPLEMENTATION,
        ControlImplementationStatus.NA,
        SERVICE_PROVIDER_CORPORATE,
        SERVICE_PROVIDER_SYSTEM_SPECIFIC,
        SERVICE_PROVIDER_HYBRID,
        CONFIGURED_BY_CUSTOMER,
        PROVIDED_BY_CUSTOMER,
        SHARED,
        INHERITED,
    ]

    # Create sample data rows
    data = [
        # Row 1: AC-1 (a) - Fully Implemented by Service Provider Corporate
        ["AC-1 (a)", "X", "", "", "", "", "X", "", "", "", "", "", ""],
        # Row 2: AC-2 - Partially Implemented by Service Provider System Specific
        ["AC-2", "", "X", "", "", "", "", "X", "", "", "", "", ""],
        # Row 3: AC-3 - Planned by Customer Configured
        ["AC-3", "", "", "X", "", "", "", "", "", "X", "", "", ""],
        # Row 4: AC-4 - Not Applicable
        ["AC-4", "", "", "", "", "X", "", "", "", "", "", "", ""],
        # Row 5: AC-5 - Alternative Implementation by Hybrid
        ["AC-5", "", "", "", "X", "", "", "", "X", "", "", "", ""],
        # Row 6: AC-6 (1) - Implemented by Customer Provided
        ["AC-6 (1)", "X", "", "", "", "", "", "", "", "", "X", "", ""],
        # Row 7: AC-7 - Shared responsibility
        ["AC-7", "X", "", "", "", "", "", "", "", "", "", "X", ""],
        # Row 8: AC-8 - Inherited
        ["AC-8", "X", "", "", "", "", "", "", "", "", "", "", "X"],
        # Row 9: AC-9 - Not Implemented (empty row)
        ["AC-9", "", "", "", "", "", "", "", "", "", "", "", ""],
        # Row 10: AC-10 - Multiple statuses
        ["AC-10", "X", "X", "", "", "", "X", "", "", "", "", "", ""],
    ]

    return pd.DataFrame(data, columns=columns)


@pytest.fixture()
def mock_crm_validator_data():
    """Create a mock validator.data that includes header rows for CRM worksheet"""
    csv_string = """
    'FedRAMP High Customer Responsibility Matrix (CRM) Worksheet,Unnamed: 1,Unnamed: 2\n"GUIDANCE: \n\n• Refer to CSP responses in the completed CIS Worksheet, “Control Origination” section. \n\n• For Control IDs identified in the CIS Worksheet as Service Provider Corporate, Service Provider System Specific, or Service Provider Hybrid (Corporate and System Specific), enter ""Yes"" in the ""Can Be Inherited from CSP"" column below, and leave the ""Specific Inheritance and Customer Agency/CSP Responsibilities"" column blank. \n\n• For Control IDs identified in the CIS Worksheet as Shared (Service Provider and Customer Responsibility), enter ""Partial"" in the ""Can Be Inherited from CSP"" column (below). In the ""Specific Inheritance and Customer Agency/CSP Responsibilities"" column, describe which elements are inherited from the CSP and describe the customer responsibilities. \n\n• For Control IDs identified in the CIS Worksheet as Configured by Customer (Customer System Specific) or Provided by Customer (Customer System Specific), enter ""No"" in the ""Can Be Inherited from CSP"" column (below). In the ""Specific Inheritance and Customer Agency/CSP Responsibilities"" column, explain why the Control ID cannot be inherited, and describe the customer responsibilities. \n\n• For CSPs that offer a variety of services or features, the CSP must clearly describe any customer responsibilities associated with each service or feature. In the ""Specific Inheritance and Customer Agency/CSP Responsibilities"" column, for each affected control, the CSP must clearly link the responsibilities to the service or feature. CSPs, with multiple services or features, may wish to add a key to the CRM Worksheet. See the examples below: \n\n- Customer responsibilities noted with ""<ServiceName A>:"" are added if <ServiceName A> is an optional service that can be used by the customer. \n- Customer responsibilities noted with ""<ServiceName B>:"" are added if <ServiceName B> is an optional service that can be used by the customer. \n\n• Example CRM responses, for sample Control IDs, are provided in the Example CRM Worksheet Responses sheet of this workbook.\n",,\nControl ID,Can Be Inherited from CSP,Specific Inheritance and Customer Agency/CSP Responsibilities\nAC-1(a),Yes,\nAC-1(b),Yes,\nAC-1(c),Yes,\nAC-2(a),Partial,Netskope creates the initial customer administrator account for the federal customer in the application. Customer Responsibility: The federal customer administrator is responsible for creating the NGC accounts for the individual users within their organization and identify the types of accounts to support their mission or business functions.\nAC-2(b),Partial,Netskope creates the initial customer administrator account for the federal customer in the application. Customer Responsibility: The federal customer administrator is responsible for creating the NGC accounts for the individual users within their organization and identify the types of accounts to support their mission or business functions.\nAC-2(c),Partial,Federal customers are responsible for establishing conditions for role membership for their NGC accounts.\nAC-2(d),Partial,Customers are responsible for specifying which users within their organization can have NGC accounts.\nAC-2(e),Partial,Customers are responsible for approving access to their NGC accounts.\n'
    """
    df = pd.read_csv(StringIO(csv_string))
    # remove the last row
    df = df.iloc[:-1]
    return df


@pytest.fixture()
def mock_validator_data(mock_cis_dataframe):
    """Create a mock validator.data that includes header rows"""
    # Add header rows that would be skipped
    header_rows = pd.DataFrame(
        [
            ["", "", "", "", "", "", "", "", "", "", "", "", ""],  # Empty row
            ["CIS Controls", "", "", "", "", "", "", "", "", "", "", "", ""],  # Title row
            list(mock_cis_dataframe.columns),  # Column headers
        ],
        columns=mock_cis_dataframe.columns,
    )

    # Combine header rows with data
    full_df = pd.concat([header_rows, mock_cis_dataframe], ignore_index=True)
    return full_df


@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.get_pandas")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.ImportValidater")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.determine_skip_row")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.ThreadPoolExecutor")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.clean_key")
def test_parse_cis_worksheet_success(
    mock_clean_key,
    mock_thread_pool,
    mock_determine_skip_row,
    mock_import_validator,
    mock_get_pandas,
    mock_validator_data,
):
    """Test successful parsing of CIS worksheet"""
    # Setup mocks
    mock_pandas = Mock()
    mock_get_pandas.return_value = mock_pandas

    # Mock the validator
    mock_validator_instance = Mock()
    mock_validator_instance.data = mock_validator_data
    mock_import_validator.return_value = mock_validator_instance

    # Mock determine_skip_row to return 3 (skipping header rows)
    mock_determine_skip_row.return_value = 3

    # Mock ThreadPoolExecutor
    mock_executor = Mock()
    mock_thread_pool.return_value.__enter__.return_value = mock_executor

    # Mock the processed results
    expected_results = [
        {
            "control_id": "AC-1 (a)",
            "regscale_control_id": "ac-1.a",
            "implementation_status": "Implemented",
            "control_origination": "Service Provider Corporate",
        },
        {
            "control_id": "AC-2",
            "regscale_control_id": "ac-2",
            "implementation_status": "Partially Implemented",
            "control_origination": "Service Provider System Specific",
        },
    ]
    mock_executor.map.return_value = expected_results

    # Mock clean_key to return the control_id as-is
    mock_clean_key.side_effect = lambda x: x

    # Call the function
    result = parse_cis_worksheet("test_file.xlsx", "CIS Sheet")

    # Assertions
    assert result == {"AC-1 (a)": expected_results[0], "AC-2": expected_results[1]}

    # Verify mocks were called correctly
    mock_import_validator.assert_called_once()
    mock_determine_skip_row.assert_called_once_with(
        original_df=mock_validator_data, text_to_find=CONTROL_ID, original_skip=2
    )
    mock_thread_pool.assert_called_once()


@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.get_pandas")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.ImportValidater")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.determine_skip_row")
def test_parse_cis_worksheet_dataframe_processing(
    mock_determine_skip_row, mock_import_validator, mock_get_pandas, mock_cis_dataframe
):
    """Test the DataFrame processing logic in parse_cis_worksheet"""
    # Setup mocks
    mock_pandas = Mock()
    mock_get_pandas.return_value = mock_pandas

    # Create a mock validator with our test data
    mock_validator_instance = Mock()
    mock_validator_instance.data = mock_cis_dataframe
    mock_import_validator.return_value = mock_validator_instance

    # Mock determine_skip_row to return 0 (no header rows to skip)
    mock_determine_skip_row.return_value = 0

    # Mock ThreadPoolExecutor to return processed results
    with patch("regscale.integrations.public.fedramp.fedramp_cis_crm.ThreadPoolExecutor") as mock_thread_pool:
        mock_executor = Mock()
        mock_thread_pool.return_value.__enter__.return_value = mock_executor

        # Mock the processed results based on our test data
        expected_results = [
            {
                "control_id": "AC-1 (a)",
                "regscale_control_id": "ac-1.a",
                "implementation_status": "Implemented",
                "control_origination": "Service Provider Corporate",
            },
            {
                "control_id": "AC-2",
                "regscale_control_id": "ac-2",
                "implementation_status": "Partially Implemented",
                "control_origination": "Service Provider System Specific",
            },
        ]
        mock_executor.map.return_value = expected_results

        # Mock clean_key
        with patch("regscale.integrations.public.fedramp.fedramp_cis_crm.clean_key") as mock_clean_key:
            mock_clean_key.side_effect = lambda x: x

            # Call the function
            result = parse_cis_worksheet("test_file.xlsx", "CIS Sheet")

            # Verify the DataFrame processing
            # The function should have called iloc, reset_index, columns assignment, etc.
            assert result == {"AC-1 (a)": expected_results[0], "AC-2": expected_results[1]}


@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.get_pandas")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.ImportValidater")
def test_parse_cis_worksheet_empty_data(mock_import_validator, mock_get_pandas):
    """Test parsing with empty data"""
    # Setup mocks
    mock_pandas = Mock()
    mock_get_pandas.return_value = mock_pandas

    # Create empty DataFrame
    empty_df = pd.DataFrame()
    mock_validator_instance = Mock()
    mock_validator_instance.data = empty_df
    mock_import_validator.return_value = mock_validator_instance

    # Mock determine_skip_row
    with patch("regscale.integrations.public.fedramp.fedramp_cis_crm.determine_skip_row") as mock_determine_skip_row:
        mock_determine_skip_row.return_value = 0

        # Mock ThreadPoolExecutor
        with patch("regscale.integrations.public.fedramp.fedramp_cis_crm.ThreadPoolExecutor") as mock_thread_pool:
            mock_executor = Mock()
            mock_thread_pool.return_value.__enter__.return_value = mock_executor
            mock_executor.map.return_value = []

            # Mock clean_key
            with patch("regscale.integrations.public.fedramp.fedramp_cis_crm.clean_key") as mock_clean_key:
                mock_clean_key.side_effect = lambda x: x

                # Call the function
                result = parse_cis_worksheet("test_file.xlsx", "CIS Sheet")

                # Should return empty dict
                assert result == {}


@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.get_pandas")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.ImportValidater")
def test_parse_cis_worksheet_with_nan_values(mock_import_validator, mock_get_pandas):
    """Test parsing with NaN values in the data"""
    # Setup mocks
    mock_pandas = Mock()
    mock_get_pandas.return_value = mock_pandas

    # Create DataFrame with NaN values
    data_with_nan = pd.DataFrame(
        [
            ["AC-1", "X", "", "", "", "", "X", "", "", "", "", "", ""],
            ["AC-2", "", "", "", "", "", "", "", "", "", "", "", ""],  # Empty row
            ["AC-3", "X", "X", "", "", "", "", "", "", "", "", "", ""],
        ],
        columns=[
            CONTROL_ID,
            "Implemented",
            ControlImplementationStatus.PartiallyImplemented,
            "Planned",
            ALT_IMPLEMENTATION,
            ControlImplementationStatus.NA,
            SERVICE_PROVIDER_CORPORATE,
            SERVICE_PROVIDER_SYSTEM_SPECIFIC,
            SERVICE_PROVIDER_HYBRID,
            CONFIGURED_BY_CUSTOMER,
            PROVIDED_BY_CUSTOMER,
            SHARED,
            INHERITED,
        ],
    )

    mock_validator_instance = Mock()
    mock_validator_instance.data = data_with_nan
    mock_import_validator.return_value = mock_validator_instance

    # Mock determine_skip_row
    with patch("regscale.integrations.public.fedramp.fedramp_cis_crm.determine_skip_row") as mock_determine_skip_row:
        mock_determine_skip_row.return_value = 0

        # Mock ThreadPoolExecutor
        with patch("regscale.integrations.public.fedramp.fedramp_cis_crm.ThreadPoolExecutor") as mock_thread_pool:
            mock_executor = Mock()
            mock_thread_pool.return_value.__enter__.return_value = mock_executor

            # Mock the processed results
            expected_results = [
                {
                    "control_id": "AC-1",
                    "regscale_control_id": "ac-1",
                    "implementation_status": "Implemented",
                    "control_origination": "Service Provider Corporate",
                },
                {
                    "control_id": "AC-2",
                    "regscale_control_id": "ac-2",
                    "implementation_status": "",
                    "control_origination": "",
                },
                {
                    "control_id": "AC-3",
                    "regscale_control_id": "ac-3",
                    "implementation_status": "Implemented, Partially Implemented",
                    "control_origination": "",
                },
            ]
            mock_executor.map.return_value = expected_results

            # Mock clean_key
            with patch("regscale.integrations.public.fedramp.fedramp_cis_crm.clean_key") as mock_clean_key:
                mock_clean_key.side_effect = lambda x: x

                # Call the function
                result = parse_cis_worksheet("test_file.xlsx", "CIS Sheet")

                # Verify results
                assert len(result) == 3
                assert "AC-1" in result
                assert "AC-2" in result
                assert "AC-3" in result

                # Verify the status extraction logic worked correctly
                assert result["AC-1"]["implementation_status"] == expected_results[0]["implementation_status"]
                assert result["AC-2"]["implementation_status"] == expected_results[1]["implementation_status"]
                assert result["AC-3"]["implementation_status"] == expected_results[2]["implementation_status"]


@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.ImportValidater")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.determine_skip_row")
def test_parse_crm_worksheet_success(mock_determine_skip_row, mock_import_validator, mock_crm_validator_data):
    """Test successful parsing of CRM worksheet"""
    # Setup mocks
    mock_validator_instance = Mock()
    mock_validator_instance.data = mock_crm_validator_data
    mock_import_validator.return_value = mock_validator_instance

    # Mock determine_skip_row to return 2 (skipping header rows)
    mock_determine_skip_row.return_value = 2

    # Call the function
    result = parse_crm_worksheet("test_file.xlsx", "CRM Sheet", "rev5")

    # Assertions - should exclude rows where "Can Be Inherited from CSP" == "No"
    assert len(result) == 8  # Should exclude AC-3, AC-9, AC-12 (which have "No")

    # Check specific entries
    assert "AC-1(a)" in result
    assert result["AC-1(a)"]["control_id"] == "AC-1(a)"
    assert result["AC-1(a)"]["can_be_inherited_from_csp"] == "Yes"
    assert (
        result["AC-2(b)"]["specific_inheritance_and_customer_agency_csp_responsibilities"]
        == "Netskope creates the initial customer administrator account for the federal customer in the application. Customer Responsibility: The federal customer administrator is responsible for creating the NGC accounts for the individual users within their organization and identify the types of accounts to support their mission or business functions."
    )

    # Verify excluded entries are not present
    assert "AC-3" not in result
    assert "AC-9" not in result
    assert "AC-12" not in result

    # Verify mocks were called correctly
    mock_import_validator.assert_called_once()
    mock_determine_skip_row.assert_called_once_with(
        original_df=mock_crm_validator_data, text_to_find=CONTROL_ID, original_skip=3
    )


@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.ImportValidater")
def test_parse_crm_worksheet_empty_data(mock_import_validator):
    """Test parsing CRM worksheet with empty data"""
    # Setup mocks
    empty_df = pd.DataFrame()
    mock_validator_instance = Mock()
    mock_validator_instance.data = empty_df
    mock_import_validator.return_value = mock_validator_instance

    # Call the function
    result = parse_crm_worksheet("test_file.xlsx", "CRM Sheet", "rev5")

    # Should return empty dict
    assert result == {}


@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.ImportValidater")
def test_parse_crm_worksheet_no_crm_sheet_name(mock_import_validator):
    """Test parsing CRM worksheet with no CRM sheet name"""
    # Call the function with empty CRM sheet name
    result = parse_crm_worksheet("test_file.xlsx", "", "rev5")

    # Should return empty dict
    assert result == {}

    # ImportValidater should not be called
    mock_import_validator.assert_not_called()


@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.ImportValidater")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.determine_skip_row")
def test_parse_crm_worksheet_filtering_logic(mock_determine_skip_row, mock_import_validator, mock_crm_validator_data):
    """Test the filtering logic that excludes rows where 'Can Be Inherited from CSP' == 'No'"""
    # Setup mocks
    mock_validator_instance = Mock()
    mock_validator_instance.data = mock_crm_validator_data
    mock_import_validator.return_value = mock_validator_instance
    mock_determine_skip_row.return_value = 2  # No header rows to skip

    # Call the function
    result = parse_crm_worksheet("test_file.xlsx", "CRM Sheet", "rev5")

    # Should exclude rows where "Can Be Inherited from CSP" == "No"
    # From our test data: AC-3, AC-9, AC-12 have "No"
    excluded_controls = ["AC-3", "AC-9", "AC-12"]
    included_controls = ["AC-1(a)", "AC-1(b)", "AC-1(c)", "AC-2(a)", "AC-2(b)", "AC-2(c)", "AC-2(d)", "AC-2(e)"]

    # Verify excluded controls are not in result
    for control in excluded_controls:
        assert control not in result

    # Verify included controls are in result
    for control in included_controls:
        assert control in result

    # Verify total count
    assert len(result) == len(included_controls)


@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.ImportValidater")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.determine_skip_row")
def test_parse_crm_worksheet_data_structure(mock_determine_skip_row, mock_import_validator, mock_crm_validator_data):
    """Test the structure of the returned CRM data"""
    # Setup mocks
    mock_validator_instance = Mock()
    mock_validator_instance.data = mock_crm_validator_data
    mock_import_validator.return_value = mock_validator_instance
    mock_determine_skip_row.return_value = 2

    # Call the function
    result = parse_crm_worksheet("test_file.xlsx", "CRM Sheet", "rev5")

    # Check structure of returned data
    for control_id, data in result.items():
        # Verify required keys exist
        assert "control_id" in data
        assert "clean_control_id" in data
        assert "regscale_control_id" in data
        assert "can_be_inherited_from_csp" in data
        assert "specific_inheritance_and_customer_agency_csp_responsibilities" in data

        # Verify data types
        assert isinstance(data["control_id"], str)
        assert isinstance(data["clean_control_id"], str)
        assert isinstance(data["regscale_control_id"], str)
        assert isinstance(data["can_be_inherited_from_csp"], str)
        assert isinstance(data["specific_inheritance_and_customer_agency_csp_responsibilities"], str)

        # Verify clean_control_id is lowercase and processed
        assert data["clean_control_id"] == data["clean_control_id"].lower()
        assert " " not in data["clean_control_id"]  # No spaces in clean_control_id


@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.ImportValidater")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.determine_skip_row")
def test_parse_crm_worksheet_column_validation(mock_determine_skip_row, mock_import_validator):
    """Test column validation in CRM worksheet parsing"""
    # Create DataFrame with missing columns
    invalid_df = pd.DataFrame(
        [
            ["", "", ""],  # Empty row
            ["CRM Controls", "", ""],  # Title row
            ["Control ID", "Wrong Column", "Another Wrong Column"],  # Wrong headers
        ]
    )

    mock_validator_instance = Mock()
    mock_validator_instance.data = invalid_df
    mock_import_validator.return_value = mock_validator_instance
    mock_determine_skip_row.return_value = 3

    # This should raise an error due to missing required columns
    with pytest.raises(SystemExit):
        parse_crm_worksheet("test_file.xlsx", "CRM Sheet", "rev5")


@staticmethod
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.SecurityPlan")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.logger")
def test_create_backup_file_success(mock_logger, mock_security_plan):
    """Test successful backup file creation"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import create_backup_file

    # Mock the SecurityPlan.export_cis_crm method
    mock_security_plan.export_cis_crm.return_value = {
        "status": "complete",
        "trustedDisplayName": "test_backup_file.docx",
    }

    # Call the function
    create_backup_file(123)

    # Verify SecurityPlan.export_cis_crm was called with correct parameter
    mock_security_plan.export_cis_crm.assert_called_once_with(123)

    # Verify logger calls
    mock_logger.info.assert_any_call("Creating a CIS/CRM Backup file of the current SSP state ..")
    mock_logger.info.assert_any_call("A CIS/CRM Backup file saved to SSP# 123 file subsystem as test_backup_file.docx!")


@staticmethod
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.SecurityPlan")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.click")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.logger")
def test_create_backup_file_failure_user_continues(mock_logger, mock_click, mock_security_plan):
    """Test backup file creation failure with user choosing to continue"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import create_backup_file

    # Mock the SecurityPlan.export_cis_crm method to return failed status
    mock_security_plan.export_cis_crm.return_value = {"status": "failed", "error": "Backup failed"}

    # Mock click.prompt to return True (user chooses to continue)
    mock_click.prompt.return_value = True

    # Call the function
    create_backup_file(456)

    # Verify SecurityPlan.export_cis_crm was called with correct parameter
    mock_security_plan.export_cis_crm.assert_called_once_with(456)

    # Verify logger calls
    mock_logger.info.assert_called_once_with("Creating a CIS/CRM Backup file of the current SSP state ..")

    # Verify click.prompt was called
    mock_click.prompt.assert_called_once_with("Unable to create a backup file. Would you like to continue?", type=bool)


@staticmethod
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.SecurityPlan")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.click")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.error_and_exit")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.logger")
def test_create_backup_file_failure_user_exits(mock_logger, mock_error_and_exit, mock_click, mock_security_plan):
    """Test backup file creation failure with user choosing not to continue"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import create_backup_file

    # Mock the SecurityPlan.export_cis_crm method to return failed status
    mock_security_plan.export_cis_crm.return_value = {"status": "failed", "error": "Backup failed"}

    # Mock click.prompt to return False (user chooses not to continue)
    mock_click.prompt.return_value = False

    # Call the function
    create_backup_file(789)

    # Verify SecurityPlan.export_cis_crm was called with correct parameter
    mock_security_plan.export_cis_crm.assert_called_once_with(789)

    # Verify logger calls
    mock_logger.info.assert_called_once_with("Creating a CIS/CRM Backup file of the current SSP state ..")

    # Verify click.prompt was called
    mock_click.prompt.assert_called_once_with("Unable to create a backup file. Would you like to continue?", type=bool)

    # Verify error_and_exit was called
    mock_error_and_exit.assert_called_once()


@staticmethod
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.SecurityPlan")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.click")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.error_and_exit")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.logger")
def test_create_backup_file_no_status(mock_logger, mock_error_and_exit, mock_click, mock_security_plan):
    """Test backup file creation when response has no status field"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import create_backup_file

    # Mock the SecurityPlan.export_cis_crm method to return response without status
    mock_security_plan.export_cis_crm.return_value = {"trustedDisplayName": "test_backup_file.docx"}

    # Mock click.prompt to return False (user chooses not to continue)
    mock_click.prompt.return_value = False

    # Call the function
    create_backup_file(999)

    # Verify SecurityPlan.export_cis_crm was called with correct parameter
    mock_security_plan.export_cis_crm.assert_called_once_with(999)

    # Verify logger calls
    mock_logger.info.assert_called_once_with("Creating a CIS/CRM Backup file of the current SSP state ..")

    # Verify click.prompt was called
    mock_click.prompt.assert_called_once_with("Unable to create a backup file. Would you like to continue?", type=bool)

    # Verify error_and_exit was called
    mock_error_and_exit.assert_called_once()


@staticmethod
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.SecurityPlan")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.click")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.logger")
def test_create_backup_file_empty_response(mock_logger, mock_click, mock_security_plan):
    """Test backup file creation when response is empty"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import create_backup_file

    # Mock the SecurityPlan.export_cis_crm method to return empty response
    mock_security_plan.export_cis_crm.return_value = {}

    # Mock click.prompt to return True (user chooses to continue)
    mock_click.prompt.return_value = True

    # Call the function
    create_backup_file(111)

    # Verify SecurityPlan.export_cis_crm was called with correct parameter
    mock_security_plan.export_cis_crm.assert_called_once_with(111)

    # Verify logger calls
    mock_logger.info.assert_called_once_with("Creating a CIS/CRM Backup file of the current SSP state ..")

    # Verify click.prompt was called
    mock_click.prompt.assert_called_once_with("Unable to create a backup file. Would you like to continue?", type=bool)


@staticmethod
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.SecurityPlan")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.logger")
def test_create_backup_file_success_no_filename(mock_logger, mock_security_plan):
    """Test successful backup file creation without filename"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import create_backup_file

    # Mock the SecurityPlan.export_cis_crm method
    mock_security_plan.export_cis_crm.return_value = {
        "status": "complete"
        # No trustedDisplayName field
    }

    # Call the function
    create_backup_file(222)

    # Verify SecurityPlan.export_cis_crm was called with correct parameter
    mock_security_plan.export_cis_crm.assert_called_once_with(222)

    # Verify logger calls
    mock_logger.info.assert_any_call("Creating a CIS/CRM Backup file of the current SSP state ..")
    mock_logger.info.assert_any_call("A CIS/CRM Backup file saved to SSP# 222 file subsystem as None!")


@staticmethod
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.SecurityPlan")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.click")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.logger")
def test_create_backup_file_partial_status(mock_logger, mock_click, mock_security_plan):
    """Test backup file creation with partial status (not 'complete')"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import create_backup_file

    # Mock the SecurityPlan.export_cis_crm method to return partial status
    mock_security_plan.export_cis_crm.return_value = {
        "status": "in_progress",
        "trustedDisplayName": "test_backup_file.docx",
    }

    # Mock click.prompt to return True (user chooses to continue)
    mock_click.prompt.return_value = True

    # Call the function
    create_backup_file(333)

    # Verify SecurityPlan.export_cis_crm was called with correct parameter
    mock_security_plan.export_cis_crm.assert_called_once_with(333)

    # Verify logger calls
    mock_logger.info.assert_called_once_with("Creating a CIS/CRM Backup file of the current SSP state ..")

    # Verify click.prompt was called
    mock_click.prompt.assert_called_once_with("Unable to create a backup file. Would you like to continue?", type=bool)


@staticmethod
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.File")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.compute_hash")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.logger")
def test_upload_file_new_file_success(mock_logger, mock_compute_hash, mock_file):
    """Test successful upload of a new file."""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import upload_file

    # Mock file path
    file_path = Path("/test/path/test_file.docx")

    # Mock API object
    mock_api = MagicMock()

    # Mock compute_hash to return a test hash
    mock_compute_hash.return_value = "test_hash_123"

    # Mock existing files (empty list - no identical files)
    mock_file.get_files_for_parent_from_regscale.return_value = []

    # Mock file content
    mock_file_content = b"test file content"

    with patch("builtins.open", mock_open(read_data=mock_file_content)):
        # Call the function
        upload_file(file_path, 123, "securityplans", mock_api)

    # Verify compute_hash was called
    mock_compute_hash.assert_called_once()

    # Verify get_files_for_parent_from_regscale was called
    mock_file.get_files_for_parent_from_regscale.assert_called_once_with(123, "securityplans")

    # Verify upload_file_to_regscale was called with correct parameters
    mock_file.upload_file_to_regscale.assert_called_once_with(
        file_name=file_path.absolute(), parent_id=123, parent_module="securityplans", api=mock_api, tags="cis-crm"
    )


@staticmethod
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.File")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.compute_hash")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.logger")
def test_upload_file_identical_file_exists(mock_logger, mock_compute_hash, mock_file):
    """Test upload when identical file already exists."""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import upload_file

    # Mock file path
    file_path = Path("/test/path/test_file.docx")

    # Mock API object
    mock_api = MagicMock()

    # Mock compute_hash to return a test hash
    mock_compute_hash.return_value = "test_hash_123"

    # Mock existing file with same hash
    mock_existing_file = MagicMock()
    mock_existing_file.shaHash = "test_hash_123"
    mock_existing_file.trustedDisplayName = "existing_file.docx"

    # Mock existing files list with identical file
    mock_file.get_files_for_parent_from_regscale.return_value = [mock_existing_file]

    # Mock file content
    mock_file_content = b"test file content"

    with patch("builtins.open", mock_open(read_data=mock_file_content)):
        # Call the function
        upload_file(file_path, 456, "securityplans", mock_api)

    # Verify compute_hash was called
    mock_compute_hash.assert_called_once()

    # Verify get_files_for_parent_from_regscale was called
    mock_file.get_files_for_parent_from_regscale.assert_called_once_with(456, "securityplans")

    # Verify upload_file_to_regscale was NOT called (file already exists)
    mock_file.upload_file_to_regscale.assert_not_called()

    # Verify logger message was called
    mock_logger.info.assert_called_once_with(
        "An identical file existing_file.docx already exists in RegScale, skipping upload."
    )


@staticmethod
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.File")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.compute_hash")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.logger")
def test_upload_file_no_hash_computed(mock_logger, mock_compute_hash, mock_file):
    """Test upload when no hash is computed (file read error)."""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import upload_file

    # Mock file path
    file_path = Path("/test/path/test_file.docx")

    # Mock API object
    mock_api = MagicMock()

    # Mock compute_hash to return None (file read error)
    mock_compute_hash.return_value = None

    # Mock existing files (empty list)
    mock_file.get_files_for_parent_from_regscale.return_value = []

    # Mock file content
    mock_file_content = b"test file content"

    with patch("builtins.open", mock_open(read_data=mock_file_content)):
        # Call the function
        upload_file(file_path, 789, "securityplans", mock_api)

    # Verify compute_hash was called
    mock_compute_hash.assert_called_once()

    # Verify get_files_for_parent_from_regscale was called
    mock_file.get_files_for_parent_from_regscale.assert_called_once_with(789, "securityplans")

    # Verify upload_file_to_regscale was called (no hash means no duplicate check)
    mock_file.upload_file_to_regscale.assert_called_once_with(
        file_name=file_path.absolute(), parent_id=789, parent_module="securityplans", api=mock_api, tags="cis-crm"
    )


@staticmethod
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.File")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.compute_hash")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.logger")
def test_upload_file_different_hash_files(mock_logger, mock_compute_hash, mock_file):
    """Test upload when files exist but with different hashes."""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import upload_file

    # Mock file path
    file_path = Path("/test/path/test_file.docx")

    # Mock API object
    mock_api = MagicMock()

    # Mock compute_hash to return a test hash
    mock_compute_hash.return_value = "new_hash_456"

    # Mock existing files with different hash
    mock_existing_file = MagicMock()
    mock_existing_file.shaHash = "different_hash_789"
    mock_existing_file.trustedDisplayName = "existing_file.docx"

    # Mock existing files list with different hash file
    mock_file.get_files_for_parent_from_regscale.return_value = [mock_existing_file]

    # Mock file content
    mock_file_content = b"test file content"

    with patch("builtins.open", mock_open(read_data=mock_file_content)):
        # Call the function
        upload_file(file_path, 101, "securityplans", mock_api)

    # Verify compute_hash was called
    mock_compute_hash.assert_called_once()

    # Verify get_files_for_parent_from_regscale was called
    mock_file.get_files_for_parent_from_regscale.assert_called_once_with(101, "securityplans")

    # Verify upload_file_to_regscale was called (different hash means new file)
    mock_file.upload_file_to_regscale.assert_called_once_with(
        file_name=file_path.absolute(), parent_id=101, parent_module="securityplans", api=mock_api, tags="cis-crm"
    )


@staticmethod
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.File")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.compute_hash")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.logger")
def test_upload_file_multiple_existing_files(mock_logger, mock_compute_hash, mock_file):
    """Test upload with multiple existing files, one with matching hash."""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import upload_file

    # Mock file path
    file_path = Path("/test/path/test_file.docx")

    # Mock API object
    mock_api = MagicMock()

    # Mock compute_hash to return a test hash
    mock_compute_hash.return_value = "target_hash_123"

    # Mock multiple existing files
    mock_file1 = MagicMock()
    mock_file1.shaHash = "different_hash_1"
    mock_file1.trustedDisplayName = "file1.docx"

    mock_file2 = MagicMock()
    mock_file2.shaHash = "target_hash_123"  # Matching hash
    mock_file2.trustedDisplayName = "matching_file.docx"

    mock_file3 = MagicMock()
    mock_file3.shaHash = "different_hash_2"
    mock_file3.trustedDisplayName = "file3.docx"

    # Mock existing files list
    mock_file.get_files_for_parent_from_regscale.return_value = [mock_file1, mock_file2, mock_file3]

    # Mock file content
    mock_file_content = b"test file content"

    with patch("builtins.open", mock_open(read_data=mock_file_content)):
        # Call the function
        upload_file(file_path, 202, "securityplans", mock_api)

    # Verify compute_hash was called
    mock_compute_hash.assert_called_once()

    # Verify get_files_for_parent_from_regscale was called
    mock_file.get_files_for_parent_from_regscale.assert_called_once_with(202, "securityplans")

    # Verify upload_file_to_regscale was NOT called (matching file found)
    mock_file.upload_file_to_regscale.assert_not_called()

    # Verify logger message was called with the matching file name
    mock_logger.info.assert_called_once_with(
        "An identical file matching_file.docx already exists in RegScale, skipping upload."
    )


@staticmethod
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.File")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.compute_hash")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.logger")
def test_upload_file_file_read_error(mock_logger, mock_compute_hash, mock_file):
    """Test upload when file read fails."""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import upload_file

    # Mock file path
    file_path = Path("/test/path/nonexistent_file.docx")

    # Mock API object
    mock_api = MagicMock()

    # Mock existing files (empty list)
    mock_file.get_files_for_parent_from_regscale.return_value = []

    # Mock file open to raise an exception
    with patch("builtins.open", side_effect=FileNotFoundError("File not found")):
        # Call the function - should handle the exception gracefully
        with pytest.raises(FileNotFoundError):
            upload_file(file_path, 303, "securityplans", mock_api)

    # Verify get_files_for_parent_from_regscale was NOT called (function exits early on file error)
    mock_file.get_files_for_parent_from_regscale.assert_not_called()

    # Verify upload_file_to_regscale was NOT called due to exception
    mock_file.upload_file_to_regscale.assert_not_called()


@staticmethod
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.File")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.compute_hash")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.logger")
def test_upload_file_different_parent_module(mock_logger, mock_compute_hash, mock_file):
    """Test upload with different parent module."""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import upload_file

    # Mock file path
    file_path = Path("/test/path/test_file.docx")

    # Mock API object
    mock_api = MagicMock()

    # Mock compute_hash to return a test hash
    mock_compute_hash.return_value = "test_hash_123"

    # Mock existing files (empty list)
    mock_file.get_files_for_parent_from_regscale.return_value = []

    # Mock file content
    mock_file_content = b"test file content"

    with patch("builtins.open", mock_open(read_data=mock_file_content)):
        # Call the function with different parent module
        upload_file(file_path, 404, "components", mock_api)

    # Verify compute_hash was called
    mock_compute_hash.assert_called_once()

    # Verify get_files_for_parent_from_regscale was called with correct module
    mock_file.get_files_for_parent_from_regscale.assert_called_once_with(404, "components")

    # Verify upload_file_to_regscale was called with correct parameters
    mock_file.upload_file_to_regscale.assert_called_once_with(
        file_name=file_path.absolute(), parent_id=404, parent_module="components", api=mock_api, tags="cis-crm"
    )


@staticmethod
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.File")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.compute_hash")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.logger")
def test_upload_file_empty_file(mock_logger, mock_compute_hash, mock_file):
    """Test upload of an empty file."""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import upload_file

    # Mock file path
    file_path = Path("/test/path/empty_file.docx")

    # Mock API object
    mock_api = MagicMock()

    # Mock compute_hash to return a hash for empty file
    mock_compute_hash.return_value = "empty_file_hash"

    # Mock existing files (empty list)
    mock_file.get_files_for_parent_from_regscale.return_value = []

    # Mock empty file content
    mock_file_content = b""

    with patch("builtins.open", mock_open(read_data=mock_file_content)):
        # Call the function
        upload_file(file_path, 505, "securityplans", mock_api)

    # Verify compute_hash was called
    mock_compute_hash.assert_called_once()

    # Verify get_files_for_parent_from_regscale was called
    mock_file.get_files_for_parent_from_regscale.assert_called_once_with(505, "securityplans")

    # Verify upload_file_to_regscale was called
    mock_file.upload_file_to_regscale.assert_called_once_with(
        file_name=file_path.absolute(), parent_id=505, parent_module="securityplans", api=mock_api, tags="cis-crm"
    )


@staticmethod
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.File")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.compute_hash")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.logger")
def test_upload_file_large_file(mock_logger, mock_compute_hash, mock_file):
    """Test upload of a large file."""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import upload_file

    # Mock file path
    file_path = Path("/test/path/large_file.docx")

    # Mock API object
    mock_api = MagicMock()

    # Mock compute_hash to return a hash for large file
    mock_compute_hash.return_value = "large_file_hash"

    # Mock existing files (empty list)
    mock_file.get_files_for_parent_from_regscale.return_value = []

    # Mock large file content (1MB of data)
    mock_file_content = b"x" * (1024 * 1024)

    with patch("builtins.open", mock_open(read_data=mock_file_content)):
        # Call the function
        upload_file(file_path, 606, "securityplans", mock_api)

    # Verify compute_hash was called
    mock_compute_hash.assert_called_once()

    # Verify get_files_for_parent_from_regscale was called
    mock_file.get_files_for_parent_from_regscale.assert_called_once_with(606, "securityplans")

    # Verify upload_file_to_regscale was called
    mock_file.upload_file_to_regscale.assert_called_once_with(
        file_name=file_path.absolute(), parent_id=606, parent_module="securityplans", api=mock_api, tags="cis-crm"
    )


@staticmethod
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.logger")
def test_map_implementation_status_single_implemented(mock_logger):
    """Test mapping implementation status when all records are implemented"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import map_implementation_status

    # Test data with single implemented status
    cis_data = {"record1": {"regscale_control_id": "AC-1", "implementation_status": "Implemented"}}

    result = map_implementation_status("AC-1", cis_data)

    assert result == ControlImplementationStatus.Implemented


@staticmethod
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.logger")
def test_map_implementation_status_single_partially_implemented(mock_logger):
    """Test mapping implementation status when all records are partially implemented"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import map_implementation_status

    # Test data with single partially implemented status
    cis_data = {"record1": {"regscale_control_id": "AC-2", "implementation_status": "Partially Implemented"}}

    result = map_implementation_status("AC-2", cis_data)

    assert result == ControlImplementationStatus.PartiallyImplemented


@staticmethod
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.logger")
def test_map_implementation_status_single_planned(mock_logger):
    """Test mapping implementation status when all records are planned"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import map_implementation_status

    # Test data with single planned status
    cis_data = {"record1": {"regscale_control_id": "AC-3", "implementation_status": "Planned"}}

    result = map_implementation_status("AC-3", cis_data)

    assert result == ControlImplementationStatus.Planned


@staticmethod
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.logger")
def test_map_implementation_status_single_na(mock_logger):
    """Test mapping implementation status when all records are N/A"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import map_implementation_status

    # Test data with single N/A status
    cis_data = {"record1": {"regscale_control_id": "AC-4", "implementation_status": "N/A"}}

    result = map_implementation_status("AC-4", cis_data)

    assert result == ControlImplementationStatus.NA


@staticmethod
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.logger")
def test_map_implementation_status_single_alternative_implementation(mock_logger):
    """Test mapping implementation status when all records are alternative implementation"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import map_implementation_status

    # Test data with single alternative implementation status
    cis_data = {"record1": {"regscale_control_id": "AC-5", "implementation_status": "Alternative Implementation"}}

    result = map_implementation_status("AC-5", cis_data)

    assert result == ControlImplementationStatus.Alternative


@staticmethod
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.logger")
def test_map_implementation_status_single_alt_implementation(mock_logger):
    """Test mapping implementation status when all records are alternate implementation"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import map_implementation_status

    # Test data with single alternate implementation status
    cis_data = {"record1": {"regscale_control_id": "AC-6", "implementation_status": "Alternate Implementation"}}

    result = map_implementation_status("AC-6", cis_data)

    assert result == ControlImplementationStatus.Alternative


@staticmethod
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.logger")
def test_map_implementation_status_single_unknown_status(mock_logger):
    """Test mapping implementation status when status is unknown"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import map_implementation_status

    # Test data with unknown status
    cis_data = {"record1": {"regscale_control_id": "AC-7", "implementation_status": "Unknown Status"}}

    result = map_implementation_status("AC-7", cis_data)

    assert result == ControlImplementationStatus.NotImplemented


@staticmethod
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.logger")
def test_map_implementation_status_no_records_found(mock_logger):
    """Test mapping implementation status when no records are found"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import map_implementation_status

    # Test data with no matching records
    cis_data = {"record1": {"regscale_control_id": "AC-8", "implementation_status": "Implemented"}}

    result = map_implementation_status("AC-9", cis_data)

    assert result == ControlImplementationStatus.NotImplemented


@staticmethod
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.logger")
def test_map_implementation_status_all_implemented(mock_logger):
    """Test mapping implementation status when all records are implemented"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import map_implementation_status

    # Test data with multiple implemented records
    cis_data = {
        "record1": {"regscale_control_id": "AC-10", "implementation_status": "Implemented"},
        "record2": {"regscale_control_id": "AC-10", "implementation_status": "Implemented"},
        "record3": {"regscale_control_id": "AC-10", "implementation_status": "Implemented"},
    }

    result = map_implementation_status("AC-10", cis_data)

    assert result == ControlImplementationStatus.Implemented


@staticmethod
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.logger")
def test_map_implementation_status_mixed_implemented_and_partial(mock_logger):
    """Test mapping implementation status with mixed implemented and partially implemented"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import map_implementation_status

    # Test data with mixed statuses
    cis_data = {
        "record1": {"regscale_control_id": "AC-11", "implementation_status": "Implemented"},
        "record2": {"regscale_control_id": "AC-11", "implementation_status": "Partially Implemented"},
    }

    result = map_implementation_status("AC-11", cis_data)

    assert result == ControlImplementationStatus.PartiallyImplemented


@staticmethod
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.logger")
def test_map_implementation_status_mixed_with_na(mock_logger):
    """Test mapping implementation status with mixed statuses including N/A"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import map_implementation_status

    # Test data with mixed statuses including N/A
    cis_data = {
        "record1": {"regscale_control_id": "AC-12", "implementation_status": "Implemented"},
        "record2": {"regscale_control_id": "AC-12", "implementation_status": "N/A"},
    }

    result = map_implementation_status("AC-12", cis_data)

    assert result == ControlImplementationStatus.PartiallyImplemented


@staticmethod
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.logger")
def test_map_implementation_status_mixed_with_alternative_implementation(mock_logger):
    """Test mapping implementation status with mixed statuses including alternative implementation"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import map_implementation_status

    # Test data with mixed statuses including alternative implementation
    cis_data = {
        "record1": {"regscale_control_id": "AC-13", "implementation_status": "Implemented"},
        "record2": {"regscale_control_id": "AC-13", "implementation_status": "Alternative Implementation"},
    }

    result = map_implementation_status("AC-13", cis_data)

    assert result == ControlImplementationStatus.PartiallyImplemented


@staticmethod
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.logger")
def test_map_implementation_status_mixed_with_planned(mock_logger):
    """Test mapping implementation status with mixed statuses including planned"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import map_implementation_status

    # Test data with mixed statuses including planned
    cis_data = {
        "record1": {"regscale_control_id": "AC-14", "implementation_status": "Implemented"},
        "record2": {"regscale_control_id": "AC-14", "implementation_status": "Planned"},
    }

    result = map_implementation_status("AC-14", cis_data)

    assert result == ControlImplementationStatus.PartiallyImplemented


@staticmethod
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.logger")
def test_map_implementation_status_only_planned(mock_logger):
    """Test mapping implementation status when only planned statuses exist"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import map_implementation_status

    # Test data with only planned statuses
    cis_data = {
        "record1": {"regscale_control_id": "AC-15", "implementation_status": "Planned"},
        "record2": {"regscale_control_id": "AC-15", "implementation_status": "Planned"},
    }

    result = map_implementation_status("AC-15", cis_data)

    assert result == ControlImplementationStatus.Planned


@staticmethod
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.logger")
def test_map_implementation_status_case_insensitive_matching(mock_logger):
    """Test mapping implementation status with case insensitive control ID matching"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import map_implementation_status

    # Test data with different case control IDs
    cis_data = {
        "record1": {"regscale_control_id": "ac-16", "implementation_status": "Implemented"},
        "record2": {"regscale_control_id": "AC-16", "implementation_status": "Implemented"},
    }

    result = map_implementation_status("ac-16", cis_data)

    assert result == ControlImplementationStatus.Implemented


@staticmethod
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.logger")
def test_map_implementation_status_missing_implementation_status(mock_logger):
    """Test mapping implementation status when implementation_status is missing"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import map_implementation_status

    # Test data with missing implementation_status
    cis_data = {
        "record1": {
            "regscale_control_id": "AC-17"
            # Missing implementation_status
        }
    }

    result = map_implementation_status("AC-17", cis_data)

    assert result == ControlImplementationStatus.NotImplemented


@staticmethod
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.logger")
def test_map_implementation_status_missing_regscale_control_id(mock_logger):
    """Test mapping implementation status when regscale_control_id is missing"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import map_implementation_status

    # Test data with missing regscale_control_id
    cis_data = {
        "record1": {
            "implementation_status": "Implemented"
            # Missing regscale_control_id
        }
    }

    result = map_implementation_status("AC-18", cis_data)

    assert result == ControlImplementationStatus.NotImplemented


@staticmethod
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.logger")
def test_map_implementation_status_empty_cis_data(mock_logger):
    """Test mapping implementation status with empty CIS data"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import map_implementation_status

    # Test data with empty CIS data
    cis_data = {}

    result = map_implementation_status("AC-19", cis_data)

    assert result == ControlImplementationStatus.NotImplemented


@staticmethod
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.logger")
def test_map_implementation_status_complex_mixed_scenario(mock_logger):
    """Test mapping implementation status with complex mixed scenario"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import map_implementation_status

    # Test data with complex mixed scenario
    cis_data = {
        "record1": {"regscale_control_id": "AC-20", "implementation_status": "Implemented"},
        "record2": {"regscale_control_id": "AC-20", "implementation_status": "Partially Implemented"},
        "record3": {"regscale_control_id": "AC-20", "implementation_status": "Planned"},
        "record4": {"regscale_control_id": "AC-20", "implementation_status": "N/A"},
    }

    result = map_implementation_status("AC-20", cis_data)

    assert result == ControlImplementationStatus.PartiallyImplemented


@staticmethod
def test_map_origination_single_service_provider_corporate():
    """Test mapping origination for single Service Provider Corporate record"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import map_origination

    # Test data with single Service Provider Corporate record
    cis_data = {"record1": {"regscale_control_id": "AC-1", "control_origination": "Service Provider Corporate"}}

    result = map_origination("AC-1", cis_data)

    # Verify the result structure
    assert isinstance(result, dict)
    assert "bServiceProviderCorporate" in result
    assert "bServiceProviderSystemSpecific" in result
    assert "bServiceProviderHybrid" in result
    assert "bProvidedByCustomer" in result
    assert "bConfiguredByCustomer" in result
    assert "bShared" in result
    assert "bInherited" in result
    assert "record_text" in result

    # Verify the correct flag is set
    assert result["bServiceProviderCorporate"] is True
    assert result["bServiceProviderSystemSpecific"] is False
    assert result["bServiceProviderHybrid"] is False
    assert result["bProvidedByCustomer"] is False
    assert result["bConfiguredByCustomer"] is False
    assert result["bShared"] is False
    assert result["bInherited"] is False
    assert result["record_text"] == "Service Provider Corporate"


@staticmethod
def test_map_origination_single_service_provider_system_specific():
    """Test mapping origination for single Service Provider System Specific record"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import map_origination

    # Test data with single Service Provider System Specific record
    cis_data = {"record1": {"regscale_control_id": "AC-2", "control_origination": "Service Provider System Specific"}}

    result = map_origination("AC-2", cis_data)

    # Verify the correct flag is set
    assert result["bServiceProviderCorporate"] is False
    assert result["bServiceProviderSystemSpecific"] is True
    assert result["bServiceProviderHybrid"] is False
    assert result["bProvidedByCustomer"] is False
    assert result["bConfiguredByCustomer"] is False
    assert result["bShared"] is False
    assert result["bInherited"] is False
    assert result["record_text"] == "Service Provider System Specific"


@staticmethod
def test_map_origination_single_service_provider_hybrid():
    """Test mapping origination for single Service Provider Hybrid record"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import map_origination

    # Test data with single Service Provider Hybrid record
    cis_data = {
        "record1": {
            "regscale_control_id": "AC-3",
            "control_origination": "Service Provider Hybrid (Corporate and System Specific)",
        }
    }

    result = map_origination("AC-3", cis_data)

    # Verify the correct flag is set
    assert result["bServiceProviderCorporate"] is False
    assert result["bServiceProviderSystemSpecific"] is False
    assert result["bServiceProviderHybrid"] is True
    assert result["bProvidedByCustomer"] is False
    assert result["bConfiguredByCustomer"] is False
    assert result["bShared"] is False
    assert result["bInherited"] is False
    assert result["record_text"] == "Service Provider Hybrid (Corporate and System Specific)"


@staticmethod
def test_map_origination_single_provided_by_customer():
    """Test mapping origination for single Provided by Customer record"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import map_origination

    # Test data with single Provided by Customer record
    cis_data = {
        "record1": {
            "regscale_control_id": "AC-4",
            "control_origination": "Provided by Customer (Customer System Specific)",
        }
    }

    result = map_origination("AC-4", cis_data)

    # Verify the correct flag is set
    assert result["bServiceProviderCorporate"] is False
    assert result["bServiceProviderSystemSpecific"] is False
    assert result["bServiceProviderHybrid"] is False
    assert result["bProvidedByCustomer"] is True
    assert result["bConfiguredByCustomer"] is False
    assert result["bShared"] is False
    assert result["bInherited"] is False
    assert result["record_text"] == "Provided by Customer (Customer System Specific)"


@staticmethod
def test_map_origination_single_configured_by_customer():
    """Test mapping origination for single Configured by Customer record"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import map_origination

    # Test data with single Configured by Customer record
    cis_data = {
        "record1": {
            "regscale_control_id": "AC-5",
            "control_origination": "Configured by Customer (Customer System Specific)",
        }
    }

    result = map_origination("AC-5", cis_data)

    # Verify the correct flag is set
    assert result["bServiceProviderCorporate"] is False
    assert result["bServiceProviderSystemSpecific"] is False
    assert result["bServiceProviderHybrid"] is False
    assert result["bProvidedByCustomer"] is False
    assert result["bConfiguredByCustomer"] is True
    assert result["bShared"] is False
    assert result["bInherited"] is False
    assert result["record_text"] == "Configured by Customer (Customer System Specific)"


@staticmethod
def test_map_origination_single_shared():
    """Test mapping origination for single Shared record"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import map_origination

    # Test data with single Shared record
    cis_data = {
        "record1": {
            "regscale_control_id": "AC-6",
            "control_origination": "Shared (Service Provider and Customer Responsibility)",
        }
    }

    result = map_origination("AC-6", cis_data)

    # Verify the correct flag is set
    assert result["bServiceProviderCorporate"] is False
    assert result["bServiceProviderSystemSpecific"] is False
    assert result["bServiceProviderHybrid"] is False
    assert result["bProvidedByCustomer"] is False
    assert result["bConfiguredByCustomer"] is False
    assert result["bShared"] is True
    assert result["bInherited"] is False
    assert result["record_text"] == "Shared (Service Provider and Customer Responsibility)"


@staticmethod
def test_map_origination_single_inherited():
    """Test mapping origination for single Inherited record"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import map_origination

    # Test data with single Inherited record
    cis_data = {
        "record1": {
            "regscale_control_id": "AC-7",
            "control_origination": "Inherited from pre-existing FedRAMP Authorization",
        }
    }

    result = map_origination("AC-7", cis_data)

    # Verify the correct flag is set
    assert result["bServiceProviderCorporate"] is False
    assert result["bServiceProviderSystemSpecific"] is False
    assert result["bServiceProviderHybrid"] is False
    assert result["bProvidedByCustomer"] is False
    assert result["bConfiguredByCustomer"] is False
    assert result["bShared"] is False
    assert result["bInherited"] is True
    assert result["record_text"] == "Inherited from pre-existing FedRAMP Authorization"


@staticmethod
def test_map_origination_multiple_records_same_control():
    """Test mapping origination for multiple records with the same control ID"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import map_origination

    # Test data with multiple records for the same control
    cis_data = {
        "record1": {"regscale_control_id": "AC-8", "control_origination": "Service Provider Corporate"},
        "record2": {"regscale_control_id": "AC-8", "control_origination": "Service Provider System Specific"},
    }

    result = map_origination("AC-8", cis_data)

    # Verify multiple flags are set
    assert result["bServiceProviderCorporate"] is True
    assert result["bServiceProviderSystemSpecific"] is True
    assert result["bServiceProviderHybrid"] is False
    assert result["bProvidedByCustomer"] is False
    assert result["bConfiguredByCustomer"] is False
    assert result["bShared"] is False
    assert result["bInherited"] is False
    # Verify record_text contains both originations
    assert "Service Provider Corporate" in result["record_text"]
    assert "Service Provider System Specific" in result["record_text"]


@staticmethod
def test_map_origination_no_matching_records():
    """Test mapping origination when no matching records are found"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import map_origination

    # Test data with no matching records
    cis_data = {"record1": {"regscale_control_id": "AC-9", "control_origination": "Service Provider Corporate"}}

    result = map_origination("AC-10", cis_data)

    # Verify all flags are False
    assert result["bServiceProviderCorporate"] is False
    assert result["bServiceProviderSystemSpecific"] is False
    assert result["bServiceProviderHybrid"] is False
    assert result["bProvidedByCustomer"] is False
    assert result["bConfiguredByCustomer"] is False
    assert result["bShared"] is False
    assert result["bInherited"] is False
    assert result["record_text"] == ""


@staticmethod
def test_map_origination_case_insensitive_matching():
    """Test mapping origination with case insensitive control ID matching"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import map_origination

    # Test data with different case control IDs
    cis_data = {
        "record1": {"regscale_control_id": "ac-11", "control_origination": "Service Provider Corporate"},
        "record2": {"regscale_control_id": "AC-11", "control_origination": "Service Provider System Specific"},
    }

    result = map_origination("ac-11", cis_data)

    # Verify both records are matched (case insensitive)
    assert result["bServiceProviderCorporate"] is True
    assert result["bServiceProviderSystemSpecific"] is True
    assert result["bServiceProviderHybrid"] is False
    assert result["bProvidedByCustomer"] is False
    assert result["bConfiguredByCustomer"] is False
    assert result["bShared"] is False
    assert result["bInherited"] is False
    assert "Service Provider Corporate" in result["record_text"]
    assert "Service Provider System Specific" in result["record_text"]


@staticmethod
def test_map_origination_missing_control_origination():
    """Test mapping origination when control_origination field is missing"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import map_origination

    # Test data with missing control_origination
    cis_data = {
        "record1": {
            "regscale_control_id": "AC-12"
            # Missing control_origination field
        }
    }

    result = map_origination("AC-12", cis_data)

    # Verify all flags are False
    assert result["bServiceProviderCorporate"] is False
    assert result["bServiceProviderSystemSpecific"] is False
    assert result["bServiceProviderHybrid"] is False
    assert result["bProvidedByCustomer"] is False
    assert result["bConfiguredByCustomer"] is False
    assert result["bShared"] is False
    assert result["bInherited"] is False
    assert result["record_text"] == ""


@staticmethod
def test_map_origination_missing_regscale_control_id():
    """Test mapping origination when regscale_control_id field is missing"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import map_origination

    # Test data with missing regscale_control_id
    cis_data = {
        "record1": {
            "control_origination": "Service Provider Corporate"
            # Missing regscale_control_id field
        }
    }

    result = map_origination("AC-13", cis_data)

    # Verify all flags are False
    assert result["bServiceProviderCorporate"] is False
    assert result["bServiceProviderSystemSpecific"] is False
    assert result["bServiceProviderHybrid"] is False
    assert result["bProvidedByCustomer"] is False
    assert result["bConfiguredByCustomer"] is False
    assert result["bShared"] is False
    assert result["bInherited"] is False
    assert result["record_text"] == ""


@staticmethod
def test_map_origination_empty_cis_data():
    """Test mapping origination with empty CIS data"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import map_origination

    # Test data with empty CIS data
    cis_data = {}

    result = map_origination("AC-14", cis_data)

    # Verify all flags are False
    assert result["bServiceProviderCorporate"] is False
    assert result["bServiceProviderSystemSpecific"] is False
    assert result["bServiceProviderHybrid"] is False
    assert result["bProvidedByCustomer"] is False
    assert result["bConfiguredByCustomer"] is False
    assert result["bShared"] is False
    assert result["bInherited"] is False
    assert result["record_text"] == ""


@staticmethod
def test_map_origination_unknown_origination():
    """Test mapping origination with unknown origination string"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import map_origination

    # Test data with unknown origination
    cis_data = {"record1": {"regscale_control_id": "AC-15", "control_origination": "Unknown Origination Type"}}

    result = map_origination("AC-15", cis_data)

    # Verify all flags are False (unknown origination doesn't match any mapping)
    assert result["bServiceProviderCorporate"] is False
    assert result["bServiceProviderSystemSpecific"] is False
    assert result["bServiceProviderHybrid"] is False
    assert result["bProvidedByCustomer"] is False
    assert result["bConfiguredByCustomer"] is False
    assert result["bShared"] is False
    assert result["bInherited"] is False
    assert result["record_text"] == "Unknown Origination Type"


@staticmethod
def test_map_origination_complex_mixed_scenario():
    """Test mapping origination with complex mixed scenario"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import map_origination

    # Test data with complex mixed scenario
    cis_data = {
        "record1": {"regscale_control_id": "AC-16", "control_origination": "Service Provider Corporate"},
        "record2": {
            "regscale_control_id": "AC-16",
            "control_origination": "Shared (Service Provider and Customer Responsibility)",
        },
        "record3": {
            "regscale_control_id": "AC-16",
            "control_origination": "Inherited from pre-existing FedRAMP Authorization",
        },
    }

    result = map_origination("AC-16", cis_data)

    # Verify multiple flags are set
    assert result["bServiceProviderCorporate"] is True
    assert result["bServiceProviderSystemSpecific"] is False
    assert result["bServiceProviderHybrid"] is False
    assert result["bProvidedByCustomer"] is False
    assert result["bConfiguredByCustomer"] is False
    assert result["bShared"] is True
    assert result["bInherited"] is True
    # Verify record_text contains all originations
    assert "Service Provider Corporate" in result["record_text"]
    assert "Shared (Service Provider and Customer Responsibility)" in result["record_text"]
    assert "Inherited from pre-existing FedRAMP Authorization" in result["record_text"]


@staticmethod
def test_map_origination_partial_string_matching():
    """Test mapping origination with partial string matching"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import map_origination

    # Test data with partial string matches
    cis_data = {
        "record1": {
            "regscale_control_id": "AC-17",
            "control_origination": "Some text Service Provider Corporate more text",
        },
        "record2": {"regscale_control_id": "AC-17", "control_origination": "Prefix Shared suffix"},
    }

    result = map_origination("AC-17", cis_data)

    # Verify flags are set based on partial matches
    assert result["bServiceProviderCorporate"] is True
    assert result["bServiceProviderSystemSpecific"] is False
    assert result["bServiceProviderHybrid"] is False
    assert result["bProvidedByCustomer"] is False
    assert result["bConfiguredByCustomer"] is False
    assert result["bShared"] is False
    assert result["bInherited"] is False
    # Verify record_text contains the full origination strings
    assert "Some text Service Provider Corporate more text" in result["record_text"]
    assert "Prefix Shared suffix" in result["record_text"]


@staticmethod
def test_map_origination_duplicate_origination_text():
    """Test mapping origination with duplicate origination text"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import map_origination

    # Test data with duplicate origination text
    cis_data = {
        "record1": {"regscale_control_id": "AC-18", "control_origination": "Service Provider Corporate"},
        "record2": {"regscale_control_id": "AC-18", "control_origination": "Service Provider Corporate"},  # Duplicate
    }

    result = map_origination("AC-18", cis_data)

    # Verify flag is set
    assert result["bServiceProviderCorporate"] is True
    assert result["bServiceProviderSystemSpecific"] is False
    assert result["bServiceProviderHybrid"] is False
    assert result["bProvidedByCustomer"] is False
    assert result["bConfiguredByCustomer"] is False
    assert result["bShared"] is False
    assert result["bInherited"] is False
    # Verify record_text contains the origination only once (no duplicates)
    assert result["record_text"] == "Service Provider Corporate"


@staticmethod
def test_map_origination_empty_control_origination():
    """Test mapping origination with empty control_origination string"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import map_origination

    # Test data with empty control_origination
    cis_data = {"record1": {"regscale_control_id": "AC-19", "control_origination": ""}}

    result = map_origination("AC-19", cis_data)

    # Verify all flags are False
    assert result["bServiceProviderCorporate"] is False
    assert result["bServiceProviderSystemSpecific"] is False
    assert result["bServiceProviderHybrid"] is False
    assert result["bProvidedByCustomer"] is False
    assert result["bConfiguredByCustomer"] is False
    assert result["bShared"] is False
    assert result["bInherited"] is False
    assert result["record_text"] == ""


@staticmethod
def test_map_origination_result_structure():
    """Test that the result structure is consistent"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import map_origination

    # Test data
    cis_data = {"record1": {"regscale_control_id": "AC-20", "control_origination": "Service Provider Corporate"}}

    result = map_origination("AC-20", cis_data)

    # Verify all expected keys are present
    expected_keys = [
        "bServiceProviderCorporate",
        "bServiceProviderSystemSpecific",
        "bServiceProviderHybrid",
        "bProvidedByCustomer",
        "bConfiguredByCustomer",
        "bShared",
        "bInherited",
        "record_text",
    ]

    for key in expected_keys:
        assert key in result
        assert isinstance(result[key], (bool, str))


@staticmethod
def test_transform_control():
    """Test the transform_control function with various control ID patterns."""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import transform_control

    # Test cases for control IDs with numeric enhancements
    assert transform_control("AC-1 (1)") == "ac-1.1"
    assert transform_control("SI-2 (5)") == "si-2.5"
    assert transform_control("AU-3 (10)") == "au-3.10"
    assert transform_control("CM-4 (2)") == "cm-4.2"

    # Test cases for control IDs with letter enhancements (should be stripped)
    assert transform_control("AC-1 (a)") == "ac-1"
    assert transform_control("SI-2 (b)") == "si-2"
    assert transform_control("AU-3 (z)") == "au-3"
    assert transform_control("CM-4 (x)") == "cm-4"

    # Test cases for control IDs with uppercase letter enhancements
    assert transform_control("AC-1 (A)") == "ac-1 (a)"
    assert transform_control("SI-2 (B)") == "si-2 (b)"
    assert transform_control("AU-3 (Z)") == "au-3 (z)"

    # Test cases for basic control IDs without enhancements
    assert transform_control("AC-1") == "ac-1"
    assert transform_control("SI-2") == "si-2"
    assert transform_control("AU-3") == "au-3"
    assert transform_control("CM-4") == "cm-4"

    # Test cases for different control families
    assert transform_control("IA-1 (1)") == "ia-1.1"
    assert transform_control("MP-1 (2)") == "mp-1.2"
    assert transform_control("PE-1 (3)") == "pe-1.3"
    assert transform_control("PL-1 (4)") == "pl-1.4"
    assert transform_control("PS-1 (5)") == "ps-1.5"
    assert transform_control("RA-1 (6)") == "ra-1.6"
    assert transform_control("SA-1 (7)") == "sa-1.7"
    assert transform_control("SC-1 (8)") == "sc-1.8"
    assert transform_control("SR-1 (9)") == "sr-1.9"

    # Test cases for edge cases and malformed patterns
    assert transform_control("AC1") == "ac1"  # No dash
    assert transform_control("AC-1a") == "ac-1a"  # Letter without parentheses
    assert transform_control("") == ""  # Empty string

    # Test cases for mixed case input
    assert transform_control("Ac-1 (1)") == "ac-1.1"
    assert transform_control("aC-1 (1)") == "ac-1.1"
    assert transform_control("AC-1 (A)") == "ac-1 (a)"

    # Test cases for large numbers
    assert transform_control("AC-1 (999)") == "ac-1.999"
    assert transform_control("SI-2 (1000)") == "si-2.1000"

    # Test cases for single digit controls
    assert transform_control("A-1 (1)") == "a-1.1"
    assert transform_control("B-2 (2)") == "b-2.2"


@staticmethod
def test_get_responsibility_single_service_provider_corporate():
    """Test getting responsibility for single Service Provider Corporate"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import get_responsibility

    # Test data with single Service Provider Corporate responsibility
    origination_bool = {
        "bServiceProviderCorporate": True,
        "bServiceProviderSystemSpecific": False,
        "bServiceProviderHybrid": False,
        "bProvidedByCustomer": False,
        "bConfiguredByCustomer": False,
        "bInherited": False,
        "bShared": False,
    }

    result = get_responsibility(origination_bool)

    assert result == "Service Provider Corporate"


@staticmethod
def test_get_responsibility_single_service_provider_system_specific():
    """Test getting responsibility for single Service Provider System Specific"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import get_responsibility

    # Test data with single Service Provider System Specific responsibility
    origination_bool = {
        "bServiceProviderCorporate": False,
        "bServiceProviderSystemSpecific": True,
        "bServiceProviderHybrid": False,
        "bProvidedByCustomer": False,
        "bConfiguredByCustomer": False,
        "bInherited": False,
        "bShared": False,
    }

    result = get_responsibility(origination_bool)

    assert result == "Service Provider System Specific"


@staticmethod
def test_get_responsibility_single_service_provider_hybrid():
    """Test getting responsibility for single Service Provider Hybrid"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import get_responsibility

    # Test data with single Service Provider Hybrid responsibility
    origination_bool = {
        "bServiceProviderCorporate": False,
        "bServiceProviderSystemSpecific": False,
        "bServiceProviderHybrid": True,
        "bProvidedByCustomer": False,
        "bConfiguredByCustomer": False,
        "bInherited": False,
        "bShared": False,
    }

    result = get_responsibility(origination_bool)

    assert result == "Service Provider Hybrid (Corporate and System Specific)"


@staticmethod
def test_get_responsibility_single_provided_by_customer():
    """Test getting responsibility for single Provided by Customer"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import get_responsibility

    # Test data with single Provided by Customer responsibility
    origination_bool = {
        "bServiceProviderCorporate": False,
        "bServiceProviderSystemSpecific": False,
        "bServiceProviderHybrid": False,
        "bProvidedByCustomer": True,
        "bConfiguredByCustomer": False,
        "bInherited": False,
        "bShared": False,
    }

    result = get_responsibility(origination_bool)

    assert result == "Provided by Customer (Customer System Specific)"


@staticmethod
def test_get_responsibility_single_configured_by_customer():
    """Test getting responsibility for single Configured by Customer"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import get_responsibility

    # Test data with single Configured by Customer responsibility
    origination_bool = {
        "bServiceProviderCorporate": False,
        "bServiceProviderSystemSpecific": False,
        "bServiceProviderHybrid": False,
        "bProvidedByCustomer": False,
        "bConfiguredByCustomer": True,
        "bInherited": False,
        "bShared": False,
    }

    result = get_responsibility(origination_bool)

    assert result == "Configured by Customer (Customer System Specific)"


@staticmethod
def test_get_responsibility_single_inherited():
    """Test getting responsibility for single Inherited"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import get_responsibility

    # Test data with single Inherited responsibility
    origination_bool = {
        "bServiceProviderCorporate": False,
        "bServiceProviderSystemSpecific": False,
        "bServiceProviderHybrid": False,
        "bProvidedByCustomer": False,
        "bConfiguredByCustomer": False,
        "bInherited": True,
        "bShared": False,
    }

    result = get_responsibility(origination_bool)

    assert result == "Inherited from pre-existing FedRAMP Authorization"


@staticmethod
def test_get_responsibility_single_shared():
    """Test getting responsibility for single Shared"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import get_responsibility

    # Test data with single Shared responsibility
    origination_bool = {
        "bServiceProviderCorporate": False,
        "bServiceProviderSystemSpecific": False,
        "bServiceProviderHybrid": False,
        "bProvidedByCustomer": False,
        "bConfiguredByCustomer": False,
        "bInherited": False,
        "bShared": True,
    }

    result = get_responsibility(origination_bool)

    assert result == "Shared (Service Provider and Customer Responsibility)"


@staticmethod
def test_get_responsibility_multiple_responsibilities():
    """Test getting responsibility for multiple responsibilities"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import get_responsibility

    # Test data with multiple responsibilities
    origination_bool = {
        "bServiceProviderCorporate": True,
        "bServiceProviderSystemSpecific": True,
        "bServiceProviderHybrid": False,
        "bProvidedByCustomer": False,
        "bConfiguredByCustomer": False,
        "bInherited": False,
        "bShared": False,
    }

    result = get_responsibility(origination_bool)

    # Should return comma-separated string
    expected = "Service Provider Corporate,Service Provider System Specific"
    assert result == expected


@staticmethod
def test_get_responsibility_all_responsibilities():
    """Test getting responsibility for all responsibilities"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import get_responsibility

    # Test data with all responsibilities
    origination_bool = {
        "bServiceProviderCorporate": True,
        "bServiceProviderSystemSpecific": True,
        "bServiceProviderHybrid": True,
        "bProvidedByCustomer": True,
        "bConfiguredByCustomer": True,
        "bInherited": True,
        "bShared": True,
    }

    result = get_responsibility(origination_bool)

    # Should return comma-separated string with all responsibilities
    expected = "Service Provider Corporate,Service Provider System Specific,Service Provider Hybrid (Corporate and System Specific),Provided by Customer (Customer System Specific),Configured by Customer (Customer System Specific),Inherited from pre-existing FedRAMP Authorization,Shared (Service Provider and Customer Responsibility)"
    assert result == expected


@staticmethod
def test_get_responsibility_no_responsibilities():
    """Test getting responsibility when no responsibilities are set"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import ControlImplementationStatus, get_responsibility

    # Test data with no responsibilities
    origination_bool = {
        "bServiceProviderCorporate": False,
        "bServiceProviderSystemSpecific": False,
        "bServiceProviderHybrid": False,
        "bProvidedByCustomer": False,
        "bConfiguredByCustomer": False,
        "bInherited": False,
        "bShared": False,
    }

    result = get_responsibility(origination_bool)

    # Should return NA when no responsibilities are found
    assert result == ControlImplementationStatus.NA.value


@staticmethod
def test_get_responsibility_empty_dict():
    """Test getting responsibility with empty dictionary"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import ControlImplementationStatus, get_responsibility

    # Test data with empty dictionary
    origination_bool = {}

    result = get_responsibility(origination_bool)

    # Should return NA when no responsibilities are found
    assert result == ControlImplementationStatus.NA.value


@staticmethod
def test_get_responsibility_missing_keys():
    """Test getting responsibility with missing boolean keys"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import get_responsibility

    # Test data with missing keys
    origination_bool = {
        "bServiceProviderCorporate": True
        # Missing other keys
    }

    result = get_responsibility(origination_bool)

    # Should return only the present responsibility
    assert result == "Service Provider Corporate"


@staticmethod
def test_get_responsibility_mixed_true_false():
    """Test getting responsibility with mixed true and false values"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import get_responsibility

    # Test data with mixed true and false values
    origination_bool = {
        "bServiceProviderCorporate": True,
        "bServiceProviderSystemSpecific": False,
        "bServiceProviderHybrid": True,
        "bProvidedByCustomer": False,
        "bConfiguredByCustomer": True,
        "bInherited": False,
        "bShared": True,
    }

    result = get_responsibility(origination_bool)

    # Should return only the True responsibilities
    expected = "Service Provider Corporate,Service Provider Hybrid (Corporate and System Specific),Configured by Customer (Customer System Specific),Shared (Service Provider and Customer Responsibility)"
    assert result == expected


@staticmethod
def test_get_responsibility_none_values():
    """Test getting responsibility with None values"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import ControlImplementationStatus, get_responsibility

    # Test data with None values
    origination_bool = {
        "bServiceProviderCorporate": None,
        "bServiceProviderSystemSpecific": None,
        "bServiceProviderHybrid": None,
        "bProvidedByCustomer": None,
        "bConfiguredByCustomer": None,
        "bInherited": None,
        "bShared": None,
    }

    result = get_responsibility(origination_bool)

    # Should return NA when all values are None (falsy)
    assert result == ControlImplementationStatus.NA.value


@staticmethod
def test_get_responsibility_mixed_none_and_true():
    """Test getting responsibility with mixed None and True values"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import get_responsibility

    # Test data with mixed None and True values
    origination_bool = {
        "bServiceProviderCorporate": None,
        "bServiceProviderSystemSpecific": True,
        "bServiceProviderHybrid": None,
        "bProvidedByCustomer": True,
        "bConfiguredByCustomer": None,
        "bInherited": None,
        "bShared": None,
    }

    result = get_responsibility(origination_bool)

    # Should return only the True responsibilities
    expected = "Service Provider System Specific,Provided by Customer (Customer System Specific)"
    assert result == expected


@staticmethod
def test_get_responsibility_mixed_values():
    """Test getting responsibility with string values"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import get_responsibility

    # Test data with string values
    origination_bool = {
        "bServiceProviderCorporate": True,
        "bServiceProviderSystemSpecific": False,
        "bServiceProviderHybrid": True,
        "bProvidedByCustomer": False,
        "bConfiguredByCustomer": True,
        "bInherited": False,
        "bShared": True,
    }

    result = get_responsibility(origination_bool)

    # Should return only the truthy string values
    expected = "Service Provider Corporate,Service Provider Hybrid (Corporate and System Specific),Configured by Customer (Customer System Specific),Shared (Service Provider and Customer Responsibility)"
    assert result == expected


@staticmethod
def test_get_responsibility_integer_values():
    """Test getting responsibility with integer values"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import get_responsibility

    # Test data with integer values
    origination_bool = {
        "bServiceProviderCorporate": 1,
        "bServiceProviderSystemSpecific": 0,
        "bServiceProviderHybrid": 1,
        "bProvidedByCustomer": 0,
        "bConfiguredByCustomer": 1,
        "bInherited": 0,
        "bShared": 1,
    }

    result = get_responsibility(origination_bool)

    # Should return only the non-zero values
    expected = "Service Provider Corporate,Service Provider Hybrid (Corporate and System Specific),Configured by Customer (Customer System Specific),Shared (Service Provider and Customer Responsibility)"
    assert result == expected


@staticmethod
def test_get_responsibility_extra_keys():
    """Test getting responsibility with extra keys in dictionary"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import get_responsibility

    # Test data with extra keys
    origination_bool = {
        "bServiceProviderCorporate": True,
        "bServiceProviderSystemSpecific": False,
        "bServiceProviderHybrid": True,
        "bProvidedByCustomer": False,
        "bConfiguredByCustomer": True,
        "bInherited": False,
        "bShared": True,
        "extraKey1": True,
        "extraKey2": False,
        "record_text": "Some text",
    }

    result = get_responsibility(origination_bool)

    # Should return only the expected responsibilities, ignoring extra keys
    expected = "Service Provider Corporate,Service Provider Hybrid (Corporate and System Specific),Configured by Customer (Customer System Specific),Shared (Service Provider and Customer Responsibility)"
    assert result == expected


@staticmethod
def test_get_responsibility_order_preservation():
    """Test that responsibility order is preserved as defined in the function"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import get_responsibility

    # Test data with all responsibilities
    origination_bool = {
        "bServiceProviderCorporate": True,
        "bServiceProviderSystemSpecific": True,
        "bServiceProviderHybrid": True,
        "bProvidedByCustomer": True,
        "bConfiguredByCustomer": True,
        "bInherited": True,
        "bShared": True,
    }

    result = get_responsibility(origination_bool)

    # Verify the order matches the order in the function
    responsibilities = result.split(",")
    assert responsibilities[0] == "Service Provider Corporate"
    assert responsibilities[1] == "Service Provider System Specific"
    assert responsibilities[2] == "Service Provider Hybrid (Corporate and System Specific)"
    assert responsibilities[3] == "Provided by Customer (Customer System Specific)"
    assert responsibilities[4] == "Configured by Customer (Customer System Specific)"
    assert responsibilities[5] == "Inherited from pre-existing FedRAMP Authorization"
    assert responsibilities[6] == "Shared (Service Provider and Customer Responsibility)"


@staticmethod
def test_get_responsibility_constant_values():
    """Test that the responsibility strings match the defined constants"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import (
        CONFIGURED_BY_CUSTOMER,
        INHERITED,
        PROVIDED_BY_CUSTOMER,
        SERVICE_PROVIDER_CORPORATE,
        SERVICE_PROVIDER_HYBRID,
        SERVICE_PROVIDER_SYSTEM_SPECIFIC,
        SHARED,
        get_responsibility,
    )

    # Test data with single responsibility
    origination_bool = {
        "bServiceProviderCorporate": True,
        "bServiceProviderSystemSpecific": False,
        "bServiceProviderHybrid": False,
        "bProvidedByCustomer": False,
        "bConfiguredByCustomer": False,
        "bInherited": False,
        "bShared": False,
    }

    result = get_responsibility(origination_bool)

    # Verify the result matches the constant
    assert result == SERVICE_PROVIDER_CORPORATE

    # Test with different responsibility
    origination_bool = {
        "bServiceProviderCorporate": False,
        "bServiceProviderSystemSpecific": True,
        "bServiceProviderHybrid": False,
        "bProvidedByCustomer": False,
        "bConfiguredByCustomer": False,
        "bInherited": False,
        "bShared": False,
    }

    result = get_responsibility(origination_bool)
    assert result == SERVICE_PROVIDER_SYSTEM_SPECIFIC


@staticmethod
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.logger")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.get_current_datetime")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.map_implementation_status")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.map_origination")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.get_responsibility")
def test_parse_control_details_basic(
    mock_get_responsibility,
    mock_map_origination,
    mock_map_implementation_status,
    mock_get_current_datetime,
    mock_logger,
):
    """Test basic functionality of parse_control_details method"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import parse_control_details

    # Mock return values
    mock_get_current_datetime.return_value = "2024-01-01T00:00:00Z"
    mock_map_implementation_status.return_value = "Implemented"
    mock_map_origination.return_value = {
        "bServiceProviderCorporate": True,
        "bServiceProviderSystemSpecific": False,
        "bServiceProviderHybrid": False,
        "bProvidedByCustomer": False,
        "bConfiguredByCustomer": False,
        "bInherited": False,
        "bShared": False,
        "record_text": "Service Provider Corporate",
    }
    mock_get_responsibility.return_value = "Service Provider Corporate"

    # Test data
    regscale_control_mock = Mock(spec=ControlImplementation)
    # Create a mock SecurityControl
    security_control_mock = Mock(spec=SecurityControl)

    # Set up the mock with typical attributes
    security_control_mock.id = 456
    security_control_mock.controlId = "AC-1"
    security_control_mock.sortId = "AC-1"
    security_control_mock.title = "Access Control Policy and Procedures"
    security_control_mock.description = "The organization develops, documents, and disseminates to [Assignment: organization-defined personnel or roles]:"
    security_control_mock.controlType = "Control"
    security_control_mock.references = "NIST SP 800-53 Rev 5"
    security_control_mock.relatedControls = "AC-2, AC-3, AC-4"
    security_control_mock.subControls = None
    security_control_mock.enhancements = None
    security_control_mock.family = "Access Control"
    security_control_mock.mappings = None
    security_control_mock.assessmentPlan = None
    security_control_mock.weight = 1.0
    security_control_mock.catalogueId = 1
    security_control_mock.catalogueID = 1  # Alias for catalogueId
    security_control_mock.practiceLevel = None
    security_control_mock.objectives = []
    security_control_mock.tests = []
    security_control_mock.parameters = []
    security_control_mock.archived = False
    security_control_mock.createdById = "user123"
    security_control_mock.dateCreated = "2024-01-01T00:00:00Z"
    security_control_mock.lastUpdatedById = "user123"
    security_control_mock.dateLastUpdated = "2024-01-01T00:00:00Z"
    security_control_mock.criticality = "High"
    security_control_mock.isPublic = True
    security_control_mock.uuid = "12345678-1234-1234-1234-123456789012"

    # Mock class methods
    security_control_mock.get_list_by_catalog = Mock(return_value=[])
    security_control_mock.lookup_control = Mock(return_value=security_control_mock)
    security_control_mock.lookup_control_by_name = Mock(return_value=security_control_mock)

    # Mock the __hash__ method
    security_control_mock.__hash__ = Mock(return_value=hash(("AC-1", 1)))

    # Mock the __eq__ method
    security_control_mock.__eq__ = Mock(return_value=True)
    # Set up the mock with typical attributes
    regscale_control_mock.id = 123
    regscale_control_mock.controlID = 456
    regscale_control_mock.status = ControlImplementationStatus.FullyImplemented.value
    regscale_control_mock.parentId = 789
    regscale_control_mock.parentModule = "securityplans"
    regscale_control_mock.responsibility = "Service Provider Corporate"
    regscale_control_mock.dateCreated = "2024-01-01T00:00:00Z"
    regscale_control_mock.dateLastUpdated = "2024-01-01T00:00:00Z"
    regscale_control_mock.controlOwnerId = "user123"
    regscale_control_mock.createdById = "user123"
    regscale_control_mock.lastUpdatedById = "user123"

    # Set up boolean flags for origination
    regscale_control_mock.bServiceProviderCorporate = True
    regscale_control_mock.bServiceProviderSystemSpecific = False
    regscale_control_mock.bServiceProviderHybrid = False
    regscale_control_mock.bConfiguredByCustomer = False
    regscale_control_mock.bProvidedByCustomer = False
    regscale_control_mock.bShared = False
    regscale_control_mock.bInherited = False
    regscale_control_mock.bInheritedFedrampAuthorization = False

    # Set up status boolean flags
    regscale_control_mock.bStatusImplemented = True
    regscale_control_mock.bStatusPartiallyImplemented = False
    regscale_control_mock.bStatusPlanned = False
    regscale_control_mock.bStatusAlternative = False
    regscale_control_mock.bStatusNotApplicable = False

    # Mock the save method
    regscale_control_mock.save.return_value = True

    # Mock the update method
    regscale_control_mock.update.return_value = True
    cis_data = {
        "record1": {
            "regscale_control_id": "AC-1",
            "implementation_status": "Implemented",
            "control_origination": "Service Provider Corporate",
        }
    }

    # Call the method
    result = parse_control_details(
        version="rev5", control_imp=regscale_control_mock, control=security_control_mock, cis_data=cis_data
    )
    if result is True:
        result = regscale_control_mock
    # Verify the result structure
    assert isinstance(result, ControlImplementation)

    # Verify the values
    assert result.status == "Implemented"
    assert result.responsibility == "Service Provider Corporate"


@staticmethod
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.logger")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.RegscaleVersion")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.clean_customer_responsibility")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.get_multi_status")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.UPDATED_IMPLEMENTATION_OBJECTIVES")
def test_update_imp_objective_new_objective_creation(
    mock_updated_objectives,
    mock_get_multi_status,
    mock_clean_customer_responsibility,
    mock_regscale_version,
    mock_logger,
):
    """Test creating a new implementation objective when none exists"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import ImplementationObjective, update_imp_objective
    from regscale.models.regscale_models.control_implementation import ControlImplementation
    from regscale.models.regscale_models.control_objective import ControlObjective

    # Mock RegScale version
    mock_regscale_version.meets_minimum_version.return_value = True

    # Mock helper functions
    mock_get_multi_status.return_value = "Implemented"
    mock_clean_customer_responsibility.return_value = "Customer responsibility text"

    # Create mock control implementation
    control_imp_mock = Mock(spec=ControlImplementation)
    control_imp_mock.id = 123
    control_imp_mock.controlID = 456
    control_imp_mock.responsibility = "Service Provider Corporate"

    # Create mock control objective
    control_objective_mock = Mock(spec=ControlObjective)
    control_objective_mock.id = 789
    control_objective_mock.name = "AC-1.1"
    control_objective_mock.securityControlId = 456
    control_objective_mock.parentObjectiveId = None

    # Create mock existing implementation objectives (empty list)
    existing_imp_obj = []

    # Test record data
    record = {
        "cis": {"control_origination": "Service Provider Corporate, Service Provider System Specific"},
        "crm": {
            "specific_inheritance_and_customer_agency_csp_responsibilities": "Customer specific responsibilities",
            "can_be_inherited_from_csp": "No",
        },
    }

    # Call the method
    update_imp_objective(
        leverage_auth_id=999,
        existing_imp_obj=existing_imp_obj,
        imp=control_imp_mock,
        objectives=[control_objective_mock],
        record=record,
    )

    # Verify that a new ImplementationObjective was added to the set
    mock_updated_objectives.add.assert_called_once()

    # Get the created objective
    created_objective = mock_updated_objectives.add.call_args[0][0]

    # Verify the objective properties
    assert created_objective.id == 0
    assert created_objective.implementationId == 123
    assert created_objective.objectiveId == 789
    assert created_objective.securityControlId == 456
    assert created_objective.status == "Implemented"
    assert created_objective.responsibility == "Service Provider Corporate,Service Provider System Specific"
    assert created_objective.cloudResponsibility == ""
    assert created_objective.customerResponsibility == "Customer responsibility text"
    assert created_objective.inherited is False
    assert created_objective.authorizationId == 999

    # Verify logging
    mock_logger.debug.assert_called()


@staticmethod
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.logger")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.RegscaleVersion")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.clean_customer_responsibility")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.get_multi_status")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.UPDATED_IMPLEMENTATION_OBJECTIVES")
def test_update_imp_objective_existing_objective_update(
    mock_updated_objectives,
    mock_get_multi_status,
    mock_clean_customer_responsibility,
    mock_regscale_version,
    mock_logger,
):
    """Test updating an existing implementation objective"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import ImplementationObjective, update_imp_objective
    from regscale.models.regscale_models.control_implementation import ControlImplementation
    from regscale.models.regscale_models.control_objective import ControlObjective

    # Mock RegScale version
    mock_regscale_version.meets_minimum_version.return_value = False

    # Mock helper functions
    mock_get_multi_status.return_value = "Partially Implemented"
    mock_clean_customer_responsibility.return_value = "Updated customer responsibility"

    # Create mock control implementation
    control_imp_mock = Mock(spec=ControlImplementation)
    control_imp_mock.id = 123
    control_imp_mock.controlID = 456
    control_imp_mock.responsibility = ""

    # Create mock control objective
    control_objective_mock = Mock(spec=ControlObjective)
    control_objective_mock.id = 789
    control_objective_mock.name = "AC-1.1"
    control_objective_mock.securityControlId = 456
    control_objective_mock.parentObjectiveId = None

    # Create mock existing implementation objective
    existing_imp_obj_mock = Mock(spec=ImplementationObjective)
    existing_imp_obj_mock.id = 555
    existing_imp_obj_mock.objectiveId = 789
    existing_imp_obj_mock.implementationId = 123
    existing_imp_obj_mock.status = "Implemented"
    existing_imp_obj_mock.responsibility = "Service Provider Corporate"
    existing_imp_obj_mock.cloudResponsibility = ""
    existing_imp_obj_mock.customerResponsibility = ""

    existing_imp_obj = [existing_imp_obj_mock]

    # Test record data
    record = {
        "cis": {"control_origination": "Service Provider Corporate"},
        "crm": {
            "specific_inheritance_and_customer_agency_csp_responsibilities": "Updated customer responsibilities",
            "can_be_inherited_from_csp": "Yes",
        },
    }

    # Call the method
    update_imp_objective(
        leverage_auth_id=999,
        existing_imp_obj=existing_imp_obj,
        imp=control_imp_mock,
        objectives=[control_objective_mock],
        record=record,
    )

    # Verify the existing objective was updated
    assert existing_imp_obj_mock.status == "Partially Implemented"
    assert existing_imp_obj_mock.responsibility == "Service Provider Corporate"
    assert existing_imp_obj_mock.cloudResponsibility == "Updated customer responsibility"
    assert existing_imp_obj_mock.customerResponsibility == ""

    # Verify the updated objective was added to the set
    mock_updated_objectives.add.assert_called_once_with(existing_imp_obj_mock)

    # Verify logging
    mock_logger.debug.assert_called()


@staticmethod
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.logger")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.RegscaleVersion")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.clean_customer_responsibility")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.get_multi_status")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.UPDATED_IMPLEMENTATION_OBJECTIVES")
def test_update_imp_objective_mismatched_control_id(
    mock_updated_objectives,
    mock_get_multi_status,
    mock_clean_customer_responsibility,
    mock_regscale_version,
    mock_logger,
):
    """Test that objectives with mismatched control IDs are skipped"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import ImplementationObjective, update_imp_objective
    from regscale.models.regscale_models.control_implementation import ControlImplementation
    from regscale.models.regscale_models.control_objective import ControlObjective

    # Mock RegScale version
    mock_regscale_version.meets_minimum_version.return_value = True

    # Create mock control implementation
    control_imp_mock = Mock(spec=ControlImplementation)
    control_imp_mock.id = 123
    control_imp_mock.controlID = 456
    control_imp_mock.responsibility = "Service Provider Corporate"

    # Create mock control objective with mismatched securityControlId
    control_objective_mock = Mock(spec=ControlObjective)
    control_objective_mock.id = 789
    control_objective_mock.name = "AC-1.1"
    control_objective_mock.securityControlId = 999  # Different from control_imp_mock.controlID
    control_objective_mock.parentObjectiveId = None

    # Create mock existing implementation objectives (empty list)
    existing_imp_obj = []

    # Test record data
    record = {
        "cis": {"control_origination": "Service Provider Corporate"},
        "crm": {
            "specific_inheritance_and_customer_agency_csp_responsibilities": "Customer responsibilities",
            "can_be_inherited_from_csp": "No",
        },
    }

    # Call the method
    update_imp_objective(
        leverage_auth_id=999,
        existing_imp_obj=existing_imp_obj,
        imp=control_imp_mock,
        objectives=[control_objective_mock],
        record=record,
    )

    # Verify that no objective was added (due to mismatched control ID)
    mock_updated_objectives.add.assert_not_called()


@staticmethod
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.logger")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.RegscaleVersion")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.clean_customer_responsibility")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.get_multi_status")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.UPDATED_IMPLEMENTATION_OBJECTIVES")
def test_update_imp_objective_fallback_responsibility(
    mock_updated_objectives,
    mock_get_multi_status,
    mock_clean_customer_responsibility,
    mock_regscale_version,
    mock_logger,
):
    """Test fallback responsibility when control_origination is empty"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import (
        SERVICE_PROVIDER_CORPORATE,
        ImplementationObjective,
        update_imp_objective,
    )
    from regscale.models.regscale_models.control_implementation import ControlImplementation
    from regscale.models.regscale_models.control_objective import ControlObjective

    # Mock RegScale version
    mock_regscale_version.meets_minimum_version.return_value = True

    # Mock helper functions
    mock_get_multi_status.return_value = "Implemented"
    mock_clean_customer_responsibility.return_value = ""

    # Create mock control implementation
    control_imp_mock = Mock(spec=ControlImplementation)
    control_imp_mock.id = 123
    control_imp_mock.controlID = 456
    control_imp_mock.responsibility = None  # No existing responsibility

    # Create mock control objective
    control_objective_mock = Mock(spec=ControlObjective)
    control_objective_mock.id = 789
    control_objective_mock.name = "AC-1.1"
    control_objective_mock.securityControlId = 456
    control_objective_mock.parentObjectiveId = None

    # Create mock existing implementation objectives (empty list)
    existing_imp_obj = []

    # Test record data with empty control_origination
    record = {
        "cis": {"control_origination": ""},  # Empty origination
        "crm": {"specific_inheritance_and_customer_agency_csp_responsibilities": "", "can_be_inherited_from_csp": "No"},
    }

    # Call the method
    update_imp_objective(
        leverage_auth_id=999,
        existing_imp_obj=existing_imp_obj,
        imp=control_imp_mock,
        objectives=[control_objective_mock],
        record=record,
    )

    # Verify that a new ImplementationObjective was added to the set
    mock_updated_objectives.add.assert_called_once()

    # Get the created objective
    created_objective = mock_updated_objectives.add.call_args[0][0]

    # Verify the objective uses the fallback responsibility
    assert created_objective.responsibility == ""


@staticmethod
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.get_pandas")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm._drop_rows_nan")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.error_and_exit")
def test_parse_instructions_worksheet_rev5_success(
    mock_error_and_exit,
    mock_drop_rows_nan,
    mock_get_pandas,
):
    """Test successful parsing of Rev5 instructions worksheet (using real DataFrame for iloc and dropna)"""

    from regscale.integrations.public.fedramp.fedramp_cis_crm import parse_instructions_worksheet

    # Create a real DataFrame that simulates the instructions sheet
    data = {
        "Unnamed: 0": ["", "", "System Name (CSP to complete all cells)", "Test System 1", "Test System 2"],
        "Unnamed: 1": ["", "", "CSP", "CSP A", "CSP B"],
        "Unnamed: 2": ["", "", "System Identifier", "SYS-001", "SYS-002"],
        "Unnamed: 3": ["", "", "Impact Level", "High", "Moderate"],
        "Unnamed: 4": ["", "", "Other Column", "Other Data", "Other Data"],
    }
    dict_df = {"Instructions": pd.DataFrame(data)}

    # Call the method
    result = parse_instructions_worksheet(dict_df, "rev5", "Instructions")

    # Verify the result
    expected_result = [
        {
            "Unnamed: 0": "System Name (CSP to complete all cells)",
            "Unnamed: 1": "CSP",
            "Unnamed: 2": "System Identifier",
            "Unnamed: 3": "Impact Level",
            "Unnamed: 4": "Other Column",
        },
        {
            "Unnamed: 0": "Test System 1",
            "Unnamed: 1": "CSP A",
            "Unnamed: 2": "SYS-001",
            "Unnamed: 3": "High",
            "Unnamed: 4": "Other Data",
        },
        {
            "Unnamed: 0": "Test System 2",
            "Unnamed: 1": "CSP B",
            "Unnamed: 2": "SYS-002",
            "Unnamed: 3": "Moderate",
            "Unnamed: 4": "Other Data",
        },
    ]
    assert result == expected_result


@staticmethod
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.get_pandas")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm._drop_rows_nan")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.error_and_exit")
def test_parse_instructions_worksheet_rev4_success(
    mock_error_and_exit,
    mock_drop_rows_nan,
    mock_get_pandas,
):
    """Test successful parsing of Rev5 instructions worksheet (using real DataFrame for iloc and dropna)"""
    import pandas as pd

    from regscale.integrations.public.fedramp.fedramp_cis_crm import parse_instructions_worksheet

    # Create a real DataFrame that simulates the instructions sheet
    data = {
        "Unnamed: 0": ["", "", "System Name (CSP to complete all cells)", "Test System 1", "Test System 2"],
        "Unnamed: 1": ["", "", "CSP", "CSP A", "CSP B"],
        "Unnamed: 2": ["", "", "System Identifier", "SYS-001", "SYS-002"],
        "Unnamed: 3": ["", "", "Impact Level", "High", "Moderate"],
        "Unnamed: 4": ["", "", "Other Column", "Other Data", "Other Data"],
    }
    dict_df = {"Instructions": pd.DataFrame(data)}

    # Call the method
    result = parse_instructions_worksheet(dict_df, "rev", "Instructions")

    # Verify the result
    expected_result = [
        {
            "System Name (CSP to complete all cells)": "Test System 1",
            "CSP": "CSP A",
            "System Identifier": "SYS-001",
            "Impact Level": "High",
            "Other Column": "Other Data",
        },
        {
            "System Name (CSP to complete all cells)": "Test System 2",
            "CSP": "CSP B",
            "System Identifier": "SYS-002",
            "Impact Level": "Moderate",
            "Other Column": "Other Data",
        },
    ]
    assert result == expected_result


@staticmethod
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.get_pandas")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm._drop_rows_nan")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.error_and_exit")
def test_parse_instructions_worksheet_missing_columns(
    mock_error_and_exit,
    mock_drop_rows_nan,
    mock_get_pandas,
):
    """Test instructions worksheet parsing when required columns are missing"""
    import pandas as pd

    from regscale.integrations.public.fedramp.fedramp_cis_crm import parse_instructions_worksheet

    # Create DataFrame with missing required columns
    data = {
        "Unnamed: 0": ["", "", "Wrong Column", "Data 1"],
        "Unnamed: 1": ["", "", "Another Wrong Column", "Data 2"],
    }
    dict_df = {"Instructions": pd.DataFrame(data)}

    # Mock _drop_rows_nan to return dataframe with wrong columns
    mock_drop_rows_nan.return_value = pd.DataFrame(
        {
            "Wrong Column": ["Data 1"],
            "Another Wrong Column": ["Data 2"],
        }
    )

    # Call the method - should raise KeyError and call error_and_exit
    parse_instructions_worksheet(dict_df, "rev4", "Instructions")

    # Verify error_and_exit was called with appropriate message
    mock_error_and_exit.assert_called_once()
    error_message = mock_error_and_exit.call_args[0][0]
    assert "Unable to find the relevant columns" in error_message
    assert "rev4" in error_message


@staticmethod
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.get_pandas")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm._drop_rows_nan")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.error_and_exit")
def test_parse_instructions_worksheet_custom_sheet_name(
    mock_error_and_exit,
    mock_drop_rows_nan,
    mock_get_pandas,
):
    """Test instructions worksheet parsing with custom sheet name"""
    import pandas as pd

    from regscale.integrations.public.fedramp.fedramp_cis_crm import parse_instructions_worksheet

    # Create DataFrame with custom sheet name
    data = {
        "Unnamed: 0": ["", "", "System Name", "Test System 1"],
        "Unnamed: 1": ["", "", "CSP", "CSP A"],
        "Unnamed: 2": ["", "", "Impact Level", "High"],
    }
    dict_df = {"Custom Instructions": pd.DataFrame(data)}

    # Mock _drop_rows_nan to return processed dataframe
    mock_drop_rows_nan.return_value = pd.DataFrame(
        {
            "System Name": ["Test System 1"],
            "CSP": ["CSP A"],
            "Impact Level": ["High"],
        }
    )

    # Call the method with custom sheet name
    result = parse_instructions_worksheet(dict_df, "rev4", "Custom Instructions")

    # Verify the result
    expected_result = [
        {
            "System Name": "Test System 1",
            "CSP": "CSP A",
            "Impact Level": "High",
        },
    ]
    assert result == expected_result


@staticmethod
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.get_pandas")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm._drop_rows_nan")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.error_and_exit")
def test_parse_instructions_worksheet_empty_data(
    mock_error_and_exit,
    mock_drop_rows_nan,
    mock_get_pandas,
):
    """Test instructions worksheet parsing with empty data"""
    import pandas as pd

    from regscale.integrations.public.fedramp.fedramp_cis_crm import parse_instructions_worksheet

    # Create empty DataFrame
    data = {
        "Unnamed: 0": ["", "", ""],
        "Unnamed: 1": ["", "", ""],
        "Unnamed: 2": ["", "", ""],
    }
    dict_df = {"Instructions": pd.DataFrame(data)}

    # Mock _drop_rows_nan to return empty dataframe
    mock_drop_rows_nan.return_value = pd.DataFrame()

    # Call the method
    result = parse_instructions_worksheet(dict_df, "rev4", "Instructions")

    assert result == [{"Unnamed: 0": "", "Unnamed: 1": "", "Unnamed: 2": ""}]


@staticmethod
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.get_pandas")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm._drop_rows_nan")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.error_and_exit")
def test_parse_instructions_worksheet_rev5_with_nan_handling(
    mock_error_and_exit,
    mock_drop_rows_nan,
    mock_get_pandas,
):
    """Test Rev5 instructions worksheet parsing with proper NaN handling"""
    import datetime

    import pandas as pd

    from regscale.integrations.public.fedramp.fedramp_cis_crm import parse_instructions_worksheet

    # Create DataFrame with NaN values in some columns
    data = [
        {
            "Unnamed: 0": pd.NA,
            "Unnamed: 1": pd.NA,
            "FedRAMP® System Security Plan (SSP) Appendix J: Netskope GovCloud CIS and CRM Workbook\n\n": pd.NA,
            "Unnamed: 3": pd.NA,
            "Unnamed: 4": pd.NA,
            "Unnamed: 5": pd.NA,
        },
        {
            "Unnamed: 0": pd.NA,
            "Unnamed: 1": "System Name",
            "FedRAMP® System Security Plan (SSP) Appendix J: Netskope GovCloud CIS and CRM Workbook\n\n": pd.NA,
            "Unnamed: 3": pd.NA,
            "Unnamed: 4": pd.NA,
            "Unnamed: 5": pd.NA,
        },
        {
            "Unnamed: 0": pd.NA,
            "Unnamed: 1": "CSP",
            "FedRAMP® System Security Plan (SSP) Appendix J: Netskope GovCloud CIS and CRM Workbook\n\n": "System Name",
            "Unnamed: 3": pd.NA,
            "Unnamed: 4": "System Identifier",
            "Unnamed: 5": "Impact Level",
        },
        {
            "Unnamed: 0": pd.NA,
            "Unnamed: 1": "Netskope, Inc.",
            "FedRAMP® System Security Plan (SSP) Appendix J: Netskope GovCloud CIS and CRM Workbook\n\n": "Netskope, Inc.",
            "Unnamed: 3": pd.NA,
            "Unnamed: 4": "NGC",
            "Unnamed: 5": "High",
        },
        {
            "Unnamed: 0": pd.NA,
            "Unnamed: 1": pd.NA,
            "FedRAMP® System Security Plan (SSP) Appendix J: Netskope GovCloud CIS and CRM Workbook\n\n": pd.NA,
            "Unnamed: 3": pd.NA,
            "Unnamed: 4": pd.NA,
            "Unnamed: 5": pd.NA,
        },
        {
            "Unnamed: 0": pd.NA,
            "Unnamed: 1": "Document Revision History",
            "FedRAMP® System Security Plan (SSP) Appendix J: Netskope GovCloud CIS and CRM Workbook\n\n": pd.NA,
            "Unnamed: 3": pd.NA,
            "Unnamed: 4": pd.NA,
            "Unnamed: 5": pd.NA,
        },
    ]
    dict_df = {"Instructions": pd.DataFrame(data)}

    # Call the method
    result = parse_instructions_worksheet(dict_df, "rev5", "Instructions")

    # Verify the result
    expected_result = [
        {
            "Unnamed: 1": "CSP",
            "FedRAMP® System Security Plan (SSP) Appendix J: Netskope GovCloud CIS and CRM Workbook\n\n": "System Name",
            "Unnamed: 4": "System Identifier",
            "Unnamed: 5": "Impact Level",
        },
        {
            "Unnamed: 1": "Netskope, Inc.",
            "FedRAMP® System Security Plan (SSP) Appendix J: Netskope GovCloud CIS and CRM Workbook\n\n": "Netskope, Inc.",
            "Unnamed: 4": "NGC",
            "Unnamed: 5": "High",
        },
        {
            "Unnamed: 1": None,
            "FedRAMP® System Security Plan (SSP) Appendix J: Netskope GovCloud CIS and CRM Workbook\n\n": None,
            "Unnamed: 4": None,
            "Unnamed: 5": None,
        },
        {
            "Unnamed: 1": "Document Revision History",
            "FedRAMP® System Security Plan (SSP) Appendix J: Netskope GovCloud CIS and CRM Workbook\n\n": None,
            "Unnamed: 4": None,
            "Unnamed: 5": None,
        },
    ]
    assert result == expected_result


@staticmethod
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.get_pandas")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm._drop_rows_nan")
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.error_and_exit")
def test_parse_instructions_worksheet_rev5_csp_row_processing_basic(
    mock_error_and_exit,
    mock_drop_rows_nan,
    mock_get_pandas,
):
    """Basic test for the CSP row processing logic in rev5 instructions worksheet parsing"""
    import pandas as pd

    from regscale.integrations.public.fedramp.fedramp_cis_crm import parse_instructions_worksheet

    # Mock pandas module with real pandas functions
    mock_pandas = Mock()
    mock_get_pandas.return_value = mock_pandas
    mock_pandas.isna = pd.isna  # Use real pandas isna function

    # Create DataFrame that simulates the actual structure for rev5
    # The function expects to find a row with "CSP" in it, then use that row to set column names
    data = {
        "Unnamed: 0": [pd.NA, pd.NA, "CSP", "Netskope, Inc.", pd.NA],
        "Unnamed: 1": [pd.NA, pd.NA, "System Name", "Netskope, Inc.", pd.NA],
        "FedRAMP® System Security Plan (SSP) Appendix J: Netskope GovCloud CIS and CRM Workbook\n\n": [
            pd.NA,
            pd.NA,
            "System Identifier",
            "NGC",
            pd.NA,
        ],
        "Unnamed: 3": [pd.NA, pd.NA, pd.NA, pd.NA, pd.NA],
        "Unnamed: 4": [pd.NA, pd.NA, "Impact Level", "High", pd.NA],
        "Unnamed: 5": [pd.NA, pd.NA, pd.NA, pd.NA, pd.NA],
    }
    dict_df = {"Instructions": pd.DataFrame(data)}

    # Mock _drop_rows_nan to return the final processed dataframe
    final_df = pd.DataFrame(
        {
            "CSP": ["Netskope, Inc."],
            "System Name": ["Netskope, Inc."],
            "System Identifier": ["NGC"],
            "Impact Level": ["High"],
        }
    )
    mock_drop_rows_nan.return_value = final_df

    # Call the method
    result = parse_instructions_worksheet(dict_df, "rev5", "Instructions")

    # Verify the result
    expected_result = [
        {
            "CSP": "Netskope, Inc.",
            "System Name": "Netskope, Inc.",
            "System Identifier": "NGC",
            "Impact Level": "High",
        },
    ]
    assert result == expected_result

    # Verify that _drop_rows_nan was called
    mock_drop_rows_nan.assert_called_once()

    # Verify that error_and_exit was not called
    mock_error_and_exit.assert_not_called()


@staticmethod
@patch("regscale.integrations.public.fedramp.fedramp_cis_crm.update_imp_objective")
def test_process_single_record_basic(mock_update_imp_objective):
    """Basic test for the process_single_record function"""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import process_single_record
    from regscale.models.regscale_models.control_implementation import ControlImplementation
    from regscale.models.regscale_models.control_objective import ControlObjective

    # Create mock control implementation
    mock_implementation = Mock(spec=ControlImplementation)
    mock_implementation.id = 123
    mock_implementation.controlID = 456

    # Create mock control objective
    mock_objective = Mock(spec=ControlObjective)
    mock_objective.id = 789
    mock_objective.otherId = "ac-2_smt.h.1"  # This should match the source returned by find_by_source
    mock_objective.name = "h.1"

    # Test data
    kwargs = {
        "version": "rev5",
        "leveraged_auth_id": 999,
        "implementation": mock_implementation,
        "record": {
            "cis": {"control_id": "AC-2(h)"},
            "crm": {"can_be_inherited_from_csp": "No"},
        },
        "control_objectives": [mock_objective],
        "existing_objectives": [],
    }
    rev_4_kwargs = {
        "version": "rev4",
        "leveraged_auth_id": 999,
        "implementation": mock_implementation,
        "record": {"cis": {"control_id": "AC-02 (h)"}},
        "control_objectives": [mock_objective],
    }

    # Call the function
    errors, result = process_single_record(**kwargs)
    rev_4_errors, rev_4_result = process_single_record(**rev_4_kwargs)
    # Verify the result - the behavior changed due to improved control ID parsing
    # Now it finds sub-parts instead of failing to find the exact match for both rev4 and rev5
    assert errors == [
        "AC-2(h): Control exists with 1 sub-parts. Update import file.",
    ]
    assert result is None
    assert rev_4_errors == [
        "AC-02 (h): Control exists with 1 sub-parts. Update import file.",
    ]
    assert rev_4_result is None


# Tests for new functions added after PartMapper removal


@staticmethod
def test_convert_to_oscal_identifier_basic_patterns():
    """Test _convert_to_oscal_identifier with basic control ID patterns."""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import _convert_to_oscal_identifier

    # Pattern 1: Control enhancement - AC-6(1), AC-02 (01)
    assert _convert_to_oscal_identifier("AC-6(1)") == "ac-6.1_smt"
    assert _convert_to_oscal_identifier("AC-02(01)") == "ac-2.1_smt"
    assert _convert_to_oscal_identifier("SI-4(2)") == "si-4.2_smt"
    assert _convert_to_oscal_identifier("AU-12(10)") == "au-12.10_smt"

    # Pattern 2: Control part - AC-1(a), AC-01 (a)
    assert _convert_to_oscal_identifier("AC-1(a)") == "ac-1_smt.a"
    assert _convert_to_oscal_identifier("AC-01(b)") == "ac-1_smt.b"
    assert _convert_to_oscal_identifier("SI-2(c)") == "si-2_smt.c"
    assert _convert_to_oscal_identifier("AU-3(z)") == "au-3_smt.z"

    # Pattern 3: Control enhancement part - AC-6(1)(a), AC-02 (07) (a)
    assert _convert_to_oscal_identifier("AC-6(1)(a)") == "ac-6.1_smt.a"
    assert _convert_to_oscal_identifier("AC-02(07)(b)") == "ac-2.7_smt.b"
    assert _convert_to_oscal_identifier("SI-4(2)(c)") == "si-4.2_smt.c"
    assert _convert_to_oscal_identifier("AU-12(3)(z)") == "au-12.3_smt.z"

    # Pattern 4: Base control - AC-1, AC-01
    assert _convert_to_oscal_identifier("AC-1") == "ac-1_smt"
    assert _convert_to_oscal_identifier("AC-01") == "ac-1_smt"
    assert _convert_to_oscal_identifier("SI-4") == "si-4_smt"
    assert _convert_to_oscal_identifier("AU-12") == "au-12_smt"


@staticmethod
def test_convert_to_oscal_identifier_with_spaces():
    """Test _convert_to_oscal_identifier with various spacing patterns."""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import _convert_to_oscal_identifier

    # Spaces around parentheses
    assert _convert_to_oscal_identifier("AC-6 (1)") == "ac-6.1_smt"
    assert _convert_to_oscal_identifier("AC-6( 1)") == "ac-6.1_smt"
    assert _convert_to_oscal_identifier("AC-6(1 )") == "ac-6.1_smt"
    assert _convert_to_oscal_identifier("AC-6 ( 1 )") == "ac-6.1_smt"

    # Multiple patterns with spaces
    assert _convert_to_oscal_identifier("AC-2 (a)") == "ac-2_smt.a"
    assert _convert_to_oscal_identifier("AC-2 ( a )") == "ac-2_smt.a"
    assert _convert_to_oscal_identifier("AC-6 (1) (a)") == "ac-6.1_smt.a"
    assert _convert_to_oscal_identifier("AC-6 ( 1 ) ( a )") == "ac-6.1_smt.a"


@staticmethod
def test_convert_to_oscal_identifier_invalid_patterns():
    """Test _convert_to_oscal_identifier with invalid or unsupported patterns."""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import _convert_to_oscal_identifier

    # Invalid patterns should return None
    assert _convert_to_oscal_identifier("") is None
    assert _convert_to_oscal_identifier("AC") is None
    assert _convert_to_oscal_identifier("AC-") is None
    assert _convert_to_oscal_identifier("AC-1-2") is None
    assert _convert_to_oscal_identifier("1-AC") is None
    assert _convert_to_oscal_identifier("AC-1(") is None
    assert _convert_to_oscal_identifier("AC-1)") is None
    assert _convert_to_oscal_identifier("AC-1(a)(b)(c)") is None  # Too many parts
    assert _convert_to_oscal_identifier("AC-1(1a)") is None  # Mixed number and letter


@staticmethod
def test_convert_to_oscal_identifier_case_handling():
    """Test _convert_to_oscal_identifier handles case correctly."""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import _convert_to_oscal_identifier

    # Mixed case input should still work
    assert _convert_to_oscal_identifier("ac-1") == "ac-1_smt"
    assert _convert_to_oscal_identifier("Ac-1") == "ac-1_smt"
    assert _convert_to_oscal_identifier("aC-1") == "ac-1_smt"
    assert _convert_to_oscal_identifier("AC-1") == "ac-1_smt"

    # Letter parts should remain lowercase
    assert _convert_to_oscal_identifier("AC-1(A)") == "ac-1_smt.a"
    assert _convert_to_oscal_identifier("AC-1(a)") == "ac-1_smt.a"


@staticmethod
def test_find_exact_objective_by_other_id_found():
    """Test _find_exact_objective_by_other_id when objective is found."""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import _find_exact_objective_by_other_id

    # Create mock control objectives
    mock_obj1 = Mock()
    mock_obj1.otherId = "ac-1_smt"

    mock_obj2 = Mock()
    mock_obj2.otherId = "ac-2.1_smt"

    mock_obj3 = Mock()
    mock_obj3.otherId = "ac-3_smt.a"

    control_objectives = [mock_obj1, mock_obj2, mock_obj3]

    # Test exact matches
    assert _find_exact_objective_by_other_id("ac-1_smt", control_objectives) is True
    assert _find_exact_objective_by_other_id("ac-2.1_smt", control_objectives) is True
    assert _find_exact_objective_by_other_id("ac-3_smt.a", control_objectives) is True


@staticmethod
def test_find_exact_objective_by_other_id_not_found():
    """Test _find_exact_objective_by_other_id when objective is not found."""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import _find_exact_objective_by_other_id

    # Create mock control objectives
    mock_obj1 = Mock()
    mock_obj1.otherId = "ac-1_smt"

    mock_obj2 = Mock()
    mock_obj2.otherId = "ac-2.1_smt"

    control_objectives = [mock_obj1, mock_obj2]

    # Test non-matching cases
    assert _find_exact_objective_by_other_id("ac-3_smt", control_objectives) is False
    assert _find_exact_objective_by_other_id("ac-1_smt.a", control_objectives) is False
    assert _find_exact_objective_by_other_id("si-1_smt", control_objectives) is False


@staticmethod
def test_find_exact_objective_by_other_id_missing_attribute():
    """Test _find_exact_objective_by_other_id with objects missing otherId attribute."""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import _find_exact_objective_by_other_id

    # Create mock control objectives, some without otherId
    mock_obj1 = Mock()
    mock_obj1.otherId = "ac-1_smt"

    mock_obj2 = Mock(spec=[])  # No otherId attribute

    mock_obj3 = Mock()
    mock_obj3.otherId = "ac-2.1_smt"

    control_objectives = [mock_obj1, mock_obj2, mock_obj3]

    # Should still work despite missing attribute
    assert _find_exact_objective_by_other_id("ac-1_smt", control_objectives) is True
    assert _find_exact_objective_by_other_id("ac-2.1_smt", control_objectives) is True
    assert _find_exact_objective_by_other_id("ac-3_smt", control_objectives) is False


@staticmethod
def test_find_exact_objective_by_other_id_empty_list():
    """Test _find_exact_objective_by_other_id with empty control objectives list."""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import _find_exact_objective_by_other_id

    control_objectives = []

    # Should return False for empty list
    assert _find_exact_objective_by_other_id("ac-1_smt", control_objectives) is False
    assert _find_exact_objective_by_other_id("", control_objectives) is False


@staticmethod
def test_convert_oscal_to_rev4_control_label_basic():
    """Test _convert_oscal_to_rev4_control_label with basic patterns."""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import _convert_oscal_to_rev4_control_label

    # Single digit numbers should be zero-padded
    assert _convert_oscal_to_rev4_control_label("ac-1") == "ac-01"
    assert _convert_oscal_to_rev4_control_label("ac-2") == "ac-02"
    assert _convert_oscal_to_rev4_control_label("si-4") == "si-04"
    assert _convert_oscal_to_rev4_control_label("au-9") == "au-09"

    # Double digit numbers should remain unchanged
    assert _convert_oscal_to_rev4_control_label("ac-10") == "ac-10"
    assert _convert_oscal_to_rev4_control_label("ac-11") == "ac-11"
    assert _convert_oscal_to_rev4_control_label("si-12") == "si-12"


@staticmethod
def test_convert_oscal_to_rev4_control_label_with_enhancements():
    """Test _convert_oscal_to_rev4_control_label strips enhancements correctly."""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import _convert_oscal_to_rev4_control_label

    # Control enhancements should be stripped, base control should be padded
    assert _convert_oscal_to_rev4_control_label("ac-1.2") == "ac-01"
    assert _convert_oscal_to_rev4_control_label("ac-2.7") == "ac-02"
    assert _convert_oscal_to_rev4_control_label("si-4.10") == "si-04"
    assert _convert_oscal_to_rev4_control_label("au-12.3") == "au-12"

    # Multiple dots should also be handled
    assert _convert_oscal_to_rev4_control_label("ac-1.2.3") == "ac-01"


@staticmethod
def test_convert_oscal_to_rev4_control_label_edge_cases():
    """Test _convert_oscal_to_rev4_control_label with edge cases."""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import _convert_oscal_to_rev4_control_label

    # Invalid formats should return as-is
    assert _convert_oscal_to_rev4_control_label("ac") == "ac"
    assert _convert_oscal_to_rev4_control_label("ac-") == "ac-"
    assert _convert_oscal_to_rev4_control_label("1-ac") == "1-ac"
    assert _convert_oscal_to_rev4_control_label("") == ""

    # Already padded numbers should remain unchanged
    assert _convert_oscal_to_rev4_control_label("ac-01") == "ac-01"
    assert _convert_oscal_to_rev4_control_label("ac-01.2") == "ac-01"

    # Three digit numbers should remain unchanged
    assert _convert_oscal_to_rev4_control_label("ac-100") == "ac-100"


@staticmethod
def test_find_subpart_objectives_by_other_id_found():
    """Test _find_subpart_objectives_by_other_id when sub-parts are found."""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import _find_subpart_objectives_by_other_id

    # Create mock control objectives with sub-parts
    mock_obj1 = Mock()
    mock_obj1.otherId = "ac-2_smt.a"

    mock_obj2 = Mock()
    mock_obj2.otherId = "ac-2_smt.b"

    mock_obj3 = Mock()
    mock_obj3.otherId = "ac-2_smt.c"

    mock_obj4 = Mock()
    mock_obj4.otherId = "ac-3_smt.a"  # Different base control

    mock_obj5 = Mock()
    mock_obj5.otherId = "ac-2.1_smt.a"  # Enhancement sub-part

    control_objectives = [mock_obj1, mock_obj2, mock_obj3, mock_obj4, mock_obj5]

    # Test finding sub-parts for ac-2_smt
    result = _find_subpart_objectives_by_other_id("ac-2_smt", control_objectives)
    expected = ["ac-2_smt.a", "ac-2_smt.b", "ac-2_smt.c"]
    assert sorted(result) == sorted(expected)

    # Test finding sub-parts for ac-2.1_smt
    result = _find_subpart_objectives_by_other_id("ac-2.1_smt", control_objectives)
    expected = ["ac-2.1_smt.a"]
    assert result == expected


@staticmethod
def test_find_subpart_objectives_by_other_id_not_found():
    """Test _find_subpart_objectives_by_other_id when no sub-parts are found."""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import _find_subpart_objectives_by_other_id

    # Create mock control objectives without matching sub-parts
    mock_obj1 = Mock()
    mock_obj1.otherId = "ac-1_smt"

    mock_obj2 = Mock()
    mock_obj2.otherId = "ac-2_smt"

    mock_obj3 = Mock()
    mock_obj3.otherId = "si-4_smt.a"  # Different family

    control_objectives = [mock_obj1, mock_obj2, mock_obj3]

    # Test with base control that has no sub-parts
    result = _find_subpart_objectives_by_other_id("ac-3_smt", control_objectives)
    assert result == []

    # Test with non-existent control
    result = _find_subpart_objectives_by_other_id("zz-1_smt", control_objectives)
    assert result == []


@staticmethod
def test_find_subpart_objectives_by_other_id_empty_list():
    """Test _find_subpart_objectives_by_other_id with empty control objectives list."""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import _find_subpart_objectives_by_other_id

    control_objectives = []

    # Should return empty list for empty input
    result = _find_subpart_objectives_by_other_id("ac-1_smt", control_objectives)
    assert result == []


@staticmethod
def test_find_subpart_objectives_by_other_id_missing_attribute():
    """Test _find_subpart_objectives_by_other_id with objects missing otherId attribute."""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import _find_subpart_objectives_by_other_id

    # Create mock control objectives, some without otherId
    mock_obj1 = Mock()
    mock_obj1.otherId = "ac-2_smt.a"

    mock_obj2 = Mock(spec=[])  # No otherId attribute

    mock_obj3 = Mock()
    mock_obj3.otherId = "ac-2_smt.b"

    control_objectives = [mock_obj1, mock_obj2, mock_obj3]

    # Should work despite missing attributes
    result = _find_subpart_objectives_by_other_id("ac-2_smt", control_objectives)
    expected = ["ac-2_smt.a", "ac-2_smt.b"]
    assert sorted(result) == sorted(expected)


@staticmethod
def test_smart_find_by_source_exact_match():
    """Test smart_find_by_source when exact match is found."""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import smart_find_by_source

    # Create mock control objective with exact match
    mock_obj = Mock()
    mock_obj.otherId = "ac-1_smt"

    control_objectives = [mock_obj]

    # Test exact match scenarios
    source, parts, status = smart_find_by_source("AC-1", control_objectives)
    assert source == "ac-1_smt"
    assert parts == []
    assert status == "Found exact match: ac-1_smt"

    source, parts, status = smart_find_by_source("AC-01", control_objectives)
    assert source == "ac-1_smt"
    assert parts == []
    assert status == "Found exact match: ac-1_smt"


@staticmethod
def test_smart_find_by_source_subparts_found():
    """Test smart_find_by_source when sub-parts are found but no exact match."""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import smart_find_by_source

    # Create mock control objectives with sub-parts but no exact match
    mock_obj1 = Mock()
    mock_obj1.otherId = "ac-1_smt.a"

    mock_obj2 = Mock()
    mock_obj2.otherId = "ac-1_smt.b"

    control_objectives = [mock_obj1, mock_obj2]

    source, parts, status = smart_find_by_source("AC-1", control_objectives)
    assert source is None
    assert sorted(parts) == ["ac-1_smt.a", "ac-1_smt.b"]
    assert status == "Control exists with 2 sub-parts. Update import file."


@staticmethod
def test_smart_find_by_source_no_match():
    """Test smart_find_by_source when no match is found."""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import smart_find_by_source

    # Create mock control objectives that don't match
    mock_obj = Mock()
    mock_obj.otherId = "si-1_smt"

    control_objectives = [mock_obj]

    source, parts, status = smart_find_by_source("AC-1", control_objectives)
    assert source is None
    assert parts == []
    assert status == "No database match found for AC-1 (expected: ac-1_smt)"


@staticmethod
def test_smart_find_by_source_invalid_control():
    """Test smart_find_by_source with invalid control ID."""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import smart_find_by_source

    control_objectives = []

    # Invalid control ID that can't be converted to OSCAL
    source, parts, status = smart_find_by_source("INVALID", control_objectives)
    assert source is None
    assert parts == []
    assert status == "Unable to convert control INVALID to OSCAL format"


@staticmethod
def test_smart_find_by_source_enhancement_patterns():
    """Test smart_find_by_source with control enhancement patterns."""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import smart_find_by_source

    # Test control enhancement
    mock_obj = Mock()
    mock_obj.otherId = "ac-6.1_smt"
    control_objectives = [mock_obj]

    source, parts, status = smart_find_by_source("AC-6(1)", control_objectives)
    assert source == "ac-6.1_smt"
    assert parts == []
    assert status == "Found exact match: ac-6.1_smt"

    # Test control enhancement part
    mock_obj2 = Mock()
    mock_obj2.otherId = "ac-6.1_smt.a"
    control_objectives = [mock_obj2]

    source, parts, status = smart_find_by_source("AC-6(1)(a)", control_objectives)
    assert source == "ac-6.1_smt.a"
    assert parts == []
    assert status == "Found exact match: ac-6.1_smt.a"


@staticmethod
def test_smart_find_by_source_with_extra_spaces():
    """Test smart_find_by_source handles control IDs with extra spaces."""
    from regscale.integrations.public.fedramp.fedramp_cis_crm import smart_find_by_source

    mock_obj = Mock()
    mock_obj.otherId = "ac-6.1_smt.a"
    control_objectives = [mock_obj]

    # Test various spacing patterns
    source, parts, status = smart_find_by_source("AC-6 ( 1 ) ( a )", control_objectives)
    assert source == "ac-6.1_smt.a"
    assert parts == []
    assert status == "Found exact match: ac-6.1_smt.a"

    source, parts, status = smart_find_by_source("AC-6 ( 1 )", control_objectives)
    assert source is None
    assert parts == ["ac-6.1_smt.a"]
    assert status == "Control exists with 1 sub-parts. Update import file."
