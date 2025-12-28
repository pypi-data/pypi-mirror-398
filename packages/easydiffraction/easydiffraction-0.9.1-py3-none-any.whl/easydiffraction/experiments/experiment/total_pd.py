# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from easydiffraction.experiments.experiment.base import PdExperimentBase
from easydiffraction.utils.logging import console

if TYPE_CHECKING:
    from easydiffraction.experiments.categories.experiment_type import ExperimentType


class TotalPdExperiment(PdExperimentBase):
    """PDF experiment class with specific attributes."""

    def __init__(
        self,
        name: str,
        type: ExperimentType,
    ):
        super().__init__(name=name, type=type)

    def _load_ascii_data_to_experiment(self, data_path):
        """Loads x, y, sy values from an ASCII data file into the
        experiment.

        The file must be structured as:
            x  y  sy
        """
        try:
            from diffpy.utils.parsers.loaddata import loadData
        except ImportError:
            raise ImportError('diffpy module not found.') from None
        try:
            data = loadData(data_path)
        except Exception as e:
            raise IOError(f'Failed to read data from {data_path}: {e}') from e

        if data.shape[1] < 2:
            raise ValueError('Data file must have at least two columns: x and y.')

        default_sy = 0.03
        if data.shape[1] < 3:
            print(f'Warning: No uncertainty (sy) column provided. Defaulting to {default_sy}.')

        x = data[:, 0]
        y = data[:, 1]
        sy = data[:, 2] if data.shape[1] > 2 else np.full_like(y, fill_value=default_sy)

        self.data._set_x(x)
        self.data._set_meas(y)
        self.data._set_meas_su(sy)

        console.paragraph('Data loaded successfully')
        console.print(f"Experiment 🔬 '{self.name}'. Number of data points: {len(x)}")
