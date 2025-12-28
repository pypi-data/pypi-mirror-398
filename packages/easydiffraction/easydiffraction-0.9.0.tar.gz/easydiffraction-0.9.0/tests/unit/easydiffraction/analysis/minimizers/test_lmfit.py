# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

import types

import numpy as np


def test_module_import():
    import easydiffraction.analysis.minimizers.lmfit as MUT

    assert MUT.__name__ == 'easydiffraction.analysis.minimizers.lmfit'


def test_lmfit_prepare_and_sync(monkeypatch):
    from easydiffraction.analysis.minimizers.lmfit import LmfitMinimizer

    class P:
        def __init__(self, name, value, free=True, lo=-np.inf, hi=np.inf):
            self._minimizer_uid = name
            self._value = value
            self.free = free
            self.fit_min = lo
            self.fit_max = hi
            self.uncertainty = None

        @property
        def value(self):
            return self._value

        @value.setter
        def value(self, v):
            self._value = v

    # Fake lmfit.Parameters and result structure
    class FakeParam:
        def __init__(self, value, stderr=None):
            self.value = value
            self.stderr = stderr

    class FakeParams(dict):
        def add(self, name, value, vary, min, max):
            self[name] = types.SimpleNamespace(value=value, vary=vary, min=min, max=max)

    class FakeResult:
        def __init__(self):
            self.params = {'p1': FakeParam(10.0, stderr=0.5), 'p2': FakeParam(20.0, stderr=1.0)}
            self.success = True

    # Monkeypatch lmfit in module namespace
    import easydiffraction.analysis.minimizers.lmfit as lm

    monkeypatch.setattr(
        lm,
        'lmfit',
        types.SimpleNamespace(Parameters=FakeParams, minimize=lambda *a, **k: FakeResult()),
    )

    minim = LmfitMinimizer()
    params = [P('p1', 1.0), P('p2', 2.0)]

    # Prepare
    kwargs = minim._prepare_solver_args(params)
    assert isinstance(kwargs.get('engine_parameters'), FakeParams)
    # Run solver calls our fake minimize and returns FakeResult
    res = minim._run_solver(lambda *a, **k: np.array([0.0]), **kwargs)
    assert isinstance(res, FakeResult)

    # Sync back updates parameter values and uncertainties
    minim._sync_result_to_parameters(params, res)
    assert params[0].value == 10.0 and params[0].uncertainty == 0.5
    assert params[1].value == 20.0 and params[1].uncertainty == 1.0
    assert minim._check_success(res) is True
