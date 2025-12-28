# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Base class for peak profile categories."""

from easydiffraction.core.category import CategoryItem


class PeakBase(CategoryItem):
    """Base class for peak profile categories."""

    def __init__(self) -> None:
        super().__init__()
        self._identity.category_code = 'peak'
