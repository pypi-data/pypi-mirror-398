# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

import pytest


def test_module_import():
    import easydiffraction.analysis.calculators.crysfml as MUT

    assert MUT.__name__ == 'easydiffraction.analysis.calculators.crysfml'


def test_crysfml_engine_flag_and_structure_factors_raises():
    from easydiffraction.analysis.calculators.crysfml import CrysfmlCalculator

    calc = CrysfmlCalculator()
    # engine_imported is a boolean flag; it may be False in our env
    assert isinstance(calc.engine_imported, bool)
    with pytest.raises(NotImplementedError):
        calc.calculate_structure_factors(sample_models=None, experiments=None)


def test_crysfml_adjust_pattern_length_truncates():
    from easydiffraction.analysis.calculators.crysfml import CrysfmlCalculator

    calc = CrysfmlCalculator()
    long = list(range(10))
    out = calc._adjust_pattern_length(long, target_length=4)
    assert out == [0, 1, 2, 3]
