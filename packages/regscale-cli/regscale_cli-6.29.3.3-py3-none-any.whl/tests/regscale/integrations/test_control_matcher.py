#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit and integration tests for control_matcher module

This module provides comprehensive test coverage for the ControlMatcher class,
including control ID parsing, catalog searches, implementation matching, and caching.
"""

import logging
from typing import Dict, List, Optional, Tuple
from unittest.mock import MagicMock, Mock, patch

import pytest

from regscale.core.app.api import Api
from regscale.core.app.application import Application
from regscale.integrations.control_matcher import ControlMatcher
from regscale.models.regscale_models.control_implementation import ControlImplementation
from regscale.models.regscale_models.security_control import SecurityControl


class TestControlMatcherInit:
    """Test cases for ControlMatcher initialization"""

    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_init_with_no_app(self, mock_app_class, mock_api_class):
        """Test ControlMatcher initialization without providing an app"""
        mock_app = MagicMock(spec=Application)
        mock_app_class.return_value = mock_app
        mock_api = MagicMock(spec=Api)
        mock_api_class.return_value = mock_api

        matcher = ControlMatcher()

        mock_app_class.assert_called_once()
        mock_api_class.assert_called_once()
        assert matcher.app == mock_app
        assert matcher.api == mock_api
        assert matcher._catalog_cache == {}
        assert matcher._control_impl_cache == {}

    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_init_with_app(self, mock_app_class, mock_api_class):
        """Test ControlMatcher initialization with an app instance"""
        # Create a mock app that is truthy (has a return value)
        mock_app = Mock(spec=Application)
        # Set a non-None return value to make the mock truthy
        mock_app.return_value = MagicMock()

        mock_api = MagicMock(spec=Api)
        mock_api_class.return_value = mock_api

        matcher = ControlMatcher(app=mock_app)

        # When app is provided and is truthy, it should be used
        assert matcher.app == mock_app
        assert matcher.api == mock_api
        assert matcher._catalog_cache == {}
        assert matcher._control_impl_cache == {}


class TestControlMatcherParseControlId:
    """Test cases for parse_control_id method"""

    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_parse_control_id_none(self, mock_app_class, mock_api_class):
        """Test parsing None control ID returns None"""
        matcher = ControlMatcher()
        result = matcher.parse_control_id(None)
        assert result is None

    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_parse_control_id_empty_string(self, mock_app_class, mock_api_class):
        """Test parsing empty string returns None"""
        matcher = ControlMatcher()
        result = matcher.parse_control_id("")
        assert result is None

    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_parse_control_id_whitespace(self, mock_app_class, mock_api_class):
        """Test parsing whitespace-only string returns None"""
        matcher = ControlMatcher()
        result = matcher.parse_control_id("   ")
        assert result is None

    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_parse_control_id_basic_format(self, mock_app_class, mock_api_class):
        """Test parsing basic NIST control ID format"""
        matcher = ControlMatcher()
        test_cases = [
            ("AC-1", "AC-1"),
            ("ac-1", "AC-1"),
            ("AC-10", "AC-10"),
            ("SI-2", "SI-2"),
            ("CM-6", "CM-6"),
        ]

        for input_id, expected in test_cases:
            result = matcher.parse_control_id(input_id)
            assert result == expected, f"Failed for input {input_id}"

    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_parse_control_id_with_parentheses(self, mock_app_class, mock_api_class):
        """Test parsing control ID with parentheses converts to dots"""
        matcher = ControlMatcher()
        test_cases = [
            ("AC-1(1)", "AC-1.1"),
            ("ac-2(3)", "AC-2.3"),
            ("SI-4(10)", "SI-4.10"),
            ("CM-6(1)", "CM-6.1"),
        ]

        for input_id, expected in test_cases:
            result = matcher.parse_control_id(input_id)
            assert result == expected, f"Failed for input {input_id}"

    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_parse_control_id_with_dots(self, mock_app_class, mock_api_class):
        """Test parsing control ID already with dot notation"""
        matcher = ControlMatcher()
        test_cases = [
            ("AC-1.1", "AC-1.1"),
            ("ac-2.5", "AC-2.5"),
            ("SI-4.12", "SI-4.12"),
        ]

        for input_id, expected in test_cases:
            result = matcher.parse_control_id(input_id)
            assert result == expected, f"Failed for input {input_id}"

    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_parse_control_id_with_text(self, mock_app_class, mock_api_class):
        """Test parsing control ID with descriptive text"""
        matcher = ControlMatcher()
        test_cases = [
            ("Access Control AC-1", "AC-1"),
            ("AC-1 Access Control Policy", "AC-1"),
            ("NIST Control AC-2 Account Management", "AC-2"),
            ("System Monitoring SI-4(5)", "SI-4.5"),
        ]

        for input_id, expected in test_cases:
            result = matcher.parse_control_id(input_id)
            assert result == expected, f"Failed for input {input_id}"

    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_parse_control_id_multiple_controls_returns_first(self, mock_app_class, mock_api_class):
        """Test parsing string with multiple controls returns first one"""
        matcher = ControlMatcher()
        test_cases = [
            ("AC-1, AC-2", "AC-1"),
            ("SI-2, SI-4, CM-6", "SI-2"),
            ("AC-1(1), AC-1(2)", "AC-1.1"),
        ]

        for input_id, expected in test_cases:
            result = matcher.parse_control_id(input_id)
            assert result == expected, f"Failed for input {input_id}"

    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_parse_control_id_three_letter_family(self, mock_app_class, mock_api_class):
        """Test parsing control IDs with three-letter family codes"""
        matcher = ControlMatcher()
        test_cases = [
            ("PTA-1", "PTA-1"),
            ("SAR-10", "SAR-10"),
            ("PRM-3(2)", "PRM-3.2"),
        ]

        for input_id, expected in test_cases:
            result = matcher.parse_control_id(input_id)
            assert result == expected, f"Failed for input {input_id}"

    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_parse_control_id_no_match(self, mock_app_class, mock_api_class):
        """Test parsing invalid control ID format returns None"""
        matcher = ControlMatcher()
        test_cases = [
            "No control here",
            "12345",
            "A-1",  # Too short family code (single letter)
            "AC",  # Missing number
            "Control without ID",
        ]

        for input_id in test_cases:
            result = matcher.parse_control_id(input_id)
            assert result is None, f"Expected None for input {input_id}, got {result}"


class TestControlMatcherParseControlIdWithSpaces:
    """Test cases for parse_control_id method with spaces in control IDs"""

    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_parse_control_id_with_space_before_parenthesis(self, mock_app_class, mock_api_class):
        """Test parsing control ID with space before parenthesis"""
        matcher = ControlMatcher()
        test_cases = [
            ("AC-1 (1)", "AC-1.1"),
            ("AC-2 (3)", "AC-2.3"),
            ("SI-4 (10)", "SI-4.10"),
            ("CM-6 (1)", "CM-6.1"),
        ]

        for input_id, expected in test_cases:
            result = matcher.parse_control_id(input_id)
            assert result == expected, f"Failed for input {input_id}"

    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_parse_control_id_with_spaces_inside_parentheses(self, mock_app_class, mock_api_class):
        """Test parsing control ID with spaces inside parentheses"""
        matcher = ControlMatcher()
        test_cases = [
            ("AC-1( 1 )", "AC-1.1"),
            ("AC-2(  3  )", "AC-2.3"),
            ("SI-4( 10)", "SI-4.10"),
            ("CM-6(1 )", "CM-6.1"),
        ]

        for input_id, expected in test_cases:
            result = matcher.parse_control_id(input_id)
            assert result == expected, f"Failed for input {input_id}"

    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_parse_control_id_with_leading_zeros_and_spaces(self, mock_app_class, mock_api_class):
        """Test parsing control ID with both leading zeros and spaces"""
        matcher = ControlMatcher()
        test_cases = [
            ("AC-01 (01)", "AC-1.1"),
            ("AC-02 (04)", "AC-2.4"),
            ("AC-17 (02)", "AC-17.2"),
            ("SI-04 (05)", "SI-4.5"),
        ]

        for input_id, expected in test_cases:
            result = matcher.parse_control_id(input_id)
            assert result == expected, f"Failed for input {input_id}"

    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_parse_control_id_with_various_space_combinations(self, mock_app_class, mock_api_class):
        """Test parsing control ID with various space combinations"""
        matcher = ControlMatcher()
        test_cases = [
            ("AC-1  (1)", "AC-1.1"),  # Multiple spaces before
            ("AC-1 ( 1 )", "AC-1.1"),  # Spaces everywhere
            ("AC-1  (  1  )", "AC-1.1"),  # Multiple spaces everywhere
            ("AC-01  (  04  )", "AC-1.4"),  # Leading zeros and multiple spaces
        ]

        for input_id, expected in test_cases:
            result = matcher.parse_control_id(input_id)
            assert result == expected, f"Failed for input {input_id}"

    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_parse_control_id_with_spaces_in_text(self, mock_app_class, mock_api_class):
        """Test parsing control ID with spaces in descriptive text"""
        matcher = ControlMatcher()
        test_cases = [
            ("Access Control AC-1 (1)", "AC-1.1"),
            ("AC-2 (3) Account Management", "AC-2.3"),
            ("NIST Control AC-17 (02)", "AC-17.2"),
        ]

        for input_id, expected in test_cases:
            result = matcher.parse_control_id(input_id)
            assert result == expected, f"Failed for input {input_id}"


class TestControlMatcherNonNISTFrameworks:
    """Test cases for non-NIST framework support (SOC2, CIS, ISO)"""

    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_parse_soc2_control_id(self, mock_app_class, mock_api_class):
        """Test parsing SOC 2 control IDs"""
        matcher = ControlMatcher()

        # Test various SOC2 formats
        test_cases = [
            ("CC1.1 COSO Principle 1", "CC1.1"),
            ("PI1.5 Privacy Information", "PI1.5"),
            ("A1.2 Availability", "A1.2"),
            ("C1.1 Confidentiality", "C1.1"),
            ("P1.1 Processing Integrity", "P1.1"),
            ("cc1.1 lowercase", "CC1.1"),  # Should uppercase
        ]

        for input_str, expected in test_cases:
            result = matcher.parse_control_id(input_str)
            assert result == expected, f"Failed for {input_str}, got {result}"

    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_parse_cis_control_id(self, mock_app_class, mock_api_class):
        """Test parsing CIS control IDs"""
        matcher = ControlMatcher()

        # Test various CIS formats
        test_cases = [
            ("1.1 Ensure something", "1.1"),
            ("1.1.1 Ensure detailed", "1.1.1"),
            ("1.1.1.1 Ensure very detailed", "1.1.1.1"),
            ("2.3 Another control", "2.3"),
            ("12.4.5 Higher numbers", "12.4.5"),
        ]

        for input_str, expected in test_cases:
            result = matcher.parse_control_id(input_str)
            assert result == expected, f"Failed for {input_str}, got {result}"

    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_parse_iso_control_id(self, mock_app_class, mock_api_class):
        """Test parsing ISO 27001 control IDs"""
        matcher = ControlMatcher()

        # Test various ISO formats
        test_cases = [
            ("A.5.1 Policies for information security", "A.5.1"),
            ("A.5.1.1 Information security policy", "A.5.1.1"),
            ("A.12.3.1 Information backup", "A.12.3.1"),
            ("a.5.1 lowercase", "A.5.1"),  # Should uppercase
        ]

        for input_str, expected in test_cases:
            result = matcher.parse_control_id(input_str)
            assert result == expected, f"Failed for {input_str}, got {result}"

    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_detect_framework(self, mock_app_class, mock_api_class):
        """Test framework detection"""
        matcher = ControlMatcher()

        # Test framework detection
        test_cases = [
            ("AC-1", "NIST"),
            ("AC-1.1", "NIST"),
            ("CC1.1", "SOC2"),
            ("PI1.5", "SOC2"),
            ("1.1", "CIS"),
            ("1.1.1.1", "CIS"),
            ("A.5.1", "ISO"),
            ("A.12.3.1", "ISO"),
            ("CUSTOM123", "GENERIC"),
        ]

        for control_id, expected_framework in test_cases:
            result = matcher._detect_framework(control_id)
            assert result == expected_framework, f"Failed for {control_id}, got {result}"

    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_get_variations_soc2(self, mock_app_class, mock_api_class):
        """Test variation generation for SOC2 controls"""
        matcher = ControlMatcher()

        # Test SOC2 variations
        variations = matcher._get_control_id_variations("CC1.1")

        # Should include case variations and version without dots
        assert "CC1.1" in variations
        assert "cc1.1" in variations
        assert "CC11" in variations
        assert "cc11" in variations

    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_get_variations_cis(self, mock_app_class, mock_api_class):
        """Test variation generation for CIS controls.

        Note: 3-part IDs starting with 1-5 are now identified as CMMC.
        CIS controls with first part >= 6 get normalized and zero-padded variations.
        """
        matcher = ControlMatcher()

        # Test CIS variations (first part >= 6 to avoid CMMC detection)
        variations = matcher._get_control_id_variations("6.1.1")

        # CIS controls get normalized and zero-padded variations
        assert "6.1.1" in variations
        assert "06.01.01" in variations

    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_get_variations_iso(self, mock_app_class, mock_api_class):
        """Test variation generation for ISO controls"""
        matcher = ControlMatcher()

        # Test ISO variations
        variations = matcher._get_control_id_variations("A.5.1")

        # Should include case variations
        assert "A.5.1" in variations
        assert "a.5.1" in variations
        assert "A.5.1" in variations


class TestControlMatcherFindControlInCatalog:
    """Test cases for find_control_in_catalog method"""

    @patch("regscale.integrations.control_matcher.ControlMatcher._get_catalog_controls")
    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_find_control_exact_match(self, mock_app_class, mock_api_class, mock_get_controls):
        """Test finding control with exact match"""
        matcher = ControlMatcher()

        # Create mock controls
        mock_control1 = MagicMock(spec=SecurityControl)
        mock_control1.controlId = "AC-1"
        mock_control1.id = 100

        mock_control2 = MagicMock(spec=SecurityControl)
        mock_control2.controlId = "AC-2"
        mock_control2.id = 101

        mock_get_controls.return_value = [mock_control1, mock_control2]

        result = matcher.find_control_in_catalog("AC-1", 1)

        assert result == mock_control1
        mock_get_controls.assert_called_once_with(1)

    @patch("regscale.integrations.control_matcher.ControlMatcher._get_catalog_controls")
    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_find_control_normalized_match(self, mock_app_class, mock_api_class, mock_get_controls):
        """Test finding control with normalized match when exact match fails"""
        matcher = ControlMatcher()

        # Create mock controls with parentheses notation
        mock_control1 = MagicMock(spec=SecurityControl)
        mock_control1.controlId = "AC-1(1)"
        mock_control1.id = 100

        mock_control2 = MagicMock(spec=SecurityControl)
        mock_control2.controlId = "AC-2"
        mock_control2.id = 101

        mock_get_controls.return_value = [mock_control1, mock_control2]

        # Search using dot notation
        result = matcher.find_control_in_catalog("AC-1.1", 1)

        assert result == mock_control1
        mock_get_controls.assert_called_once_with(1)

    @patch("regscale.integrations.control_matcher.ControlMatcher._get_catalog_controls")
    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_find_control_not_found(self, mock_app_class, mock_api_class, mock_get_controls):
        """Test finding control that doesn't exist returns None"""
        matcher = ControlMatcher()

        mock_control1 = MagicMock(spec=SecurityControl)
        mock_control1.controlId = "AC-1"
        mock_control1.id = 100

        mock_get_controls.return_value = [mock_control1]

        result = matcher.find_control_in_catalog("SI-4", 1)

        assert result is None
        mock_get_controls.assert_called_once_with(1)

    @patch("regscale.integrations.control_matcher.ControlMatcher._get_catalog_controls")
    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_find_control_empty_catalog(self, mock_app_class, mock_api_class, mock_get_controls):
        """Test finding control in empty catalog returns None"""
        matcher = ControlMatcher()
        mock_get_controls.return_value = []

        result = matcher.find_control_in_catalog("AC-1", 1)

        assert result is None
        mock_get_controls.assert_called_once_with(1)


