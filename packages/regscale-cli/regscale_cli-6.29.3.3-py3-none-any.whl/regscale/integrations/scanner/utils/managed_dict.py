#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Managed default dictionary utility for scanner integrations.

This module provides a thread-safe default dictionary implementation
that uses ThreadSafeDict for concurrent access in multi-threaded
scanner operations.
"""
from typing import Any, Callable, Generic, Optional, TypeVar

from regscale.utils.threading import ThreadSafeDict

K = TypeVar("K")  # Key type
V = TypeVar("V")  # Value type


class ManagedDefaultDict(Generic[K, V]):
    """
    A thread-safe default dictionary that uses a multiprocessing Manager.

    :param default_factory: A callable that produces default values for missing keys
    """

    def __init__(self, default_factory: Callable[[], V]):
        self.store: ThreadSafeDict[Any, Any] = ThreadSafeDict()  # type: ignore[type-arg]
        self.default_factory = default_factory

    def __getitem__(self, key: Any) -> Any:
        """
        Get the item from the store

        :param Any key: Key to get the item from the store
        :return: Value from the store
        :rtype: Any
        """
        if key not in self.store:
            self.store[key] = self.default_factory()
        return self.store[key]

    def __setitem__(self, key: Any, value: Any) -> None:
        """
        Set the item in the store

        :param Any key: Key to set the item in the store
        :param Any value: Value to set in the store
        :rtype: None
        """
        self.store[key] = value

    def __contains__(self, key: Any) -> bool:
        """
        Check if the key is in the store

        :param Any key: Key to check in the store
        :return: Whether the key is in the store
        :rtype: bool
        """
        return key in self.store

    def __len__(self) -> int:
        """
        Get the length of the store

        :return: Number of items in the store
        :rtype: int
        """
        return len(self.store)

    def get(self, key: Any, default: Optional[Any] = None) -> Optional[Any]:
        """
        Get the value from the store

        :param Any key: Key to get the value from the store
        :param Optional[Any] default: Default value to return if the key is not in the store, defaults to None
        :return: The value from the store, or the default value
        :rtype: Optional[Any]
        """
        if key not in self.store:
            return default
        return self.store[key]

    def items(self) -> Any:
        """
        Get the items from the store

        :return: Items from the store
        :rtype: Any
        """
        return self.store.items()

    def keys(self) -> Any:
        """
        Get the keys from the store

        :return: Keys from the store
        :rtype: Any
        """
        return self.store.keys()

    def values(self) -> Any:
        """
        Get the values from the store

        :return: Values in the store
        :rtype: Any
        """
        return self.store.values()

    def update(self, *args, **kwargs) -> None:
        """
        Update the store

        :rtype: None
        """
        self.store.update(*args, **kwargs)
