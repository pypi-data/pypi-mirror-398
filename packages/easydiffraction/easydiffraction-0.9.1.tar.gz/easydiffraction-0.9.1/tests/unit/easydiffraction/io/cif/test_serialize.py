# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

def test_module_import():
    import easydiffraction.io.cif.serialize as MUT

    expected_module_name = 'easydiffraction.io.cif.serialize'
    actual_module_name = MUT.__name__
    assert expected_module_name == actual_module_name


def test_format_value_quotes_whitespace_strings():
    import easydiffraction.io.cif.serialize as MUT

    assert MUT.format_value('a b') == '   "a b"'
    assert MUT.format_value('ab') == '      ab'


def test_param_to_cif_minimal():
    import easydiffraction.io.cif.serialize as MUT
    from easydiffraction.io.cif.handler import CifHandler

    class P:
        def __init__(self):
            self._cif_handler = CifHandler(names=['_x.y'])  # noqa: SLF001 for tests
            self.value = 3

    p = P()
    assert MUT.param_to_cif(p) == '_x.y   3.0000'


def test_category_collection_to_cif_empty_and_one_row():
    import easydiffraction.io.cif.serialize as MUT
    from easydiffraction.core.category import CategoryCollection
    from easydiffraction.core.category import CategoryItem
    from easydiffraction.io.cif.handler import CifHandler

    class Item(CategoryItem):
        def __init__(self, name, value):
            super().__init__()
            self._identity.category_entry_name = name
            self._p = type('P', (), {})()
            self._p._cif_handler = CifHandler(names=['_x'])  # noqa: SLF001
            self._p.value = value

        @property
        def parameters(self):
            return [self._p]

        @property
        def as_cif(self) -> str:
            return MUT.category_item_to_cif(self)

    coll = CategoryCollection(item_type=Item)
    assert MUT.category_collection_to_cif(coll) == ''
    i = Item('n1', 5)
    coll['n1'] = i
    out = MUT.category_collection_to_cif(coll)
    assert 'loop_' in out and '_x' in out and '5' in out


def test_project_to_cif_assembles_present_sections():
    import easydiffraction.io.cif.serialize as MUT

    class Obj:
        def __init__(self, text):
            self._text = text

        @property
        def as_cif(self):
            return self._text

    class Project:
        def __init__(self):
            self.info = Obj('I')
            self.sample_models = None
            self.experiments = Obj('E')
            self.analysis = None
            self.summary = None

    p = Project()
    out = MUT.project_to_cif(p)
    assert out == 'I\n\nE'