class TestControlMatcherFindControlImplementation:
    """Test cases for find_control_implementation method"""

    @patch("regscale.integrations.control_matcher.ControlMatcher._get_control_implementations")
    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_find_implementation_by_label(self, mock_app_class, mock_api_class, mock_get_impls):
        """Test finding implementation by control label"""
        matcher = ControlMatcher()

        # Create mock implementations
        mock_impl1 = MagicMock(spec=ControlImplementation)
        mock_impl1.id = 200
        mock_impl1.controlID = 100

        mock_impl2 = MagicMock(spec=ControlImplementation)
        mock_impl2.id = 201
        mock_impl2.controlID = 101

        mock_get_impls.return_value = {
            "AC-1": mock_impl1,
            "AC-2": mock_impl2,
        }

        result = matcher.find_control_implementation("AC-1", 50, "securityplans")

        assert result == mock_impl1
        mock_get_impls.assert_called_once_with(50, "securityplans")

    @patch("regscale.integrations.control_matcher.ControlMatcher._get_control_implementations")
    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_find_implementation_case_insensitive(self, mock_app_class, mock_api_class, mock_get_impls):
        """Test finding implementation with case-insensitive matching"""
        matcher = ControlMatcher()

        mock_impl1 = MagicMock(spec=ControlImplementation)
        mock_impl1.id = 200
        mock_impl1.controlID = 100

        mock_get_impls.return_value = {
            "ac-1": mock_impl1,  # lowercase in dict
        }

        result = matcher.find_control_implementation("AC-1", 50)

        assert result == mock_impl1

    @patch("regscale.integrations.control_matcher.ControlMatcher.find_control_in_catalog")
    @patch("regscale.integrations.control_matcher.ControlMatcher._get_control_implementations")
    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_find_implementation_via_catalog(self, mock_app_class, mock_api_class, mock_get_impls, mock_find_control):
        """Test finding implementation via catalog when label match fails"""
        matcher = ControlMatcher()

        # No label match
        mock_impl1 = MagicMock(spec=ControlImplementation)
        mock_impl1.id = 200
        mock_impl1.controlID = 100

        mock_get_impls.return_value = {
            "SI-2": mock_impl1,  # Different control
        }

        # But catalog returns a control
        mock_control = MagicMock(spec=SecurityControl)
        mock_control.id = 100
        mock_control.controlId = "AC-1"
        mock_find_control.return_value = mock_control

        result = matcher.find_control_implementation("AC-1", 50, "securityplans", catalog_id=1)

        assert result == mock_impl1
        mock_find_control.assert_called_once_with("AC-1", 1)

    @patch("regscale.integrations.control_matcher.ControlMatcher._get_control_implementations")
    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_find_implementation_invalid_control_id(self, mock_app_class, mock_api_class, mock_get_impls):
        """Test finding implementation with invalid control ID returns None"""
        matcher = ControlMatcher()
        mock_get_impls.return_value = {}

        with patch("regscale.integrations.control_matcher.logger") as mock_logger:
            result = matcher.find_control_implementation("Invalid", 50)

            assert result is None
            mock_logger.warning.assert_called_once()

    @patch("regscale.integrations.control_matcher.ControlMatcher._get_control_implementations")
    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_find_implementation_not_found(self, mock_app_class, mock_api_class, mock_get_impls):
        """Test finding implementation that doesn't exist returns None"""
        matcher = ControlMatcher()
        mock_get_impls.return_value = {
            "SI-2": MagicMock(spec=ControlImplementation),
        }

        result = matcher.find_control_implementation("AC-1", 50)

        assert result is None


