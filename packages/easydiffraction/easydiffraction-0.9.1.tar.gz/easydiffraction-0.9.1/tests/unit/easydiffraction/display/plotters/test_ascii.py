# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

import numpy as np


def test_module_import():
    import easydiffraction.display.plotters.ascii as MUT

    expected_module_name = 'easydiffraction.display.plotters.ascii'
    actual_module_name = MUT.__name__
    assert expected_module_name == actual_module_name


def test_ascii_plotter_plot_minimal(capsys):
    from easydiffraction.display.plotters.ascii import AsciiPlotter

    x = np.array([0.0, 1.0, 2.0])
    y = np.array([1.0, 2.0, 3.0])
    p = AsciiPlotter()
    p.plot(x=x, y_series=[y], labels=['meas'], axes_labels=['x', 'y'], title='T', height=5)
    out = capsys.readouterr().out
    assert 'Displaying data for selected x-range' in out
