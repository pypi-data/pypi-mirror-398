# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from typing import Optional

from easydiffraction.experiments.experiment.enums import BeamModeEnum
from easydiffraction.experiments.experiment.enums import PeakProfileTypeEnum
from easydiffraction.experiments.experiment.enums import ScatteringTypeEnum


# TODO: Consider inheriting from FactoryBase
class PeakFactory:
    """Factory for creating peak profile objects.

    Lazily imports implementations to avoid circular dependencies and
    selects the appropriate class based on scattering type, beam mode
    and requested profile type.
    """

    ST = ScatteringTypeEnum
    BM = BeamModeEnum
    PPT = PeakProfileTypeEnum
    _supported = None  # type: ignore[var-annotated]

    @classmethod
    def _supported_map(cls):
        """Return nested mapping of supported profile classes.

        Structure:
            ``{ScatteringType: {BeamMode: {ProfileType: Class}}}``.
        """
        # Lazy import to avoid circular imports between
        # base and cw/tof/pdf modules
        if cls._supported is None:
            from easydiffraction.experiments.categories.peak.cwl import CwlPseudoVoigt as CwPv
            from easydiffraction.experiments.categories.peak.cwl import (
                CwlSplitPseudoVoigt as CwSpv,
            )
            from easydiffraction.experiments.categories.peak.cwl import (
                CwlThompsonCoxHastings as CwTch,
            )
            from easydiffraction.experiments.categories.peak.tof import TofPseudoVoigt as TofPv
            from easydiffraction.experiments.categories.peak.tof import (
                TofPseudoVoigtBackToBack as TofBtb,
            )
            from easydiffraction.experiments.categories.peak.tof import (
                TofPseudoVoigtIkedaCarpenter as TofIc,
            )
            from easydiffraction.experiments.categories.peak.total import (
                TotalGaussianDampedSinc as PdfGds,
            )

            cls._supported = {
                cls.ST.BRAGG: {
                    cls.BM.CONSTANT_WAVELENGTH: {
                        cls.PPT.PSEUDO_VOIGT: CwPv,
                        cls.PPT.SPLIT_PSEUDO_VOIGT: CwSpv,
                        cls.PPT.THOMPSON_COX_HASTINGS: CwTch,
                    },
                    cls.BM.TIME_OF_FLIGHT: {
                        cls.PPT.PSEUDO_VOIGT: TofPv,
                        cls.PPT.PSEUDO_VOIGT_IKEDA_CARPENTER: TofIc,
                        cls.PPT.PSEUDO_VOIGT_BACK_TO_BACK: TofBtb,
                    },
                },
                cls.ST.TOTAL: {
                    cls.BM.CONSTANT_WAVELENGTH: {
                        cls.PPT.GAUSSIAN_DAMPED_SINC: PdfGds,
                    },
                    cls.BM.TIME_OF_FLIGHT: {
                        cls.PPT.GAUSSIAN_DAMPED_SINC: PdfGds,
                    },
                },
            }
        return cls._supported

    @classmethod
    def create(
        cls,
        scattering_type: Optional[ScatteringTypeEnum] = None,
        beam_mode: Optional[BeamModeEnum] = None,
        profile_type: Optional[PeakProfileTypeEnum] = None,
    ):
        """Instantiate a peak profile for the given configuration.

        Args:
            scattering_type: Bragg or Total. Defaults to library
                default.
            beam_mode: CW or TOF. Defaults to library default.
            profile_type: Concrete profile within the mode. If omitted,
                a sensible default is chosen based on the other args.

        Returns:
            A newly created peak profile object.

        Raises:
            ValueError: If a requested option is not supported.
        """
        if beam_mode is None:
            beam_mode = BeamModeEnum.default()
        if scattering_type is None:
            scattering_type = ScatteringTypeEnum.default()
        if profile_type is None:
            profile_type = PeakProfileTypeEnum.default(scattering_type, beam_mode)
        supported = cls._supported_map()
        supported_scattering_types = list(supported.keys())
        if scattering_type not in supported_scattering_types:
            raise ValueError(
                f"Unsupported scattering type: '{scattering_type}'.\n"
                f'Supported scattering types: {supported_scattering_types}'
            )

        supported_beam_modes = list(supported[scattering_type].keys())
        if beam_mode not in supported_beam_modes:
            raise ValueError(
                f"Unsupported beam mode: '{beam_mode}' for scattering type: "
                f"'{scattering_type}'.\n Supported beam modes: '{supported_beam_modes}'"
            )

        supported_profile_types = list(supported[scattering_type][beam_mode].keys())
        if profile_type not in supported_profile_types:
            raise ValueError(
                f"Unsupported profile type '{profile_type}' for beam mode '{beam_mode}'.\n"
                f'Supported profile types: {supported_profile_types}'
            )

        peak_class = supported[scattering_type][beam_mode][profile_type]
        peak_obj = peak_class()

        return peak_obj
