# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Optional

from easydiffraction.experiments.categories.data.bragg_pd import PdCwlData
from easydiffraction.experiments.categories.data.bragg_pd import PdTofData
from easydiffraction.experiments.categories.data.total import TotalData
from easydiffraction.experiments.experiment.enums import BeamModeEnum
from easydiffraction.experiments.experiment.enums import SampleFormEnum
from easydiffraction.experiments.experiment.enums import ScatteringTypeEnum

if TYPE_CHECKING:
    from easydiffraction.core.category import CategoryCollection


class DataFactory:
    """Factory for creating powder diffraction data collections."""

    _supported = {
        SampleFormEnum.POWDER: {
            ScatteringTypeEnum.BRAGG: {
                BeamModeEnum.CONSTANT_WAVELENGTH: PdCwlData,
                BeamModeEnum.TIME_OF_FLIGHT: PdTofData,
            },
            ScatteringTypeEnum.TOTAL: {
                BeamModeEnum.CONSTANT_WAVELENGTH: TotalData,
                BeamModeEnum.TIME_OF_FLIGHT: TotalData,
            },
        },
    }

    @classmethod
    def create(
        cls,
        *,
        sample_form: Optional[SampleFormEnum] = None,
        beam_mode: Optional[BeamModeEnum] = None,
        scattering_type: Optional[ScatteringTypeEnum] = None,
    ) -> CategoryCollection:
        """Create a data collection for the given configuration."""
        if sample_form is None:
            sample_form = SampleFormEnum.default()
        if beam_mode is None:
            beam_mode = BeamModeEnum.default()
        if scattering_type is None:
            scattering_type = ScatteringTypeEnum.default()

        supported_sample_forms = list(cls._supported.keys())
        if sample_form not in supported_sample_forms:
            raise ValueError(
                f"Unsupported sample form: '{sample_form}'.\n"
                f'Supported sample forms: {supported_sample_forms}'
            )

        supported_scattering_types = list(cls._supported[sample_form].keys())
        if scattering_type not in supported_scattering_types:
            raise ValueError(
                f"Unsupported scattering type: '{scattering_type}' for sample form: "
                f"'{sample_form}'.\n Supported scattering types: '{supported_scattering_types}'"
            )
        supported_beam_modes = list(cls._supported[sample_form][scattering_type].keys())
        if beam_mode not in supported_beam_modes:
            raise ValueError(
                f"Unsupported beam mode: '{beam_mode}' for sample form: "
                f"'{sample_form}' and scattering type '{scattering_type}'.\n"
                f"Supported beam modes: '{supported_beam_modes}'"
            )

        data_class = cls._supported[sample_form][scattering_type][beam_mode]
        data_obj = data_class()

        return data_obj
