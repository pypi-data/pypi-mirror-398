#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Comprehensive unit tests for IssueHandler class."""
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, Mock, patch, call

import pytest

from regscale.core.app.utils.app_utils import get_current_datetime
from regscale.integrations.due_date_handler import DueDateHandler
from regscale.integrations.milestone_manager import MilestoneManager
from regscale.integrations.scanner.cache import IssueCache
from regscale.integrations.scanner.handlers.issue_handler import IssueHandler
from regscale.integrations.scanner.models import IntegrationFinding
from regscale.models import regscale_models
from regscale.utils.threading import ThreadSafeDict


@pytest.fixture
def mock_app():
    """Create mock Application instance."""
    mock = MagicMock()
    mock.config = {
        "azure365AccessToken": "Bearer test-token",
        "issues": {
            "noPastDueDates": True,
            "test_integration": {
                "critical": 15,
                "high": 30,
                "moderate": 60,
                "low": 180,
            },
        },
    }
    return mock


@pytest.fixture
def mock_issue_cache():
    """Create mock IssueCache instance."""
    cache = MagicMock(spec=IssueCache)
    cache.find_existing_for_finding.return_value = None
    return cache


@pytest.fixture
def mock_due_date_handler():
    """Create mock DueDateHandler instance."""
    handler = MagicMock(spec=DueDateHandler)
    handler.calculate_due_date.return_value = "2025-06-01T00:00:00"
    handler._ensure_future_due_date.return_value = "2025-06-01T00:00:00"
    handler.integration_timelines = {
        regscale_models.IssueSeverity.Critical: 30,
        regscale_models.IssueSeverity.High: 60,
        regscale_models.IssueSeverity.Moderate: 120,
        regscale_models.IssueSeverity.Low: 364,
    }
    return handler


@pytest.fixture
def mock_kev_data():
    """Create mock KEV data that behaves like ThreadSafeDict."""
    # ThreadSafeDict is dict-like, so we can use a regular dict
    kev_data = {
        "vulnerabilities": [
            {"cveID": "CVE-2024-1234", "dueDate": "2024-12-31"},
            {"cveID": "CVE-2024-5678", "dueDate": "2025-01-15"},
        ]
    }
    return kev_data


@pytest.fixture
def sample_finding():
    """Create a sample IntegrationFinding for testing."""
    return IntegrationFinding(
        control_labels=["AC-2", "AC-3"],
        title="Test Vulnerability",
        category="Security",
        plugin_name="Test Plugin",
        severity=regscale_models.IssueSeverity.High,
        description="Test description",
        status=regscale_models.IssueStatus.Open,
        external_id="EXT-001",
        plugin_id="PLUGIN-001",
        cve="CVE-2024-1234",
        date_created=get_current_datetime(),
        first_seen=get_current_datetime(),
        last_seen=get_current_datetime(),
        asset_identifier="test-asset-1",
        recommendation_for_mitigation="Apply patch",
        remediation="Update software",
    )


@pytest.fixture
def issue_handler(mock_app, mock_issue_cache, mock_due_date_handler):
    """Create IssueHandler instance with mocked dependencies."""
    with patch("regscale.integrations.scanner.handlers.issue_handler.Application") as mock_app_class:
        mock_app_class.return_value = mock_app
        handler = IssueHandler(
            plan_id=123,
            parent_module="securityplans",
            issue_cache=mock_issue_cache,
            assessor_id="user-001",
            title="Test Integration",
            is_component=False,
            issue_identifier_field="wizId",
            due_date_handler=mock_due_date_handler,
        )
        return handler


