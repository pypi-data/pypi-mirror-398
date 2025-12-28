# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Abstract base and shared constants for plotting backends."""

from abc import ABC
from abc import abstractmethod

import numpy as np

from easydiffraction.experiments.experiment.enums import BeamModeEnum
from easydiffraction.experiments.experiment.enums import ScatteringTypeEnum

DEFAULT_HEIGHT = 9
DEFAULT_MIN = -np.inf
DEFAULT_MAX = np.inf

DEFAULT_AXES_LABELS = {
    (ScatteringTypeEnum.BRAGG, BeamModeEnum.CONSTANT_WAVELENGTH): [
        '2θ (degree)',
        'Intensity (arb. units)',
    ],
    (ScatteringTypeEnum.BRAGG, BeamModeEnum.TIME_OF_FLIGHT): [
        'TOF (µs)',
        'Intensity (arb. units)',
    ],
    (ScatteringTypeEnum.BRAGG, 'd-spacing'): [
        'd (Å)',
        'Intensity (arb. units)',
    ],
    (ScatteringTypeEnum.TOTAL, BeamModeEnum.CONSTANT_WAVELENGTH): [
        'r (Å)',
        'G(r) (Å)',
    ],
    (ScatteringTypeEnum.TOTAL, BeamModeEnum.TIME_OF_FLIGHT): [
        'r (Å)',
        'G(r) (Å)',
    ],
}

SERIES_CONFIG = dict(
    calc=dict(
        mode='lines',
        name='Total calculated (Icalc)',
    ),
    meas=dict(
        mode='lines+markers',
        name='Measured (Imeas)',
    ),
    resid=dict(
        mode='lines',
        name='Residual (Imeas - Icalc)',
    ),
)


class PlotterBase(ABC):
    """Abstract base for plotting backends.

    Implementations accept x values, multiple y-series, optional labels
    and render a plot to the chosen medium.
    """

    @abstractmethod
    def plot(
        self,
        x,
        y_series,
        labels,
        axes_labels,
        title,
        height,
    ):
        """Render a plot.

        Args:
            x: 1D array of x-axis values.
            y_series: Sequence of y arrays to plot.
            labels: Identifiers corresponding to y_series.
            axes_labels: Pair of strings for the x and y titles.
            title: Figure title.
            height: Backend-specific height (text rows or pixels).
        """
        pass
