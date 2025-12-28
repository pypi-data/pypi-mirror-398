# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

import pytest



def test_module_import():
    import easydiffraction.experiments.experiment.factory as MUT

    expected_module_name = 'easydiffraction.experiments.experiment.factory'
    actual_module_name = MUT.__name__
    assert expected_module_name == actual_module_name


def test_experiment_factory_create_without_data_and_invalid_combo():
    import easydiffraction.experiments.experiment.factory as EF
    from easydiffraction.experiments.experiment.enums import BeamModeEnum
    from easydiffraction.experiments.experiment.enums import RadiationProbeEnum
    from easydiffraction.experiments.experiment.enums import SampleFormEnum
    from easydiffraction.experiments.experiment.enums import ScatteringTypeEnum

    ex = EF.ExperimentFactory.create(
        name='ex1',
        sample_form=SampleFormEnum.POWDER.value,
        beam_mode=BeamModeEnum.CONSTANT_WAVELENGTH.value,
        radiation_probe=RadiationProbeEnum.NEUTRON.value,
        scattering_type=ScatteringTypeEnum.BRAGG.value,
    )
    # Instance should be created (BraggPdExperiment)
    assert hasattr(ex, 'type') and ex.type.sample_form.value == SampleFormEnum.POWDER.value

    # invalid combination: unexpected key
    with pytest.raises(ValueError):
        EF.ExperimentFactory.create(name='ex2', unexpected=True)
