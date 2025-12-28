# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

def test_cwl_peak_classes_expose_expected_parameters_and_category():
    from easydiffraction.experiments.categories.peak.cwl import CwlPseudoVoigt
    from easydiffraction.experiments.categories.peak.cwl import CwlSplitPseudoVoigt
    from easydiffraction.experiments.categories.peak.cwl import CwlThompsonCoxHastings

    pv = CwlPseudoVoigt()
    spv = CwlSplitPseudoVoigt()
    tch = CwlThompsonCoxHastings()

    # Category code set by PeakBase
    for obj in (pv, spv, tch):
        assert obj._identity.category_code == 'peak'

    # Broadening parameters added by CwlBroadeningMixin
    for obj in (pv, spv, tch):
        names = {p.name for p in obj.parameters}
        assert {
            'broad_gauss_u',
            'broad_gauss_v',
            'broad_gauss_w',
            'broad_lorentz_x',
            'broad_lorentz_y',
        }.issubset(names)

    # EmpiricalAsymmetry added only for split PV
    names_spv = {p.name for p in spv.parameters}
    assert {'asym_empir_1', 'asym_empir_2', 'asym_empir_3', 'asym_empir_4'}.issubset(names_spv)

    # FCJ asymmetry for TCH
    names_tch = {p.name for p in tch.parameters}
    assert {'asym_fcj_1', 'asym_fcj_2'}.issubset(names_tch)
