#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test CISA Integrations"""

from datetime import datetime
from unittest import TestCase
from unittest.mock import MagicMock, patch
from urllib.error import URLError
import dateutil.parser as dparser
from requests.exceptions import RequestException

from bs4 import Tag, BeautifulSoup
import pytest
from regscale.integrations.public.cisa import (
    build_threat,
    convert_date_string,
    filter_elements,
    fuzzy_find_date,
    gen_soup,
    insert_or_upd_threat,
    is_url,
    merge_old,
    parse_html,
    process_element,
    process_params,
    process_threats,
    unique,
    update_regscale_links,
    alerts,
    parse_details,
    pull_cisa_kev,
    update_regscale,
    update_regscale_threats,
)
from regscale.models import Threat, Link
from regscale.core.app.application import Application
from tests import CLITestFixture


class TestCisa(CLITestFixture, TestCase):
    """Test CISA Integrations"""

    @patch("regscale.integrations.public.cisa.Link.batch_update", return_value=None)
    def test_update_regscale_links_no_threats(self, mock_batch_update):
        """Test update_regscale_links function with no threats"""
        threats = []
        update_regscale_links(threats)
        mock_batch_update.assert_called_once_with(threats)

    @patch("regscale.integrations.public.cisa.Link.batch_update", return_value=None)
    def test_update_regscale_links(self, mock_batch_update):
        """Test update_regscale_links function"""
        threats = [
            Threat(
                id=1,
                threatType="Vulnerability",
                status="Under Investigation",
                source="Open Source",
                title="Threat 1",
                targetType="Target Type",
                description="Description https://example.com",
            )
        ]
        links = [Link(parentID=1, parentModule="threats", url="https://example.com", title="Threat 1")]

        update_regscale_links(threats)
        mock_batch_update.assert_called_once_with(links)

    def test_process_threats_without_threats(self):
        """Test process_threats with no threats"""
        threats = []
        unique_threats = set()
        reg_threats = []
        insert_threats, update_threats = process_threats(threats, unique_threats, reg_threats)
        assert insert_threats == []
        assert update_threats == []

    def test_process_threats_insert(self):
        """Test process_threats with insertions"""
        threats = [
            Threat(
                id=1,
                threatType="Vulnerability",
                status="Under Investigation",
                source="Open Source",
                title="Threat 1",
            )
        ]
        unique_threats = set()
        reg_threats = []
        insert_threats, update_threats = process_threats(threats, unique_threats, reg_threats)
        assert insert_threats == [threats[0].dict()]
        assert update_threats == []

    def test_process_threats_update(self):
        """Test process_threats with updates"""
        threats = [
            Threat(
                id=1,
                threatType="Vulnerability",
                status="Closed",
                source="Open Source",
                title="Threat 1",
                description="Description https://example.com",
            )
        ]
        unique_threats = set(["Description https://example.com"])
        reg_threats = [
            Threat(
                id=1,
                threatType="Vulnerability",
                status="Under Investigation",
                source="Open Source",
                title="Threat 1",
                description="Description https://example.com",
            )
        ]
        insert_threats, update_threats = process_threats(threats, unique_threats, reg_threats)
        assert insert_threats == []
        assert update_threats == [reg_threats[0].dict()]

    @patch("regscale.integrations.public.cisa.parse_details")
    def test_build_empty_threat(self, mock_parse_details):
        """Test build_threat function with empty threat"""
        mock_parse_details.return_value = None
        app = MagicMock()
        threat = build_threat(app, "https://example.com", "Description https://example.com", "Threat 1")
        assert threat is None

    @patch("regscale.integrations.public.cisa.parse_details")
    @patch("regscale.integrations.public.cisa.Threat")
    def test_build_threat(self, mock_threat_class, mock_parse_details):
        """Test build_threat function"""
        app = MagicMock()
        app.config = {"userId": "1"}

        mock_threat_instance = MagicMock()
        mock_threat_class.return_value = mock_threat_instance
        mock_threat_class.xstr.return_value = ""

        dat = (
            "2025-05-26",
            ["Vulnerability 1"],
            ["Mitigation 1"],
            ["Note 1"],
        )
        mock_parse_details.return_value = dat

        threat = build_threat(app, "https://example.com", "Description https://example.com", "Threat 1")

        mock_threat_class.assert_called_once_with(
            uuid=Threat.xstr(None),
            title="Threat 1",
            threatType="Specific",
            threatOwnerId="1",
            dateIdentified="2025-05-26",
            targetType="Other",
            source="Open Source",
            description="Description https://example.com",
            vulnerabilityAnalysis="Vulnerability 1",
            mitigations="Mitigation 1",
            notes="Note 1",
            dateCreated="2025-05-26",
            status="Initial Report/Notification",
        )

        assert threat is not None
        assert threat == mock_threat_instance

    def test_filter_elements_filter_list(self):
        """Test filter_elements function blocked by filter list"""
        filter_list = [
            "c-figure__media",
            "c-product-survey__text-area",
            "l-full__footer",
            "usa-navbar",
        ]
        for cls in filter_list:
            element = Tag(name="p", attrs={"class": [cls]})
            assert filter_elements(element) is None

    def test_filter_elements_tags(self):
        """Test filter_elements function"""
        tags = ["p", "li", "div", "table"]
        for tag in tags:
            element = Tag(name=tag)
            assert filter_elements(element) == element

    def test_filter_elements_bad_tag(self):
        """Test filter_elements function with bad tag"""
        element = Tag(name="h1")  # tag not in list
        assert filter_elements(element) is None

    def test_process_params_filtered_element(self):
        """Test process_params function with filtered element"""
        element = Tag(name="p", attrs={"class": ["c-figure__media"]})
        vulnerability, mitigation, notes = process_params(element, "", [], [], [])
        assert vulnerability == []
        assert mitigation == []
        assert notes == []

    def test_process_params_summary(self):
        """Test process_params function with summary"""
        element = Tag(name="p")
        element.string = "Lorem ipsum or something"

        # check summary is appended to notes
        vulnerability, mitigation, notes = process_params(element, "summary", [], [], [])
        assert vulnerability == []
        assert mitigation == []
        assert notes == ["<p>Lorem ipsum or something</p>"]

        # check summary is not appended to notes if already in notes
        vulnerability, mitigation, notes = process_params(element, "summary", [], [], notes)
        assert vulnerability == []
        assert mitigation == []
        assert notes == ["<p>Lorem ipsum or something</p>"]

    def test_process_params_vulnerability(self):
        """Test process_params function with vulnerability"""
        element = Tag(name="p")
        element.string = "Lorem ipsum or something"

        # check vulnerability is appended to vulnerability
        vulnerability, mitigation, notes = process_params(element, "technical details", [], [], [])
        assert vulnerability == ["<p>Lorem ipsum or something</p>"]
        assert mitigation == []
        assert notes == []

        # check vulnerability is not appended to vulnerability if already in vulnerability
        vulnerability, mitigation, notes = process_params(element, "technical details", vulnerability, [], [])
        assert vulnerability == ["<p>Lorem ipsum or something</p>"]
        assert mitigation == []
        assert notes == []

    def test_process_params_mitigation(self):
        """Test process_params function with mitigation"""
        element = Tag(name="p")
        element.string = "Lorem ipsum or something"

        # check mitigation is appended to mitigation
        vulnerability, mitigation, notes = process_params(element, "mitigations", [], [], [])
        assert vulnerability == []
        assert mitigation == ["<p>Lorem ipsum or something</p>"]
        assert notes == []

        # check mitigation is not appended to mitigation if already in mitigation
        vulnerability, mitigation, notes = process_params(element, "mitigations", [], mitigation, [])
        assert vulnerability == []
        assert mitigation == ["<p>Lorem ipsum or something</p>"]
        assert notes == []

    def test_process_element_basic_non_header(self):
        """Test process_element with a basic non-header element"""
        dat = Tag(name="p")
        dat.string = "Some content"
        last_header = {"type": "h2", "title": "Previous Header"}
        last_h3 = "Previous H3"
        nav_string = "technical details"
        div_list = ["technical details", "mitigations", "summary"]
        args = (
            dat,
            last_header,
            last_h3,
            nav_string,
            div_list,
            [],  # vulnerability
            [],  # mitigation
            [],  # notes
        )
        new_last_header, new_last_h3, new_nav_string = process_element(args)
        assert new_last_header == last_header
        assert new_last_h3 == last_h3
        assert new_nav_string == nav_string

    def test_process_element_header_update(self):
        """Test process_element updates headers for h1-h6 elements"""
        for header_type in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            dat = Tag(name=header_type)
            dat.string = f"New {header_type} Header"
            last_header = {"type": "h2", "title": "Previous Header"}
            last_h3 = "Previous H3"
            args = (
                dat,
                last_header,
                last_h3,
                "",  # nav_string
                [],  # div_list
                [],  # vulnerability
                [],  # mitigation
                [],  # notes
            )
            new_last_header, new_last_h3, new_nav_string = process_element(args)
            assert new_last_header == {"type": header_type, "title": f"New {header_type} Header"}
            # Only h3 should update last_h3
            assert new_last_h3 == (f"New {header_type} Header" if header_type == "h3" else last_h3)
            assert new_nav_string == ""

    def test_process_element_nav_string_update(self):
        """Test process_element updates nav_string when text matches div_list"""
        div_list = ["technical details", "mitigations", "summary"]
        for nav_text in div_list:
            dat = Tag(name="p")
            dat.string = nav_text
            last_header = {"type": "h2", "title": "Some Header"}
            last_h3 = "Some H3"
            args = (
                dat,
                last_header,
                last_h3,
                "",  # nav_string
                div_list,
                [],  # vulnerability
                [],  # mitigation
                [],  # notes
            )
            new_last_header, new_last_h3, new_nav_string = process_element(args)
            assert new_last_header == last_header
            assert new_last_h3 == last_h3
            assert new_nav_string == nav_text

    def test_process_element_process_params_conditions(self):
        """Test process_element calls process_params when all conditions are met"""
        dat = Tag(name="p")
        dat.string = "Content to process"
        last_header = {"type": "h2", "title": "Some Header"}
        last_h3 = "technical details"  # matches div_list
        nav_string = "technical details"  # matches div_list
        div_list = ["technical details", "mitigations", "summary"]
        vulnerability = []
        mitigation = []
        notes = []
        args = (
            dat,
            last_header,
            last_h3,
            nav_string,
            div_list,
            vulnerability,
            mitigation,
            notes,
        )
        with patch("regscale.integrations.public.cisa.process_params") as mock_process_params:
            new_last_header, new_last_h3, new_nav_string = process_element(args)
            mock_process_params.assert_called_once_with(dat, nav_string, vulnerability, mitigation, notes)
            assert new_last_header == last_header
            assert new_last_h3 == last_h3
            assert new_nav_string == nav_string

    def test_process_element_no_process_params_missing_last_h3(self):
        """Test process_element doesn't call process_params when last_h3 is missing"""
        dat = Tag(name="p")
        dat.string = "Content to process"
        last_header = {"type": "h2", "title": "Some Header"}
        last_h3 = None  # Missing last_h3
        nav_string = "technical details"
        div_list = ["technical details", "mitigations", "summary"]
        args = (
            dat,
            last_header,
            last_h3,
            nav_string,
            div_list,
            [],  # vulnerability
            [],  # mitigation
            [],  # notes
        )
        with patch("regscale.integrations.public.cisa.process_params") as mock_process_params:
            new_last_header, new_last_h3, new_nav_string = process_element(args)
            mock_process_params.assert_not_called()
            assert new_last_header == last_header
            assert new_last_h3 == last_h3
            assert new_nav_string == nav_string

    def test_process_element_no_process_params_missing_nav_string(self):
        """Test process_element doesn't call process_params when nav_string is missing"""
        dat = Tag(name="p")
        dat.string = "Content to process"
        last_header = {"type": "h2", "title": "Some Header"}
        last_h3 = "technical details"
        nav_string = ""  # Missing nav_string
        div_list = ["technical details", "mitigations", "summary"]
        args = (
            dat,
            last_header,
            last_h3,
            nav_string,
            div_list,
            [],  # vulnerability
            [],  # mitigation
            [],  # notes
        )
        with patch("regscale.integrations.public.cisa.process_params") as mock_process_params:
            new_last_header, new_last_h3, new_nav_string = process_element(args)
            mock_process_params.assert_not_called()
            assert new_last_header == last_header
            assert new_last_h3 == last_h3
            assert new_nav_string == nav_string

    def test_process_element_no_process_params_h3_not_in_div_list(self):
        """Test process_element doesn't call process_params when last_h3 doesn't match div_list"""
        dat = Tag(name="p")
        dat.string = "Content to process"
        last_header = {"type": "h2", "title": "Some Header"}
        last_h3 = "unmatched h3"  # Doesn't match div_list
        nav_string = "technical details"
        div_list = ["technical details", "mitigations", "summary"]
        args = (
            dat,
            last_header,
            last_h3,
            nav_string,
            div_list,
            [],  # vulnerability
            [],  # mitigation
            [],  # notes
        )
        with patch("regscale.integrations.public.cisa.process_params") as mock_process_params:
            new_last_header, new_last_h3, new_nav_string = process_element(args)
            mock_process_params.assert_not_called()
            assert new_last_header == last_header
            assert new_last_h3 == last_h3
            assert new_nav_string == nav_string

    def test_process_element_no_process_params_content_in_div_list(self):
        """Test process_element doesn't call process_params when content matches div_list"""
        dat = Tag(name="p")
        dat.string = "technical details"  # Matches div_list
        last_header = {"type": "h2", "title": "Some Header"}
        last_h3 = "technical details"
        nav_string = "technical details"
        div_list = ["technical details", "mitigations", "summary"]
        args = (
            dat,
            last_header,
            last_h3,
            nav_string,
            div_list,
            [],  # vulnerability
            [],  # mitigation
            [],  # notes
        )
        with patch("regscale.integrations.public.cisa.process_params") as mock_process_params:
            new_last_header, new_last_h3, new_nav_string = process_element(args)
            mock_process_params.assert_not_called()
            assert new_last_header == last_header
            assert new_last_h3 == last_h3
            assert new_nav_string == nav_string

    @patch("regscale.integrations.public.cisa.fuzzy_find_date", return_value="2023-01-01T00:00:00")
    @patch("regscale.integrations.public.cisa.gen_soup")
    def test_parse_details_with_content(self, mock_gen_soup, mock_find_date):
        """Test parse_details function with actual content processing"""
        html = """
        <div class="l-full__main">
            <h2>Technical Details</h2>
            <h3>technical details</h3>
            <p>Vulnerability content</p>
            <h2>Mitigations</h2>
            <p>Mitigation content</p>
            <h2>Summary</h2>
            <p>Summary content</p>
        </div>
        """
        mock_gen_soup.return_value = BeautifulSoup(html, "html.parser")

        result = parse_details("https://example.com")

        assert result is not None
        assert result[0] == "2023-01-01T00:00:00"
        assert result[1] == ["<p>Vulnerability content</p>"]
        assert result[2] == ["<p>Mitigation content</p>"]
        assert result[3] == ["<p>Summary content</p>"]

    @patch("regscale.integrations.public.cisa.fuzzy_find_date", return_value="2023-01-01T00:00:00")
    @patch("regscale.integrations.public.cisa.gen_soup")
    def test_parse_details_empty_content(self, mock_gen_soup, mock_find_date):
        """Test parse_details function with no content to process"""
        html = """
        <div class="l-full__main">
            <h2>Some Header</h2>
            <p>Some content that doesn't match any sections</p>
        </div>
        """
        mock_gen_soup.return_value = BeautifulSoup(html, "html.parser")

        result = parse_details("https://example.com")

        assert result is not None
        assert result[0] == "2023-01-01T00:00:00"
        assert result[1] == ["See Link for details."]
        assert result[2] == ["See Link for details."]
        assert result[3] == ["See Link for details."]

    @patch("regscale.integrations.public.cisa.fuzzy_find_date", return_value=None)
    @patch("regscale.integrations.public.cisa.gen_soup", return_value=MagicMock())
    def test_parse_details_no_date(self, mock_gen_soup, mock_find_date):
        """Test parse_details function with no date"""
        result = parse_details("https://example.com")
        assert result is None

    def test_fuzzy_find_date_first_regex(self):
        """Test fuzzy_find_date function with first call match"""
        html1 = """<div class="c-field__content">Last Revised: January 15, 2024</div>"""
        html2 = """<div class="c-field__content">Release Date: January 15, 2024</div>"""
        soup1 = BeautifulSoup(html1, "html.parser")
        soup2 = BeautifulSoup(html2, "html.parser")
        assert fuzzy_find_date(soup1) == "2024-01-15T00:00:00"
        assert fuzzy_find_date(soup2) == "2024-01-15T00:00:00"

    def test_fuzzy_find_date(self):
        """Test fuzzy_find_date's recursive functionality"""
        html1 = """
        <div class="c-field__content">Some other content</div>
        <div class="c-field__content">More content</div>
        <div class="c-field__content">January 15, 2024</div>
        """

        for i in range(0, 5):
            with patch(
                "regscale.integrations.public.cisa.fuzzy_find_date", wraps=fuzzy_find_date
            ) as mock_fuzzy_find_date:
                html1 = '<div class="c-field__content">Content</div>' + html1 if i > 0 else html1
                soup1 = BeautifulSoup(html1, "html.parser")
                assert fuzzy_find_date(soup1) == "2024-01-15T00:00:00"
                assert mock_fuzzy_find_date.call_count == i

    def test_fuzzy_find_date_not_found(self):
        """Test fuzzy_find_date function when we run out of attempts"""
        html1 = """<div class="c-field__content">Invalid Date</div>"""
        soup1 = BeautifulSoup(html1, "html.parser")
        with patch("regscale.integrations.public.cisa.fuzzy_find_date", wraps=fuzzy_find_date) as mock_fuzzy_find_date:
            # throw parser error to skip date parsing and force next attempt
            with patch("regscale.integrations.public.cisa.BeautifulSoup.find_all", side_effect=dparser.ParserError):
                assert fuzzy_find_date(soup1) is None
                assert mock_fuzzy_find_date.call_count == 5  # Should try all 5 attempts

    def test_gen_soup(self):
        """Test gen_soup function"""
        html = "<html><body>Test</body></html>"
        mock_response = MagicMock()
        mock_response.content = html
        mock_response.raise_for_status = MagicMock()

        with patch("regscale.integrations.public.cisa.Api.get", return_value=mock_response) as mock_api_get:
            soup = gen_soup("https://example.com")
            assert soup is not None
            mock_api_get.assert_called_once_with("https://example.com")
            mock_response.raise_for_status.assert_called_once()

    def test_gen_soup_tuple(self):
        """Test gen_soup function with tuple"""
        html = "<html><body>Test</body></html>"
        mock_response = MagicMock()
        mock_response.content = html
        mock_response.raise_for_status = MagicMock()
        with patch("regscale.integrations.public.cisa.Api.get", return_value=mock_response) as mock_api_get:
            soup = gen_soup(("https://example.com", "https://example2.com"))
            assert soup is not None
            mock_api_get.assert_called_once_with("https://example.com")
            mock_response.raise_for_status.assert_called_once()

    def test_gen_soup_invalid_url(self):
        """Test gen_soup function with invalid url"""
        # Test with a string that's not a URL
        with pytest.raises(URLError) as context:
            gen_soup("not_a_url")
        assert context.type == URLError
        assert context.value.reason == "URL is invalid, exiting..."

    def test_pull_cisa_kev_integration(self):
        """Test pull_cisa_kev with actual call"""
        # Clear any cached data
        if hasattr(pull_cisa_kev, "_cached_data"):
            delattr(pull_cisa_kev, "_cached_data")

        data = pull_cisa_kev()
        assert "title" in data.keys()
        assert data["title"] == "CISA Catalog of Known Exploited Vulnerabilities"

    @patch("regscale.integrations.public.cisa.Api.get")
    def test_pull_cisa_kev_success(self, mock_get):
        """Test pull_cisa_kev successful API call"""
        # Clear any cached data
        if hasattr(pull_cisa_kev, "_cached_data"):
            delattr(pull_cisa_kev, "_cached_data")

        mock_response = MagicMock()
        mock_response.json.return_value = {"title": "Test Data"}
        mock_get.return_value = mock_response

        # First call should hit the API
        data = pull_cisa_kev()
        assert data == {"title": "Test Data"}
        mock_get.assert_called_once()

        # Second call should use cached data
        mock_get.reset_mock()
        data = pull_cisa_kev()
        assert data == {"title": "Test Data"}
        mock_get.assert_not_called()

    @patch("regscale.integrations.public.cisa.Api.get")
    def test_pull_cisa_kev_fallback(self, mock_get):
        """Test pull_cisa_kev falls back to package data on error"""
        # Clear any cached data
        if hasattr(pull_cisa_kev, "_cached_data"):
            delattr(pull_cisa_kev, "_cached_data")

        mock_get.side_effect = RequestException("API Error")

        data = pull_cisa_kev()
        assert "title" in data
        assert data["title"] == "CISA Catalog of Known Exploited Vulnerabilities"

    @patch("regscale.integrations.public.cisa.Api.get")
    def test_pull_cisa_kev_config_url(self, mock_get):
        """Test pull_cisa_kev with custom URL from config"""
        # Clear any cached data
        if hasattr(pull_cisa_kev, "_cached_data"):
            delattr(pull_cisa_kev, "_cached_data")

        mock_response = MagicMock()
        mock_response.json.return_value = {"title": "Custom Data"}
        mock_get.return_value = mock_response

        # Set up custom URL in config
        app = Application()
        kev_url = app.config["cisaKev"] or None
        app.config["cisaKev"] = "https://custom.url"
        app.save_config(app.config)
        app.logger.info(f"cisaKev: {app.config['cisaKev']}")

        data = pull_cisa_kev()
        assert data == {"title": "Custom Data"}
        mock_get.assert_called_once_with(url="https://custom.url", headers={}, retry_login=False)

        # cleanup
        if kev_url:
            app.config["cisaKev"] = kev_url
        else:
            app.config.pop("cisaKev")
        app.save_config(app.config)

    @patch("regscale.integrations.public.cisa.Api.get")
    def test_pull_cisa_kev_var_url(self, mock_get):
        """Test pull_cisa_kev with default cisa url from integration"""
        # Clear any cached data
        if hasattr(pull_cisa_kev, "_cached_data"):
            delattr(pull_cisa_kev, "_cached_data")

        mock_response = MagicMock()
        mock_response.json.return_value = {"title": "Custom Data"}
        mock_get.return_value = mock_response

        # Remove url from config
        app = Application()
        kev_url = app.config["cisaKev"] or None
        app.config.pop("cisaKev")
        app.save_config(app.config)

        data = pull_cisa_kev()
        assert data == {"title": "Custom Data"}
        mock_get.assert_called_once()

        # cleanup
        if kev_url:
            app.config["cisaKev"] = kev_url
        app.save_config(app.config)

    def test_merge_old(self):
        """Test merge_old function"""
        update_vuln = {"id": 2, "name": "Test Threat", "title": "New Title", "description": "New Description"}
        old_vuln = {
            "id": 1,
            "uuid": "123",
            "status": "Active",
            "source": "CISA",
            "threatType": "Specific",
            "threatOwnerId": 456,
            "notes": "Old Notes",
            "targetType": "Other",
            "dateCreated": "2024-01-01",
            "isPublic": True,
            "investigated": False,
            "investigationResults": "Closed",
        }
        expected = {
            "id": 1,
            "name": "Test Threat",
            "title": "New Title",
            "description": "New Description",
            "uuid": "123",
            "status": "Active",
            "source": "CISA",
            "threatType": "Specific",
            "threatOwnerId": 456,
            "notes": "Old Notes",
            "targetType": "Other",
            "dateCreated": "2024-01-01",
            "isPublic": True,
            "investigated": False,
            "investigationResults": "Closed",
        }
        assert merge_old(update_vuln, old_vuln) == expected
        assert merge_old(update_vuln, {}) == update_vuln
        assert merge_old({}, old_vuln) == {
            "id": 1,
            "uuid": "123",
            "status": "Active",
            "source": "CISA",
            "threatType": "Specific",
            "threatOwnerId": 456,
            "notes": "Old Notes",
            "targetType": "Other",
            "dateCreated": "2024-01-01",
            "isPublic": True,
            "investigated": False,
            "investigationResults": "Closed",
        }

    @patch("regscale.integrations.public.cisa.Api.post", return_value=None)
    def test_insert_or_upd_threat_insert(self, mock_post):
        """Test insert_or_upd_threat function"""
        threat = {}
        app = MagicMock()
        insert_or_upd_threat(threat, app)
        mock_post.assert_called_once()

    @patch("regscale.integrations.public.cisa.Api.put", return_value=None)
    def test_insert_or_upd_threat_update(self, mock_put):
        """Test insert_or_upd_threat function"""
        threat = {}
        app = MagicMock()
        insert_or_upd_threat(threat, app, 1)
        mock_put.assert_called_once()

    @patch("regscale.integrations.public.cisa.Threat.bulk_update", return_value=None)
    def test_update_regscale_threats(self, mock_bulk_update):
        """Test update_regscale_threats function"""
        threats = [Threat()]
        update_regscale_threats(threats)
        mock_bulk_update.assert_called_once_with(None, threats)

    @patch("regscale.integrations.public.cisa.Threat.bulk_update", return_value=None)
    def test_update_regscale_threats_no_threats(self, mock_bulk_update):
        """Test update_regscale_threats function with no threats"""
        update_regscale_threats()
        update_regscale_threats([])
        mock_bulk_update.assert_not_called()

    def test_convert_date_string(self):
        """Test convert_date_string function"""
        date_str = "2022-11-03"
        assert convert_date_string(date_str) == "2022-11-03T00:00:00.000Z"

    def test_unique(self):
        """Test unique function"""
        test_list = ["a", "b", "c", "a", "b", "c"]
        assert unique(test_list) == ["a", "b", "c"]

    def test_is_url(self):
        """Test is_url function"""
        assert is_url("https://example.com")
        assert not is_url("not_a_url")
        assert not is_url("")

    def test_is_url_value_error(self):
        """Test is_url function raising a ValueError"""
        with patch("regscale.integrations.public.cisa.urlparse", side_effect=ValueError):
            assert not is_url("not_a_url")

    @patch("regscale.integrations.public.cisa.update_regscale_threats")
    @patch("regscale.integrations.public.cisa.Threat.bulk_insert")
    @patch("regscale.integrations.public.cisa.Threat.fetch_all_threats")
    @patch("regscale.integrations.public.cisa.Application")
    def test_update_regscale(self, mock_app, mock_fetch_threats, mock_bulk_insert, mock_update_threats):
        """Test update_regscale function with both insert and update"""
        # Setup mocks
        mock_app_instance = MagicMock()
        mock_app_instance.config = {"userId": "123"}
        mock_app.return_value = mock_app_instance

        # Mock existing threats
        existing_threat = Threat(
            id=1,
            description="Qualcomm Multiple Chipsets Incorrect Authorization Vulnerability",
            investigationResults="Some results",
            threatType="Specific",
            title="CVE-2025-21479",
            threatOwnerId="123",
            targetType="Other",
            source="Open Source",
            dateCreated=datetime.now().isoformat(),
            status="Initial Report/Notification",
        )
        mock_fetch_threats.return_value = [existing_threat]

        data = {
            "title": "CISA Catalog of Known Exploited Vulnerabilities",
            "catalogVersion": "2025.06.03",
            "dateReleased": "2025-06-03T16:48:39.9414Z",
            "count": 3,
            "vulnerabilities": [
                {
                    "cveID": "CVE-2025-21479",
                    "vendorProject": "Qualcomm",
                    "product": "Multiple Chipsets",
                    "vulnerabilityName": "Qualcomm Multiple Chipsets Incorrect Authorization Vulnerability",
                    "dateAdded": "2025-06-03",
                    "shortDescription": "Multiple Qualcomm chipsets contain an incorrect authorization vulnerability.",
                    "requiredAction": "Apply mitigations per vendor instructions",
                    "notes": "Please check with specific vendors",
                    "cwes": ["CWE-863"],
                    "dueDate": "2025-06-24",
                },
                {
                    "cveID": "CVE-2025-27038",
                    "vendorProject": "Qualcomm",
                    "product": "Multiple Chipsets",
                    "vulnerabilityName": "Qualcomm Multiple Chipsets Use-After-Free Vulnerability",
                    "dateAdded": "2025-06-03",
                    "shortDescription": "Multiple Qualcomm chipsets contain a use-after-free vulnerability.",
                    "requiredAction": "Apply mitigations per vendor instructions",
                    "notes": "Please check with specific vendors",
                    "cwes": ["CWE-416"],
                    "dueDate": "2025-06-24",
                },
            ],
        }

        try:
            update_regscale(data)
        except Exception as e:
            assert False, "update_regscale raised exception: {}".format(e)

        # Verify new threats were inserted
        mock_bulk_insert.assert_called_once()
        inserted_threats = mock_bulk_insert.call_args[0][1]
        assert len(inserted_threats) == 1  # should only insert second vuln
        assert inserted_threats[0]["title"] == "CVE-2025-27038"

        # Verify existing threats were updated
        mock_update_threats.assert_called_once()
        updated_threats = mock_update_threats.call_args[1]["json_list"]
        assert len(updated_threats) == 1  # only update first vuln
        assert updated_threats[0]["title"] == "CVE-2025-21479"
        assert "investigationResults" in updated_threats[0]  # preserve investigation results

    def test_parsing(self):
        """Test link parse method"""
        links = [
            "https://www.cisa.gov/news-events/cybersecurity-advisories/aa23-039a",
            "https://www.cisa.gov/news-events/cybersecurity-advisories/aa22-249a",
            "https://www.cisa.gov/news-events/cybersecurity-advisories/aa22-131a",
        ]
        for link in links:
            dat = parse_details(link)
            assert dat is not None

    @patch("regscale.core.app.api.Api.get")
    def test_load_from_package(self, mock_pull_cisa_kev):
        mock_pull_cisa_kev.return_value = None
        data = pull_cisa_kev()
        assert data is not None

    @patch("regscale.integrations.public.cisa.is_valid", return_value=False)
    def test_alerts_bad_app(self, mock_is_valid):
        """Test alerts function with bad app"""
        with pytest.raises(SystemExit) as e:
            alerts(1)
        mock_is_valid.assert_called_once()
        assert e.type == SystemExit
        assert e.value.code == 1

    @patch("regscale.integrations.public.cisa.parse_html")
    @patch("regscale.integrations.public.cisa.update_regscale_links")
    @patch("regscale.integrations.public.cisa.update_regscale_threats")
    @patch("regscale.integrations.public.cisa.Threat.fetch_all_threats")
    @patch("regscale.integrations.public.cisa.process_threats")
    def test_alerts_no_threats(
        self,
        mock_process_threats,
        mock_fetch_threats,
        mock_update_regscale_links,
        mock_update_regscale_threats,
        mock_parse_html,
    ):
        """Test alerts function with no threats from CISA"""
        mock_fetch_threats.return_value = []
        mock_parse_html.return_value = []
        alerts(1)
        mock_parse_html.assert_called_once()
        mock_process_threats.assert_not_called()
        mock_update_regscale_links.assert_not_called()
        mock_update_regscale_threats.assert_not_called()

    @patch("regscale.integrations.public.cisa.parse_html")
    @patch("regscale.integrations.public.cisa.update_regscale_links")
    @patch("regscale.integrations.public.cisa.update_regscale_threats")
    @patch("regscale.integrations.public.cisa.Threat.fetch_all_threats")
    @patch("regscale.integrations.public.cisa.process_threats")
    @patch("regscale.integrations.public.cisa.Threat.bulk_insert")
    def test_alerts_insert(
        self,
        mock_bulk_insert,
        mock_process_threats,
        mock_fetch_threats,
        mock_update_regscale_threats,
        mock_update_regscale_links,
        mock_parse_html,
    ):
        """Test alerts function with inserts"""
        insert_threats = [
            {
                "title": "CVE-2025-21479",
                "description": "Qualcomm Multiple Chipsets Incorrect Authorization Vulnerability",
                "threatType": "Specific",
                "targetType": "Other",
                "source": "Open Source",
                "status": "Initial Report/Notification",
            }
        ]
        mock_parse_html.return_value = ["Threat"]
        mock_process_threats.return_value = (insert_threats, [])
        alerts(1)
        mock_process_threats.assert_called_once()
        mock_bulk_insert.assert_called_once()
        mock_update_regscale_links.assert_called_once()
        mock_update_regscale_threats.assert_not_called()

    @patch("regscale.integrations.public.cisa.parse_html")
    @patch("regscale.integrations.public.cisa.update_regscale_links")
    @patch("regscale.integrations.public.cisa.update_regscale_threats")
    @patch("regscale.integrations.public.cisa.Threat.fetch_all_threats")
    @patch("regscale.integrations.public.cisa.process_threats")
    @patch("regscale.integrations.public.cisa.Threat.bulk_insert")
    def test_alerts_update(
        self,
        mock_bulk_insert,
        mock_process_threats,
        mock_fetch_threats,
        mock_update_regscale_threats,
        mock_update_regscale_links,
        mock_parse_html,
    ):
        """Test alerts function with updates"""
        update_threats = [
            {
                "title": "CVE-2025-21479",
                "description": "Qualcomm Multiple Chipsets Incorrect Authorization Vulnerability",
                "threatType": "Specific",
                "targetType": "Other",
                "source": "Open Source",
                "status": "Initial Report/Notification",
            }
        ]
        mock_parse_html.return_value = ["Threat"]
        mock_process_threats.return_value = ([], update_threats)
        alerts(1)
        mock_process_threats.assert_called_once()
        mock_update_regscale_threats.assert_called_once()
        mock_bulk_insert.assert_not_called()
        mock_update_regscale_links.assert_not_called()

    @pytest.mark.skip("Skipping alerts integration test due to forbidden url error")
    @patch("regscale.integrations.public.cisa.Threat.fetch_all_threats", wraps=Threat.fetch_all_threats)
    @patch("regscale.integrations.public.cisa.parse_html", wraps=parse_html)
    def test_alerts(self, mock_parse_html, mock_fetch_threats):
        """Integration test for alerts function"""
        alerts(2021)

        # Verify core operations were called
        mock_fetch_threats.assert_called_once()
        mock_parse_html.assert_called_once()

    @pytest.mark.skip("Skipping kev integration test to due api error")
    def test_cisa_integration(self):
        """Full integration test of CISA KEV ingestion"""
        data = pull_cisa_kev()
        assert data is not None
        assert "title" in data.keys()
        assert data["title"] == "CISA Catalog of Known Exploited Vulnerabilities"
        assert "vulnerabilities" in data

        update_regscale(data)

        reg_threats = Threat.fetch_all_threats()
        assert len(reg_threats) > 0

    @patch("regscale.integrations.public.cisa.build_threat")
    @patch("regscale.integrations.public.cisa.gen_soup")
    def test_parse_html(self, mock_gen_soup, mock_build_threat):
        """Test parse_html function's core parsing logic"""
        mock_soup = MagicMock()
        mock_article = MagicMock()
        mock_article.text = "Some Title | CISA Alert"
        mock_link = MagicMock()
        mock_link.__getitem__.return_value = "/some/path"  # This handles the href access
        mock_article.find_all.return_value = [mock_link]

        # First call returns one article, second call returns empty list
        mock_soup.find_all.side_effect = [[mock_article], []]
        mock_gen_soup.return_value = mock_soup

        mock_threat = Threat(
            title="CISA Alert",
            description="Test Description",
            threatType="Specific",
            targetType="Other",
            source="Open Source",
            status="Initial Report/Notification",
        )
        mock_build_threat.return_value = mock_threat

        app = Application()
        result = parse_html("https://example.com", app)

        assert mock_gen_soup.call_count == 2
        assert mock_build_threat.call_count == 2
        assert result == [mock_threat]
