#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""QRadar to OCSF mapper for normalizing QRadar security events"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from regscale.integrations.commercial.qradar.ocsf import constants

logger = logging.getLogger("regscale")

# Constants
QRADAR_VENDOR_NAME = "IBM Security"
QRADAR_PRODUCT_NAME = "QRadar SIEM"

# QRadar Event Field Names
FIELD_LOG_SOURCE = "Log Source"
FIELD_SOURCE_IP = "Source IP"
FIELD_SOURCE_PORT = "Source Port"
FIELD_DEST_IP = "Dest IP"
FIELD_DEST_PORT = "Dest Port"
FIELD_EVENT_COUNT = "Event Count"


class QRadarOCSFMapper:
    """Maps QRadar security events to OCSF (Open Cybersecurity Schema Framework) format"""

    def __init__(self):
        """Initialize OCSF mapper"""
        self.ocsf_version = constants.OCSF_VERSION

    def event_to_ocsf(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map QRadar security event to OCSF Detection Finding (Class 2004).

        QRadar events represent security incidents detected by the SIEM platform.
        These are mapped to OCSF Detection Findings which describe security
        detections and alerts.

        Args:
            event: QRadar event in native format

        Returns:
            OCSF-formatted detection finding
        """
        # Extract severity and map to OCSF
        severity_value = self._extract_severity(event)
        severity_id = constants.map_qradar_severity(severity_value)

        # Extract magnitude and map to confidence
        magnitude = self._extract_magnitude(event)
        confidence_id = constants.map_qradar_magnitude(magnitude)

        # Get event category and determine OCSF class
        category = event.get("Low Level Category") or event.get("category", "Unknown")
        class_uid = constants.get_qradar_class_uid(category)

        # Build OCSF finding
        ocsf_finding = {
            "metadata": {
                "version": self.ocsf_version,
                "product": {
                    "name": QRADAR_PRODUCT_NAME,
                    "vendor_name": QRADAR_VENDOR_NAME,
                },
                "logged_time": self._parse_qradar_timestamp(event.get("Time")),
            },
            "class_uid": class_uid,
            "class_name": self._get_class_name(class_uid),
            "category_uid": 2,  # Findings
            "category_name": "Findings",
            "activity_id": constants.ACTIVITY_CREATE,  # New event
            "activity_name": "Create",
            "severity_id": severity_id,
            "severity": self._get_severity_name(severity_id),
            "confidence_id": confidence_id,
            "confidence": self._get_confidence_name(confidence_id),
            "finding_info": {
                "title": event.get("Event Name", "QRadar Security Event"),
                "desc": self._build_event_description(event),
                "types": [category],
                "created_time": self._parse_qradar_timestamp(event.get("Time")),
                "src": event.get(FIELD_LOG_SOURCE, ""),
            },
            "resources": self._extract_resources(event),
            "network": self._extract_network_info(event),
            "observables": self._extract_observables(event),
            "src_endpoint": self._build_endpoint(
                event.get(FIELD_SOURCE_IP), event.get(FIELD_SOURCE_PORT), is_source=True
            ),
            "dst_endpoint": self._build_endpoint(event.get(FIELD_DEST_IP), event.get(FIELD_DEST_PORT), is_source=False),
            "enrichments": [
                {
                    "name": "event_count",
                    "value": str(event.get(FIELD_EVENT_COUNT, 1)),
                    "type": "count",
                },
                {
                    "name": "magnitude",
                    "value": str(magnitude),
                    "type": "score",
                },
            ],
            "unmapped": self._extract_unmapped_fields(event),
            "raw_data": event,
        }

        # Add username if present
        if event.get("Username"):
            ocsf_finding["actor"] = {
                "user": {
                    "name": event.get("Username"),
                    "type_id": 1,  # User
                }
            }

        return ocsf_finding

    def _extract_severity(self, event: Dict[str, Any]) -> int:
        """
        Extract severity value from QRadar event.

        Args:
            event: QRadar event

        Returns:
            Severity value (0-10)
        """
        # Try different field names for severity
        severity = event.get("Severity") or event.get("severity")
        if severity is not None:
            try:
                return int(severity)
            except (ValueError, TypeError):
                logger.warning("Invalid severity value: %s", severity)
        return 0

    def _extract_magnitude(self, event: Dict[str, Any]) -> int:
        """
        Extract magnitude value from QRadar event.

        Args:
            event: QRadar event

        Returns:
            Magnitude value (0-10)
        """
        magnitude = event.get("Magnitude") or event.get("magnitude")
        if magnitude is not None:
            try:
                return int(magnitude)
            except (ValueError, TypeError):
                logger.warning("Invalid magnitude value: %s", magnitude)
        return 0

    def _build_event_description(self, event: Dict[str, Any]) -> str:
        """
        Build a descriptive text for the event.

        Args:
            event: QRadar event

        Returns:
            Event description
        """
        parts = []

        event_name = event.get("Event Name", "")
        if event_name:
            parts.append(f"Event: {event_name}")

        log_source = event.get(FIELD_LOG_SOURCE, "")
        if log_source:
            parts.append(f"Source: {log_source}")

        category = event.get("Low Level Category", "")
        if category:
            parts.append(f"Category: {category}")

        event_count = event.get(FIELD_EVENT_COUNT, 1)
        if event_count and int(event_count) > 1:
            parts.append(f"Occurrences: {event_count}")

        return " | ".join(parts) if parts else "QRadar security event"

    def _extract_resources(self, event: Dict[str, Any]) -> Optional[list]:
        """
        Extract resource information from QRadar event.

        Args:
            event: QRadar event

        Returns:
            List of OCSF resources
        """
        resources = []

        # Add source IP as a resource
        source_ip = event.get(FIELD_SOURCE_IP)
        if source_ip:
            resources.append(
                {
                    "name": source_ip,
                    "type": "IP Address",
                    "uid": source_ip,
                }
            )

        # Add destination IP as a resource
        dest_ip = event.get(FIELD_DEST_IP)
        if dest_ip and dest_ip != source_ip:
            resources.append(
                {
                    "name": dest_ip,
                    "type": "IP Address",
                    "uid": dest_ip,
                }
            )

        return resources if resources else None

    def _extract_network_info(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract network-related information.

        Args:
            event: QRadar event

        Returns:
            Network information dict or None
        """
        has_network_data = any(
            [
                event.get(FIELD_SOURCE_IP),
                event.get(FIELD_DEST_IP),
                event.get(FIELD_SOURCE_PORT),
                event.get(FIELD_DEST_PORT),
            ]
        )

        if not has_network_data:
            return None

        return {
            "src_ip": event.get(FIELD_SOURCE_IP),
            "dst_ip": event.get(FIELD_DEST_IP),
            "src_port": self._parse_port(event.get(FIELD_SOURCE_PORT)),
            "dst_port": self._parse_port(event.get(FIELD_DEST_PORT)),
        }

    def _extract_observables(self, event: Dict[str, Any]) -> Optional[list]:
        """
        Extract observable indicators from the event.

        Args:
            event: QRadar event

        Returns:
            List of observables or None
        """
        observables = []

        # Add source IP as observable
        source_ip = event.get(FIELD_SOURCE_IP)
        if source_ip:
            observables.append(
                {
                    "name": "source_ip",
                    "type_id": 2,  # IP Address
                    "value": source_ip,
                }
            )

        # Add destination IP as observable
        dest_ip = event.get(FIELD_DEST_IP)
        if dest_ip:
            observables.append(
                {
                    "name": "destination_ip",
                    "type_id": 2,  # IP Address
                    "value": dest_ip,
                }
            )

        # Add username as observable
        username = event.get("Username")
        if username:
            observables.append(
                {
                    "name": "username",
                    "type_id": 4,  # User Name
                    "value": username,
                }
            )

        return observables if observables else None

    def _build_endpoint(
        self, ip_address: Optional[str], port: Optional[str], is_source: bool
    ) -> Optional[Dict[str, Any]]:
        """
        Build endpoint information.

        Args:
            ip_address: IP address
            port: Port number
            is_source: True if source endpoint, False if destination

        Returns:
            Endpoint dict or None
        """
        if not ip_address:
            return None

        endpoint = {
            "ip": ip_address,
            "type_id": 1 if is_source else 2,  # 1=source, 2=destination
        }

        if port:
            parsed_port = self._parse_port(port)
            if parsed_port:
                endpoint["port"] = parsed_port

        return endpoint

    def _extract_unmapped_fields(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract fields that don't have direct OCSF mappings.

        Args:
            event: QRadar event

        Returns:
            Dict of unmapped fields or None
        """
        unmapped = {}

        # Store QRadar-specific fields that aren't mapped to OCSF
        qradar_fields = [FIELD_EVENT_COUNT, FIELD_LOG_SOURCE, "Magnitude"]

        for field in qradar_fields:
            value = event.get(field)
            if value is not None:
                unmapped[field.lower().replace(" ", "_")] = value

        return unmapped if unmapped else None

    def _parse_qradar_timestamp(self, timestamp: Optional[str]) -> Optional[int]:
        """
        Parse QRadar timestamp to Unix epoch milliseconds.

        QRadar timestamps are typically in format: "YYYY-MM-DD HH:MM:SS"

        Args:
            timestamp: QRadar timestamp string

        Returns:
            Unix epoch milliseconds or None
        """
        if not timestamp:
            return None

        try:
            # Try parsing QRadar format
            dt = datetime.strptime(str(timestamp), "%Y-%m-%d %H:%M:%S")
            return int(dt.timestamp() * 1000)
        except ValueError:
            try:
                # Try ISO format as fallback
                dt = datetime.fromisoformat(str(timestamp).replace("Z", "+00:00"))
                return int(dt.timestamp() * 1000)
            except (ValueError, AttributeError) as ex:
                logger.warning("Failed to parse timestamp %s: %s", timestamp, ex)
                return None

    def _parse_port(self, port: Optional[str]) -> Optional[int]:
        """
        Parse port number from string.

        Args:
            port: Port as string

        Returns:
            Port as integer or None
        """
        if not port:
            return None

        try:
            port_num = int(port)
            return port_num if 0 <= port_num <= 65535 else None
        except (ValueError, TypeError):
            logger.warning("Invalid port value: %s", port)
            return None

    def _get_severity_name(self, severity_id: int) -> str:
        """
        Get OCSF severity name from severity ID.

        Args:
            severity_id: OCSF severity ID

        Returns:
            Severity name
        """
        severity_names = {
            constants.SEVERITY_UNKNOWN: "Unknown",
            constants.SEVERITY_INFORMATIONAL: "Informational",
            constants.SEVERITY_LOW: "Low",
            constants.SEVERITY_MEDIUM: "Medium",
            constants.SEVERITY_HIGH: "High",
            constants.SEVERITY_CRITICAL: "Critical",
            constants.SEVERITY_FATAL: "Fatal",
        }
        return severity_names.get(severity_id, "Unknown")

    def _get_confidence_name(self, confidence_id: int) -> str:
        """
        Get OCSF confidence name from confidence ID.

        Args:
            confidence_id: OCSF confidence ID

        Returns:
            Confidence name
        """
        confidence_names = {
            constants.CONFIDENCE_UNKNOWN: "Unknown",
            constants.CONFIDENCE_LOW: "Low",
            constants.CONFIDENCE_MEDIUM: "Medium",
            constants.CONFIDENCE_HIGH: "High",
        }
        return confidence_names.get(confidence_id, "Unknown")

    def _get_class_name(self, class_uid: int) -> str:
        """
        Get OCSF class name from class UID.

        Args:
            class_uid: OCSF class UID

        Returns:
            Class name
        """
        class_names = {
            constants.CLASS_SECURITY_FINDING: "Security Finding",
            constants.CLASS_DETECTION_FINDING: "Detection Finding",
            constants.CLASS_NETWORK_ACTIVITY: "Network Activity",
        }
        return class_names.get(class_uid, "Detection Finding")
