# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from easydiffraction.analysis.categories.constraints import Constraint
from easydiffraction.analysis.categories.constraints import Constraints


def test_constraint_creation_and_collection():
    c = Constraint(lhs_alias='a', rhs_expr='b + c')
    assert c.lhs_alias.value == 'a'
    coll = Constraints()
    coll.add(lhs_alias='a', rhs_expr='b + c')
    assert 'a' in coll.names
    assert coll['a'].rhs_expr.value == 'b + c'
