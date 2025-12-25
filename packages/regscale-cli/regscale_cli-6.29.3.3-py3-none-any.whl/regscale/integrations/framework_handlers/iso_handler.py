#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ISO 27001 Framework Handler."""

import re
from typing import Optional, Set

from regscale.integrations.framework_handlers.base import FrameworkHandler


class ISOHandler(FrameworkHandler):
    """
    Handler for ISO 27001 control IDs.

    Formats supported:
    - Annex A format: A.5.1, A.5.1.1, A.12.3.1
    - Case variations: a.5.1, A.5.1
    """

    framework_name = "ISO"
    detection_pattern = r"^[A-Z]\.\d+(?:\.\d+){1,2}$"
    detection_priority = 10

    def parse(self, control_string: str) -> Optional[str]:
        """
        Parse ISO control ID from string.

        :param str control_string: Raw control string
        :return: Parsed control ID or None
        :rtype: Optional[str]
        """
        if not control_string:
            return None

        control_string = control_string.strip().upper()

        pattern = r"^([A-Z]\.\d+(?:\.\d+){1,2})"

        if match := re.match(pattern, control_string):
            return match.group(1).upper()

        return None

    def normalize(self, control_id: str) -> str:
        """
        Normalize ISO control ID to uppercase.

        :param str control_id: Control ID to normalize
        :return: Normalized control ID
        :rtype: str
        """
        return control_id.upper()

    def get_variations(self, control_id: str) -> Set[str]:
        """
        Generate ISO control ID variations with case variations.

        :param str control_id: Control ID to generate variations for
        :return: Set of all valid variations
        :rtype: Set[str]
        """
        parsed = self.parse(control_id)
        if not parsed:
            return set()

        return {parsed, parsed.upper(), parsed.lower()}

    def matches(self, control_id: str) -> bool:
        """
        Check if control ID matches ISO pattern.

        :param str control_id: Control ID to check
        :return: True if matches ISO pattern
        :rtype: bool
        """
        if not control_id:
            return False
        return bool(re.match(r"^[A-Za-z]\.\d+(?:\.\d+){1,2}$", control_id.strip()))
