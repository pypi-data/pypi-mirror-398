# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Low-level backends for rendering tables.

This module defines the abstract base for tabular renderers and small
helpers for consistent styling across terminal and notebook outputs.
"""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import Any

from IPython import get_ipython
from jupyter_dark_detect import is_dark
from rich.color import Color


class TableBackendBase(ABC):
    """Abstract base class for concrete table backends.

    Subclasses implement the ``render`` method which receives an
    index-aware pandas DataFrame and the alignment for each column
    header.
    """

    FLOAT_PRECISION = 5
    RICH_BORDER_DARK_THEME = 'grey35'
    RICH_BORDER_LIGHT_THEME = 'grey85'

    def __init__(self) -> None:
        super().__init__()
        self._float_fmt = f'{{:.{self.FLOAT_PRECISION}f}}'.format

    def _format_value(self, value: Any) -> Any:
        """Format floats with fixed precision and others as strings.

        Args:
            value: Cell value to format.

        Returns:
            A string representation with fixed precision for floats or
            ``str(value)`` for other types.
        """
        return self._float_fmt(value) if isinstance(value, float) else str(value)

    def _is_dark_theme(self) -> bool:
        """Return True when a dark theme is detected in Jupyter.

        If not running inside Jupyter, return a sane default (True).
        """
        default = True

        in_jupyter = (
            get_ipython() is not None and get_ipython().__class__.__name__ == 'ZMQInteractiveShell'
        )

        if not in_jupyter:
            return default

        return is_dark()

    def _rich_to_hex(self, color):
        """Convert a Rich color name to a CSS-style hex string.

        Args:
            color: Rich color name or specification parsable by
                :mod:`rich`.

        Returns:
            Hex color string in the form ``#RRGGBB``.
        """
        c = Color.parse(color)
        rgb = c.get_truecolor()
        hex_value = '#{:02x}{:02x}{:02x}'.format(*rgb)
        return hex_value

    @property
    def _rich_border_color(self) -> str:
        return (
            self.RICH_BORDER_DARK_THEME if self._is_dark_theme() else self.RICH_BORDER_LIGHT_THEME
        )

    @property
    def _pandas_border_color(self) -> str:
        return self._rich_to_hex(self._rich_border_color)

    @abstractmethod
    def render(
        self,
        alignments,
        df,
        display_handle: Any | None = None,
    ) -> Any:
        """Render the provided DataFrame with backend-specific styling.

        Args:
            alignments: Iterable of column justifications (e.g.,
                ``'left'`` or ``'center'``) corresponding to the data
                columns.
            df: Index-aware DataFrame with data to render.
            display_handle: Optional environment-specific handle to
                enable in-place updates.

        Returns:
            Backend-defined return value (commonly ``None``).
        """
        pass
