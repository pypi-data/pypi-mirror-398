# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from abc import abstractmethod

from easydiffraction.core.category import CategoryCollection


class BackgroundBase(CategoryCollection):
    """Abstract base for background subcategories in experiments.

    Concrete implementations provide parameterized background models and
    compute background intensities on the experiment grid.
    """

    # TODO: Consider moving to CategoryCollection
    @abstractmethod
    def show(self) -> None:
        """Print a human-readable view of background components."""
        pass
