#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SOC 2 Trust Services Criteria Framework Handler."""

import re
from typing import Optional, Set

from regscale.integrations.framework_handlers.base import FrameworkHandler


class SOC2Handler(FrameworkHandler):
    """
    Handler for SOC 2 Trust Services Criteria control IDs.

    Formats supported:
    - Common Criteria: CC1.1, CC1.2
    - Availability: A1.1, A1.2
    - Confidentiality: C1.1, C1.2
    - Processing Integrity: PI1.1, PI1.5
    - Privacy: P1.1, P1.2
    """

    framework_name = "SOC2"
    detection_pattern = r"^(?:CC|PI|A|C|P)\d+\.\d+"
    detection_priority = 10

    # Valid SOC2 prefixes
    SOC2_PREFIXES = {"CC", "PI", "A", "C", "P"}

    def parse(self, control_string: str) -> Optional[str]:
        """
        Parse SOC2 control ID from string.

        :param str control_string: Raw control string
        :return: Parsed control ID or None
        :rtype: Optional[str]
        """
        if not control_string:
            return None

        control_string = control_string.strip().upper()

        # Pattern for SOC2 controls
        pattern = r"^([A-Z]{1,2}\d+\.\d+)"

        if match := re.match(pattern, control_string):
            control_id = match.group(1)
            # Verify it's a valid SOC2 prefix
            prefix_match = re.match(r"^([A-Z]+)", control_id)
            if prefix_match and prefix_match.group(1) in self.SOC2_PREFIXES:
                return control_id.upper()

        return None

    def normalize(self, control_id: str) -> str:
        """
        Normalize SOC2 control ID to uppercase.

        :param str control_id: Control ID to normalize
        :return: Normalized control ID
        :rtype: str
        """
        return control_id.upper()

    def get_variations(self, control_id: str) -> Set[str]:
        """
        Generate SOC2 control ID variations.

        :param str control_id: Control ID to generate variations for
        :return: Set of all valid variations
        :rtype: Set[str]
        """
        parsed = self.parse(control_id)
        if not parsed:
            return set()

        variations = {parsed, parsed.upper(), parsed.lower()}

        # Version without dots (CC1.1 -> CC11)
        nodot = parsed.replace(".", "")
        variations.update({nodot, nodot.upper(), nodot.lower()})

        return variations

    def matches(self, control_id: str) -> bool:
        """
        Check if control ID matches SOC2 pattern.

        :param str control_id: Control ID to check
        :return: True if matches SOC2 pattern
        :rtype: bool
        """
        if not control_id:
            return False

        control_id = control_id.strip().upper()

        if not re.match(r"^[A-Z]{1,2}\d+\.\d+$", control_id):
            return False

        # Extract and verify prefix
        prefix_match = re.match(r"^([A-Z]+)", control_id)
        if prefix_match:
            return prefix_match.group(1) in self.SOC2_PREFIXES

        return False