class TestIssueHandlerConstructor:
    """Tests for IssueHandler initialization."""

    def test_initialization_with_required_params(self, mock_app, mock_issue_cache):
        """Test initialization with only required parameters."""
        with patch("regscale.integrations.scanner.handlers.issue_handler.Application") as mock_app_class:
            mock_app_class.return_value = mock_app

            handler = IssueHandler(
                plan_id=123,
                parent_module="securityplans",
                issue_cache=mock_issue_cache,
                assessor_id="user-001",
                title="Test Integration",
            )

            assert handler.plan_id == 123
            assert handler.parent_module == "securityplans"
            assert handler.issue_cache == mock_issue_cache
            assert handler.assessor_id == "user-001"
            assert handler.title == "Test Integration"
            assert handler.is_component is False
            assert handler.issue_identifier_field is None
            assert isinstance(handler.due_date_handler, DueDateHandler)
            assert isinstance(handler._kev_data, ThreadSafeDict)
            assert handler._milestone_manager is None
            assert handler._max_poam_id is None

    def test_initialization_with_all_params(self, mock_app, mock_issue_cache, mock_due_date_handler, mock_kev_data):
        """Test initialization with all parameters."""
        with patch("regscale.integrations.scanner.handlers.issue_handler.Application") as mock_app_class:
            mock_app_class.return_value = mock_app

            def get_finding_id(f):
                return f.external_id or "default"

            def get_control_impl(cci):
                return 456

            def determine_org_id(owner_id):
                return 789

            handler = IssueHandler(
                plan_id=123,
                parent_module="components",
                issue_cache=mock_issue_cache,
                assessor_id="user-001",
                title="Test Integration",
                is_component=True,
                issue_identifier_field="wizId",
                due_date_handler=mock_due_date_handler,
                kev_data=mock_kev_data,
                get_finding_identifier=get_finding_id,
                get_control_implementation_id_for_cci=get_control_impl,
                determine_issue_organization_id=determine_org_id,
            )

            assert handler.is_component is True
            assert handler.issue_identifier_field == "wizId"
            assert handler.due_date_handler == mock_due_date_handler
            assert handler._kev_data == mock_kev_data
            assert handler._get_finding_identifier == get_finding_id
            assert handler._get_control_implementation_id_for_cci == get_control_impl
            assert handler._determine_issue_organization_id == determine_org_id

    def test_dedup_stats_initialization(self, issue_handler):
        """Test that deduplication stats are initialized correctly."""
        stats = issue_handler.get_dedup_stats()
        assert stats["new"] == 0
        assert stats["existing"] == 0


class TestCreateOrUpdateIssue:
    """Tests for create_or_update_issue method.

    Note: This method now uses server-side deduplication via UniqueKeyFields.
    Client-side lookups have been removed. Issues are built and returned
    for batch processing, with the server handling create vs update decisions.
    """

    def test_create_new_issue(self, issue_handler, sample_finding, mock_issue_cache):
        """Test building an issue for batch processing."""
        with patch.object(issue_handler, "_build_issue_from_finding") as mock_build:
            mock_result = MagicMock()
            mock_result.id = 0  # New issue
            mock_build.return_value = mock_result

            result = issue_handler.create_or_update_issue(title="Test Issue", finding=sample_finding)

            assert result == mock_result
            mock_build.assert_called_once()

    @patch("regscale.integrations.scanner.handlers.issue_handler.regscale_models.Issue")
    def test_update_existing_issue(self, mock_issue_class, issue_handler, sample_finding, mock_issue_cache):
        """Test that issue is built for batch (server handles update detection)."""
        with patch.object(issue_handler, "_build_issue_from_finding") as mock_build:
            mock_result = MagicMock()
            mock_build.return_value = mock_result

            result = issue_handler.create_or_update_issue(title="Test Issue", finding=sample_finding)

            # Issue is built for batch, server determines if create or update
            assert result == mock_result
            mock_build.assert_called_once()

    def test_thread_safety_with_same_finding_id(self, issue_handler, sample_finding):
        """Test that concurrent requests are handled correctly."""
        call_count = []

        with patch.object(issue_handler, "_build_issue_from_finding") as mock_build:
            mock_build.side_effect = lambda *args, **kwargs: (call_count.append(1), MagicMock())[1]

            threads = []
            for _ in range(5):
                t = threading.Thread(target=issue_handler.create_or_update_issue, args=("Test", sample_finding))
                threads.append(t)
                t.start()

            for t in threads:
                t.join()

            # All threads should have executed
            assert len(call_count) == 5


