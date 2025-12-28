# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING
from typing import Any
from typing import List

from easydiffraction.core.datablock import DatablockItem
from easydiffraction.experiments.categories.data.factory import DataFactory
from easydiffraction.experiments.categories.excluded_regions import ExcludedRegions
from easydiffraction.experiments.categories.linked_phases import LinkedPhases
from easydiffraction.experiments.categories.peak.factory import PeakFactory
from easydiffraction.experiments.categories.peak.factory import PeakProfileTypeEnum
from easydiffraction.io.cif.serialize import experiment_to_cif
from easydiffraction.utils.logging import console
from easydiffraction.utils.logging import log
from easydiffraction.utils.utils import render_cif
from easydiffraction.utils.utils import render_table

if TYPE_CHECKING:
    from easydiffraction.experiments.categories.experiment_type import ExperimentType
    from easydiffraction.sample_models.sample_models import SampleModels


class ExperimentBase(DatablockItem):
    """Base class for all experiments with only core attributes.

    Wraps experiment type and instrument.
    """

    def __init__(
        self,
        *,
        name: str,
        type: ExperimentType,
    ):
        super().__init__()
        self._name = name
        self._type = type
        # TODO: Should return default calculator based on experiment
        #  type
        from easydiffraction.analysis.calculators.factory import CalculatorFactory

        self._calculator = CalculatorFactory.create_calculator('cryspy')
        self._identity.datablock_entry_name = lambda: self.name

    @property
    def name(self) -> str:
        """Human-readable name of the experiment."""
        return self._name

    @name.setter
    def name(self, new: str) -> None:
        """Rename the experiment.

        Args:
            new: New name for this experiment.
        """
        self._name = new

    @property
    def type(self):  # TODO: Consider another name
        """Experiment type descriptor (sample form, probe, beam
        mode).
        """
        return self._type

    @property
    def calculator(self):
        """Calculator engine used for pattern calculations."""
        return self._calculator

    @property
    def as_cif(self) -> str:
        """Serialize this experiment to a CIF fragment."""
        return experiment_to_cif(self)

    def show_as_cif(self) -> None:
        """Pretty-print the experiment as CIF text."""
        experiment_cif = super().as_cif
        paragraph_title: str = f"Experiment 🔬 '{self.name}' as cif"
        console.paragraph(paragraph_title)
        render_cif(experiment_cif)

    @abstractmethod
    def _load_ascii_data_to_experiment(self, data_path: str) -> None:
        """Load ASCII data from file into the experiment data category.

        Args:
            data_path: Path to the ASCII file to load.
        """
        raise NotImplementedError()


class PdExperimentBase(ExperimentBase):
    """Base class for all powder experiments."""

    def __init__(
        self,
        *,
        name: str,
        type: ExperimentType,
    ) -> None:
        super().__init__(name=name, type=type)

        self._linked_phases: LinkedPhases = LinkedPhases()
        self._excluded_regions: ExcludedRegions = ExcludedRegions()

        self._peak_profile_type: PeakProfileTypeEnum = PeakProfileTypeEnum.default(
            self.type.scattering_type.value,
            self.type.beam_mode.value,
        )
        self._peak = PeakFactory.create(
            scattering_type=self.type.scattering_type.value,
            beam_mode=self.type.beam_mode.value,
            profile_type=self._peak_profile_type,
        )

        self._data = DataFactory.create(
            sample_form=self.type.sample_form.value,
            beam_mode=self.type.beam_mode.value,
            scattering_type=self.type.scattering_type.value,
        )

    def _get_valid_linked_phases(
        self,
        sample_models: SampleModels,
    ) -> List[Any]:
        """Get valid linked phases for this experiment.

        Args:
            sample_models: Collection of sample models.

        Returns:
            A list of valid linked phases.
        """
        if not self.linked_phases:
            print('Warning: No linked phases defined. Returning empty pattern.')
            return []

        valid_linked_phases = []
        for linked_phase in self.linked_phases:
            if linked_phase._identity.category_entry_name not in sample_models.names:
                print(
                    f"Warning: Linked phase '{linked_phase.id.value}' not "
                    f'found in Sample Models {sample_models.names}. Skipping it.'
                )
                continue
            valid_linked_phases.append(linked_phase)

        if not valid_linked_phases:
            print(
                'Warning: None of the linked phases found in Sample '
                'Models. Returning empty pattern.'
            )

        return valid_linked_phases

    @abstractmethod
    def _load_ascii_data_to_experiment(self, data_path: str) -> None:
        """Load powder diffraction data from an ASCII file.

        Args:
            data_path: Path to data file with columns compatible with
                the beam mode (e.g. 2θ/I/σ for CWL, TOF/I/σ for TOF).
        """
        pass

    @property
    def linked_phases(self):
        """Collection of phases linked to this experiment."""
        return self._linked_phases

    @property
    def excluded_regions(self):
        """Collection of excluded regions for the x-grid."""
        return self._excluded_regions

    @property
    def peak(self) -> str:
        """Peak category object with profile parameters and mixins."""
        return self._peak

    @peak.setter
    def peak(self, value):
        """Replace the peak model used for this powder experiment.

        Args:
            value: New peak object created by the `PeakFactory`.
        """
        self._peak = value

    @property
    def data(self):
        return self._data

    @property
    def peak_profile_type(self):
        """Currently selected peak profile type enum."""
        return self._peak_profile_type

    @peak_profile_type.setter
    def peak_profile_type(self, new_type: str | PeakProfileTypeEnum):
        """Change the active peak profile type, if supported.

        Args:
            new_type: New profile type as enum or its string value.
        """
        if isinstance(new_type, str):
            try:
                new_type = PeakProfileTypeEnum(new_type)
            except ValueError:
                log.warning(f"Unknown peak profile type '{new_type}'")
                return

        supported_types = list(
            PeakFactory._supported[self.type.scattering_type.value][
                self.type.beam_mode.value
            ].keys()
        )

        if new_type not in supported_types:
            log.warning(
                f"Unsupported peak profile '{new_type.value}', "
                f'Supported peak profiles: {supported_types}',
                "For more information, use 'show_supported_peak_profile_types()'",
            )
            return

        self._peak = PeakFactory.create(
            scattering_type=self.type.scattering_type.value,
            beam_mode=self.type.beam_mode.value,
            profile_type=new_type,
        )
        self._peak_profile_type = new_type
        console.paragraph(f"Peak profile type for experiment '{self.name}' changed to")
        console.print(new_type.value)

    def show_supported_peak_profile_types(self):
        """Print available peak profile types for this experiment."""
        columns_headers = ['Peak profile type', 'Description']
        columns_alignment = ['left', 'left']
        columns_data = []

        scattering_type = self.type.scattering_type.value
        beam_mode = self.type.beam_mode.value

        for profile_type in PeakFactory._supported[scattering_type][beam_mode]:
            columns_data.append([profile_type.value, profile_type.description()])

        console.paragraph('Supported peak profile types')
        render_table(
            columns_headers=columns_headers,
            columns_alignment=columns_alignment,
            columns_data=columns_data,
        )

    def show_current_peak_profile_type(self):
        """Print the currently selected peak profile type."""
        console.paragraph('Current peak profile type')
        console.print(self.peak_profile_type)
