# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

import numpy as np


def test_total_gaussian_damped_sinc_parameters_and_setters():
    from easydiffraction.experiments.categories.peak.total import TotalGaussianDampedSinc

    p = TotalGaussianDampedSinc()
    assert p._identity.category_code == 'peak'
    names = {param.name for param in p.parameters}
    assert {
        'damp_q',
        'broad_q',
        'cutoff_q',
        'sharp_delta_1',
        'sharp_delta_2',
        'damp_particle_diameter',
    }.issubset(names)

    # Setters update values
    p.damp_q = 0.1
    p.broad_q = 0.2
    p.cutoff_q = 30.0
    p.sharp_delta_1 = 1.0
    p.sharp_delta_2 = 2.0
    p.damp_particle_diameter = 50.0

    vals = {param.name: param.value for param in p.parameters}
    assert np.isclose(vals['damp_q'], 0.1)
    assert np.isclose(vals['broad_q'], 0.2)
    assert np.isclose(vals['cutoff_q'], 30.0)
    assert np.isclose(vals['sharp_delta_1'], 1.0)
    assert np.isclose(vals['sharp_delta_2'], 2.0)
    assert np.isclose(vals['damp_particle_diameter'], 50.0)