class TestSetIssueFields:
    """Tests for set_issue_fields method."""

    @patch("regscale.integrations.scanner.handlers.issue_handler.regscale_models.Issue")
    def test_set_all_fields(self, mock_issue_class, issue_handler, sample_finding):
        """Test that all fields are set correctly from finding."""
        issue = regscale_models.Issue()
        sample_finding.vulnerability_id = 789  # Set a valid vulnerability ID

        result = issue_handler.set_issue_fields(issue, sample_finding)

        assert result.title is not None
        assert result.severityLevel == sample_finding.severity
        assert result.vulnerabilityId == 789
        assert result.assetIdentifier == sample_finding.asset_identifier
        assert result.cve == sample_finding.cve
        assert result.description == sample_finding.description

    def test_set_fields_with_kev_lookup(self, issue_handler, sample_finding, mock_kev_data):
        """Test KEV lookup during field setting."""
        issue_handler._kev_data = mock_kev_data
        issue = regscale_models.Issue()
        sample_finding.cve = "CVE-2024-1234"

        result = issue_handler.set_issue_fields(issue, sample_finding)

        assert result.kevList == "Yes"


class TestFindExistingIssue:
    """Tests for find_existing_issue method.

    Note: find_existing_issue is deprecated. Server-side deduplication via
    UniqueKeyFields handles create vs update decisions. These tests verify
    the method returns None as expected.
    """

    def test_find_with_finding_id(self, issue_handler, sample_finding, mock_issue_cache):
        """Test that find_existing_issue returns None (deprecated for server-side deduplication)."""
        result = issue_handler.find_existing_issue(finding=sample_finding)

        # Method is deprecated - always returns None, server handles deduplication
        assert result is None

    def test_find_without_finding_id(self, issue_handler, sample_finding, mock_issue_cache):
        """Test that find_existing_issue returns None without finding ID."""
        result = issue_handler.find_existing_issue(finding=sample_finding)

        # Method is deprecated - always returns None
        assert result is None


class TestBatchCreateIssues:
    """Tests for batch_create_issues method."""

    @patch("regscale.integrations.scanner.handlers.issue_handler.regscale_models.Issue.batch_create")
    def test_batch_create_with_issues(self, mock_batch_create, issue_handler):
        """Test batch creating multiple issues."""
        issues = [MagicMock(spec=regscale_models.Issue) for _ in range(5)]
        mock_batch_create.return_value = issues

        result = issue_handler.batch_create_issues(issues)

        assert result == issues
        mock_batch_create.assert_called_once_with(issues)

    @patch("regscale.integrations.scanner.handlers.issue_handler.regscale_models.Issue.batch_create")
    def test_batch_create_with_empty_list(self, mock_batch_create, issue_handler):
        """Test batch create with empty list returns empty list."""
        result = issue_handler.batch_create_issues([])

        assert result == []
        mock_batch_create.assert_not_called()


class TestBuildIssueFromFinding:
    """Tests for _build_issue_from_finding method.

    Note: This method was renamed from _create_or_update_issue to reflect
    that it now only builds the issue object. Server handles create vs update.
    """

    @patch("regscale.integrations.scanner.handlers.issue_handler.regscale_models.Issue")
    def test_build_new_issue(self, mock_issue_class, issue_handler, sample_finding):
        """Test building an issue from a finding."""
        mock_issue = MagicMock()
        mock_issue.id = 0  # New issue
        mock_issue_class.return_value = mock_issue

        result = issue_handler._build_issue_from_finding(
            finding=sample_finding,
            issue_status=regscale_models.IssueStatus.Open,
            title="Test Issue",
        )

        assert result is not None
        # Issue is built but not saved - batch operations handle persistence

    @patch("regscale.integrations.scanner.handlers.issue_handler.regscale_models.Issue")
    def test_build_issue_with_all_fields(self, mock_issue_class, issue_handler, sample_finding):
        """Test that issue is built with all required fields."""
        mock_issue = MagicMock()
        mock_issue_class.return_value = mock_issue

        result = issue_handler._build_issue_from_finding(
            finding=sample_finding,
            issue_status=regscale_models.IssueStatus.Open,
            title="Test Issue",
        )

        # Verify set_issue_fields was called by checking the result
        assert result is not None


