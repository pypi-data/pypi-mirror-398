# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any
from typing import Optional
from typing import Sequence

import numpy as np

from easydiffraction.core.validation import DataTypes
from easydiffraction.utils.logging import log
from easydiffraction.utils.utils import str_to_ufloat

if TYPE_CHECKING:
    import gemmi

    from easydiffraction.core.category import CategoryCollection
    from easydiffraction.core.category import CategoryItem
    from easydiffraction.core.parameters import GenericDescriptorBase


def format_value(value) -> str:
    """Format a single CIF value, quoting strings with whitespace, and
    format floats with global precision.
    """
    width = 8
    precision = 4

    # Converting

    # Convert ints to floats
    if isinstance(value, int):
        value = float(value)
    # Strings with whitespace are quoted
    elif isinstance(value, str) and (' ' in value or '\t' in value):
        value = f'"{value}"'

    # Formatting

    # Format floats with given precision
    if isinstance(value, float):
        return f'{value:>{width}.{precision}f}'
    # Format strings right-aligned
    elif isinstance(value, str):
        return f'{value:>{width}s}'
    # Everything else: fallback
    else:
        return str(value)


##################
# Serialize to CIF
##################


def param_to_cif(param) -> str:
    """Render a single descriptor/parameter to a CIF line.

    Expects ``param`` to expose ``_cif_handler.names`` and ``value``.
    """
    tags: Sequence[str] = param._cif_handler.names  # type: ignore[attr-defined]
    main_key: str = tags[0]
    return f'{main_key} {format_value(param.value)}'


def category_item_to_cif(item) -> str:
    """Render a CategoryItem-like object to CIF text.

    Expects ``item.parameters`` iterable of params with
    ``_cif_handler.names`` and ``value``.
    """
    lines: list[str] = []
    for p in item.parameters:
        lines.append(param_to_cif(p))
    return '\n'.join(lines)


def category_collection_to_cif(
    collection,
    max_display: Optional[int] = 20,
) -> str:
    """Render a CategoryCollection-like object to CIF text.

    Uses first item to build loop header, then emits rows for each item.
    """
    if not len(collection):
        return ''

    lines: list[str] = []

    # Header
    first_item = list(collection.values())[0]
    lines.append('loop_')
    for p in first_item.parameters:
        tags = p._cif_handler.names  # type: ignore[attr-defined]
        lines.append(tags[0])

    # Rows
    # Limit number of displayed rows if requested
    if len(collection) > max_display:
        half_display = max_display // 2
        for i in range(half_display):
            item = list(collection.values())[i]
            row_vals = [format_value(p.value) for p in item.parameters]
            lines.append(' '.join(row_vals))
        lines.append('...')
        for i in range(-half_display, 0):
            item = list(collection.values())[i]
            row_vals = [format_value(p.value) for p in item.parameters]
            lines.append(' '.join(row_vals))
    # No limit
    else:
        for item in collection.values():
            row_vals = [format_value(p.value) for p in item.parameters]
            lines.append(' '.join(row_vals))

    return '\n'.join(lines)


def datablock_item_to_cif(datablock) -> str:
    """Render a DatablockItem-like object to CIF text.

    Emits a data_ header and then concatenates category CIF sections.
    """
    # Local imports to avoid import-time cycles
    from easydiffraction.core.category import CategoryCollection
    from easydiffraction.core.category import CategoryItem

    header = f'data_{datablock._identity.datablock_entry_name}'
    parts: list[str] = [header]

    # First categories
    for v in vars(datablock).values():
        if isinstance(v, CategoryItem):
            parts.append(v.as_cif)

    # Then collections
    for v in vars(datablock).values():
        if isinstance(v, CategoryCollection):
            parts.append(v.as_cif)

    return '\n\n'.join(parts)


def datablock_collection_to_cif(collection) -> str:
    """Render a collection of datablocks by joining their CIF blocks."""
    return '\n\n'.join([block.as_cif for block in collection.values()])


def project_info_to_cif(info) -> str:
    """Render ProjectInfo to CIF text (id, title, description,
    dates).
    """
    name = f'{info.name}'

    title = f'{info.title}'
    if ' ' in title:
        title = f"'{title}'"

    if len(info.description) > 60:
        description = f'\n;\n{info.description}\n;'
    else:
        description = f'{info.description}'
        if ' ' in description:
            description = f"'{description}'"

    created = f"'{info._created.strftime('%d %b %Y %H:%M:%S')}'"
    last_modified = f"'{info._last_modified.strftime('%d %b %Y %H:%M:%S')}'"

    return (
        f'_project.id               {name}\n'
        f'_project.title            {title}\n'
        f'_project.description      {description}\n'
        f'_project.created          {created}\n'
        f'_project.last_modified    {last_modified}'
    )


def project_to_cif(project) -> str:
    """Render a whole project by concatenating sections when present."""
    parts: list[str] = []
    if hasattr(project, 'info'):
        parts.append(project.info.as_cif)
    if getattr(project, 'sample_models', None):
        parts.append(project.sample_models.as_cif)
    if getattr(project, 'experiments', None):
        parts.append(project.experiments.as_cif)
    if getattr(project, 'analysis', None):
        parts.append(project.analysis.as_cif())
    if getattr(project, 'summary', None):
        parts.append(project.summary.as_cif())
    return '\n\n'.join([p for p in parts if p])


