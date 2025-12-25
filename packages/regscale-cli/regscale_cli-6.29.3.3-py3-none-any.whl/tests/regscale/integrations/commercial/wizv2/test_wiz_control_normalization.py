#!/usr/bin/env python3
"""Test Wiz control ID normalization after fix."""

import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WizComplianceReportItemTest:
    """Test version of WizComplianceReportItem with normalization methods."""

    def _normalize_base_control(self, base_control: str) -> str:
        """Normalize leading zeros in base control number (e.g., AC-01 -> AC-1)."""
        if "-" in base_control:
            prefix, number = base_control.split("-", 1)
            try:
                normalized_number = str(int(number))
                return f"{prefix.upper()}-{normalized_number}"
            except ValueError:
                return base_control.upper()
        else:
            return base_control.upper()

    def _format_control_id(self, base_control: str, enhancement: str) -> str:
        """Format control ID with optional enhancement."""
        if enhancement:
            # Normalize enhancement number to remove leading zeros
            try:
                normalized_enhancement = str(int(enhancement))
            except ValueError:
                normalized_enhancement = enhancement
            return f"{base_control}({normalized_enhancement})"
        else:
            return base_control

    def get_all_control_ids(self, compliance_check_name: str) -> list:
        """Extract all control IDs from compliance check name and normalize leading zeros."""
        if not compliance_check_name:
            return []

        control_id_pattern = r"([A-Za-z]{2}-\d+)(?:\s*\(\s*(\d+)\s*\))?"
        control_ids = []

        for part in compliance_check_name.split(", "):
            matches = re.findall(control_id_pattern, part.strip())
            for match in matches:
                base_control, enhancement = match
                normalized_control = self._normalize_base_control(base_control)
                formatted_control = self._format_control_id(normalized_control, enhancement)
                control_ids.append(formatted_control)

        return control_ids


def test_normalization():
    """Test control ID normalization."""

    test_item = WizComplianceReportItemTest()

    # Test cases from actual Wiz data
    test_cases = [
        # Single controls
        ("AC-3 Access Enforcement", ["AC-3"]),
        ("AC-2(4) Account Management | Automated Audit Actions", ["AC-2(4)"]),
        ("SI-4(20) System Monitoring | Privileged Users", ["SI-4(20)"]),
        # Multi-control strings
        (
            "AC-2(4) Account Management | Automated Audit Actions, AC-6(9) Least Privilege | Log Use of Privileged Functions, AU-12 Audit Record Generation",
            ["AC-2(4)", "AC-6(9)", "AU-12"],
        ),
        # Edge cases with leading zeros (potential future data)
        ("AC-01 Access Control", ["AC-1"]),
        ("AC-01(04) Access Control Enhancement", ["AC-1(4)"]),
        ("SC-08(01) Transmission Security", ["SC-8(1)"]),
        # Complex multi-control with various formats
        ("AC-01(04) Access Control, AU-3(1) Audit Content, SI-04(20) Monitoring", ["AC-1(4)", "AU-3(1)", "SI-4(20)"]),
    ]

    logger.info("Testing Wiz Control ID Normalization")
    logger.info("=" * 60)

    all_passed = True

    for input_string, expected_output in test_cases:
        result = test_item.get_all_control_ids(input_string)

        logger.info(f"\nInput: {input_string}")
        logger.info(f"Expected: {expected_output}")
        logger.info(f"Got:      {result}")

        if result == expected_output:
            logger.info("✓ PASS")
        else:
            logger.error("✗ FAIL")
            all_passed = False

    logger.info("\n" + "=" * 60)
    if all_passed:
        logger.info("All tests PASSED ✓")
    else:
        logger.error("Some tests FAILED ✗")

    # Test specific normalization cases
    logger.info("\n" + "=" * 60)
    logger.info("Testing specific normalization methods:")

    # Test base control normalization
    base_tests = [
        ("AC-01", "AC-1"),
        ("AC-1", "AC-1"),
        ("AU-003", "AU-3"),
        ("sc-7", "SC-7"),  # lowercase
    ]

    for input_val, expected in base_tests:
        result = test_item._normalize_base_control(input_val)
        status = "✓" if result == expected else "✗"
        logger.info(f"  _normalize_base_control('{input_val}') -> '{result}' (expected: '{expected}') {status}")

    # Test format control ID
    format_tests = [
        (("AC-1", "04"), "AC-1(4)"),
        (("AC-1", "4"), "AC-1(4)"),
        (("AC-1", ""), "AC-1"),
        (("SC-7", "001"), "SC-7(1)"),
    ]

    logger.info("\nTesting _format_control_id:")
    for (base, enhancement), expected in format_tests:
        result = test_item._format_control_id(base, enhancement)
        status = "✓" if result == expected else "✗"
        logger.info(f"  _format_control_id('{base}', '{enhancement}') -> '{result}' (expected: '{expected}') {status}")


if __name__ == "__main__":
    test_normalization()
