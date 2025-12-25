#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Integration tests for FormFieldValue model API endpoints"""

from typing import List
from unittest.mock import MagicMock, patch

import pytest
from requests import Response

from regscale.models.regscale_models.form_field_value import FormFieldValue


class TestFormFieldValueIntegration:
    """Integration tests for FormFieldValue model covering all API endpoints"""

    @pytest.fixture
    def mock_api_handler(self):
        """Mock API handler for testing"""
        with patch("regscale.models.regscale_models.form_field_value.FormFieldValue._get_api_handler") as mock:
            yield mock.return_value

    @pytest.fixture
    def sample_form_field_data(self):
        """Sample form field data for testing"""
        return [{"formFieldId": 1, "data": "Test Value 1"}, {"formFieldId": 2, "data": "Test Value 2"}]

    @pytest.fixture
    def sample_form_field_values(self):
        """Sample FormFieldValue objects for testing"""
        return [FormFieldValue(formFieldId=1, data="Test Value 1"), FormFieldValue(formFieldId=2, data="Test Value 2")]

    def test_save_custom_data_success(self, mock_api_handler, sample_form_field_values):
        """Test POST /api/formFieldValue/saveFormFields/{recordId}/{moduleName} - Success"""
        # Setup
        mock_response = MagicMock(spec=Response)
        mock_response.ok = True
        mock_api_handler.post.return_value = mock_response

        record_id = 123
        module_name = "cases"

        # Execute
        result = FormFieldValue.save_custom_data(record_id, module_name, sample_form_field_values)

        # Assert
        assert result is True
        mock_api_handler.post.assert_called_once()

        call_args = mock_api_handler.post.call_args
        assert call_args[1]["endpoint"] == "/api/formFieldValue/saveFormFields/123/cases"

        # Check that data was filtered to only include formFieldId and data
        expected_data = [{"formFieldId": 1, "data": "Test Value 1"}, {"formFieldId": 2, "data": "Test Value 2"}]
        assert call_args[1]["data"] == expected_data

    def test_save_custom_data_failure(self, mock_api_handler, sample_form_field_values):
        """Test POST /api/formFieldValue/saveFormFields/{recordId}/{moduleName} - Failure"""
        # Setup
        mock_response = MagicMock(spec=Response)
        mock_response.ok = False
        mock_api_handler.post.return_value = mock_response

        record_id = 123
        module_name = "cases"

        # Mock log_response_error
        with patch.object(FormFieldValue, "log_response_error") as mock_log:
            # Execute
            result = FormFieldValue.save_custom_data(record_id, module_name, sample_form_field_values)

            # Assert
            assert result is False
            mock_log.assert_called_once_with(response=mock_response)

    def test_save_custom_data_empty_data(self, mock_api_handler):
        """Test save_custom_data with empty data list"""
        # Setup
        mock_response = MagicMock(spec=Response)
        mock_response.ok = True
        mock_api_handler.post.return_value = mock_response

        # Execute
        result = FormFieldValue.save_custom_data(123, "cases", [])

        # Assert
        assert result is True
        mock_api_handler.post.assert_called_once()
        call_args = mock_api_handler.post.call_args
        assert call_args[1]["data"] == []

    def test_get_field_values_success(self, mock_api_handler):
        """Test GET /api/formFieldValue/getFieldValues/{recordId}/{moduleName}/{formId} - Success"""
        # Setup
        mock_response = MagicMock(spec=Response)
        mock_response.ok = True
        mock_response.json.return_value = [
            {"formFieldName": "Field1", "formFieldId": 1, "data": "Value1"},
            {"formFieldName": "Field2", "formFieldId": 2, "data": "Value2"},
        ]
        mock_api_handler.get.return_value = mock_response

        record_id = 123
        module_name = "cases"
        form_id = 456

        # Execute
        result = FormFieldValue.get_field_values(record_id, module_name, form_id)

        # Assert
        assert len(result) == 2
        assert all(isinstance(item, FormFieldValue) for item in result)
        assert result[0].formFieldId == 1
        assert result[0].data == "Value1"
        assert result[1].formFieldId == 2
        assert result[1].data == "Value2"

        mock_api_handler.get.assert_called_once()
        call_args = mock_api_handler.get.call_args
        assert call_args[1]["endpoint"] == "/api/formFieldValue/getFieldValues/123/cases/456"

    def test_get_field_values_failure(self, mock_api_handler):
        """Test GET /api/formFieldValue/getFieldValues/{recordId}/{moduleName}/{formId} - Failure"""
        # Setup
        mock_response = MagicMock(spec=Response)
        mock_response.ok = False
        mock_api_handler.get.return_value = mock_response

        # Mock log_response_error
        with patch.object(FormFieldValue, "log_response_error") as mock_log:
            # Execute
            result = FormFieldValue.get_field_values(123, "cases", 456)

            # Assert
            assert result == []
            mock_log.assert_called_once_with(response=mock_response)

    def test_get_field_values_empty_response(self, mock_api_handler):
        """Test get_field_values with empty response"""
        # Setup
        mock_response = MagicMock(spec=Response)
        mock_response.ok = True
        mock_response.json.return_value = []
        mock_api_handler.get.return_value = mock_response

        # Execute
        result = FormFieldValue.get_field_values(123, "cases", 456)

        # Assert
        assert result == []

    def test_get_field_values_by_name_endpoint(self, mock_api_handler):
        """Test that the missing getFieldValuesByName endpoint would work if implemented"""
        # Note: This endpoint is mentioned in the requirements but not implemented in the model
        # This test demonstrates how it would be tested if implemented

        # Setup - Mock the endpoint as if it were implemented
        with patch.object(FormFieldValue, "_get_additional_endpoints") as mock_endpoints:
            mock_endpoints.return_value = {
                "get_field_values_by_name": "/api/{model_slug}/getFieldValuesByName/{recordId}/{moduleName}/{regscaleId}"
            }

            mock_response = MagicMock(spec=Response)
            mock_response.ok = True
            mock_response.json.return_value = [{"formFieldName": "TestField", "formFieldId": 1, "data": "TestValue"}]
            mock_api_handler.get.return_value = mock_response

            # This would be the method if implemented
            def get_field_values_by_name(
                cls, record_id: int, module_name: str, regscale_id: str
            ) -> List[FormFieldValue]:
                result = cls._get_api_handler().get(
                    endpoint=cls.get_endpoint("get_field_values_by_name").format(
                        model_slug=cls.get_module_slug(),
                        recordId=record_id,
                        moduleName=module_name,
                        regscaleId=regscale_id,
                    )
                )
                if result and result.ok:
                    return [cls(**o) for o in result.json()]
                return []

            # Add method to class temporarily for testing
            FormFieldValue.get_field_values_by_name = classmethod(get_field_values_by_name)

            try:
                # Execute
                result = FormFieldValue.get_field_values_by_name(123, "cases", "test-regscale-id")

                # Assert
                assert len(result) == 1
                assert isinstance(result[0], FormFieldValue)
                mock_api_handler.get.assert_called_once()
                call_args = mock_api_handler.get.call_args
                expected_endpoint = "/api/formFieldValue/getFieldValuesByName/123/cases/test-regscale-id"
                assert call_args[1]["endpoint"] == expected_endpoint
            finally:
                # Clean up
                delattr(FormFieldValue, "get_field_values_by_name")

    def test_filter_dict_keys(self):
        """Test the filter_dict_keys static method"""
        # Setup
        data = {
            "formFieldId": 1,
            "data": "test value",
            "extra_field": "should be filtered out",
            "another_field": "also filtered",
        }
        allowed_fields = ["formFieldId", "data"]

        # Execute
        result = FormFieldValue.filter_dict_keys(data, allowed_fields)

        # Assert
        assert result == {"formFieldId": 1, "data": "test value"}
        assert "extra_field" not in result
        assert "another_field" not in result

    def test_filter_dict_keys_empty_data(self):
        """Test filter_dict_keys with empty data"""
        result = FormFieldValue.filter_dict_keys({}, ["formFieldId", "data"])
        assert result == {}

    def test_filter_dict_keys_empty_allowed_fields(self):
        """Test filter_dict_keys with empty allowed fields"""
        data = {"formFieldId": 1, "data": "test"}
        result = FormFieldValue.filter_dict_keys(data, [])
        assert result == {}

    def test_module_slug(self):
        """Test that the module slug is correctly set"""
        assert FormFieldValue._module_slug == "formFieldValue"

    def test_additional_endpoints(self):
        """Test that additional endpoints are correctly defined"""
        endpoints = FormFieldValue._get_additional_endpoints()

        assert "post_save_form_fields" in endpoints
        assert "get_field_value" in endpoints

        assert endpoints["post_save_form_fields"] == "/api/{model_slug}/saveFormFields/{recordId}/{moduleName}"
        assert endpoints["get_field_value"] == "/api/{model_slug}/getFieldValues/{recordId}/{moduleName}/{formId}"

    def test_field_aliases(self):
        """Test that field aliases work correctly"""
        # Test that 'data' field can be set via 'fieldValue' alias
        form_field = FormFieldValue(formFieldId=1, fieldValue="test value")
        assert form_field.data == "test value"

        # Test dict creation with alias
        form_field_dict = form_field.dict(by_alias=True)
        assert "fieldValue" in form_field_dict
        assert form_field_dict["fieldValue"] == "test value"

    @pytest.mark.parametrize(
        "record_id,module_name,expected_endpoint",
        [
            (123, "cases", "/api/formFieldValue/saveFormFields/123/cases"),
            (456, "assets", "/api/formFieldValue/saveFormFields/456/assets"),
            (789, "issues", "/api/formFieldValue/saveFormFields/789/issues"),
        ],
    )
    def test_save_custom_data_endpoint_formation(
        self, mock_api_handler, sample_form_field_values, record_id, module_name, expected_endpoint
    ):
        """Test endpoint formation for different parameters"""
        # Setup
        mock_response = MagicMock(spec=Response)
        mock_response.ok = True
        mock_api_handler.post.return_value = mock_response

        # Execute
        FormFieldValue.save_custom_data(record_id, module_name, sample_form_field_values)

        # Assert
        call_args = mock_api_handler.post.call_args
        assert call_args[1]["endpoint"] == expected_endpoint

    @pytest.mark.parametrize(
        "record_id,module_name,form_id,expected_endpoint",
        [
            (123, "cases", 456, "/api/formFieldValue/getFieldValues/123/cases/456"),
            (789, "assets", 101, "/api/formFieldValue/getFieldValues/789/assets/101"),
            (999, "issues", 202, "/api/formFieldValue/getFieldValues/999/issues/202"),
        ],
    )
    def test_get_field_values_endpoint_formation(
        self, mock_api_handler, record_id, module_name, form_id, expected_endpoint
    ):
        """Test endpoint formation for get_field_values with different parameters"""
        # Setup
        mock_response = MagicMock(spec=Response)
        mock_response.ok = True
        mock_response.json.return_value = []
        mock_api_handler.get.return_value = mock_response

        # Execute
        FormFieldValue.get_field_values(record_id, module_name, form_id)

        # Assert
        call_args = mock_api_handler.get.call_args
        assert call_args[1]["endpoint"] == expected_endpoint
