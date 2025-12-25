#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GCP Resource Collectors Package.

This package contains service-specific collectors for GCP resources:
- ComputeCollector: Compute Engine, GKE, Cloud Run
- StorageCollector: Cloud Storage, Filestore
- DatabaseCollector: Cloud SQL, Spanner, Bigtable
- NetworkingCollector: VPC, Load Balancers, Cloud NAT
- IAMCollector: IAM policies, service accounts
- SecurityCollector: SCC findings, Security Health Analytics
- KMSCollector: Cloud KMS keys
- LoggingCollector: Cloud Logging, Audit Logs
"""

__all__ = [
    "ComputeCollector",
    "StorageCollector",
    "DatabaseCollector",
    "NetworkingCollector",
    "IAMCollector",
    "SecurityCollector",
    "KMSCollector",
    "LoggingCollector",
]


def __getattr__(name: str):
    """Lazy import for collector classes."""
    if name == "ComputeCollector":
        from regscale.integrations.commercial.gcp.inventory.resources.compute import ComputeCollector

        return ComputeCollector
    if name == "StorageCollector":
        from regscale.integrations.commercial.gcp.inventory.resources.storage import StorageCollector

        return StorageCollector
    if name == "DatabaseCollector":
        from regscale.integrations.commercial.gcp.inventory.resources.database import DatabaseCollector

        return DatabaseCollector
    if name == "NetworkingCollector":
        from regscale.integrations.commercial.gcp.inventory.resources.networking import NetworkingCollector

        return NetworkingCollector
    if name == "IAMCollector":
        from regscale.integrations.commercial.gcp.inventory.resources.iam import IAMCollector

        return IAMCollector
    if name == "SecurityCollector":
        from regscale.integrations.commercial.gcp.inventory.resources.security import SecurityCollector

        return SecurityCollector
    if name == "KMSCollector":
        from regscale.integrations.commercial.gcp.inventory.resources.kms import KMSCollector

        return KMSCollector
    if name == "LoggingCollector":
        from regscale.integrations.commercial.gcp.inventory.resources.logging import LoggingCollector

        return LoggingCollector
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
