# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

def test_module_import():
    import easydiffraction.analysis.calculators.base as MUT

    assert MUT.__name__ == 'easydiffraction.analysis.calculators.base'
