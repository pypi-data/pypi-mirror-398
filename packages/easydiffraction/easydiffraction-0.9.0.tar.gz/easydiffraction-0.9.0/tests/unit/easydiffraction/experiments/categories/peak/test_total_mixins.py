# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from easydiffraction.experiments.categories.peak.total import TotalGaussianDampedSinc


def test_total_gaussian_damped_sinc_params():
    peak = TotalGaussianDampedSinc()
    assert peak.damp_q.name == 'damp_q'
    peak.damp_q = 0.12
    assert peak.damp_q.value == 0.12
    assert peak.broad_q.name == 'broad_q'
