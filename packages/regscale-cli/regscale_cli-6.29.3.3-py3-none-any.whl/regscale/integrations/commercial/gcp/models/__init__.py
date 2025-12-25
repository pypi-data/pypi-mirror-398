#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GCP Models Package.

This package contains data models for GCP integration:
- GCPComplianceItem: Compliance item for GCP SCC findings
"""

from regscale.integrations.commercial.gcp.models.compliance_item import GCPComplianceItem

__all__ = ["GCPComplianceItem"]
