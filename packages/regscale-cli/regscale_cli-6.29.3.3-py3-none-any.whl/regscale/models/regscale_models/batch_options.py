"""
Batch operation options for RegScale API endpoints.

This module provides TypedDict definitions for the options parameters used in batch
create/update operations for assets, issues, and vulnerabilities. These typed dictionaries
ensure type safety when constructing options for the RegScale batch API endpoints.

NOTE: All keys must be camelCase to match the server's JSON deserialization expectations.
"""

from typing import List
from typing_extensions import TypedDict


class AssetBatchOptions(TypedDict, total=False):
    """
    Options for batch asset create/update operations.

    Attributes:
        source: The source system identifier for the assets.
        uniqueKeyFields: List of field names used to identify unique assets.
        enableMopUp: Whether to enable mop-up processing for orphaned assets.
        mopUpStatus: The status to set for assets during mop-up processing.
        batchSize: The number of assets to process per batch.
    """

    source: str
    uniqueKeyFields: List[str]
    enableMopUp: bool
    mopUpStatus: str
    batchSize: int


class IssueBatchOptions(TypedDict, total=False):
    """
    Options for batch issue create/update operations.

    Attributes:
        source: The source system identifier for the issues.
        uniqueKeyFields: List of field names used to identify unique issues.
        enableMopUp: Whether to enable mop-up processing for orphaned issues.
        mopUpStatus: The status to set for issues during mop-up processing.
        performValidation: Whether to perform validation on issues before processing.
        poamCreation: Whether to automatically create POAMs for qualifying issues.
        parentId: The ID of the parent record (e.g., security plan ID).
        parentModule: The module type of the parent record.
        issueOwnerId: The user ID to assign as the issue owner.
        assetIdentifierFieldName: The field name used to identify associated assets.
        batchSize: The number of issues to process per batch.
    """

    source: str
    uniqueKeyFields: List[str]
    enableMopUp: bool
    mopUpStatus: str
    performValidation: bool
    poamCreation: bool
    parentId: int
    parentModule: str
    issueOwnerId: str
    assetIdentifierFieldName: str
    batchSize: int


class VulnerabilityBatchOptions(TypedDict, total=False):
    """
    Options for batch vulnerability create/update operations.

    Attributes:
        source: The source system identifier for the vulnerabilities.
        uniqueKeys: List of field names used to identify unique vulnerabilities.
            Note: This differs from other batch options which use 'uniqueKeyFields'.
        enableMopUp: Whether to enable mop-up processing for orphaned vulnerabilities.
        mopUpStatus: The status to set for vulnerabilities during mop-up processing.
        enableAssetDiscovery: Whether to enable automatic asset discovery and linking.
        suppressAssetNotFoundWarnings: Whether to suppress warnings when assets are not found.
        poamCreation: Whether to automatically create POAMs for qualifying vulnerabilities.
        parentId: The ID of the parent record (e.g., security plan ID).
        parentModule: The module type of the parent record.
        batchSize: The number of vulnerabilities to process per batch.
    """

    source: str
    uniqueKeys: List[str]
    enableMopUp: bool
    mopUpStatus: str
    enableAssetDiscovery: bool
    suppressAssetNotFoundWarnings: bool
    poamCreation: bool
    parentId: int
    parentModule: str
    batchSize: int
