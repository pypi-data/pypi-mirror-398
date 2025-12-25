#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NIST SP 800-53 Framework Handler."""

import re
from typing import Optional, Set

from regscale.integrations.framework_handlers.base import FrameworkHandler


class NISTHandler(FrameworkHandler):
    """
    Handler for NIST SP 800-53 control IDs.

    Formats supported:
    - Basic: AC-1, SI-2, CM-6
    - With leading zeros: AC-01, AC-17
    - With enhancements (parentheses): AC-1(1), AC-17(02)
    - With enhancements (dots): AC-1.1, AC-17.2
    - With spaces: AC-1 (1), AC-02 (04)
    - Letter enhancements: AC-1(a), AC-1.a
    - Three-letter families: PTA-1, SAR-10, PRM-3
    """

    framework_name = "NIST"
    detection_pattern = r"^[A-Z]{2,3}-\d+"
    detection_priority = 10  # High priority

    def parse(self, control_string: str) -> Optional[str]:
        """
        Parse NIST control ID from string.

        :param str control_string: Raw control string
        :return: Parsed and normalized control ID or None
        :rtype: Optional[str]
        """
        if not control_string:
            return None

        control_string = control_string.strip().upper()

        # Pattern to match NIST control IDs with optional enhancements
        # Uses negated character class [^)]+ instead of alternation for lower complexity
        pattern = r"([A-Z]{2,3}-\d+(?:\s*\([^)]+\)|[.][0-9A-Z]+)?)"

        matches = re.findall(pattern, control_string)
        if not matches:
            return None

        control_id = matches[0]
        return self.normalize(control_id)

    def normalize(self, control_id: str) -> str:
        """
        Normalize NIST control ID.

        Converts parentheses to dots and removes leading zeros.
        AC-01(02) -> AC-1.2

        :param str control_id: Control ID to normalize
        :return: Normalized control ID
        :rtype: str
        """
        # Remove spaces and normalize parentheses to dots
        control_id = control_id.replace(" ", "").replace("(", ".").replace(")", "")

        parts = control_id.split("-")
        if len(parts) != 2:
            return control_id

        family = parts[0]
        number_part = parts[1]

        if "." in number_part:
            main_num, enhancement = number_part.split(".", 1)
            main_num = str(int(main_num))
            # Only normalize numeric enhancements
            if enhancement.isdigit():
                enhancement = str(int(enhancement))
            return f"{family}-{main_num}.{enhancement}"

        main_num = str(int(number_part))
        return f"{family}-{main_num}"

    def get_variations(self, control_id: str) -> Set[str]:
        """
        Generate all NIST control ID variations.

        :param str control_id: Control ID to generate variations for
        :return: Set of all valid variations
        :rtype: Set[str]
        """
        parsed = self.parse(control_id)
        if not parsed:
            return set()

        parts = parsed.split("-")
        if len(parts) != 2:
            return set()

        family = parts[0]
        number_part = parts[1]

        if "." in number_part:
            main_num, enhancement = number_part.split(".", 1)

            if enhancement.isalpha():
                return self._generate_letter_variations(family, main_num, enhancement)
            else:
                return self._generate_numeric_variations(family, main_num, enhancement)
        else:
            return self._generate_simple_variations(family, number_part)

    def _generate_simple_variations(self, family: str, main_num: str) -> Set[str]:
        """
        Generate variations for controls without enhancements.

        :param str family: Control family (e.g., AC, SI)
        :param str main_num: Main control number
        :return: Set of variations
        :rtype: Set[str]
        """
        main_int = int(main_num)
        return {
            f"{family}-{main_int}",
            f"{family}-{main_int:02d}",
        }

    def _generate_letter_variations(self, family: str, main_num: str, enhancement: str) -> Set[str]:
        """
        Generate variations for letter-based enhancements.

        :param str family: Control family (e.g., AC, SI)
        :param str main_num: Main control number
        :param str enhancement: Letter enhancement (e.g., a, b)
        :return: Set of variations
        :rtype: Set[str]
        """
        main_int = int(main_num)
        variations = set()

        for main_fmt in [str(main_int), f"{main_int:02d}"]:
            variations.add(f"{family}-{main_fmt}.{enhancement}")
            variations.add(f"{family}-{main_fmt}({enhancement})")

        return {v.upper() for v in variations}

    def _generate_numeric_variations(self, family: str, main_num: str, enhancement: str) -> Set[str]:
        """
        Generate variations for numeric enhancements.

        :param str family: Control family (e.g., AC, SI)
        :param str main_num: Main control number
        :param str enhancement: Numeric enhancement
        :return: Set of variations
        :rtype: Set[str]
        """
        main_int = int(main_num)
        enh_int = int(enhancement)
        variations = set()

        for main_fmt in [str(main_int), f"{main_int:02d}"]:
            for enh_fmt in [str(enh_int), f"{enh_int:02d}"]:
                variations.add(f"{family}-{main_fmt}.{enh_fmt}")
                variations.add(f"{family}-{main_fmt}({enh_fmt})")

        return {v.upper() for v in variations}

    def matches(self, control_id: str) -> bool:
        """
        Check if control ID matches NIST pattern.

        :param str control_id: Control ID to check
        :return: True if matches NIST pattern
        :rtype: bool
        """
        if not control_id:
            return False
        return bool(re.match(r"^[A-Z]{2,3}-\d+", control_id.strip().upper()))
