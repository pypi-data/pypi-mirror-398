# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import secrets
import string
from typing import TYPE_CHECKING
from typing import Any

import numpy as np

from easydiffraction.core.diagnostic import Diagnostics
from easydiffraction.core.guard import GuardedBase
from easydiffraction.core.singletons import UidMapHandler
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import DataTypes
from easydiffraction.core.validation import RangeValidator
from easydiffraction.core.validation import TypeValidator
from easydiffraction.io.cif.serialize import param_from_cif
from easydiffraction.io.cif.serialize import param_to_cif

if TYPE_CHECKING:
    from easydiffraction.io.cif.handler import CifHandler


class GenericDescriptorBase(GuardedBase):
    """Base class for all parameter-like descriptors.

    A descriptor encapsulates a typed value with validation,
    human-readable name/description and a globally unique identifier
    that is stable across the session. Concrete subclasses specialize
    the expected data type and can extend the public API with
    additional behavior (e.g. units).

    Attributes:
        name: Local parameter name (e.g. 'a', 'b_iso').
        description: Optional human-readable description.
        uid: Stable random identifier for external references.
    """

    _BOOL_SPEC_TEMPLATE = AttributeSpec(
        type_=DataTypes.BOOL,
        default=False,
    )

    def __init__(
        self,
        *,
        value_spec: AttributeSpec,
        name: str,
        description: str = None,
    ):
        """Initialize the descriptor with validation and identity.

        Args:
            value_spec: Validation specification for the value.
            name: Local name of the descriptor within its category.
            description: Optional human-readable description.
        """
        super().__init__()

        expected_type = getattr(self, '_value_type', None)

        if expected_type:
            user_type = (
                value_spec._type_validator.expected_type
                if value_spec._type_validator is not None
                else None
            )
            if user_type and user_type is not expected_type:
                Diagnostics.type_override_error(
                    type(self).__name__,
                    expected_type,
                    user_type,
                )
            else:
                # Enforce descriptor's own type if not already defined
                value_spec._type_validator = TypeValidator(expected_type)

        self._value_spec = value_spec
        self._name = name
        self._description = description

        # Initial validated states
        self._value = self._value_spec.validated(
            value_spec.value,
            name=self.unique_name,
        )

    def __str__(self) -> str:
        return f'<{self.unique_name} = {self.value!r}>'

    @property
    def name(self) -> str:
        """Local name of the descriptor (without category/datablock)."""
        return self._name

    @property
    def unique_name(self):
        """Fully qualified name including datablock, category and entry
        name.
        """
        # 7c: Use filter(None, [...])
        parts = [
            self._identity.datablock_entry_name,
            self._identity.category_code,
            self._identity.category_entry_name,
            self.name,
        ]
        return '.'.join(filter(None, parts))

    def _parent_of_type(self, cls):
        """Walk up the parent chain and return the first parent of type
        `cls`.
        """
        obj = getattr(self, '_parent', None)
        visited = set()
        while obj is not None and id(obj) not in visited:
            visited.add(id(obj))
            if isinstance(obj, cls):
                return obj
            obj = getattr(obj, '_parent', None)
        return None

    def _datablock_item(self):
        """Return the DatablockItem ancestor, if any."""
        from easydiffraction.core.datablock import DatablockItem

        return self._parent_of_type(DatablockItem)

    @property
    def value(self):
        """Current validated value."""
        return self._value

    @value.setter
    def value(self, v):
        """Set a new value after validating against the spec."""
        # Do nothing if the value is unchanged
        if self._value == v:
            return

        # Validate and set the new value
        self._value = self._value_spec.validated(
            v,
            name=self.unique_name,
            current=self._value,
        )

        # Mark parent datablock as needing categories update
        # TODO: Check if it is actually in use?
        parent_datablock = self._datablock_item()
        if parent_datablock is not None:
            parent_datablock._need_categories_update = True

    @property
    def description(self):
        """Optional human-readable description."""
        return self._description

    @property
    def parameters(self):
        """Return a flat list of parameters contained by this object.

        For a single descriptor, it returns a one-element list with
        itself. Composite objects override this to flatten nested
        structures.
        """
        return [self]

    @property
    def as_cif(self) -> str:
        """Serialize this descriptor to a CIF-formatted string."""
        return param_to_cif(self)

    def from_cif(self, block, idx=0):
        """Populate this parameter from a CIF block."""
        param_from_cif(self, block, idx)


class GenericStringDescriptor(GenericDescriptorBase):
    _value_type = DataTypes.STRING

    def __init__(
        self,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)


