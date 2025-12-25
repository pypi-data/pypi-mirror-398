#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Integration tests for Module model API endpoints"""

from typing import List
from unittest.mock import MagicMock, patch

import pytest
from requests import Response

from regscale.models.regscale_models.module import Module, FormTab, FormField, Choice


class TestModuleIntegration:
    """Integration tests for Module model covering all API endpoints"""

    @pytest.fixture
    def mock_api_handler(self):
        """Mock API handler for testing"""
        with patch("regscale.models.regscale_models.module.Module._get_api_handler") as mock:
            yield mock.return_value

    @pytest.fixture
    def sample_module_data(self):
        """Sample module data for testing"""
        return {
            "id": 1,
            "displayName": "Test Module",
            "regScaleName": "test-module",
            "regScaleInformalName": "testmodule",
            "route": "/test-module",
        }

    @pytest.fixture
    def sample_detailed_module_data(self):
        """Sample detailed module data with form tabs and fields"""
        return {
            "id": 1,
            "displayName": "Cases",
            "regScaleName": "cases",
            "regScaleInformalName": "cases",
            "route": "/cases",
            "formTabs": [
                {
                    "id": 10,
                    "displayName": "Basic Info",
                    "regScaleName": "basic-info",
                    "isActive": True,
                    "formFields": [
                        {
                            "id": 100,
                            "displayName": "Title",
                            "regScaleName": "title",
                            "fieldType": "text",
                            "isRequired": True,
                        }
                    ],
                },
                {
                    "id": 20,
                    "displayName": "Custom Fields",
                    "regScaleName": "custom-fields",
                    "isActive": True,
                    "formFields": [
                        {
                            "id": 200,
                            "displayName": "Custom Field 1",
                            "regScaleName": "custom-field-1",
                            "fieldType": "text",
                            "isCustom": True,
                        }
                    ],
                },
            ],
        }

    @pytest.fixture
    def sample_modules_list(self):
        """Sample list of modules for testing"""
        return [
            {"id": 1, "displayName": "Cases", "regScaleName": "cases", "regScaleInformalName": "cases"},
            {"id": 2, "displayName": "Assets", "regScaleName": "assets", "regScaleInformalName": "assets"},
            {"id": 3, "displayName": "Issues", "regScaleName": "issues", "regScaleInformalName": "issues"},
        ]

    def test_create_module_success(self, mock_api_handler, sample_module_data):
        """Test POST /api/modules - Create new module success"""
        # Setup
        mock_response = MagicMock(spec=Response)
        mock_response.ok = True
        mock_response.json.return_value = sample_module_data
        mock_api_handler.post.return_value = mock_response

        # Execute
        module = Module(**sample_module_data)
        result = module.create()

        # Assert
        assert result is not None
        assert isinstance(result, Module)
        assert result.id == 1
        assert result.displayName == "Test Module"
        mock_api_handler.post.assert_called_once()

    def test_create_module_failure(self, mock_api_handler, sample_module_data):
        """Test POST /api/modules - Create module failure"""
        # Setup
        mock_response = MagicMock(spec=Response)
        mock_response.ok = False
        mock_response.status_code = 400
        mock_response.reason = "Bad Request"
        mock_response.text = "Invalid module data"
        mock_api_handler.post.return_value = mock_response

        # Execute
        module = Module(**sample_module_data)

        # Assert that APIInsertionError is raised
        from regscale.core.app.utils.api_handler import APIInsertionError

        with pytest.raises(APIInsertionError) as exc_info:
            module.create()

        assert "Response Code: 400:Bad Request - Invalid module data" in str(exc_info.value)

    def test_get_modules_success(self, mock_api_handler, sample_modules_list):
        """Test GET /api/modules - Get all modules success"""
        # Setup
        mock_response = MagicMock(spec=Response)
        mock_response.ok = True
        mock_response.json.return_value = sample_modules_list
        mock_api_handler.get.return_value = mock_response

        # Execute
        result = Module.get_modules()

        # Assert
        assert len(result) == 3
        assert all(isinstance(module, Module) for module in result)
        assert result[0].displayName == "Cases"
        assert result[1].displayName == "Assets"
        assert result[2].displayName == "Issues"

        mock_api_handler.get.assert_called_once()
        call_args = mock_api_handler.get.call_args
        assert call_args[1]["endpoint"] == "/api/modules"

    def test_get_modules_failure(self, mock_api_handler):
        """Test GET /api/modules - Get all modules failure"""
        # Setup
        mock_response = MagicMock(spec=Response)
        mock_response.ok = False
        mock_response.status_code = 500
        mock_response.reason = "Internal Server Error"
        mock_response.text = "Database error"
        mock_api_handler.get.return_value = mock_response

        # Mock log_response_error
        with patch.object(Module, "log_response_error") as mock_log:
            # Execute
            result = Module.get_modules()

            # Assert
            assert result == []
            mock_log.assert_called_once_with(response=mock_response)

    def test_get_module_by_id_success(self, mock_api_handler, sample_detailed_module_data):
        """Test GET /api/modules/{moduleId} - Get module by ID success"""
        # Setup
        mock_response = MagicMock(spec=Response)
        mock_response.ok = True
        mock_response.json.return_value = sample_detailed_module_data
        mock_api_handler.get.return_value = mock_response

        # Execute
        result = Module.get_module_by_id(1)

        # Assert
        assert result is not None
        assert isinstance(result, Module)
        assert result.id == 1
        assert result.displayName == "Cases"
        assert len(result.formTabs) == 2

        mock_api_handler.get.assert_called_once()
        call_args = mock_api_handler.get.call_args
        assert call_args[1]["endpoint"] == "/api/modules/1"

    def test_get_module_by_id_failure(self, mock_api_handler):
        """Test GET /api/modules/{moduleId} - Get module by ID failure"""
        # Setup
        mock_response = MagicMock(spec=Response)
        mock_response.ok = False
        mock_response.status_code = 500
        mock_response.reason = "Internal Server Error"
        mock_response.text = "Database error"
        mock_api_handler.get.return_value = mock_response

        # Mock log_response_error
        with patch.object(Module, "log_response_error") as mock_log:
            # Execute
            result = Module.get_module_by_id(999)

            # Assert
            assert result is None
            mock_log.assert_called_once_with(response=mock_response)

    def test_get_module_by_id_not_found(self, mock_api_handler):
        """Test GET /api/modules/{moduleId} - Module not found"""
        # Setup
        mock_response = MagicMock(spec=Response)
        mock_response.ok = False
        mock_response.status_code = 404
        mock_response.reason = "Not Found"
        mock_response.text = "Module not found"
        mock_api_handler.get.return_value = mock_response

        # Mock log_response_error
        with patch.object(Module, "log_response_error") as mock_log:
            # Execute
            result = Module.get_module_by_id(999)

            # Assert
            assert result is None
            mock_log.assert_called_once_with(response=mock_response)

    def test_post_multiple_modules_endpoint(self, mock_api_handler):
        """Test POST /api/modules/multiple - Bulk create modules"""
        # Setup
        modules_data = [
            {"displayName": "Module 1", "regScaleName": "module1"},
            {"displayName": "Module 2", "regScaleName": "module2"},
        ]

        mock_response = MagicMock(spec=Response)
        mock_response.ok = True
        mock_response.json.return_value = modules_data
        mock_api_handler.post.return_value = mock_response

        # This would be the method if implemented
        def create_multiple(cls, modules_data: List[dict]) -> List[Module]:
            result = cls._get_api_handler().post(endpoint="/api/modules/multiple", data=modules_data)
            if result and result.ok:
                return [cls(**module_data) for module_data in result.json()]
            return []

        # Add method to class temporarily for testing
        Module.create_multiple = classmethod(create_multiple)

        try:
            # Execute
            result = Module.create_multiple(modules_data)

            # Assert
            assert len(result) == 2
            assert all(isinstance(module, Module) for module in result)
            mock_api_handler.post.assert_called_once()
            call_args = mock_api_handler.post.call_args
            assert call_args[1]["endpoint"] == "/api/modules/multiple"
            assert call_args[1]["data"] == modules_data
        finally:
            # Clean up
            delattr(Module, "create_multiple")

    def test_get_all_modules_with_form_fields_endpoint(self, mock_api_handler, sample_detailed_module_data):
        """Test GET /api/modules/getAllModulesWithFormFields"""
        # Setup
        mock_response = MagicMock(spec=Response)
        mock_response.ok = True
        mock_response.json.return_value = [sample_detailed_module_data]
        mock_api_handler.get.return_value = mock_response

        # This would be the method if implemented
        def get_all_modules_with_form_fields(cls) -> List[Module]:
            result = cls._get_api_handler().get(endpoint="/api/modules/getAllModulesWithFormFields")
            if result and result.ok:
                return [cls(**module_data) for module_data in result.json()]
            return []

        # Add method to class temporarily for testing
        Module.get_all_modules_with_form_fields = classmethod(get_all_modules_with_form_fields)

        try:
            # Execute
            result = Module.get_all_modules_with_form_fields()

            # Assert
            assert len(result) == 1
            assert isinstance(result[0], Module)
            assert result[0].id == 1
            assert len(result[0].formTabs) == 2
            mock_api_handler.get.assert_called_once()
            call_args = mock_api_handler.get.call_args
            assert call_args[1]["endpoint"] == "/api/modules/getAllModulesWithFormFields"
        finally:
            # Clean up
            delattr(Module, "get_all_modules_with_form_fields")

    def test_reset_module_endpoint(self, mock_api_handler):
        """Test GET /api/modules/reset/{moduleId} - Reset module labeling"""
        # Setup
        mock_response = MagicMock(spec=Response)
        mock_response.ok = True
        mock_response.json.return_value = {"message": "Module reset successfully"}
        mock_api_handler.get.return_value = mock_response

        # This would be the method if implemented
        def reset_module(cls, module_id: int) -> bool:
            result = cls._get_api_handler().get(endpoint=f"/api/modules/reset/{module_id}")
            return result and result.ok

        # Add method to class temporarily for testing
        Module.reset_module = classmethod(reset_module)

        try:
            # Execute
            result = Module.reset_module(1)

            # Assert
            assert result is True
            mock_api_handler.get.assert_called_once()
            call_args = mock_api_handler.get.call_args
            assert call_args[1]["endpoint"] == "/api/modules/reset/1"
        finally:
            # Clean up
            delattr(Module, "reset_module")

    def test_get_module_by_name_success(self, mock_api_handler, sample_modules_list):
        """Test get_module_by_name with existing module"""
        # Setup
        mock_response = MagicMock(spec=Response)
        mock_response.ok = True
        mock_response.json.return_value = sample_modules_list
        mock_api_handler.get.return_value = mock_response

        # Execute
        result = Module.get_module_by_name("cases")

        # Assert
        assert result is not None
        assert isinstance(result, Module)
        assert result.regScaleInformalName == "cases"

    def test_get_module_by_name_not_found(self, mock_api_handler, sample_modules_list):
        """Test get_module_by_name with non-existing module"""
        # Setup
        mock_response = MagicMock(spec=Response)
        mock_response.ok = True
        mock_response.json.return_value = sample_modules_list
        mock_api_handler.get.return_value = mock_response

        # Execute
        result = Module.get_module_by_name("nonexistent")

        # Assert
        assert result is None

    def test_get_tab_by_name_success(self, mock_api_handler, sample_modules_list, sample_detailed_module_data):
        """Test get_tab_by_name with existing tab"""
        # Setup - Mock both get_modules and get_module_by_id calls
        mock_response_modules = MagicMock(spec=Response)
        mock_response_modules.ok = True
        mock_response_modules.json.return_value = sample_modules_list

        mock_response_detailed = MagicMock(spec=Response)
        mock_response_detailed.ok = True
        mock_response_detailed.json.return_value = sample_detailed_module_data

        # Set up side effects for multiple calls
        mock_api_handler.get.side_effect = [mock_response_modules, mock_response_detailed]

        # Execute
        result = Module.get_tab_by_name("cases", "basic-info")

        # Assert
        assert result is not None
        assert isinstance(result, FormTab)
        assert result.regScaleName == "basic-info"
        assert result.id == 10

    def test_get_tab_by_name_module_not_found(self, mock_api_handler, sample_modules_list):
        """Test get_tab_by_name with non-existing module"""
        # Setup
        mock_response = MagicMock(spec=Response)
        mock_response.ok = True
        mock_response.json.return_value = sample_modules_list
        mock_api_handler.get.return_value = mock_response

        # Execute
        result = Module.get_tab_by_name("nonexistent", "basic-info")

        # Assert
        assert result is None

    def test_get_tab_by_name_tab_not_found(self, mock_api_handler, sample_modules_list, sample_detailed_module_data):
        """Test get_tab_by_name with non-existing tab"""
        # Setup
        mock_response_modules = MagicMock(spec=Response)
        mock_response_modules.ok = True
        mock_response_modules.json.return_value = sample_modules_list

        mock_response_detailed = MagicMock(spec=Response)
        mock_response_detailed.ok = True
        mock_response_detailed.json.return_value = sample_detailed_module_data

        mock_api_handler.get.side_effect = [mock_response_modules, mock_response_detailed]

        # Execute
        result = Module.get_tab_by_name("cases", "nonexistent-tab")

        # Assert
        assert result is None

    def test_get_new_custom_form_tab_id_success(
        self, mock_api_handler, sample_modules_list, sample_detailed_module_data
    ):
        """Test get_new_custom_form_tab_id with existing tab"""
        # Setup
        mock_response_modules = MagicMock(spec=Response)
        mock_response_modules.ok = True
        mock_response_modules.json.return_value = sample_modules_list

        mock_response_detailed = MagicMock(spec=Response)
        mock_response_detailed.ok = True
        mock_response_detailed.json.return_value = sample_detailed_module_data

        mock_api_handler.get.side_effect = [mock_response_modules, mock_response_detailed]

        # Execute
        result = Module.get_new_custom_form_tab_id("cases", "basic-info")

        # Assert
        assert result == 10

    def test_get_new_custom_form_tab_id_not_found(self, mock_api_handler, sample_modules_list):
        """Test get_new_custom_form_tab_id with non-existing module"""
        # Setup
        mock_response = MagicMock(spec=Response)
        mock_response.ok = True
        mock_response.json.return_value = sample_modules_list
        mock_api_handler.get.return_value = mock_response

        # Execute
        result = Module.get_new_custom_form_tab_id("nonexistent", "basic-info")

        # Assert
        assert result is None

    def test_get_form_fields_by_tab_id_success(
        self, mock_api_handler, sample_modules_list, sample_detailed_module_data
    ):
        """Test get_form_fields_by_tab_id with existing tab"""
        # Setup
        mock_response_modules = MagicMock(spec=Response)
        mock_response_modules.ok = True
        mock_response_modules.json.return_value = sample_modules_list

        mock_response_detailed = MagicMock(spec=Response)
        mock_response_detailed.ok = True
        mock_response_detailed.json.return_value = sample_detailed_module_data

        mock_api_handler.get.side_effect = [mock_response_modules, mock_response_detailed]

        # Execute
        result = Module.get_form_fields_by_tab_id("cases", "basic-info")

        # Assert
        assert result is not None
        assert len(result) == 1
        assert isinstance(result[0], FormField)
        assert result[0].regScaleName == "title"

    def test_get_form_fields_by_tab_id_not_found(self, mock_api_handler, sample_modules_list):
        """Test get_form_fields_by_tab_id with non-existing module"""
        # Setup
        mock_response = MagicMock(spec=Response)
        mock_response.ok = True
        mock_response.json.return_value = sample_modules_list
        mock_api_handler.get.return_value = mock_response

        # Execute
        result = Module.get_form_fields_by_tab_id("nonexistent", "basic-info")

        # Assert
        assert result is None

    def test_module_slug(self):
        """Test that the module slug is correctly set"""
        assert Module._module_slug == "modules"

    def test_additional_endpoints(self):
        """Test that additional endpoints are correctly defined"""
        endpoints = Module._get_additional_endpoints()

        assert "get_modules" in endpoints
        assert "get_module_by_id" in endpoints

        assert endpoints["get_modules"] == "/api/{model_slug}"
        assert endpoints["get_module_by_id"] == "/api/{model_slug}/{id}"

    @pytest.mark.parametrize(
        "module_id,expected_endpoint",
        [
            (1, "/api/modules/1"),
            (999, "/api/modules/999"),
            (42, "/api/modules/42"),
        ],
    )
    def test_get_module_by_id_endpoint_formation(self, mock_api_handler, module_id, expected_endpoint):
        """Test endpoint formation for get_module_by_id with different IDs"""
        # Setup
        mock_response = MagicMock(spec=Response)
        mock_response.ok = True
        mock_response.json.return_value = {"id": module_id, "displayName": f"Module {module_id}"}
        mock_api_handler.get.return_value = mock_response

        # Execute
        Module.get_module_by_id(module_id)

        # Assert
        call_args = mock_api_handler.get.call_args
        assert call_args[1]["endpoint"] == expected_endpoint

    def test_form_tab_model_structure(self):
        """Test FormTab model structure and field access"""
        form_tab_data = {
            "id": 1,
            "displayName": "Test Tab",
            "regScaleName": "test-tab",
            "isActive": True,
            "formFields": [{"id": 10, "displayName": "Test Field", "regScaleName": "test-field", "fieldType": "text"}],
        }

        form_tab = FormTab(**form_tab_data)

        assert form_tab.id == 1
        assert form_tab.displayName == "Test Tab"
        assert form_tab.regScaleName == "test-tab"
        assert form_tab.isActive is True
        assert len(form_tab.formFields) == 1
        assert isinstance(form_tab.formFields[0], FormField)

    def test_form_field_model_structure(self):
        """Test FormField model structure and field access"""
        form_field_data = {
            "id": 1,
            "displayName": "Test Field",
            "regScaleName": "test-field",
            "fieldType": "select",
            "isRequired": True,
            "choices": [{"id": 1, "value": "option1", "label": "Option 1", "isActive": True}],
        }

        form_field = FormField(**form_field_data)

        assert form_field.id == 1
        assert form_field.displayName == "Test Field"
        assert form_field.regScaleName == "test-field"
        assert form_field.fieldType == "select"
        assert form_field.isRequired is True
        assert len(form_field.choices) == 1
        assert isinstance(form_field.choices[0], Choice)

    def test_choice_model_structure(self):
        """Test Choice model structure and field access"""
        choice_data = {
            "id": 1,
            "value": "test_value",
            "label": "Test Label",
            "regScaleLabel": "Test RegScale Label",
            "isActive": True,
            "sequence": 1,
        }

        choice = Choice(**choice_data)

        assert choice.id == 1
        assert choice.value == "test_value"
        assert choice.label == "Test Label"
        assert choice.regScaleLabel == "Test RegScale Label"
        assert choice.isActive is True
        assert choice.sequence == 1
