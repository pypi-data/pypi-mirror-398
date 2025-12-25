#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Framework Handler Registry for dynamic handler selection."""

import logging
from typing import Dict, List, Optional

from regscale.integrations.framework_handlers.base import FrameworkHandler

logger = logging.getLogger("regscale")


class FrameworkHandlerRegistry:
    """
    Registry for framework handlers with automatic detection.

    Handlers are registered with a priority and selected based on
    which handler can best handle a given control ID.
    """

    def __init__(self) -> None:
        """Initialize the registry with default handlers."""
        self._handlers: Dict[str, FrameworkHandler] = {}
        self._priority_order: List[str] = []

        # Register default handlers
        self._register_default_handlers()

    def _register_default_handlers(self) -> None:
        """Register all default framework handlers."""
        # Import handlers here to avoid circular imports
        from regscale.integrations.framework_handlers.cis_handler import CISHandler
        from regscale.integrations.framework_handlers.cmmc_handler import CMMCHandler
        from regscale.integrations.framework_handlers.iso_handler import ISOHandler
        from regscale.integrations.framework_handlers.nist_handler import NISTHandler
        from regscale.integrations.framework_handlers.soc2_handler import SOC2Handler

        default_handlers = [
            CMMCHandler(),  # Priority 5 - check before CIS
            NISTHandler(),  # Priority 10
            ISOHandler(),  # Priority 10
            SOC2Handler(),  # Priority 10
            CISHandler(),  # Priority 15 - check after CMMC
        ]

        for handler in default_handlers:
            self.register(handler)

    def register(self, handler: FrameworkHandler) -> None:
        """
        Register a framework handler.

        :param FrameworkHandler handler: Handler instance to register
        """
        self._handlers[handler.framework_name] = handler

        # Re-sort by priority
        self._priority_order = sorted(self._handlers.keys(), key=lambda name: self._handlers[name].detection_priority)

        logger.debug("Registered handler %s with priority %d", handler.framework_name, handler.detection_priority)

    def get_handler(self, framework_name: str) -> Optional[FrameworkHandler]:
        """
        Get a specific framework handler by name.

        :param str framework_name: Name of the framework
        :return: Handler if found, None otherwise
        :rtype: Optional[FrameworkHandler]
        """
        return self._handlers.get(framework_name)

    def detect_handler(self, control_id: str) -> Optional[FrameworkHandler]:
        """
        Detect the appropriate handler for a control ID.

        Handlers are checked in priority order (lowest priority number first).

        :param str control_id: Control ID to detect handler for
        :return: Appropriate handler or None
        :rtype: Optional[FrameworkHandler]
        """
        if not control_id:
            return None

        for framework_name in self._priority_order:
            handler = self._handlers[framework_name]
            if handler.matches(control_id):
                logger.debug("Detected framework %s for control %s", framework_name, control_id)
                return handler

        logger.debug("No specific handler matched for control %s", control_id)
        return None

    def get_all_handlers(self) -> List[FrameworkHandler]:
        """
        Get all registered handlers in priority order.

        :return: List of handlers
        :rtype: List[FrameworkHandler]
        """
        return [self._handlers[name] for name in self._priority_order]


# Global singleton registry
_registry: Optional[FrameworkHandlerRegistry] = None


def get_registry() -> FrameworkHandlerRegistry:
    """
    Get the global framework handler registry.

    :return: Global registry instance
    :rtype: FrameworkHandlerRegistry
    """
    global _registry
    if _registry is None:
        _registry = FrameworkHandlerRegistry()
    return _registry
