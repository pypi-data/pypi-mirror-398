#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for AWS Audit Manager datetime parsing and comparison.
Tests that all timestamp formats are properly parsed as timezone-naive UTC datetimes.
"""

import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch
from regscale.integrations.commercial.aws.audit_manager_compliance import AWSAuditManagerCompliance


class TestDateTimeParsing(unittest.TestCase):
    """Test cases for datetime parsing and timezone handling."""

    def setUp(self):
        """Set up test fixtures."""
        self.compliance = AWSAuditManagerCompliance(plan_id=50)

        # Calculate yesterday's date range (same as in the actual code)
        now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
        self.yesterday_start = (now_utc - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        self.yesterday_end = self.yesterday_start + timedelta(days=1)

    def test_parse_iso_format_with_z(self):
        """Test parsing ISO format with Z timezone indicator."""
        timestamp = "2025-11-03T19:00:00Z"
        result = self.compliance._parse_evidence_timestamp(timestamp)

        self.assertIsNotNone(result)
        self.assertIsNone(result.tzinfo, "Result should be timezone-naive")

        # Should be able to compare with naive datetimes
        try:
            _ = self.yesterday_start <= result < self.yesterday_end
            self.assertTrue(True, "Comparison should not raise exception")
        except TypeError:
            self.fail("Should be able to compare naive datetimes")

    def test_parse_iso_format_with_positive_offset(self):
        """Test parsing ISO format with positive timezone offset."""
        timestamp = "2025-11-03T19:00:00+00:00"
        result = self.compliance._parse_evidence_timestamp(timestamp)

        self.assertIsNotNone(result)
        self.assertIsNone(result.tzinfo, "Result should be timezone-naive")

        # Should be able to compare with naive datetimes
        try:
            _ = self.yesterday_start <= result < self.yesterday_end
            self.assertTrue(True, "Comparison should not raise exception")
        except TypeError:
            self.fail("Should be able to compare naive datetimes")

    def test_parse_iso_format_with_negative_offset(self):
        """Test parsing ISO format with negative timezone offset."""
        timestamp = "2025-11-03T19:00:00-05:00"
        result = self.compliance._parse_evidence_timestamp(timestamp)

        self.assertIsNotNone(result)
        self.assertIsNone(result.tzinfo, "Result should be timezone-naive")

        # Time should be converted to UTC (19:00 -05:00 = 00:00 next day UTC)
        expected_utc = datetime(2025, 11, 4, 0, 0, 0)
        self.assertEqual(result, expected_utc)

        # Should be able to compare with naive datetimes
        try:
            _ = self.yesterday_start <= result < self.yesterday_end
            self.assertTrue(True, "Comparison should not raise exception")
        except TypeError:
            self.fail("Should be able to compare naive datetimes")

    def test_parse_space_format_with_offset(self):
        """Test parsing format with space separator and timezone offset."""
        timestamp = "2025-11-03 19:00:00-05:00"
        result = self.compliance._parse_evidence_timestamp(timestamp)

        self.assertIsNotNone(result)
        self.assertIsNone(result.tzinfo, "Result should be timezone-naive")

        # Should be able to compare with naive datetimes
        try:
            _ = self.yesterday_start <= result < self.yesterday_end
            self.assertTrue(True, "Comparison should not raise exception")
        except TypeError:
            self.fail("Should be able to compare naive datetimes")

    def test_parse_simple_format(self):
        """Test parsing simple datetime format without timezone."""
        timestamp = "2025-11-03 19:00:00"
        result = self.compliance._parse_evidence_timestamp(timestamp)

        self.assertIsNotNone(result)
        self.assertIsNone(result.tzinfo, "Result should be timezone-naive")

        # Should be able to compare with naive datetimes
        try:
            _ = self.yesterday_start <= result < self.yesterday_end
            self.assertTrue(True, "Comparison should not raise exception")
        except TypeError:
            self.fail("Should be able to compare naive datetimes")

    def test_parse_with_microseconds(self):
        """Test parsing datetime with microseconds."""
        timestamp = "2025-11-03 19:00:00.123456"
        result = self.compliance._parse_evidence_timestamp(timestamp)

        self.assertIsNotNone(result)
        self.assertIsNone(result.tzinfo, "Result should be timezone-naive")
        self.assertEqual(result.microsecond, 123456)

    def test_parse_datetime_object(self):
        """Test handling datetime object as input."""
        # Test with naive datetime
        dt_naive = datetime(2025, 11, 3, 19, 0, 0)
        result = self.compliance._parse_evidence_timestamp(dt_naive)

        self.assertEqual(result, dt_naive)
        self.assertIsNone(result.tzinfo, "Result should be timezone-naive")

        # Test with aware datetime - should be converted to naive
        dt_aware = datetime(2025, 11, 3, 19, 0, 0, tzinfo=timezone.utc)
        result = self.compliance._parse_evidence_timestamp(dt_aware)

        self.assertIsNotNone(result)
        self.assertIsNone(result.tzinfo, "Result should be timezone-naive after conversion")

    def test_parse_invalid_input(self):
        """Test handling invalid input."""
        # None input
        result = self.compliance._parse_evidence_timestamp(None)
        self.assertIsNone(result)

        # Integer input
        result = self.compliance._parse_evidence_timestamp(12345)
        self.assertIsNone(result)

        # Invalid string format
        result = self.compliance._parse_evidence_timestamp("not-a-date")
        self.assertIsNone(result)

    def test_filter_evidence_by_date(self):
        """Test filtering evidence items by date range."""
        # Create test evidence items with different timestamps
        evidence_items = [
            {"id": "1", "time": "2025-11-03T10:00:00Z"},  # Yesterday morning
            {"id": "2", "time": "2025-11-03T23:59:59Z"},  # Yesterday evening
            {"id": "3", "time": "2025-11-04T00:00:01Z"},  # Today
            {"id": "4", "time": "2025-11-02T23:59:59Z"},  # Day before yesterday
            {"id": "5", "time": None},  # No timestamp
            {"id": "6", "time": "invalid"},  # Invalid timestamp
        ]

        # Set up yesterday's range for Nov 3rd
        yesterday_start = datetime(2025, 11, 3, 0, 0, 0)
        yesterday_end = datetime(2025, 11, 4, 0, 0, 0)

        filtered = self.compliance._filter_evidence_by_date(evidence_items, yesterday_start, yesterday_end)

        # Should only include items 1 and 2 (yesterday's evidence)
        self.assertEqual(len(filtered), 2)
        self.assertEqual(filtered[0]["id"], "1")
        self.assertEqual(filtered[1]["id"], "2")

    def test_filter_evidence_with_timezone_offsets(self):
        """Test filtering evidence with various timezone offsets."""
        evidence_items = [
            {"id": "1", "time": "2025-11-03T05:00:00-05:00"},  # 10:00 UTC - yesterday
            {"id": "2", "time": "2025-11-03T20:00:00+01:00"},  # 19:00 UTC - yesterday
            {"id": "3", "time": "2025-11-04T01:00:00+01:00"},  # 00:00 UTC - today
        ]

        yesterday_start = datetime(2025, 11, 3, 0, 0, 0)
        yesterday_end = datetime(2025, 11, 4, 0, 0, 0)

        filtered = self.compliance._filter_evidence_by_date(evidence_items, yesterday_start, yesterday_end)

        # Items 1 and 2 are in yesterday's range in UTC
        self.assertEqual(len(filtered), 2)
        self.assertEqual(filtered[0]["id"], "1")
        self.assertEqual(filtered[1]["id"], "2")

    @patch("regscale.integrations.commercial.aws.audit_manager_compliance.logger")
    def test_collect_evidence_with_mixed_timestamps(self, mock_logger):
        """Test evidence collection with mixed timestamp formats."""
        # Mock AWS client
        self.compliance.audit_manager_client = MagicMock()

        # Mock response with mixed timestamp formats
        mock_response = {
            "evidence": [
                {"id": "ev-1", "time": "2025-11-03T10:00:00Z"},
                {"id": "ev-2", "time": "2025-11-03T15:00:00-05:00"},  # 20:00 UTC
                {"id": "ev-3", "time": datetime(2025, 11, 3, 18, 0, 0)},  # Naive datetime
                {"id": "ev-4", "time": datetime(2025, 11, 3, 19, 0, 0, tzinfo=timezone.utc)},  # Aware datetime
            ],
            "nextToken": None,
        }

        self.compliance.client = MagicMock()
        self.compliance.client.get_evidence_by_evidence_folder = MagicMock(return_value=mock_response)

        evidence_items = []
        self.compliance._collect_evidence_from_folder(
            assessment_id="test-assessment",
            control_set_id="test-control-set",
            evidence_folder_id="test-folder",
            evidence_items=evidence_items,
        )

        # All evidence items should be collected without errors
        self.assertEqual(len(evidence_items), 4)

        # Verify no TypeError was raised
        self.assertFalse(
            any("can't compare offset-naive and offset-aware" in str(call) for call in mock_logger.error.call_args_list)
        )


if __name__ == "__main__":
    unittest.main()