class TestSetBasicIssueFields:
    """Tests for _set_basic_issue_fields method."""

    def test_set_all_basic_fields(self, issue_handler, sample_finding):
        """Test setting all basic issue fields."""
        issue = regscale_models.Issue()

        issue_handler._set_basic_issue_fields(
            issue=issue,
            finding=sample_finding,
            issue_status=regscale_models.IssueStatus.Open,
            issue_title="Test Title",
            asset_identifier="test-asset",
        )

        assert issue.parentId == 123
        assert issue.parentModule == "securityplans"
        assert issue.title == "Test Title"
        assert issue.status == regscale_models.IssueStatus.Open
        assert issue.severityLevel == sample_finding.severity
        assert issue.issueOwnerId == "user-001"
        assert issue.assetIdentifier == "test-asset"

    def test_vulnerability_id_only_set_when_valid(self, issue_handler, sample_finding):
        """Test that vulnerabilityId is only set when > 0."""
        issue = regscale_models.Issue()
        sample_finding.vulnerability_id = 0

        issue_handler._set_basic_issue_fields(
            issue=issue,
            finding=sample_finding,
            issue_status=regscale_models.IssueStatus.Open,
            issue_title="Test",
            asset_identifier="test",
        )

        assert not hasattr(issue, "vulnerabilityId") or issue.vulnerabilityId is None

        # Now with valid ID
        sample_finding.vulnerability_id = 789
        issue_handler._set_basic_issue_fields(
            issue=issue,
            finding=sample_finding,
            issue_status=regscale_models.IssueStatus.Open,
            issue_title="Test",
            asset_identifier="test",
        )

        assert issue.vulnerabilityId == 789

    def test_organization_id_callback(self, issue_handler, sample_finding):
        """Test organization ID determination via callback."""

        def determine_org_id(owner_id):  # noqa: ARG001
            return 999

        issue_handler._determine_issue_organization_id = determine_org_id

        issue = regscale_models.Issue()
        issue_handler._set_basic_issue_fields(
            issue=issue,
            finding=sample_finding,
            issue_status=regscale_models.IssueStatus.Open,
            issue_title="Test",
            asset_identifier="test",
        )

        assert issue.orgId == 999


class TestSetIssueDueDate:
    """Tests for _set_issue_due_date method."""

    def test_calculate_new_due_date(self, issue_handler, sample_finding, mock_due_date_handler):
        """Test calculating new due date when not provided."""
        sample_finding.due_date = ""
        issue = regscale_models.Issue()

        issue_handler._set_issue_due_date(issue, sample_finding)

        mock_due_date_handler.calculate_due_date.assert_called_once()
        assert issue.dueDate == "2025-06-01T00:00:00"

    def test_validate_existing_due_date(self, issue_handler, sample_finding, mock_due_date_handler):
        """Test validating existing due date."""
        sample_finding.due_date = "2025-01-15T00:00:00"
        issue = regscale_models.Issue()

        issue_handler._set_issue_due_date(issue, sample_finding)

        mock_due_date_handler._ensure_future_due_date.assert_called_once()
        assert issue.dueDate == "2025-06-01T00:00:00"

    def test_fallback_on_calculation_error(self, issue_handler, sample_finding, mock_due_date_handler):
        """Test fallback when due date calculation fails."""
        sample_finding.due_date = ""
        issue = regscale_models.Issue()
        mock_due_date_handler.calculate_due_date.side_effect = [Exception("Test error"), "2025-07-01T00:00:00"]

        issue_handler._set_issue_due_date(issue, sample_finding)

        # Should call twice: first fails, second succeeds with Low severity
        assert mock_due_date_handler.calculate_due_date.call_count == 2
        assert issue.dueDate == "2025-07-01T00:00:00"


class TestSetControlFields:
    """Tests for _set_control_fields method."""

    def test_set_control_fields_with_cci(self, issue_handler, sample_finding):
        """Test setting control fields with CCI reference."""

        def get_control_impl(cci):  # noqa: ARG001
            return 456

        issue_handler._get_control_implementation_id_for_cci = get_control_impl
        sample_finding.cci_ref = "CCI-001234"
        sample_finding._control_implementation_ids = [123]

        issue = regscale_models.Issue()
        issue_handler._set_control_fields(issue, sample_finding)

        assert 456 in issue.controlImplementationIds
        assert 123 in issue.controlImplementationIds

    def test_set_affected_controls_from_labels(self, issue_handler, sample_finding):
        """Test setting affected controls from control labels."""
        sample_finding.control_labels = ["AC-2", "AC-3", "AC-4"]
        sample_finding.affected_controls = None

        issue = regscale_models.Issue()
        issue_handler._set_control_fields(issue, sample_finding)

        assert "AC-2" in issue.affectedControls
        assert "AC-3" in issue.affectedControls
        assert "AC-4" in issue.affectedControls

    def test_use_existing_affected_controls(self, issue_handler, sample_finding):
        """Test using existing affected_controls field."""
        sample_finding.affected_controls = "AC-2, AC-3"
        sample_finding.control_labels = ["AC-4"]

        issue = regscale_models.Issue()
        issue_handler._set_control_fields(issue, sample_finding)

        assert issue.affectedControls == "AC-2, AC-3"


