#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Base Framework Handler for control ID parsing and matching."""

import re
from abc import ABC, abstractmethod
from typing import Optional, Set


class FrameworkHandler(ABC):
    """
    Abstract base class for framework-specific control ID handling.

    Each framework handler implements control ID parsing, normalization,
    and variation generation specific to its framework format.

    Following the Strategy Pattern:
    - Single Responsibility: Each handler handles one framework
    - Open/Closed: Extend via new handlers, closed for modification
    - Liskov Substitution: Any handler can replace the base

    Attributes:
        framework_name: Identifier for this framework (e.g., "NIST", "CMMC")
        detection_pattern: Regex pattern to identify this framework's control IDs
        detection_priority: Priority for detection (lower = higher priority)
    """

    # Class attribute - framework identifier
    framework_name: str = "GENERIC"

    # Class attribute - regex pattern to identify this framework
    detection_pattern: str = r".*"

    # Class attribute - priority for detection (lower = higher priority)
    detection_priority: int = 100

    @abstractmethod
    def parse(self, control_string: str) -> Optional[str]:
        """
        Parse a control ID string and extract the standardized identifier.

        :param str control_string: Raw control ID string
        :return: Standardized control ID or None if not parseable
        :rtype: Optional[str]
        """

    @abstractmethod
    def normalize(self, control_id: str) -> str:
        """
        Normalize a control ID to its canonical form.

        :param str control_id: Control ID to normalize
        :return: Normalized control ID
        :rtype: str
        """

    @abstractmethod
    def get_variations(self, control_id: str) -> Set[str]:
        """
        Generate all valid variations of a control ID.

        :param str control_id: Control ID to generate variations for
        :return: Set of all valid variations
        :rtype: Set[str]
        """

    @abstractmethod
    def matches(self, control_id: str) -> bool:
        """
        Check if a control ID matches this framework's pattern.

        :param str control_id: Control ID to check
        :return: True if matches this framework
        :rtype: bool
        """

    def can_handle(self, control_string: str) -> bool:
        """
        Determine if this handler can process the given control string.

        Default implementation uses the detection_pattern regex.

        :param str control_string: Control string to check
        :return: True if this handler can process the string
        :rtype: bool
        """
        if not control_string:
            return False
        return bool(re.match(self.detection_pattern, control_string.strip().upper()))
