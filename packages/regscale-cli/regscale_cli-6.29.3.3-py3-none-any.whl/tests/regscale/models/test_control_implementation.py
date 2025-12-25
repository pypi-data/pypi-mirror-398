import unittest
from unittest.mock import MagicMock, patch

from regscale.core.app.application import Application
from regscale.models import ControlImplementation


class TestControlImplementation(unittest.TestCase):
    @patch("regscale.models.regscale_models.control_implementation.ControlImplementation._get_api_handler")
    def test_get_control_map_by_plan_lower_case_keys(self, mock_api_handler):
        # Create a mock response object with 'ok' attribute and 'json' method
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = [
            {"control": {"controlId": "CA-1"}, "id": 1},
            {"control": {"controlId": "AC-6"}, "id": 2},
        ]

        # Set up the mock API handler to return the mock response when .get() is called
        mock_handler = MagicMock()
        mock_handler.get.return_value = mock_response
        mock_api_handler.return_value = mock_handler

        # Expected result should have lower case control IDs as keys
        expected_result = {"ca-1": 1, "ac-6": 2}

        # Call the method under test
        result = ControlImplementation.get_control_label_map_by_plan(plan_id=123)

        # Assert that the result matches the expected result
        self.assertEqual(result, expected_result)

    @patch("regscale.core.app.api.Api.graph")
    def test_get_export_query_with_none_control_owner(self, mock_graph):
        """Test get_export_query handles None controlOwner gracefully."""
        # Mock API response with None controlOwner
        mock_graph.return_value = {
            "controlImplementations": {
                "totalCount": 1,
                "items": [
                    {
                        "id": 1,
                        "controlID": 100,
                        "controlOwner": None,  # None control owner
                        "control": {
                            "title": "Test Control",
                            "description": "Test Description",
                            "controlId": "AC-1",
                        },
                        "status": "Implemented",
                        "policy": "Test Policy",
                        "implementation": "Test Implementation",
                        "responsibility": "Provider",
                        "inheritable": True,
                    }
                ],
            }
        }

        # Call the method under test
        app = Application()
        result = ControlImplementation.get_export_query(app, parent_id=1, parent_module="securityplans")

        # Verify the result handles None gracefully
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["controlOwnerId"], "Unassigned")

    @patch("regscale.core.app.api.Api.graph")
    def test_get_export_query_with_none_control(self, mock_graph):
        """Test get_export_query handles None control gracefully."""
        # Mock API response with None control
        mock_graph.return_value = {
            "controlImplementations": {
                "totalCount": 1,
                "items": [
                    {
                        "id": 1,
                        "controlID": 100,
                        "controlOwner": {
                            "firstName": "John",
                            "lastName": "Doe",
                            "userName": "jdoe",
                        },
                        "control": None,  # None control
                        "status": "Implemented",
                        "policy": "Test Policy",
                        "implementation": "Test Implementation",
                        "responsibility": "Provider",
                        "inheritable": True,
                    }
                ],
            }
        }

        # Call the method under test
        app = Application()
        result = ControlImplementation.get_export_query(app, parent_id=1, parent_module="securityplans")

        # Verify the result handles None gracefully
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["controlName"], "")
        self.assertEqual(result[0]["controlTitle"], "")
        self.assertEqual(result[0]["description"], "")

    @patch("regscale.core.app.api.Api.graph")
    def test_get_export_query_with_partial_control_owner(self, mock_graph):
        """Test get_export_query handles partial controlOwner data gracefully."""
        # Mock API response with partial controlOwner data
        mock_graph.return_value = {
            "controlImplementations": {
                "totalCount": 1,
                "items": [
                    {
                        "id": 1,
                        "controlID": 100,
                        "controlOwner": {
                            "firstName": None,
                            "lastName": "Doe",
                            "userName": "jdoe",
                        },
                        "control": {
                            "title": "Test Control",
                            "description": "Test Description",
                            "controlId": "AC-1",
                        },
                        "status": "Implemented",
                        "policy": "Test Policy",
                        "implementation": "Test Implementation",
                        "responsibility": "Provider",
                        "inheritable": True,
                    }
                ],
            }
        }

        # Call the method under test
        app = Application()
        result = ControlImplementation.get_export_query(app, parent_id=1, parent_module="securityplans")

        # Verify the result handles partial data gracefully
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["controlOwnerId"], "Doe,  (jdoe)")
