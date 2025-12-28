# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Minimal CIF tag handler used by descriptors/parameters."""

from __future__ import annotations


class CifHandler:
    """Canonical CIF handler used by descriptors/parameters.

    Holds CIF tags (names) and attaches to an owning descriptor so it
    can derive a stable uid if needed.
    """

    def __init__(self, *, names: list[str]) -> None:
        self._names = names
        self._owner = None  # set by attach

    def attach(self, owner):
        """Attach to a descriptor or parameter instance."""
        self._owner = owner

    @property
    def names(self) -> list[str]:
        """List of CIF tag names associated with the owner."""
        return self._names

    @property
    def uid(self) -> str | None:
        """Unique identifier taken from the owner, if attached."""
        if self._owner is None:
            return None
        return self._owner.unique_name
