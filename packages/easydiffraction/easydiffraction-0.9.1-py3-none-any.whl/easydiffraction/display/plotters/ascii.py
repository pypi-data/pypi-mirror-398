# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""ASCII plotting backend.

Renders compact line charts in the terminal using
``asciichartpy``. This backend is well suited for quick feedback in
CLI environments and keeps a consistent API with other plotters.
"""

import asciichartpy

from easydiffraction.display.plotters.base import DEFAULT_HEIGHT
from easydiffraction.display.plotters.base import SERIES_CONFIG
from easydiffraction.display.plotters.base import PlotterBase
from easydiffraction.utils.logging import console

DEFAULT_COLORS = {
    'meas': asciichartpy.blue,
    'calc': asciichartpy.red,
    'resid': asciichartpy.green,
}


class AsciiPlotter(PlotterBase):
    """Terminal-based plotter using ASCII art."""

    def _get_legend_item(self, label):
        """Return a colored legend entry for a given series label.

        The legend uses a colored line matching the series color and
        the human-readable name from :data:`SERIES_CONFIG`.

        Args:
            label: Series identifier (e.g., ``'meas'``).

        Returns:
            A formatted legend string with color escapes.
        """
        color_start = DEFAULT_COLORS[label]
        color_end = asciichartpy.reset
        line = '────'
        name = SERIES_CONFIG[label]['name']
        item = f'{color_start}{line}{color_end} {name}'
        return item

    def plot(
        self,
        x,
        y_series,
        labels,
        axes_labels,
        title,
        height=None,
    ):
        """Render a compact ASCII chart in the terminal.

        Args:
            x: 1D array-like of x values (only used for range
                display).
            y_series: Sequence of y arrays to plot.
            labels: Series identifiers corresponding to y_series.
            axes_labels: Ignored; kept for API compatibility.
            title: Figure title printed above the chart.
            height: Number of text rows to allocate for the chart.
        """
        # Intentionally unused; kept for a consistent display API
        del axes_labels
        legend = '\n'.join([self._get_legend_item(label) for label in labels])

        if height is None:
            height = DEFAULT_HEIGHT
        colors = [DEFAULT_COLORS[label] for label in labels]
        config = {'height': height, 'colors': colors}
        y_series = [y.tolist() for y in y_series]

        chart = asciichartpy.plot(y_series, config)

        console.paragraph(f'{title}')  # TODO: f''?
        console.print(
            f'Displaying data for selected x-range from {x[0]} to {x[-1]} ({len(x)} points)'
        )
        console.print(f'Legend:\n{legend}')

        padded = '\n'.join(' ' + line for line in chart.splitlines())

        print(padded)
