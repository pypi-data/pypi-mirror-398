# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

def test_module_import():
    import easydiffraction.analysis.analysis as MUT

    expected_module_name = 'easydiffraction.analysis.analysis'
    actual_module_name = MUT.__name__
    assert expected_module_name == actual_module_name


def _make_project_with_names(names):
    class ExpCol:
        def __init__(self, names):
            self._names = names

        @property
        def names(self):
            return self._names

    class P:
        experiments = ExpCol(names)
        sample_models = object()
        _varname = 'proj'

    return P()


def test_show_current_calculator_and_minimizer_prints(capsys):
    from easydiffraction.analysis.analysis import Analysis

    a = Analysis(project=_make_project_with_names([]))
    a.show_current_calculator()
    a.show_current_minimizer()
    out = capsys.readouterr().out
    assert 'Current calculator' in out
    assert 'cryspy' in out
    assert 'Current minimizer' in out
    assert 'lmfit (leastsq)' in out


def test_current_calculator_setter_success_and_unknown(monkeypatch, capsys):
    from easydiffraction.analysis import calculators as calc_pkg
    from easydiffraction.analysis.analysis import Analysis

    a = Analysis(project=_make_project_with_names([]))

    # Success path
    monkeypatch.setattr(
        calc_pkg.factory.CalculatorFactory,
        'create_calculator',
        lambda name: object(),
    )
    a.current_calculator = 'pdffit'
    out = capsys.readouterr().out
    assert 'Current calculator changed to' in out
    assert a.current_calculator == 'pdffit'

    # Unknown path (create_calculator returns None): no change
    monkeypatch.setattr(
        calc_pkg.factory.CalculatorFactory,
        'create_calculator',
        lambda name: None,
    )
    a.current_calculator = 'unknown'
    assert a.current_calculator == 'pdffit'


def test_fit_modes_show_and_switch_to_joint(monkeypatch, capsys):
    from easydiffraction.analysis.analysis import Analysis

    a = Analysis(project=_make_project_with_names(['e1', 'e2']))

    a.show_available_fit_modes()
    a.show_current_fit_mode()
    out1 = capsys.readouterr().out
    assert 'Available fit modes' in out1
    assert 'Current fit mode' in out1
    assert 'single' in out1

    a.fit_mode = 'joint'
    out2 = capsys.readouterr().out
    assert 'Current fit mode changed to' in out2
    assert a.fit_mode == 'joint'
