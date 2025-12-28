# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Background collection entry point (public facade).

End users should import Background classes from this module. Internals
live under the package
`easydiffraction.experiments.category_collections.background_types`
and are re-exported here for a stable and readable API.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Optional

from easydiffraction.experiments.categories.background.enums import BackgroundTypeEnum

if TYPE_CHECKING:
    from easydiffraction.experiments.categories.background import BackgroundBase


class BackgroundFactory:
    """Create background collections by type."""

    BT = BackgroundTypeEnum

    @classmethod
    def _supported_map(cls) -> dict:
        """Return mapping of enum values to concrete background
        classes.
        """
        # Lazy import to avoid circulars
        from easydiffraction.experiments.categories.background.chebyshev import (
            ChebyshevPolynomialBackground,
        )
        from easydiffraction.experiments.categories.background.line_segment import (
            LineSegmentBackground,
        )

        return {
            cls.BT.LINE_SEGMENT: LineSegmentBackground,
            cls.BT.CHEBYSHEV: ChebyshevPolynomialBackground,
        }

    @classmethod
    def create(
        cls,
        background_type: Optional[BackgroundTypeEnum] = None,
    ) -> BackgroundBase:
        """Instantiate a background collection of requested type.

        If type is None, the default enum value is used.
        """
        if background_type is None:
            background_type = BackgroundTypeEnum.default()

        supported = cls._supported_map()
        if background_type not in supported:
            supported_types = list(supported.keys())
            raise ValueError(
                f"Unsupported background type: '{background_type}'. "
                f'Supported background types: {[bt.value for bt in supported_types]}'
            )

        background_class = supported[background_type]
        return background_class()
