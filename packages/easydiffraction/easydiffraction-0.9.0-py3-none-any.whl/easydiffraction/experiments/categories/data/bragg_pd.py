# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import numpy as np

from easydiffraction.core.category import CategoryCollection
from easydiffraction.core.category import CategoryItem
from easydiffraction.core.parameters import NumericDescriptor
from easydiffraction.core.parameters import StringDescriptor
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import DataTypes
from easydiffraction.core.validation import MembershipValidator
from easydiffraction.core.validation import RangeValidator
from easydiffraction.core.validation import RegexValidator
from easydiffraction.io.cif.handler import CifHandler
from easydiffraction.utils.utils import tof_to_d
from easydiffraction.utils.utils import twotheta_to_d


class PdDataPointBaseMixin:
    """Single base data point mixin for powder diffraction data."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._point_id = StringDescriptor(
            name='point_id',
            description='Identifier for this data point in the dataset.',
            value_spec=AttributeSpec(
                type_=DataTypes.STRING,
                default='0',
                # TODO: the following pattern is valid for dict key
                #  (keywords are not checked). CIF label is less strict.
                #  Do we need conversion between CIF and internal label?
                content_validator=RegexValidator(pattern=r'^[A-Za-z0-9_]*$'),
            ),
            cif_handler=CifHandler(
                names=[
                    '_pd_data.point_id',
                ]
            ),
        )
        self._d_spacing = NumericDescriptor(
            name='d_spacing',
            description='d-spacing value corresponding to this data point.',
            value_spec=AttributeSpec(
                type_=DataTypes.NUMERIC,
                default=0.0,
                content_validator=RangeValidator(ge=0),
            ),
            cif_handler=CifHandler(
                names=[
                    '_pd_proc.d_spacing',
                ]
            ),
        )
        self._intensity_meas = NumericDescriptor(
            name='intensity_meas',
            description='Intensity recorded at each measurement point as a function of angle/time',
            value_spec=AttributeSpec(
                type_=DataTypes.NUMERIC,
                default=0.0,
                content_validator=RangeValidator(ge=0),
            ),
            cif_handler=CifHandler(
                names=[
                    '_pd_meas.intensity_total',
                    '_pd_proc.intensity_norm',
                ]
            ),
        )
        self._intensity_meas_su = NumericDescriptor(
            name='intensity_meas_su',
            description='Standard uncertainty of the measured intensity at this data point.',
            value_spec=AttributeSpec(
                type_=DataTypes.NUMERIC,
                default=0.0,
                content_validator=RangeValidator(ge=0),
            ),
            cif_handler=CifHandler(
                names=[
                    '_pd_meas.intensity_total_su',
                    '_pd_proc.intensity_norm_su',
                ]
            ),
        )
        self._intensity_calc = NumericDescriptor(
            name='intensity_calc',
            description='Intensity value for a computed diffractogram at this data point.',
            value_spec=AttributeSpec(
                type_=DataTypes.NUMERIC,
                default=0.0,
                content_validator=RangeValidator(ge=0),
            ),
            cif_handler=CifHandler(
                names=[
                    '_pd_calc.intensity_total',
                ]
            ),
        )
        self._intensity_bkg = NumericDescriptor(
            name='intensity_bkg',
            description='Intensity value for a computed background at this data point.',
            value_spec=AttributeSpec(
                type_=DataTypes.NUMERIC,
                default=0.0,
                content_validator=RangeValidator(ge=0),
            ),
            cif_handler=CifHandler(
                names=[
                    '_pd_calc.intensity_bkg',
                ]
            ),
        )
        self._calc_status = StringDescriptor(
            name='calc_status',
            description='Status code of the data point in the calculation process.',
            value_spec=AttributeSpec(
                type_=DataTypes.STRING,
                default='incl',  # TODO: Make Enum
                content_validator=MembershipValidator(allowed=['incl', 'excl']),
            ),
            cif_handler=CifHandler(
                names=[
                    '_pd_data.refinement_status',  # TODO: rename to calc_status
                ]
            ),
        )

    @property
    def point_id(self) -> StringDescriptor:
        return self._point_id

    @property
    def d_spacing(self) -> NumericDescriptor:
        return self._d_spacing

    @property
    def intensity_meas(self) -> NumericDescriptor:
        return self._intensity_meas

    @property
    def intensity_meas_su(self) -> NumericDescriptor:
        return self._intensity_meas_su

    @property
    def intensity_calc(self) -> NumericDescriptor:
        return self._intensity_calc

    @property
    def intensity_bkg(self) -> NumericDescriptor:
        return self._intensity_bkg

    @property
    def calc_status(self) -> StringDescriptor:
        return self._calc_status


class PdCwlDataPointMixin:
    """Mixin for powder diffraction data points with constant
    wavelength.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._two_theta = NumericDescriptor(
            name='two_theta',
            description='Measured 2θ diffraction angle.',
            value_spec=AttributeSpec(
                type_=DataTypes.NUMERIC,
                default=0.0,
                content_validator=RangeValidator(ge=0, le=180),
            ),
            units='deg',
            cif_handler=CifHandler(
                names=[
                    '_pd_proc.2theta_scan',
                    '_pd_meas.2theta_scan',
                ]
            ),
        )

    @property
    def two_theta(self) -> NumericDescriptor:
        return self._two_theta


