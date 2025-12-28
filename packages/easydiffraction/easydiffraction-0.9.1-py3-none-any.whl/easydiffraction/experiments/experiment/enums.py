# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Enumerations for experiment configuration (forms, modes, types)."""

from enum import Enum


class SampleFormEnum(str, Enum):
    """Physical sample form supported by experiments."""

    POWDER = 'powder'
    SINGLE_CRYSTAL = 'single crystal'

    @classmethod
    def default(cls) -> 'SampleFormEnum':
        return cls.POWDER

    def description(self) -> str:
        if self is SampleFormEnum.POWDER:
            return 'Powdered or polycrystalline sample.'
        elif self is SampleFormEnum.SINGLE_CRYSTAL:
            return 'Single crystal sample.'


class ScatteringTypeEnum(str, Enum):
    """Type of scattering modeled in an experiment."""

    BRAGG = 'bragg'
    TOTAL = 'total'

    @classmethod
    def default(cls) -> 'ScatteringTypeEnum':
        return cls.BRAGG

    def description(self) -> str:
        if self is ScatteringTypeEnum.BRAGG:
            return 'Bragg diffraction for conventional structure refinement.'
        elif self is ScatteringTypeEnum.TOTAL:
            return 'Total scattering for pair distribution function analysis (PDF).'


class RadiationProbeEnum(str, Enum):
    """Incident radiation probe used in the experiment."""

    NEUTRON = 'neutron'
    XRAY = 'xray'

    @classmethod
    def default(cls) -> 'RadiationProbeEnum':
        return cls.NEUTRON

    def description(self) -> str:
        if self is RadiationProbeEnum.NEUTRON:
            return 'Neutron diffraction.'
        elif self is RadiationProbeEnum.XRAY:
            return 'X-ray diffraction.'


class BeamModeEnum(str, Enum):
    """Beam delivery mode for the instrument."""

    # TODO: Rename to CWL and TOF
    CONSTANT_WAVELENGTH = 'constant wavelength'
    TIME_OF_FLIGHT = 'time-of-flight'

    @classmethod
    def default(cls) -> 'BeamModeEnum':
        return cls.CONSTANT_WAVELENGTH

    def description(self) -> str:
        if self is BeamModeEnum.CONSTANT_WAVELENGTH:
            return 'Constant wavelength (CW) diffraction.'
        elif self is BeamModeEnum.TIME_OF_FLIGHT:
            return 'Time-of-flight (TOF) diffraction.'


class PeakProfileTypeEnum(str, Enum):
    """Available peak profile types per scattering and beam mode."""

    PSEUDO_VOIGT = 'pseudo-voigt'
    SPLIT_PSEUDO_VOIGT = 'split pseudo-voigt'
    THOMPSON_COX_HASTINGS = 'thompson-cox-hastings'
    PSEUDO_VOIGT_IKEDA_CARPENTER = 'pseudo-voigt * ikeda-carpenter'
    PSEUDO_VOIGT_BACK_TO_BACK = 'pseudo-voigt * back-to-back'
    GAUSSIAN_DAMPED_SINC = 'gaussian-damped-sinc'

    @classmethod
    def default(
        cls,
        scattering_type: ScatteringTypeEnum | None = None,
        beam_mode: BeamModeEnum | None = None,
    ) -> 'PeakProfileTypeEnum':
        if scattering_type is None:
            scattering_type = ScatteringTypeEnum.default()
        if beam_mode is None:
            beam_mode = BeamModeEnum.default()
        return {
            (ScatteringTypeEnum.BRAGG, BeamModeEnum.CONSTANT_WAVELENGTH): cls.PSEUDO_VOIGT,
            (
                ScatteringTypeEnum.BRAGG,
                BeamModeEnum.TIME_OF_FLIGHT,
            ): cls.PSEUDO_VOIGT_IKEDA_CARPENTER,
            (ScatteringTypeEnum.TOTAL, BeamModeEnum.CONSTANT_WAVELENGTH): cls.GAUSSIAN_DAMPED_SINC,
            (ScatteringTypeEnum.TOTAL, BeamModeEnum.TIME_OF_FLIGHT): cls.GAUSSIAN_DAMPED_SINC,
        }[(scattering_type, beam_mode)]

    def description(self) -> str:
        if self is PeakProfileTypeEnum.PSEUDO_VOIGT:
            return 'Pseudo-Voigt profile'
        elif self is PeakProfileTypeEnum.SPLIT_PSEUDO_VOIGT:
            return 'Split pseudo-Voigt profile with empirical asymmetry correction.'
        elif self is PeakProfileTypeEnum.THOMPSON_COX_HASTINGS:
            return 'Thompson-Cox-Hastings profile with FCJ asymmetry correction.'
        elif self is PeakProfileTypeEnum.PSEUDO_VOIGT_IKEDA_CARPENTER:
            return 'Pseudo-Voigt profile with Ikeda-Carpenter asymmetry correction.'
        elif self is PeakProfileTypeEnum.PSEUDO_VOIGT_BACK_TO_BACK:
            return 'Pseudo-Voigt profile with Back-to-Back Exponential asymmetry correction.'
        elif self is PeakProfileTypeEnum.GAUSSIAN_DAMPED_SINC:
            return 'Gaussian-damped sinc profile for pair distribution function (PDF) analysis.'
