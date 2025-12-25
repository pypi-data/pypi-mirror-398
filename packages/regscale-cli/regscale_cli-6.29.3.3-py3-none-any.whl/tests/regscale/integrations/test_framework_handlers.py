#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for Framework Handlers."""

import pytest

from regscale.integrations.framework_handlers.base import FrameworkHandler
from regscale.integrations.framework_handlers.cis_handler import CISHandler
from regscale.integrations.framework_handlers.cmmc_handler import CMMCHandler
from regscale.integrations.framework_handlers.iso_handler import ISOHandler
from regscale.integrations.framework_handlers.nist_handler import NISTHandler
from regscale.integrations.framework_handlers.registry import FrameworkHandlerRegistry, get_registry
from regscale.integrations.framework_handlers.soc2_handler import SOC2Handler


class TestCMMCHandler:
    """Tests for CMMC Handler."""

    @pytest.fixture
    def handler(self):
        """Create CMMC handler instance."""
        return CMMCHandler()

    def test_framework_name(self, handler):
        """Test framework name is set correctly."""
        assert handler.framework_name == "CMMC"

    def test_detection_priority(self, handler):
        """Test CMMC has higher priority than CIS."""
        assert handler.detection_priority == 5
        assert handler.detection_priority < CISHandler().detection_priority

    @pytest.mark.parametrize(
        "control_id,expected",
        [
            ("3.1.1", True),
            ("3.01.01", True),
            ("1.1.1", True),
            ("5.1.1", True),
            ("AC.1.001", True),
            ("SC.2.178", True),
            ("6.1.1", False),  # Not CMMC - too high first number
            ("AC-1", False),  # NIST format
            ("CC1.1", False),  # SOC2 format
        ],
    )
    def test_matches(self, handler, control_id, expected):
        """Test CMMC pattern matching."""
        assert handler.matches(control_id) == expected

    @pytest.mark.parametrize(
        "control_id,expected",
        [
            ("3.1.1", "3.1.1"),
            ("3.01.01", "3.1.1"),
            ("AC.1.001", "AC.1.1"),
            ("ac.1.001", "AC.1.1"),
            ("AC.01.001", "AC.1.1"),
        ],
    )
    def test_parse(self, handler, control_id, expected):
        """Test CMMC control parsing.

        Note: CMMC levels are 1-5 (single digit), so leading zeros on
        the level (e.g., '03.1.1') are not standard CMMC format.
        """
        assert handler.parse(control_id) == expected

    def test_get_variations_numeric(self, handler):
        """Test CMMC variation generation for numeric format.

        Note: CMMC levels are 1-5 (single digit), so variations don't
        include leading zeros on the level (e.g., no '03.1.1').
        """
        variations = handler.get_variations("3.1.1")
        assert "3.1.1" in variations
        assert "3.01.01" in variations
        assert "3.1.01" in variations
        assert "3.01.1" in variations
        # Level is always single digit 1-5, so no '03.1.1'
        # Should have multiple variations for domain and practice
        assert len(variations) > 1

    def test_get_variations_domain(self, handler):
        """Test CMMC variation generation for domain format."""
        variations = handler.get_variations("AC.1.001")
        assert "AC.1.1" in variations
        assert "AC.1.01" in variations
        assert "AC.01.1" in variations
        assert "AC.01.01" in variations

    def test_normalize(self, handler):
        """Test CMMC normalization."""
        assert handler.normalize("3.01.01") == "3.1.1"
        assert handler.normalize("AC.01.001") == "AC.1.1"


class TestCISHandler:
    """Tests for CIS Handler."""

    @pytest.fixture
    def handler(self):
        """Create CIS handler instance."""
        return CISHandler()

    def test_framework_name(self, handler):
        """Test framework name is set correctly."""
        assert handler.framework_name == "CIS"

    def test_detection_priority(self, handler):
        """Test CIS has lower priority than CMMC."""
        assert handler.detection_priority == 15
        assert handler.detection_priority > CMMCHandler().detection_priority

    @pytest.mark.parametrize(
        "control_id,expected",
        [
            ("6.1.1", True),
            ("10.1.1", True),
            ("1.1", True),
            ("1.1.1.1", True),
            ("3.1.1", False),  # CMMC territory - 3 parts starting with 1-5
            ("1.1.1", False),  # CMMC territory
            ("5.1.1", False),  # CMMC territory
            ("AC-1", False),  # NIST format
        ],
    )
    def test_matches(self, handler, control_id, expected):
        """Test CIS pattern matching avoids CMMC territory."""
        assert handler.matches(control_id) == expected

    def test_get_variations(self, handler):
        """Test CIS variation generation."""
        variations = handler.get_variations("6.1.1")
        assert "6.1.1" in variations


