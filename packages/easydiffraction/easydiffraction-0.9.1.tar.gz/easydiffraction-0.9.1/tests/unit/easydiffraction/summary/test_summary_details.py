# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

def test_summary_crystallographic_and_experimental_sections(capsys):
    from easydiffraction.summary.summary import Summary

    # Build a minimal sample model stub that exposes required attributes
    class Val:
        def __init__(self, v):
            self.value = v

    class CellParam:
        def __init__(self, name, value):
            self.name = name
            self.value = value

    class Model:
        def __init__(self):
            self.name = 'phaseA'
            self.space_group = type('SG', (), {'name_h_m': Val('P 1')})()

            class Cell:
                @property
                def parameters(self_inner):
                    return [
                        CellParam('length_a', 5.4321),
                        CellParam('angle_alpha', 90.0),
                    ]

            self.cell = Cell()

            class Site:
                def __init__(self, label, typ, x, y, z, occ, biso):
                    self.label = Val(label)
                    self.type_symbol = Val(typ)
                    self.fract_x = Val(x)
                    self.fract_y = Val(y)
                    self.fract_z = Val(z)
                    self.occupancy = Val(occ)
                    self.b_iso = Val(biso)

            self.atom_sites = [Site('Na1', 'Na', 0.1, 0.2, 0.3, 1.0, 0.5)]

    # Minimal experiment stub with instrument and peak info
    class Expt:
        def __init__(self):
            self.name = 'exp1'
            typ = type(
                'T',
                (),
                {
                    'sample_form': Val('powder'),
                    'radiation_probe': Val('neutron'),
                    'beam_mode': Val('constant wavelength'),
                },
            )
            self.type = typ()

            class Instr:
                def __init__(self):
                    self.setup_wavelength = Val(1.23456)
                    self.calib_twotheta_offset = Val(0.12345)

                def _public_attrs(self):
                    return ['setup_wavelength', 'calib_twotheta_offset']

            self.instrument = Instr()
            self.peak_profile_type = 'pseudo-Voigt'

            class Peak:
                def __init__(self):
                    self.broad_gauss_u = Val(0.1)
                    self.broad_gauss_v = Val(0.2)
                    self.broad_gauss_w = Val(0.3)
                    self.broad_lorentz_x = Val(0.4)
                    self.broad_lorentz_y = Val(0.5)

                def _public_attrs(self):
                    return [
                        'broad_gauss_u',
                        'broad_gauss_v',
                        'broad_gauss_w',
                        'broad_lorentz_x',
                        'broad_lorentz_y',
                    ]

            self.peak = Peak()

        def _public_attrs(self):
            return ['instrument', 'peak_profile_type', 'peak']

    class Info:
        title = 'T'
        description = ''

    class Project:
        def __init__(self):
            self.info = Info()
            self.sample_models = {'phaseA': Model()}
            self.experiments = {'exp1': Expt()}

            class A:
                current_calculator = 'cryspy'
                current_minimizer = 'lmfit'

                class R:
                    reduced_chi_square = 1.23

                fit_results = R()

            self.analysis = A()

    s = Summary(Project())
    # Run both sections separately for targeted assertions
    s.show_crystallographic_data()
    s.show_experimental_data()
    out = capsys.readouterr().out

    # Crystallographic section
    assert 'CRYSTALLOGRAPHIC DATA' in out
    assert '🧩 phaseA' in out
    assert 'Space group' in out and 'P 1' in out
    # Cell parameter names are shortened by the implementation (e.g., 'length_a' -> 'a')
    assert 'Cell parameters' in out and ' a ' in out and ' alpha ' in out
    assert 'Atom sites' in out and 'Na1' in out and 'Na' in out

    # Experimental section
    assert 'EXPERIMENTS' in out
    assert '🔬 exp1' in out
    assert 'powder' in out and 'neutron' in out and 'constant wavelength' in out
    assert 'Wavelength' in out and '1.23456'[:6] in out
    assert '2θ offset' in out and '0.12345'[:6] in out
    assert 'Profile type' in out and 'pseudo-Voigt' in out
    assert 'Peak broadening (Gaussian)' in out
    assert 'Peak broadening (Lorentzian)' in out