class TestControlMatcherMatchControlsToImplementations:
    """Test cases for match_controls_to_implementations method"""

    @patch("regscale.integrations.control_matcher.ControlMatcher.find_control_implementation")
    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_match_multiple_controls(self, mock_app_class, mock_api_class, mock_find_impl):
        """Test matching multiple control IDs to implementations"""
        matcher = ControlMatcher()

        mock_impl1 = MagicMock(spec=ControlImplementation)
        mock_impl1.id = 200

        mock_impl2 = MagicMock(spec=ControlImplementation)
        mock_impl2.id = 201

        def find_impl_side_effect(control_id, parent_id, parent_module="securityplans", catalog_id=None):
            if control_id == "AC-1":
                return mock_impl1
            elif control_id == "AC-2":
                return mock_impl2
            return None

        mock_find_impl.side_effect = find_impl_side_effect

        control_ids = ["AC-1", "AC-2", "SI-4"]
        result = matcher.match_controls_to_implementations(control_ids, 50)

        assert len(result) == 3
        assert result["AC-1"] == mock_impl1
        assert result["AC-2"] == mock_impl2
        assert result["SI-4"] is None
        assert mock_find_impl.call_count == 3

    @patch("regscale.integrations.control_matcher.ControlMatcher.find_control_implementation")
    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_match_empty_list(self, mock_app_class, mock_api_class, mock_find_impl):
        """Test matching empty list returns empty dict"""
        matcher = ControlMatcher()
        result = matcher.match_controls_to_implementations([], 50)

        assert result == {}
        mock_find_impl.assert_not_called()

    @patch("regscale.integrations.control_matcher.ControlMatcher.find_control_implementation")
    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_match_with_catalog_id(self, mock_app_class, mock_api_class, mock_find_impl):
        """Test matching controls with catalog ID provided"""
        matcher = ControlMatcher()
        mock_impl = MagicMock(spec=ControlImplementation)
        mock_find_impl.return_value = mock_impl

        control_ids = ["AC-1"]
        result = matcher.match_controls_to_implementations(control_ids, 50, "securityplans", catalog_id=1)

        assert result["AC-1"] == mock_impl
        mock_find_impl.assert_called_once_with("AC-1", 50, "securityplans", 1)


