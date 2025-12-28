# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

import numpy as np
from numpy.testing import assert_array_equal
from pooch import retrieve

import easydiffraction as ed


def test_read_tof_cif_from_scipp() -> None:
    """
    Test reading a CIF file from scipp
    :return: None
    """

    # Retrieve the CIF file
    file_path = retrieve(
        url="https://pub-6c25ef91903d4301a3338bd53b370098.r2.dev/dream_reduced.cif",
        known_hash=None,
    )

    # Add experiment type
    expt_type = {
        '_expt_type.sample_form': 'powder',
        '_expt_type.beam_mode': 'time-of-flight',
        '_expt_type.radiation_probe': 'neutron',
        '_expt_type.scattering_type': 'bragg',
    }
    with open(file_path) as f:
        content = f.read()
    for key, value in expt_type.items():
        if key not in content:
            with open(file_path, "a") as f:
                f.write(f"{key} {value}\n")

    # Create project
    proj = ed.Project()

    # Add experiment from CIF file
    proj.experiments.add(cif_path=file_path)

    # Check the experiment names
    assert proj.experiments.names == ['reduced_tof']

    # Alias for easier access
    experiment = proj.experiments['reduced_tof']

    # Check data size
    assert experiment.data.x.size == 200

    # Check some x data points
    assert_array_equal(
        experiment.data.x[:4],
        np.array([
            57.526660478722604,
            172.57998143616783,
            287.633302393613,
            402.68662335105824,
        ])
    )
    assert_array_equal(
        experiment.data.x[-2:],
        np.array([
            22838.084210052875,
            22953.137531010318,
        ])
    )

    # Check some measured y data points
    #assert experiment.data.meas[93] == 2.0

    # Check some uncertainty data points
    #assert experiment.data.meas_su[93] == 1.4142135623730951
