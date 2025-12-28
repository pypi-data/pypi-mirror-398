# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

import numpy as np


def test_module_import():
    import easydiffraction.analysis.fit_helpers.tracking as MUT

    expected_module_name = 'easydiffraction.analysis.fit_helpers.tracking'
    actual_module_name = MUT.__name__
    assert expected_module_name == actual_module_name


def test_tracker_terminal_flow_prints_and_updates_best(monkeypatch, capsys):
    import easydiffraction.analysis.fit_helpers.tracking as tracking_mod
    from easydiffraction.analysis.fit_helpers.tracking import FitProgressTracker

    # Force terminal branch (not notebook): tracking imports in_jupyter directly
    monkeypatch.setattr(tracking_mod, 'in_jupyter', lambda: False)

    tracker = FitProgressTracker()
    tracker.start_tracking('dummy')
    tracker.start_timer()

    # First iteration sets previous and best
    res1 = np.array([2.0, 1.0])  # chi2 = 5, dof depends on num params but relative change only
    tracker.track(res1, parameters=[1])

    # Second iteration small change below threshold -> no row emitted
    out1 = capsys.readouterr().out
    assert 'Goodness-of-fit' in out1

    res2 = np.array([1.9, 1.0])
    tracker.track(res2, parameters=[1])

    # Third iteration large improvement -> row emitted
    res3 = np.array([0.1, 0.1])
    tracker.track(res3, parameters=[1])

    tracker.stop_timer()
    tracker.finish_tracking()
    out2 = capsys.readouterr().out
    assert 'Best goodness-of-fit' in out2
    assert tracker.best_iteration is not None