class TestSaveOrCreateIssue:
    """Tests for _save_or_create_issue method.

    Note: This method is deprecated. Server-side batch operations now handle
    creating and updating issues. The method now just logs a warning and
    returns the issue unchanged.
    """

    @patch("regscale.integrations.scanner.handlers.issue_handler.regscale_models.Property")
    def test_save_existing_issue(self, mock_property, issue_handler, sample_finding):  # noqa: ARG001
        """Test that deprecated method returns issue unchanged."""
        existing_issue = MagicMock()
        existing_issue.id = 456
        issue = existing_issue

        result = issue_handler._save_or_create_issue(issue, sample_finding)

        # Deprecated method returns issue unchanged
        assert result == issue
        # No save call - batch operations handle persistence
        existing_issue.save.assert_not_called()

    def test_create_new_issue(self, issue_handler, sample_finding):
        """Test that deprecated method returns issue unchanged for new issues."""
        issue = MagicMock()
        issue.id = 0

        result = issue_handler._save_or_create_issue(issue, sample_finding)

        # Deprecated method returns issue unchanged
        assert result == issue
        # No create_or_update call - batch operations handle persistence
        issue.create_or_update.assert_not_called()

    def test_create_new_issue_with_poam_id(self, issue_handler, sample_finding):
        """Test deprecated method with POAM ID - returns issue unchanged."""
        issue = MagicMock()
        issue.id = 0
        sample_finding.poam_id = None

        result = issue_handler._save_or_create_issue(issue, sample_finding)

        # Deprecated method returns issue unchanged
        assert result == issue


class TestKEVLookup:
    """Tests for KEV lookup functionality."""

    def test_kev_found(self, issue_handler, mock_kev_data):
        """Test KEV found in data."""
        issue_handler._kev_data = mock_kev_data
        issue = regscale_models.Issue()

        result = issue_handler._lookup_kev_and_update_issue(cve="CVE-2024-1234", issue=issue)

        assert result.kevList == "Yes"

    def test_kev_not_found(self, issue_handler, mock_kev_data):
        """Test KEV not found in data."""
        issue_handler._kev_data = mock_kev_data
        issue = regscale_models.Issue()

        result = issue_handler._lookup_kev_and_update_issue(cve="CVE-9999-9999", issue=issue)

        assert result.kevList == "No"

    def test_kev_case_insensitive(self, issue_handler, mock_kev_data):
        """Test KEV lookup is case insensitive."""
        issue_handler._kev_data = mock_kev_data
        issue = regscale_models.Issue()

        result = issue_handler._lookup_kev_and_update_issue(cve="cve-2024-1234", issue=issue)

        assert result.kevList == "Yes"

    def test_kev_no_data(self, issue_handler):
        """Test KEV lookup with no data."""
        issue_handler._kev_data = None
        issue = regscale_models.Issue()

        result = issue_handler._lookup_kev_and_update_issue(cve="CVE-2024-1234", issue=issue)

        assert result.kevList == "No"


class TestMilestoneCreation:
    """Tests for milestone creation functionality."""

    def test_get_milestone_manager_lazy_init(self, issue_handler):
        """Test lazy initialization of milestone manager."""
        assert issue_handler._milestone_manager is None

        manager = issue_handler.get_milestone_manager()

        assert manager is not None
        assert isinstance(manager, MilestoneManager)
        assert manager.integration_title == "Test Integration"
        assert manager.assessor_id == "user-001"

    def test_get_milestone_manager_reuses_instance(self, issue_handler):
        """Test that milestone manager is reused."""
        manager1 = issue_handler.get_milestone_manager()
        manager2 = issue_handler.get_milestone_manager()

        assert manager1 is manager2

    def test_set_scan_date(self, issue_handler):
        """Test setting scan date."""
        issue_handler.set_scan_date("2024-12-01T00:00:00")

        assert issue_handler._scan_date == "2024-12-01T00:00:00"


