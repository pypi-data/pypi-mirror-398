# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Time-of-flight (TOF) peak-profile mixins.

Defines mixins that add Gaussian/Lorentz broadening, mixing, and
Ikeda–Carpenter asymmetry parameters used by TOF peak shapes.
"""

from easydiffraction.core.parameters import Parameter
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import DataTypes
from easydiffraction.core.validation import RangeValidator
from easydiffraction.io.cif.handler import CifHandler


class TofBroadeningMixin:
    """Mixin that adds TOF Gaussian/Lorentz broadening and mixing
    terms.
    """

    def _add_time_of_flight_broadening(self) -> None:
        """Create TOF broadening and mixing parameters."""
        self._broad_gauss_sigma_0: Parameter = Parameter(
            name='gauss_sigma_0',
            description='Gaussian broadening coefficient (instrumental resolution)',
            value_spec=AttributeSpec(
                value=0.0,
                type_=DataTypes.NUMERIC,
                default=0.0,
                content_validator=RangeValidator(),
            ),
            units='µs²',
            cif_handler=CifHandler(
                names=[
                    '_peak.gauss_sigma_0',
                ]
            ),
        )
        self._broad_gauss_sigma_1: Parameter = Parameter(
            name='gauss_sigma_1',
            description='Gaussian broadening coefficient (dependent on d-spacing)',
            value_spec=AttributeSpec(
                value=0.0,
                type_=DataTypes.NUMERIC,
                default=0.0,
                content_validator=RangeValidator(),
            ),
            units='µs/Å',
            cif_handler=CifHandler(
                names=[
                    '_peak.gauss_sigma_1',
                ]
            ),
        )
        self._broad_gauss_sigma_2: Parameter = Parameter(
            name='gauss_sigma_2',
            description='Gaussian broadening coefficient (instrument-dependent term)',
            value_spec=AttributeSpec(
                value=0.0,
                type_=DataTypes.NUMERIC,
                default=0.0,
                content_validator=RangeValidator(),
            ),
            units='µs²/Å²',
            cif_handler=CifHandler(
                names=[
                    '_peak.gauss_sigma_2',
                ]
            ),
        )
        self._broad_lorentz_gamma_0: Parameter = Parameter(
            name='lorentz_gamma_0',
            description='Lorentzian broadening coefficient (dependent on microstrain effects)',
            value_spec=AttributeSpec(
                value=0.0,
                type_=DataTypes.NUMERIC,
                default=0.0,
                content_validator=RangeValidator(),
            ),
            units='µs',
            cif_handler=CifHandler(
                names=[
                    '_peak.lorentz_gamma_0',
                ]
            ),
        )
        self._broad_lorentz_gamma_1: Parameter = Parameter(
            name='lorentz_gamma_1',
            description='Lorentzian broadening coefficient (dependent on d-spacing)',
            value_spec=AttributeSpec(
                value=0.0,
                type_=DataTypes.NUMERIC,
                default=0.0,
                content_validator=RangeValidator(),
            ),
            units='µs/Å',
            cif_handler=CifHandler(
                names=[
                    '_peak.lorentz_gamma_1',
                ]
            ),
        )
        self._broad_lorentz_gamma_2: Parameter = Parameter(
            name='lorentz_gamma_2',
            description='Lorentzian broadening coefficient (instrument-dependent term)',
            value_spec=AttributeSpec(
                value=0.0,
                type_=DataTypes.NUMERIC,
                default=0.0,
                content_validator=RangeValidator(),
            ),
            units='µs²/Å²',
            cif_handler=CifHandler(
                names=[
                    '_peak.lorentz_gamma_2',
                ]
            ),
        )
        self._broad_mix_beta_0: Parameter = Parameter(
            name='mix_beta_0',
            description='Mixing parameter. Defines the ratio of Gaussian '
            'to Lorentzian contributions in TOF profiles',
            value_spec=AttributeSpec(
                value=0.0,
                type_=DataTypes.NUMERIC,
                default=0.0,
                content_validator=RangeValidator(),
            ),
            units='deg',
            cif_handler=CifHandler(
                names=[
                    '_peak.mix_beta_0',
                ]
            ),
        )
        self._broad_mix_beta_1: Parameter = Parameter(
            name='mix_beta_1',
            description='Mixing parameter. Defines the ratio of Gaussian '
            'to Lorentzian contributions in TOF profiles',
            value_spec=AttributeSpec(
                value=0.0,
                type_=DataTypes.NUMERIC,
                default=0.0,
                content_validator=RangeValidator(),
            ),
            units='deg',
            cif_handler=CifHandler(
                names=[
                    '_peak.mix_beta_1',
                ]
            ),
        )

    @property
    def broad_gauss_sigma_0(self) -> Parameter:
        """Get Gaussian sigma_0 parameter."""
        return self._broad_gauss_sigma_0

    @broad_gauss_sigma_0.setter
    def broad_gauss_sigma_0(self, value: float) -> None:
        """Set Gaussian sigma_0 parameter."""
        self._broad_gauss_sigma_0.value = value

    @property
    def broad_gauss_sigma_1(self) -> Parameter:
        """Get Gaussian sigma_1 parameter."""
        return self._broad_gauss_sigma_1

    @broad_gauss_sigma_1.setter
    def broad_gauss_sigma_1(self, value: float) -> None:
        """Set Gaussian sigma_1 parameter."""
        self._broad_gauss_sigma_1.value = value

    @property
    def broad_gauss_sigma_2(self) -> Parameter:
        """Get Gaussian sigma_2 parameter."""
        return self._broad_gauss_sigma_2

    @broad_gauss_sigma_2.setter
    def broad_gauss_sigma_2(self, value: float) -> None:
        """Set Gaussian sigma_2 parameter."""
        self._broad_gauss_sigma_2.value = value

    @property
    def broad_lorentz_gamma_0(self) -> Parameter:
        """Get Lorentz gamma_0 parameter."""
        return self._broad_lorentz_gamma_0

    @broad_lorentz_gamma_0.setter
    def broad_lorentz_gamma_0(self, value: float) -> None:
        """Set Lorentz gamma_0 parameter."""
        self._broad_lorentz_gamma_0.value = value

    @property
    def broad_lorentz_gamma_1(self) -> Parameter:
        """Get Lorentz gamma_1 parameter."""
        return self._broad_lorentz_gamma_1

    @broad_lorentz_gamma_1.setter
    def broad_lorentz_gamma_1(self, value: float) -> None:
        """Set Lorentz gamma_1 parameter."""
        self._broad_lorentz_gamma_1.value = value

    @property
    def broad_lorentz_gamma_2(self) -> Parameter:
        """Get Lorentz gamma_2 parameter."""
        return self._broad_lorentz_gamma_2

    @broad_lorentz_gamma_2.setter
    def broad_lorentz_gamma_2(self, value: float) -> None:
        """Set Lorentz gamma_2 parameter."""
        self._broad_lorentz_gamma_2.value = value

    @property
    def broad_mix_beta_0(self) -> Parameter:
        """Get mixing parameter beta_0."""
        return self._broad_mix_beta_0

    @broad_mix_beta_0.setter
    def broad_mix_beta_0(self, value: float) -> None:
        """Set mixing parameter beta_0."""
        self._broad_mix_beta_0.value = value

    @property
    def broad_mix_beta_1(self) -> Parameter:
        """Get mixing parameter beta_1."""
        return self._broad_mix_beta_1

    @broad_mix_beta_1.setter
    def broad_mix_beta_1(self, value: float) -> None:
        """Set mixing parameter beta_1."""
        self._broad_mix_beta_1.value = value


class IkedaCarpenterAsymmetryMixin:
    """Mixin that adds Ikeda–Carpenter asymmetry parameters."""

    def _add_ikeda_carpenter_asymmetry(self) -> None:
        """Create Ikeda–Carpenter asymmetry parameters alpha_0 and
        alpha_1.
        """
        self._asym_alpha_0: Parameter = Parameter(
            name='asym_alpha_0',
            description='Ikeda-Carpenter asymmetry parameter α₀',
            value_spec=AttributeSpec(
                value=0.01,
                type_=DataTypes.NUMERIC,
                default=0.01,
                content_validator=RangeValidator(),
            ),
            units='',
            cif_handler=CifHandler(
                names=[
                    '_peak.asym_alpha_0',
                ]
            ),
        )
        self._asym_alpha_1: Parameter = Parameter(
            name='asym_alpha_1',
            description='Ikeda-Carpenter asymmetry parameter α₁',
            value_spec=AttributeSpec(
                value=0.02,
                type_=DataTypes.NUMERIC,
                default=0.02,
                content_validator=RangeValidator(),
            ),
            units='',
            cif_handler=CifHandler(
                names=[
                    '_peak.asym_alpha_1',
                ]
            ),
        )

    @property
    def asym_alpha_0(self) -> Parameter:
        """Get Ikeda–Carpenter asymmetry alpha_0."""
        return self._asym_alpha_0

    @asym_alpha_0.setter
    def asym_alpha_0(self, value: float) -> None:
        """Set Ikeda–Carpenter asymmetry alpha_0."""
        self._asym_alpha_0.value = value

    @property
    def asym_alpha_1(self) -> Parameter:
        """Get Ikeda–Carpenter asymmetry alpha_1."""
        return self._asym_alpha_1

    @asym_alpha_1.setter
    def asym_alpha_1(self, value: float) -> None:
        """Set Ikeda–Carpenter asymmetry alpha_1."""
        self._asym_alpha_1.value = value
