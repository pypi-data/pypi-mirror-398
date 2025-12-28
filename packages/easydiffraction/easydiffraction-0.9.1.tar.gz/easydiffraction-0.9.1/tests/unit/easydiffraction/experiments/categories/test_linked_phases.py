# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

def test_linked_phases_add_and_cif_headers():
    from easydiffraction.experiments.categories.linked_phases import LinkedPhase
    from easydiffraction.experiments.categories.linked_phases import LinkedPhases

    lp = LinkedPhase(id='Si', scale=2.0)
    assert lp.id.value == 'Si' and lp.scale.value == 2.0

    coll = LinkedPhases()
    coll.add(id='Si', scale=2.0)

    # CIF loop header presence
    cif = coll.as_cif
    assert 'loop_' in cif and '_pd_phase_block.id' in cif and '_pd_phase_block.scale' in cif
