# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

import numpy as np


def test_excluded_regions_add_updates_datastore_and_cif():
    from types import SimpleNamespace

    from easydiffraction.experiments.categories.excluded_regions import ExcludedRegions

    # Minimal fake datastore
    full_x = np.array([0.0, 1.0, 2.0, 3.0])
    full_meas = np.array([10.0, 11.0, 12.0, 13.0])
    full_meas_su = np.array([1.0, 1.0, 1.0, 1.0])
    ds = SimpleNamespace(
        all_x=full_x,  # ExcludedRegions._update uses all_x not full_x
        full_x=full_x,
        full_meas=full_meas,
        full_meas_su=full_meas_su,
        excluded=np.zeros_like(full_x, dtype=bool),
        x=full_x.copy(),
        meas=full_meas.copy(),
        meas_su=full_meas_su.copy(),
    )
    
    def set_calc_status(status):
        # _set_calc_status sets excluded to the inverse
        ds.excluded = ~status
        # Filter x, meas, meas_su to only include non-excluded points
        ds.x = ds.full_x[status]
        ds.meas = ds.full_meas[status]
        ds.meas_su = ds.full_meas_su[status]
    
    ds._set_calc_status = set_calc_status

    coll = ExcludedRegions()
    # stitch in a parent with data
    object.__setattr__(coll, '_parent', SimpleNamespace(data=ds))

    coll.add(start=1.0, end=2.0)
    # Call _update() to apply exclusions
    coll._update()

    # Second and third points excluded
    assert np.array_equal(ds.excluded, np.array([False, True, True, False]))
    assert np.array_equal(ds.x, np.array([0.0, 3.0]))
    assert np.array_equal(ds.meas, np.array([10.0, 13.0]))

    # CIF loop includes header tags
    cif = coll.as_cif
    assert 'loop_' in cif and '_excluded_region.start' in cif and '_excluded_region.end' in cif