class TestControlMatcherGetSecurityPlanControls:
    """Test cases for get_security_plan_controls method"""

    @patch("regscale.integrations.control_matcher.ControlMatcher._get_control_implementations")
    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_get_security_plan_controls(self, mock_app_class, mock_api_class, mock_get_impls):
        """Test getting all control implementations for a security plan"""
        matcher = ControlMatcher()

        mock_impl1 = MagicMock(spec=ControlImplementation)
        mock_impl2 = MagicMock(spec=ControlImplementation)

        expected_dict = {
            "AC-1": mock_impl1,
            "AC-2": mock_impl2,
        }
        mock_get_impls.return_value = expected_dict

        result = matcher.get_security_plan_controls(50)

        assert result == expected_dict
        mock_get_impls.assert_called_once_with(50, "securityplans")


class TestControlMatcherFindControlsByPattern:
    """Test cases for find_controls_by_pattern method"""

    @patch("regscale.integrations.control_matcher.ControlMatcher._get_catalog_controls")
    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_find_by_control_id_pattern(self, mock_app_class, mock_api_class, mock_get_controls):
        """Test finding controls by control ID pattern"""
        matcher = ControlMatcher()

        mock_control1 = MagicMock(spec=SecurityControl)
        mock_control1.controlId = "AC-1"
        mock_control1.title = "Access Control Policy"

        mock_control2 = MagicMock(spec=SecurityControl)
        mock_control2.controlId = "AC-2"
        mock_control2.title = "Account Management"

        mock_control3 = MagicMock(spec=SecurityControl)
        mock_control3.controlId = "SI-2"
        mock_control3.title = "Flaw Remediation"

        mock_get_controls.return_value = [mock_control1, mock_control2, mock_control3]

        result = matcher.find_controls_by_pattern("^AC-", 1)

        assert len(result) == 2
        assert mock_control1 in result
        assert mock_control2 in result
        assert mock_control3 not in result

    @patch("regscale.integrations.control_matcher.ControlMatcher._get_catalog_controls")
    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_find_by_title_pattern(self, mock_app_class, mock_api_class, mock_get_controls):
        """Test finding controls by title pattern"""
        matcher = ControlMatcher()

        mock_control1 = MagicMock(spec=SecurityControl)
        mock_control1.controlId = "AC-1"
        mock_control1.title = "Access Control Policy"

        mock_control2 = MagicMock(spec=SecurityControl)
        mock_control2.controlId = "AC-2"
        mock_control2.title = "Account Management"

        mock_control3 = MagicMock(spec=SecurityControl)
        mock_control3.controlId = "SI-2"
        mock_control3.title = "Access Review"

        mock_get_controls.return_value = [mock_control1, mock_control2, mock_control3]

        result = matcher.find_controls_by_pattern("Access", 1)

        assert len(result) == 2
        assert mock_control1 in result
        assert mock_control3 in result
        assert mock_control2 not in result

    @patch("regscale.integrations.control_matcher.ControlMatcher._get_catalog_controls")
    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_find_by_pattern_case_insensitive(self, mock_app_class, mock_api_class, mock_get_controls):
        """Test finding controls with case-insensitive pattern"""
        matcher = ControlMatcher()

        mock_control1 = MagicMock(spec=SecurityControl)
        mock_control1.controlId = "ac-1"
        mock_control1.title = "access control"

        mock_get_controls.return_value = [mock_control1]

        result = matcher.find_controls_by_pattern("ACCESS", 1)

        assert len(result) == 1
        assert mock_control1 in result

    @patch("regscale.integrations.control_matcher.ControlMatcher._get_catalog_controls")
    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_find_by_pattern_no_matches(self, mock_app_class, mock_api_class, mock_get_controls):
        """Test finding controls with pattern that has no matches"""
        matcher = ControlMatcher()

        mock_control1 = MagicMock(spec=SecurityControl)
        mock_control1.controlId = "AC-1"
        mock_control1.title = "Access Control"

        mock_get_controls.return_value = [mock_control1]

        result = matcher.find_controls_by_pattern("NOMATCH", 1)

        assert len(result) == 0

    @patch("regscale.integrations.control_matcher.ControlMatcher._get_catalog_controls")
    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_find_by_pattern_none_title(self, mock_app_class, mock_api_class, mock_get_controls):
        """Test finding controls when title is None"""
        matcher = ControlMatcher()

        mock_control1 = MagicMock(spec=SecurityControl)
        mock_control1.controlId = "AC-1"
        mock_control1.title = None

        mock_control2 = MagicMock(spec=SecurityControl)
        mock_control2.controlId = "AC-2"
        mock_control2.title = "Account Management"

        mock_get_controls.return_value = [mock_control1, mock_control2]

        result = matcher.find_controls_by_pattern("AC-1", 1)

        assert len(result) == 1
        assert mock_control1 in result


