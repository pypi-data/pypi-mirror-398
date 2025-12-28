# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from easydiffraction.core.category import CategoryCollection
from easydiffraction.core.category import CategoryItem
from easydiffraction.core.parameters import StringDescriptor
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import DataTypes
from easydiffraction.io.cif.handler import CifHandler


class SimpleItem(CategoryItem):
    def __init__(self, entry_name):
        super().__init__()
        self._identity.category_code = 'simple'
        self._identity.category_entry_name = entry_name
        object.__setattr__(
            self,
            '_a',
            StringDescriptor(
                name='a',
                description='',
                value_spec=AttributeSpec(value='x', type_=DataTypes.STRING, default=''),
                cif_handler=CifHandler(names=['_simple.a']),
            ),
        )
        object.__setattr__(
            self,
            '_b',
            StringDescriptor(
                name='b',
                description='',
                value_spec=AttributeSpec(value='y', type_=DataTypes.STRING, default=''),
                cif_handler=CifHandler(names=['_simple.b']),
            ),
        )

    @property
    def a(self):
        return self._a

    @property
    def b(self):
        return self._b


class SimpleCollection(CategoryCollection):
    def __init__(self):
        super().__init__(item_type=SimpleItem)


def test_category_item_str_and_properties():
    it = SimpleItem('name1')
    s = str(it)
    assert '<' in s and 'a=' in s and 'b=' in s
    assert it.unique_name.endswith('.simple.name1') or it.unique_name == 'simple.name1'
    assert len(it.parameters) == 2


def test_category_collection_str_and_cif_calls():
    c = SimpleCollection()
    c.add('n1')
    c.add('n2')
    s = str(c)
    assert 'collection' in s and '2 items' in s
    # as_cif delegates to serializer; should be a string (possibly empty)
    assert isinstance(c.as_cif, str)
