# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from easydiffraction.core.collection import CollectionBase
from easydiffraction.core.guard import GuardedBase
from easydiffraction.core.parameters import GenericDescriptorBase
from easydiffraction.core.validation import checktype
from easydiffraction.io.cif.serialize import category_collection_from_cif
from easydiffraction.io.cif.serialize import category_collection_to_cif
from easydiffraction.io.cif.serialize import category_item_from_cif
from easydiffraction.io.cif.serialize import category_item_to_cif


class CategoryItem(GuardedBase):
    """Base class for items in a category collection."""

    # TODO: Set different default priorities for CategoryItem and
    #  CategoryCollection and use them when serializing to CIF!
    # TODO: Common for all categories
    _update_priority = 10  # Default. Lower values run first.

    def __str__(self) -> str:
        """Human-readable representation of this component."""
        name = self._log_name
        params = ', '.join(f'{p.name}={p.value!r}' for p in self.parameters)
        return f'<{name} ({params})>'

    # TODO: Common for all categories
    def _update(self, called_by_minimizer=False):
        del called_by_minimizer
        pass

    @property
    def unique_name(self):
        parts = [
            self._identity.datablock_entry_name,
            self._identity.category_code,
            self._identity.category_entry_name,
        ]
        # Convert all parts to strings and filter out None/empty values
        str_parts = [str(part) for part in parts if part is not None]
        return '.'.join(str_parts)

    @property
    def parameters(self):
        return [v for v in vars(self).values() if isinstance(v, GenericDescriptorBase)]

    @property
    def as_cif(self) -> str:
        """Return CIF representation of this object."""
        return category_item_to_cif(self)

    def from_cif(self, block, idx=0):
        """Populate this item from a CIF block."""
        category_item_from_cif(self, block, idx)


class CategoryCollection(CollectionBase):
    """Handles loop-style category containers (e.g. AtomSites).

    Each item is a CategoryItem (component).
    """

    # TODO: Common for all categories
    _update_priority = 10  # Default. Lower values run first.

    def __str__(self) -> str:
        """Human-readable representation of this component."""
        name = self._log_name
        size = len(self)
        return f'<{name} collection ({size} items)>'

    # TODO: Common for all categories
    def _update(self, called_by_minimizer=False):
        del called_by_minimizer
        pass

    @property
    def unique_name(self):
        return None

    @property
    def parameters(self):
        """All parameters from all items in this collection."""
        params = []
        for item in self._items:
            params.extend(item.parameters)
        return params

    @property
    def as_cif(self) -> str:
        """Return CIF representation of this object."""
        return category_collection_to_cif(self)

    def from_cif(self, block):
        """Populate this collection from a CIF block."""
        category_collection_from_cif(self, block)

    @checktype
    def _add(self, item) -> None:
        """Add an item to the collection."""
        self[item._identity.category_entry_name] = item

    # TODO: Disallow args and only allow kwargs?
    # TODO: Check kwargs as for, e.g.,
    #  ExperimentFactory.create(**kwargs)?
    @checktype
    def add(self, *args, **kwargs) -> None:
        """Create and add a new child instance from the provided
        arguments.
        """
        child_obj = self._item_type(*args, **kwargs)
        self._add(child_obj)
