# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Table rendering engines: console (Rich) and Jupyter (pandas)."""

from __future__ import annotations

from enum import Enum
from typing import Any

import pandas as pd

from easydiffraction.display.base import RendererBase
from easydiffraction.display.base import RendererFactoryBase
from easydiffraction.display.tablers.pandas import PandasTableBackend
from easydiffraction.display.tablers.rich import RichTableBackend
from easydiffraction.utils.environment import in_jupyter
from easydiffraction.utils.logging import console
from easydiffraction.utils.logging import log


class TableEngineEnum(str, Enum):
    RICH = 'rich'
    PANDAS = 'pandas'

    @classmethod
    def default(cls) -> 'TableEngineEnum':
        """Select default engine based on environment.

        Returns Pandas when running in Jupyter, otherwise Rich.
        """
        if in_jupyter():
            log.debug('Setting default table engine to Pandas for Jupyter')
            return cls.PANDAS
        log.debug('Setting default table engine to Rich for console')
        return cls.RICH

    def description(self) -> str:
        if self is TableEngineEnum.RICH:
            return 'Console rendering with Rich'
        elif self is TableEngineEnum.PANDAS:
            return 'Jupyter DataFrame rendering with Pandas'
        return ''


class TableRenderer(RendererBase):
    """Renderer for tabular data with selectable engines (singleton)."""

    @classmethod
    def _factory(cls) -> RendererFactoryBase:
        return TableRendererFactory

    @classmethod
    def _default_engine(cls) -> str:
        """Default engine derived from TableEngineEnum."""
        return TableEngineEnum.default().value

    def show_config(self) -> None:
        """Display minimal configuration for this renderer."""
        headers = [
            ('Parameter', 'left'),
            ('Value', 'left'),
        ]
        rows = [['engine', self._engine]]
        df = pd.DataFrame(rows, columns=pd.MultiIndex.from_tuples(headers))
        console.paragraph('Current tabler configuration')
        TableRenderer.get().render(df)

    def render(self, df, display_handle: Any | None = None) -> Any:
        """Render a DataFrame as a table using the active backend.

        Args:
            df: DataFrame with a two-level column index where the
                second level provides per-column alignment.
            display_handle: Optional environment-specific handle used
                to update an existing output area in-place (e.g., an
                IPython DisplayHandle or a terminal live handle).

        Returns:
            Backend-specific return value (usually ``None``).
        """
        # Work on a copy to avoid mutating the original DataFrame
        df = df.copy()

        # Force starting index from 1
        df.index += 1

        # Extract column alignments
        alignments = df.columns.get_level_values(1)

        # Remove alignments from df (Keep only the first index level)
        df.columns = df.columns.get_level_values(0)

        return self._backend.render(alignments, df, display_handle)


class TableRendererFactory(RendererFactoryBase):
    """Factory for creating tabler instances."""

    @classmethod
    def _registry(cls) -> dict:
        """Build registry, adapting available engines to the
        environment.

        - In Jupyter: expose both 'rich' and 'pandas'.
        - In terminal: expose only 'rich' (pandas is notebook-only).
        """
        base = {
            TableEngineEnum.RICH.value: {
                'description': TableEngineEnum.RICH.description(),
                'class': RichTableBackend,
            }
        }
        if in_jupyter():
            base[TableEngineEnum.PANDAS.value] = {
                'description': TableEngineEnum.PANDAS.description(),
                'class': PandasTableBackend,
            }
        return base
