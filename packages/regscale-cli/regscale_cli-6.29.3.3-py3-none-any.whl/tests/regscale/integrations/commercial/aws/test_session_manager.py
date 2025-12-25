#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for AWS Session Token Manager."""

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch, mock_open

import pytest

from regscale.integrations.commercial.aws.session_manager import AWSSessionManager


class TestAWSSessionManager:
    """Test suite for AWS Session Manager."""

    @pytest.fixture
    def temp_cache_dir(self, tmp_path):
        """Create a temporary cache directory for testing."""
        cache_dir = tmp_path / "aws_sessions"
        cache_dir.mkdir()
        return str(cache_dir)

    @pytest.fixture
    def session_manager(self, temp_cache_dir):
        """Create a session manager with temporary cache directory."""
        return AWSSessionManager(cache_dir=temp_cache_dir)

    @pytest.fixture
    def mock_credentials(self):
        """Create mock AWS credentials response."""
        expiration = datetime.now(timezone.utc) + timedelta(hours=1)
        return {
            "aws_access_key_id": "ASIAIOSFODNN7EXAMPLE",
            "aws_secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "aws_session_token": "FwoGZXIvYXdzEBYaD...",
            "expiration": expiration.isoformat(),
        }

    def test_init_creates_cache_directory(self, tmp_path):
        """Test that __init__ creates cache directory if it doesn't exist."""
        cache_dir = tmp_path / "test_cache"
        assert not cache_dir.exists()

        manager = AWSSessionManager(cache_dir=str(cache_dir))

        assert cache_dir.exists()
        assert manager.cache_dir == cache_dir

    def test_init_default_cache_directory(self):
        """Test that __init__ uses default cache directory."""
        manager = AWSSessionManager()

        expected_path = Path.home() / ".regscale" / "aws_sessions"
        assert manager.cache_dir == expected_path

    @patch("os.chmod")
    @patch("os.name", "posix")
    def test_init_sets_directory_permissions_unix(self, mock_chmod, temp_cache_dir):
        """Test that __init__ sets restrictive permissions on Unix systems."""
        manager = AWSSessionManager(cache_dir=temp_cache_dir)

        # Verify chmod was called with owner-only permissions (0o700)
        mock_chmod.assert_called_with(manager.cache_dir, 0o700)

    @patch("os.name", "nt")
    def test_init_skips_permissions_windows(self, temp_cache_dir):
        """Test that __init__ skips chmod on Windows."""
        # Should not raise an error on Windows
        manager = AWSSessionManager(cache_dir=temp_cache_dir)
        assert manager.cache_dir == Path(temp_cache_dir)

    def test_get_session_token_with_profile(self, session_manager):
        """Test getting session token using AWS profile."""
        expiration = datetime.now(timezone.utc) + timedelta(hours=1)
        mock_response = {
            "Credentials": {
                "AccessKeyId": "ASIAIOSFODNN7EXAMPLE",
                "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                "SessionToken": "FwoGZXIvYXdzEBYaD...",
                "Expiration": expiration,
            }
        }

        with patch("boto3.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_sts_client = MagicMock()
            mock_sts_client.get_session_token.return_value = mock_response
            mock_session.client.return_value = mock_sts_client
            mock_session_class.return_value = mock_session

            credentials = session_manager.get_session_token(profile="test-profile", duration_seconds=3600)

            # Verify boto3 Session was created with profile
            mock_session_class.assert_called_once_with(profile_name="test-profile")

            # Verify credentials were returned correctly
            assert credentials["aws_access_key_id"] == "ASIAIOSFODNN7EXAMPLE"
            assert credentials["aws_secret_access_key"] == "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
            assert credentials["aws_session_token"] == "FwoGZXIvYXdzEBYaD..."
            assert "expiration" in credentials

    def test_get_session_token_with_explicit_credentials(self, session_manager):
        """Test getting session token using explicit AWS credentials."""
        expiration = datetime.now(timezone.utc) + timedelta(hours=1)
        mock_response = {
            "Credentials": {
                "AccessKeyId": "ASIAIOSFODNN7EXAMPLE",
                "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                "SessionToken": "FwoGZXIvYXdzEBYaD...",
                "Expiration": expiration,
            }
        }

        with patch("boto3.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_sts_client = MagicMock()
            mock_sts_client.get_session_token.return_value = mock_response
            mock_session.client.return_value = mock_sts_client
            mock_session_class.return_value = mock_session

            credentials = session_manager.get_session_token(
                aws_access_key_id="AKIAIOSFODNN7EXAMPLE",
                aws_secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                duration_seconds=7200,
            )

            # Verify boto3 Session was created with explicit credentials
            mock_session_class.assert_called_once_with(
                aws_access_key_id="AKIAIOSFODNN7EXAMPLE",
                aws_secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            )

            # Verify get_session_token was called with correct duration
            mock_sts_client.get_session_token.assert_called_once_with(DurationSeconds=7200)

            assert credentials["aws_access_key_id"] == "ASIAIOSFODNN7EXAMPLE"

    def test_get_session_token_with_mfa(self, session_manager):
        """Test getting session token with MFA."""
        expiration = datetime.now(timezone.utc) + timedelta(hours=1)
        mock_response = {
            "Credentials": {
                "AccessKeyId": "ASIAIOSFODNN7EXAMPLE",
                "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                "SessionToken": "FwoGZXIvYXdzEBYaD...",
                "Expiration": expiration,
            }
        }

        with patch("boto3.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_sts_client = MagicMock()
            mock_sts_client.get_session_token.return_value = mock_response
            mock_session.client.return_value = mock_sts_client
            mock_session_class.return_value = mock_session

            credentials = session_manager.get_session_token(
                profile="test-profile",
                mfa_serial="arn:aws:iam::123456789012:mfa/user",
                mfa_code="123456",
                duration_seconds=3600,
            )

            # Verify get_session_token was called with MFA parameters
            mock_sts_client.get_session_token.assert_called_once_with(
                SerialNumber="arn:aws:iam::123456789012:mfa/user", TokenCode="123456", DurationSeconds=3600
            )

            assert credentials["aws_access_key_id"] == "ASIAIOSFODNN7EXAMPLE"

    def test_get_session_token_assume_role(self, session_manager):
        """Test assuming a role to get session token."""
        expiration = datetime.now(timezone.utc) + timedelta(hours=1)
        mock_response = {
            "Credentials": {
                "AccessKeyId": "ASIAIOSFODNN7EXAMPLE",
                "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                "SessionToken": "FwoGZXIvYXdzEBYaD...",
                "Expiration": expiration,
            }
        }

        with patch("boto3.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_sts_client = MagicMock()
            mock_sts_client.assume_role.return_value = mock_response
            mock_session.client.return_value = mock_sts_client
            mock_session_class.return_value = mock_session

            credentials = session_manager.get_session_token(
                profile="test-profile",
                role_arn="arn:aws:iam::987654321098:role/TestRole",
                role_session_name="test-session",
                duration_seconds=3600,
            )

            # Verify assume_role was called instead of get_session_token
            mock_sts_client.assume_role.assert_called_once()
            call_args = mock_sts_client.assume_role.call_args[1]
            assert call_args["RoleArn"] == "arn:aws:iam::987654321098:role/TestRole"
            assert call_args["RoleSessionName"] == "test-session"
            assert call_args["DurationSeconds"] == 3600

            assert credentials["aws_access_key_id"] == "ASIAIOSFODNN7EXAMPLE"

    def test_get_session_token_assume_role_with_mfa(self, session_manager):
        """Test assuming a role with MFA."""
        expiration = datetime.now(timezone.utc) + timedelta(hours=1)
        mock_response = {
            "Credentials": {
                "AccessKeyId": "ASIAIOSFODNN7EXAMPLE",
                "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                "SessionToken": "FwoGZXIvYXdzEBYaD...",
                "Expiration": expiration,
            }
        }

        with patch("boto3.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_sts_client = MagicMock()
            mock_sts_client.assume_role.return_value = mock_response
            mock_session.client.return_value = mock_sts_client
            mock_session_class.return_value = mock_session

            credentials = session_manager.get_session_token(
                profile="test-profile",
                role_arn="arn:aws:iam::987654321098:role/TestRole",
                role_session_name="test-session",
                mfa_serial="arn:aws:iam::123456789012:mfa/user",
                mfa_code="123456",
                duration_seconds=3600,
            )

            # Verify assume_role was called with MFA parameters
            call_args = mock_sts_client.assume_role.call_args[1]
            assert call_args["SerialNumber"] == "arn:aws:iam::123456789012:mfa/user"
            assert call_args["TokenCode"] == "123456"

            assert credentials["aws_access_key_id"] == "ASIAIOSFODNN7EXAMPLE"

    def test_get_session_token_error_handling(self, session_manager):
        """Test error handling when getting session token fails."""
        with patch("boto3.Session") as mock_session_class:
            mock_session = MagicMock()
            mock_sts_client = MagicMock()
            mock_sts_client.get_session_token.side_effect = Exception("AWS API Error")
            mock_session.client.return_value = mock_sts_client
            mock_session_class.return_value = mock_session

            with pytest.raises(Exception) as exc_info:
                session_manager.get_session_token(profile="test-profile")

            assert "AWS API Error" in str(exc_info.value)

    def test_cache_session(self, session_manager, mock_credentials, temp_cache_dir):
        """Test caching session credentials to file."""
        session_manager.cache_session("test-session", mock_credentials, region="us-east-1")

        cache_file = Path(temp_cache_dir) / "test-session.json"
        assert cache_file.exists()

        with open(cache_file, "r") as f:
            cached_data = json.load(f)

        assert cached_data["session_name"] == "test-session"
        assert cached_data["region"] == "us-east-1"
        assert cached_data["credentials"] == mock_credentials
        assert "cached_at" in cached_data

    @patch("os.chmod")
    @patch("os.name", "posix")
    def test_cache_session_sets_file_permissions_unix(
        self, mock_chmod, session_manager, mock_credentials, temp_cache_dir
    ):
        """Test that cache_session sets restrictive permissions on Unix."""
        session_manager.cache_session("test-session", mock_credentials)

        # Verify chmod was called with owner-only permissions (0o600)
        cache_file = Path(temp_cache_dir) / "test-session.json"
        mock_chmod.assert_called_with(cache_file, 0o600)

    def test_get_cached_session_valid(self, session_manager, mock_credentials, temp_cache_dir):
        """Test retrieving a valid cached session."""
        # Cache a session first
        session_manager.cache_session("test-session", mock_credentials, region="us-east-1")

        # Retrieve it
        cached_data = session_manager.get_cached_session("test-session")

        assert cached_data is not None
        assert cached_data["session_name"] == "test-session"
        assert cached_data["region"] == "us-east-1"
        assert cached_data["credentials"] == mock_credentials

    def test_get_cached_session_not_found(self, session_manager):
        """Test retrieving a non-existent cached session."""
        cached_data = session_manager.get_cached_session("nonexistent")

        assert cached_data is None

    def test_get_cached_session_expired(self, session_manager, temp_cache_dir):
        """Test retrieving an expired cached session."""
        # Create expired credentials (expired 1 hour ago)
        expiration = datetime.now(timezone.utc) - timedelta(hours=1)
        expired_credentials = {
            "aws_access_key_id": "ASIAIOSFODNN7EXAMPLE",
            "aws_secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "aws_session_token": "FwoGZXIvYXdzEBYaD...",
            "expiration": expiration.isoformat(),
        }

        session_manager.cache_session("expired-session", expired_credentials)

        # Try to retrieve it
        cached_data = session_manager.get_cached_session("expired-session")

        assert cached_data is None

        # Verify cache file was deleted
        cache_file = Path(temp_cache_dir) / "expired-session.json"
        assert not cache_file.exists()

    def test_get_cached_session_expiring_soon(self, session_manager, temp_cache_dir):
        """Test retrieving a session that expires in less than 5 minutes."""
        # Create credentials that expire in 2 minutes
        expiration = datetime.now(timezone.utc) + timedelta(minutes=2)
        expiring_credentials = {
            "aws_access_key_id": "ASIAIOSFODNN7EXAMPLE",
            "aws_secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "aws_session_token": "FwoGZXIvYXdzEBYaD...",
            "expiration": expiration.isoformat(),
        }

        session_manager.cache_session("expiring-session", expiring_credentials)

        # Try to retrieve it
        cached_data = session_manager.get_cached_session("expiring-session")

        # Should be treated as expired (5 minute buffer)
        assert cached_data is None

    def test_get_cached_session_corrupted_file(self, session_manager, temp_cache_dir):
        """Test retrieving a session with corrupted cache file."""
        # Create a corrupted cache file
        cache_file = Path(temp_cache_dir) / "corrupted-session.json"
        with open(cache_file, "w") as f:
            f.write("not valid json{{{")

        cached_data = session_manager.get_cached_session("corrupted-session")

        assert cached_data is None

    def test_clear_session_exists(self, session_manager, mock_credentials, temp_cache_dir):
        """Test clearing an existing cached session."""
        session_manager.cache_session("test-session", mock_credentials)

        result = session_manager.clear_session("test-session")

        assert result is True

        cache_file = Path(temp_cache_dir) / "test-session.json"
        assert not cache_file.exists()

    def test_clear_session_not_found(self, session_manager):
        """Test clearing a non-existent cached session."""
        result = session_manager.clear_session("nonexistent")

        assert result is False

    def test_clear_all_sessions(self, session_manager, mock_credentials, temp_cache_dir):
        """Test clearing all cached sessions."""
        # Create multiple sessions
        session_manager.cache_session("session-1", mock_credentials)
        session_manager.cache_session("session-2", mock_credentials)
        session_manager.cache_session("session-3", mock_credentials)

        count = session_manager.clear_all_sessions()

        assert count == 3

        # Verify all cache files are deleted
        cache_dir = Path(temp_cache_dir)
        assert len(list(cache_dir.glob("*.json"))) == 0

    def test_clear_all_sessions_empty(self, session_manager):
        """Test clearing all sessions when none exist."""
        count = session_manager.clear_all_sessions()

        assert count == 0

    def test_list_sessions(self, session_manager, mock_credentials, temp_cache_dir):
        """Test listing all cached sessions."""
        # Create multiple sessions
        session_manager.cache_session("session-1", mock_credentials, region="us-east-1")
        session_manager.cache_session("session-2", mock_credentials, region="us-west-2")

        sessions = session_manager.list_sessions()

        assert len(sessions) == 2

        # Verify session data
        session_names = {s["name"] for s in sessions}
        assert "session-1" in session_names
        assert "session-2" in session_names

        # Verify each session has required fields
        for session in sessions:
            assert "name" in session
            assert "region" in session
            assert "expiration" in session
            assert "expired" in session
            assert "cached_at" in session
            assert isinstance(session["expired"], bool)

    def test_list_sessions_with_expired(self, session_manager, temp_cache_dir):
        """Test listing sessions includes expired status."""
        # Create one valid and one expired session
        valid_expiration = datetime.now(timezone.utc) + timedelta(hours=1)
        valid_credentials = {
            "aws_access_key_id": "ASIAIOSFODNN7EXAMPLE",
            "aws_secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "aws_session_token": "FwoGZXIvYXdzEBYaD...",
            "expiration": valid_expiration.isoformat(),
        }

        expired_expiration = datetime.now(timezone.utc) - timedelta(hours=1)
        expired_credentials = {
            "aws_access_key_id": "ASIAIOSFODNN7EXAMPLE",
            "aws_secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "aws_session_token": "FwoGZXIvYXdzEBYaD...",
            "expiration": expired_expiration.isoformat(),
        }

        session_manager.cache_session("valid-session", valid_credentials)
        session_manager.cache_session("expired-session", expired_credentials)

        sessions = session_manager.list_sessions()

        assert len(sessions) == 2

        # Find the sessions and check their expired status
        valid_session = next(s for s in sessions if s["name"] == "valid-session")
        expired_session = next(s for s in sessions if s["name"] == "expired-session")

        assert valid_session["expired"] is False
        assert expired_session["expired"] is True

    def test_list_sessions_empty(self, session_manager):
        """Test listing sessions when none exist."""
        sessions = session_manager.list_sessions()

        assert sessions == []

    def test_list_sessions_corrupted_file(self, session_manager, temp_cache_dir):
        """Test listing sessions skips corrupted files."""
        # Create one valid and one corrupted session
        valid_expiration = datetime.now(timezone.utc) + timedelta(hours=1)
        valid_credentials = {
            "aws_access_key_id": "ASIAIOSFODNN7EXAMPLE",
            "aws_secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "aws_session_token": "FwoGZXIvYXdzEBYaD...",
            "expiration": valid_expiration.isoformat(),
        }

        session_manager.cache_session("valid-session", valid_credentials)

        # Create corrupted file
        corrupted_file = Path(temp_cache_dir) / "corrupted.json"
        with open(corrupted_file, "w") as f:
            f.write("not valid json{{{")

        sessions = session_manager.list_sessions()

        # Should only return the valid session
        assert len(sessions) == 1
        assert sessions[0]["name"] == "valid-session"

    def test_get_credentials_for_session(self, session_manager, mock_credentials):
        """Test getting credentials tuple for use in CLI commands."""
        session_manager.cache_session("test-session", mock_credentials, region="us-east-1")

        credentials_tuple = session_manager.get_credentials_for_session("test-session")

        assert credentials_tuple is not None
        access_key_id, secret_access_key, session_token, region = credentials_tuple

        assert access_key_id == mock_credentials["aws_access_key_id"]
        assert secret_access_key == mock_credentials["aws_secret_access_key"]
        assert session_token == mock_credentials["aws_session_token"]
        assert region == "us-east-1"

    def test_get_credentials_for_session_not_found(self, session_manager):
        """Test getting credentials for non-existent session."""
        credentials_tuple = session_manager.get_credentials_for_session("nonexistent")

        assert credentials_tuple is None

    def test_get_credentials_for_session_expired(self, session_manager):
        """Test getting credentials for expired session."""
        # Create expired credentials
        expiration = datetime.now(timezone.utc) - timedelta(hours=1)
        expired_credentials = {
            "aws_access_key_id": "ASIAIOSFODNN7EXAMPLE",
            "aws_secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "aws_session_token": "FwoGZXIvYXdzEBYaD...",
            "expiration": expiration.isoformat(),
        }

        session_manager.cache_session("expired-session", expired_credentials)

        credentials_tuple = session_manager.get_credentials_for_session("expired-session")

        assert credentials_tuple is None
