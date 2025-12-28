# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from abc import ABC
from abc import abstractmethod

import numpy as np

from easydiffraction.experiments.experiment.base import ExperimentBase
from easydiffraction.sample_models.sample_model.base import SampleModelBase
from easydiffraction.sample_models.sample_models import SampleModels


class CalculatorBase(ABC):
    """Base API for diffraction calculation engines."""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def engine_imported(self) -> bool:
        pass

    @abstractmethod
    def calculate_structure_factors(
        self,
        sample_model: SampleModelBase,
        experiment: ExperimentBase,
    ) -> None:
        """Calculate structure factors for a single sample model and
        experiment.
        """
        pass

    @abstractmethod
    def calculate_pattern(
        self,
        sample_model: SampleModels,  # TODO: SampleModelBase?
        experiment: ExperimentBase,
        called_by_minimizer: bool,
    ) -> np.ndarray:
        """Calculate the diffraction pattern for a single sample model
        and experiment.

        Args:
            sample_model: The sample model object.
            experiment: The experiment object.
            called_by_minimizer: Whether the calculation is called by a
                minimizer.

        Returns:
            The calculated diffraction pattern as a NumPy array.
        """
        pass
