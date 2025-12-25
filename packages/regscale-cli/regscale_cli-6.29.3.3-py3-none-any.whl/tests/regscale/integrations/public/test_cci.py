#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for CCI Importer functionality."""
import xml.etree.ElementTree as ET
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from regscale.integrations.public.cci_importer import CCIImporter, cci_importer, _load_xml_file
from tests import CLITestFixture


class TestCCIImporter(CLITestFixture):
    """Test cases for the CCIImporter class."""

    @pytest.fixture
    def sample_xml_data(self):
        """Create sample XML data for testing."""
        xml_content = """<?xml version="1.0" encoding="utf-8"?>
        <cci_list xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                  xmlns="http://iase.disa.mil/cci">
            <cci_item id="CCI-000001">
                <definition>The organization develops, documents, and disseminates access control policy.</definition>
                <references>
                    <reference creator="NIST" title="NIST SP 800-53 Revision 5" version="5"
                              location="AC-1" index="AC-1 a" />
                </references>
            </cci_item>
            <cci_item id="CCI-000002">
                <definition>The organization reviews and updates access control policy.</definition>
                <references>
                    <reference creator="NIST" title="NIST SP 800-53 Revision 5" version="5"
                              location="AC-1" index="AC-1 b" />
                    <reference creator="NIST" title="NIST SP 800-53 Revision 4" version="4"
                              location="AC-1" index="AC-1 b" />
                </references>
            </cci_item>
            <cci_item id="CCI-000003">
                <definition>The organization develops access control procedures.</definition>
                <references>
                    <reference creator="NIST" title="NIST SP 800-53 Revision 5" version="5"
                              location="AC-2" index="AC-2 a 1" />
                </references>
            </cci_item>
        </cci_list>"""
        return ET.fromstring(xml_content)

    @pytest.fixture
    def cci_importer_instance(self, sample_xml_data):
        """Create a CCIImporter instance for testing."""
        return CCIImporter(sample_xml_data, version="5", verbose=False)

    def test_init(self, sample_xml_data):
        """Test CCIImporter initialization."""
        importer = CCIImporter(sample_xml_data, version="4", verbose=True)

        assert importer.xml_data == sample_xml_data
        assert importer.reference_version == "4"
        assert importer.verbose is True
        assert importer.normalized_cci == {}
        assert importer.cci_grouped_by_index == {}
        assert importer._user_context is None

    def test_parse_control_id(self, cci_importer_instance):
        """Test parsing control IDs from reference indices."""
        assert cci_importer_instance._parse_control_id("AC-1 a 1 (b)") == "AC-1"
        assert cci_importer_instance._parse_control_id("SC-7") == "SC-7"
        assert cci_importer_instance._parse_control_id("") == ""
        assert cci_importer_instance._parse_control_id("   ") == ""

    def test_extract_cci_data(self, cci_importer_instance, sample_xml_data):
        """Test extracting CCI ID and definition from XML elements."""
        cci_item = sample_xml_data.find(".//{http://iase.disa.mil/cci}cci_item")
        cci_id, definition = cci_importer_instance._extract_cci_data(cci_item)

        assert cci_id == "CCI-000001"
        assert "organization develops, documents, and disseminates access control policy" in definition

    def test_is_valid_reference(self, cci_importer_instance, sample_xml_data):
        """Test validation of reference elements based on version."""
        references = sample_xml_data.findall(".//{http://iase.disa.mil/cci}reference")

        # Should accept version 5 references
        version_5_refs = [ref for ref in references if ref.get("version") == "5"]
        assert len(version_5_refs) > 0
        assert cci_importer_instance._is_valid_reference(version_5_refs[0]) is True

        # Should reject version 4 references when configured for version 5
        version_4_refs = [ref for ref in references if ref.get("version") == "4"]
        if version_4_refs:
            assert cci_importer_instance._is_valid_reference(version_4_refs[0]) is False

    def test_parse_cci(self, cci_importer_instance):
        """Test parsing CCI items and normalizing them."""
        cci_importer_instance.parse_cci()
        normalized = cci_importer_instance.get_normalized_cci()

        # Should have parsed AC-1 and AC-2 controls
        assert "AC-1" in normalized
        assert "AC-2" in normalized

        # AC-1 should have 2 CCI items (CCI-000001 and CCI-000002)
        assert len(normalized["AC-1"]) == 2

        # AC-2 should have 1 CCI item (CCI-000003)
        assert len(normalized["AC-2"]) == 1

        # Check CCI content
        ac1_ccis = normalized["AC-1"]
        cci_ids = [cci["cci_id"] for cci in ac1_ccis]
        assert "CCI-000001" in cci_ids
        assert "CCI-000002" in cci_ids

    @patch("regscale.integrations.public.cci_importer.Application")
    def test_get_user_context(self, mock_app_class, cci_importer_instance):
        """Test getting user context from application config."""
        mock_app = MagicMock()
        mock_app.config.get.side_effect = lambda key, default=None: {"userId": "123", "tenantId": 456}.get(key, default)
        mock_app_class.return_value = mock_app

        user_id, tenant_id = cci_importer_instance._get_user_context()

        assert user_id == "123"  # Code keeps user_id as string (UUID)
        assert tenant_id == 456

        # Should cache the result
        user_id2, tenant_id2 = cci_importer_instance._get_user_context()
        assert user_id2 == "123"
        assert tenant_id2 == 456

    @patch("regscale.integrations.public.cci_importer.Application")
    def test_get_user_context_none_user_id(self, mock_app_class, cci_importer_instance):
        """Test handling None user ID in config."""
        mock_app = MagicMock()
        mock_app.config.get.side_effect = lambda key, default=None: {"userId": None, "tenantId": "456"}.get(
            key, default
        )
        mock_app_class.return_value = mock_app

        user_id, tenant_id = cci_importer_instance._get_user_context()

        assert user_id is None
        assert tenant_id == 456  # tenant_id converted to int

    @patch("regscale.models.regscale_models.Catalog.get")
    def test_get_catalog_success(self, mock_get, cci_importer_instance):
        """Test successful catalog retrieval."""
        mock_catalog = MagicMock()
        mock_get.return_value = mock_catalog

        result = cci_importer_instance._get_catalog(1)

        assert result == mock_catalog
        mock_get.assert_called_once_with(id=1)

    @patch("regscale.integrations.public.cci_importer.error_and_exit")
    @patch("regscale.models.regscale_models.Catalog.get")
    def test_get_catalog_not_found(self, mock_get, mock_error_exit, cci_importer_instance):
        """Test catalog not found scenario."""
        mock_get.return_value = None
        mock_error_exit.side_effect = SystemExit(1)  # Mock the actual exit behavior

        with pytest.raises(SystemExit):
            cci_importer_instance._get_catalog(999)

        mock_error_exit.assert_called_once_with("Catalog with id 999 not found. Please ensure the catalog exists.")

    @patch("regscale.models.regscale_models.CCI.get_all_by_parent")
    def test_find_existing_cci(self, mock_get_all, cci_importer_instance):
        """Test finding existing CCI by ID."""
        mock_cci1 = MagicMock()
        mock_cci1.uuid = "CCI-000001"
        mock_cci2 = MagicMock()
        mock_cci2.uuid = "CCI-000002"

        mock_get_all.return_value = [mock_cci1, mock_cci2]

        result = cci_importer_instance._find_existing_cci(123, "CCI-000001")
        assert result == mock_cci1

        result = cci_importer_instance._find_existing_cci(123, "CCI-999999")
        assert result is None

    def test_create_cci_data(self, cci_importer_instance):
        """Test creating CCI data structure."""
        current_time = "2023-01-01 12:00:00"

        result = cci_importer_instance._create_cci_data("CCI-000001", "Test definition", "uuid-123", 456, current_time)

        expected = {
            "name": "CCI-000001",
            "description": "Test definition",
            "controlType": "policy",
            "publishDate": current_time,
            "dateLastUpdated": current_time,
            "lastUpdatedById": "uuid-123",
            "isPublic": True,
            "tenantsId": 456,
        }

        assert result == expected

    def test_create_cci_data_no_user(self, cci_importer_instance):
        """Test creating CCI data with no user ID."""
        current_time = "2023-01-01 12:00:00"

        result = cci_importer_instance._create_cci_data("CCI-000001", "Test definition", None, 456, current_time)

        assert result["lastUpdatedById"] is None

    @patch("regscale.models.regscale_models.CCI")
    def test_update_existing_cci(self, mock_cci_class, cci_importer_instance):
        """Test updating an existing CCI."""
        mock_cci = MagicMock()
        cci_data = {"name": "Updated Name", "description": "Updated Description"}

        cci_importer_instance._update_existing_cci(mock_cci, cci_data)

        assert mock_cci.name == "Updated Name"
        assert mock_cci.description == "Updated Description"
        mock_cci.create_or_update.assert_called_once()

    @patch("regscale.integrations.public.cci_importer.CCI")
    def test_create_new_cci(self, mock_cci_class, cci_importer_instance):
        """Test creating a new CCI."""
        mock_cci = MagicMock()
        mock_cci_class.return_value = mock_cci
        mock_cci.create.return_value = mock_cci  # Mock the create method return

        cci_data = {"name": "CCI-000001", "description": "Test definition"}
        current_time = "2023-01-01 12:00:00"

        result = cci_importer_instance._create_new_cci("CCI-000001", cci_data, 123, "uuid-456", current_time)

        mock_cci_class.assert_called_once_with(
            uuid="CCI-000001", securityControlId=123, createdById="uuid-456", dateCreated=current_time, **cci_data
        )
        mock_cci.create.assert_called_once()
        assert result == mock_cci

    @patch("regscale.integrations.public.cci_importer.CCIImporter._get_user_context")
    @patch("regscale.integrations.public.cci_importer.CCIImporter._find_existing_cci")
    @patch("regscale.integrations.public.cci_importer.CCIImporter._create_new_cci")
    @patch("regscale.integrations.public.cci_importer.CCIImporter._update_existing_cci")
    def test_process_cci_for_control(self, mock_update, mock_create, mock_find, mock_context, cci_importer_instance):
        """Test processing CCI items for a control."""
        mock_context.return_value = ("uuid-123", 456)
        mock_find.side_effect = [None, MagicMock()]  # First not found, second found
        mock_create.return_value = MagicMock()

        cci_list = [
            {"cci_id": "CCI-000001", "definition": "Definition 1"},
            {"cci_id": "CCI-000002", "definition": "Definition 2"},
        ]

        created, updated = cci_importer_instance._process_cci_for_control(789, cci_list, "uuid-123", 456)

        assert created == 1
        assert updated == 1
        mock_create.assert_called_once()
        mock_update.assert_called_once()

    @patch("regscale.integrations.public.cci_importer.CCIImporter._get_catalog")
    @patch("regscale.integrations.public.cci_importer.CCIImporter._get_user_context")
    @patch("regscale.integrations.public.cci_importer.CCIImporter._process_cci_for_control")
    @patch("regscale.models.regscale_models.SecurityControl.get_all_by_parent")
    def test_map_to_security_controls(
        self, mock_get_controls, mock_process, mock_context, mock_catalog, cci_importer_instance
    ):
        """Test mapping CCI data to security controls."""
        # Setup mocks
        mock_catalog_obj = MagicMock()
        mock_catalog_obj.id = 1
        mock_catalog.return_value = mock_catalog_obj

        mock_control1 = MagicMock()
        mock_control1.controlId = "AC-1"
        mock_control1.id = 101
        mock_control2 = MagicMock()
        mock_control2.controlId = "AC-2"
        mock_control2.id = 102
        mock_get_controls.return_value = [mock_control1, mock_control2]

        mock_context.return_value = ("uuid-123", 456)
        mock_process.return_value = (2, 1)  # 2 created, 1 updated

        # Setup test data
        cci_importer_instance.normalized_cci = {
            "AC-1": [{"cci_id": "CCI-000001", "definition": "Definition 1"}],
            "AC-2": [{"cci_id": "CCI-000002", "definition": "Definition 2"}],
            "AC-99": [{"cci_id": "CCI-000099", "definition": "Definition 99"}],  # Non-existent control
        }

        result = cci_importer_instance.map_to_security_controls(catalog_id=1)

        assert result["created"] == 4  # 2 calls * 2 created each
        assert result["updated"] == 2  # 2 calls * 1 updated each
        assert result["skipped"] == 1  # AC-99 control not found
        assert result["total_processed"] == 3

        mock_catalog.assert_called_once_with(1)
        assert mock_process.call_count == 2  # Called for AC-1 and AC-2

    def test_get_normalized_cci(self, cci_importer_instance):
        """Test getting normalized CCI data."""
        test_data = {"AC-1": [{"cci_id": "CCI-000001", "definition": "Test"}]}
        cci_importer_instance.normalized_cci = test_data

        result = cci_importer_instance.get_normalized_cci()
        assert result == test_data

    def test_format_index(self, cci_importer_instance):
        """Test formatting CCI index strings."""
        # Basic formatting
        assert cci_importer_instance.format_index("AC-1 a 1") == "AC-1(a)(1)"
        assert cci_importer_instance.format_index("AC-2 a") == "AC-2(a)"

        # Already formatted with parentheses
        assert cci_importer_instance.format_index("IA-13 (03) (a)") == "IA-13(03)(a)"

        # Mixed format
        assert cci_importer_instance.format_index("AC-1 a 1 (a)") == "AC-1(a)(1)(a)"

        # Single component (no parts)
        assert cci_importer_instance.format_index("SC-7") == "SC-7"

        # Empty or whitespace
        assert cci_importer_instance.format_index("") == ""
        assert cci_importer_instance.format_index("   ") == ""

    def test_parse_objective_id(self, cci_importer_instance):
        """Test parsing objective otherId strings."""
        # Basic control with part
        control_base, part = cci_importer_instance.parse_objective_id("ac-1_smt.a")
        assert control_base == "AC-1"
        assert part == "a"

        # Enhancement with part
        control_base, part = cci_importer_instance.parse_objective_id("ac-2.3_smt.a")
        assert control_base == "AC-2(3)"
        assert part == "a"

        # Enhancement with part (different enhancement number)
        control_base, part = cci_importer_instance.parse_objective_id("au-10.1_smt.b")
        assert control_base == "AU-10(1)"
        assert part == "b"

        # Enhancement without part
        control_base, part = cci_importer_instance.parse_objective_id("ac-2.4_smt")
        assert control_base == "AC-2(4)"
        assert part is None

        # Invalid format
        control_base, part = cci_importer_instance.parse_objective_id("invalid")
        assert control_base is None
        assert part is None

        # Invalid format (no _smt)
        control_base, part = cci_importer_instance.parse_objective_id("ac-1.a")
        assert control_base is None
        assert part is None

    def test_parse_objective_id_revision_4(self, cci_importer_instance):
        """Test parsing objective otherId strings in NIST 800-53 Revision 4 format."""
        # Rev 4 format: control_smt.part.subpart
        control_base, part = cci_importer_instance.parse_objective_id("ac-1_smt.a.1")
        assert control_base == "AC-1"
        assert part == "a"

        control_base, part = cci_importer_instance.parse_objective_id("ac-1_smt.b.2")
        assert control_base == "AC-1"
        assert part == "b"

        # Rev 4 with enhancement
        control_base, part = cci_importer_instance.parse_objective_id("ac-2.3_smt.d.1")
        assert control_base == "AC-2(3)"
        assert part == "d"

        # Rev 4 with multiple digit subpart
        control_base, part = cci_importer_instance.parse_objective_id("au-10.1_smt.c.15")
        assert control_base == "AU-10(1)"
        assert part == "c"

    def test_find_matching_ccis(self, cci_importer_instance):
        """Test finding matching CCIs by control base and part."""
        cci_map = {
            "AC-1(a)": "CCI-000001",
            "AC-1(a)(1)": "CCI-000002",
            "AC-1(a)(2)": "CCI-000003",
            "AC-1(b)": "CCI-000004",
            "AC-2(3)": "CCI-000005",
            "AC-2(3)(a)": "CCI-000006",
        }

        # Match with part 'a'
        matches = cci_importer_instance.find_matching_ccis("AC-1", "a", cci_map)
        assert len(matches) == 3
        assert "CCI-000001" in matches
        assert "CCI-000002" in matches
        assert "CCI-000003" in matches

        # Match with part 'b'
        matches = cci_importer_instance.find_matching_ccis("AC-1", "b", cci_map)
        assert len(matches) == 1
        assert "CCI-000004" in matches

        # Enhancement without part (exact match only)
        matches = cci_importer_instance.find_matching_ccis("AC-2(3)", None, cci_map)
        assert len(matches) == 1
        assert "CCI-000005" in matches

        # No matches
        matches = cci_importer_instance.find_matching_ccis("AC-99", "a", cci_map)
        assert len(matches) == 0

    def test_find_matching_ccis_by_name(self, cci_importer_instance):
        """Test finding CCIs by name fallback method."""
        cci_map = {
            "AC-1(a)": "CCI-000001",
            "AC-1(a)(1)": "CCI-000002",
            "AC-2(4)": "CCI-000003",
        }

        # Exact match by name
        matches = cci_importer_instance.find_matching_ccis_by_name("AC-2(4)", "AC-2(4)", cci_map)
        assert len(matches) == 1
        assert "CCI-000003" in matches

        # Single letter match
        matches = cci_importer_instance.find_matching_ccis_by_name("AC-1", "a.", cci_map)
        assert len(matches) == 2
        assert "CCI-000001" in matches
        assert "CCI-000002" in matches

        # Single letter without period
        matches = cci_importer_instance.find_matching_ccis_by_name("AC-1", "a", cci_map)
        assert len(matches) == 2

        # No match
        matches = cci_importer_instance.find_matching_ccis_by_name("AC-1", "xyz", cci_map)
        assert len(matches) == 0

    def test_find_matching_ccis_by_name_revision_4(self, cci_importer_instance):
        """Test finding CCIs by name using NIST 800-53 Revision 4 label formats."""
        cci_map = {
            "AC-1(a)": "CCI-000001",
            "AC-1(a)(1)": "CCI-000002",
            "AC-1(b)": "CCI-000003",
            "AC-1(b)(2)": "CCI-000004",
        }

        # Rev 4 label format: "a.1."
        matches = cci_importer_instance.find_matching_ccis_by_name("AC-1", "a.1.", cci_map)
        assert len(matches) == 2
        assert "CCI-000001" in matches
        assert "CCI-000002" in matches

        # Rev 4 label format without trailing period: "a.1"
        matches = cci_importer_instance.find_matching_ccis_by_name("AC-1", "a.1", cci_map)
        assert len(matches) == 2

        # Rev 4 label format: "b.2."
        matches = cci_importer_instance.find_matching_ccis_by_name("AC-1", "b.2.", cci_map)
        assert len(matches) == 2
        assert "CCI-000003" in matches
        assert "CCI-000004" in matches

        # Invalid rev 4 format (no digit)
        matches = cci_importer_instance.find_matching_ccis_by_name("AC-1", "a.", cci_map)
        assert len(matches) == 2  # Should still match as single letter

    def test_ccis_already_present(self, cci_importer_instance):
        """Test checking for duplicate CCI IDs."""
        # CCIs already present
        current = "ac-1_smt.a, CCI-000001, CCI-000002"
        new = "CCI-000002, CCI-000003"
        assert cci_importer_instance.ccis_already_present(current, new) is True

        # No overlap
        current = "ac-1_smt.a, CCI-000001, CCI-000002"
        new = "CCI-000003, CCI-000004"
        assert cci_importer_instance.ccis_already_present(current, new) is False

        # Empty current
        current = ""
        new = "CCI-000001"
        assert cci_importer_instance.ccis_already_present(current, new) is False

        # No CCI IDs in current
        current = "ac-1_smt.a"
        new = "CCI-000001"
        assert cci_importer_instance.ccis_already_present(current, new) is False

    def test_parse_cci_creates_grouped_index(self, cci_importer_instance):
        """Test that parse_cci creates both normalized_cci and cci_grouped_by_index."""
        cci_importer_instance.parse_cci()

        # Check normalized_cci was created
        assert len(cci_importer_instance.normalized_cci) > 0

        # Check cci_grouped_by_index was created
        assert len(cci_importer_instance.cci_grouped_by_index) > 0

        # Verify formatted indices
        # The sample data has "AC-1 a" and "AC-1 b" and "AC-2 a 1"
        assert "AC-1(a)" in cci_importer_instance.cci_grouped_by_index
        assert "AC-1(b)" in cci_importer_instance.cci_grouped_by_index
        assert "AC-2(a)(1)" in cci_importer_instance.cci_grouped_by_index

    @patch("regscale.integrations.public.cci_importer.ControlObjective")
    def test_map_to_control_objectives(self, mock_objective_class, cci_importer_instance):
        """Test mapping CCIs to control objectives."""
        # Setup sample grouped index data
        cci_importer_instance.cci_grouped_by_index = {
            "AC-1(a)": "CCI-000001, CCI-000002",
            "AC-1(b)": "CCI-000003",
            "AC-2(3)": "CCI-000004",
        }

        # Create mock objectives
        mock_obj1 = MagicMock()
        mock_obj1.otherId = "ac-1_smt.a"
        mock_obj1.name = "a."

        mock_obj2 = MagicMock()
        mock_obj2.otherId = "ac-1_smt.b"
        mock_obj2.name = "b."

        mock_obj3 = MagicMock()
        mock_obj3.otherId = "ac-2.3_smt"
        mock_obj3.name = "AC-2(3)"

        mock_obj4 = MagicMock()
        mock_obj4.otherId = "invalid"
        mock_obj4.name = "invalid"

        mock_objective_class.get_by_catalog.return_value = [mock_obj1, mock_obj2, mock_obj3, mock_obj4]

        # Run the mapping
        result = cci_importer_instance.map_to_control_objectives(catalog_id=1)

        # Verify results
        assert result["updated"] == 3
        assert result["not_found"] == 1
        assert result["skipped"] == 0
        assert result["total_processed"] == 4

        # Verify CCIs were added to otherId
        assert "CCI-000001, CCI-000002" in mock_obj1.otherId
        assert "CCI-000003" in mock_obj2.otherId
        assert "CCI-000004" in mock_obj3.otherId

        # Verify save was called
        assert mock_obj1.save.call_count == 1
        assert mock_obj2.save.call_count == 1
        assert mock_obj3.save.call_count == 1

    @patch("regscale.integrations.public.cci_importer.ControlObjective")
    def test_map_to_control_objectives_with_duplicates(self, mock_objective_class, cci_importer_instance):
        """Test that duplicate CCIs are not added again."""
        cci_importer_instance.cci_grouped_by_index = {"AC-1(a)": "CCI-000001, CCI-000002"}

        # Create mock objective with existing CCIs
        mock_obj = MagicMock()
        mock_obj.otherId = "ac-1_smt.a, CCI-000001"
        mock_obj.name = "a."

        mock_objective_class.get_by_catalog.return_value = [mock_obj]

        # Run the mapping
        result = cci_importer_instance.map_to_control_objectives(catalog_id=1)

        # Should be skipped due to duplicate
        assert result["skipped"] == 1
        assert result["updated"] == 0

        # Verify save was NOT called
        mock_obj.save.assert_not_called()

    @patch("regscale.integrations.public.cci_importer.ControlObjective")
    def test_map_to_control_objectives_fallback_by_name(self, mock_objective_class, cci_importer_instance):
        """Test fallback matching by name when otherId doesn't match."""
        cci_importer_instance.cci_grouped_by_index = {"AC-1(a)": "CCI-000001"}

        # Create mock objective with non-standard otherId but valid name
        mock_obj = MagicMock()
        mock_obj.otherId = "custom_id"
        mock_obj.name = "a."

        # This would normally fail otherId parsing, but should work with name fallback
        # However, the parse_objective_id will return None, None for "custom_id"
        # So it won't match. Let me adjust the test.

        # Actually, looking at the code, if parse_objective_id returns None, it skips
        # So the fallback only works if control_base is valid
        # Let me create a better test

        mock_obj.otherId = "ac-1_smt"  # Valid but no part
        mock_obj.name = "a"  # Single letter should match as part

        mock_objective_class.get_by_catalog.return_value = [mock_obj]

        # This should use fallback matching
        result = cci_importer_instance.map_to_control_objectives(catalog_id=1)

        # With the current logic, ac-1_smt will parse to ("AC-1", None)
        # Then it tries to match with find_matching_ccis("AC-1", None, cci_map)
        # which will only match exact "AC-1" with no remainder
        # So it won't find "AC-1(a)"
        # Then it falls back to find_matching_ccis_by_name("AC-1", "a", cci_map)
        # which should find "AC-1(a)"

        assert result["updated"] == 1

    @patch("regscale.integrations.public.cci_importer.ControlObjective")
    def test_map_to_control_objectives_revision_4_format(self, mock_objective_class):
        """Test mapping CCIs to control objectives using NIST 800-53 Revision 4 formats."""
        # Create XML with rev 4 references
        xml_content = """<?xml version="1.0" encoding="utf-8"?>
        <cci_list xmlns="http://iase.disa.mil/cci">
            <cci_item id="CCI-000001">
                <definition>Rev 4 definition for AC-1 a 1</definition>
                <references>
                    <reference creator="NIST" title="NIST SP 800-53 Revision 4" version="4"
                              location="AC-1" index="AC-1 a 1" />
                </references>
            </cci_item>
            <cci_item id="CCI-000002">
                <definition>Rev 4 definition for AC-1 a 2</definition>
                <references>
                    <reference creator="NIST" title="NIST SP 800-53 Revision 4" version="4"
                              location="AC-1" index="AC-1 a 2" />
                </references>
            </cci_item>
            <cci_item id="CCI-000003">
                <definition>Rev 4 definition for AC-1 b 1</definition>
                <references>
                    <reference creator="NIST" title="NIST SP 800-53 Revision 4" version="4"
                              location="AC-1" index="AC-1 b 1" />
                </references>
            </cci_item>
        </cci_list>"""

        root = ET.fromstring(xml_content)
        importer = CCIImporter(root, version="4", verbose=False)
        importer.parse_cci()

        # Create mock objectives with rev 4 format (otherId with subparts)
        mock_obj1 = MagicMock()
        mock_obj1.otherId = "ac-1_smt.a.1"  # Rev 4 format: part.subpart
        mock_obj1.name = "a.1."

        mock_obj2 = MagicMock()
        mock_obj2.otherId = "ac-1_smt.a.2"
        mock_obj2.name = "a.2."

        mock_obj3 = MagicMock()
        mock_obj3.otherId = "ac-1_smt.b.1"
        mock_obj3.name = "b.1."

        mock_objective_class.get_by_catalog.return_value = [mock_obj1, mock_obj2, mock_obj3]

        # Run the mapping
        result = importer.map_to_control_objectives(catalog_id=1)

        # Verify all rev 4 objectives were successfully mapped
        assert result["updated"] == 3
        assert result["not_found"] == 0
        assert result["skipped"] == 0
        assert result["total_processed"] == 3

        # Verify CCIs were added to otherId
        assert "CCI-000001" in mock_obj1.otherId
        assert "CCI-000002" in mock_obj2.otherId
        assert "CCI-000003" in mock_obj3.otherId

        # Verify save was called for all
        assert mock_obj1.save.call_count == 1
        assert mock_obj2.save.call_count == 1
        assert mock_obj3.save.call_count == 1

    @patch("regscale.integrations.public.cci_importer.ControlObjective")
    def test_map_to_control_objectives_revision_5_format(self, mock_objective_class):
        """Test mapping CCIs to control objectives using NIST 800-53 Revision 5 formats."""
        # Create XML with rev 5 references
        xml_content = """<?xml version="1.0" encoding="utf-8"?>
        <cci_list xmlns="http://iase.disa.mil/cci">
            <cci_item id="CCI-000001">
                <definition>Rev 5 definition for AC-1 a 1 (a)</definition>
                <references>
                    <reference creator="NIST" title="NIST SP 800-53 Revision 5" version="5"
                              location="AC-1" index="AC-1 a 1 (a)" />
                </references>
            </cci_item>
            <cci_item id="CCI-000002">
                <definition>Rev 5 definition for AC-1 a 2</definition>
                <references>
                    <reference creator="NIST" title="NIST SP 800-53 Revision 5" version="5"
                              location="AC-1" index="AC-1 a 2" />
                </references>
            </cci_item>
            <cci_item id="CCI-000003">
                <definition>Rev 5 definition for AC-1 c 1</definition>
                <references>
                    <reference creator="NIST" title="NIST SP 800-53 Revision 5" version="5"
                              location="AC-1" index="AC-1 c 1" />
                </references>
            </cci_item>
        </cci_list>"""

        root = ET.fromstring(xml_content)
        importer = CCIImporter(root, version="5", verbose=False)
        importer.parse_cci()

        # Create mock objectives with rev 5 format (no subparts)
        mock_obj1 = MagicMock()
        mock_obj1.otherId = "ac-1_smt.a"  # Rev 5 format: just part letter
        mock_obj1.name = "a"

        mock_obj2 = MagicMock()
        mock_obj2.otherId = "ac-1_smt.c"
        mock_obj2.name = "c"

        mock_objective_class.get_by_catalog.return_value = [mock_obj1, mock_obj2]

        # Run the mapping
        result = importer.map_to_control_objectives(catalog_id=1)

        # Verify rev 5 objectives were successfully mapped
        # obj1 should get both CCI-000001 (AC-1(a)(1)(a)) and CCI-000002 (AC-1(a)(2))
        # obj2 should get CCI-000003 (AC-1(c)(1))
        assert result["updated"] == 2
        assert result["not_found"] == 0
        assert result["skipped"] == 0
        assert result["total_processed"] == 2

        # Verify CCIs were added to otherId
        assert "CCI-000001" in mock_obj1.otherId or "CCI-000002" in mock_obj1.otherId
        assert "CCI-000003" in mock_obj2.otherId

        # Verify save was called for both
        assert mock_obj1.save.call_count == 1
        assert mock_obj2.save.call_count == 1

    @patch("regscale.integrations.public.cci_importer.ControlObjective")
    def test_map_to_control_objectives_mixed_revisions(self, mock_objective_class):
        """Test mapping CCIs with mixed revision 4 and 5 control objectives."""
        # Create XML with both rev 4 and rev 5 references
        xml_content = """<?xml version="1.0" encoding="utf-8"?>
        <cci_list xmlns="http://iase.disa.mil/cci">
            <cci_item id="CCI-000001">
                <definition>AC-1 part a definition</definition>
                <references>
                    <reference creator="NIST" title="NIST SP 800-53 Revision 4" version="4"
                              location="AC-1" index="AC-1 a 1" />
                    <reference creator="NIST" title="NIST SP 800-53 Revision 5" version="5"
                              location="AC-1" index="AC-1 a 1 (a)" />
                </references>
            </cci_item>
        </cci_list>"""

        root = ET.fromstring(xml_content)

        # Test with rev 4 importer
        importer_v4 = CCIImporter(root, version="4", verbose=False)
        importer_v4.parse_cci()

        mock_obj_v4 = MagicMock()
        mock_obj_v4.otherId = "ac-1_smt.a.1"
        mock_obj_v4.name = "a.1."

        mock_objective_class.get_by_catalog.return_value = [mock_obj_v4]

        result_v4 = importer_v4.map_to_control_objectives(catalog_id=1)
        assert result_v4["updated"] == 1
        assert "CCI-000001" in mock_obj_v4.otherId

        # Test with rev 5 importer
        importer_v5 = CCIImporter(root, version="5", verbose=False)
        importer_v5.parse_cci()

        mock_obj_v5 = MagicMock()
        mock_obj_v5.otherId = "ac-1_smt.a"
        mock_obj_v5.name = "a"

        mock_objective_class.get_by_catalog.return_value = [mock_obj_v5]

        result_v5 = importer_v5.map_to_control_objectives(catalog_id=1)
        assert result_v5["updated"] == 1
        assert "CCI-000001" in mock_obj_v5.otherId

    @patch("regscale.integrations.public.cci_importer.ControlObjective")
    def test_map_to_control_objectives_revision_4_with_enhancements(self, mock_objective_class):
        """Test mapping CCIs with revision 4 control enhancements."""
        xml_content = """<?xml version="1.0" encoding="utf-8"?>
        <cci_list xmlns="http://iase.disa.mil/cci">
            <cci_item id="CCI-000001">
                <definition>AC-2(3) enhancement definition</definition>
                <references>
                    <reference creator="NIST" title="NIST SP 800-53 Revision 4" version="4"
                              location="AC-2(3)" index="AC-2 (3)" />
                </references>
            </cci_item>
            <cci_item id="CCI-000002">
                <definition>AC-2(3) part d definition</definition>
                <references>
                    <reference creator="NIST" title="NIST SP 800-53 Revision 4" version="4"
                              location="AC-2(3)" index="AC-2 (3) d" />
                </references>
            </cci_item>
        </cci_list>"""

        root = ET.fromstring(xml_content)
        importer = CCIImporter(root, version="4", verbose=False)
        importer.parse_cci()

        # Create mock objectives with rev 4 enhancement format
        mock_obj1 = MagicMock()
        mock_obj1.otherId = "ac-2.3_smt"  # Enhancement without part
        mock_obj1.name = "AC-2(3)"

        mock_obj2 = MagicMock()
        mock_obj2.otherId = "ac-2.3_smt.d.1"  # Enhancement with part and subpart
        mock_obj2.name = "d.1."

        mock_objective_class.get_by_catalog.return_value = [mock_obj1, mock_obj2]

        result = importer.map_to_control_objectives(catalog_id=1)

        assert result["updated"] == 2
        assert result["not_found"] == 0

        # Verify the enhancement without part got the base CCI
        assert "CCI-000001" in mock_obj1.otherId
        # Verify the enhancement with part got the part-specific CCI
        assert "CCI-000002" in mock_obj2.otherId

    @patch("regscale.integrations.public.cci_importer.ControlObjective")
    def test_map_to_control_objectives_revision_4_label_fallback(self, mock_objective_class):
        """Test that revision 4 label format fallback matching works correctly."""
        xml_content = """<?xml version="1.0" encoding="utf-8"?>
        <cci_list xmlns="http://iase.disa.mil/cci">
            <cci_item id="CCI-000001">
                <definition>AC-1 part a definition</definition>
                <references>
                    <reference creator="NIST" title="NIST SP 800-53 Revision 4" version="4"
                              location="AC-1" index="AC-1 a" />
                </references>
            </cci_item>
        </cci_list>"""

        root = ET.fromstring(xml_content)
        importer = CCIImporter(root, version="4", verbose=False)
        importer.parse_cci()

        # Create objective with rev 4 format where otherId parsing should work
        mock_obj = MagicMock()
        mock_obj.otherId = "ac-1_smt"  # No part specified
        mock_obj.name = "a.1."  # Rev 4 label format should trigger fallback

        mock_objective_class.get_by_catalog.return_value = [mock_obj]

        result = importer.map_to_control_objectives(catalog_id=1)

        # Should successfully map using fallback name matching
        assert result["updated"] == 1
        assert "CCI-000001" in mock_obj.otherId


