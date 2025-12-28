# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from typeguard import typechecked

from easydiffraction.core.category import CategoryCollection
from easydiffraction.core.category import CategoryItem
from easydiffraction.core.collection import CollectionBase
from easydiffraction.core.guard import GuardedBase
from easydiffraction.core.parameters import Parameter


class DatablockItem(GuardedBase):
    """Base class for items in a datablock collection."""

    def __init__(self):
        super().__init__()
        self._need_categories_update = False

    def __str__(self) -> str:
        """Human-readable representation of this component."""
        name = self._log_name
        items = getattr(self, '_items', None)
        return f'<{name} ({items})>'

    def _update_categories(
        self,
        called_by_minimizer=False,
    ) -> None:
        # TODO: Make abstract method and implement in subclasses.
        # This should call apply_symmetry and apply_constraints in the
        # case of sample models. In the case of experiments, it should
        # run calculations to update the "data" categories.
        # Any parameter change should set _need_categories_update to
        # True.
        # Calling as_cif or data getter should first check this flag
        # and call this method if True.
        # Should this be also called when parameters are accessed? E.g.
        # if one change background coefficients, then access the
        # background points in the data category?
        # return
        # if not self._need_categories_update:
        #    return

        for category in self.categories:
            category._update(called_by_minimizer=called_by_minimizer)

        self._need_categories_update = False

    @property
    def unique_name(self):
        return self._identity.datablock_entry_name

    @property
    def categories(self):
        cats = [
            v for v in vars(self).values() if isinstance(v, (CategoryItem, CategoryCollection))
        ]
        # Sort by _update_priority (lower values first)
        return sorted(cats, key=lambda c: type(c)._update_priority)

    @property
    def parameters(self):
        """All parameters from all categories contained in this
        datablock.
        """
        params = []
        for v in self.categories:
            params.extend(v.parameters)
        return params

    @property
    def as_cif(self) -> str:
        """Return CIF representation of this object."""
        from easydiffraction.io.cif.serialize import datablock_item_to_cif

        self._update_categories()
        return datablock_item_to_cif(self)


class DatablockCollection(CollectionBase):
    """Handles top-level category collections (e.g. SampleModels,
    Experiments).

    Each item is a DatablockItem.
    """

    def __str__(self) -> str:
        """Human-readable representation of this component."""
        name = self._log_name
        size = len(self)
        return f'<{name} collection ({size} items)>'

    @property
    def unique_name(self):
        return None

    @property
    def parameters(self):
        """All parameters from all datablocks in this collection."""
        params = []
        for db in self._items:
            params.extend(db.parameters)
        return params

    # was in class AbstractDatablock(ABC):
    @property
    def fittable_parameters(self) -> list:
        return [p for p in self.parameters if isinstance(p, Parameter) and not p.constrained]

    # was in class AbstractDatablock(ABC):
    @property
    def free_parameters(self) -> list:
        return [p for p in self.fittable_parameters if p.free]

    @property
    def as_cif(self) -> str:
        """Return CIF representation of this object."""
        from easydiffraction.io.cif.serialize import datablock_collection_to_cif

        return datablock_collection_to_cif(self)

    @typechecked
    def _add(self, item) -> None:
        """Add an item to the collection."""
        self[item._identity.datablock_entry_name] = item
