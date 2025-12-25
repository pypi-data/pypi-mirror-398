"""Processors for Wiz integration - handles business logic and data transformation."""

from regscale.integrations.commercial.wizv2.processors.finding import (
    FindingConsolidator,
    FindingToIssueProcessor,
)

__all__ = [
    "FindingConsolidator",
    "FindingToIssueProcessor",
]