def experiment_to_cif(experiment) -> str:
    """Render an experiment: datablock part plus measured data."""
    return datablock_item_to_cif(experiment)


def analysis_to_cif(analysis) -> str:
    """Render analysis metadata, aliases, and constraints to CIF."""
    cur_min = format_value(analysis.current_minimizer)
    lines: list[str] = []
    lines.append(f'_analysis.calculator_engine  {format_value(analysis.current_calculator)}')
    lines.append(f'_analysis.fitting_engine  {cur_min}')
    lines.append(f'_analysis.fit_mode  {format_value(analysis.fit_mode)}')
    lines.append('')
    lines.append(analysis.aliases.as_cif)
    lines.append('')
    lines.append(analysis.constraints.as_cif)
    return '\n'.join(lines)


def summary_to_cif(_summary) -> str:
    """Render a summary CIF block (placeholder for now)."""
    return 'To be added...'


# TODO: Check the following methods:

######################
# Deserialize from CIF
######################


def param_from_cif(
    self: GenericDescriptorBase,
    block: gemmi.cif.Block,
    idx: int = 0,
) -> None:
    found_values: list[Any] = []

    # Try to find the value(s) from the CIF block iterating over
    # the possible cif names in order of preference.
    for tag in self._cif_handler.names:
        candidates = list(block.find_values(tag))
        if candidates:
            found_values = candidates
            break

    # If no values found, the parameter keeps its default value.
    if not found_values:
        return

    # If found, pick the one at the given index
    raw = found_values[idx]

    # If numeric, parse with uncertainty if present
    if self._value_type == DataTypes.NUMERIC:
        u = str_to_ufloat(raw)
        self.value = u.n
        if not np.isnan(u.s) and hasattr(self, 'uncertainty'):
            self.uncertainty = u.s  # type: ignore[attr-defined]
            self.free = True  # Mark as free if uncertainty is present

    # If string, strip quotes if present
    elif self._value_type == DataTypes.STRING:
        if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in {"'", '"'}:
            self.value = raw[1:-1]
        else:
            self.value = raw

    # Other types are not supported
    else:
        log.debug(f'Unrecognized type: {self._value_type}')


def category_item_from_cif(
    self: CategoryItem,
    block: gemmi.cif.Block,
    idx: int = 0,
) -> None:
    """Populate each parameter from CIF block at given loop index."""
    for param in self.parameters:
        param.from_cif(block, idx=idx)


def category_collection_from_cif(
    self: CategoryCollection,
    block: gemmi.cif.Block,
) -> None:
    # TODO: Find a better way and then remove TODO in the AtomSite
    #  class
    # TODO: Rename to _item_cls?
    if self._item_type is None:
        raise ValueError('Child class is not defined.')

    # Create a temporary instance to access its parameters and
    # parameter CIF names
    category_item = self._item_type()

    # Iterate over category parameters and their possible CIF names
    # trying to find the whole loop it belongs to inside the CIF block
    def _get_loop(block, category_item):
        for param in category_item.parameters:
            for name in param._cif_handler.names:
                loop = block.find_loop(name).get_loop()
                if loop is not None:
                    return loop
        return None

    loop = _get_loop(block, category_item)

    # If no loop found
    if loop is None:
        log.debug(f'No loop found for category {self}.')
        return

    # Get 2D array of loop values (as strings)
    num_rows = loop.length()
    num_cols = loop.width()
    array = np.array(loop.values, dtype=str).reshape(num_rows, num_cols)

    # Pre-create default items in the collection
    self._items = [self._item_type() for _ in range(num_rows)]

    # Set parent for each item to enable identity resolution
    for item in self._items:
        object.__setattr__(item, '_parent', self)

    # Set those items' parameters, which are present in the loop
    for row_idx in range(num_rows):
        current_item = self._items[row_idx]
        for param in current_item.parameters:
            for cif_name in param._cif_handler.names:
                if cif_name in loop.tags:
                    col_idx = loop.tags.index(cif_name)

                    # TODO: The following is duplication of
                    #  param_from_cif
                    raw = array[row_idx][col_idx]

                    # If numeric, parse with uncertainty if present
                    if param._value_type == DataTypes.NUMERIC:
                        u = str_to_ufloat(raw)
                        param.value = u.n
                        if not np.isnan(u.s) and hasattr(param, 'uncertainty'):
                            param.uncertainty = u.s  # type: ignore[attr-defined]
                            param.free = True  # Mark as free if uncertainty is present

                    # If string, strip quotes if present
                    # TODO: Make a helper function for this
                    elif param._value_type == DataTypes.STRING:
                        if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in {"'", '"'}:
                            param.value = raw[1:-1]
                        else:
                            param.value = raw

                    # Other types are not supported
                    else:
                        log.debug(f'Unrecognized type: {param._value_type}')

                    break
