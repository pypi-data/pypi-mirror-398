# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

def test_identity_direct_and_parent_resolution():
    from easydiffraction.core.identity import Identity

    class Node:
        def __init__(self, name=None, parent=None):
            self._identity = Identity(owner=self, category_code=name)
            if parent is not None:
                self._parent = parent

    parent = Node(name='cat')
    child = Node(parent=parent)
    assert parent._identity.category_code == 'cat'
    assert child._identity.category_code == 'cat'


def test_identity_cycle_safe_resolution():
    from easydiffraction.core.identity import Identity

    class Node:
        def __init__(self):
            self._identity = Identity(owner=self)

    a = Node()
    b = Node()
    a._parent = b
    b._parent = a
    assert a._identity.category_code is None
