# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Plotting facade for measured and calculated patterns.

Uses the common :class:`RendererBase` so plotters and tablers share a
consistent configuration surface and engine handling.
"""

from enum import Enum

import numpy as np
import pandas as pd

from easydiffraction.display.base import RendererBase
from easydiffraction.display.base import RendererFactoryBase
from easydiffraction.display.plotters.ascii import AsciiPlotter
from easydiffraction.display.plotters.base import DEFAULT_AXES_LABELS
from easydiffraction.display.plotters.base import DEFAULT_HEIGHT
from easydiffraction.display.plotters.base import DEFAULT_MAX
from easydiffraction.display.plotters.base import DEFAULT_MIN
from easydiffraction.display.plotters.plotly import PlotlyPlotter
from easydiffraction.display.tables import TableRenderer
from easydiffraction.utils.environment import in_jupyter
from easydiffraction.utils.logging import console
from easydiffraction.utils.logging import log


class PlotterEngineEnum(str, Enum):
    ASCII = 'asciichartpy'
    PLOTLY = 'plotly'

    @classmethod
    def default(cls) -> 'PlotterEngineEnum':
        """Select default engine based on environment."""
        if in_jupyter():
            log.debug('Setting default plotting engine to Plotly for Jupyter')
            return cls.PLOTLY
        log.debug('Setting default plotting engine to Asciichartpy for console')
        return cls.ASCII

    def description(self) -> str:
        """Human-readable description for UI listings."""
        if self is PlotterEngineEnum.ASCII:
            return 'Console ASCII line charts'
        elif self is PlotterEngineEnum.PLOTLY:
            return 'Interactive browser-based graphing library'
        return ''


class Plotter(RendererBase):
    """User-facing plotting facade backed by concrete plotters."""

    def __init__(self):
        super().__init__()
        # X-axis limits
        self._x_min = DEFAULT_MIN
        self._x_max = DEFAULT_MAX
        # Chart height
        self.height = DEFAULT_HEIGHT

    @classmethod
    def _factory(cls) -> type[RendererFactoryBase]:  # type: ignore[override]
        return PlotterFactory

    @classmethod
    def _default_engine(cls) -> str:
        return PlotterEngineEnum.default().value

    def show_config(self):
        """Display the current plotting configuration."""
        headers = [
            ('Parameter', 'left'),
            ('Value', 'left'),
        ]
        rows = [
            ['Plotting engine', self.engine],
            ['x-axis limits', f'[{self.x_min}, {self.x_max}]'],
            ['Chart height', self.height],
        ]
        df = pd.DataFrame(rows, columns=pd.MultiIndex.from_tuples(headers))
        console.paragraph('Current plotter configuration')
        TableRenderer.get().render(df)

    @property
    def x_min(self):
        """Minimum x-axis limit."""
        return self._x_min

    @x_min.setter
    def x_min(self, value):
        """Set the minimum x-axis limit.

        Args:
            value: Minimum limit or ``None`` to reset to default.
        """
        if value is not None:
            self._x_min = value
        else:
            self._x_min = DEFAULT_MIN

    @property
    def x_max(self):
        """Maximum x-axis limit."""
        return self._x_max

    @x_max.setter
    def x_max(self, value):
        """Set the maximum x-axis limit.

        Args:
            value: Maximum limit or ``None`` to reset to default.
        """
        if value is not None:
            self._x_max = value
        else:
            self._x_max = DEFAULT_MAX

    @property
    def height(self):
        """Plot height (rows for ASCII, pixels for Plotly)."""
        return self._height

    @height.setter
    def height(self, value):
        """Set plot height.

        Args:
            value: Height value or ``None`` to reset to default.
        """
        if value is not None:
            self._height = value
        else:
            self._height = DEFAULT_HEIGHT

    def plot_meas(
        self,
        pattern,
        expt_name,
        expt_type,
        x_min=None,
        x_max=None,
        d_spacing=False,
    ):
        """Plot measured pattern using the current engine.

        Args:
            pattern: Object with ``x`` and ``meas`` arrays (and
                ``d`` when ``d_spacing`` is true).
            expt_name: Experiment name for the title.
            expt_type: Experiment type with scattering/beam enums.
            x_min: Optional minimum x-axis limit.
            x_max: Optional maximum x-axis limit.
            d_spacing: If ``True``, plot against d-spacing values.
        """
        if pattern.x is None:
            log.error(f'No data available for experiment {expt_name}')
            return
        if pattern.meas is None:
            log.error(f'No measured data available for experiment {expt_name}')
            return

        # Select x-axis data based on d-spacing or original x values
        x_array = pattern.d if d_spacing else pattern.x

        # For asciichartpy, if x_min or x_max is not provided, center
        # around the maximum intensity peak
        if self._engine == 'asciichartpy' and (x_min is None or x_max is None):
            max_intensity_pos = np.argmax(pattern.meas)
            half_range = 50
            start = max(0, max_intensity_pos - half_range)
            end = min(len(x_array) - 1, max_intensity_pos + half_range)
            x_min = x_array[start]
            x_max = x_array[end]

        # Filter x, y_meas, and y_calc based on x_min and x_max
        x = self._filtered_y_array(
            y_array=x_array,
            x_array=x_array,
            x_min=x_min,
            x_max=x_max,
        )
        y_meas = self._filtered_y_array(
            y_array=pattern.meas,
            x_array=x_array,
            x_min=x_min,
            x_max=x_max,
        )

        y_series = [y_meas]
        y_labels = ['meas']

        if d_spacing:
            axes_labels = DEFAULT_AXES_LABELS[
                (
                    expt_type.scattering_type.value,
                    'd-spacing',
                )
            ]
        else:
            axes_labels = DEFAULT_AXES_LABELS[
                (
                    expt_type.scattering_type.value,
                    expt_type.beam_mode.value,
                )
            ]

        # TODO: Before, it was self._plotter.plot. Check what is better.
        self._backend.plot(
            x=x,
            y_series=y_series,
            labels=y_labels,
            axes_labels=axes_labels,
            title=f"Measured data for experiment 🔬 '{expt_name}'",
            height=self.height,
        )

    def plot_calc(
        self,
        pattern,
        expt_name,
        expt_type,
        x_min=None,
        x_max=None,
        d_spacing=False,
    ):
        """Plot calculated pattern using the current engine.

        Args:
            pattern: Object with ``x`` and ``calc`` arrays (and
                ``d`` when ``d_spacing`` is true).
            expt_name: Experiment name for the title.
            expt_type: Experiment type with scattering/beam enums.
            x_min: Optional minimum x-axis limit.
            x_max: Optional maximum x-axis limit.
            d_spacing: If ``True``, plot against d-spacing values.
        """
        if pattern.x is None:
            log.error(f'No data available for experiment {expt_name}')
            return
        if pattern.calc is None:
            log.error(f'No calculated data available for experiment {expt_name}')
            return

        # Select x-axis data based on d-spacing or original x values
        x_array = pattern.d if d_spacing else pattern.x

        # For asciichartpy, if x_min or x_max is not provided, center
        # around the maximum intensity peak
        if self._engine == 'asciichartpy' and (x_min is None or x_max is None):
            max_intensity_pos = np.argmax(pattern.meas)
            half_range = 50
            start = max(0, max_intensity_pos - half_range)
            end = min(len(x_array) - 1, max_intensity_pos + half_range)
            x_min = x_array[start]
            x_max = x_array[end]

        # Filter x, y_meas, and y_calc based on x_min and x_max
        x = self._filtered_y_array(
            y_array=x_array,
            x_array=x_array,
            x_min=x_min,
            x_max=x_max,
        )
        y_calc = self._filtered_y_array(
            y_array=pattern.calc,
            x_array=x_array,
            x_min=x_min,
            x_max=x_max,
        )

        y_series = [y_calc]
        y_labels = ['calc']

        if d_spacing:
            axes_labels = DEFAULT_AXES_LABELS[
                (
                    expt_type.scattering_type.value,
                    'd-spacing',
                )
            ]
        else:
            axes_labels = DEFAULT_AXES_LABELS[
                (
                    expt_type.scattering_type.value,
                    expt_type.beam_mode.value,
                )
            ]

        self._backend.plot(
            x=x,
            y_series=y_series,
            labels=y_labels,
            axes_labels=axes_labels,
            title=f"Calculated data for experiment 🔬 '{expt_name}'",
            height=self.height,
        )

    def plot_meas_vs_calc(
        self,
        pattern,
        expt_name,
        expt_type,
        x_min=None,
        x_max=None,
        show_residual=False,
        d_spacing=False,
    ):
        """Plot measured and calculated series and optional residual.

        Args:
            pattern: Object with ``x``, ``meas`` and ``calc`` arrays
                (and ``d`` when ``d_spacing`` is true).
            expt_name: Experiment name for the title.
            expt_type: Experiment type with scattering/beam enums.
            x_min: Optional minimum x-axis limit.
            x_max: Optional maximum x-axis limit.
            show_residual: If ``True``, add residual series.
            d_spacing: If ``True``, plot against d-spacing values.
        """
        if pattern.x is None:
            log.error(f'No data available for experiment {expt_name}')
            return
        if pattern.meas is None:
            log.error(f'No measured data available for experiment {expt_name}')
            return
        if pattern.calc is None:
            log.error(f'No calculated data available for experiment {expt_name}')
            return

        # Select x-axis data based on d-spacing or original x values
        x_array = pattern.d if d_spacing else pattern.x

        # For asciichartpy, if x_min or x_max is not provided, center
        # around the maximum intensity peak
        if self._engine == 'asciichartpy' and (x_min is None or x_max is None):
            max_intensity_pos = np.argmax(pattern.meas)
            half_range = 50
            start = max(0, max_intensity_pos - half_range)
            end = min(len(x_array) - 1, max_intensity_pos + half_range)
            x_min = x_array[start]
            x_max = x_array[end]

        # Filter x, y_meas, and y_calc based on x_min and x_max
        x = self._filtered_y_array(
            y_array=x_array,
            x_array=x_array,
            x_min=x_min,
            x_max=x_max,
        )
        y_meas = self._filtered_y_array(
            y_array=pattern.meas,
            x_array=x_array,
            x_min=x_min,
            x_max=x_max,
        )
        y_calc = self._filtered_y_array(
            y_array=pattern.calc,
            x_array=x_array,
            x_min=x_min,
            x_max=x_max,
        )

        y_series = [y_meas, y_calc]
        y_labels = ['meas', 'calc']

        if d_spacing:
            axes_labels = DEFAULT_AXES_LABELS[
                (
                    expt_type.scattering_type.value,
                    'd-spacing',
                )
            ]
        else:
            axes_labels = DEFAULT_AXES_LABELS[
                (
                    expt_type.scattering_type.value,
                    expt_type.beam_mode.value,
                )
            ]

        if show_residual:
            y_resid = y_meas - y_calc
            y_series.append(y_resid)
            y_labels.append('resid')

        self._backend.plot(
            x=x,
            y_series=y_series,
            labels=y_labels,
            axes_labels=axes_labels,
            title=f"Measured vs Calculated data for experiment 🔬 '{expt_name}'",
            height=self.height,
        )

    def _filtered_y_array(
        self,
        y_array,
        x_array,
        x_min,
        x_max,
    ):
        """Filter an array by the inclusive x-range limits.

        Args:
            y_array: 1D array-like of y values.
            x_array: 1D array-like of x values (same length as
                ``y_array``).
            x_min: Minimum x limit (or ``None`` to use default).
            x_max: Maximum x limit (or ``None`` to use default).

        Returns:
            Filtered ``y_array`` values where ``x_array`` lies within
            ``[x_min, x_max]``.
        """
        if x_min is None:
            x_min = self.x_min
        if x_max is None:
            x_max = self.x_max

        mask = (x_array >= x_min) & (x_array <= x_max)
        filtered_y_array = y_array[mask]

        return filtered_y_array


class PlotterFactory(RendererFactoryBase):
    """Factory for plotter implementations."""

    @classmethod
    def _registry(cls) -> dict:
        return {
            PlotterEngineEnum.ASCII.value: {
                'description': PlotterEngineEnum.ASCII.description(),
                'class': AsciiPlotter,
            },
            PlotterEngineEnum.PLOTLY.value: {
                'description': PlotterEngineEnum.PLOTLY.description(),
                'class': PlotlyPlotter,
            },
        }
