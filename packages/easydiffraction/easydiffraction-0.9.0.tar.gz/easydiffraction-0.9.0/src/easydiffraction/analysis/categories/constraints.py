# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Simple symbolic constraint between parameters.

Represents an equation of the form ``lhs_alias = rhs_expr`` where
``rhs_expr`` is evaluated elsewhere by the analysis engine.
"""

from easydiffraction.core.category import CategoryCollection
from easydiffraction.core.category import CategoryItem
from easydiffraction.core.parameters import StringDescriptor
from easydiffraction.core.singletons import ConstraintsHandler
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import DataTypes
from easydiffraction.core.validation import RegexValidator
from easydiffraction.io.cif.handler import CifHandler


class Constraint(CategoryItem):
    """Single constraint item.

    Args:
        lhs_alias: Left-hand side alias name being constrained.
        rhs_expr: Right-hand side expression as a string.
    """

    def __init__(
        self,
        *,
        lhs_alias: str,
        rhs_expr: str,
    ) -> None:
        super().__init__()

        self._lhs_alias: StringDescriptor = StringDescriptor(
            name='lhs_alias',
            description='...',
            value_spec=AttributeSpec(
                value=lhs_alias,
                type_=DataTypes.STRING,
                default='...',
                content_validator=RegexValidator(pattern=r'.*'),
            ),
            cif_handler=CifHandler(
                names=[
                    '_constraint.lhs_alias',
                ]
            ),
        )
        self._rhs_expr: StringDescriptor = StringDescriptor(
            name='rhs_expr',
            description='...',
            value_spec=AttributeSpec(
                value=rhs_expr,
                type_=DataTypes.STRING,
                default='...',
                content_validator=RegexValidator(pattern=r'.*'),
            ),
            cif_handler=CifHandler(
                names=[
                    '_constraint.rhs_expr',
                ]
            ),
        )

        self._identity.category_code = 'constraint'
        self._identity.category_entry_name = lambda: str(self.lhs_alias.value)

    @property
    def lhs_alias(self):
        """Alias name on the left-hand side of the equation."""
        return self._lhs_alias

    @lhs_alias.setter
    def lhs_alias(self, value):
        """Set the left-hand side alias.

        Args:
            value: New alias string.
        """
        self._lhs_alias.value = value

    @property
    def rhs_expr(self):
        """Right-hand side expression string."""
        return self._rhs_expr

    @rhs_expr.setter
    def rhs_expr(self, value):
        """Set the right-hand side expression.

        Args:
            value: New expression string.
        """
        self._rhs_expr.value = value


class Constraints(CategoryCollection):
    """Collection of :class:`Constraint` items."""

    _update_priority = 90  # After most others, but before data categories

    def __init__(self):
        """Create an empty constraints collection."""
        super().__init__(item_type=Constraint)

    def _update(self, called_by_minimizer=False):
        del called_by_minimizer

        constraints = ConstraintsHandler.get()
        constraints.apply()
