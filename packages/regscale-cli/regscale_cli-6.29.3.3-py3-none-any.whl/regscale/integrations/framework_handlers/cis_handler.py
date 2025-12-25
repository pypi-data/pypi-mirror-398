#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CIS (Center for Internet Security) Benchmark Framework Handler."""

import re
from typing import Optional, Set

from regscale.integrations.framework_handlers.base import FrameworkHandler


class CISHandler(FrameworkHandler):
    """
    Handler for CIS Benchmark control IDs.

    Formats supported:
    - Section.subsection: 1.1, 2.3
    - Multi-level: 1.1.1, 1.1.1.1

    CIS controls are purely numeric with dots.
    They typically start with section numbers 1-20.

    Note: CMMC controls also use numeric format (e.g., 3.1.1) but represent
    Level.Domain.Practice. To distinguish, this handler does NOT match
    3-part IDs starting with 1-5 (which are handled by CMMCHandler).
    """

    framework_name = "CIS"
    # CIS pattern: starts with section numbers, but excludes CMMC-style 3-part IDs
    detection_pattern = r"^\d+(?:\.\d+){1,3}$"
    detection_priority = 15  # Lower priority than CMMC

    def parse(self, control_string: str) -> Optional[str]:
        """
        Parse CIS control ID from string.

        :param str control_string: Raw control string
        :return: Parsed control ID or None
        :rtype: Optional[str]
        """
        if not control_string:
            return None

        control_string = control_string.strip()

        # CIS pattern: numeric sections separated by dots
        pattern = r"^(\d+(?:\.\d+){1,3})"

        if match := re.match(pattern, control_string):
            return self.normalize(match.group(1))

        return None

    def normalize(self, control_id: str) -> str:
        """
        Normalize CIS control ID.

        CIS controls are typically already normalized.
        Just ensure no leading zeros in sections.

        :param str control_id: Control ID to normalize
        :return: Normalized control ID
        :rtype: str
        """
        parts = control_id.split(".")
        normalized_parts = [str(int(p)) for p in parts]
        return ".".join(normalized_parts)

    def get_variations(self, control_id: str) -> Set[str]:
        """
        Generate CIS control ID variations.

        CIS controls have limited variations - mainly normalized and
        zero-padded versions.

        :param str control_id: Control ID to generate variations for
        :return: Set of all valid variations
        :rtype: Set[str]
        """
        parsed = self.parse(control_id)
        if not parsed:
            return set()

        normalized = self.normalize(parsed)
        variations = {normalized, parsed}

        # Add zero-padded variations for consistency
        parts = normalized.split(".")
        if len(parts) >= 2:
            # Try with leading zeros
            padded = ".".join(f"{int(p):02d}" for p in parts)
            variations.add(padded)

        return variations

    def matches(self, control_id: str) -> bool:
        """
        Check if control ID matches CIS pattern.

        Important: This must NOT match CMMC numeric format (1-5.x.x).
        CMMC controls with format Level.Domain.Practice (e.g., 3.1.1)
        should be handled by CMMCHandler.

        :param str control_id: Control ID to check
        :return: True if matches CIS pattern
        :rtype: bool
        """
        if not control_id:
            return False

        control_id = control_id.strip()

        # Must be purely numeric with dots
        if not re.match(r"^\d+(?:\.\d+){1,3}$", control_id):
            return False

        # Check first section number
        parts = control_id.split(".")
        first_section = int(parts[0])

        # If it's a 3-part ID starting with 1-5, it could be CMMC
        # Let CMMC handler take priority for these
        if len(parts) == 3 and 1 <= first_section <= 5:
            return False

        # CIS controls typically use sections 1-20+
        # 2-part IDs (like 1.1) or 4-part IDs are clearly CIS
        return True
