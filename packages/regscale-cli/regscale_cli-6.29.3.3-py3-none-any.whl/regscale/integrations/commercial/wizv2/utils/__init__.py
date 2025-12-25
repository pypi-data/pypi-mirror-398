#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Utils module for Wiz integration - re-exports from main.py for clean imports."""

# Import all util functions from the main utils module
from regscale.integrations.commercial.wizv2.utils.main import (
    create_asset_type,
    get_notes_from_wiz_props,
    handle_management_type,
    map_category,
    is_report_expired,
    convert_first_seen_to_days,
    fetch_report_by_id,
    download_file,
    fetch_sbom_report,
    compliance_job_progress,
    get_report_url_and_status,
    get_or_create_report_id,
    create_compliance_report,
    download_report,
    rerun_expired_report,
)

# Import constants needed by tests and other modules
from regscale.integrations.commercial.wizv2.core.constants import (
    CHECK_INTERVAL_FOR_DOWNLOAD_REPORT,
    MAX_RETRIES,
)

__all__ = [
    "create_asset_type",
    "get_notes_from_wiz_props",
    "handle_management_type",
    "map_category",
    "is_report_expired",
    "convert_first_seen_to_days",
    "fetch_report_by_id",
    "download_file",
    "fetch_sbom_report",
    "compliance_job_progress",
    "get_report_url_and_status",
    "get_or_create_report_id",
    "create_compliance_report",
    "download_report",
    "rerun_expired_report",
    "CHECK_INTERVAL_FOR_DOWNLOAD_REPORT",
    "MAX_RETRIES",
]
