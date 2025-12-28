# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

def test_module_import():
    import easydiffraction.experiments.experiment.enums as MUT

    expected_module_name = 'easydiffraction.experiments.experiment.enums'
    actual_module_name = MUT.__name__
    assert expected_module_name == actual_module_name


def test_default_enums_consistency():
    import easydiffraction.experiments.experiment.enums as MUT

    assert MUT.SampleFormEnum.default() in list(MUT.SampleFormEnum)
    assert MUT.ScatteringTypeEnum.default() in list(MUT.ScatteringTypeEnum)
    assert MUT.RadiationProbeEnum.default() in list(MUT.RadiationProbeEnum)
    assert MUT.BeamModeEnum.default() in list(MUT.BeamModeEnum)