class TestControlMatcherBulkMatchControls:
    """Test cases for bulk_match_controls method"""

    @patch("regscale.integrations.control_matcher.ControlMatcher.find_control_implementation")
    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_bulk_match_controls(self, mock_app_class, mock_api_class, mock_find_impl):
        """Test bulk matching external IDs to control implementations"""
        matcher = ControlMatcher()

        mock_impl1 = MagicMock(spec=ControlImplementation)
        mock_impl1.id = 200

        mock_impl2 = MagicMock(spec=ControlImplementation)
        mock_impl2.id = 201

        def find_impl_side_effect(control_id, parent_id, parent_module="securityplans", catalog_id=None):
            if control_id == "AC-1":
                return mock_impl1
            elif control_id == "AC-2":
                return mock_impl2
            return None

        mock_find_impl.side_effect = find_impl_side_effect

        control_mappings = {
            "ext-001": "AC-1",
            "ext-002": "AC-2",
            "ext-003": "SI-4",
        }

        result = matcher.bulk_match_controls(control_mappings, 50)

        assert len(result) == 3
        assert result["ext-001"] == mock_impl1
        assert result["ext-002"] == mock_impl2
        assert result["ext-003"] is None
        assert mock_find_impl.call_count == 3

    @patch("regscale.integrations.control_matcher.ControlMatcher.find_control_implementation")
    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_bulk_match_empty_dict(self, mock_app_class, mock_api_class, mock_find_impl):
        """Test bulk matching with empty dict returns empty dict"""
        matcher = ControlMatcher()
        result = matcher.bulk_match_controls({}, 50)

        assert result == {}
        mock_find_impl.assert_not_called()

    @patch("regscale.integrations.control_matcher.ControlMatcher.find_control_implementation")
    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_bulk_match_with_catalog(self, mock_app_class, mock_api_class, mock_find_impl):
        """Test bulk matching with catalog ID"""
        matcher = ControlMatcher()
        mock_impl = MagicMock(spec=ControlImplementation)
        mock_find_impl.return_value = mock_impl

        control_mappings = {"ext-001": "AC-1"}
        result = matcher.bulk_match_controls(control_mappings, 50, "securityplans", catalog_id=1)

        assert result["ext-001"] == mock_impl
        mock_find_impl.assert_called_once_with("AC-1", 50, "securityplans", 1)


class TestControlMatcherGetCatalogControls:
    """Test cases for _get_catalog_controls method"""

    @patch("regscale.models.regscale_models.security_control.SecurityControl.get_list_by_catalog")
    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_get_catalog_controls_first_call(self, mock_app_class, mock_api_class, mock_get_list):
        """Test getting catalog controls on first call (not cached)"""
        matcher = ControlMatcher()

        mock_control1 = MagicMock(spec=SecurityControl)
        mock_control2 = MagicMock(spec=SecurityControl)
        mock_get_list.return_value = [mock_control1, mock_control2]

        result = matcher._get_catalog_controls(1)

        assert len(result) == 2
        assert mock_control1 in result
        assert mock_control2 in result
        mock_get_list.assert_called_once_with(1)
        assert 1 in matcher._catalog_cache

    @patch("regscale.models.regscale_models.security_control.SecurityControl.get_list_by_catalog")
    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_get_catalog_controls_cached(self, mock_app_class, mock_api_class, mock_get_list):
        """Test getting catalog controls from cache on subsequent calls"""
        matcher = ControlMatcher()

        mock_control1 = MagicMock(spec=SecurityControl)
        mock_control2 = MagicMock(spec=SecurityControl)
        cached_controls = [mock_control1, mock_control2]

        # Pre-populate cache
        matcher._catalog_cache[1] = cached_controls

        result = matcher._get_catalog_controls(1)

        assert result == cached_controls
        mock_get_list.assert_not_called()

    @patch("regscale.models.regscale_models.security_control.SecurityControl.get_list_by_catalog")
    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_get_catalog_controls_error(self, mock_app_class, mock_api_class, mock_get_list):
        """Test getting catalog controls handles exception"""
        matcher = ControlMatcher()
        mock_get_list.side_effect = Exception("API Error")

        with patch("regscale.integrations.control_matcher.logger") as mock_logger:
            result = matcher._get_catalog_controls(1)

            assert result == []
            mock_logger.error.assert_called_once()
            assert 1 not in matcher._catalog_cache


