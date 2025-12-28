# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Enumerations for background model types."""

from __future__ import annotations

from enum import Enum


# TODO: Consider making EnumBase class with: default, description, ...
class BackgroundTypeEnum(str, Enum):
    """Supported background model types."""

    LINE_SEGMENT = 'line-segment'
    CHEBYSHEV = 'chebyshev polynomial'

    @classmethod
    def default(cls) -> 'BackgroundTypeEnum':
        """Return a default background type."""
        return cls.LINE_SEGMENT

    def description(self) -> str:
        """Human-friendly description for the enum value."""
        if self is BackgroundTypeEnum.LINE_SEGMENT:
            return 'Linear interpolation between points'
        elif self is BackgroundTypeEnum.CHEBYSHEV:
            return 'Chebyshev polynomial background'
