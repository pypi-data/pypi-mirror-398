# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

import numpy as np


def test_tof_instrument_defaults_and_setters_and_parameters_and_cif():
    from easydiffraction.experiments.categories.instrument.tof import TofInstrument

    inst = TofInstrument()

    # Defaults
    assert np.isclose(inst.setup_twotheta_bank.value, 150.0)
    assert np.isclose(inst.calib_d_to_tof_offset.value, 0.0)
    assert np.isclose(inst.calib_d_to_tof_linear.value, 10000.0)
    assert np.isclose(inst.calib_d_to_tof_quad.value, -0.00001)
    assert np.isclose(inst.calib_d_to_tof_recip.value, 0.0)

    # Setters
    inst.setup_twotheta_bank = 160.0
    inst.calib_d_to_tof_offset = 1.0
    inst.calib_d_to_tof_linear = 9000.0
    inst.calib_d_to_tof_quad = -2e-5
    inst.calib_d_to_tof_recip = 0.5

    assert np.isclose(inst.setup_twotheta_bank.value, 160.0)
    assert np.isclose(inst.calib_d_to_tof_offset.value, 1.0)
    assert np.isclose(inst.calib_d_to_tof_linear.value, 9000.0)
    assert np.isclose(inst.calib_d_to_tof_quad.value, -2e-5)
    assert np.isclose(inst.calib_d_to_tof_recip.value, 0.5)

    # Parameters exposure via CategoryItem.parameters
    names = {p.name for p in inst.parameters}
    assert {
        'twotheta_bank',
        'd_to_tof_offset',
        'd_to_tof_linear',
        'd_to_tof_quad',
        'd_to_tof_recip',
    }.issubset(names)

    # CIF representation of the item should include tags in separate lines
    cif = inst.as_cif
    assert '_instr.2theta_bank' in cif and '_instr.d_to_tof_linear' in cif
