# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

import numpy as np
import pytest


def test_datablock_item_to_cif_includes_item_and_collection():
    import easydiffraction.io.cif.serialize as MUT
    from easydiffraction.core.category import CategoryCollection
    from easydiffraction.core.category import CategoryItem
    from easydiffraction.io.cif.handler import CifHandler

    class Item(CategoryItem):
        def __init__(self, val):
            super().__init__()
            self._p = type('P', (), {})()
            self._p._cif_handler = CifHandler(names=['_aa'])  # noqa: SLF001
            self._p.value = val

        @property
        def parameters(self):
            return [self._p]

        @property
        def as_cif(self) -> str:
            return MUT.category_item_to_cif(self)

    class DB:
        def __init__(self):
            self._identity = type('I', (), {'datablock_entry_name': 'block1'})()
            # one CategoryItem-like
            self.item = Item(42)
            # one CategoryCollection-like
            self.coll = CategoryCollection(item_type=Item)
            self.coll['row1'] = Item(7)

    out = MUT.datablock_item_to_cif(DB())
    assert out.startswith('data_block1')
    assert '_aa  42.0000' in out
    assert 'loop_' in out and '_aa' in out and '7' in out


def test_datablock_collection_to_cif_concatenates_blocks():
    import easydiffraction.io.cif.serialize as MUT

    class B:
        def __init__(self, t):
            self._t = t

        @property
        def as_cif(self):
            return self._t

    coll = {'a': B('A'), 'b': B('B')}
    out = MUT.datablock_collection_to_cif(coll)
    assert out == 'A\n\nB'


def test_project_info_to_cif_contains_core_fields():
    import easydiffraction.io.cif.serialize as MUT
    from easydiffraction.project.project_info import ProjectInfo

    info = ProjectInfo(name='p1', title='My Title', description='Some description text')
    out = MUT.project_info_to_cif(info)
    assert '_project.id               p1' in out
    assert '_project.title' in out and 'My Title' in out
    assert '_project.description' in out
    assert '_project.created' in out and '_project.last_modified' in out


def test_experiment_to_cif_with_and_without_data():
    import easydiffraction.io.cif.serialize as MUT

    class DS:
        def __init__(self, text):
            self._text = text

        @property
        def as_cif(self):
            return self._text

    class Exp:
        def __init__(self, data_text):
            self._identity = type('I', (), {'datablock_entry_name': 'expA'})()
            self.datastore = DS(data_text)
            # Minimal CategoryItem to be picked up by datablock_item_to_cif
            from easydiffraction.core.category import CategoryItem
            from easydiffraction.io.cif.handler import CifHandler

            class Item(CategoryItem):
                def __init__(self):
                    super().__init__()
                    self._p = type('P', (), {})()
                    self._p._cif_handler = CifHandler(names=['_k'])  # noqa: SLF001
                    self._p.value = 1

                @property
                def parameters(self):
                    return [self._p]

                @property
                def as_cif(self):
                    return MUT.category_item_to_cif(self)

            self.item = Item()

    out_with = MUT.experiment_to_cif(Exp('loop_\\n_x\\n1'))
    # Datastore CIF no longer automatically included in experiment CIF output
    assert out_with.startswith('data_expA')
    # Check that item CIF is included
    assert '_k' in out_with and '1' in out_with

    out_without = MUT.experiment_to_cif(Exp(''))
    assert out_without.startswith('data_expA') and out_without.endswith('1.0000')


def test_analysis_to_cif_renders_all_sections():
    import easydiffraction.io.cif.serialize as MUT

    class Obj:
        def __init__(self, t):
            self._t = t

        @property
        def as_cif(self):
            return self._t

    class A:
        current_calculator = 'cryspy engine'
        current_minimizer = 'lmfit (leastsq)'
        fit_mode = 'single'
        aliases = Obj('ALIASES')
        constraints = Obj('CONSTRAINTS')

    out = MUT.analysis_to_cif(A())
    lines = out.splitlines()
    assert lines[0].startswith('_analysis.calculator_engine')
    assert '"cryspy engine"' in lines[0]
    assert lines[1].startswith('_analysis.fitting_engine') and '"lmfit (leastsq)"' in lines[1]
    assert lines[2].startswith('_analysis.fit_mode') and 'single' in lines[2]
    assert 'ALIASES' in out and 'CONSTRAINTS' in out
