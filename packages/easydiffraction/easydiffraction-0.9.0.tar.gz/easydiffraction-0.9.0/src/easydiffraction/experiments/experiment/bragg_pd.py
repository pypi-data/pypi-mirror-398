# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from easydiffraction.experiments.categories.background.enums import BackgroundTypeEnum
from easydiffraction.experiments.categories.background.factory import BackgroundFactory
from easydiffraction.experiments.experiment.base import PdExperimentBase
from easydiffraction.experiments.experiment.instrument_mixin import InstrumentMixin
from easydiffraction.utils.logging import console
from easydiffraction.utils.logging import log
from easydiffraction.utils.utils import render_table

if TYPE_CHECKING:
    from easydiffraction.experiments.categories.experiment_type import ExperimentType


class BraggPdExperiment(InstrumentMixin, PdExperimentBase):
    """Powder diffraction experiment.

    Wraps background model, peak profile and linked phases for Bragg PD.
    """

    def __init__(
        self,
        *,
        name: str,
        type: ExperimentType,
    ) -> None:
        super().__init__(name=name, type=type)

        self._background_type: BackgroundTypeEnum = BackgroundTypeEnum.default()
        self._background = BackgroundFactory.create(background_type=self.background_type)

    @property
    def background(self):
        return self._background

    @background.setter
    def background(self, value):
        self._background = value

    # -------------
    # Measured data
    # -------------

    def _load_ascii_data_to_experiment(self, data_path: str) -> None:
        """Load (x, y, sy) data from an ASCII file into the data
        category.

        The file format is space/column separated with 2 or 3 columns:
        ``x y [sy]``. If ``sy`` is missing, it is approximated as
        ``sqrt(y)`` with small values clamped to ``1.0``.
        """
        try:
            data = np.loadtxt(data_path)
        except Exception as e:
            raise IOError(f'Failed to read data from {data_path}: {e}') from e

        if data.shape[1] < 2:
            raise ValueError('Data file must have at least two columns: x and y.')

        if data.shape[1] < 3:
            print('Warning: No uncertainty (sy) column provided. Defaulting to sqrt(y).')

        # Extract x, y data
        x: np.ndarray = data[:, 0]
        y: np.ndarray = data[:, 1]

        # Round x to 4 decimal places
        x = np.round(x, 4)

        # Determine sy from column 3 if available, otherwise use sqrt(y)
        sy: np.ndarray = data[:, 2] if data.shape[1] > 2 else np.sqrt(y)

        # Replace values smaller than 0.0001 with 1.0
        sy = np.where(sy < 0.0001, 1.0, sy)

        # Set the experiment data
        self.data._set_x(x)
        self.data._set_meas(y)
        self.data._set_meas_su(sy)

        console.paragraph('Data loaded successfully')
        console.print(f"Experiment 🔬 '{self.name}'. Number of data points: {len(x)}")

    @property
    def background_type(self):
        """Current background type enum value."""
        return self._background_type

    @background_type.setter
    def background_type(self, new_type):
        """Set and apply a new background type.

        Falls back to printing supported types if the new value is not
        supported.
        """
        if new_type not in BackgroundFactory._supported_map():
            supported_types = list(BackgroundFactory._supported_map().keys())
            log.warning(
                f"Unknown background type '{new_type}'. "
                f'Supported background types: {[bt.value for bt in supported_types]}. '
                f"For more information, use 'show_supported_background_types()'"
            )
            return
        self.background = BackgroundFactory.create(new_type)
        self._background_type = new_type
        console.paragraph(f"Background type for experiment '{self.name}' changed to")
        console.print(new_type)

    def show_supported_background_types(self):
        """Print a table of supported background types."""
        columns_headers = ['Background type', 'Description']
        columns_alignment = ['left', 'left']
        columns_data = []
        for bt in BackgroundFactory._supported_map():
            columns_data.append([bt.value, bt.description()])

        console.paragraph('Supported background types')
        render_table(
            columns_headers=columns_headers,
            columns_alignment=columns_alignment,
            columns_data=columns_data,
        )

    def show_current_background_type(self):
        """Print the currently used background type."""
        console.paragraph('Current background type')
        console.print(self.background_type)
