# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

import numpy as np


def test_module_import():
    import easydiffraction.analysis.minimizers.dfols as MUT

    assert MUT.__name__ == 'easydiffraction.analysis.minimizers.dfols'


def test_dfols_prepare_run_and_sync(monkeypatch):
    from easydiffraction.analysis.minimizers.dfols import DfolsMinimizer

    class P:
        def __init__(self, v, lo=-np.inf, hi=np.inf):
            self.value = v
            self.fit_min = lo
            self.fit_max = hi
            self.uncertainty = None

    class FakeRes:
        EXIT_SUCCESS = 0

        def __init__(self):
            self.x = np.array([3.0, 4.0])
            self.flag = 0

    # Patch dfols.solve to return our FakeRes
    import easydiffraction.analysis.minimizers.dfols as mod

    def fake_solve(fun, x0, bounds, maxfun):
        # Verify we pass reasonable arguments
        assert isinstance(x0, np.ndarray) and x0.shape[0] == 2
        assert isinstance(bounds, tuple) and all(isinstance(b, np.ndarray) for b in bounds)
        return FakeRes()

    monkeypatch.setattr(mod, 'solve', fake_solve)

    minim = DfolsMinimizer(max_iterations=10)
    params = [P(1.0, lo=0.0, hi=5.0), P(2.0, lo=1.0, hi=6.0)]
    kwargs = minim._prepare_solver_args(params)
    assert set(kwargs.keys()) == {'x0', 'bounds'}
    res = minim._run_solver(lambda p: np.array([0.0]), **kwargs)
    # Sync back values and check success flag handling
    minim._sync_result_to_parameters(params, res)
    assert params[0].value == 3.0 and params[1].value == 4.0
    assert params[0].uncertainty is None and params[1].uncertainty is None
    assert minim._check_success(res) is True