class TestPOAMDetermination:
    """Tests for POAM determination logic."""

    @patch("regscale.integrations.scanner.handlers.issue_handler.ScannerVariables")
    @patch("regscale.integrations.scanner.handlers.issue_handler.get_current_datetime")
    def test_poam_by_vulnerability_creation_setting(self, mock_datetime, mock_vars, issue_handler, sample_finding):
        """Test POAM determination by vulnerabilityCreation setting."""
        mock_vars.vulnerabilityCreation.lower.return_value = "poamcreation"
        mock_vars.complianceCreation.lower.return_value = "assessment"
        mock_datetime.return_value = "2024-12-01T00:00:00"
        sample_finding.due_date = "2025-12-01T00:00:00"

        result = issue_handler._is_poam(sample_finding)

        assert result is True

    @patch("regscale.integrations.scanner.handlers.issue_handler.ScannerVariables")
    @patch("regscale.integrations.scanner.handlers.issue_handler.get_current_datetime")
    def test_poam_by_compliance_creation_setting(self, mock_datetime, mock_vars, issue_handler, sample_finding):
        """Test POAM determination by complianceCreation setting."""
        mock_vars.vulnerabilityCreation.lower.return_value = "issuecreation"
        mock_vars.complianceCreation.lower.return_value = "poam"
        mock_datetime.return_value = "2024-12-01T00:00:00"
        sample_finding.due_date = "2025-12-01T00:00:00"

        result = issue_handler._is_poam(sample_finding)

        assert result is True

    @patch("regscale.integrations.scanner.handlers.issue_handler.ScannerVariables")
    @patch("regscale.integrations.scanner.handlers.issue_handler.get_current_datetime")
    def test_poam_by_past_due_date(self, mock_datetime, mock_vars, issue_handler, sample_finding):
        """Test POAM determination by past due date."""
        mock_vars.vulnerabilityCreation.lower.return_value = "issuecreation"
        mock_vars.complianceCreation.lower.return_value = "assessment"
        mock_datetime.return_value = "2025-12-01T00:00:00"
        sample_finding.due_date = "2024-06-01T00:00:00"

        result = issue_handler._is_poam(sample_finding)

        assert result is True

    @patch("regscale.integrations.scanner.handlers.issue_handler.ScannerVariables")
    @patch("regscale.integrations.scanner.handlers.issue_handler.get_current_datetime")
    def test_not_poam(self, mock_datetime, mock_vars, issue_handler, sample_finding):
        """Test when issue is not a POAM."""
        mock_vars.vulnerabilityCreation.lower.return_value = "issuecreation"
        mock_vars.complianceCreation.lower.return_value = "assessment"
        mock_datetime.return_value = "2024-12-01T00:00:00"
        sample_finding.due_date = "2025-12-01T00:00:00"

        result = issue_handler._is_poam(sample_finding)

        assert result is False


class TestDedupStatistics:
    """Tests for deduplication statistics."""

    def test_get_dedup_stats(self, issue_handler):
        """Test getting deduplication stats."""
        stats = issue_handler.get_dedup_stats()

        assert isinstance(stats, dict)
        assert "new" in stats
        assert "existing" in stats
        assert stats["new"] == 0
        assert stats["existing"] == 0

    def test_reset_dedup_stats(self, issue_handler):
        """Test resetting deduplication stats."""
        # Manually set some stats
        issue_handler._dedup_stats["new"] = 5
        issue_handler._dedup_stats["existing"] = 10

        issue_handler.reset_dedup_stats()

        stats = issue_handler.get_dedup_stats()
        assert stats["new"] == 0
        assert stats["existing"] == 0

    def test_dedup_stats_thread_safety(self, issue_handler):
        """Test that dedup stats are thread-safe."""

        def increment_stats():
            for _ in range(100):
                with issue_handler._dedup_lock:
                    issue_handler._dedup_stats["new"] += 1

        threads = []
        for _ in range(10):
            t = threading.Thread(target=increment_stats)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        stats = issue_handler.get_dedup_stats()
        assert stats["new"] == 1000  # 10 threads * 100 increments


