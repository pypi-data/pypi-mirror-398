#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Framework Handlers for Control ID Matching.

This module provides specialized handlers for different compliance frameworks
(NIST, CMMC, CIS, ISO, SOC2) to properly parse, normalize, and match control IDs.
"""

from regscale.integrations.framework_handlers.base import FrameworkHandler
from regscale.integrations.framework_handlers.registry import FrameworkHandlerRegistry, get_registry

__all__ = [
    "FrameworkHandler",
    "FrameworkHandlerRegistry",
    "get_registry",
]