class TestNISTHandler:
    """Tests for NIST Handler."""

    @pytest.fixture
    def handler(self):
        """Create NIST handler instance."""
        return NISTHandler()

    def test_framework_name(self, handler):
        """Test framework name is set correctly."""
        assert handler.framework_name == "NIST"

    @pytest.mark.parametrize(
        "control_id,expected",
        [
            ("AC-1", True),
            ("AC-01", True),
            ("AC-1(1)", True),
            ("AC-1.1", True),
            ("SI-2", True),
            ("PTA-1", True),  # Three-letter family
            ("3.1.1", False),  # CIS/CMMC format
            ("CC1.1", False),  # SOC2 format
        ],
    )
    def test_matches(self, handler, control_id, expected):
        """Test NIST pattern matching."""
        assert handler.matches(control_id) == expected

    @pytest.mark.parametrize(
        "control_id,expected",
        [
            ("AC-1", "AC-1"),
            ("AC-01", "AC-1"),
            ("AC-1(1)", "AC-1.1"),
            ("AC-01(02)", "AC-1.2"),
            ("AC-1 (1)", "AC-1.1"),
            ("AC-1.a", "AC-1.A"),
        ],
    )
    def test_parse(self, handler, control_id, expected):
        """Test NIST control parsing."""
        assert handler.parse(control_id) == expected

    def test_get_variations_simple(self, handler):
        """Test NIST variation generation for simple controls."""
        variations = handler.get_variations("AC-1")
        assert "AC-1" in variations
        assert "AC-01" in variations

    def test_get_variations_enhancement(self, handler):
        """Test NIST variation generation with enhancements."""
        variations = handler.get_variations("AC-1(1)")
        assert "AC-1.1" in variations
        assert "AC-01.01" in variations
        assert "AC-1(1)" in variations
        assert "AC-01(01)" in variations


class TestISOHandler:
    """Tests for ISO Handler."""

    @pytest.fixture
    def handler(self):
        """Create ISO handler instance."""
        return ISOHandler()

    def test_framework_name(self, handler):
        """Test framework name is set correctly."""
        assert handler.framework_name == "ISO"

    @pytest.mark.parametrize(
        "control_id,expected",
        [
            ("A.5.1", True),
            ("A.5.1.1", True),
            ("A.12.3.1", True),
            ("a.5.1", True),
            ("AC-1", False),  # NIST format
            ("3.1.1", False),  # CIS/CMMC format
        ],
    )
    def test_matches(self, handler, control_id, expected):
        """Test ISO pattern matching."""
        assert handler.matches(control_id) == expected

    def test_get_variations(self, handler):
        """Test ISO variation generation."""
        variations = handler.get_variations("A.5.1")
        assert "A.5.1" in variations
        assert "a.5.1" in variations


class TestSOC2Handler:
    """Tests for SOC2 Handler."""

    @pytest.fixture
    def handler(self):
        """Create SOC2 handler instance."""
        return SOC2Handler()

    def test_framework_name(self, handler):
        """Test framework name is set correctly."""
        assert handler.framework_name == "SOC2"

    @pytest.mark.parametrize(
        "control_id,expected",
        [
            ("CC1.1", True),
            ("PI1.5", True),
            ("A1.2", True),
            ("C1.1", True),
            ("P1.1", True),
            ("AC-1", False),  # NIST format
            ("3.1.1", False),  # CIS/CMMC format
            ("X1.1", False),  # Invalid prefix
        ],
    )
    def test_matches(self, handler, control_id, expected):
        """Test SOC2 pattern matching."""
        assert handler.matches(control_id) == expected

    def test_get_variations(self, handler):
        """Test SOC2 variation generation."""
        variations = handler.get_variations("CC1.1")
        assert "CC1.1" in variations
        assert "cc1.1" in variations
        assert "CC11" in variations  # Without dot


