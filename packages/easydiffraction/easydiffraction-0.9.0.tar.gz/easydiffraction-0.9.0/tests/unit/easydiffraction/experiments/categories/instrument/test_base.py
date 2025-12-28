# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

def test_instrument_base_sets_category_code():
    from easydiffraction.experiments.categories.instrument.base import InstrumentBase

    class DummyInstr(InstrumentBase):
        def __init__(self):
            super().__init__()

    d = DummyInstr()
    assert d._identity.category_code == 'instrument'
