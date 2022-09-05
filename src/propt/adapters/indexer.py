"""An indexer to store collection and easily look for object given a key."""
from __future__ import annotations

from collections import defaultdict
from typing import Callable, Hashable, TypeVar, Iterable

TKey = TypeVar("TKey", bound=Hashable)
"""Type of the key"""
TObj = TypeVar("TObj")
"""Type of the objects in the collection."""
OneToOneGetter = Callable[[TObj], TKey]
"""Function returning the key for an object."""
MultiToMultiGetter = Callable[[TObj], Iterable[TKey]]
"""Function returning the keys for an object."""


class OneToOneIndexer(dict[TKey, TObj]):
    """Index a collection where the object has one key and one key matches one object only."""

    def __init__(self, idx_getter: OneToOneGetter):
        super().__init__()
        self._idx_getter = idx_getter

    def set_collection(self, collection: Iterable[TObj]) -> None:
        self.clear()
        for obj in collection:
            self[self._idx_getter(obj)] = obj


class MultiToMultiIndexer(defaultdict[TKey, list[TObj]]):
    """Index a collection where an object must index under several keys and keys have several objects."""

    def __init__(self, idx_getter: MultiToMultiGetter):
        super().__init__(list)
        self._idx_getter = idx_getter

    def set_collection(self, collection: Iterable[TObj]) -> None:
        self.clear()
        for obj in collection:
            for key in self._idx_getter(obj):
                self[key].append(obj)
