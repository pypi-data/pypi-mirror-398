# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Factory for instrument category items.

Provides a stable entry point for creating instrument objects from the
experiment's scattering type and beam mode.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Optional
from typing import Type

from easydiffraction.experiments.experiment.enums import BeamModeEnum
from easydiffraction.experiments.experiment.enums import ScatteringTypeEnum

if TYPE_CHECKING:
    from easydiffraction.experiments.categories.instrument.base import InstrumentBase


class InstrumentFactory:
    """Create instrument instances for supported modes.

    The factory hides implementation details and lazy-loads concrete
    instrument classes to avoid circular imports.
    """

    ST = ScatteringTypeEnum
    BM = BeamModeEnum

    @classmethod
    def _supported_map(cls) -> dict:
        # Lazy import to avoid circulars
        from easydiffraction.experiments.categories.instrument.cwl import CwlInstrument
        from easydiffraction.experiments.categories.instrument.tof import TofInstrument

        return {
            cls.ST.BRAGG: {
                cls.BM.CONSTANT_WAVELENGTH: CwlInstrument,
                cls.BM.TIME_OF_FLIGHT: TofInstrument,
            }
        }

    @classmethod
    def create(
        cls,
        scattering_type: Optional[ScatteringTypeEnum] = None,
        beam_mode: Optional[BeamModeEnum] = None,
    ) -> InstrumentBase:
        if beam_mode is None:
            beam_mode = BeamModeEnum.default()
        if scattering_type is None:
            scattering_type = ScatteringTypeEnum.default()

        supported = cls._supported_map()

        supported_scattering_types = list(supported.keys())
        if scattering_type not in supported_scattering_types:
            raise ValueError(
                f"Unsupported scattering type: '{scattering_type}'.\n "
                f'Supported scattering types: {supported_scattering_types}'
            )

        supported_beam_modes = list(supported[scattering_type].keys())
        if beam_mode not in supported_beam_modes:
            raise ValueError(
                f"Unsupported beam mode: '{beam_mode}' for scattering type: "
                f"'{scattering_type}'.\n "
                f'Supported beam modes: {supported_beam_modes}'
            )

        instrument_class: Type[InstrumentBase] = supported[scattering_type][beam_mode]
        return instrument_class()
