# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

import numpy as np


def test_calculate_r_metrics_and_chi_square():
    from easydiffraction.analysis.fit_helpers import metrics as M

    y_obs = np.array([1.0, 2.0, 3.0])
    y_calc = np.array([1.1, 1.9, 2.8])
    weights = np.array([1.0, 2.0, 3.0])
    residuals = y_obs - y_calc

    r = M.calculate_r_factor(y_obs, y_calc)
    rb = M.calculate_rb_factor(y_obs, y_calc)
    rw = M.calculate_weighted_r_factor(y_obs, y_calc, weights)
    r2 = M.calculate_r_factor_squared(y_obs, y_calc)
    chi2 = M.calculate_reduced_chi_square(residuals, num_parameters=1)

    assert 0 <= r <= 1 and np.isfinite(r)
    assert np.isclose(r, rb)
    assert np.isfinite(rw)
    assert np.isfinite(r2)
    assert np.isfinite(chi2)


def test_get_reliability_inputs_collects_arrays_with_default_su():
    from easydiffraction.analysis.fit_helpers import metrics as M

    # Minimal fakes for experiments
    class DS:
        def __init__(self):
            self.meas = np.array([1.0, 2.0])
            self.meas_su = None  # triggers default ones
            self.calc = np.array([1.1, 1.9])

    class Expt:
        def __init__(self):
            self.data = DS()

        def _update_categories(self, called_by_minimizer=False):
            pass

    class Expts(dict):
        def values(self):
            return [Expt()]

    class SampleModels(dict):
        pass

    y_obs, y_calc, y_err = M.get_reliability_inputs(SampleModels(), Expts())
    assert y_obs.shape == (2,) and y_calc.shape == (2,) and y_err.shape == (2,)
    assert np.allclose(y_err, 1.0)