class TestCCIImporterCLI:
    """Test cases for the CCI importer CLI command."""

    @patch("regscale.integrations.public.cci_importer._load_xml_file")
    @patch("regscale.integrations.public.cci_importer.CCIImporter")
    def test_cci_importer_command_dry_run(self, mock_importer_class, mock_load_xml):
        """Test CLI command with dry run flag."""
        runner = CliRunner()

        # Setup mocks
        mock_root = MagicMock()
        mock_load_xml.return_value = mock_root

        mock_importer = MagicMock()
        mock_importer.get_normalized_cci.return_value = {"AC-1": []}
        mock_importer_class.return_value = mock_importer

        result = runner.invoke(cci_importer, ["--dry-run", "--verbose"])

        # More detailed assertion with error context
        if result.exit_code != 0:
            print(f"Command output: {result.output}")
            print(f"Exception: {result.exception}")
        assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"
        mock_load_xml.assert_called_once()
        mock_importer_class.assert_called_once_with(mock_root, version="5", verbose=True)
        mock_importer.parse_cci.assert_called_once()
        mock_importer.map_to_security_controls.assert_not_called()

    @patch("regscale.integrations.public.cci_importer._load_xml_file")
    @patch("regscale.integrations.public.cci_importer.CCIImporter")
    def test_cci_importer_command_with_database(self, mock_importer_class, mock_load_xml):
        """Test CLI command with database operations (default: maps to objectives)."""
        runner = CliRunner()

        # Setup mocks
        mock_root = MagicMock()
        mock_load_xml.return_value = mock_root

        mock_importer = MagicMock()
        mock_importer.get_normalized_cci.return_value = {"AC-1": []}
        mock_importer.map_to_security_controls.return_value = {
            "created": 5,
            "updated": 3,
            "skipped": 1,
            "total_processed": 2,
        }
        mock_importer.map_to_control_objectives.return_value = {
            "updated": 10,
            "skipped": 2,
            "not_found": 1,
            "total_processed": 13,
        }
        mock_importer_class.return_value = mock_importer

        result = runner.invoke(cci_importer, ["-n", "4", "-c", "2"])

        # More detailed assertion with error context
        if result.exit_code != 0:
            print(f"Command output: {result.output}")
            print(f"Exception: {result.exception}")
        assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}. Output: {result.output}"
        mock_importer_class.assert_called_once_with(mock_root, version="4", verbose=False)
        mock_importer.map_to_security_controls.assert_called_with(2)
        # By default, should also map to objectives
        mock_importer.map_to_control_objectives.assert_called_with(2)

    @patch("regscale.integrations.public.cci_importer._load_xml_file")
    @patch("regscale.integrations.public.cci_importer.CCIImporter")
    def test_cci_importer_command_with_disable_objectives(self, mock_importer_class, mock_load_xml):
        """Test CLI command with --disable-objectives flag."""
        runner = CliRunner()

        # Setup mocks
        mock_root = MagicMock()
        mock_load_xml.return_value = mock_root

        mock_importer = MagicMock()
        mock_importer.get_normalized_cci.return_value = {"AC-1": []}
        mock_importer.map_to_security_controls.return_value = {
            "created": 5,
            "updated": 3,
            "skipped": 1,
            "total_processed": 2,
        }
        mock_importer_class.return_value = mock_importer

        result = runner.invoke(cci_importer, ["-n", "4", "-c", "2", "--disable-objectives"])

        # Should succeed
        assert result.exit_code == 0
        mock_importer_class.assert_called_once_with(mock_root, version="4", verbose=False)
        mock_importer.map_to_security_controls.assert_called_with(2)
        # Should NOT map to objectives when flag is set
        mock_importer.map_to_control_objectives.assert_not_called()

    @patch("regscale.integrations.public.cci_importer._load_xml_file")
    def test_cci_importer_command_xml_error(self, mock_load_xml):
        """Test CLI command with XML loading error."""
        runner = CliRunner()

        mock_load_xml.side_effect = ET.ParseError("Invalid XML")

        result = runner.invoke(cci_importer)

        assert result.exit_code != 0

    def test_load_xml_file_success(self, tmp_path):
        """Test successful XML file loading."""
        xml_content = """<?xml version="1.0" encoding="utf-8"?>
        <cci_list xmlns="http://iase.disa.mil/cci">
            <cci_item id="CCI-000001">
                <definition>Test definition</definition>
            </cci_item>
        </cci_list>"""

        xml_file = tmp_path / "test.xml"
        xml_file.write_text(xml_content)

        root = _load_xml_file(str(xml_file))

        assert root is not None
        assert root.tag.endswith("cci_list")

    def test_load_xml_file_parse_error(self, tmp_path):
        """Test XML file loading with parse error."""
        invalid_xml = "This is not valid XML"

        xml_file = tmp_path / "invalid.xml"
        xml_file.write_text(invalid_xml)

        with pytest.raises(SystemExit):
            _load_xml_file(str(xml_file))


