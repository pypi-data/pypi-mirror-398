# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Chebyshev polynomial background model.

Provides a collection of polynomial terms and evaluation helpers.
"""

from __future__ import annotations

from typing import List
from typing import Union

import numpy as np
from numpy.polynomial.chebyshev import chebval

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


class PolynomialTerm(CategoryItem):
    """Chebyshev polynomial term.

    New public attribute names: ``order`` and ``coef`` replacing the
    longer ``chebyshev_order`` / ``chebyshev_coef``. Backward-compatible
    aliases are kept so existing serialized data / external code does
    not break immediately. Tests should migrate to the short names.
    """

    def __init__(
        self,
        *,
        id=None,  # TODO: rename as in the case of data points?
        order=None,
        coef=None,
    ) -> None:
        super().__init__()

        self._id = StringDescriptor(
            name='id',
            description='Identifier for this background polynomial term.',
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
        self._order = NumericDescriptor(
            name='order',
            description='Order used in a Chebyshev polynomial background term',
            value_spec=AttributeSpec(
                value=order,
                type_=DataTypes.NUMERIC,
                default=0.0,
                content_validator=RangeValidator(),
            ),
            cif_handler=CifHandler(
                names=[
                    '_pd_background.Chebyshev_order',
                ]
            ),
        )
        self._coef = Parameter(
            name='coef',
            description='Coefficient used in a Chebyshev polynomial background term',
            value_spec=AttributeSpec(
                value=coef,
                type_=DataTypes.NUMERIC,
                default=0.0,
                content_validator=RangeValidator(),
            ),
            cif_handler=CifHandler(
                names=[
                    '_pd_background.Chebyshev_coef',
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
    def order(self):
        return self._order

    @order.setter
    def order(self, value):
        self._order.value = value

    @property
    def coef(self):
        return self._coef

    @coef.setter
    def coef(self, value):
        self._coef.value = value


class ChebyshevPolynomialBackground(BackgroundBase):
    _description: str = 'Chebyshev polynomial background'

    def __init__(self):
        super().__init__(item_type=PolynomialTerm)

    def _update(self, called_by_minimizer=False):
        """Evaluate polynomial background over x data."""
        del called_by_minimizer

        data = self._parent.data
        x = data.x

        if not self._items:
            log.warning('No background points found. Setting background to zero.')
            data._set_bkg(np.zeros_like(x))
            return

        u = (x - x.min()) / (x.max() - x.min()) * 2 - 1
        coefs = [term.coef.value for term in self._items]

        y = chebval(u, coefs)
        data._set_bkg(y)

    def show(self) -> None:
        """Print a table of polynomial orders and coefficients."""
        columns_headers: List[str] = ['Order', 'Coefficient']
        columns_alignment = ['left', 'left']
        columns_data: List[List[Union[int, float]]] = [
            [t.order.value, t.coef.value] for t in self._items
        ]

        console.paragraph('Chebyshev polynomial background terms')
        render_table(
            columns_headers=columns_headers,
            columns_alignment=columns_alignment,
            columns_data=columns_data,
        )
