# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Lightweight container for guarded items with name-based indexing.

`CollectionBase` maintains an ordered list of items and a lazily rebuilt
index by the item's identity key. It supports dict-like access for get,
set and delete, along with iteration over the items.
"""

from __future__ import annotations

from easydiffraction.core.guard import GuardedBase


class CollectionBase(GuardedBase):
    """A minimal collection with stable iteration and name indexing.

    Args:
        item_type: Type of items accepted by the collection. Used for
            validation and tooling; not enforced at runtime here.
    """

    def __init__(self, item_type) -> None:
        super().__init__()
        self._items: list = []
        self._index: dict = {}
        self._item_type = item_type

    def __getitem__(self, name: str):
        """Return an item by its identity key.

        Rebuilds the internal index on a cache miss to stay consistent
        with recent mutations.
        """
        try:
            return self._index[name]
        except KeyError:
            self._rebuild_index()
            return self._index[name]

    def __setitem__(self, name: str, item) -> None:
        """Insert or replace an item under the given identity key."""
        # Check if item with same identity exists; if so, replace it
        for i, existing_item in enumerate(self._items):
            if existing_item._identity.category_entry_name == name:
                self._items[i] = item
                self._rebuild_index()
                return
        # Otherwise append new item
        item._parent = self  # Explicitly set the parent for the item
        self._items.append(item)
        self._rebuild_index()

    def __delitem__(self, name: str) -> None:
        """Delete an item by key or raise ``KeyError`` if missing."""
        # Remove from _items by identity entry name
        for i, item in enumerate(self._items):
            if item._identity.category_entry_name == name:
                object.__setattr__(item, '_parent', None)  # Unlink the parent before removal
                del self._items[i]
                self._rebuild_index()
                return
        raise KeyError(name)

    def __iter__(self):
        """Iterate over items in insertion order."""
        return iter(self._items)

    def __len__(self) -> int:
        """Return the number of items in the collection."""
        return len(self._items)

    def _key_for(self, item):
        """Return the identity key for ``item`` (category or
        datablock).
        """
        return item._identity.category_entry_name or item._identity.datablock_entry_name

    def _rebuild_index(self) -> None:
        """Rebuild the name-to-item index from the ordered item list."""
        self._index.clear()
        for item in self._items:
            key = self._key_for(item)
            if key:
                self._index[key] = item

    def keys(self):
        """Yield keys for all items in insertion order."""
        return (self._key_for(item) for item in self._items)

    def values(self):
        """Yield items in insertion order."""
        return (item for item in self._items)

    def items(self):
        """Yield ``(key, item)`` pairs in insertion order."""
        return ((self._key_for(item), item) for item in self._items)

    @property
    def names(self):
        """List of all item keys in the collection."""
        return list(self.keys())