class TestControlMatcherGetControlImplementations:
    """Test cases for _get_control_implementations method"""

    @patch("regscale.models.regscale_models.control_implementation.ControlImplementation.get_object")
    @patch(
        "regscale.models.regscale_models.control_implementation.ControlImplementation.get_control_label_map_by_parent"
    )
    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_get_control_implementations_first_call(
        self, mock_app_class, mock_api_class, mock_get_label_map, mock_get_object
    ):
        """Test getting control implementations on first call (not cached)"""
        matcher = ControlMatcher()

        mock_impl1 = MagicMock(spec=ControlImplementation)
        mock_impl1.id = 200

        mock_impl2 = MagicMock(spec=ControlImplementation)
        mock_impl2.id = 201

        mock_get_label_map.return_value = {
            "AC-1": 200,
            "AC-2": 201,
        }

        def get_object_side_effect(impl_id):
            if impl_id == 200:
                return mock_impl1
            elif impl_id == 201:
                return mock_impl2
            return None

        mock_get_object.side_effect = get_object_side_effect

        result = matcher._get_control_implementations(50, "securityplans")

        assert len(result) == 2
        assert result["AC-1"] == mock_impl1
        assert result["AC-2"] == mock_impl2
        mock_get_label_map.assert_called_once_with(50, "securityplans")
        assert (50, "securityplans") in matcher._control_impl_cache

    @patch(
        "regscale.models.regscale_models.control_implementation.ControlImplementation.get_control_label_map_by_parent"
    )
    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_get_control_implementations_cached(self, mock_app_class, mock_api_class, mock_get_label_map):
        """Test getting control implementations from cache"""
        matcher = ControlMatcher()

        mock_impl = MagicMock(spec=ControlImplementation)
        cached_impls = {"AC-1": mock_impl}

        # Pre-populate cache
        matcher._control_impl_cache[(50, "securityplans")] = cached_impls

        result = matcher._get_control_implementations(50, "securityplans")

        assert result == cached_impls
        mock_get_label_map.assert_not_called()

    @patch("regscale.models.regscale_models.control_implementation.ControlImplementation.get_object")
    @patch(
        "regscale.models.regscale_models.control_implementation.ControlImplementation.get_control_label_map_by_parent"
    )
    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_get_control_implementations_with_none(
        self, mock_app_class, mock_api_class, mock_get_label_map, mock_get_object
    ):
        """Test getting control implementations when some objects return None"""
        matcher = ControlMatcher()

        mock_impl1 = MagicMock(spec=ControlImplementation)
        mock_impl1.id = 200

        mock_get_label_map.return_value = {
            "AC-1": 200,
            "AC-2": 201,  # This will return None
        }

        def get_object_side_effect(impl_id):
            if impl_id == 200:
                return mock_impl1
            return None

        mock_get_object.side_effect = get_object_side_effect

        result = matcher._get_control_implementations(50, "securityplans")

        # Should only include the valid implementation
        assert len(result) == 1
        assert result["AC-1"] == mock_impl1
        assert "AC-2" not in result

    @patch(
        "regscale.models.regscale_models.control_implementation.ControlImplementation.get_control_label_map_by_parent"
    )
    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_get_control_implementations_error(self, mock_app_class, mock_api_class, mock_get_label_map):
        """Test getting control implementations handles exception"""
        matcher = ControlMatcher()
        mock_get_label_map.side_effect = Exception("API Error")

        with patch("regscale.integrations.control_matcher.logger") as mock_logger:
            result = matcher._get_control_implementations(50, "securityplans")

            assert result == {}
            mock_logger.error.assert_called_once()
            assert (50, "securityplans") not in matcher._control_impl_cache


class TestControlMatcherClearCache:
    """Test cases for clear_cache method"""

    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_clear_cache_empty(self, mock_app_class, mock_api_class):
        """Test clearing cache when already empty"""
        matcher = ControlMatcher()

        with patch("regscale.integrations.control_matcher.logger") as mock_logger:
            matcher.clear_cache()

            assert matcher._catalog_cache == {}
            assert matcher._control_impl_cache == {}
            mock_logger.info.assert_called_once_with("Cleared control matcher cache")

    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_clear_cache_with_data(self, mock_app_class, mock_api_class):
        """Test clearing cache with data"""
        matcher = ControlMatcher()

        # Add data to caches
        matcher._catalog_cache[1] = [MagicMock(spec=SecurityControl)]
        matcher._control_impl_cache[(50, "securityplans")] = {"AC-1": MagicMock(spec=ControlImplementation)}

        with patch("regscale.integrations.control_matcher.logger") as mock_logger:
            matcher.clear_cache()

            assert matcher._catalog_cache == {}
            assert matcher._control_impl_cache == {}
            mock_logger.info.assert_called_once_with("Cleared control matcher cache")


class TestControlMatcherEdgeCases:
    """Test cases for edge cases and error scenarios"""

    @patch("regscale.integrations.control_matcher.ControlMatcher._get_catalog_controls")
    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_find_control_with_special_characters(self, mock_app_class, mock_api_class, mock_get_controls):
        """Test finding control with special characters in ID"""
        matcher = ControlMatcher()

        mock_control = MagicMock(spec=SecurityControl)
        mock_control.controlId = "AC-1(1)"
        mock_get_controls.return_value = [mock_control]

        # Test with different variations
        result1 = matcher.find_control_in_catalog("AC-1(1)", 1)
        result2 = matcher.find_control_in_catalog("AC-1.1", 1)

        assert result1 == mock_control
        assert result2 == mock_control

    @patch("regscale.integrations.control_matcher.ControlMatcher.find_control_implementation")
    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_match_controls_with_duplicates(self, mock_app_class, mock_api_class, mock_find_impl):
        """Test matching controls when list contains duplicates"""
        matcher = ControlMatcher()

        mock_impl1 = MagicMock(spec=ControlImplementation)
        mock_impl2 = MagicMock(spec=ControlImplementation)

        def find_impl_side_effect(control_id, parent_id, parent_module="securityplans", catalog_id=None):
            if control_id == "AC-1":
                return mock_impl1
            elif control_id == "AC-2":
                return mock_impl2
            return None

        mock_find_impl.side_effect = find_impl_side_effect

        control_ids = ["AC-1", "AC-1", "AC-2"]
        result = matcher.match_controls_to_implementations(control_ids, 50)

        # Result is a dict, so duplicates are collapsed - should have 2 unique keys
        assert len(result) == 2
        assert result["AC-1"] == mock_impl1
        assert result["AC-2"] == mock_impl2
        # Should still call find_impl for each entry in the list, including duplicates
        assert mock_find_impl.call_count == 3

    @patch("regscale.integrations.control_matcher.ControlMatcher._get_catalog_controls")
    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_find_by_pattern_with_empty_string(self, mock_app_class, mock_api_class, mock_get_controls):
        """Test finding controls with empty string pattern"""
        matcher = ControlMatcher()

        mock_control = MagicMock(spec=SecurityControl)
        mock_control.controlId = "AC-1"
        mock_control.title = "Access Control"
        mock_get_controls.return_value = [mock_control]

        result = matcher.find_controls_by_pattern("", 1)

        # Empty pattern should match everything
        assert len(result) == 1
        assert mock_control in result

    @patch("regscale.integrations.control_matcher.ControlMatcher._get_control_implementations")
    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_find_implementation_different_parent_modules(self, mock_app_class, mock_api_class, mock_get_impls):
        """Test finding implementations with different parent modules"""
        matcher = ControlMatcher()

        mock_impl1 = MagicMock(spec=ControlImplementation)
        mock_impl2 = MagicMock(spec=ControlImplementation)

        def get_impls_side_effect(parent_id, parent_module):
            if parent_module == "securityplans":
                return {"AC-1": mock_impl1}
            elif parent_module == "assessments":
                return {"AC-1": mock_impl2}
            return {}

        mock_get_impls.side_effect = get_impls_side_effect

        result1 = matcher.find_control_implementation("AC-1", 50, "securityplans")
        result2 = matcher.find_control_implementation("AC-1", 51, "assessments")

        assert result1 == mock_impl1
        assert result2 == mock_impl2


