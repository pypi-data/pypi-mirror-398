"""Unit tests for FedrampPoamIntegration.gen_asset_list method."""

import pytest
from regscale.integrations.public.fedramp.poam.scanner import FedrampPoamIntegration


class TestGenAssetList:
    """Test cases for the gen_asset_list method."""

    @pytest.fixture
    def integration(self):
        """Create a minimal FedrampPoamIntegration instance for testing."""
        # We need to bypass the normal __init__ that requires a file
        integration = FedrampPoamIntegration.__new__(FedrampPoamIntegration)
        return integration

    def test_single_asset_with_port_protocol(self, integration):
        """Test parsing single asset with port/protocol information in parentheses.

        This is the main bug fix - spaces within an asset identifier should be preserved,
        not treated as delimiters.
        """
        asset_string = "10.10.160.200 ( 2049 / TCP )"
        result = integration.gen_asset_list(asset_string)

        assert len(result) == 1, f"Expected 1 asset, got {len(result)}: {result}"
        assert result[0] == "10.10.160.200 ( 2049 / TCP )"

    def test_multiple_comma_separated_ips(self, integration):
        """Test parsing multiple comma-separated IP addresses."""
        asset_string = "10.10.1.1, 10.10.1.2, 10.10.1.3"
        result = integration.gen_asset_list(asset_string)

        assert len(result) == 3
        assert result == ["10.10.1.1", "10.10.1.2", "10.10.1.3"]

    def test_multiple_semicolon_separated(self, integration):
        """Test parsing multiple semicolon-separated hostnames."""
        asset_string = "server1.example.com; server2.example.com"
        result = integration.gen_asset_list(asset_string)

        assert len(result) == 2
        assert result == ["server1.example.com", "server2.example.com"]

    def test_multiple_pipe_separated(self, integration):
        """Test parsing multiple pipe-separated assets."""
        asset_string = "10.10.1.1|10.10.1.2|10.10.1.3"
        result = integration.gen_asset_list(asset_string)

        assert len(result) == 3
        assert result == ["10.10.1.1", "10.10.1.2", "10.10.1.3"]

    def test_bracketed_list(self, integration):
        """Test parsing bracketed comma-separated list."""
        asset_string = "[10.10.1.1, 10.10.1.2]"
        result = integration.gen_asset_list(asset_string)

        assert len(result) == 2
        assert result == ["10.10.1.1", "10.10.1.2"]

    def test_multiple_assets_with_port_info(self, integration):
        """Test parsing multiple assets, each with port/protocol information."""
        asset_string = "server1.example.com ( 443 / TCP ), server2.example.com ( 80 / HTTP )"
        result = integration.gen_asset_list(asset_string)

        assert len(result) == 2
        assert result[0] == "server1.example.com ( 443 / TCP )"
        assert result[1] == "server2.example.com ( 80 / HTTP )"

    def test_tab_separated(self, integration):
        """Test parsing tab-separated assets."""
        asset_string = "10.10.1.1\t10.10.1.2"
        result = integration.gen_asset_list(asset_string)

        assert len(result) == 2
        assert result == ["10.10.1.1", "10.10.1.2"]

    def test_newline_separated(self, integration):
        """Test parsing newline-separated assets."""
        asset_string = "10.10.1.1\n10.10.1.2\n10.10.1.3"
        result = integration.gen_asset_list(asset_string)

        assert len(result) == 3
        assert result == ["10.10.1.1", "10.10.1.2", "10.10.1.3"]

    def test_mixed_separators(self, integration):
        """Test parsing assets with mixed separator types."""
        asset_string = "10.10.1.1, 10.10.1.2; 10.10.1.3|10.10.1.4"
        result = integration.gen_asset_list(asset_string)

        assert len(result) == 4
        assert result == ["10.10.1.1", "10.10.1.2", "10.10.1.3", "10.10.1.4"]

    def test_extra_whitespace_trimmed(self, integration):
        """Test that extra whitespace around separators is trimmed."""
        asset_string = "10.10.1.1  ,   10.10.1.2  ;  10.10.1.3"
        result = integration.gen_asset_list(asset_string)

        assert len(result) == 3
        assert result == ["10.10.1.1", "10.10.1.2", "10.10.1.3"]

    def test_empty_string(self, integration):
        """Test handling of empty string."""
        asset_string = ""
        result = integration.gen_asset_list(asset_string)

        assert len(result) == 0
        assert result == []

    def test_single_asset_no_port_info(self, integration):
        """Test parsing single asset without port information."""
        asset_string = "10.10.160.200"
        result = integration.gen_asset_list(asset_string)

        assert len(result) == 1
        assert result[0] == "10.10.160.200"

    def test_hostname_with_spaces_in_description(self, integration):
        """Test asset identifier with descriptive text containing spaces."""
        # This represents a common pattern where port/protocol or other metadata
        # is included with the asset identifier
        asset_string = "webserver.example.com ( HTTPS Port 443 )"
        result = integration.gen_asset_list(asset_string)

        assert len(result) == 1
        assert result[0] == "webserver.example.com ( HTTPS Port 443 )"

    def test_regression_client_issue(self, integration):
        """Regression test for client issue with line 186 in Cornerstone Galaxy POAM.

        Client reported that asset identifier "10.10.160.200 ( 2049 / TCP )" in Column G
        was being split into 6 separate assets: ['10.10.160.200', '(', '2049', '/', 'TCP', ')']

        This test ensures the fix prevents that incorrect behavior.
        """
        asset_string = "10.10.160.200 ( 2049 / TCP )"
        result = integration.gen_asset_list(asset_string)

        # Should create exactly 1 asset, not 6
        assert len(result) == 1, f"Expected 1 asset but got {len(result)}: {result}"

        # Should preserve the full string including parentheses and spaces
        assert result[0] == "10.10.160.200 ( 2049 / TCP )"

        # Ensure we're NOT getting the buggy behavior
        assert "(" not in [r for r in result if r != asset_string]
        assert ")" not in [r for r in result if r != asset_string]
        assert "2049" not in [r for r in result if r != asset_string]
        assert "/" not in [r for r in result if r != asset_string]
        assert "TCP" not in [r for r in result if r != asset_string]
