"""AWS Session Token Manager for RegScale CLI.

This module provides functionality to generate, cache, and manage temporary AWS session tokens.
Session tokens provide better security than long-term access keys and support MFA authentication.
"""

import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Tuple

logger = logging.getLogger("regscale")


class AWSSessionManager:
    """Manages AWS session tokens with local caching and automatic expiration."""

    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize the AWS session manager.

        :param Optional[str] cache_dir: Directory to store cached session tokens.
                                       Defaults to ~/.regscale/aws_sessions/
        """
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            self.cache_dir = Path.home() / ".regscale" / "aws_sessions"

        # Create cache directory if it doesn't exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Set restrictive permissions on the cache directory (owner read/write only)
        if os.name != "nt":  # Unix-like systems
            os.chmod(self.cache_dir, 0o700)

    def get_session_token(
        self,
        profile: Optional[str] = None,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        mfa_serial: Optional[str] = None,
        mfa_code: Optional[str] = None,
        role_arn: Optional[str] = None,
        role_session_name: Optional[str] = None,
        duration_seconds: int = 3600,
    ) -> Dict[str, str]:
        """
        Generate a new AWS session token using STS.

        :param Optional[str] profile: AWS profile name to use
        :param Optional[str] aws_access_key_id: AWS access key ID
        :param Optional[str] aws_secret_access_key: AWS secret access key
        :param Optional[str] mfa_serial: ARN of MFA device (e.g., arn:aws:iam::123456789012:mfa/user)
        :param Optional[str] mfa_code: 6-digit MFA code from authenticator app
        :param Optional[str] role_arn: ARN of role to assume
        :param Optional[str] role_session_name: Name for the assumed role session
        :param int duration_seconds: Duration for session token (900-43200 seconds, default 3600)
        :return: Dictionary with temporary credentials
        :rtype: Dict[str, str]
        """
        import boto3

        # Create initial session
        if aws_access_key_id and aws_secret_access_key:
            session = boto3.Session(
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
            )
        elif profile:
            session = boto3.Session(profile_name=profile)
        else:
            # Use default credential chain
            session = boto3.Session()

        sts_client = session.client("sts")

        try:
            if role_arn:
                # Assume role (with or without MFA)
                logger.info(f"Assuming role: {role_arn}")
                assume_role_params = {
                    "RoleArn": role_arn,
                    "RoleSessionName": role_session_name or f"regscale-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "DurationSeconds": duration_seconds,
                }

                if mfa_serial and mfa_code:
                    assume_role_params["SerialNumber"] = mfa_serial
                    assume_role_params["TokenCode"] = mfa_code

                response = sts_client.assume_role(**assume_role_params)
                credentials = response["Credentials"]

                return {
                    "aws_access_key_id": credentials["AccessKeyId"],
                    "aws_secret_access_key": credentials["SecretAccessKey"],
                    "aws_session_token": credentials["SessionToken"],
                    "expiration": credentials["Expiration"].isoformat(),
                }
            else:
                # Get session token (with or without MFA)
                logger.info("Getting session token from AWS STS")
                get_session_params = {"DurationSeconds": duration_seconds}

                if mfa_serial and mfa_code:
                    get_session_params["SerialNumber"] = mfa_serial
                    get_session_params["TokenCode"] = mfa_code
                    logger.info(f"Using MFA device: {mfa_serial}")

                response = sts_client.get_session_token(**get_session_params)
                credentials = response["Credentials"]

                return {
                    "aws_access_key_id": credentials["AccessKeyId"],
                    "aws_secret_access_key": credentials["SecretAccessKey"],
                    "aws_session_token": credentials["SessionToken"],
                    "expiration": credentials["Expiration"].isoformat(),
                }

        except Exception as e:
            logger.error(f"Failed to get AWS session token: {e}")
            raise

    def cache_session(
        self,
        session_name: str,
        credentials: Dict[str, str],
        region: Optional[str] = None,
    ) -> None:
        """
        Cache session credentials to local file.

        :param str session_name: Name for this session (e.g., profile name or custom name)
        :param Dict[str, str] credentials: Credentials dictionary from get_session_token()
        :param Optional[str] region: AWS region to associate with this session
        """
        cache_file = self.cache_dir / f"{session_name}.json"

        cache_data = {
            "session_name": session_name,
            "credentials": credentials,
            "region": region,
            "cached_at": datetime.now().isoformat(),
        }

        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, indent=2)

        # Set restrictive permissions on the cache file (owner read/write only)
        if os.name != "nt":  # Unix-like systems
            os.chmod(cache_file, 0o600)

        logger.info(f"Cached session credentials to: {cache_file}")
        logger.info(f"Session expires at: {credentials['expiration']}")

    def get_cached_session(self, session_name: str) -> Optional[Dict[str, str]]:
        """
        Retrieve cached session credentials if they exist and are not expired.

        :param str session_name: Name of the cached session
        :return: Credentials dictionary or None if not found/expired
        :rtype: Optional[Dict[str, str]]
        """
        cache_file = self.cache_dir / f"{session_name}.json"

        if not cache_file.exists():
            logger.debug(f"No cached session found: {session_name}")
            return None

        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cache_data = json.load(f)

            credentials = cache_data["credentials"]
            expiration = datetime.fromisoformat(credentials["expiration"])

            # Check if session is expired (with 5 minute buffer for safety)
            if expiration - timedelta(minutes=5) < datetime.now(expiration.tzinfo):
                logger.warning(f"Cached session expired: {session_name}")
                # Clean up expired cache file
                cache_file.unlink()
                return None

            logger.info(f"Using cached session: {session_name}")
            logger.info(f"Session expires at: {credentials['expiration']}")
            return cache_data

        except Exception as e:
            logger.error(f"Failed to read cached session: {e}")
            return None

    def clear_session(self, session_name: str) -> bool:
        """
        Clear a cached session.

        :param str session_name: Name of the session to clear
        :return: True if session was cleared, False if not found
        :rtype: bool
        """
        cache_file = self.cache_dir / f"{session_name}.json"

        if cache_file.exists():
            cache_file.unlink()
            logger.info(f"Cleared cached session: {session_name}")
            return True
        else:
            logger.warning(f"No cached session found: {session_name}")
            return False

    def clear_all_sessions(self) -> int:
        """
        Clear all cached sessions.

        :return: Number of sessions cleared
        :rtype: int
        """
        count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()
            count += 1

        logger.info(f"Cleared {count} cached session(s)")
        return count

    def list_sessions(self) -> list[Dict[str, str]]:
        """
        List all cached sessions with their expiration status.

        :return: List of session information dictionaries
        :rtype: list[Dict[str, str]]
        """
        sessions = []

        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cache_data = json.load(f)

                credentials = cache_data["credentials"]
                expiration = datetime.fromisoformat(credentials["expiration"])
                is_expired = expiration < datetime.now(expiration.tzinfo)

                sessions.append(
                    {
                        "name": cache_data["session_name"],
                        "region": cache_data.get("region", "N/A"),
                        "expiration": credentials["expiration"],
                        "expired": is_expired,
                        "cached_at": cache_data.get("cached_at", "Unknown"),
                    }
                )

            except Exception as e:
                logger.error(f"Failed to read session file {cache_file}: {e}")

        return sorted(sessions, key=lambda x: x["expiration"], reverse=True)

    def get_credentials_for_session(
        self, session_name: str
    ) -> Optional[Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]]:
        """
        Get AWS credentials from cached session for use in CLI commands.

        :param str session_name: Name of the cached session
        :return: Tuple of (access_key_id, secret_access_key, session_token, region) or None
        :rtype: Optional[Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]]
        """
        cache_data = self.get_cached_session(session_name)

        if not cache_data:
            return None

        credentials = cache_data["credentials"]
        return (
            credentials["aws_access_key_id"],
            credentials["aws_secret_access_key"],
            credentials["aws_session_token"],
            cache_data.get("region"),
        )
