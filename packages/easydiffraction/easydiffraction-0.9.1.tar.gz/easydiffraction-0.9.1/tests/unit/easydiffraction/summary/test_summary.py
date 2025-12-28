# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

def test_summary_as_cif_returns_placeholder_string():
    from easydiffraction.summary.summary import Summary

    class P:
        pass

    s = Summary(P())
    out = s.as_cif()
    assert isinstance(out, str)
    assert 'To be added' in out


def test_summary_show_report_prints_sections(capsys):
    from easydiffraction.summary.summary import Summary

    class Info:
        title = 'T'
        description = ''

    class Project:
        def __init__(self):
            self.info = Info()
            self.sample_models = {}  # empty mapping to exercise loops safely
            self.experiments = {}  # empty mapping to exercise loops safely

            class A:
                current_calculator = 'cryspy'
                current_minimizer = 'lmfit'

                class R:
                    reduced_chi_square = 0.0

                fit_results = R()

            self.analysis = A()

    s = Summary(Project())
    s.show_report()
    out = capsys.readouterr().out
    # Verify that all top-level sections appear (titles are uppercased by formatter)
    assert 'PROJECT INFO' in out
    assert 'CRYSTALLOGRAPHIC DATA' in out
    assert 'EXPERIMENTS' in out
    assert 'FITTING' in out







def test_module_import():
    import easydiffraction.summary.summary as MUT

    expected_module_name = 'easydiffraction.summary.summary'
    actual_module_name = MUT.__name__
    assert expected_module_name == actual_module_name
