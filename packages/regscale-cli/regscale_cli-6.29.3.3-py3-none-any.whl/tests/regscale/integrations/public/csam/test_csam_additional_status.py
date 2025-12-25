#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test CSAM Additional Status Integration"""

import logging
from unittest.mock import patch, MagicMock, call
import pytest

from regscale.integrations.public.csam.csam_additional_status import (
    import_csam_additional_status,
    get_additional_status,
)

# Test Constants
PATH = "regscale.integrations.public.csam.csam_additional_status"

# Sample test data
SAMPLE_SSP_MAP = {
    1: "10001",  # SSP ID: CSAM ID
    2: "10002",
    3: "10003",
}

SAMPLE_STATUS_RESPONSE = {
    "riskAssessmentDateCompleted": "2024-01-15",
    "riskAssessmentNextDueDate": "2025-01-15",
    "riskAssessmentExpirationDate": "2025-01-15",
    "systemSecurityPlanDateCompleted": "2024-02-01",
    "systemSecurityPlanNextDueDate": "2025-02-01",
    "configurationManagementDateCompleted": "2024-03-01",
    "configurationManagementNextDueDate": "2025-03-01",
}

SAMPLE_STATUS_FIELD_MAP = {
    "Risk Assessment Completed": 101,
    "Risk Assessment Next Due Date": 102,
    "Risk Assessment Expiration Date": 103,
    "SSP Completed": 104,
    "SSP Next Due Date": 105,
    "CM Completed": 106,
    "CM Next Due Date": 107,
}

SAMPLE_FORM_FIELD_VALUES = [
    {"record_id": 1, "record_module": "securityplans", "form_field_id": 101, "field_value": "2024-01-15"},
    {"record_id": 1, "record_module": "securityplans", "form_field_id": 102, "field_value": "2025-01-15"},
    {"record_id": 1, "record_module": "securityplans", "form_field_id": 103, "field_value": "2025-01-15"},
]


