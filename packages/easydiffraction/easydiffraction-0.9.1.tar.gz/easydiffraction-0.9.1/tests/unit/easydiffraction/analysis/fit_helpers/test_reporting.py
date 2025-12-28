# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

def test_module_import():
    import easydiffraction.analysis.fit_helpers.reporting as MUT

    expected_module_name = 'easydiffraction.analysis.fit_helpers.reporting'
    actual_module_name = MUT.__name__
    assert expected_module_name == actual_module_name


def test_fitresults_display_results_prints_and_table(capsys, monkeypatch):
    # Arrange: build a minimal fake parameter object with required attributes
    class Identity:
        def __init__(self):
            self.datablock_entry_name = 'db'
            self.category_code = 'cat'
            self.category_entry_name = 'entry'

    class Param:
        def __init__(self, start, value, uncertainty, name='p', units='u'):
            self._identity = Identity()
            self._fit_start_value = start
            self.value = value
            self.uncertainty = uncertainty
            self.name = name
            self.units = units

    from easydiffraction.analysis.fit_helpers.reporting import FitResults

    params = [Param(start=1.0, value=1.2, uncertainty=0.05, name='a', units='arb')]

    # Act: create results and display with all metrics available
    fr = FitResults(
        success=True,
        parameters=params,
        reduced_chi_square=1.2345,
        fitting_time=0.9876,
    )

    y_obs = [10.0, 20.0]
    y_calc = [9.5, 19.5]
    y_err = [1.0, 1.0]
    f_obs = [5.0, 6.0]
    f_calc = [5.1, 5.9]

    fr.display_results(y_obs=y_obs, y_calc=y_calc, y_err=y_err, f_obs=f_obs, f_calc=f_calc)

    # Assert: key lines printed and a table rendered
    out = capsys.readouterr().out
    assert 'Fit results' in out
    assert 'Success: True' in out
    assert 'reduced χ²' in out
    assert 'R-factor (Rf)' in out
    assert 'R-factor squared (Rf²)' in out
    assert 'Weighted R-factor (wR)' in out
    assert 'Bragg R-factor (BR)' in out
    assert 'Fitted parameters:' in out
    # Table border: accept common border glyphs from Rich/tabulate
    assert any(ch in out for ch in ('╒', '┌', '+', '─'))
