# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Line-segment background model.

Interpolate user-specified points to form a background curve.
"""

from __future__ import annotations

from typing import List

import numpy as np
from scipy.interpolate import interp1d

from easydiffraction.core.category import CategoryItem
from easydiffraction.core.parameters import NumericDescriptor
from easydiffraction.core.parameters import Parameter
from easydiffraction.core.parameters import StringDescriptor
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import DataTypes
from easydiffraction.core.validation import RangeValidator
from easydiffraction.core.validation import RegexValidator
from easydiffraction.experiments.categories.background.base import BackgroundBase
from easydiffraction.io.cif.handler import CifHandler
from easydiffraction.utils.logging import console
from easydiffraction.utils.logging import log
from easydiffraction.utils.utils import render_table


class LineSegment(CategoryItem):
    """Single background control point for interpolation."""

    def __init__(
        self,
        *,
        id=None,  # TODO: rename as in the case of data points?
        x=None,
        y=None,
    ) -> None:
        super().__init__()

        self._id = StringDescriptor(
            name='id',
            description='Identifier for this background line segment.',
            value_spec=AttributeSpec(
                type_=DataTypes.STRING,
                value=id,
                default='0',
                # TODO: the following pattern is valid for dict key
                #  (keywords are not checked). CIF label is less strict.
                #  Do we need conversion between CIF and internal label?
                content_validator=RegexValidator(pattern=r'^[A-Za-z0-9_]*$'),
            ),
            cif_handler=CifHandler(
                names=[
                    '_pd_background.id',
                ]
            ),
        )
        self._x = NumericDescriptor(
            name='x',
            description=(
                'X-coordinates used to create many straight-line segments '
                'representing the background in a calculated diffractogram.'
            ),
            value_spec=AttributeSpec(
                value=x,
                type_=DataTypes.NUMERIC,
                default=0.0,
                content_validator=RangeValidator(),
            ),
            cif_handler=CifHandler(
                names=[
                    '_pd_background.line_segment_X',
                    '_pd_background_line_segment_X',
                ]
            ),
        )
        self._y = Parameter(
            name='y',  # TODO: rename to intensity
            description=(
                'Intensity used to create many straight-line segments '
                'representing the background in a calculated diffractogram'
            ),
            value_spec=AttributeSpec(
                value=y,
                type_=DataTypes.NUMERIC,
                default=0.0,
                content_validator=RangeValidator(),
            ),  # TODO: rename to intensity
            cif_handler=CifHandler(
                names=[
                    '_pd_background.line_segment_intensity',
                    '_pd_background_line_segment_intensity',
                ]
            ),
        )

        self._identity.category_code = 'background'
        self._identity.category_entry_name = lambda: str(self._id.value)

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        self._id.value = value

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, value):
        self._x.value = value

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, value):
        self._y.value = value


class LineSegmentBackground(BackgroundBase):
    _description: str = 'Linear interpolation between points'

    def __init__(self):
        super().__init__(item_type=LineSegment)

    def _update(self, called_by_minimizer=False):
        """Interpolate background points over x data."""
        del called_by_minimizer

        data = self._parent.data
        x = data.x

        if not self._items:
            log.debug('No background points found. Setting background to zero.')
            data._set_bkg(np.zeros_like(x))
            return

        segments_x = np.array([point.x.value for point in self._items])
        segments_y = np.array([point.y.value for point in self._items])
        interp_func = interp1d(
            segments_x,
            segments_y,
            kind='linear',
            bounds_error=False,
            fill_value=(segments_y[0], segments_y[-1]),
        )

        y = interp_func(x)
        data._set_bkg(y)

    def show(self) -> None:
        """Print a table of control points (x, intensity)."""
        columns_headers: List[str] = ['X', 'Intensity']
        columns_alignment = ['left', 'left']
        columns_data: List[List[float]] = [[p.x.value, p.y.value] for p in self._items]

        console.paragraph('Line-segment background points')
        render_table(
            columns_headers=columns_headers,
            columns_alignment=columns_alignment,
            columns_data=columns_data,
        )
