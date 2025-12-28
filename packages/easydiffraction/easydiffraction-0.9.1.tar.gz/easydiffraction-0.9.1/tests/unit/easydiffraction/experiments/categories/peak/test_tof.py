# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from easydiffraction.experiments.categories.peak.tof import TofPseudoVoigt
from easydiffraction.experiments.categories.peak.tof import TofPseudoVoigtBackToBack
from easydiffraction.experiments.categories.peak.tof import TofPseudoVoigtIkedaCarpenter


def test_tof_pseudo_voigt_has_broadening_params():
    peak = TofPseudoVoigt()
    assert peak.broad_gauss_sigma_0.name == 'gauss_sigma_0'
    peak.broad_gauss_sigma_2 = 1.23
    assert peak.broad_gauss_sigma_2.value == 1.23


def test_tof_back_to_back_adds_ikeda_carpenter():
    peak = TofPseudoVoigtBackToBack()
    assert peak.asym_alpha_0.name == 'asym_alpha_0'
    peak.asym_alpha_1 = 0.77
    assert peak.asym_alpha_1.value == 0.77


def test_tof_ikeda_carpenter_has_mix_beta():
    peak = TofPseudoVoigtIkedaCarpenter()
    assert peak.broad_mix_beta_0.name == 'mix_beta_0'
