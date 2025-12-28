# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

def test_module_import():
    import easydiffraction.analysis.fitting as MUT

    expected_module_name = 'easydiffraction.analysis.fitting'
    actual_module_name = MUT.__name__
    assert expected_module_name == actual_module_name


def test_fitter_early_exit_when_no_params(capsys, monkeypatch):
    from easydiffraction.analysis.fitting import Fitter

    class DummyCollection:
        free_parameters = []

        def __init__(self):
            self._names = ['e1']

        @property
        def names(self):
            return self._names

    class DummyMin:
        tracker = type('T', (), {'track': staticmethod(lambda a, b: a)})()

        def fit(self, params, obj):
            return None

    f = Fitter()
    # Avoid creating a real minimizer
    f.minimizer = DummyMin()
    f.fit(sample_models=DummyCollection(), experiments=DummyCollection())
    out = capsys.readouterr().out
    assert 'No parameters selected for fitting' in out
