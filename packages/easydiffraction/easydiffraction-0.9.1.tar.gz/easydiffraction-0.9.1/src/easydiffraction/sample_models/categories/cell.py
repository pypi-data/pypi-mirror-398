# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Unit cell parameters category for sample models."""

from typing import Optional

from easydiffraction.core.category import CategoryItem
from easydiffraction.core.parameters import Parameter
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import DataTypes
from easydiffraction.core.validation import RangeValidator
from easydiffraction.crystallography import crystallography as ecr
from easydiffraction.io.cif.handler import CifHandler


class Cell(CategoryItem):
    """Unit cell with lengths a, b, c and angles alpha, beta, gamma."""

    def __init__(
        self,
        *,
        length_a: Optional[int | float] = None,
        length_b: Optional[int | float] = None,
        length_c: Optional[int | float] = None,
        angle_alpha: Optional[int | float] = None,
        angle_beta: Optional[int | float] = None,
        angle_gamma: Optional[int | float] = None,
    ) -> None:
        super().__init__()

        self._length_a: Parameter = Parameter(
            name='length_a',
            description='Length of the a axis of the unit cell.',
            value_spec=AttributeSpec(
                value=length_a,
                type_=DataTypes.NUMERIC,
                default=10.0,
                content_validator=RangeValidator(ge=0, le=1000),
            ),
            units='Å',
            cif_handler=CifHandler(names=['_cell.length_a']),
        )
        self._length_b: Parameter = Parameter(
            name='length_b',
            description='Length of the b axis of the unit cell.',
            value_spec=AttributeSpec(
                value=length_b,
                type_=DataTypes.NUMERIC,
                default=10.0,
                content_validator=RangeValidator(ge=0, le=1000),
            ),
            units='Å',
            cif_handler=CifHandler(names=['_cell.length_b']),
        )
        self._length_c: Parameter = Parameter(
            name='length_c',
            description='Length of the c axis of the unit cell.',
            value_spec=AttributeSpec(
                value=length_c,
                type_=DataTypes.NUMERIC,
                default=10.0,
                content_validator=RangeValidator(ge=0, le=1000),
            ),
            units='Å',
            cif_handler=CifHandler(names=['_cell.length_c']),
        )
        self._angle_alpha: Parameter = Parameter(
            name='angle_alpha',
            description='Angle between edges b and c.',
            value_spec=AttributeSpec(
                value=angle_alpha,
                type_=DataTypes.NUMERIC,
                default=90.0,
                content_validator=RangeValidator(ge=0, le=180),
            ),
            units='deg',
            cif_handler=CifHandler(names=['_cell.angle_alpha']),
        )
        self._angle_beta: Parameter = Parameter(
            name='angle_beta',
            description='Angle between edges a and c.',
            value_spec=AttributeSpec(
                value=angle_beta,
                type_=DataTypes.NUMERIC,
                default=90.0,
                content_validator=RangeValidator(ge=0, le=180),
            ),
            units='deg',
            cif_handler=CifHandler(names=['_cell.angle_beta']),
        )
        self._angle_gamma: Parameter = Parameter(
            name='angle_gamma',
            description='Angle between edges a and b.',
            value_spec=AttributeSpec(
                value=angle_gamma,
                type_=DataTypes.NUMERIC,
                default=90.0,
                content_validator=RangeValidator(ge=0, le=180),
            ),
            units='deg',
            cif_handler=CifHandler(names=['_cell.angle_gamma']),
        )

        self._identity.category_code = 'cell'

    @property
    def length_a(self):
        """Descriptor for a-axis length in Å."""
        return self._length_a

    @length_a.setter
    def length_a(self, value):
        self._length_a.value = value

    @property
    def length_b(self):
        """Descriptor for b-axis length in Å."""
        return self._length_b

    @length_b.setter
    def length_b(self, value):
        self._length_b.value = value

    @property
    def length_c(self):
        """Descriptor for c-axis length in Å."""
        return self._length_c

    @length_c.setter
    def length_c(self, value):
        self._length_c.value = value

    @property
    def angle_alpha(self):
        """Descriptor for angle alpha in degrees."""
        return self._angle_alpha

    @angle_alpha.setter
    def angle_alpha(self, value):
        self._angle_alpha.value = value

    @property
    def angle_beta(self):
        """Descriptor for angle beta in degrees."""
        return self._angle_beta

    @angle_beta.setter
    def angle_beta(self, value):
        self._angle_beta.value = value

    @property
    def angle_gamma(self):
        """Descriptor for angle gamma in degrees."""
        return self._angle_gamma

    @angle_gamma.setter
    def angle_gamma(self, value):
        self._angle_gamma.value = value

    def _apply_cell_symmetry_constraints(self):
        """Apply symmetry constraints to cell parameters."""
        dummy_cell = {
            'lattice_a': self.length_a.value,
            'lattice_b': self.length_b.value,
            'lattice_c': self.length_c.value,
            'angle_alpha': self.angle_alpha.value,
            'angle_beta': self.angle_beta.value,
            'angle_gamma': self.angle_gamma.value,
        }
        space_group_name = self._parent.space_group.name_h_m.value

        ecr.apply_cell_symmetry_constraints(
            cell=dummy_cell,
            name_hm=space_group_name,
        )

        self.length_a.value = dummy_cell['lattice_a']
        self.length_b.value = dummy_cell['lattice_b']
        self.length_c.value = dummy_cell['lattice_c']
        self.angle_alpha.value = dummy_cell['angle_alpha']
        self.angle_beta.value = dummy_cell['angle_beta']
        self.angle_gamma.value = dummy_cell['angle_gamma']

    def _update(self, called_by_minimizer=False):
        """Update cell parameters by applying symmetry constraints."""
        del called_by_minimizer

        self._apply_cell_symmetry_constraints()
