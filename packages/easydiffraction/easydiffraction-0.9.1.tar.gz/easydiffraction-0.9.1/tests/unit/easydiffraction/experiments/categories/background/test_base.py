# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

import numpy as np


def test_background_base_minimal_impl_and_collection_cif():
    from easydiffraction.core.category import CategoryItem
    from easydiffraction.core.collection import CollectionBase
    from easydiffraction.core.parameters import Parameter
    from easydiffraction.core.validation import AttributeSpec
    from easydiffraction.core.validation import DataTypes
    from easydiffraction.experiments.categories.background.base import BackgroundBase
    from easydiffraction.io.cif.handler import CifHandler

    class ConstantBackground(CategoryItem):
        def __init__(self, name: str, value: float):
            # CategoryItem doesn't define __init__; call GuardedBase via super()
            super().__init__()
            self._identity.category_code = 'background'
            self._identity.category_entry_name = name
            self._level = Parameter(
                name='level',
                value_spec=AttributeSpec(value=value, type_=DataTypes.NUMERIC, default=0.0),
                cif_handler=CifHandler(names=['_bkg.level']),
            )

        def calculate(self, x_data):
            return np.full_like(np.asarray(x_data), fill_value=self._level.value, dtype=float)

        def show(self):
            # No-op for tests
            return None

    class BackgroundCollection(BackgroundBase):
        def __init__(self):
            # Initialize underlying collection with the item type
            CollectionBase.__init__(self, item_type=ConstantBackground)

        def calculate(self, x_data):
            x = np.asarray(x_data)
            total = np.zeros_like(x, dtype=float)
            for item in self.values():
                total += item.calculate(x)
            return total

        def show(self) -> None:  # pragma: no cover - trivial
            return None

    coll = BackgroundCollection()
    a = ConstantBackground('a', 1.0)
    coll.add('a', 1.0)
    coll.add('b', 2.0)

    # calculate sums two backgrounds externally (out of scope), here just verify item.calculate
    x = np.array([0.0, 1.0, 2.0])
    assert np.allclose(a.calculate(x), [1.0, 1.0, 1.0])

    # CIF of collection is loop with header tag and two rows
    cif = coll.as_cif
    assert 'loop_' in cif and '_bkg.level' in cif and '1.0' in cif and '2.0' in cif
