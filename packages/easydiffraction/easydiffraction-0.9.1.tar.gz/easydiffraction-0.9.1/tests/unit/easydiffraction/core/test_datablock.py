# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

def test_datablock_collection_add_and_filters_with_real_parameters():
    from easydiffraction.core.category import CategoryItem
    from easydiffraction.core.datablock import DatablockCollection
    from easydiffraction.core.datablock import DatablockItem
    from easydiffraction.core.parameters import Parameter
    from easydiffraction.core.validation import AttributeSpec
    from easydiffraction.core.validation import DataTypes
    from easydiffraction.io.cif.handler import CifHandler

    class Cat(CategoryItem):
        def __init__(self):
            super().__init__()
            self._identity.category_code = 'cat'
            self._identity.category_entry_name = 'e1'
            # real Parameters
            self._p1 = Parameter(
                name='p1',
                description='',
                value_spec=AttributeSpec(value=1.0, type_=DataTypes.NUMERIC, default=0.0),
                units='',
                cif_handler=CifHandler(names=['_cat.p1']),
            )
            self._p2 = Parameter(
                name='p2',
                description='',
                value_spec=AttributeSpec(value=2.0, type_=DataTypes.NUMERIC, default=0.0),
                units='',
                cif_handler=CifHandler(names=['_cat.p2']),
            )
            # Make p2 constrained and not free
            self._p2._constrained = True
            self._p2._free = False
            # Mark p1 free to be included in free_parameters
            self._p1.free = True

        @property
        def p1(self):
            return self._p1

        @property
        def p2(self):
            return self._p2

    class Block(DatablockItem):
        def __init__(self, name):
            super().__init__()
            # set datablock entry name
            self._identity.datablock_entry_name = lambda: name
            # include the category as attribute so DatablockItem.parameters picks them up
            self._cat = Cat()

        @property
        def cat(self):
            return self._cat

    coll = DatablockCollection(item_type=Block)
    a = Block('A')
    b = Block('B')
    coll._add(a)
    coll._add(b)
    # parameters collection aggregates from both blocks (p1 & p2 each)
    params = coll.parameters
    assert len(params) == 4
    # fittable excludes constrained parameters
    fittable = coll.fittable_parameters
    assert all(isinstance(p, Parameter) for p in fittable)
    assert len(fittable) == 2  # only p1 from each block
    # free is subset of fittable where free=True (true for p1)
    free_params = coll.free_parameters
    assert free_params == fittable