class TestControlMatcherLeadingZeros:
    """Test cases for control IDs with leading zeros"""

    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_normalize_control_id_with_leading_zeros(self, mock_app_class, mock_api_class):
        """Test normalizing control IDs with leading zeros"""
        matcher = ControlMatcher()

        test_cases = [
            ("AC-01", "AC-1"),
            ("AC-17", "AC-17"),
            ("AC-01.02", "AC-1.2"),
            ("AC-17.02", "AC-17.2"),
            ("AC-1.1", "AC-1.1"),
        ]

        for input_id, expected in test_cases:
            result = matcher._normalize_control_id(input_id)
            assert result == expected, f"Failed for input {input_id}"

    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_get_control_id_variations_simple(self, mock_app_class, mock_api_class):
        """Test generating variations for simple control IDs"""
        matcher = ControlMatcher()

        result = matcher._get_control_id_variations("AC-1")
        expected = {"AC-1", "AC-01"}
        assert result == expected

    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_get_control_id_variations_with_enhancement(self, mock_app_class, mock_api_class):
        """Test generating variations for control IDs with enhancements"""
        matcher = ControlMatcher()

        result = matcher._get_control_id_variations("AC-17.2")
        expected = {
            "AC-17.2",
            "AC-17.02",
            "AC-17(2)",
            "AC-17(02)",
        }
        assert result == expected

    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_get_control_id_variations_with_leading_zeros_input(self, mock_app_class, mock_api_class):
        """Test generating variations when input has leading zeros"""
        matcher = ControlMatcher()

        result = matcher._get_control_id_variations("AC-01")
        expected = {"AC-1", "AC-01"}
        assert result == expected

    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_get_control_id_variations_with_parentheses_input(self, mock_app_class, mock_api_class):
        """Test generating variations when input has parentheses"""
        matcher = ControlMatcher()

        result = matcher._get_control_id_variations("AC-17(02)")
        expected = {
            "AC-17.2",
            "AC-17.02",
            "AC-17(2)",
            "AC-17(02)",
        }
        assert result == expected

    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_get_control_id_variations_with_letter_enhancement(self, mock_app_class, mock_api_class):
        """Test generating variations for control IDs with letter-based enhancements"""
        matcher = ControlMatcher()

        result = matcher._get_control_id_variations("AC-1.a")
        expected = {
            "AC-1.A",
            "AC-01.A",
            "AC-1(A)",
            "AC-01(A)",
        }
        assert result == expected

    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_get_control_id_variations_invalid_input(self, mock_app_class, mock_api_class):
        """Test generating variations for invalid control ID returns empty set"""
        matcher = ControlMatcher()

        result = matcher._get_control_id_variations("Invalid")
        assert result == set()

    @patch("regscale.integrations.control_matcher.ControlMatcher._get_catalog_controls")
    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_find_control_in_catalog_with_leading_zeros(self, mock_app_class, mock_api_class, mock_get_controls):
        """Test finding controls with leading zeros in catalog"""
        matcher = ControlMatcher()

        # Catalog has control with leading zeros
        mock_control = MagicMock(spec=SecurityControl)
        mock_control.controlId = "AC-01"
        mock_control.id = 100

        mock_get_controls.return_value = [mock_control]

        # Search without leading zero should find it
        result = matcher.find_control_in_catalog("AC-1", 1)
        assert result == mock_control

    @patch("regscale.integrations.control_matcher.ControlMatcher._get_catalog_controls")
    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_find_control_in_catalog_search_with_leading_zeros(self, mock_app_class, mock_api_class, mock_get_controls):
        """Test finding controls when search ID has leading zeros"""
        matcher = ControlMatcher()

        # Catalog has control without leading zeros
        mock_control = MagicMock(spec=SecurityControl)
        mock_control.controlId = "AC-1"
        mock_control.id = 100

        mock_get_controls.return_value = [mock_control]

        # Search with leading zero should find it
        result = matcher.find_control_in_catalog("AC-01", 1)
        assert result == mock_control

    @patch("regscale.integrations.control_matcher.ControlMatcher._get_catalog_controls")
    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_find_control_with_leading_zeros_enhancement(self, mock_app_class, mock_api_class, mock_get_controls):
        """Test finding controls with leading zeros in enhancement numbers"""
        matcher = ControlMatcher()

        # Catalog has control with leading zeros in enhancement
        mock_control = MagicMock(spec=SecurityControl)
        mock_control.controlId = "AC-17(02)"
        mock_control.id = 100

        mock_get_controls.return_value = [mock_control]

        # Search with different formats should all find it
        result1 = matcher.find_control_in_catalog("AC-17.2", 1)
        result2 = matcher.find_control_in_catalog("AC-17(2)", 1)
        result3 = matcher.find_control_in_catalog("AC-17.02", 1)

        assert result1 == mock_control
        assert result2 == mock_control
        assert result3 == mock_control

    @patch("regscale.integrations.control_matcher.ControlMatcher._get_control_implementations")
    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_find_implementation_with_leading_zeros(self, mock_app_class, mock_api_class, mock_get_impls):
        """Test finding implementation when control IDs have leading zeros"""
        matcher = ControlMatcher()

        mock_impl = MagicMock(spec=ControlImplementation)
        mock_impl.id = 200
        mock_impl.controlID = 100

        # Implementation key has leading zero
        mock_get_impls.return_value = {
            "AC-01": mock_impl,
        }

        # Search without leading zero should find it
        result = matcher.find_control_implementation("AC-1", 50)
        assert result == mock_impl

    @patch("regscale.integrations.control_matcher.ControlMatcher._get_control_implementations")
    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_find_implementation_search_with_leading_zeros(self, mock_app_class, mock_api_class, mock_get_impls):
        """Test finding implementation when search ID has leading zeros"""
        matcher = ControlMatcher()

        mock_impl = MagicMock(spec=ControlImplementation)
        mock_impl.id = 200
        mock_impl.controlID = 100

        # Implementation key has no leading zero
        mock_get_impls.return_value = {
            "AC-1": mock_impl,
        }

        # Search with leading zero should find it
        result = matcher.find_control_implementation("AC-01", 50)
        assert result == mock_impl

    @patch("regscale.integrations.control_matcher.ControlMatcher._get_control_implementations")
    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_find_implementation_with_leading_zeros_complex(self, mock_app_class, mock_api_class, mock_get_impls):
        """Test finding implementation with complex leading zero scenarios"""
        matcher = ControlMatcher()

        mock_impl = MagicMock(spec=ControlImplementation)
        mock_impl.id = 200

        # Implementation key has leading zeros in enhancement
        mock_get_impls.return_value = {
            "AC-17(02)": mock_impl,
        }

        # Search with different formats should find it
        result1 = matcher.find_control_implementation("AC-17.2", 50)
        result2 = matcher.find_control_implementation("AC-17(2)", 50)
        result3 = matcher.find_control_implementation("AC-17.02", 50)

        assert result1 == mock_impl
        assert result2 == mock_impl
        assert result3 == mock_impl


