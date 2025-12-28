# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

def test_list_and_show_supported_calculators_do_not_crash(capsys, monkeypatch):
    from easydiffraction.analysis.calculators.factory import CalculatorFactory

    # Simulate no engines available by forcing engine_imported to False
    class DummyCalc:
        def __call__(self):
            return self

        @property
        def engine_imported(self):
            return False

    monkeypatch = monkeypatch  # keep name
    monkeypatch.setitem(
        CalculatorFactory._potential_calculators,
        'dummy',
        {
            'description': 'Dummy calc',
            'class': DummyCalc,
        },
    )

    lst = CalculatorFactory.list_supported_calculators()
    assert isinstance(lst, list)

    CalculatorFactory.show_supported_calculators()
    out = capsys.readouterr().out
    # Should print the paragraph title
    assert 'Supported calculators' in out


def test_create_calculator_unknown_returns_none(capsys):
    from easydiffraction.analysis.calculators.factory import CalculatorFactory

    obj = CalculatorFactory.create_calculator('this_is_unknown')
    assert obj is None
    out = capsys.readouterr().out
    assert 'Unknown calculator' in out
