#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test for Burp scan integration in RegScale CLI"""
import shutil
from datetime import datetime
import pytest

from regscale.integrations.commercial.burp import import_burp_scan
from regscale.models.regscale_models.scan_history import ScanHistory
from tests import CLITestFixture


class TestBurpIntegration(CLITestFixture):
    """Test the Burp integration"""

    @pytest.fixture(autouse=True)
    def setup_ssp(self, create_security_plan):
        self.security_plan = create_security_plan

    def test_burp_integration(self, test_data_dir):
        """Test the Burp integration"""
        burp_scan_file = test_data_dir / "burp-scan.xml"
        assert burp_scan_file.exists(), "Test data file not found"
        processed_files = []

        try:
            current_datetime = datetime.now().strftime("%Y-%m-%d")
            security_plan = self.security_plan

            import_burp_scan(test_data_dir, security_plan.id, current_datetime, True)
            scan_history = ScanHistory.get_all_by_parent(security_plan.id, security_plan.get_module_string())[0]

            # Verify file was processed and moved
            processed_dir = burp_scan_file.parent / "processed"
            assert processed_dir.exists()
            processed_files = list(processed_dir.glob("*.xml"))
            assert len(processed_files) > 0, "No processed files found"

            assert scan_history.vInfo == 1
            assert scan_history.vLow == 3
            assert scan_history.vMedium == 0
            assert scan_history.vHigh == 0
            assert scan_history.vCritical == 0

        finally:
            for file in processed_files:
                if "burp" in file.name:
                    shutil.move(file, test_data_dir / "burp-scan.xml")
