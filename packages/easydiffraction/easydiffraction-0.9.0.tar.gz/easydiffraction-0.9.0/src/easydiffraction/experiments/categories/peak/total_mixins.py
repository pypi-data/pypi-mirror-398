# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Total scattering/PDF peak-profile mixins.

Adds damping, broadening, sharpening and envelope parameters used in
pair distribution function (PDF) modeling.
"""

from easydiffraction.core.parameters import Parameter
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import DataTypes
from easydiffraction.core.validation import RangeValidator
from easydiffraction.io.cif.handler import CifHandler


class TotalBroadeningMixin:
    """Mixin adding PDF broadening/damping/sharpening parameters."""

    def _add_pair_distribution_function_broadening(self):
        """Create PDF parameters: damp_q, broad_q, cutoff_q,
        sharp deltas, and particle diameter envelope.
        """
        self._damp_q: Parameter = Parameter(
            name='damp_q',
            description='Instrumental Q-resolution damping factor '
            '(affects high-r PDF peak amplitude)',
            value_spec=AttributeSpec(
                value=0.05,
                type_=DataTypes.NUMERIC,
                default=0.05,
                content_validator=RangeValidator(),
            ),
            units='Å⁻¹',
            cif_handler=CifHandler(
                names=[
                    '_peak.damp_q',
                ]
            ),
        )
        self._broad_q: Parameter = Parameter(
            name='broad_q',
            description='Quadratic PDF peak broadening coefficient '
            '(thermal and model uncertainty contribution)',
            value_spec=AttributeSpec(
                value=0.0,
                type_=DataTypes.NUMERIC,
                default=0.0,
                content_validator=RangeValidator(),
            ),
            units='Å⁻²',
            cif_handler=CifHandler(
                names=[
                    '_peak.broad_q',
                ]
            ),
        )
        self._cutoff_q: Parameter = Parameter(
            name='cutoff_q',
            description='Q-value cutoff applied to model PDF for Fourier '
            'transform (controls real-space resolution)',
            value_spec=AttributeSpec(
                value=25.0,
                type_=DataTypes.NUMERIC,
                default=25.0,
                content_validator=RangeValidator(),
            ),
            units='Å⁻¹',
            cif_handler=CifHandler(
                names=[
                    '_peak.cutoff_q',
                ]
            ),
        )
        self._sharp_delta_1: Parameter = Parameter(
            name='sharp_delta_1',
            description='PDF peak sharpening coefficient (1/r dependence)',
            value_spec=AttributeSpec(
                value=0.0,
                type_=DataTypes.NUMERIC,
                default=0.0,
                content_validator=RangeValidator(),
            ),
            units='Å',
            cif_handler=CifHandler(
                names=[
                    '_peak.sharp_delta_1',
                ]
            ),
        )
        self._sharp_delta_2: Parameter = Parameter(
            name='sharp_delta_2',
            description='PDF peak sharpening coefficient (1/r² dependence)',
            value_spec=AttributeSpec(
                value=0.0,
                type_=DataTypes.NUMERIC,
                default=0.0,
                content_validator=RangeValidator(),
            ),
            units='Å²',
            cif_handler=CifHandler(
                names=[
                    '_peak.sharp_delta_2',
                ]
            ),
        )
        self._damp_particle_diameter: Parameter = Parameter(
            name='damp_particle_diameter',
            description='Particle diameter for spherical envelope damping correction in PDF',
            value_spec=AttributeSpec(
                value=0.0,
                type_=DataTypes.NUMERIC,
                default=0.0,
                content_validator=RangeValidator(),
            ),
            units='Å',
            cif_handler=CifHandler(
                names=[
                    '_peak.damp_particle_diameter',
                ]
            ),
        )

    @property
    def damp_q(self) -> Parameter:
        """Get Q-resolution damping factor."""
        return self._damp_q

    @damp_q.setter
    def damp_q(self, value: float) -> None:
        """Set Q-resolution damping factor."""
        self._damp_q.value = value

    @property
    def broad_q(self) -> Parameter:
        """Get quadratic PDF broadening coefficient."""
        return self._broad_q

    @broad_q.setter
    def broad_q(self, value: float) -> None:
        """Set quadratic PDF broadening coefficient."""
        self._broad_q.value = value

    @property
    def cutoff_q(self) -> Parameter:
        """Get Q cutoff used for Fourier transform."""
        return self._cutoff_q

    @cutoff_q.setter
    def cutoff_q(self, value: float) -> None:
        """Set Q cutoff used for Fourier transform."""
        self._cutoff_q.value = value

    @property
    def sharp_delta_1(self) -> Parameter:
        """Get sharpening coefficient with 1/r dependence."""
        return self._sharp_delta_1

    @sharp_delta_1.setter
    def sharp_delta_1(self, value: float) -> None:
        """Set sharpening coefficient with 1/r dependence."""
        self._sharp_delta_1.value = value

    @property
    def sharp_delta_2(self) -> Parameter:
        """Get sharpening coefficient with 1/r^2 dependence."""
        return self._sharp_delta_2

    @sharp_delta_2.setter
    def sharp_delta_2(self, value: float) -> None:
        """Set sharpening coefficient with 1/r^2 dependence."""
        self._sharp_delta_2.value = value

    @property
    def damp_particle_diameter(self) -> Parameter:
        """Get particle diameter for spherical envelope damping."""
        return self._damp_particle_diameter

    @damp_particle_diameter.setter
    def damp_particle_diameter(self, value: float) -> None:
        """Set particle diameter for spherical envelope damping."""
        self._damp_particle_diameter.value = value
