# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

import numpy as np


def test_line_segment_background_calculate_and_cif():
    from types import SimpleNamespace

    from easydiffraction.experiments.categories.background.line_segment import (
        LineSegmentBackground,
    )

    # Create mock parent with data
    x = np.array([0.0, 1.0, 2.0])
    mock_data = SimpleNamespace(x=x, _bkg=None)
    mock_data._set_bkg = lambda y: setattr(mock_data, '_bkg', y)
    mock_parent = SimpleNamespace(data=mock_data)

    bkg = LineSegmentBackground()
    object.__setattr__(bkg, '_parent', mock_parent)

    # No points -> zeros
    bkg._update()
    assert np.allclose(mock_data._bkg, [0.0, 0.0, 0.0])

    # Add two points -> linear interpolation
    bkg.add(id='1', x=0.0, y=0.0)
    bkg.add(id='2', x=2.0, y=4.0)
    bkg._update()
    assert np.allclose(mock_data._bkg, [0.0, 2.0, 4.0])

    # CIF loop has correct header and rows
    cif = bkg.as_cif
    assert (
        'loop_' in cif
        and '_pd_background.line_segment_X' in cif
        and '_pd_background.line_segment_intensity' in cif
    )
