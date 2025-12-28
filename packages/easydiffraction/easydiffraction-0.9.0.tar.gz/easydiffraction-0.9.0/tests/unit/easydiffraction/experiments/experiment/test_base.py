# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

def test_module_import():
    import easydiffraction.experiments.experiment.base as MUT

    expected_module_name = 'easydiffraction.experiments.experiment.base'
    actual_module_name = MUT.__name__
    assert expected_module_name == actual_module_name


def test_pd_experiment_peak_profile_type_switch(capsys):
    from easydiffraction.experiments.categories.experiment_type import ExperimentType
    from easydiffraction.experiments.experiment.base import PdExperimentBase
    from easydiffraction.experiments.experiment.enums import BeamModeEnum
    from easydiffraction.experiments.experiment.enums import PeakProfileTypeEnum
    from easydiffraction.experiments.experiment.enums import RadiationProbeEnum
    from easydiffraction.experiments.experiment.enums import SampleFormEnum
    from easydiffraction.experiments.experiment.enums import ScatteringTypeEnum

    class ConcretePd(PdExperimentBase):
        def _load_ascii_data_to_experiment(self, data_path: str) -> None:
            pass

    et = ExperimentType(
        sample_form=SampleFormEnum.POWDER.value,
        beam_mode=BeamModeEnum.CONSTANT_WAVELENGTH.value,
        radiation_probe=RadiationProbeEnum.NEUTRON.value,
        scattering_type=ScatteringTypeEnum.BRAGG.value,
    )
    ex = ConcretePd(name='ex1', type=et)
    # valid switch using enum
    ex.peak_profile_type = PeakProfileTypeEnum.PSEUDO_VOIGT
    assert ex.peak_profile_type == PeakProfileTypeEnum.PSEUDO_VOIGT
    # invalid string should warn and keep previous
    ex.peak_profile_type = 'non-existent'
    captured = capsys.readouterr().out
    assert 'Unsupported' in captured or 'Unknown' in captured
