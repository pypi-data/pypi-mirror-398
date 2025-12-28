# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

import pytest


def test_peak_factory_default_and_combinations_and_errors():
    from easydiffraction.experiments.categories.peak.factory import PeakFactory
    from easydiffraction.experiments.experiment.enums import BeamModeEnum
    from easydiffraction.experiments.experiment.enums import PeakProfileTypeEnum
    from easydiffraction.experiments.experiment.enums import ScatteringTypeEnum

    # Defaults -> valid object for default enums
    p = PeakFactory.create()
    assert p._identity.category_code == 'peak'

    # Explicit valid combos
    p1 = PeakFactory.create(
        ScatteringTypeEnum.BRAGG,
        BeamModeEnum.CONSTANT_WAVELENGTH,
        PeakProfileTypeEnum.PSEUDO_VOIGT,
    )
    assert p1.__class__.__name__ == 'CwlPseudoVoigt'
    p2 = PeakFactory.create(
        ScatteringTypeEnum.BRAGG,
        BeamModeEnum.TIME_OF_FLIGHT,
        PeakProfileTypeEnum.PSEUDO_VOIGT_IKEDA_CARPENTER,
    )
    assert p2.__class__.__name__ == 'TofPseudoVoigtIkedaCarpenter'
    p3 = PeakFactory.create(
        ScatteringTypeEnum.TOTAL,
        BeamModeEnum.CONSTANT_WAVELENGTH,
        PeakProfileTypeEnum.GAUSSIAN_DAMPED_SINC,
    )
    assert p3.__class__.__name__ == 'TotalGaussianDampedSinc'

    # Invalid scattering type
    class FakeST:
        pass

    with pytest.raises(ValueError):
        PeakFactory.create(
            FakeST, BeamModeEnum.CONSTANT_WAVELENGTH, PeakProfileTypeEnum.PSEUDO_VOIGT
        )  # type: ignore[arg-type]

    # Invalid beam mode
    class FakeBM:
        pass

    with pytest.raises(ValueError):
        PeakFactory.create(ScatteringTypeEnum.BRAGG, FakeBM, PeakProfileTypeEnum.PSEUDO_VOIGT)  # type: ignore[arg-type]

    # Invalid profile type
    class FakePPT:
        pass

    with pytest.raises(ValueError):
        PeakFactory.create(ScatteringTypeEnum.BRAGG, BeamModeEnum.CONSTANT_WAVELENGTH, FakePPT)  # type: ignore[arg-type]