class PdTofDataPointMixin:
    """Mixin for powder diffraction data points with time-of-flight."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._time_of_flight = NumericDescriptor(
            name='time_of_flight',
            description='Measured time for time-of-flight neutron measurement.',
            value_spec=AttributeSpec(
                type_=DataTypes.NUMERIC,
                default=0.0,
                content_validator=RangeValidator(ge=0),
            ),
            units='µs',
            cif_handler=CifHandler(
                names=[
                    '_pd_meas.time_of_flight',
                ]
            ),
        )

    @property
    def time_of_flight(self) -> NumericDescriptor:
        return self._time_of_flight


class PdCwlDataPoint(
    PdDataPointBaseMixin,
    PdCwlDataPointMixin,
    CategoryItem,  # Must be last to ensure mixins initialized first
):
    """Powder diffraction data point for constant-wavelength
    experiments.
    """

    def __init__(self) -> None:
        super().__init__()
        self._identity.category_code = 'pd_data'
        self._identity.category_entry_name = lambda: str(self.point_id.value)


class PdTofDataPoint(
    PdDataPointBaseMixin,
    PdTofDataPointMixin,
    CategoryItem,  # Must be last to ensure mixins initialized first
):
    """Powder diffraction data point for time-of-flight experiments."""

    def __init__(self) -> None:
        super().__init__()
        self._identity.category_code = 'pd_data'
        self._identity.category_entry_name = lambda: str(self.point_id.value)


class PdDataBase(CategoryCollection):
    # TODO: ???

    # Redefine update priority to ensure data updated after other
    # categories. Higher number = runs later. Default for other
    # categories, e.g., background and excluded regions are 10 by
    # default
    _update_priority = 100

    # Should be set only once

    def _set_point_id(self, values) -> None:
        """Helper method to set point IDs."""
        for p, v in zip(self._items, values, strict=True):
            p.point_id._value = v

    def _set_meas(self, values) -> None:
        """Helper method to set measured intensity."""
        for p, v in zip(self._items, values, strict=True):
            p.intensity_meas._value = v

    def _set_meas_su(self, values) -> None:
        """Helper method to set standard uncertainty of measured
        intensity.
        """
        for p, v in zip(self._items, values, strict=True):
            p.intensity_meas_su._value = v

    # Can be set multiple times

    def _set_d_spacing(self, values) -> None:
        """Helper method to set d-spacing values."""
        for p, v in zip(self._calc_items, values, strict=True):
            p.d_spacing._value = v

    def _set_calc(self, values) -> None:
        """Helper method to set calculated intensity."""
        for p, v in zip(self._calc_items, values, strict=True):
            p.intensity_calc._value = v

    def _set_bkg(self, values) -> None:
        """Helper method to set background intensity."""
        for p, v in zip(self._calc_items, values, strict=True):
            p.intensity_bkg._value = v

    def _set_calc_status(self, values) -> None:
        """Helper method to set refinement status."""
        for p, v in zip(self._items, values, strict=True):
            if v:
                p.calc_status._value = 'incl'
            elif not v:
                p.calc_status._value = 'excl'
            else:
                raise ValueError(
                    f'Invalid refinement status value: {v}. Expected boolean True/False.'
                )

    @property
    def _calc_mask(self) -> np.ndarray:
        return self.calc_status == 'incl'

    @property
    def _calc_items(self):
        """Get only the items included in calculations."""
        return [item for item, mask in zip(self._items, self._calc_mask, strict=False) if mask]

    @property
    def calc_status(self) -> np.ndarray:
        return np.fromiter((p.calc_status.value for p in self._items), dtype=object)

    @property
    def d(self) -> np.ndarray:
        return np.fromiter((p.d_spacing.value for p in self._calc_items), dtype=float)

    @property
    def meas(self) -> np.ndarray:
        return np.fromiter((p.intensity_meas.value for p in self._calc_items), dtype=float)

    @property
    def meas_su(self) -> np.ndarray:
        return np.fromiter((p.intensity_meas_su.value for p in self._calc_items), dtype=float)

    @property
    def calc(self) -> np.ndarray:
        return np.fromiter((p.intensity_calc.value for p in self._calc_items), dtype=float)

    @property
    def bkg(self) -> np.ndarray:
        return np.fromiter((p.intensity_bkg.value for p in self._calc_items), dtype=float)

    def _update(self, called_by_minimizer=False):
        experiment = self._parent
        experiments = experiment._parent
        project = experiments._parent
        sample_models = project.sample_models
        # calculator = experiment.calculator  # TODO: move from analysis
        calculator = project.analysis.calculator

        initial_calc = np.zeros_like(self.x)
        calc = initial_calc
        for linked_phase in experiment._get_valid_linked_phases(sample_models):
            sample_model_id = linked_phase._identity.category_entry_name
            sample_model_scale = linked_phase.scale.value
            sample_model = sample_models[sample_model_id]

            sample_model_calc = calculator.calculate_pattern(
                sample_model,
                experiment,
                called_by_minimizer=called_by_minimizer,
            )

            sample_model_scaled_calc = sample_model_scale * sample_model_calc
            calc += sample_model_scaled_calc

        self._set_calc(calc + self.bkg)


class PdCwlData(PdDataBase):
    # TODO: ???
    # _description: str = 'Powder diffraction data points for
    # constant-wavelength experiments.'

    def __init__(self):
        super().__init__(item_type=PdCwlDataPoint)

    # Should be set only once

    def _set_x(self, values) -> None:
        """Helper method to set 2θ values."""
        # TODO: split into multiple methods
        self._items = [self._item_type() for _ in range(values.size)]
        for p, v in zip(self._items, values, strict=True):
            p.two_theta._value = v
        self._set_point_id([str(i + 1) for i in range(values.size)])

    @property
    def all_x(self) -> np.ndarray:
        """Get the 2θ values for all data points in this collection."""
        return np.fromiter((p.two_theta.value for p in self._items), dtype=float)

    @property
    def x(self) -> np.ndarray:
        """Get the 2θ values for data points included in
        calculations.
        """
        return np.fromiter((p.two_theta.value for p in self._calc_items), dtype=float)

    def _update(self, called_by_minimizer=False):
        super()._update(called_by_minimizer)

        experiment = self._parent
        d_spacing = twotheta_to_d(
            self.x,
            experiment.instrument.setup_wavelength.value,
        )
        self._set_d_spacing(d_spacing)


class PdTofData(PdDataBase):
    # TODO: ???
    # _description: str = 'Powder diffraction data points for
    # time-of-flight experiments.'

    def __init__(self):
        super().__init__(item_type=PdTofDataPoint)

    def _set_x(self, values) -> None:
        """Helper method to set time-of-flight values."""
        # TODO: split into multiple methods
        self._items = [self._item_type() for _ in range(values.size)]
        for p, v in zip(self._items, values, strict=True):
            p.time_of_flight._value = v
        self._set_point_id([str(i + 1) for i in range(values.size)])

    @property
    def all_x(self) -> np.ndarray:
        """Get the TOF values for all data points in this collection."""
        return np.fromiter((p.time_of_flight.value for p in self._items), dtype=float)

    @property
    def x(self) -> np.ndarray:
        """Get the TOF values for data points included in
        calculations.
        """
        return np.fromiter((p.time_of_flight.value for p in self._calc_items), dtype=float)

    def _update(self, called_by_minimizer=False):
        super()._update(called_by_minimizer)

        experiment = self._parent
        d_spacing = tof_to_d(
            self.x,
            experiment.instrument.calib_d_to_tof_offset.value,
            experiment.instrument.calib_d_to_tof_linear.value,
            experiment.instrument.calib_d_to_tof_quad.value,
        )
        self._set_d_spacing(d_spacing)
