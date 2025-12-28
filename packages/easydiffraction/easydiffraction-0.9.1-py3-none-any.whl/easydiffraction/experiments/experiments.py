# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from typeguard import typechecked

from easydiffraction.core.datablock import DatablockCollection
from easydiffraction.experiments.experiment.base import ExperimentBase
from easydiffraction.experiments.experiment.factory import ExperimentFactory
from easydiffraction.utils.logging import console


class Experiments(DatablockCollection):
    """Collection of Experiment data blocks.

    Provides convenience constructors for common creation patterns and
    helper methods for simple presentation of collection contents.
    """

    def __init__(self) -> None:
        super().__init__(item_type=ExperimentBase)

    # --------------------
    # Add / Remove methods
    # --------------------

    # TODO: Move to DatablockCollection?
    # TODO: Disallow args and only allow kwargs?
    def add(self, **kwargs):
        experiment = kwargs.pop('experiment', None)

        if experiment is None:
            experiment = ExperimentFactory.create(**kwargs)

        self._add(experiment)

    # @typechecked
    # def add_from_cif_path(self, cif_path: str):
    #    """Add an experiment from a CIF file path.
    #
    #    Args:
    #        cif_path: Path to a CIF document.
    #    """
    #    experiment = ExperimentFactory.create(cif_path=cif_path)
    #    self.add(experiment)

    # @typechecked
    # def add_from_cif_str(self, cif_str: str):
    #    """Add an experiment from a CIF string.
    #
    #    Args:
    #        cif_str: Full CIF document as a string.
    #    """
    #    experiment = ExperimentFactory.create(cif_str=cif_str)
    #    self.add(experiment)

    # @typechecked
    # def add_from_data_path(
    #    self,
    #    name: str,
    #    data_path: str,
    #    sample_form: str = SampleFormEnum.default().value,
    #    beam_mode: str = BeamModeEnum.default().value,
    #    radiation_probe: str = RadiationProbeEnum.default().value,
    #    scattering_type: str = ScatteringTypeEnum.default().value,
    # ):
    #    """Add an experiment from a data file path.
    #
    #    Args:
    #        name: Experiment identifier.
    #        data_path: Path to the measured data file.
    #        sample_form: Sample form (powder or single crystal).
    #        beam_mode: Beam mode (constant wavelength or TOF).
    #        radiation_probe: Radiation probe (neutron or xray).
    #        scattering_type: Scattering type (bragg or total).
    #    """
    #    experiment = ExperimentFactory.create(
    #        name=name,
    #        data_path=data_path,
    #        sample_form=sample_form,
    #        beam_mode=beam_mode,
    #        radiation_probe=radiation_probe,
    #        scattering_type=scattering_type,
    #    )
    #    self.add(experiment)

    # @typechecked
    # def add_without_data(
    #    self,
    #    name: str,
    #    sample_form: str = SampleFormEnum.default().value,
    #    beam_mode: str = BeamModeEnum.default().value,
    #    radiation_probe: str = RadiationProbeEnum.default().value,
    #    scattering_type: str = ScatteringTypeEnum.default().value,
    # ):
    #    """Add an experiment without associating a data file.
    #
    #    Args:
    #        name: Experiment identifier.
    #        sample_form: Sample form (powder or single crystal).
    #        beam_mode: Beam mode (constant wavelength or TOF).
    #        radiation_probe: Radiation probe (neutron or xray).
    #        scattering_type: Scattering type (bragg or total).
    #    """
    #    experiment = ExperimentFactory.create(
    #        name=name,
    #        sample_form=sample_form,
    #        beam_mode=beam_mode,
    #        radiation_probe=radiation_probe,
    #        scattering_type=scattering_type,
    #    )
    #    self.add(experiment)

    # TODO: Move to DatablockCollection?
    @typechecked
    def remove(self, name: str) -> None:
        """Remove an experiment by name if it exists."""
        if name in self:
            del self[name]

    # ------------
    # Show methods
    # ------------

    # TODO: Move to DatablockCollection?
    def show_names(self) -> None:
        """Print the list of experiment names."""
        console.paragraph('Defined experiments' + ' 🔬')
        console.print(self.names)

    # TODO: Move to DatablockCollection?
    def show_params(self) -> None:
        """Print parameters for each experiment in the collection."""
        for exp in self.values():
            exp.show_params()
