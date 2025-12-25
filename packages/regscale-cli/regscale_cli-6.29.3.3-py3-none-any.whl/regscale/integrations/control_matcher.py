#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Control Matcher - A utility class for identifying and matching control implementations
across different RegScale entities based on control ID strings.
"""

import logging
import re
from typing import Dict, List, Optional, Tuple

from regscale.core.app.api import Api
from regscale.core.app.application import Application
from regscale.integrations.framework_handlers.registry import get_registry
from regscale.models.regscale_models.control_implementation import ControlImplementation
from regscale.models.regscale_models.security_control import SecurityControl

logger = logging.getLogger("regscale")


class ControlMatcher:
    """
    A class to identify control IDs and match them across different RegScale entities.

    This class provides control matching capabilities:
    - Parse control ID strings to extract NIST control identifiers
    - Match controls from catalogs to security plans
    - Find control implementations based on control IDs
    - Support multiple control ID formats (e.g., AC-1, AC-1(1), AC-1.1)

    Note: This class is focused on finding and matching existing controls only.
    Control creation/modification should be handled by calling code.
    """

    def __init__(self, app: Optional[Application] = None):
        """
        Initialize the ControlMatcher.

        :param Optional[Application] app: RegScale Application instance
        """
        self.app = app or Application()
        self.api = Api()
        self._catalog_cache: Dict[int, List[SecurityControl]] = {}
        self._control_impl_cache: Dict[Tuple[int, str], Dict[str, ControlImplementation]] = {}
        self._handler_registry = get_registry()

    @staticmethod
    def _normalize_nist_control_id(control_id: str) -> str:
        """
        Normalize a NIST control ID by removing spaces, normalizing parentheses, and removing leading zeros.

        :param str control_id: Raw NIST control ID
        :return: Normalized control ID
        :rtype: str
        """
        # Remove spaces and normalize parentheses to dots
        control_id = control_id.replace(" ", "").replace("(", ".").replace(")", "")

        # Normalize leading zeros (e.g., AC-01.02 -> AC-1.2)
        parts = control_id.split("-")
        if len(parts) != 2:
            return control_id

        family = parts[0]
        number_part = parts[1]

        if "." in number_part:
            main_num, enhancement = number_part.split(".", 1)
            main_num = str(int(main_num))
            # Only normalize if enhancement is numeric, preserve letters as-is
            if enhancement.isdigit():
                enhancement = str(int(enhancement))
            return f"{family}-{main_num}.{enhancement}"

        main_num = str(int(number_part))
        return f"{family}-{main_num}"

    @staticmethod
    def parse_control_id(control_string: str) -> Optional[str]:
        """
        Parse a control ID string and extract the standardized control identifier.

        Handles various formats:
        - NIST format: AC-1, AC-1(1), AC-1.1, AC-1(a), AC-1.a
        - SOC 2 format: CC1.1, PI1.5, A1.2, C1.1, P1.1
        - CIS format: 1.1, 1.1.1, 1.1.1.1
        - ISO format: A.5.1, A.5.1.1
        - With leading zeros: AC-01, AC-17(02)
        - With spaces: AC-1 (1), AC-02 (04), AC-1 (a)
        - With text: "Access Control AC-1"
        - Multiple controls: "AC-1, AC-2"

        :param str control_string: Raw control ID string
        :return: Standardized control ID or None if not found
        :rtype: Optional[str]
        """
        if not control_string:
            return None

        # Clean the string
        control_string = control_string.strip().upper()

        # Try framework-specific patterns in order of specificity
        patterns = [
            # NIST control ID pattern
            (r"([A-Z]{2,3}-\d+(?:\s*\(\s*(?:\d+|[A-Z])\s*\)|\.(?:\d+|[A-Z]))?)", "NIST"),
            # SOC 2 pattern (CC1.1, PI1.5, etc.)
            (r"^([A-Z]{1,3}\d+\.\d+)", "SOC2"),
            # CIS pattern (1.1, 1.1.1, 1.1.1.1)
            (r"^(\d+(?:\.\d+){1,3})", "CIS"),
            # ISO pattern (A.5.1, A.5.1.1)
            (r"^([A-Z]\.\d+(?:\.\d+){1,2})", "ISO"),
            # Generic alphanumeric with dots (fallback)
            (r"^([A-Z]+\d+(?:\.\d+)*)", "GENERIC"),
        ]

        for pattern, framework in patterns:
            if matches := re.findall(pattern, control_string):
                control_id = matches[0]

                # Framework-specific normalization
                if framework == "NIST":
                    return ControlMatcher._normalize_nist_control_id(control_id)
                if framework in ["SOC2", "CIS", "ISO"]:
                    # These formats are already normalized, just ensure uppercase
                    return control_id.upper()

                return control_id

        return None

    def find_control_in_catalog(self, control_id: str, catalog_id: int) -> Optional[SecurityControl]:
        """
        Find a security control in a specific catalog by control ID.

        :param str control_id: The control ID to search for
        :param int catalog_id: The catalog ID to search in
        :return: SecurityControl object if found, None otherwise
        :rtype: Optional[SecurityControl]
        """
        controls = self._get_catalog_controls(catalog_id)

        # Generate all possible variations of the control ID
        search_ids = self._get_control_id_variations(control_id)

        # Try exact match with any variation
        for control in controls:
            if control.controlId in search_ids:
                return control

        # Try matching control variations against search variations
        for control in controls:
            control_variations = self._get_control_id_variations(control.controlId)
            if control_variations & search_ids:  # Set intersection
                return control

        return None

    def find_control_implementation(
        self, control_id: str, parent_id: int, parent_module: str = "securityplans", catalog_id: Optional[int] = None
    ) -> Optional[ControlImplementation]:
        """
        Find a control implementation based on control ID and parent context.

        :param str control_id: The control ID to match
        :param int parent_id: Parent entity ID (e.g., security plan ID)
        :param str parent_module: Parent module type (default: securityplans)
        :param Optional[int] catalog_id: Optional catalog ID for better matching
        :return: ControlImplementation if found, None otherwise
        :rtype: Optional[ControlImplementation]
        """
        # Get control implementations for the parent
        implementations = self._get_control_implementations(parent_id, parent_module)

        # Get all variations of the control ID for matching
        search_variations = self._get_control_id_variations(control_id)
        if not search_variations:
            logger.warning(f"Could not parse control ID: {control_id}")
            return None

        # Try to find matching implementation with variation matching
        for impl_key, impl in implementations.items():
            impl_variations = self._get_control_id_variations(impl_key)
            if impl_variations & search_variations:  # Set intersection
                return impl

        # If catalog ID provided, try to find via security control
        if catalog_id:
            control = self.find_control_in_catalog(control_id, catalog_id)
            if control:
                # Search implementations by control ID
                for impl in implementations.values():
                    if impl.controlID == control.id:
                        return impl

        return None

    def match_controls_to_implementations(
        self,
        control_ids: List[str],
        parent_id: int,
        parent_module: str = "securityplans",
        catalog_id: Optional[int] = None,
    ) -> Dict[str, Optional[ControlImplementation]]:
        """
        Match multiple control IDs to their implementations.

        :param List[str] control_ids: List of control ID strings
        :param int parent_id: Parent entity ID
        :param str parent_module: Parent module type
        :param Optional[int] catalog_id: Optional catalog ID
        :return: Dictionary mapping control IDs to implementations
        :rtype: Dict[str, Optional[ControlImplementation]]
        """
        results = {}

        for control_id in control_ids:
            impl = self.find_control_implementation(control_id, parent_id, parent_module, catalog_id)
            results[control_id] = impl

        return results

    def get_security_plan_controls(self, security_plan_id: int) -> Dict[str, ControlImplementation]:
        """
        Get all control implementations for a security plan.

        :param int security_plan_id: The security plan ID
        :return: Dictionary of control implementations keyed by control ID
        :rtype: Dict[str, ControlImplementation]
        """
        return self._get_control_implementations(security_plan_id, "securityplans")

    def find_controls_by_pattern(self, pattern: str, catalog_id: int) -> List[SecurityControl]:
        """
        Find all controls in a catalog matching a pattern.

        :param str pattern: Regex pattern or substring to match
        :param int catalog_id: Catalog ID to search in
        :return: List of matching SecurityControl objects
        :rtype: List[SecurityControl]
        """
        controls = self._get_catalog_controls(catalog_id)
        matched = []

        for control in controls:
            if (re.search(pattern, control.controlId, re.IGNORECASE)) or (
                control.title and re.search(pattern, control.title, re.IGNORECASE)
            ):
                matched.append(control)

        return matched

    def bulk_match_controls(
        self,
        control_mappings: Dict[str, str],
        parent_id: int,
        parent_module: str = "securityplans",
        catalog_id: Optional[int] = None,
    ) -> Dict[str, Optional[ControlImplementation]]:
        """
        Bulk match control IDs to their implementations.

        :param Dict[str, str] control_mappings: Dict of {external_id: control_id}
        :param int parent_id: Parent entity ID
        :param str parent_module: Parent module type
        :param Optional[int] catalog_id: Catalog ID for controls
        :return: Dictionary mapping external IDs to ControlImplementations (None if not found)
        :rtype: Dict[str, Optional[ControlImplementation]]
        """
        results = {}

        for external_id, control_id in control_mappings.items():
            impl = self.find_control_implementation(control_id, parent_id, parent_module, catalog_id)
            results[external_id] = impl

        return results

    def _get_catalog_controls(self, catalog_id: int) -> List[SecurityControl]:
        """
        Get all controls for a catalog (with caching).

        :param int catalog_id: Catalog ID
        :return: List of SecurityControl objects
        :rtype: List[SecurityControl]
        """
        if catalog_id not in self._catalog_cache:
            try:
                controls = SecurityControl.get_list_by_catalog(catalog_id)
                self._catalog_cache[catalog_id] = controls
            except Exception as e:
                logger.error(f"Failed to get controls for catalog {catalog_id}: {e}")
                return []

        return self._catalog_cache.get(catalog_id, [])

    def _normalize_control_id(self, control_id: str) -> Optional[str]:
        """
        Normalize a control ID by removing leading zeros from all numeric parts.

        Examples:
        - AC-01 -> AC-1
        - AC-17(02) -> AC-17.2
        - AC-1.01 -> AC-1.1

        :param str control_id: The control ID to normalize
        :return: Normalized control ID or None if invalid
        :rtype: Optional[str]
        """
        parsed = self.parse_control_id(control_id)
        if not parsed:
            return None

        # Split by '-' to get family and number parts
        parts = parsed.split("-")
        if len(parts) != 2:
            return None

        family = parts[0]
        number_part = parts[1]

        # Handle enhancement notation (both . and parentheses are normalized to .)
        if "." in number_part:
            main_num, enhancement = number_part.split(".", 1)
            # Remove leading zeros from both parts
            main_num = str(int(main_num))
            enhancement = str(int(enhancement))
            return f"{family}-{main_num}.{enhancement}"
        else:
            # Just main control number
            main_num = str(int(number_part))
            return f"{family}-{main_num}"

    @staticmethod
    def _generate_simple_variations(family: str, main_num: str) -> set:
        """
        Generate variations for simple control IDs without enhancements.

        :param str family: Control family (e.g., AC, SI)
        :param str main_num: Main control number
        :return: Set of variations
        :rtype: set
        """
        main_int = int(main_num)
        return {
            f"{family}-{main_int}",
            f"{family}-{main_int:02d}",
        }

    @staticmethod
    def _generate_letter_enhancement_variations(family: str, main_num: str, enhancement: str) -> set:
        """
        Generate variations for control IDs with letter-based enhancements.

        :param str family: Control family (e.g., AC, SI)
        :param str main_num: Main control number
        :param str enhancement: Letter enhancement (e.g., a, b)
        :return: Set of variations
        :rtype: set
        """
        main_int = int(main_num)
        variations = set()

        for main_fmt in [str(main_int), f"{main_int:02d}"]:
            variations.add(f"{family}-{main_fmt}.{enhancement}")
            variations.add(f"{family}-{main_fmt}({enhancement})")

        return variations

    @staticmethod
    def _generate_numeric_enhancement_variations(family: str, main_num: str, enhancement: str) -> set:
        """
        Generate variations for control IDs with numeric enhancements.

        :param str family: Control family (e.g., AC, SI)
        :param str main_num: Main control number
        :param str enhancement: Numeric enhancement
        :return: Set of variations
        :rtype: set
        """
        main_int = int(main_num)
        enh_int = int(enhancement)
        variations = set()

        for main_fmt in [str(main_int), f"{main_int:02d}"]:
            for enh_fmt in [str(enh_int), f"{enh_int:02d}"]:
                variations.add(f"{family}-{main_fmt}.{enh_fmt}")
                variations.add(f"{family}-{main_fmt}({enh_fmt})")

        return variations

    def _get_control_id_variations(self, control_id: str) -> set:
        """
        Generate all valid variations of a control ID (with and without leading zeros).

        Examples:
        - NIST: AC-1 -> {AC-1, AC-01}
        - NIST: AC-17.2 -> {AC-17.2, AC-17.02, AC-17(2), AC-17(02)}
        - NIST: AC-1.a -> {AC-1.a, AC-01.a, AC-1(a), AC-01(a)}
        - SOC2: CC1.1 -> {CC1.1, cc1.1}
        - CIS: 1.1.1 -> {1.1.1}
        - ISO: A.5.1 -> {A.5.1, a.5.1}
        - CMMC: 3.1.1 -> {3.1.1, 3.01.01, 3.1.01, 3.01.1, 03.1.1, ...}

        :param str control_id: The control ID to generate variations for
        :return: Set of all valid variations
        :rtype: set
        """
        # Try handler registry first for specialized variation generation
        handler_variations = self._try_handler_variations(control_id)
        if handler_variations:
            return handler_variations

        # Fall back to legacy variation generation
        parsed = self.parse_control_id(control_id)
        if not parsed:
            return set()

        # Detect framework type and dispatch to appropriate generator
        framework = self._detect_framework(parsed)
        variation_generators = {
            "NIST": self._get_nist_legacy_variations,
            "SOC2": self._get_soc2_variations,
            "CIS": lambda p: {p},
            "ISO": self._get_case_variations,
        }

        generator = variation_generators.get(framework, self._get_case_variations)
        return generator(parsed)

    def _try_handler_variations(self, control_id: str) -> set:
        """
        Try to get variations from handler registry.

        :param str control_id: Control ID to process
        :return: Set of variations or empty set if handler not found
        :rtype: set
        """
        handler = self._handler_registry.detect_handler(control_id)
        if not handler:
            return set()

        variations = handler.get_variations(control_id)
        if variations:
            logger.debug(
                "Generated %d variations for %s using %s handler",
                len(variations),
                control_id,
                handler.framework_name,
            )
        return variations or set()

    def _get_nist_legacy_variations(self, parsed: str) -> set:
        """
        Generate NIST control ID variations (legacy fallback).

        :param str parsed: Parsed control ID
        :return: Set of variations
        :rtype: set
        """
        parts = parsed.split("-")
        if len(parts) != 2:
            return set()

        family = parts[0]
        number_part = parts[1]

        if "." not in number_part:
            variations = self._generate_simple_variations(family, number_part)
        else:
            main_num, enhancement = number_part.split(".", 1)
            if enhancement.isalpha():
                variations = self._generate_letter_enhancement_variations(family, main_num, enhancement)
            else:
                variations = self._generate_numeric_enhancement_variations(family, main_num, enhancement)

        return {v.upper() for v in variations}

    def _get_soc2_variations(self, parsed: str) -> set:
        """
        Generate SOC2 control ID variations.

        :param str parsed: Parsed control ID
        :return: Set of variations with case and dot variations
        :rtype: set
        """
        nodot_version = parsed.replace(".", "")
        return {
            parsed,
            parsed.upper(),
            parsed.lower(),
            nodot_version,
            nodot_version.upper(),
            nodot_version.lower(),
        }

    def _get_case_variations(self, parsed: str) -> set:
        """
        Generate simple case variations.

        :param str parsed: Parsed control ID
        :return: Set with original, upper, and lower case variations
        :rtype: set
        """
        return {parsed, parsed.upper(), parsed.lower()}

    def _detect_framework(self, control_id: str) -> str:
        """
        Detect the framework type from a control ID.

        Uses the framework handler registry for detection, with fallback
        to legacy regex patterns for backward compatibility.

        :param str control_id: Control ID to analyze
        :return: Framework type (NIST, SOC2, CIS, ISO, CMMC, or GENERIC)
        :rtype: str
        """
        # Try handler registry first
        handler = self._handler_registry.detect_handler(control_id)
        if handler:
            return handler.framework_name

        # Fallback to legacy detection for backward compatibility
        if re.match(r"^[A-Z]{2,3}-\d+", control_id):
            return "NIST"
        elif re.match(r"^[A-Z]{1,3}\d+\.\d+", control_id):
            return "SOC2"
        elif re.match(r"^\d+(?:\.\d+){1,3}$", control_id):
            return "CIS"
        elif re.match(r"^[A-Z]\.\d+(?:\.\d+){1,2}$", control_id):
            return "ISO"
        else:
            return "GENERIC"

    def _get_control_implementations(self, parent_id: int, parent_module: str) -> Dict[str, ControlImplementation]:
        """
        Get control implementations for a parent (with caching).

        :param int parent_id: Parent ID
        :param str parent_module: Parent module
        :return: Dict of implementations keyed by control ID
        :rtype: Dict[str, ControlImplementation]
        """
        cache_key = (parent_id, parent_module)

        if cache_key not in self._control_impl_cache:
            try:
                # Get the label map which maps control IDs to implementation IDs
                label_map = ControlImplementation.get_control_label_map_by_parent(parent_id, parent_module)

                if not label_map:
                    logger.warning(
                        "No control implementations found for %s/%s. "
                        "This may indicate API connectivity issues or missing configuration. "
                        "Ensure RegScale init.yaml is accessible and API credentials are valid.",
                        parent_module,
                        parent_id,
                    )

                implementations = {}
                for control_label, impl_id in label_map.items():
                    impl = ControlImplementation.get_object(impl_id)
                    if impl:
                        implementations[control_label] = impl

                self._control_impl_cache[cache_key] = implementations
                logger.debug("Cached %d implementations for %s/%s", len(implementations), parent_module, parent_id)
            except Exception as e:
                logger.error("Failed to get implementations for %s/%s: %s", parent_module, parent_id, e)
                return {}

        return self._control_impl_cache.get(cache_key, {})

    def clear_cache(self):
        """Clear all cached data."""
        self._catalog_cache.clear()
        self._control_impl_cache.clear()
        logger.info("Cleared control matcher cache")