class TestImportCsamAdditionalStatus:
    """Tests for import_csam_additional_status function"""

    @patch(f"{PATH}.track", side_effect=lambda x, **kwargs: x)
    @patch(f"{PATH}.fix_form_field_value")
    @patch(f"{PATH}.get_additional_status")
    @patch(f"{PATH}.FormFieldValue.save_custom_fields")
    @patch(f"{PATH}.retrieve_ssps_custom_form_map")
    @patch(f"{PATH}.FormFieldValue.check_custom_fields")
    def test_import_csam_additional_status_success_multiple_ssps(
        self,
        mock_check_custom_fields,
        mock_retrieve_ssps,
        mock_save_custom_fields,
        mock_get_additional_status,
        mock_fix_form_field_value,
        mock_track,
        caplog,
    ):
        """Test successful import with multiple SSPs"""
        # Setup mocks
        mock_check_custom_fields.return_value = {"CSAM Id": 1}
        mock_retrieve_ssps.return_value = SAMPLE_SSP_MAP

        # Mock get_additional_status to return field values for each SSP
        mock_get_additional_status.side_effect = [
            SAMPLE_FORM_FIELD_VALUES.copy(),
            SAMPLE_FORM_FIELD_VALUES.copy(),
            SAMPLE_FORM_FIELD_VALUES.copy(),
        ]

        # Mock fix_form_field_value to return cleaned data
        expected_field_values = SAMPLE_FORM_FIELD_VALUES * 3
        mock_fix_form_field_value.return_value = expected_field_values

        # Execute
        with caplog.at_level(logging.INFO):
            import_csam_additional_status()

        # Verify
        assert mock_retrieve_ssps.call_count == 1
        assert mock_get_additional_status.call_count == 3
        mock_save_custom_fields.assert_called_once_with(expected_field_values)
        assert "Updated 3 Security Plans with contingency data" in caplog.text

    @patch(f"{PATH}.track", side_effect=lambda x, **kwargs: x)
    @patch(f"{PATH}.fix_form_field_value")
    @patch(f"{PATH}.get_additional_status")
    @patch(f"{PATH}.FormFieldValue.save_custom_fields")
    @patch(f"{PATH}.retrieve_ssps_custom_form_map")
    @patch(f"{PATH}.FormFieldValue.check_custom_fields")
    def test_import_csam_additional_status_with_import_ids(
        self,
        mock_check_custom_fields,
        mock_retrieve_ssps,
        mock_save_custom_fields,
        mock_get_additional_status,
        mock_fix_form_field_value,
        mock_track,
        caplog,
    ):
        """Test successful import with filtered SSP list"""
        # Setup mocks
        mock_check_custom_fields.return_value = {"CSAM Id": 1}
        large_ssp_map = {1: "10001", 2: "10002", 3: "10003", 4: "10004", 5: "10005"}
        mock_retrieve_ssps.return_value = large_ssp_map

        # Only import SSPs 1 and 3
        import_ids = [1, 3]

        mock_get_additional_status.side_effect = [
            SAMPLE_FORM_FIELD_VALUES.copy(),
            SAMPLE_FORM_FIELD_VALUES.copy(),
        ]

        expected_field_values = SAMPLE_FORM_FIELD_VALUES * 2
        mock_fix_form_field_value.return_value = expected_field_values

        # Execute
        with caplog.at_level(logging.INFO):
            import_csam_additional_status(import_ids=import_ids)

        # Verify only 2 SSPs processed
        assert mock_get_additional_status.call_count == 2
        mock_save_custom_fields.assert_called_once_with(expected_field_values)
        assert "Updated 2 Security Plans with contingency data" in caplog.text

    @patch(f"{PATH}.track", side_effect=lambda x, **kwargs: x)
    @patch(f"{PATH}.FormFieldValue.save_custom_fields")
    @patch(f"{PATH}.retrieve_ssps_custom_form_map")
    @patch(f"{PATH}.FormFieldValue.check_custom_fields")
    def test_import_csam_additional_status_empty_ssp_list(
        self,
        mock_check_custom_fields,
        mock_retrieve_ssps,
        mock_save_custom_fields,
        mock_track,
    ):
        """Test import with empty SSP list"""
        # Setup mocks - empty SSP map
        mock_check_custom_fields.return_value = {"CSAM Id": 1}
        mock_retrieve_ssps.return_value = {}

        # Execute
        import_csam_additional_status()

        # Verify early return - save_custom_fields should not be called
        mock_save_custom_fields.assert_not_called()

    @patch(f"{PATH}.track", side_effect=lambda x, **kwargs: x)
    @patch(f"{PATH}.fix_form_field_value")
    @patch(f"{PATH}.get_additional_status")
    @patch(f"{PATH}.FormFieldValue.save_custom_fields")
    @patch(f"{PATH}.retrieve_ssps_custom_form_map")
    @patch(f"{PATH}.FormFieldValue.check_custom_fields")
    def test_import_csam_additional_status_missing_csam_id(
        self,
        mock_check_custom_fields,
        mock_retrieve_ssps,
        mock_save_custom_fields,
        mock_get_additional_status,
        mock_fix_form_field_value,
        mock_track,
        caplog,
    ):
        """Test import with SSP missing CSAM ID"""
        # Setup mocks - one SSP has None as CSAM ID
        mock_check_custom_fields.return_value = {"CSAM Id": 1}
        ssp_map_with_none = {1: "10001", 2: None, 3: "10003"}
        mock_retrieve_ssps.return_value = ssp_map_with_none

        mock_get_additional_status.side_effect = [
            SAMPLE_FORM_FIELD_VALUES.copy(),
            SAMPLE_FORM_FIELD_VALUES.copy(),
        ]

        expected_field_values = SAMPLE_FORM_FIELD_VALUES * 2
        mock_fix_form_field_value.return_value = expected_field_values

        # Execute
        with caplog.at_level(logging.ERROR):
            import_csam_additional_status()

        # Verify error logged for SSP with no CSAM ID
        assert "Could not find CSAM ID for SSP id: 2" in caplog.text

        # Verify only 2 SSPs (1 and 3) processed successfully
        assert mock_get_additional_status.call_count == 2
        mock_save_custom_fields.assert_called_once_with(expected_field_values)

    @patch(f"{PATH}.track", side_effect=lambda x, **kwargs: x)
    @patch(f"{PATH}.get_additional_status")
    @patch(f"{PATH}.FormFieldValue.save_custom_fields")
    @patch(f"{PATH}.retrieve_ssps_custom_form_map")
    @patch(f"{PATH}.FormFieldValue.check_custom_fields")
    def test_import_csam_additional_status_csam_api_failure(
        self,
        mock_check_custom_fields,
        mock_retrieve_ssps,
        mock_save_custom_fields,
        mock_get_additional_status,
        mock_track,
    ):
        """Test import with CSAM API failure"""
        # Setup mocks
        mock_check_custom_fields.return_value = {"CSAM Id": 1}
        mock_retrieve_ssps.return_value = SAMPLE_SSP_MAP

        # Mock get_additional_status to return empty lists (API failure)
        mock_get_additional_status.return_value = []

        # Execute
        import_csam_additional_status()

        # Verify save_custom_fields not called when no field values
        mock_save_custom_fields.assert_not_called()

    @patch(f"{PATH}.track", side_effect=lambda x, **kwargs: x)
    @patch(f"{PATH}.fix_form_field_value")
    @patch(f"{PATH}.get_additional_status")
    @patch(f"{PATH}.FormFieldValue.save_custom_fields")
    @patch(f"{PATH}.retrieve_ssps_custom_form_map")
    @patch(f"{PATH}.FormFieldValue.check_custom_fields")
    def test_import_csam_additional_status_partial_data(
        self,
        mock_check_custom_fields,
        mock_retrieve_ssps,
        mock_save_custom_fields,
        mock_get_additional_status,
        mock_fix_form_field_value,
        mock_track,
        caplog,
    ):
        """Test import with partial CSAM data"""
        # Setup mocks
        mock_check_custom_fields.return_value = {"CSAM Id": 1}
        mock_retrieve_ssps.return_value = {1: "10001"}

        # Return only some field values
        partial_field_values = [SAMPLE_FORM_FIELD_VALUES[0]]
        mock_get_additional_status.return_value = partial_field_values
        mock_fix_form_field_value.return_value = partial_field_values

        # Execute
        with caplog.at_level(logging.INFO):
            import_csam_additional_status()

        # Verify partial data processed successfully
        mock_save_custom_fields.assert_called_once_with(partial_field_values)
        assert "Updated 1 Security Plans with contingency data" in caplog.text

    @patch(f"{PATH}.track", side_effect=lambda x, **kwargs: x)
    @patch(f"{PATH}.fix_form_field_value")
    @patch(f"{PATH}.get_additional_status")
    @patch(f"{PATH}.FormFieldValue.save_custom_fields")
    @patch(f"{PATH}.retrieve_ssps_custom_form_map")
    @patch(f"{PATH}.FormFieldValue.check_custom_fields")
    def test_import_csam_additional_status_with_invalid_field_values(
        self,
        mock_check_custom_fields,
        mock_retrieve_ssps,
        mock_save_custom_fields,
        mock_get_additional_status,
        mock_fix_form_field_value,
        mock_track,
    ):
        """Test fix_form_field_value integration with invalid field values"""
        # Setup mocks
        mock_check_custom_fields.return_value = {"CSAM Id": 1}
        mock_retrieve_ssps.return_value = {1: "10001"}

        # Mock field values with "None" strings
        invalid_field_values = [
            {"record_id": 1, "record_module": "securityplans", "form_field_id": 101, "field_value": "None"},
            {"record_id": 1, "record_module": "securityplans", "form_field_id": 102, "field_value": "2025-01-15"},
        ]
        mock_get_additional_status.return_value = invalid_field_values

        # Mock fix_form_field_value to clean the data
        cleaned_field_values = [
            {"record_id": 1, "record_module": "securityplans", "form_field_id": 101, "field_value": ""},
            {"record_id": 1, "record_module": "securityplans", "form_field_id": 102, "field_value": "2025-01-15"},
        ]
        mock_fix_form_field_value.return_value = cleaned_field_values

        # Execute
        import_csam_additional_status()

        # Verify fix_form_field_value was called with invalid data
        mock_fix_form_field_value.assert_called_once_with(invalid_field_values)

        # Verify save_custom_fields called with cleaned data
        mock_save_custom_fields.assert_called_once_with(cleaned_field_values)

    @patch(f"{PATH}.track", side_effect=lambda x, **kwargs: x)
    @patch(f"{PATH}.fix_form_field_value")
    @patch(f"{PATH}.get_additional_status")
    @patch(f"{PATH}.FormFieldValue.save_custom_fields")
    @patch(f"{PATH}.retrieve_ssps_custom_form_map")
    @patch(f"{PATH}.FormFieldValue.check_custom_fields")
    def test_import_csam_additional_status_with_empty_import_ids(
        self,
        mock_check_custom_fields,
        mock_retrieve_ssps,
        mock_save_custom_fields,
        mock_get_additional_status,
        mock_fix_form_field_value,
        mock_track,
        caplog,
    ):
        """
        Test import with explicitly empty import_ids list.
        In Python, [] is falsy, so the code falls back to list(ssp_map.keys()).
        This means passing [] is equivalent to passing None - all SSPs are processed.
        """
        # Setup mocks
        mock_check_custom_fields.return_value = {"CSAM Id": 1}
        mock_retrieve_ssps.return_value = SAMPLE_SSP_MAP

        # Pass empty list explicitly - [] is falsy so code uses ssp_map.keys() instead
        # ssps = import_ids if import_ids else list(ssp_map.keys())
        import_ids = []

        mock_get_additional_status.side_effect = [
            SAMPLE_FORM_FIELD_VALUES.copy(),
            SAMPLE_FORM_FIELD_VALUES.copy(),
            SAMPLE_FORM_FIELD_VALUES.copy(),
        ]

        expected_field_values = SAMPLE_FORM_FIELD_VALUES * 3
        mock_fix_form_field_value.return_value = expected_field_values

        # Execute
        with caplog.at_level(logging.INFO):
            import_csam_additional_status(import_ids=import_ids)

        # Verify all SSPs from ssp_map are processed (3 SSPs)
        assert mock_get_additional_status.call_count == 3
        mock_save_custom_fields.assert_called_once_with(expected_field_values)
        assert "Updated 3 Security Plans with contingency data" in caplog.text


