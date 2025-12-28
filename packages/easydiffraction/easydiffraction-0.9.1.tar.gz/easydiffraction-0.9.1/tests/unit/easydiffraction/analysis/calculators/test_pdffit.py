# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

import numpy as np


def test_module_import():
    import easydiffraction.analysis.calculators.pdffit as MUT

    assert MUT.__name__ == 'easydiffraction.analysis.calculators.pdffit'


def test_pdffit_engine_flag_and_hkl_message(capsys):
    from easydiffraction.analysis.calculators.pdffit import PdffitCalculator

    calc = PdffitCalculator()
    assert isinstance(calc.engine_imported, bool)
    # calculate_structure_factors prints fixed message and returns [] by contract
    out = calc.calculate_structure_factors(sample_models=None, experiments=None)
    assert out == []
    # The method prints a note
    printed = capsys.readouterr().out
    assert 'HKLs (not applicable)' in printed


def test_pdffit_cif_v2_to_v1_regex_behavior(monkeypatch):
    # Exercise the regex conversion path indirectly by providing minimal objects
    from easydiffraction.analysis.calculators.pdffit import PdffitCalculator

    class DummyParam:
        def __init__(self, v):
            self.value = v

    class DummyPeak:
        # provide required attributes used in calculation
        def __init__(self):
            self.sharp_delta_1 = DummyParam(0.0)
            self.sharp_delta_2 = DummyParam(0.0)
            self.damp_particle_diameter = DummyParam(0.0)
            self.cutoff_q = DummyParam(1.0)
            self.damp_q = DummyParam(0.0)
            self.broad_q = DummyParam(0.0)

    class DummyLinkedPhases(dict):
        def __getitem__(self, k):
            return type('LP', (), {'scale': DummyParam(1.0)})()

    class DummyExperiment:
        def __init__(self):
            self.name = 'E'
            self.peak = DummyPeak()
            self.data = type('D', (), {'x': np.linspace(0.0, 1.0, 5)})()
            self.type = type('T', (), {'radiation_probe': type('P', (), {'value': 'neutron'})()})()
            self.linked_phases = DummyLinkedPhases()

    class DummySampleModel:
        name = 'PhaseA'

        @property
        def as_cif(self):
            # CIF v2-like tags with dots between letters
            return '_atom.site.label A1\n_cell.length_a 1.0'

    # Monkeypatch PdfFit and parser to avoid real engine usage
    import easydiffraction.analysis.calculators.pdffit as mod

    class FakePdf:
        def add_structure(self, s):
            pass

        def setvar(self, *a, **k):
            pass

        def read_data_lists(self, *a, **k):
            pass

        def calc(self):
            pass

        def getpdf_fit(self):
            return [0.0, 0.0, 0.0, 0.0, 0.0]

    class FakeParser:
        def parse(self, text):
            # Ensure the dot between letters is converted to underscore
            assert '_atom_site_label' in text or '_atom.site.label' not in text
            return object()

    monkeypatch.setattr(mod, 'PdfFit', FakePdf)
    monkeypatch.setattr(mod, 'pdffit_cif_parser', lambda: FakeParser())
    monkeypatch.setattr(mod, 'redirect_stdout', lambda *a, **k: None)
    monkeypatch.setattr(mod, '_pdffit_devnull', None, raising=False)

    calc = PdffitCalculator()
    pattern = calc.calculate_pattern(
        DummySampleModel(), DummyExperiment(), called_by_minimizer=False
    )
    assert isinstance(pattern, np.ndarray) and pattern.shape[0] == 5
