# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Rich-based table renderer for terminals and notebooks."""

from __future__ import annotations

import io
from typing import Any

from rich.box import Box
from rich.console import Console
from rich.table import Table

try:
    from IPython.display import HTML
    from IPython.display import display
except Exception:
    HTML = None
    display = None

from easydiffraction.display.tablers.base import TableBackendBase
from easydiffraction.utils.environment import can_use_ipython_display
from easydiffraction.utils.logging import ConsoleManager
from easydiffraction.utils.logging import log

"""Custom compact box style used for consistent borders."""
CUSTOM_BOX = """\
┌──┐
│  │
├──┤
│  │
├──┤
├──┤
│  │
└──┘
"""
RICH_TABLE_BOX: Box = Box(CUSTOM_BOX, ascii=False)


class RichTableBackend(TableBackendBase):
    """Render tables to terminal or Jupyter using the Rich library."""

    def _to_html(self, table: Table) -> str:
        """Render a Rich table to HTML using an off-screen console.

        A fresh ``Console(record=True, file=StringIO())`` avoids
        private attribute access and guarantees no visible output
        in notebooks.

        Args:
            table: Rich :class:`~rich.table.Table` to export.

        Returns:
            HTML string with inline styles for notebook display.
        """
        tmp = Console(force_jupyter=False, record=True, file=io.StringIO())
        tmp.print(table)
        html = tmp.export_html(inline_styles=True)
        # Remove margins inside pre blocks and adjust font size
        html = html.replace(
            '<pre ',
            "<pre style='margin:0; font-size: 0.9em !important; ' ",
        )
        return html

    def _build_table(self, df, alignments, color: str) -> Table:
        """Construct a Rich Table with formatted data and alignment.

        Args:
            df: DataFrame-like object providing rows to render.
            alignments: Iterable of text alignment values for columns.
            color: Rich color name used for borders/index style.

        Returns:
            A :class:`~rich.table.Table` configured for display.
        """
        table = Table(
            title=None,
            box=RICH_TABLE_BOX,
            show_header=True,
            header_style='bold',
            border_style=color,
        )

        # Index column
        table.add_column(justify='right', style=color)

        # Data columns
        for col, align in zip(df, alignments, strict=False):
            table.add_column(str(col), justify=align, no_wrap=False)

        # Rows
        for idx, row_values in df.iterrows():
            formatted_row = [self._format_value(v) for v in row_values]
            table.add_row(str(idx), *formatted_row)

        return table

    def _update_display(self, table: Table, display_handle) -> None:
        """Single, consistent update path for Jupyter and terminal.

        - With a handle that has ``update()``:
          * If it's an IPython DisplayHandle, export to HTML and
            update.
          * Otherwise, treat it as a terminal/live-like handle and
            update with the Rich renderable.
        - Without a handle, print once to the shared console.

        Args:
            table: Rich :class:`~rich.table.Table` to display.
            display_handle: Optional environment-specific handle for
                in-place updates (IPython or terminal live).
        """
        # Handle with update() method
        if display_handle is not None and hasattr(display_handle, 'update'):
            # IPython DisplayHandle path
            if can_use_ipython_display(display_handle) and HTML is not None:
                try:
                    html = self._to_html(table)
                    display_handle.update(HTML(html))
                    return
                except Exception as err:
                    log.debug(f'Rich to HTML DisplayHandle update failed: {err!r}')

            # Assume terminal/live-like handle
            else:
                try:
                    display_handle.update(table)
                    return
                except Exception as err:
                    log.debug(f'Rich live handle update failed: {err!r}')

        # Normal print to console
        console = ConsoleManager.get()
        console.print(table)

    def render(
        self,
        alignments,
        df,
        display_handle=None,
    ) -> Any:
        """Render a styled table using Rich.

        Args:
            alignments: Iterable of text-align values for columns.
            df: Index-aware DataFrame to render.
            display_handle: Optional environment handle for in-place
                updates.
        """
        color = self._rich_border_color
        table = self._build_table(df, alignments, color)
        self._update_display(table, display_handle)