class GenericNumericDescriptor(GenericDescriptorBase):
    _value_type = DataTypes.NUMERIC

    def __init__(
        self,
        *,
        units: str = '',
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._units: str = units

    def __str__(self) -> str:
        s: str = super().__str__()
        s = s[1:-1]  # strip <>
        if self.units:
            s += f' {self.units}'
        return f'<{s}>'

    @property
    def units(self) -> str:
        """Units associated with the numeric value, if any."""
        return self._units


class GenericParameter(GenericNumericDescriptor):
    """Numeric descriptor extended with fitting-related attributes.

    Adds standard attributes used by minimizers: "free" flag,
    uncertainty, bounds and an optional starting value. Subclasses can
    integrate with specific backends while preserving this interface.
    """

    def __init__(
        self,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)

        # Initial validated states
        self._free_spec = self._BOOL_SPEC_TEMPLATE
        self._free = self._free_spec.default
        self._uncertainty_spec = AttributeSpec(
            type_=DataTypes.NUMERIC,
            content_validator=RangeValidator(ge=0),
            allow_none=True,
        )
        self._uncertainty = self._uncertainty_spec.default
        self._fit_min_spec = AttributeSpec(type_=DataTypes.NUMERIC, default=-np.inf)
        self._fit_min = self._fit_min_spec.default
        self._fit_max_spec = AttributeSpec(type_=DataTypes.NUMERIC, default=np.inf)
        self._fit_max = self._fit_max_spec.default
        self._start_value_spec = AttributeSpec(type_=DataTypes.NUMERIC, default=0.0)
        self._start_value = self._start_value_spec.default
        self._constrained_spec = self._BOOL_SPEC_TEMPLATE
        self._constrained = self._constrained_spec.default

        self._uid: str = self._generate_uid()
        UidMapHandler.get().add_to_uid_map(self)

    def __str__(self) -> str:
        s = GenericDescriptorBase.__str__(self)
        s = s[1:-1]  # strip <>
        if self.uncertainty is not None:
            s += f' ± {self.uncertainty}'
        if self.units is not None:
            s += f' {self.units}'
        s += f' (free={self.free})'
        return f'<{s}>'

    @staticmethod
    def _generate_uid(length: int = 16) -> str:
        letters = string.ascii_lowercase
        return ''.join(secrets.choice(letters) for _ in range(length))

    @property
    def uid(self):
        """Stable random identifier for this descriptor."""
        return self._uid

    @property
    def _minimizer_uid(self):
        """Variant of uid that is safe for minimizer engines."""
        # return self.unique_name.replace('.', '__')
        return self.uid

    @property
    def name(self) -> str:
        """Local name of the parameter (without category/datablock)."""
        return self._name

    @property
    def unique_name(self):
        """Fully qualified parameter name including its context path."""
        parts = [
            self._identity.datablock_entry_name,
            self._identity.category_code,
            self._identity.category_entry_name,
            self.name,
        ]
        return '.'.join(filter(None, parts))

    @property
    def constrained(self):
        """Whether this parameter is part of a constraint expression."""
        return self._constrained

    @property
    def free(self):
        """Whether this parameter is currently varied during fitting."""
        return self._free

    @free.setter
    def free(self, v):
        """Set the "free" flag after validation."""
        self._free = self._free_spec.validated(
            v, name=f'{self.unique_name}.free', current=self._free
        )

    @property
    def uncertainty(self):
        """Estimated standard uncertainty of the fitted value, if
        available.
        """
        return self._uncertainty

    @uncertainty.setter
    def uncertainty(self, v):
        """Set the uncertainty value (must be non-negative or None)."""
        self._uncertainty = self._uncertainty_spec.validated(
            v, name=f'{self.unique_name}.uncertainty', current=self._uncertainty
        )

    @property
    def fit_min(self):
        """Lower fitting bound."""
        return self._fit_min

    @fit_min.setter
    def fit_min(self, v):
        """Set the lower bound for the parameter value."""
        self._fit_min = self._fit_min_spec.validated(
            v, name=f'{self.unique_name}.fit_min', current=self._fit_min
        )

    @property
    def fit_max(self):
        """Upper fitting bound."""
        return self._fit_max

    @fit_max.setter
    def fit_max(self, v):
        """Set the upper bound for the parameter value."""
        self._fit_max = self._fit_max_spec.validated(
            v, name=f'{self.unique_name}.fit_max', current=self._fit_max
        )


class StringDescriptor(GenericStringDescriptor):
    def __init__(
        self,
        *,
        cif_handler: CifHandler,
        **kwargs: Any,
    ) -> None:
        """String descriptor bound to a CIF handler.

        Args:
            cif_handler: Object that tracks CIF identifiers.
            **kwargs: Forwarded to GenericStringDescriptor.
        """
        super().__init__(**kwargs)
        self._cif_handler = cif_handler
        self._cif_handler.attach(self)


class NumericDescriptor(GenericNumericDescriptor):
    def __init__(
        self,
        *,
        cif_handler: CifHandler,
        **kwargs: Any,
    ) -> None:
        """Numeric descriptor bound to a CIF handler.

        Args:
            cif_handler: Object that tracks CIF identifiers.
            **kwargs: Forwarded to GenericNumericDescriptor.
        """
        super().__init__(**kwargs)
        self._cif_handler = cif_handler
        self._cif_handler.attach(self)


class Parameter(GenericParameter):
    def __init__(
        self,
        *,
        cif_handler: CifHandler,
        **kwargs: Any,
    ) -> None:
        """Fittable parameter bound to a CIF handler.

        Args:
            cif_handler: Object that tracks CIF identifiers.
            **kwargs: Forwarded to GenericParameter.
        """
        super().__init__(**kwargs)
        self._cif_handler = cif_handler
        self._cif_handler.attach(self)