class TestFrameworkHandlerRegistry:
    """Tests for Framework Handler Registry."""

    @pytest.fixture
    def registry(self):
        """Create fresh registry instance."""
        return FrameworkHandlerRegistry()

    def test_default_handlers_registered(self, registry):
        """Test all default handlers are registered."""
        handlers = registry.get_all_handlers()
        framework_names = [h.framework_name for h in handlers]

        assert "CMMC" in framework_names
        assert "NIST" in framework_names
        assert "ISO" in framework_names
        assert "SOC2" in framework_names
        assert "CIS" in framework_names

    def test_priority_order(self, registry):
        """Test handlers are ordered by priority."""
        handlers = registry.get_all_handlers()
        priorities = [h.detection_priority for h in handlers]

        # Should be in ascending order (lowest priority number = highest priority)
        assert priorities == sorted(priorities)

    def test_cmmc_before_cis(self, registry):
        """Test CMMC handler comes before CIS handler."""
        handlers = registry.get_all_handlers()
        framework_names = [h.framework_name for h in handlers]

        cmmc_idx = framework_names.index("CMMC")
        cis_idx = framework_names.index("CIS")

        assert cmmc_idx < cis_idx

    @pytest.mark.parametrize(
        "control_id,expected_framework",
        [
            ("3.1.1", "CMMC"),
            ("AC.1.001", "CMMC"),
            ("AC-1", "NIST"),
            ("AC-1(1)", "NIST"),
            ("A.5.1", "ISO"),
            ("CC1.1", "SOC2"),
            ("6.1.1", "CIS"),
            ("10.1.1", "CIS"),
        ],
    )
    def test_detect_handler(self, registry, control_id, expected_framework):
        """Test handler detection for various control formats."""
        handler = registry.detect_handler(control_id)
        assert handler is not None
        assert handler.framework_name == expected_framework

    def test_detect_handler_cmmc_not_cis(self, registry):
        """Test that CMMC-style controls are detected as CMMC, not CIS."""
        # These are CMMC controls that could be confused with CIS
        cmmc_controls = ["3.1.1", "1.1.1", "5.1.1", "2.3.4"]

        for control_id in cmmc_controls:
            handler = registry.detect_handler(control_id)
            assert handler is not None, f"No handler for {control_id}"
            assert handler.framework_name == "CMMC", f"{control_id} detected as {handler.framework_name}, not CMMC"

    def test_get_handler_by_name(self, registry):
        """Test getting handler by framework name."""
        handler = registry.get_handler("NIST")
        assert handler is not None
        assert handler.framework_name == "NIST"

    def test_get_handler_not_found(self, registry):
        """Test getting non-existent handler."""
        handler = registry.get_handler("NONEXISTENT")
        assert handler is None


class TestGlobalRegistry:
    """Tests for global registry singleton."""

    def test_get_registry_returns_singleton(self):
        """Test get_registry returns same instance."""
        reg1 = get_registry()
        reg2 = get_registry()
        assert reg1 is reg2

    def test_registry_has_handlers(self):
        """Test global registry has handlers."""
        registry = get_registry()
        handlers = registry.get_all_handlers()
        assert len(handlers) >= 5  # At least 5 default handlers


class TestFrameworkHandlerIntegration:
    """Integration tests for framework handlers with ControlMatcher."""

    def test_cmmc_variations_prevent_duplicates(self):
        """Test that CMMC handler generates enough variations to match existing controls.

        Note: CMMC levels are 1-5 (single digit), so '03.1.1' is not a valid
        CMMC format and is excluded from test cases.
        """
        handler = CMMCHandler()

        # Simulate different formats that might exist in the database
        # (excluding leading zeros on level since CMMC levels are 1-5)
        db_formats = ["3.1.1", "3.01.01", "3.1.01", "3.01.1"]
        input_format = "3.1.1"

        input_variations = handler.get_variations(input_format)

        # Each database format should be matched by input variations
        for db_format in db_formats:
            db_variations = handler.get_variations(db_format)
            intersection = input_variations & db_variations
            assert intersection, f"No match between input {input_format} and db {db_format}"

    def test_domain_format_variations(self):
        """Test domain format CMMC controls generate proper variations."""
        handler = CMMCHandler()

        input_variations = handler.get_variations("AC.1.001")
        db_variations = handler.get_variations("AC.1.1")

        intersection = input_variations & db_variations
        assert intersection, "Domain format variations should overlap"
