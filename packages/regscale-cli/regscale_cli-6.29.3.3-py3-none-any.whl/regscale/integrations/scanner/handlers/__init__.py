#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scanner Handlers Module.

This module provides handler classes for delegating scanner integration responsibilities.
"""
from regscale.integrations.scanner.handlers.asset_handler import AssetHandler
from regscale.integrations.scanner.handlers.issue_handler import IssueHandler
from regscale.integrations.scanner.handlers.vulnerability_handler import VulnerabilityHandler

__all__ = ["AssetHandler", "IssueHandler", "VulnerabilityHandler"]