class TestCCIImporterIntegration:
    """Integration tests for CCI importer."""

    def test_full_workflow_dry_run(self):
        """Test full workflow in dry run mode."""
        xml_content = """<?xml version="1.0" encoding="utf-8"?>
        <cci_list xmlns="http://iase.disa.mil/cci">
            <cci_item id="CCI-000001">
                <definition>Test definition for AC-1</definition>
                <references>
                    <reference creator="NIST" title="NIST SP 800-53 Revision 5" version="5"
                              location="AC-1" index="AC-1 a" />
                </references>
            </cci_item>
        </cci_list>"""

        root = ET.fromstring(xml_content)
        importer = CCIImporter(root, version="5", verbose=False)

        # Parse CCI data
        importer.parse_cci()
        normalized = importer.get_normalized_cci()

        # Verify parsing worked correctly
        assert "AC-1" in normalized
        assert len(normalized["AC-1"]) == 1
        assert normalized["AC-1"][0]["cci_id"] == "CCI-000001"
        assert "Test definition for AC-1" in normalized["AC-1"][0]["definition"]

    @patch("regscale.integrations.public.cci_importer.Application")
    def test_user_context_caching(self, mock_app_class):
        """Test that user context is properly cached."""
        mock_app = MagicMock()
        mock_app.config.get.side_effect = lambda key, default=None: {"userId": "uuid-123", "tenantId": "456"}.get(
            key, default
        )
        mock_app_class.return_value = mock_app

        root = ET.fromstring("<root></root>")
        importer = CCIImporter(root)

        # First call should create the context
        context1 = importer._get_user_context()
        # Second call should use cached context
        context2 = importer._get_user_context()

        assert context1 == context2
        assert mock_app_class.call_count == 1  # Should only create Application once
