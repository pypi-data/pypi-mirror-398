# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

def test_cif_handler_names_and_uid():
    import easydiffraction.io.cif.handler as H

    names = ['_cell.length_a', '_cell.length_b']
    h = H.CifHandler(names=names)
    assert h.names == names
    assert h.uid is None

    class Owner:
        unique_name = 'db.cat.entry.param'

    h.attach(Owner())
    assert h.uid == 'db.cat.entry.param'
