# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from easydiffraction.experiments.categories.peak.cwl import CwlPseudoVoigt
from easydiffraction.experiments.categories.peak.cwl import CwlSplitPseudoVoigt
from easydiffraction.experiments.categories.peak.cwl import CwlThompsonCoxHastings


def test_cwl_pseudo_voigt_params_exist_and_settable():
    peak = CwlPseudoVoigt()
    # Created by _add_constant_wavelength_broadening
    assert peak.broad_gauss_u.name == 'broad_gauss_u'
    peak.broad_gauss_u = 0.123
    assert peak.broad_gauss_u.value == 0.123


def test_cwl_split_pseudo_voigt_adds_empirical_asymmetry():
    peak = CwlSplitPseudoVoigt()
    # Has broadening and empirical asymmetry params
    assert peak.broad_gauss_w.name == 'broad_gauss_w'
    assert peak.asym_empir_1.name == 'asym_empir_1'
    peak.asym_empir_2 = 0.345
    assert peak.asym_empir_2.value == 0.345


def test_cwl_tch_adds_fcj_asymmetry():
    peak = CwlThompsonCoxHastings()
    assert peak.asym_fcj_1.name == 'asym_fcj_1'
    peak.asym_fcj_2 = 0.456
    assert peak.asym_fcj_2.value == 0.456
