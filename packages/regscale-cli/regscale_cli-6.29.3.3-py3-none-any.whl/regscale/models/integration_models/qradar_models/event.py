"""Pydantic models for QRadar security events."""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator


class QRadarEvent(BaseModel):
    """
    QRadar security event model.

    This model validates and normalizes QRadar event data from the Ariel Query API.
    QRadar events represent security incidents, policy violations, and system activity
    across the monitored IT environment.

    Field Mappings:
        - Event Name: QIDNAME(qid) - Human-readable name of the event type
        - Log Source: LOGSOURCENAME(logsourceid) - Source system/device
        - Magnitude: magnitude - Event severity level 0-10
        - Severity: severity - Alternative severity field
        - Source IP: sourceip - Originating IP address
        - Dest IP: destinationip - Destination IP address
        - Username: username - Associated user account
        - Low Level Category: CATEGORYNAME(category) - Event classification
        - Event Count: COUNT(*) - Number of aggregated events
        - Time: DATEFORMAT(deviceTime) - Event timestamp
    """

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    # Event identification - QRadar returns lowercase field names
    qid: Optional[int] = Field(default=None, alias="qid", description="QRadar event ID")
    event_name: Optional[str] = Field(default="Unknown Event", alias="qidname", description="Event type name")
    logsource_id: Optional[int] = Field(default=None, alias="logsourceid", description="Log source ID")
    log_source: Optional[str] = Field(
        default="Unknown Source", alias="logsourcename", description="Source system generating the event"
    )
    category: Optional[str] = Field(
        default="Security Event", alias="categoryname", description="Event classification category"
    )
    resource_id: Optional[str] = Field(default="", alias="resourceid", description="AWS/Cloud resource identifier")

    # Severity and priority - QRadar returns severity as int 0-10
    magnitude: Optional[int] = Field(
        default=None, alias="magnitude", ge=0, le=10, description="Event magnitude/severity level (0-10)"
    )
    severity: Optional[int] = Field(
        default=None, alias="severity", ge=0, le=10, description="Event severity level (0-10)"
    )

    # Network information - QRadar uses lowercase field names
    source_ip: Optional[str] = Field(default="", alias="sourceip", description="Source IP address")
    source_port: Optional[int] = Field(default=0, alias="sourceport", description="Source port number")
    dest_ip: Optional[str] = Field(default="", alias="destinationip", description="Destination IP address")
    dest_port: Optional[int] = Field(default=0, alias="destinationport", description="Destination port number")

    # User and identity
    username: Optional[str] = Field(default="", alias="username", description="Associated username")

    # AWS account information - added for AWS CloudTrail events
    account_id: Optional[str] = Field(default="", alias="accountid", description="AWS Account ID")
    account_name: Optional[str] = Field(default="", alias="accountname", description="AWS Account Name")
    aws_access_key_id: Optional[str] = Field(default="", alias="awsaccesskeyid", description="AWS Access Key ID")

    # Event metadata
    event_count: int = Field(default=1, alias="eventcount", description="Number of aggregated events")
    event_time: Optional[int] = Field(
        default=None, alias="devicetime", description="Device time in milliseconds since epoch"
    )
    # Also support 'starttime' field from QRadar mock API and some real QRadar responses
    start_time: Optional[int] = Field(default=None, alias="starttime", description="Alternative time field")

    @model_validator(mode="after")
    def handle_time_field_fallback(self):
        """Fallback event_time to start_time if event_time is None."""
        # If event_time is None but start_time has a value, use start_time
        if self.event_time is None and self.start_time is not None:
            self.event_time = self.start_time
        return self

    @field_validator("category", "event_name", "log_source", mode="before")
    @classmethod
    def convert_none_to_default(cls, v, info):
        """Convert None values to default strings."""
        if v is None or v == "":
            field_defaults = {
                "category": "Security Event",
                "event_name": "Unknown Event",
                "log_source": "Unknown Source",
            }
            return field_defaults.get(info.field_name, "Unknown")
        return str(v)  # Ensure it's a string

    @field_validator("magnitude", "severity", mode="before")
    @classmethod
    def convert_severity_to_int(cls, v):
        """Convert severity values to integers, handling None and strings."""
        if v is None:
            return None
        try:
            return int(v)
        except (ValueError, TypeError):
            return 5  # Default to medium severity

    @field_validator(
        "source_ip",
        "dest_ip",
        "username",
        "resource_id",
        "account_id",
        "account_name",
        "aws_access_key_id",
        mode="before",
    )
    @classmethod
    def convert_to_string(cls, v):
        """Convert values to strings, handling None."""
        if v is None or v == "":
            return ""
        return str(v)

    def get_severity_value(self) -> int:
        """
        Get the effective severity value for this event.

        Returns magnitude if available, otherwise severity, with a default of 5.

        Returns:
            int: Severity value 0-10
        """
        import logging

        logger = logging.getLogger("regscale")

        if self.magnitude is not None:
            return self.magnitude
        if self.severity is not None:
            logger.debug(f"Event '{self.event_name}' has no magnitude, using severity field: {self.severity}")
            return self.severity

        # Log when defaulting because both fields are None
        logger.warning(
            f"Event '{self.event_name}' has no magnitude or severity fields from QRadar API, "
            f"defaulting to severity 5 (Medium). This may indicate a QRadar API query issue."
        )
        return 5

    def get_primary_asset_identifier(self) -> str:
        """
        Get the primary asset identifier for this event.

        Prefers AWS account ID for CloudTrail events, falls back to source IP,
        destination IP, then username.

        Returns:
            str: Asset identifier (AWS account ID, IP address, or username)
        """
        # Prioritize AWS account ID for CloudTrail events
        if self.account_id and self.account_id != "":
            return self.account_id
        if self.source_ip and self.source_ip not in ["", "0.0.0.0", "127.0.0.1"]:
            return self.source_ip
        if self.dest_ip and self.dest_ip not in ["", "0.0.0.0", "127.0.0.1"]:
            return self.dest_ip
        if self.username:
            return self.username
        return "Unknown"

    def is_valid_source_asset(self) -> bool:
        """
        Check if this event has a valid source IP for asset creation.

        Returns:
            bool: True if source IP is valid
        """
        return bool(self.source_ip and self.source_ip not in ["", "0.0.0.0", "127.0.0.1"])

    def is_valid_dest_asset(self) -> bool:
        """
        Check if this event has a valid destination IP for asset creation.

        Returns:
            bool: True if destination IP is valid
        """
        return bool(self.dest_ip and self.dest_ip not in ["", "0.0.0.0", "127.0.0.1"])