class TestHelperMethods:
    """Tests for helper methods."""

    def test_get_finding_id_with_callback(self, issue_handler, sample_finding):
        """Test getting finding ID with callback."""

        def get_finding_id(f):
            return f"custom-{f.external_id}"

        issue_handler._get_finding_identifier = get_finding_id

        result = issue_handler._get_finding_id(sample_finding)

        assert result == "custom-EXT-001"

    def test_get_finding_id_without_callback(self, issue_handler, sample_finding):
        """Test getting finding ID without callback."""
        issue_handler._get_finding_identifier = None

        result = issue_handler._get_finding_id(sample_finding)

        assert result == "EXT-001"

    def test_get_finding_id_fallback_to_plugin_title(self, issue_handler, sample_finding):
        """Test getting finding ID falls back to plugin_id:title."""
        issue_handler._get_finding_identifier = None
        sample_finding.external_id = ""

        result = issue_handler._get_finding_id(sample_finding)

        assert result == "PLUGIN-001:Test Vulnerability"

    @patch("regscale.integrations.scanner.handlers.issue_handler.ScannerVariables")
    def test_get_issue_title_by_plugin_id(self, mock_vars, issue_handler, sample_finding):
        """Test getting issue title by plugin ID."""
        mock_vars.poamTitleType.lower.return_value = "pluginid"

        result = issue_handler._get_issue_title(sample_finding)

        assert "PLUGIN-001" in result
        assert "Test Plugin" in result

    @patch("regscale.integrations.scanner.handlers.issue_handler.ScannerVariables")
    def test_get_issue_title_by_cve(self, mock_vars, issue_handler, sample_finding):
        """Test getting issue title by CVE (default)."""
        mock_vars.poamTitleType.lower.return_value = "cve"

        result = issue_handler._get_issue_title(sample_finding)

        assert result == "Test Vulnerability"

    def test_get_issue_title_truncation(self, issue_handler, sample_finding):
        """Test issue title is truncated to 450 characters."""
        sample_finding.title = "A" * 500

        result = issue_handler._get_issue_title(sample_finding)

        assert len(result) == 450

    def test_parse_poam_id_with_prefix(self, issue_handler):
        """Test parsing POAM ID with V- prefix."""
        result = issue_handler._parse_poam_id("V-0042")

        assert result == 42

    def test_parse_poam_id_without_prefix(self, issue_handler):
        """Test parsing POAM ID without prefix."""
        result = issue_handler._parse_poam_id("0123")

        assert result == 123

    def test_parse_poam_id_invalid(self, issue_handler):
        """Test parsing invalid POAM ID."""
        result = issue_handler._parse_poam_id("INVALID")

        assert result is None

    def test_get_next_poam_id(self, issue_handler):
        """Test getting next POAM ID."""
        assert issue_handler._max_poam_id is None

        result1 = issue_handler._get_next_poam_id()
        assert result1 == 1

        result2 = issue_handler._get_next_poam_id()
        assert result2 == 2

        result3 = issue_handler._get_next_poam_id()
        assert result3 == 3

    @patch("regscale.integrations.scanner.handlers.issue_handler.ScannerVariables")
    def test_get_consolidated_asset_identifier_per_asset(self, mock_vars, sample_finding):
        """Test consolidated asset identifier in per-asset mode."""
        mock_vars.issueCreation.lower.return_value = "perasset"

        result = IssueHandler._get_consolidated_asset_identifier(sample_finding, None)

        assert result == "test-asset-1"

    @patch("regscale.integrations.scanner.handlers.issue_handler.ScannerVariables")
    def test_get_consolidated_asset_identifier_consolidated_new(self, mock_vars, sample_finding):
        """Test consolidated asset identifier for new issue."""
        mock_vars.issueCreation.lower.return_value = "consolidated"

        result = IssueHandler._get_consolidated_asset_identifier(sample_finding, None)

        assert result == "test-asset-1"

    @patch("regscale.integrations.scanner.handlers.issue_handler.ScannerVariables")
    def test_get_consolidated_asset_identifier_consolidated_existing(self, mock_vars, sample_finding):
        """Test consolidated asset identifier - now returns finding's asset only.

        Note: Server-side deduplication handles asset consolidation now.
        The method no longer merges existing issue assets with new finding assets.
        """
        mock_vars.issueCreation.lower.return_value = "consolidated"
        existing_issue = MagicMock()
        existing_issue.assetIdentifier = "asset-1\nasset-2"

        result = IssueHandler._get_consolidated_asset_identifier(sample_finding, existing_issue)

        # Now only returns the finding's asset identifier
        assert "test-asset-1" in result
        # Existing assets are not merged - server handles consolidation
        # This is by design for server-side deduplication


