# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

import numpy as np


def test_module_import():
    import easydiffraction.analysis.minimizers.base as MUT

    assert MUT.__name__ == 'easydiffraction.analysis.minimizers.base'


def test_minimizer_base_fit_flow_and_finalize():
    from easydiffraction.analysis.minimizers.base import MinimizerBase

    class DummyParam:
        def __init__(self, v):
            self.value = v

    class DummyResult:
        def __init__(self, success=True):
            self.success = success

    class DummyMinimizer(MinimizerBase):
        def __init__(self):
            super().__init__(name='dummy', method='m', max_iterations=5)
            self.synced = False

        def _prepare_solver_args(self, parameters):
            # Make sure parameters list is received
            assert isinstance(parameters, list)
            return {'engine_parameters': {'ok': True}}

        def _run_solver(self, objective_function, **kwargs):
            # Exercise calling of the provided objective
            residuals = objective_function(kwargs.get('engine_parameters'))
            # Update tracker so finish_tracking has valid metrics
            self.tracker.track(residuals=np.array(residuals), parameters=[1])
            return DummyResult(success=True)

        def _sync_result_to_parameters(self, parameters, raw_result):
            # Mark that syncing happened and tweak a parameter
            self.synced = True
            if parameters:
                parameters[0].value = 42

        def _check_success(self, raw_result):
            return getattr(raw_result, 'success', False)

        # Provide residuals implementation used by _objective_function
        def _compute_residuals(
            self, engine_params, parameters, sample_models, experiments, calculator
        ):
            # Minimal residuals; verify engine params passed through
            assert engine_params == {'ok': True}
            return np.array([0.0, 0.0])

    minim = DummyMinimizer()

    params = [DummyParam(1.0), DummyParam(2.0)]

    # Wrap minimizer's objective creator to simulate higher-level usage
    objective = minim._create_objective_function(
        parameters=params,
        sample_models=None,
        experiments=None,
        calculator=None,
    )

    result = minim.fit(parameters=params, objective_function=objective)

    # Assertions: finalize populated, sync occurred, tracker captured time
    assert result.success is True
    assert minim.synced is True
    assert isinstance(result.parameters, list) and result.parameters[0].value == 42
    # Fitting time should be a positive float
    assert minim.tracker.fitting_time is not None and minim.tracker.fitting_time >= 0.0


def test_minimizer_base_create_objective_function_uses_compute_residuals():
    from easydiffraction.analysis.minimizers.base import MinimizerBase

    class M(MinimizerBase):
        def _prepare_solver_args(self, parameters):
            return {}

        def _run_solver(self, objective_function, **kwargs):
            return None

        def _sync_result_to_parameters(self, parameters, raw_result):
            pass

        def _check_success(self, raw_result):
            return True

        def _compute_residuals(
            self, engine_params, parameters, sample_models, experiments, calculator
        ):
            # Return a deterministic vector to assert against
            return np.array([1.0, 2.0, 3.0])

    m = M()
    f = m._create_objective_function(
        parameters=[], sample_models=None, experiments=None, calculator=None
    )
    out = f({})
    assert np.allclose(out, np.array([1.0, 2.0, 3.0]))
