# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Alias category for mapping friendly names to parameter UIDs.

Defines a small record type used by analysis configuration to refer to
parameters via readable labels instead of raw unique identifiers.
"""

from easydiffraction.core.category import CategoryCollection
from easydiffraction.core.category import CategoryItem
from easydiffraction.core.parameters import StringDescriptor
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import DataTypes
from easydiffraction.core.validation import RegexValidator
from easydiffraction.io.cif.handler import CifHandler


class Alias(CategoryItem):
    """Single alias entry.

    Maps a human-readable ``label`` to a concrete ``param_uid`` used by
    the engine.

    Args:
        label: Alias label. Must match ``^[A-Za-z_][A-Za-z0-9_]*$``.
        param_uid: Target parameter uid. Same identifier pattern as
            ``label``.
    """

    def __init__(
        self,
        *,
        label: str,
        param_uid: str,
    ) -> None:
        super().__init__()

        self._label: StringDescriptor = StringDescriptor(
            name='label',
            description='...',
            value_spec=AttributeSpec(
                value=label,
                type_=DataTypes.STRING,
                default='...',
                content_validator=RegexValidator(pattern=r'^[A-Za-z_][A-Za-z0-9_]*$'),
            ),
            cif_handler=CifHandler(
                names=[
                    '_alias.label',
                ]
            ),
        )
        self._param_uid: StringDescriptor = StringDescriptor(
            name='param_uid',
            description='...',
            value_spec=AttributeSpec(
                value=param_uid,
                type_=DataTypes.STRING,
                default='...',
                content_validator=RegexValidator(pattern=r'^[A-Za-z_][A-Za-z0-9_]*$'),
            ),
            cif_handler=CifHandler(
                names=[
                    '_alias.param_uid',
                ]
            ),
        )

        self._identity.category_code = 'alias'
        self._identity.category_entry_name = lambda: str(self.label.value)

    @property
    def label(self):
        """Alias label descriptor."""
        return self._label

    @label.setter
    def label(self, value):
        """Set alias label.

        Args:
            value: New label.
        """
        self._label.value = value

    @property
    def param_uid(self):
        """Parameter uid descriptor the alias points to."""
        return self._param_uid

    @param_uid.setter
    def param_uid(self, value):
        """Set the parameter uid.

        Args:
            value: New uid.
        """
        self._param_uid.value = value


class Aliases(CategoryCollection):
    """Collection of :class:`Alias` items."""

    def __init__(self):
        """Create an empty collection of aliases."""
        super().__init__(item_type=Alias)
