"""Class to handle mapping RegScale models to OCSF models for Synqly integration"""

from datetime import datetime
from typing import Any, Union, TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from regscale.models.integration_models.synqly_models.connectors import Edr, Ticketing, Vulnerabilities
    from synqly.engine.resources.ocsf.resources.v_1_3_0.resources.securityfinding import (
        Finding,
        ResourceDetails,
        Vulnerability,
    )

from synqly import engine
from synqly.engine import CreateTicketRequest
from synqly.engine.resources.ticketing.types.priority import Priority

from regscale.core.app.utils.app_utils import (
    error_and_exit,
    convert_datetime_to_regscale_string,
)
from synqly.engine.resources.ticketing.types.ticket import Ticket
from synqly.engine.resources.vulnerabilities.types import Asset as OCSFAsset, SecurityFinding
from synqly.engine.resources.events.types import Event_DetectionFinding as Alerts
from synqly.engine.resources.ocsf.resources.v_1_3_0.resources.softwareinfo import SoftwareInfo
from synqly.engine.resources.ocsf.resources.v_1_3_0.resources.inventoryinfo import InventoryInfo
from regscale.models.regscale_models import Issue
from regscale.integrations.scanner_integration import IntegrationAsset, IntegrationFinding


class Mapper:
    """Mapping class to handle RegScale models to OCSF models for Synqly integration"""

    date_format = "%Y-%m-%dT%H:%M:%S"

    def to_ocsf(self, regscale_object: Any, **kwargs) -> Any:
        """
        Convert RegScale object to OCSF object

        :param Any regscale_object: RegScale object to convert to an OCSF object
        :return: The comparable OCSF object
        :rtype: Any
        """
        if isinstance(regscale_object, Issue):
            return self._regscale_issue_to_ticket(regscale_object, **kwargs)
        else:
            error_and_exit(f"Unsupported object type {type(regscale_object)}")

    def to_regscale(self, ocsf_object: Any, connector: Union["Edr", "Ticketing", "Vulnerabilities"], **kwargs) -> Any:
        """
        Convert OCSF object to RegScale object

        :param Any ocsf_object: OCSF object to convert to a RegScale object
        :param Union["Edr", "Ticketing", "Vulnerabilities"] connector: Connector class object
        :return: The comparable RegScale object
        :rtype: Any
        """
        if isinstance(ocsf_object, Ticket):
            return self._ticket_to_regscale(connector, ocsf_object, **kwargs)
        elif (
            isinstance(ocsf_object, OCSFAsset)
            or isinstance(ocsf_object, SoftwareInfo)
            or isinstance(ocsf_object, InventoryInfo)
        ):
            return self._ocsf_asset_to_regscale(connector, ocsf_object, **kwargs)
        elif isinstance(ocsf_object, SecurityFinding):
            return self._security_finding_to_regscale(connector, ocsf_object, **kwargs)
        elif isinstance(ocsf_object, Alerts):
            return self._security_alert_to_regscale(connector, ocsf_object, **kwargs)
        else:
            error_and_exit(f"Unsupported object type {type(ocsf_object)}")

    def _ticket_to_regscale(self, connector: "Ticketing", ticket: Ticket, **kwargs) -> Issue:
        """
        Convert OCSF Ticket to RegScale Issue

        :param "Ticketing" connector: Ticketing connector class object
        :param Ticket ticket: OCSF Ticket to convert to a RegScale Issue
        :param dict **kwargs: Keyword Arguments
        :return: The comparable RegScale Issue
        :rtype: Issue
        """
        due_date = convert_datetime_to_regscale_string(ticket.due_date)
        if not due_date:
            due_date = self._determine_due_date(ticket.priority, connector)
        ticket_dict = ticket.dict()
        key_val_parts = ["All fields:\n"]
        for k, v in ticket_dict.items():
            key_val_parts.append(f"{k.replace('_', ' ').title()}: {str(v) or 'NULL'}\n")
        key_val_desc = "".join(key_val_parts)
        regscale_issue = Issue(
            title=ticket.summary,
            severityLevel=Issue.assign_severity(ticket.priority),
            dueDate=due_date,
            description=f"Description {ticket.description}\n{key_val_desc}",
            status=("Closed" if ticket.status.lower() == "done" else "Draft"),
            dateCompleted=(
                convert_datetime_to_regscale_string(ticket.completion_date) if ticket.status.lower() == "done" else None
            ),
            **kwargs,
        )
        # update the correct integration field names or manual detection fields
        if connector.has_integration_field:
            setattr(regscale_issue, connector.integration_id_field, ticket.id)
        else:
            regscale_issue.manualDetectionSource = connector.integration
            regscale_issue.manualDetectionId = ticket.id
        return regscale_issue

    def _ocsf_asset_to_regscale(
        self, connector: Union["Edr", "Vulnerabilities"], asset: Union[InventoryInfo, OCSFAsset, SoftwareInfo], **kwargs
    ) -> IntegrationAsset:
        """
        Convert OCSF Asset to RegScale Asset

        :param Union["Edr", "Vulnerabilities"] connector: Edr or Vulnerabilities connector class object
        :param Union[InventoryInfo, OCSFAsset, SoftwareInfo] asset: OCSF Asset data to convert to an IntegrationAsset
        :return: The comparable IntegrationAsset object
        :rtype: IntegrationAsset
        """
        from regscale.models.regscale_models import AssetCategory, SecurityPlan

        device_data = asset.device
        os_data = device_data.os
        if device_data.sw_info:
            software_inventory = [
                {"name": sw.name, "version": sw.version} for sw in device_data.sw_info if getattr(sw, "name", None)
            ]
        else:
            software_inventory = []
        if isinstance(asset, OCSFAsset):  # this is a hardware asset
            name = device_data.name or device_data.hostname or f"{connector.provider} Asset: {device_data.instance_uid}"
            category = AssetCategory.Hardware
        else:
            name = device_data.name or device_data.hostname or f"{connector.provider} Asset: {device_data.uid}"
            category = AssetCategory.Software
        ip_v4s, ip_v6s = self._determine_ip_addresses(
            device_data.ip_addresses if device_data.ip_addresses else [device_data.ip]
        )
        return IntegrationAsset(
            name=name,
            identifier=device_data.uid,
            asset_type=device_data.type or "Other",
            asset_category=category,
            parent_id=kwargs.pop("regscale_ssp_id"),
            parent_module=SecurityPlan.get_module_string(),
            mac_address=device_data.mac,
            fqdn=device_data.hostname,
            ip_address=", ".join(ip_v4s),
            ipv6_address=", ".join(ip_v6s),
            location=device_data.location or device_data.zone,
            vlan_id=device_data.vlan_uid,
            other_tracking_number=device_data.uid,
            serial_number=device_data.hw_info.serial_number if device_data.hw_info else None,
            cpu=device_data.hw_info.cpu_cores if device_data.hw_info else None,
            ram=device_data.hw_info.ram_size if device_data.hw_info else None,
            operating_system=os_data.name or os_data.type if os_data else None,
            os_version=os_data.version if os_data else None,
            software_inventory=software_inventory,
        )

    @staticmethod
    def _determine_ip_addresses(ips: list) -> tuple[list[str], list[str]]:
        """
        Parse the list of ips and return a tuple of two lists: list of IP v4 and IP v6 addresses

        :param list ips: List of IP addresses (may contain strings, integers, or None values)
        :return: Tuple containing two lists, list of IP v4 addresses and list of IP v6 addresses
        :rtype: tuple[list[str], list[str]]
        """
        import ipaddress

        ip_v4s = []
        ip_v6s = []
        for ip in ips:
            # Skip None values
            if ip is None:
                continue
            # Convert to string if not already (handles integer IPs from some APIs)
            ip_str = str(ip).strip() if not isinstance(ip, str) else ip.strip()
            # Skip empty strings
            if not ip_str:
                continue
            try:
                ipaddress.IPv4Address(ip_str)
                ip_v4s.append(ip_str)
            except ipaddress.AddressValueError:
                try:
                    ipaddress.IPv6Address(ip_str)
                    ip_v6s.append(ip_str)
                except ipaddress.AddressValueError:
                    continue
        return ip_v4s, ip_v6s

    @staticmethod
    def _determine_date(
        attribute: str, finding: Optional["Finding"] = None, vuln: Optional["Vulnerability"] = None
    ) -> datetime:
        """
        Determine the date based on the provided vulnerability or finding

        :param str attribute: The attribute to determine the date for
        :param Optional[SecurityFinding] finding: The finding to determine the date for
        :param Optional[Vulnerability] vuln: The vulnerability to determine the date for
        :return: The date
        :rtype: datetime
        """
        from regscale.core.utils.date import normalize_timestamp

        vuln_date = getattr(vuln, attribute) if vuln else None
        fallback_vuln_date = getattr(vuln, attribute.replace("_dt", ""), None) if vuln else None
        finding_date = getattr(finding, attribute) if finding else None
        fallback_finding_date = getattr(finding, attribute.replace("_dt", ""), None) if finding else None
        if vuln_date:
            return vuln_date
        elif finding_date:
            return finding_date
        # No datetime objects, lets try the epoch integers
        if fallback_vuln_date:
            fallback_vuln_date = normalize_timestamp(fallback_vuln_date)
            return datetime.fromtimestamp(fallback_vuln_date)
        elif fallback_finding_date:
            fallback_finding_date = normalize_timestamp(fallback_finding_date)
            return datetime.fromtimestamp(fallback_finding_date)
        else:
            return datetime.now()

    @staticmethod
    def _extract_remediation_text(remediation_obj: Any) -> Optional[str]:
        """
        Extract remediation description text from various data structures

        :param Any remediation_obj: Remediation object, dict, or other structure
        :return: Remediation description text or None
        :rtype: Optional[str]
        """
        if not remediation_obj:
            return None

        # Handle dictionary structure: {"desc": "text"}
        if isinstance(remediation_obj, dict):
            return remediation_obj.get("desc")

        # Handle object with desc attribute
        return getattr(remediation_obj, "desc", None)

    def _get_remediation_from_finding(self, finding_obj: Any) -> Optional[str]:
        """
        Get remediation text from finding object with safe access patterns

        :param Any finding_obj: Finding object (could be object or dict)
        :return: Remediation description text or None
        :rtype: Optional[str]
        """
        if not finding_obj:
            return None

        # Try object attribute access first (most common case)
        remediation = getattr(finding_obj, "remediation", None)

        # Fallback to dictionary access if needed
        if remediation is None and isinstance(finding_obj, dict):
            remediation = finding_obj.get("remediation")

        return self._extract_remediation_text(remediation)

    def _parse_finding_data(self, finding: "SecurityFinding", vuln: Optional["Vulnerability"] = None) -> dict:
        """
        Parse the data from the SecurityFinding object

        :param Optional[Vulnerability] vuln: OCSF Vulnerability object, defaults to None
        :return: A dictionary of the parsed data
        :rtype: dict
        """
        from synqly.engine.resources.ocsf.resources.v_1_3_0.resources.securityfinding import Remediation

        # Extract remediation text from vulnerability or finding
        if vuln:
            remediation_text = self._extract_remediation_text(getattr(vuln, "remediation", None))
        else:
            finding_obj = getattr(finding, "finding", None)
            remediation_text = self._get_remediation_from_finding(finding_obj)

        finding_data = {
            "cve": None,
            "first_seen": self._determine_date("first_seen_time_dt", getattr(finding, "finding", None), vuln),
            "last_seen": self._determine_date("last_seen_time_dt", getattr(finding, "finding", None), vuln),
            "plugin_id": vuln.cve.uid if vuln else finding.finding.product_uid,
            "severity": vuln.severity if vuln and vuln.severity else finding.severity_id,
            "remediation": remediation_text,
            "title": vuln.title or finding.finding.title,
        }
        if vuln:
            finding_data["cve"] = vuln.cve.uid
        else:
            # Safely check for CVE in title, handling potential non-string values
            title_str = str(finding.finding.title) if finding.finding.title else ""
            finding_data["cve"] = finding.finding.title if "cve" in title_str.lower() else None
        try:
            finding_data["severity"] = int(finding_data["severity"])
        except ValueError:
            finding_data["severity"] = 0
        if isinstance(finding_data["remediation"], Remediation):
            finding_data["remediation"] = finding_data["remediation"].desc
        elif isinstance(finding_data["remediation"], dict):
            remediation_parts = [f"{f}: {v}\n" for f, v in finding_data["remediation"].items()]
            finding_data["remediation"] = "".join(remediation_parts)
        elif isinstance(finding_data["remediation"], list):
            finding_data["remediation"] = "\n".join(finding_data["remediation"])
        finding_data["title"] = self._determine_title(
            finding_data["title"], finding_data["cve"], finding_data["plugin_id"]
        )
        return finding_data

    @staticmethod
    def _determine_title(title: Optional[str], cve: Optional[str], plugin_id: Optional[str] = None) -> str:
        """
        Determine the title based on the provided title, cve, and plugin_id

        :param Optional[str] title: The title to determine the title for, defaults to None
        :param Optional[str] cve: The cve to determine the title for, defaults to None
        :param Optional[str] plugin_id: The plugin_id to use as fallback, defaults to None
        :return: The title (never None, uses fallbacks)
        :rtype: str
        """
        if title and cve:
            return f"{title} - {cve}"
        elif title:
            return title
        elif cve:
            return cve
        elif plugin_id:
            return f"Vulnerability {plugin_id}"
        else:
            return "Unknown Vulnerability"

    @staticmethod
    def _populate_cvs_scores(finding_obj: IntegrationFinding, vuln: Optional["Vulnerability"] = None) -> None:
        """
        Populates the CVSS scores for the provided IntegrationFinding object

        :param IntegrationFinding finding_obj: IntegrationFinding object
        :param Vulnerability vuln: OCSF Vulnerability object, defaults to None
        :rtype: None
        """
        if vuln:
            for cvs in getattr(vuln.cve, "cvss", []):
                if "3" in cvs.version:
                    finding_obj.cvss_v3_score = cvs.base_score
                elif "2" in cvs.version:
                    finding_obj.cvss_v2_score = cvs.base_score
                else:
                    finding_obj.cvss_score = cvs.base_score

        # validate that only one of the CVSS scores is populated
        if finding_obj.cvss_v3_score:
            finding_obj.cvss_v2_score = None
            finding_obj.cvss_score = None
        elif finding_obj.cvss_v2_score:
            finding_obj.cvss_v3_score = None
            finding_obj.cvss_score = None
        elif finding_obj.cvss_score:
            finding_obj.cvss_v3_score = None
            finding_obj.cvss_v2_score = None

    def _security_finding_to_regscale(
        self, connector: "Vulnerabilities", finding: SecurityFinding, **_
    ) -> list[IntegrationFinding]:
        """
        Convert OCSF SecurityFinding to RegScale IntegrationFinding

        :param "Vulnerabilities" connector: Vulnerabilities connector class object
        :param SecurityFinding finding: OCSF SecurityFinding to convert to an IntegrationFinding
        :return: List of comparable IntegrationFinding objects
        :rtype: list[IntegrationFinding]
        """
        findings: list[IntegrationFinding] = []

        def _create_finding(resource: "ResourceDetails", vuln: Optional["Vulnerability"] = None) -> IntegrationFinding:
            """
            Create an IntegrationFinding object from a resource and vulnerability

            :param ResourceDetails resource: OCSF ResourceDetails object
            :param Optional[Vulnerability] vuln: OCSF Vulnerability object, defaults to None
            :return: An IntegrationFinding object
            :rtype: IntegrationFinding
            """
            base = vuln if vuln else finding.finding
            finding_data = self._parse_finding_data(finding, vuln)
            resource_data = getattr(resource, "data", {})
            dns = resource_data.get("hostname") or resource.uid if vuln else None
            # Get IP addresses, filtering out None values
            ip_list = resource_data["ipAddresses"] if resource_data.get("ipAddresses") else [resource_data.get("ip")]
            ip_list_filtered = [ip for ip in ip_list if ip is not None]
            ip_v4s, ip_v6s = self._determine_ip_addresses(ip_list_filtered)
            ips = ip_v4s + ip_v6s

            finding_obj = IntegrationFinding(
                control_labels=[],
                category=f"{connector.integration_name} Vulnerability",
                title=finding_data["title"],
                plugin_name=connector.integration_name,
                severity=Issue.assign_severity(finding.severity),  # type: ignore
                description=base.desc,
                status=finding.status or "Open",  # type: ignore[arg-type]
                first_seen=self._datetime_to_str(finding_data["first_seen"]),
                last_seen=self._datetime_to_str(finding_data["last_seen"]),
                ip_address=", ".join(ips),
                plugin_id=finding_data["plugin_id"],
                due_date=self._determine_due_date(finding_data["severity"], connector),
                dns=dns,
                severity_int=finding_data["severity"],
                issue_title=finding_data["title"],
                cve=finding_data["cve"],
                evidence=finding.evidence,
                impact=finding.impact,
                asset_identifier=resource.uid,
                source_report=connector.integration_name,
                remediation=finding_data["remediation"],
            )

            self._populate_cvs_scores(finding_obj, vuln)

            return finding_obj

        for asset in finding.resources:
            if finding.vulnerabilities:
                findings.extend(_create_finding(asset, vuln) for vuln in finding.vulnerabilities)
            else:
                findings.append(_create_finding(asset))

        return findings

    def _security_alert_to_regscale(self, connector: "Edr", finding: Alerts, **_) -> IntegrationFinding:
        """
        Converts an OCSF Event_DetectionFinding (Alerts) to a RegScale IntegrationFinding

        :param "Edr" connector: Edr connector class object
        :param Alerts finding: OCSF Event_DetectionFinding (Alerts) to convert to an IntegrationFinding
        :return: Comparable IntegrationFinding object
        :rtype: IntegrationFinding
        """
        from regscale.models.regscale_models.issue import IssueStatus

        asset = finding.device
        vuln = finding.finding_info

        return IntegrationFinding(
            control_labels=[],
            category=f"{connector.integration_name} Vulnerability",
            title=vuln.title,
            plugin_name=connector.integration_name,
            severity=Issue.assign_severity(finding.severity),  # type: ignore
            description=vuln.desc or finding.comment,
            status=IssueStatus.Open,
            first_seen=self._datetime_to_str(vuln.first_seen_time_dt),
            last_seen=self._datetime_to_str(vuln.last_seen_time_dt),
            ip_address=asset.ip,
            plugin_id=vuln.product_uid,
            dns=asset.hostname,
            issue_title=vuln.title,
            impact=finding.impact,
            asset_identifier=asset.uid,
            source_report=connector.integration_name,
        )

    def _datetime_to_str(self, date_time: Optional[datetime] = None) -> str:
        """
        Convert a datetime object to a string

        :param Optional[datetime] date_time: The datetime object to convert, defaults to None
        :return: The datetime as a string
        :rtype: str
        """
        from regscale.core.utils.date import datetime_str

        return datetime_str(date_time, self.date_format)

    @staticmethod
    def _map_ticket_priority(severity: Union[str, int]) -> Priority:
        """
        Map RegScale severity to OCSF priority

        :param Union[str, int] severity: RegScale severity (string or integer)
        :return: OCSF priority
        :rtype: Priority
        """
        # Handle integer severity values (0-4 scale commonly used)
        if isinstance(severity, int):
            if severity >= 4:
                return Priority.HIGH
            elif severity >= 2:
                return Priority.MEDIUM
            else:
                return Priority.LOW
        # Handle string severity values
        severity_str = str(severity).lower()
        if "high" in severity_str or "critical" in severity_str:
            return Priority.HIGH
        elif "moderate" in severity_str or "medium" in severity_str:
            return Priority.MEDIUM
        else:
            return Priority.LOW

    def _determine_due_date(self, severity: Union[str, int], connector: Union["Ticketing", "Vulnerabilities"]) -> str:
        """
        Determine the due date based on the provided severity

        :param Union[str, int] severity: RegScale severity (string or integer)
        :param Union["Ticketing", "Vulnerabilities"] connector: Ticketing or Vulnerabilities connector class object
        :return: Due date for the issue
        :rtype: str
        """
        # Handle integer severity values (0-4 scale commonly used)
        if isinstance(severity, int):
            if severity >= 4:
                default_days = 30
            elif severity >= 2:
                default_days = 90
            else:
                default_days = 180
        else:
            # Handle string severity values
            severity_str = str(severity).lower()
            if "high" in severity_str or "critical" in severity_str:
                default_days = 30
            elif "medium" in severity_str or "moderate" in severity_str:
                default_days = 90
            else:
                default_days = 180
        # Convert severity to string for Issue.get_due_date which expects Union[IssueSeverity, str]
        severity_str = str(severity) if isinstance(severity, int) else severity
        return Issue.get_due_date(severity_str, connector.app.config, connector.integration, default_days=default_days)

    def _regscale_issue_to_ticket(self, regscale_issue: Issue, **kwargs) -> CreateTicketRequest:
        """
        Maps a RegScale issue to a JIRA issue

        :param Issue regscale_issue: RegScale issue object
        :return: Synqly CreateTicketRequest object
        :rtype: CreateTicketRequest
        """
        description_parts = []
        for key, value in regscale_issue.dict().items():
            if key != "id" and value:
                description_parts.append(f"{key.title()}: {value}\n")
        description = "".join(description_parts)
        if project := kwargs.get("default_project"):
            kwargs.pop("default_project")
            return engine.CreateTicketRequest(
                name=regscale_issue.title,
                description=f"RegScale Issue #{regscale_issue.id}:\n{description}",
                summary=regscale_issue.title,
                creator=kwargs.get("creator", "RegScale CLI"),
                priority=self._map_ticket_priority(regscale_issue.severityLevel),
                project=project,
                **kwargs,
            )
        else:
            return engine.CreateTicketRequest(
                name=regscale_issue.title,
                description=f"RegScale Issue #{regscale_issue.id}:\n{description}",
                summary=regscale_issue.title,
                creator=kwargs.get("creator", "RegScale CLI"),
                priority=self._map_ticket_priority(regscale_issue.severityLevel),
                **kwargs,
            )
