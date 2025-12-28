# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from easydiffraction.experiments.categories.peak.base import PeakBase


def test_peak_base_identity_code():
    class DummyPeak(PeakBase):
        def __init__(self):
            super().__init__()

    p = DummyPeak()
    assert p._identity.category_code == 'peak'