class TestControlMatcherIntegrationScenarios:
    """Integration test scenarios for complex workflows"""

    @patch("regscale.models.regscale_models.control_implementation.ControlImplementation.get_object")
    @patch(
        "regscale.models.regscale_models.control_implementation.ControlImplementation.get_control_label_map_by_parent"
    )
    @patch("regscale.models.regscale_models.security_control.SecurityControl.get_list_by_catalog")
    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_full_workflow_with_caching(
        self, mock_app_class, mock_api_class, mock_get_catalog, mock_get_label_map, mock_get_object
    ):
        """Test full workflow with multiple operations and caching"""
        matcher = ControlMatcher()

        # Setup catalog controls
        mock_control1 = MagicMock(spec=SecurityControl)
        mock_control1.controlId = "AC-1"
        mock_control1.id = 100
        mock_control1.title = "Access Control Policy"

        mock_control2 = MagicMock(spec=SecurityControl)
        mock_control2.controlId = "AC-2"
        mock_control2.id = 101
        mock_control2.title = "Account Management"

        mock_get_catalog.return_value = [mock_control1, mock_control2]

        # Setup implementations
        mock_impl1 = MagicMock(spec=ControlImplementation)
        mock_impl1.id = 200
        mock_impl1.controlID = 100

        mock_get_label_map.return_value = {"AC-1": 200}
        mock_get_object.return_value = mock_impl1

        # First operation: find control in catalog
        control = matcher.find_control_in_catalog("AC-1", 1)
        assert control == mock_control1
        assert mock_get_catalog.call_count == 1

        # Second operation: find same control (should use cache)
        control2 = matcher.find_control_in_catalog("AC-2", 1)
        assert control2 == mock_control2
        assert mock_get_catalog.call_count == 1  # Should not increase

        # Third operation: find implementation
        impl = matcher.find_control_implementation("AC-1", 50)
        assert impl == mock_impl1
        assert mock_get_label_map.call_count == 1

        # Fourth operation: find same implementation (should use cache)
        impl2 = matcher.find_control_implementation("AC-1", 50)
        assert impl2 == mock_impl1
        assert mock_get_label_map.call_count == 1  # Should not increase

        # Clear cache
        matcher.clear_cache()

        # Fifth operation: after cache clear, should fetch again
        control3 = matcher.find_control_in_catalog("AC-1", 1)
        assert control3 == mock_control1
        assert mock_get_catalog.call_count == 2  # Should increase now

    @patch("regscale.integrations.control_matcher.ControlMatcher.find_control_implementation")
    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_bulk_operations_with_mixed_results(self, mock_app_class, mock_api_class, mock_find_impl):
        """Test bulk operations with some successes and some failures"""
        matcher = ControlMatcher()

        mock_impl1 = MagicMock(spec=ControlImplementation)
        mock_impl2 = MagicMock(spec=ControlImplementation)

        def find_impl_side_effect(control_id, parent_id, parent_module="securityplans", catalog_id=None):
            impl_map = {
                "AC-1": mock_impl1,
                "AC-2": mock_impl2,
            }
            return impl_map.get(control_id)

        mock_find_impl.side_effect = find_impl_side_effect

        # Bulk match with mixed results
        mappings = {
            "finding-001": "AC-1",  # Will find
            "finding-002": "AC-2",  # Will find
            "finding-003": "SI-4",  # Won't find
            "finding-004": "CM-6",  # Won't find
        }

        result = matcher.bulk_match_controls(mappings, 50)

        assert result["finding-001"] == mock_impl1
        assert result["finding-002"] == mock_impl2
        assert result["finding-003"] is None
        assert result["finding-004"] is None
        assert len(result) == 4

    @patch("regscale.models.regscale_models.control_implementation.ControlImplementation.get_object")
    @patch(
        "regscale.models.regscale_models.control_implementation.ControlImplementation.get_control_label_map_by_parent"
    )
    @patch("regscale.models.regscale_models.security_control.SecurityControl.get_list_by_catalog")
    @patch("regscale.integrations.control_matcher.Api")
    @patch("regscale.integrations.control_matcher.Application")
    def test_workflow_with_leading_zeros_catalog(
        self, mock_app_class, mock_api_class, mock_get_catalog, mock_get_label_map, mock_get_object
    ):
        """Test workflow when catalog has control IDs with leading zeros"""
        matcher = ControlMatcher()

        # Catalog has controls with leading zeros
        mock_control1 = MagicMock(spec=SecurityControl)
        mock_control1.controlId = "AC-01"
        mock_control1.id = 100

        mock_control2 = MagicMock(spec=SecurityControl)
        mock_control2.controlId = "AC-17(02)"
        mock_control2.id = 101

        mock_get_catalog.return_value = [mock_control1, mock_control2]

        # Implementations have standard format
        mock_impl1 = MagicMock(spec=ControlImplementation)
        mock_impl1.id = 200
        mock_impl1.controlID = 100

        mock_impl2 = MagicMock(spec=ControlImplementation)
        mock_impl2.id = 201
        mock_impl2.controlID = 101

        mock_get_label_map.return_value = {
            "AC-1": 200,
            "AC-17.2": 201,
        }

        def get_object_side_effect(impl_id):
            if impl_id == 200:
                return mock_impl1
            elif impl_id == 201:
                return mock_impl2
            return None

        mock_get_object.side_effect = get_object_side_effect

        # Search with standard format should find controls with leading zeros
        control1 = matcher.find_control_in_catalog("AC-1", 1)
        assert control1 == mock_control1

        control2 = matcher.find_control_in_catalog("AC-17.2", 1)
        assert control2 == mock_control2

        # Find implementations should work with either format
        impl1 = matcher.find_control_implementation("AC-01", 50)
        assert impl1 == mock_impl1

        impl2 = matcher.find_control_implementation("AC-17(02)", 50)
        assert impl2 == mock_impl2
