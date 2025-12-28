# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

import pytest

from easydiffraction.experiments.categories.experiment_type import ExperimentType
from easydiffraction.experiments.experiment.bragg_sc import BraggScExperiment
from easydiffraction.experiments.experiment.enums import BeamModeEnum
from easydiffraction.experiments.experiment.enums import RadiationProbeEnum
from easydiffraction.experiments.experiment.enums import SampleFormEnum
from easydiffraction.experiments.experiment.enums import ScatteringTypeEnum
from easydiffraction.utils.logging import Logger


def _mk_type_sc_bragg():
    return ExperimentType(
        sample_form=SampleFormEnum.SINGLE_CRYSTAL.value,
        beam_mode=BeamModeEnum.CONSTANT_WAVELENGTH.value,
        radiation_probe=RadiationProbeEnum.NEUTRON.value,
        scattering_type=ScatteringTypeEnum.BRAGG.value,
    )


class _ConcreteBraggSc(BraggScExperiment):
    def _load_ascii_data_to_experiment(self, data_path: str) -> None:
        # Not used in this test
        pass


def test_init_and_placeholder_no_crash(monkeypatch: pytest.MonkeyPatch):
    # Prevent logger from raising on attribute errors inside __init__
    monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)
    expt = _ConcreteBraggSc(name='sc1', type=_mk_type_sc_bragg())
    # show_meas_chart just prints placeholder text; ensure no exception
    expt.show_meas_chart()
