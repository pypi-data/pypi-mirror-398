#!/usr/bin/env python3
"""Test control matching for Wiz compliance report against catalog 3."""

import logging
from regscale.integrations.control_matcher import ControlMatcher

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sample control IDs from Wiz report
wiz_control_samples = [
    "AC-2(4)",
    "AC-6(9)",
    "AU-12",
    "AU-3(1)",
    "CM-3",
    "SI-4(20)",
    "AC-4(21)",
    "AC-3",
    "AC-17(1)",
    "AC-17(2)",
    "SC-8(1)",
    "SC-28",
    "SC-28(1)",
    "SI-7(12)",
    "PE-19",
    "PS-6",
    "SA-9(5)",
    "SC-7",
    "SI-4",
    "AU-13",
]


def test_individual_controls(matcher: ControlMatcher, catalog_id: int) -> tuple:
    """
    Test individual control matching.

    :param ControlMatcher matcher: Control matcher instance
    :param int catalog_id: Catalog ID to search
    :return: Tuple of (found_controls, not_found_controls)
    :rtype: tuple
    """
    found_controls = []
    not_found_controls = []

    for control_id in wiz_control_samples:
        logger.info(f"\nTesting: {control_id}")

        parsed = matcher.parse_control_id(control_id)
        logger.info(f"  Parsed as: {parsed}")

        control = matcher.find_control_in_catalog(control_id, catalog_id)

        if control:
            logger.info(f"  ✓ FOUND in catalog: {control.controlId} (ID: {control.id})")
            found_controls.append(control_id)
        else:
            logger.warning("  ✗ NOT FOUND in catalog")
            not_found_controls.append(control_id)

    return found_controls, not_found_controls


def log_summary(found_controls: list, not_found_controls: list) -> None:
    """
    Log summary of control matching results.

    :param list found_controls: List of found controls
    :param list not_found_controls: List of not found controls
    :return: None
    :rtype: None
    """
    logger.info("\n" + "=" * 60)
    logger.info("SUMMARY:")
    logger.info(f"Total tested: {len(wiz_control_samples)}")
    logger.info(f"Found: {len(found_controls)} ({len(found_controls) / len(wiz_control_samples) * 100:.1f}%)")
    logger.info(
        f"Not found: {len(not_found_controls)} ({len(not_found_controls) / len(wiz_control_samples) * 100:.1f}%)"
    )

    if not_found_controls:
        logger.info("\nControls not found in catalog:")
        for control in not_found_controls:
            logger.info(f"  - {control}")


def test_multi_control_parsing() -> None:
    """Test multi-control parsing from Wiz data format."""
    logger.info("\n" + "=" * 60)
    logger.info("Testing multi-control parsing:")

    multi_control_string = "AC-2(4) Account Management | Automated Audit Actions, AC-6(9) Least Privilege | Log Use of Privileged Functions, AU-12 Audit Record Generation"
    logger.info(f"\nInput: {multi_control_string}")

    import re

    control_id_pattern = r"([A-Za-z]{2}-\d+)(?:\s*\(\s*(\d+)\s*\))?"
    matches = []
    for part in multi_control_string.split(", "):
        found = re.findall(control_id_pattern, part.strip())
        for match in found:
            base_control, enhancement = match
            if enhancement:
                matches.append(f"{base_control}({enhancement})")
            else:
                matches.append(base_control)

    logger.info(f"Extracted control IDs: {matches}")


def test_normalization(matcher: ControlMatcher) -> None:
    """
    Test control ID normalization.

    :param ControlMatcher matcher: Control matcher instance
    :return: None
    :rtype: None
    """
    logger.info("\n" + "=" * 60)
    logger.info("Testing control ID normalization:")

    test_cases = [
        ("AC-01", "AC-1"),
        ("AC-1(01)", "AC-1.1"),
        ("AC-2 (4)", "AC-2.4"),
        ("ac-3", "AC-3"),
    ]

    for original, expected in test_cases:
        parsed = matcher.parse_control_id(original)
        logger.info(f"  {original} -> {parsed} (expected: {expected})")
        if parsed == expected:
            logger.info("    ✓ Correct")
        else:
            logger.warning(f"    ✗ Mismatch (got {parsed}, expected {expected})")


def test_control_matching():
    """Test control matching against catalog 3."""
    matcher = ControlMatcher()
    catalog_id = 3

    logger.info(f"Testing control matching for catalog {catalog_id}")
    logger.info("=" * 60)

    found_controls, not_found_controls = test_individual_controls(matcher, catalog_id)
    log_summary(found_controls, not_found_controls)
    test_multi_control_parsing()
    test_normalization(matcher)


if __name__ == "__main__":
    test_control_matching()
