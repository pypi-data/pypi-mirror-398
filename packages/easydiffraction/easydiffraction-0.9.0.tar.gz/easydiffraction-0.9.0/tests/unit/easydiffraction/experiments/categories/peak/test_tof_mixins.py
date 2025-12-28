# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

import numpy as np


def test_tof_broadening_and_asymmetry_mixins():
    from easydiffraction.experiments.categories.peak.base import PeakBase
    from easydiffraction.experiments.categories.peak.tof_mixins import IkedaCarpenterAsymmetryMixin
    from easydiffraction.experiments.categories.peak.tof_mixins import TofBroadeningMixin

    class TofPeak(PeakBase, TofBroadeningMixin, IkedaCarpenterAsymmetryMixin):
        def __init__(self):
            super().__init__()
            self._add_time_of_flight_broadening()
            self._add_ikeda_carpenter_asymmetry()

    p = TofPeak()
    names = {param.name for param in p.parameters}
    # Broadening
    assert {
        'gauss_sigma_0',
        'gauss_sigma_1',
        'gauss_sigma_2',
        'lorentz_gamma_0',
        'lorentz_gamma_1',
        'lorentz_gamma_2',
        'mix_beta_0',
        'mix_beta_1',
    }.issubset(names)
    # Asymmetry
    assert {'asym_alpha_0', 'asym_alpha_1'}.issubset(names)

    # Verify setters update values
    p.broad_gauss_sigma_0 = 1.0
    p.asym_alpha_1 = 0.5
    assert np.isclose(p.broad_gauss_sigma_0.value, 1.0)
    assert np.isclose(p.asym_alpha_1.value, 0.5)
