# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Single crystal experiment types and helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from easydiffraction.experiments.experiment.base import ExperimentBase

if TYPE_CHECKING:
    from easydiffraction.experiments.categories.experiment_type import ExperimentType


class BraggScExperiment(ExperimentBase):
    """Single crystal experiment class with specific attributes."""

    def __init__(
        self,
        *,
        name: str,
        type: ExperimentType,
    ) -> None:
        super().__init__(name=name, type=type)
        self.linked_crystal = None

    def show_meas_chart(self) -> None:
        print('Showing measured data chart is not implemented yet.')
