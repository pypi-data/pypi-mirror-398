# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

def test_module_import():
    import easydiffraction.analysis.calculators.cryspy as MUT

    assert MUT.__name__ == 'easydiffraction.analysis.calculators.cryspy'


def test_cryspy_calculator_engine_flag_and_converters():
    # These tests avoid requiring real cryspy by not invoking heavy paths
    from easydiffraction.analysis.calculators.cryspy import CryspyCalculator

    calc = CryspyCalculator()
    # engine_imported is boolean (may be False if cryspy not installed)
    assert isinstance(calc.engine_imported, bool)

    # Converters should just delegate/format without external deps
    class DummySample:
        @property
        def as_cif(self):
            return 'data_x'

    # _convert_sample_model_to_cryspy_cif returns input as_cif
    assert calc._convert_sample_model_to_cryspy_cif(DummySample()) == 'data_x'