class TestGetAdditionalStatus:
    """Tests for get_additional_status function"""

    @patch(f"{PATH}.build_form_values")
    @patch(f"{PATH}.retrieve_from_csam")
    @patch(f"{PATH}.FormFieldValue.check_custom_fields")
    def test_get_additional_status_success_complete_data(
        self, mock_check_custom_fields, mock_retrieve_from_csam, mock_build_form_values
    ):
        """Test successful status retrieval with all fields"""
        # Setup mocks
        mock_check_custom_fields.return_value = SAMPLE_STATUS_FIELD_MAP
        mock_retrieve_from_csam.return_value = SAMPLE_STATUS_RESPONSE
        mock_build_form_values.return_value = SAMPLE_FORM_FIELD_VALUES

        # Define expected status_map
        expected_status_map = {
            "Risk Assessment Completed": "riskAssessmentDateCompleted",
            "Risk Assessment Next Due Date": "riskAssessmentNextDueDate",
            "Risk Assessment Expiration Date": "riskAssessmentExpirationDate",
            "SSP Completed": "systemSecurityPlanDateCompleted",
            "SSP Next Due Date": "systemSecurityPlanNextDueDate",
            "CM Completed": "configurationManagementDateCompleted",
            "CM Next Due Date": "configurationManagementNextDueDate",
        }

        # Execute
        result = get_additional_status(ssp=1, csam_id=10001, status_map=expected_status_map)

        # Verify
        mock_check_custom_fields.assert_called_once_with(
            expected_status_map.keys(), "securityplans", "Status and Archive"
        )
        mock_retrieve_from_csam.assert_called_once_with(csam_endpoint="/CSAM/api/v1/systems/10001/status")
        mock_build_form_values.assert_called_once_with(
            ssp=1, result=SAMPLE_STATUS_RESPONSE, custom_map=SAMPLE_STATUS_FIELD_MAP, custom_fields=expected_status_map
        )
        assert result == SAMPLE_FORM_FIELD_VALUES

    @patch(f"{PATH}.retrieve_from_csam")
    @patch(f"{PATH}.FormFieldValue.check_custom_fields")
    def test_get_additional_status_csam_api_failure(self, mock_check_custom_fields, mock_retrieve_from_csam, caplog):
        """Test status retrieval with CSAM API failure"""
        # Setup mocks
        mock_check_custom_fields.return_value = SAMPLE_STATUS_FIELD_MAP
        mock_retrieve_from_csam.return_value = []  # API failure

        status_map = {
            "Risk Assessment Completed": "riskAssessmentDateCompleted",
        }

        # Execute
        with caplog.at_level(logging.ERROR):
            result = get_additional_status(ssp=1, csam_id=10001, status_map=status_map)

        # Verify error logged and empty list returned
        assert "Could not retrieve status details for CSAM ID 10001" in caplog.text
        assert "RegScale SSP id: 1" in caplog.text
        assert result == []

    @patch(f"{PATH}.retrieve_from_csam")
    @patch(f"{PATH}.FormFieldValue.check_custom_fields")
    def test_get_additional_status_none_response(self, mock_check_custom_fields, mock_retrieve_from_csam, caplog):
        """Test status retrieval with None response"""
        # Setup mocks
        mock_check_custom_fields.return_value = SAMPLE_STATUS_FIELD_MAP
        mock_retrieve_from_csam.return_value = None  # None response

        status_map = {
            "Risk Assessment Completed": "riskAssessmentDateCompleted",
        }

        # Execute
        with caplog.at_level(logging.ERROR):
            result = get_additional_status(ssp=1, csam_id=10001, status_map=status_map)

        # Verify error logged and empty list returned
        assert "Could not retrieve status details for CSAM ID 10001" in caplog.text
        assert result == []

    @patch(f"{PATH}.build_form_values")
    @patch(f"{PATH}.retrieve_from_csam")
    @patch(f"{PATH}.FormFieldValue.check_custom_fields")
    def test_get_additional_status_missing_custom_fields(
        self, mock_check_custom_fields, mock_retrieve_from_csam, mock_build_form_values
    ):
        """Test status retrieval with missing custom fields"""
        # Setup mocks - only some custom fields available
        partial_status_field_map = {
            "Risk Assessment Completed": 101,
            "SSP Completed": 104,
            # Other fields missing
        }
        mock_check_custom_fields.return_value = partial_status_field_map
        mock_retrieve_from_csam.return_value = SAMPLE_STATUS_RESPONSE

        partial_field_values = [
            {"record_id": 1, "record_module": "securityplans", "form_field_id": 101, "field_value": "2024-01-15"},
        ]
        mock_build_form_values.return_value = partial_field_values

        status_map = {
            "Risk Assessment Completed": "riskAssessmentDateCompleted",
            "Risk Assessment Next Due Date": "riskAssessmentNextDueDate",
            "SSP Completed": "systemSecurityPlanDateCompleted",
        }

        # Execute
        result = get_additional_status(ssp=1, csam_id=10001, status_map=status_map)

        # Verify build_form_values called with partial custom_map
        mock_build_form_values.assert_called_once_with(
            ssp=1, result=SAMPLE_STATUS_RESPONSE, custom_map=partial_status_field_map, custom_fields=status_map
        )
        assert result == partial_field_values

    @patch(f"{PATH}.build_form_values")
    @patch(f"{PATH}.retrieve_from_csam")
    @patch(f"{PATH}.FormFieldValue.check_custom_fields")
    def test_get_additional_status_status_map_values(
        self, mock_check_custom_fields, mock_retrieve_from_csam, mock_build_form_values
    ):
        """Test status map correctness"""
        # Setup mocks
        mock_check_custom_fields.return_value = SAMPLE_STATUS_FIELD_MAP
        mock_retrieve_from_csam.return_value = SAMPLE_STATUS_RESPONSE
        mock_build_form_values.return_value = SAMPLE_FORM_FIELD_VALUES

        # Define the exact status_map that should be used
        expected_status_map = {
            "Risk Assessment Completed": "riskAssessmentDateCompleted",
            "Risk Assessment Next Due Date": "riskAssessmentNextDueDate",
            "Risk Assessment Expiration Date": "riskAssessmentExpirationDate",
            "SSP Completed": "systemSecurityPlanDateCompleted",
            "SSP Next Due Date": "systemSecurityPlanNextDueDate",
            "CM Completed": "configurationManagementDateCompleted",
            "CM Next Due Date": "configurationManagementNextDueDate",
        }

        # Execute
        get_additional_status(ssp=1, csam_id=10001, status_map=expected_status_map)

        # Verify the status_map keys passed to check_custom_fields
        call_args = mock_check_custom_fields.call_args
        assert set(call_args[0][0]) == set(expected_status_map.keys())

        # Verify the status_map passed to build_form_values
        build_call_args = mock_build_form_values.call_args
        assert build_call_args[1]["custom_fields"] == expected_status_map

    @patch(f"{PATH}.build_form_values")
    @patch(f"{PATH}.retrieve_from_csam")
    @patch(f"{PATH}.FormFieldValue.check_custom_fields")
    def test_get_additional_status_endpoint_construction(
        self, mock_check_custom_fields, mock_retrieve_from_csam, mock_build_form_values
    ):
        """Test endpoint construction with specific CSAM ID"""
        # Setup mocks
        mock_check_custom_fields.return_value = SAMPLE_STATUS_FIELD_MAP
        mock_retrieve_from_csam.return_value = SAMPLE_STATUS_RESPONSE
        mock_build_form_values.return_value = SAMPLE_FORM_FIELD_VALUES

        status_map = {"Risk Assessment Completed": "riskAssessmentDateCompleted"}

        # Execute with specific CSAM ID
        csam_id = 12345
        get_additional_status(ssp=1, csam_id=csam_id, status_map=status_map)

        # Verify endpoint construction
        mock_retrieve_from_csam.assert_called_once_with(csam_endpoint=f"/CSAM/api/v1/systems/{csam_id}/status")

    @patch(f"{PATH}.build_form_values")
    @patch(f"{PATH}.retrieve_from_csam")
    @patch(f"{PATH}.FormFieldValue.check_custom_fields")
    def test_get_additional_status_with_empty_csam_response(
        self, mock_check_custom_fields, mock_retrieve_from_csam, mock_build_form_values, caplog
    ):
        """
        Test status retrieval with empty CSAM response dict.
        In Python, {} is falsy, so 'if not result:' will trigger the error path.
        build_form_values should NOT be called.
        """
        # Setup mocks
        mock_check_custom_fields.return_value = SAMPLE_STATUS_FIELD_MAP
        mock_retrieve_from_csam.return_value = {}  # Empty dict is falsy

        status_map = {"Risk Assessment Completed": "riskAssessmentDateCompleted"}

        # Execute
        with caplog.at_level(logging.ERROR):
            result = get_additional_status(ssp=1, csam_id=10001, status_map=status_map)

        # Verify error path taken - build_form_values should NOT be called
        assert "Could not retrieve status details for CSAM ID 10001" in caplog.text
        mock_build_form_values.assert_not_called()
        assert result == []

    @patch(f"{PATH}.build_form_values")
    @patch(f"{PATH}.retrieve_from_csam")
    @patch(f"{PATH}.FormFieldValue.check_custom_fields")
    def test_get_additional_status_with_extra_csam_fields(
        self, mock_check_custom_fields, mock_retrieve_from_csam, mock_build_form_values
    ):
        """Test status retrieval when CSAM returns extra fields not in status_map"""
        # Setup mocks
        mock_check_custom_fields.return_value = SAMPLE_STATUS_FIELD_MAP

        # CSAM response with extra fields
        csam_response_with_extras = {
            **SAMPLE_STATUS_RESPONSE,
            "extraField1": "value1",
            "extraField2": "value2",
        }
        mock_retrieve_from_csam.return_value = csam_response_with_extras
        mock_build_form_values.return_value = SAMPLE_FORM_FIELD_VALUES

        status_map = {
            "Risk Assessment Completed": "riskAssessmentDateCompleted",
            "SSP Completed": "systemSecurityPlanDateCompleted",
        }

        # Execute
        result = get_additional_status(ssp=1, csam_id=10001, status_map=status_map)

        # Verify build_form_values called with full CSAM response (extra fields included)
        mock_build_form_values.assert_called_once_with(
            ssp=1, result=csam_response_with_extras, custom_map=SAMPLE_STATUS_FIELD_MAP, custom_fields=status_map
        )
        # build_form_values should handle filtering - we just verify the call
        assert result == SAMPLE_FORM_FIELD_VALUES

    @patch(f"{PATH}.build_form_values")
    @patch(f"{PATH}.retrieve_from_csam")
    @patch(f"{PATH}.FormFieldValue.check_custom_fields")
    def test_get_additional_status_with_string_csam_id(
        self, mock_check_custom_fields, mock_retrieve_from_csam, mock_build_form_values
    ):
        """Test status retrieval with string CSAM ID"""
        # Setup mocks
        mock_check_custom_fields.return_value = SAMPLE_STATUS_FIELD_MAP
        mock_retrieve_from_csam.return_value = SAMPLE_STATUS_RESPONSE
        mock_build_form_values.return_value = SAMPLE_FORM_FIELD_VALUES

        status_map = {"Risk Assessment Completed": "riskAssessmentDateCompleted"}

        # Execute with string CSAM ID (as it comes from the map)
        csam_id = "10001"
        get_additional_status(ssp=1, csam_id=csam_id, status_map=status_map)

        # Verify endpoint construction works with string ID
        mock_retrieve_from_csam.assert_called_once_with(csam_endpoint=f"/CSAM/api/v1/systems/{csam_id}/status")

    @patch(f"{PATH}.build_form_values")
    @patch(f"{PATH}.retrieve_from_csam")
    @patch(f"{PATH}.FormFieldValue.check_custom_fields")
    def test_get_additional_status_verify_status_and_archive_tab(
        self, mock_check_custom_fields, mock_retrieve_from_csam, mock_build_form_values
    ):
        """Test that check_custom_fields is called with correct tab name"""
        # Setup mocks
        mock_check_custom_fields.return_value = SAMPLE_STATUS_FIELD_MAP
        mock_retrieve_from_csam.return_value = SAMPLE_STATUS_RESPONSE
        mock_build_form_values.return_value = SAMPLE_FORM_FIELD_VALUES

        status_map = {"Risk Assessment Completed": "riskAssessmentDateCompleted"}

        # Execute
        get_additional_status(ssp=1, csam_id=10001, status_map=status_map)

        # Verify check_custom_fields called with "Status and Archive" tab
        mock_check_custom_fields.assert_called_once_with(status_map.keys(), "securityplans", "Status and Archive")
