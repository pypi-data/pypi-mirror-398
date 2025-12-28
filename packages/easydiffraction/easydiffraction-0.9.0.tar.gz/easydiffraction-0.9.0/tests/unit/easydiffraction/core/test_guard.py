# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

import pytest


def test_guard_allows_only_declared_public_properties_and_links_parent(monkeypatch):
    from easydiffraction.core.guard import GuardedBase

    class Child(GuardedBase):
        @property
        def parameters(self):
            return []

        @property
        def as_cif(self) -> str:
            return ''

        @property
        def value(self):
            return getattr(self, '_value', 0)

        @value.setter
        def value(self, v):
            self._assign_attr('_value', v)

    class Parent(GuardedBase):
        def __init__(self):
            super().__init__()
            self._child = Child()

        @property
        def child(self):
            return self._child

        @property
        def parameters(self):
            return []

        @property
        def as_cif(self) -> str:
            return ''

    p = Parent()
    # Writable property on child should set and link parent
    p.child.value = 3
    assert p.child.value == 3
    # Private assign links parent automatically
    assert p.child._parent is p

    # Unknown attribute should raise AttributeError under current logging mode
    with pytest.raises(AttributeError):
        p.child.unknown_attr = 1
