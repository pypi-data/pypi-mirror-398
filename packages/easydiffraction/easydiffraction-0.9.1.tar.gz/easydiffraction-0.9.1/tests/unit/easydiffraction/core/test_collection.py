# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

def test_collection_add_get_delete_and_names():
    from easydiffraction.core.collection import CollectionBase
    from easydiffraction.core.identity import Identity

    class Item:
        def __init__(self, name):
            self._identity = Identity(owner=self, category_entry=lambda: name)

    class MyCollection(CollectionBase):
        @property
        def parameters(self):
            return []

        @property
        def as_cif(self) -> str:
            return ''

    c = MyCollection(item_type=Item)
    a = Item('a')
    b = Item('b')
    c['a'] = a
    c['b'] = b
    assert c['a'] is a and c['b'] is b
    a2 = Item('a')
    c['a'] = a2
    assert c['a'] is a2 and len(list(c.keys())) == 2
    del c['b']
    assert list(c.names) == ['a']
