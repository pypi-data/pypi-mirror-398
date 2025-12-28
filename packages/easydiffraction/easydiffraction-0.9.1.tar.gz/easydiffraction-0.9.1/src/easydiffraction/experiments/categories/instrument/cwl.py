# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from easydiffraction.core.parameters import Parameter
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import DataTypes
from easydiffraction.core.validation import RangeValidator
from easydiffraction.experiments.categories.instrument.base import InstrumentBase
from easydiffraction.io.cif.handler import CifHandler


class CwlInstrument(InstrumentBase):
    def __init__(
        self,
        *,
        setup_wavelength=None,
        calib_twotheta_offset=None,
    ) -> None:
        super().__init__()

        self._setup_wavelength: Parameter = Parameter(
            name='wavelength',
            description='Incident neutron or X-ray wavelength',
            value_spec=AttributeSpec(
                value=setup_wavelength,
                type_=DataTypes.NUMERIC,
                default=1.5406,
                content_validator=RangeValidator(),
            ),
            units='Å',
            cif_handler=CifHandler(
                names=[
                    '_instr.wavelength',
                ]
            ),
        )
        self._calib_twotheta_offset: Parameter = Parameter(
            name='twotheta_offset',
            description='Instrument misalignment offset',
            value_spec=AttributeSpec(
                value=calib_twotheta_offset,
                type_=DataTypes.NUMERIC,
                default=0.0,
                content_validator=RangeValidator(),
            ),
            units='deg',
            cif_handler=CifHandler(
                names=[
                    '_instr.2theta_offset',
                ]
            ),
        )

    @property
    def setup_wavelength(self):
        """Incident wavelength parameter (Å)."""
        return self._setup_wavelength

    @setup_wavelength.setter
    def setup_wavelength(self, value):
        """Set incident wavelength value (Å)."""
        self._setup_wavelength.value = value

    @property
    def calib_twotheta_offset(self):
        """Instrument misalignment two-theta offset (deg)."""
        return self._calib_twotheta_offset

    @calib_twotheta_offset.setter
    def calib_twotheta_offset(self, value):
        """Set two-theta offset value (deg)."""
        self._calib_twotheta_offset.value = value
