#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Control Cache Module.

This module provides a thread-safe cache for control and CCI-related mappings
used by scanner integrations.
"""

import logging
import threading
from collections import defaultdict
from typing import Dict, Optional, Set

from regscale.models import regscale_models
from regscale.utils.threading import ThreadSafeDict

logger = logging.getLogger("regscale")


class ControlCache:
    """
    Thread-safe cache for control and CCI-related mappings.

    This class encapsulates the caching functionality for:
    - CCI to control ID mapping
    - Control label to implementation ID mapping
    - Control ID to implementation ID mapping

    All mappings are lazily loaded on first access.

    :param int plan_id: The ID of the security plan
    :param str parent_module: The parent module string (e.g., "SecurityPlans" or "Components")
    """

    def __init__(
        self,
        plan_id: int,
        parent_module: str,
        enable_cci_mapping: bool = True,
    ) -> None:
        """
        Initialize the ControlCache.

        :param int plan_id: The ID of the security plan
        :param str parent_module: The parent module string
        :param bool enable_cci_mapping: Whether to enable CCI mapping, defaults to True
        """
        self.plan_id = plan_id
        self.parent_module = parent_module
        self._enable_cci_mapping = enable_cci_mapping

        # CCI to control ID mapping
        self._cci_to_control_map: ThreadSafeDict[str, Set[int]] = ThreadSafeDict()
        self._no_ccis: bool = not enable_cci_mapping  # Skip loading if disabled
        self._cci_map_loaded: bool = False
        self._cci_map_lock: threading.Lock = threading.Lock()

        # Control label to implementation ID mapping
        self._control_label_to_impl_id_map: Dict[str, int] = {}
        self._control_label_map_loaded: bool = False
        self._control_label_map_lock: threading.Lock = threading.Lock()

        # Control ID to implementation ID mapping
        self._control_id_to_impl_id_map: Dict[int, int] = {}
        self._control_id_map_loaded: bool = False
        self._control_id_map_lock: threading.Lock = threading.Lock()

        # Reverse mapping: implementation ID to control label
        self._impl_id_to_control_label_map: Dict[int, str] = {}

    def get_cci_to_control_map(self) -> ThreadSafeDict[str, Set[int]]:
        """
        Get the CCI to control ID mapping.

        Lazily loads the mapping from the API on first access.
        Thread-safe with double-checked locking.

        :return: Dictionary mapping CCI strings to sets of control IDs
        :rtype: ThreadSafeDict[str, Set[int]]
        """
        # Fast path: if we know there are no CCIs, return immediately
        if self._no_ccis:
            return self._cci_to_control_map

        # Fast path: if already loaded, return immediately
        if self._cci_map_loaded:
            return self._cci_to_control_map

        with self._cci_map_lock:
            # Double-check inside the lock
            if self._cci_map_loaded:
                return self._cci_to_control_map

            logger.debug("Loading CCI to control map...")
            try:
                loaded_map = regscale_models.map_ccis_to_control_ids(parent_id=self.plan_id)
                if loaded_map:
                    self._cci_to_control_map.update(loaded_map)
                else:
                    self._no_ccis = True
            except Exception as e:
                logger.debug("Could not load CCI to control map: %s", e)
                self._no_ccis = True
            finally:
                # Mark as loaded regardless of success/failure to prevent repeated attempts
                self._cci_map_loaded = True

            return self._cci_to_control_map

    def get_control_to_cci_map(self) -> Dict[int, Set[str]]:
        """
        Get the control ID to CCI mapping (reverse of CCI to control map).

        :return: Dictionary mapping control IDs to sets of CCI strings
        :rtype: Dict[int, Set[str]]
        """
        control_id_to_cci_map: Dict[int, Set[str]] = defaultdict(set)
        for cci, control_ids in self.get_cci_to_control_map().items():
            for control_id in control_ids:
                control_id_to_cci_map[control_id].add(cci)
        return control_id_to_cci_map

    def get_implementation_id_for_cci(self, cci: Optional[str]) -> Optional[int]:
        """
        Get the control implementation ID for a CCI.

        Falls back to CCI-000366 if the provided CCI is not found.

        :param Optional[str] cci: The CCI string (e.g., "CCI-000001")
        :return: The control implementation ID, or None if not found
        :rtype: Optional[int]
        """
        if not cci:
            return None

        cci_to_control_map = self.get_cci_to_control_map()
        if cci not in cci_to_control_map:
            cci = "CCI-000366"

        control_ids = cci_to_control_map.get(cci, set())
        if control_ids:
            for control_id in control_ids:
                impl_id = self.get_control_id_to_implementation_map().get(control_id)
                if impl_id is not None:
                    return impl_id
        return None

    def get_implementation_id_for_control_label(self, label: str) -> Optional[int]:
        """
        Get the implementation ID for a control label.

        :param str label: The control label (e.g., "AC-1")
        :return: The implementation ID, or None if not found
        :rtype: Optional[int]
        """
        return self.get_control_label_to_implementation_map().get(label)

    def get_control_label_to_implementation_map(self) -> Dict[str, int]:
        """
        Get the control label to implementation ID mapping.

        Lazily loads from the API on first access.

        :return: Dictionary mapping control labels to implementation IDs
        :rtype: Dict[str, int]
        """
        if self._control_label_map_loaded:
            return self._control_label_to_impl_id_map

        with self._control_label_map_lock:
            if self._control_label_map_loaded:
                return self._control_label_to_impl_id_map

            logger.debug("Loading control label to implementation ID map...")
            try:
                self._control_label_to_impl_id_map = (
                    regscale_models.ControlImplementation.get_control_label_map_by_parent(
                        parent_id=self.plan_id, parent_module=self.parent_module
                    )
                )
                # Build reverse mapping
                self._impl_id_to_control_label_map = {v: k for k, v in self._control_label_to_impl_id_map.items()}
            except Exception as e:
                logger.debug("Could not load control label map: %s", e)
                self._control_label_to_impl_id_map = {}
                self._impl_id_to_control_label_map = {}
            finally:
                self._control_label_map_loaded = True

            return self._control_label_to_impl_id_map

    def get_control_id_to_implementation_map(self) -> Dict[int, int]:
        """
        Get the control ID to implementation ID mapping.

        Lazily loads from the API on first access.

        :return: Dictionary mapping control IDs to implementation IDs
        :rtype: Dict[int, int]
        """
        if self._control_id_map_loaded:
            return self._control_id_to_impl_id_map

        with self._control_id_map_lock:
            if self._control_id_map_loaded:
                return self._control_id_to_impl_id_map

            logger.debug("Loading control ID to implementation ID map...")
            try:
                self._control_id_to_impl_id_map = regscale_models.ControlImplementation.get_control_id_map_by_parent(
                    parent_id=self.plan_id, parent_module=self.parent_module
                )
            except Exception as e:
                logger.debug("Could not load control ID map: %s", e)
                self._control_id_to_impl_id_map = {}
            finally:
                self._control_id_map_loaded = True

            return self._control_id_to_impl_id_map

    def get_implementation_id_to_control_label_map(self) -> Dict[int, str]:
        """
        Get the implementation ID to control label mapping (reverse).

        :return: Dictionary mapping implementation IDs to control labels
        :rtype: Dict[int, str]
        """
        # Ensure the forward map is loaded first
        self.get_control_label_to_implementation_map()
        return self._impl_id_to_control_label_map

    def load_cci_map(self) -> None:
        """
        Explicitly load the CCI to control ID mapping.

        This can be called to preload the cache before threaded operations.

        :rtype: None
        """
        _ = self.get_cci_to_control_map()

    def load_control_maps(self) -> None:
        """
        Explicitly load all control-related mappings.

        This can be called to preload the cache before threaded operations.

        :rtype: None
        """
        _ = self.get_control_label_to_implementation_map()
        _ = self.get_control_id_to_implementation_map()

    def clear(self) -> None:
        """
        Clear all cached mappings.

        :rtype: None
        """
        with self._cci_map_lock:
            self._cci_to_control_map.clear()
            self._no_ccis = False
            self._cci_map_loaded = False

        with self._control_label_map_lock:
            self._control_label_to_impl_id_map = {}
            self._impl_id_to_control_label_map = {}
            self._control_label_map_loaded = False

        with self._control_id_map_lock:
            self._control_id_to_impl_id_map = {}
            self._control_id_map_loaded = False

    @property
    def is_cci_map_loaded(self) -> bool:
        """
        Check if the CCI map has been loaded.

        :return: True if the CCI map has been loaded
        :rtype: bool
        """
        return self._cci_map_loaded

    @property
    def has_ccis(self) -> bool:
        """
        Check if CCIs are available.

        Note: This will trigger loading the CCI map if not already loaded.

        :return: True if CCIs are available
        :rtype: bool
        """
        _ = self.get_cci_to_control_map()
        return not self._no_ccis
