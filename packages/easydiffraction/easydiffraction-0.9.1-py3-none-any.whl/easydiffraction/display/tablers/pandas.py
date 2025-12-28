# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Pandas-based table renderer for notebooks using DataFrame Styler."""

from __future__ import annotations

from typing import Any

try:
    from IPython.display import HTML
    from IPython.display import display
except Exception:
    HTML = None
    display = None

from easydiffraction.display.tablers.base import TableBackendBase
from easydiffraction.utils.environment import can_use_ipython_display
from easydiffraction.utils.logging import log


class PandasTableBackend(TableBackendBase):
    """Render tables using the pandas Styler in Jupyter environments."""

    def _build_base_styles(self, color: str) -> list[dict]:
        """Return base CSS table styles for a given border color.

        Args:
            color: CSS color value (e.g., ``#RRGGBB``) to use for
                borders and header accents.

        Returns:
            A list of ``Styler.set_table_styles`` dictionaries.
        """
        return [
            # Margins and outer border on the entire table
            {
                'selector': ' ',
                'props': [
                    ('border', f'1px solid {color}'),
                    ('border-collapse', 'collapse'),
                    ('margin-top', '0.5em'),
                    ('margin-left', '0.5em'),
                ],
            },
            # Horizontal border under header row
            {
                'selector': 'thead',
                'props': [
                    ('border-bottom', f'1px solid {color}'),
                ],
            },
            # Cell border, padding and line height
            {
                'selector': 'th, td',
                'props': [
                    ('border', 'none'),
                    ('padding-top', '0.25em'),
                    ('padding-bottom', '0.25em'),
                    ('line-height', '1.15em'),
                ],
            },
            # Style for index column
            {
                'selector': 'th.row_heading',
                'props': [
                    ('color', color),
                    ('font-weight', 'normal'),
                ],
            },
            # Remove zebra-row background
            {
                'selector': 'tbody tr:nth-child(odd), tbody tr:nth-child(even)',
                'props': [
                    ('background-color', 'transparent'),
                ],
            },
        ]

    def _build_header_alignment_styles(self, df, alignments) -> list[dict]:
        """Generate header cell alignment styles per column.

        Args:
            df: DataFrame whose columns are being rendered.
            alignments: Iterable of text alignment values (e.g.,
                ``'left'``, ``'center'``) matching ``df`` columns.

        Returns:
            A list of CSS rules for header cell alignment.
        """
        return [
            {
                'selector': f'th.col{df.columns.get_loc(column)}',
                'props': [('text-align', align)],
            }
            for column, align in zip(df.columns, alignments, strict=False)
        ]

    def _apply_styling(self, df, alignments, color: str):
        """Build a configured Styler with alignments and base styles.

        Args:
            df: DataFrame to style.
            alignments: Iterable of text alignment values for columns.
            color: CSS color value used for borders/header.

        Returns:
            A configured pandas Styler ready for display.
        """
        table_styles = self._build_base_styles(color)
        header_alignment_styles = self._build_header_alignment_styles(df, alignments)

        styler = df.style.format(precision=self.FLOAT_PRECISION)
        styler = styler.set_table_attributes('class="dataframe"')  # For mkdocs-jupyter
        styler = styler.set_table_styles(table_styles + header_alignment_styles)

        for column, align in zip(df.columns, alignments, strict=False):
            styler = styler.set_properties(
                subset=[column],
                **{'text-align': align},
            )
        return styler

    def _update_display(self, styler, display_handle) -> None:
        """Single, consistent update path for Jupyter.

        If a handle with ``update()`` is provided and it's a
        DisplayHandle, update the output area in-place using HTML.
        Otherwise, display once via IPython ``display()``.

        Args:
            styler: Configured DataFrame Styler to be rendered.
            display_handle: Optional IPython DisplayHandle used for
                in-place updates.
        """
        # Handle with update() method
        if display_handle is not None and hasattr(display_handle, 'update'):
            # IPython DisplayHandle path
            if can_use_ipython_display(display_handle) and HTML is not None:
                try:
                    html = styler.to_html()
                    display_handle.update(HTML(html))
                    return
                except Exception as err:
                    log.debug(f'Pandas DisplayHandle update failed: {err!r}')

            # This should not happen in Pandas backend
            else:
                pass

        # Normal display
        display(styler)

    def render(
        self,
        alignments,
        df,
        display_handle: Any | None = None,
    ) -> Any:
        """Render a styled DataFrame.

        Args:
            alignments: Iterable of column justifications (e.g. 'left').
            df: DataFrame whose index is displayed as the first column.
            display_handle: Optional IPython DisplayHandle to update an
                existing output area in place when running in Jupyter.
        """
        color = self._pandas_border_color
        styler = self._apply_styling(df, alignments, color)
        self._update_display(styler, display_handle)