class QRadarAssetInfo(BaseModel):
    """
    QRadar asset information extracted from events.

    This model represents an asset discovered through QRadar event analysis.
    Assets are inferred from IP addresses, hostnames, and log sources in events.
    """

    model_config = ConfigDict(populate_by_name=True)

    # Asset identification
    ip_address: str = Field(description="IP address of the asset")
    hostname: Optional[str] = Field(default=None, description="Hostname if available")
    log_source: Optional[str] = Field(default=None, description="Associated log source")

    # Asset classification
    asset_type: str = Field(default="Unknown", description="Type of asset (Server, Workstation, etc.)")
    asset_category: str = Field(default="Unknown", description="Category of asset (OS, Network Device, etc.)")

    # Discovery metadata
    first_seen: str = Field(description="First time asset was observed")
    last_seen: str = Field(description="Last time asset was observed")
    event_count: int = Field(default=1, description="Number of events associated with this asset")


# Example usage and validation
if __name__ == "__main__":
    import json

    # Example event data from QRadar API
    sample_event = {
        "Event Name": "Failed Authentication Attempt",
        "Log Source": "Windows Active Directory",
        "Event Count": 25,
        "Time": "2025-01-06 14:30:00",
        "Low Level Category": "Authentication Failure",
        "Magnitude": 7,
        "Severity": 7,
        "Source IP": "192.168.1.100",
        "Source Port": "54321",
        "Dest IP": "192.168.1.10",
        "Dest Port": "445",
        "Username": "jdoe",
    }

    # Validate and parse
    event = QRadarEvent(**sample_event)  # type: ignore[arg-type]
    print("Parsed QRadar Event:")
    print(json.dumps(event.model_dump(), indent=2))
    print(f"\nEffective Severity: {event.get_severity_value()}")
    print(f"Primary Asset: {event.get_primary_asset_identifier()}")
    print(f"Valid Source Asset: {event.is_valid_source_asset()}")
    print(f"Valid Dest Asset: {event.is_valid_dest_asset()}")
