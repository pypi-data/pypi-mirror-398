# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

import importlib
import types
import sys


def test_module_import():
    import easydiffraction.display.plotters.base as MUT

    expected_module_name = 'easydiffraction.display.plotters.base'
    actual_module_name = MUT.__name__
    assert expected_module_name == actual_module_name


def test_default_engine_switches_with_notebook(monkeypatch):
    from easydiffraction.display.plotting import PlotterEngineEnum

    # Simulate running in a Jupyter kernel
    mod = types.ModuleType('IPython')
    mod.get_ipython = lambda: types.SimpleNamespace(config={'IPKernelApp': True})
    monkeypatch.setitem(sys.modules, 'IPython', mod)
    assert PlotterEngineEnum.default().value == 'plotly'

    # Now simulate non-notebook environment
    mod2 = types.ModuleType('IPython')
    mod2.get_ipython = lambda: None
    monkeypatch.setitem(sys.modules, 'IPython', mod2)
    assert PlotterEngineEnum.default().value == 'asciichartpy'


def test_default_axes_labels_keys_present():
    import easydiffraction.display.plotters.base as pb
    from easydiffraction.experiments.experiment.enums import BeamModeEnum
    from easydiffraction.experiments.experiment.enums import ScatteringTypeEnum

    assert (ScatteringTypeEnum.BRAGG, BeamModeEnum.CONSTANT_WAVELENGTH) in pb.DEFAULT_AXES_LABELS
    assert (ScatteringTypeEnum.BRAGG, BeamModeEnum.TIME_OF_FLIGHT) in pb.DEFAULT_AXES_LABELS