class TestPropertyCreation:
    """Tests for property creation functionality."""

    @patch("regscale.integrations.scanner.handlers.issue_handler.regscale_models.Property")
    def test_create_poc_property(self, mock_property_class, issue_handler, sample_finding):
        """Test creating POC property."""
        mock_property = MagicMock()
        mock_property_class.return_value = mock_property
        sample_finding.point_of_contact = "John Doe"

        issue = MagicMock()
        issue.id = 999

        issue_handler._create_issue_properties(issue, sample_finding)

        mock_property_class.assert_called_once()
        mock_property.create_or_update.assert_called_once()

    @patch("regscale.integrations.scanner.handlers.issue_handler.regscale_models.Property")
    def test_create_cwe_property(self, mock_property_class, issue_handler, sample_finding):
        """Test creating CWE property."""
        mock_property = MagicMock()
        mock_property_class.return_value = mock_property
        sample_finding.is_cwe = True
        sample_finding.plugin_id = "CWE-79"

        issue = MagicMock()
        issue.id = 999

        issue_handler._create_issue_properties(issue, sample_finding)

        mock_property_class.assert_called_once()
        mock_property.create_or_update.assert_called_once()

    @patch("regscale.integrations.scanner.handlers.issue_handler.regscale_models.Property")
    def test_skip_property_creation_for_bulk_issue(self, mock_property_class, issue_handler, sample_finding):
        """Test property creation is skipped for issues pending bulk save."""
        sample_finding.point_of_contact = "John Doe"

        issue = MagicMock()
        issue.id = 0  # Pending bulk save

        issue_handler._create_issue_properties(issue, sample_finding)

        mock_property_class.assert_not_called()


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_closed_issue_creation(self, issue_handler, sample_finding):
        """Test creating a closed issue."""
        sample_finding.status = regscale_models.ControlTestResultStatus.PASS

        issue_status = sample_finding.get_issue_status()

        assert issue_status == regscale_models.IssueStatus.Closed

    def test_empty_external_id(self, issue_handler, sample_finding):
        """Test handling empty external ID."""
        sample_finding.external_id = ""

        finding_id = issue_handler._get_finding_id(sample_finding)

        assert finding_id == "PLUGIN-001:Test Vulnerability"

    def test_none_vulnerability_id(self, issue_handler, sample_finding):
        """Test handling None vulnerability ID."""
        sample_finding.vulnerability_id = None
        issue = regscale_models.Issue()

        issue_handler._set_basic_issue_fields(
            issue=issue,
            finding=sample_finding,
            issue_status=regscale_models.IssueStatus.Open,
            issue_title="Test",
            asset_identifier="test",
        )

        # Should not set vulnerabilityId
        assert not hasattr(issue, "vulnerabilityId") or issue.vulnerabilityId is None

    def test_missing_callbacks(self, issue_handler, sample_finding):
        """Test graceful handling when callbacks are not provided."""
        issue_handler._get_finding_identifier = None
        issue_handler._get_control_implementation_id_for_cci = None
        issue_handler._determine_issue_organization_id = None

        issue = regscale_models.Issue()

        # Should not raise errors
        issue_handler._set_basic_issue_fields(
            issue=issue,
            finding=sample_finding,
            issue_status=regscale_models.IssueStatus.Open,
            issue_title="Test",
            asset_identifier="test",
        )

        issue_handler._set_control_fields(issue, sample_finding)

    @patch("regscale.integrations.scanner.handlers.issue_handler.regscale_models.Property")
    def test_property_creation_error_handling(self, mock_property_class, issue_handler, sample_finding):
        """Test error handling during property creation."""
        mock_property = MagicMock()
        mock_property.create_or_update.side_effect = Exception("API Error")
        mock_property_class.return_value = mock_property

        sample_finding.point_of_contact = "John Doe"
        issue = MagicMock()
        issue.id = 999

        # Should log warning but not raise exception
        issue_handler._create_issue_properties(issue, sample_finding)

        mock_property.create_or_update.assert_called_once()

    def test_thread_safe_lock_registry(self, issue_handler):
        """Test thread-safe lock registry."""

        def get_locks():
            for i in range(100):
                lock = issue_handler._get_lock(f"key-{i % 10}")
                assert lock is not None

        threads = []
        for _ in range(10):
            t = threading.Thread(target=get_locks)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Should have created 10 unique locks
        assert len(issue_handler._lock_registry) == 10
