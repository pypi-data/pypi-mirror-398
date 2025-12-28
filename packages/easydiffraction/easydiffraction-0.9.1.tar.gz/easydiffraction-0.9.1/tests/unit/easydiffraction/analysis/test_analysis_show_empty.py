# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

def test_show_params_empty_branches(capsys):
    from easydiffraction.analysis.analysis import Analysis

    class Empty:
        @property
        def parameters(self):
            return []

        @property
        def fittable_parameters(self):
            return []

        @property
        def free_parameters(self):
            return []

    class P:
        sample_models = Empty()
        experiments = Empty()
        _varname = 'proj'

    a = Analysis(project=P())

    # show_all_params -> warning path
    a.show_all_params()
    # show_fittable_params -> warning path
    a.show_fittable_params()
    # show_free_params -> warning path
    a.show_free_params()

    out = capsys.readouterr().out
    assert (
        'No parameters found' in out
        or 'No fittable parameters' in out
        or 'No free parameters' in out
    )
