#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CMMC (Cybersecurity Maturity Model Certification) Framework Handler."""

import re
from typing import Optional, Set

from regscale.integrations.framework_handlers.base import FrameworkHandler


class CMMCHandler(FrameworkHandler):
    """
    Handler for CMMC control IDs.

    Formats supported:
    - Numeric format: 3.1.1, 3.4.1 (Level.Domain.Practice)
    - Domain prefix format: AC.1.001, SC.2.007
    - Leading zeros: 03.01.001

    CMMC Level structure:
    - Level 1: Basic Cyber Hygiene (17 practices)
    - Level 2: Intermediate Cyber Hygiene
    - Level 3: Good Cyber Hygiene (based on NIST 800-171)
    - Level 4: Proactive
    - Level 5: Advanced/Progressive

    Domain codes:
    - AC: Access Control
    - AM: Asset Management
    - AU: Audit and Accountability
    - AT: Awareness and Training
    - CM: Configuration Management
    - IA: Identification and Authentication
    - IR: Incident Response
    - MA: Maintenance
    - MP: Media Protection
    - PS: Personnel Security
    - PE: Physical Protection
    - RE: Recovery
    - RM: Risk Management
    - CA: Security Assessment
    - SC: System and Communications Protection
    - SI: System and Information Integrity
    - SR: Situational Awareness
    """

    framework_name = "CMMC"
    # CMMC pattern: Must have domain prefix OR be in specific CMMC numeric ranges
    # Domain format: AC.1.001, SC.2.178
    # Numeric format: 3.1.1, 3.4.1 (where first digit 1-5 represents CMMC level)
    detection_pattern = r"^(?:[A-Z]{2}\.\d+\.\d+|\d\.\d+\.\d+)$"
    detection_priority = 5  # Higher priority than CIS to catch CMMC first

    # CMMC domain prefixes
    CMMC_DOMAINS = {
        "AC",
        "AM",
        "AU",
        "AT",
        "CM",
        "IA",
        "IR",
        "MA",
        "MP",
        "PS",
        "PE",
        "RE",
        "RM",
        "CA",
        "SC",
        "SI",
        "SR",
    }

    def parse(self, control_string: str) -> Optional[str]:
        """
        Parse CMMC control ID from string.

        :param str control_string: Raw control string
        :return: Parsed and normalized control ID or None
        :rtype: Optional[str]
        """
        if not control_string:
            return None

        control_string = control_string.strip().upper()

        # Try domain prefix format first: AC.1.001
        domain_pattern = r"^([A-Z]{2}\.\d+\.\d+)"
        if match := re.match(domain_pattern, control_string):
            return self.normalize(match.group(1))

        # Try numeric format: 3.1.1 (CMMC level.domain.practice)
        numeric_pattern = r"^(\d\.\d+\.\d+)"
        if match := re.match(numeric_pattern, control_string):
            return self.normalize(match.group(1))

        return None

    def normalize(self, control_id: str) -> str:
        """
        Normalize CMMC control ID.

        Removes leading zeros and ensures consistent formatting.
        03.01.001 -> 3.1.1
        AC.01.001 -> AC.1.1

        :param str control_id: Control ID to normalize
        :return: Normalized control ID
        :rtype: str
        """
        parts = control_id.split(".")

        if len(parts) != 3:
            return control_id

        # Handle domain prefix vs numeric first part
        if parts[0].isalpha():
            # Domain format: AC.1.001
            domain = parts[0].upper()
            level = str(int(parts[1]))
            practice = str(int(parts[2]))
            return f"{domain}.{level}.{practice}"

        # Numeric format: 3.1.1
        level = str(int(parts[0]))
        domain = str(int(parts[1]))
        practice = str(int(parts[2]))
        return f"{level}.{domain}.{practice}"

    def get_variations(self, control_id: str) -> Set[str]:
        """
        Generate all CMMC control ID variations.

        This is the KEY FIX for the duplicate issue problem.
        Unlike CIS which only returns {parsed}, CMMC needs variations.

        :param str control_id: Control ID to generate variations for
        :return: Set of all valid variations
        :rtype: Set[str]
        """
        parsed = self.parse(control_id)
        if not parsed:
            return set()

        parts = parsed.split(".")
        if len(parts) != 3:
            return {parsed}

        if parts[0].isalpha():
            return self._generate_domain_format_variations(parts)
        return self._generate_numeric_format_variations(parts)

    def _generate_domain_format_variations(self, parts: list) -> Set[str]:
        """
        Generate variations for domain format (e.g., AC.1.1).

        :param list parts: Split parts of the control ID
        :return: Set of variations
        :rtype: Set[str]
        """
        domain = parts[0]
        level = int(parts[1])
        practice = int(parts[2])

        level_formats = [str(level), f"{level:02d}"]
        practice_formats = [str(practice), f"{practice:02d}", f"{practice:03d}"]

        return {f"{domain}.{lf}.{pf}" for lf in level_formats for pf in practice_formats}

    def _generate_numeric_format_variations(self, parts: list) -> Set[str]:
        """
        Generate variations for numeric format (e.g., 3.1.1).

        :param list parts: Split parts of the control ID
        :return: Set of variations
        :rtype: Set[str]
        """
        level = int(parts[0])
        domain = int(parts[1])
        practice = int(parts[2])

        # Level is always single digit 1-5
        domain_formats = [str(domain), f"{domain:02d}"]
        practice_formats = [str(practice), f"{practice:02d}", f"{practice:03d}"]

        return {f"{level}.{df}.{pf}" for df in domain_formats for pf in practice_formats}

    def matches(self, control_id: str) -> bool:
        """
        Check if control ID matches CMMC pattern.

        :param str control_id: Control ID to check
        :return: True if matches CMMC pattern
        :rtype: bool
        """
        if not control_id:
            return False

        control_id = control_id.strip().upper()

        # Check domain prefix format
        if re.match(r"^[A-Z]{2}\.\d+\.\d+$", control_id):
            domain = control_id.split(".")[0]
            return domain in self.CMMC_DOMAINS

        # Check numeric format (level.domain.practice where level is 1-5)
        if re.match(r"^[1-5]\.\d+\.\d+$", control_id):
            return True

        return False
