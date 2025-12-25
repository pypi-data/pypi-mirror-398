#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Wiz Variables"""

from regscale.core.app.utils.variables import RsVariableType, RsVariablesMeta

# Define constants locally to avoid circular import with core.constants
_RECOMMENDED_WIZ_INVENTORY_TYPES = [
    # Compute resources
    "CONTAINER",
    "CONTAINER_GROUP",
    "CONTAINER_IMAGE",
    "POD",
    "SERVERLESS",
    "SERVERLESS_PACKAGE",
    "VIRTUAL_DESKTOP",
    "VIRTUAL_MACHINE",
    "VIRTUAL_MACHINE_IMAGE",
    # Network and exposure
    "API_GATEWAY",
    "CDN",
    "CERTIFICATE",
    "DNS_RECORD",
    "ENDPOINT",
    "FIREWALL",
    "GATEWAY",
    "LOAD_BALANCER",
    "MANAGED_CERTIFICATE",
    "NETWORK_ADDRESS",
    "NETWORK_INTERFACE",
    "PRIVATE_ENDPOINT",
    "PRIVATE_LINK",
    "PROXY",
    "WEB_SERVICE",
    # Storage and data
    "BACKUP_SERVICE",
    "BUCKET",
    "DATABASE",
    "DATA_WORKLOAD",
    "DB_SERVER",
    "FILE_SYSTEM_SERVICE",
    "SECRET",
    "SECRET_CONTAINER",
    "STORAGE_ACCOUNT",
    "VOLUME",
    # Identity and access management
    "ACCESS_ROLE",
    "AUTHENTICATION_CONFIGURATION",
    "IAM_BINDING",
    "RAW_ACCESS_POLICY",
    "SERVICE_ACCOUNT",
    # Development and CI/CD
    "APPLICATION",
    "CICD_SERVICE",
    "CONFIG_MAP",
    "CONTAINER_REGISTRY",
    "CONTAINER_SERVICE",
    # Kubernetes resources
    "CONTROLLER_REVISION",
    "KUBERNETES_CLUSTER",
    "KUBERNETES_INGRESS",
    "KUBERNETES_NODE",
    "KUBERNETES_SERVICE",
    "NAMESPACE",
    # Infrastructure and management
    "CLOUD_LOG_CONFIGURATION",
    "CLOUD_ORGANIZATION",
    "DOMAIN",
    "EMAIL_SERVICE",
    "ENCRYPTION_KEY",
    "MANAGEMENT_SERVICE",
    "MESSAGING_SERVICE",
    "REGISTERED_DOMAIN",
    "RESOURCE_GROUP",
    "SERVICE_CONFIGURATION",
    "SUBNET",
    "SUBSCRIPTION",
    "VIRTUAL_NETWORK",
]

_DEFAULT_WIZ_HARDWARE_TYPES = [
    # CloudResource types
    "VIRTUAL_MACHINE",
    "VIRTUAL_MACHINE_IMAGE",
    "CONTAINER",
    "CONTAINER_IMAGE",
    "DB_SERVER",
    # technology deploymentModels
    "SERVER_APPLICATION",
    "CLIENT_APPLICATION",
    "VIRTUAL_APPLIANCE",
]


class WizVariables(metaclass=RsVariablesMeta):
    """
    Wiz Variables class to define class-level attributes with type annotations and examples
    """

    # Define class-level attributes with type annotations and examples
    wizFullPullLimitHours: RsVariableType(int, 8)  # type: ignore
    wizUrl: RsVariableType(str, "https://api.us27.app.wiz.io/graphql", required=False)  # type: ignore
    wizIssueFilterBy: RsVariableType(
        str,
        '{"projectId": ["xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"], "type": ["API_GATEWAY"]}',
        default={},
        required=False,
    )  # type: ignore
    wizInventoryFilterBy: RsVariableType(
        str,
        '{"projectId": ["xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"], "type": ["API_GATEWAY"]}',
        default="""{"type": ["%s"] }""" % '","'.join(_RECOMMENDED_WIZ_INVENTORY_TYPES),  # type: ignore
    )  # type: ignore
    wizAccessToken: RsVariableType(str, "", sensitive=True, required=False)  # type: ignore
    wizClientId: RsVariableType(str, "", sensitive=True)  # type: ignore
    wizClientSecret: RsVariableType(str, "", sensitive=True)  # type: ignore
    wizLastInventoryPull: RsVariableType(str, "2022-01-01T00:00:00Z", required=False)  # type: ignore
    useWizHardwareAssetTypes: RsVariableType(bool, False, required=False)  # type: ignore
    wizHardwareAssetTypes: RsVariableType(
        list,
        '["CONTAINER", "CONTAINER_IMAGE", "VIRTUAL_MACHINE", "VIRTUAL_MACHINE_IMAGE", "DB_SERVER", '
        '"CLIENT_APPLICATION", "SERVER_APPLICATION", "VIRTUAL_APPLIANCE"]',
        default=_DEFAULT_WIZ_HARDWARE_TYPES,
        required=False,
    )  # type: ignore
    wizReportAge: RsVariableType(int, "14", default=14, required=False)  # type: ignore
