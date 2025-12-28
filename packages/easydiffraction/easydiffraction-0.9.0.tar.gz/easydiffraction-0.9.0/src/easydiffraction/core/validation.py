# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Lightweight runtime validation utilities.

Provides DataTypes, type/content validators, and AttributeSpec used by
descriptors and parameters. Only documentation was added here.
"""

import functools
import re
from abc import ABC
from abc import abstractmethod
from enum import Enum
from enum import auto

import numpy as np
from typeguard import TypeCheckError
from typeguard import typechecked

from easydiffraction.core.diagnostic import Diagnostics
from easydiffraction.utils.logging import log

# ==============================================================
# Shared constants
# ==============================================================


class DataTypes(Enum):
    NUMERIC = (int, float, np.integer, np.floating, np.number)
    STRING = (str,)
    BOOL = (bool,)
    ANY = (object,)  # fallback for unconstrained

    def __str__(self):
        return self.name.lower()

    @property
    def expected_type(self):
        """Convenience alias for tuple of allowed Python types."""
        return self.value


# ==============================================================
# Runtime type checking decorator
# ==============================================================

# Runtime type checking decorator for validating those methods
# annotated with type hints, which are writable for the user, and
# which are not covered by custom validators for Parameter attribute
# types and content, implemented below.


def checktype(func=None, *, context=None):
    """Runtime type check decorator using typeguard.

    When a TypeCheckError occurs, the error is logged and None is
    returned. If context is provided, it is added to the message.
    """

    def decorator(f):
        checked_func = typechecked(f)

        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            try:
                return checked_func(*args, **kwargs)
            except TypeCheckError as err:
                msg = str(err)
                if context:
                    msg = f'{context}: {msg}'
                log.error(message=msg, exc_type=TypeError)
                return None

        return wrapper

    if func is None:
        return decorator
    return decorator(func)


# ==============================================================
# Validation stages (enum/constant)
# ==============================================================


class ValidationStage(Enum):
    """Phases of validation for diagnostic logging."""

    TYPE = auto()
    RANGE = auto()
    MEMBERSHIP = auto()
    REGEX = auto()

    def __str__(self):
        return self.name.lower()


# ==============================================================
# Advanced runtime custom validators for Parameter types/content
# ==============================================================


class ValidatorBase(ABC):
    """Abstract base class for all validators."""

    @abstractmethod
    def validated(self, value, name, default=None, current=None):
        """Return a validated value or fallback.

        Subclasses must implement this method.
        """
        raise NotImplementedError

    def _fallback(
        self,
        current=None,
        default=None,
    ):
        """Return current if set, else default."""
        return current if current is not None else default


class TypeValidator(ValidatorBase):
    """Ensure a value is of the expected Python type."""

    def __init__(self, expected_type: DataTypes):
        if isinstance(expected_type, DataTypes):
            self.expected_type = expected_type
            self.expected_label = str(expected_type)
        else:
            raise TypeError(f'TypeValidator expected a DataTypes member, got {expected_type!r}')

    def validated(
        self,
        value,
        name,
        default=None,
        current=None,
        allow_none=False,
    ):
        """Validate type and return value or fallback.

        If allow_none is True, None bypasses content checks.
        """
        # Fresh initialization, use default
        if current is None and value is None:
            Diagnostics.no_value(name, default)
            return default

        # Explicit None (allowed)
        if value is None and allow_none:
            Diagnostics.none_value(name)
            return None

        # Normal type validation
        if not isinstance(value, self.expected_type.value):
            Diagnostics.type_mismatch(
                name,
                value,
                expected_type=self.expected_label,
                current=current,
                default=default,
            )
            return self._fallback(current, default)

        Diagnostics.validated(
            name,
            value,
            stage=ValidationStage.TYPE,
        )
        return value


class RangeValidator(ValidatorBase):
    """Ensure a numeric value lies within [ge, le]."""

    def __init__(
        self,
        *,
        ge=-np.inf,
        le=np.inf,
    ):
        self.ge, self.le = ge, le

    def validated(
        self,
        value,
        name,
        default=None,
        current=None,
    ):
        """Validate range and return value or fallback."""
        if not (self.ge <= value <= self.le):
            Diagnostics.range_mismatch(
                name,
                value,
                self.ge,
                self.le,
                current=current,
                default=default,
            )
            return self._fallback(current, default)

        Diagnostics.validated(
            name,
            value,
            stage=ValidationStage.RANGE,
        )
        return value


class MembershipValidator(ValidatorBase):
    """Ensure that a value is among allowed choices.

    `allowed` may be an iterable or a callable returning a collection.
    """

    def __init__(self, allowed):
        # Do not convert immediately to list — may be callable
        self.allowed = allowed

    def validated(
        self,
        value,
        name,
        default=None,
        current=None,
    ):
        """Validate membership and return value or fallback."""
        # Dynamically evaluate allowed if callable (e.g. lambda)
        allowed_values = self.allowed() if callable(self.allowed) else self.allowed

        if value not in allowed_values:
            Diagnostics.choice_mismatch(
                name,
                value,
                allowed_values,
                current=current,
                default=default,
            )
            return self._fallback(current, default)

        Diagnostics.validated(
            name,
            value,
            stage=ValidationStage.MEMBERSHIP,
        )
        return value


class RegexValidator(ValidatorBase):
    """Ensure that a string matches a given regular expression."""

    def __init__(self, pattern):
        self.pattern = re.compile(pattern)

    def validated(
        self,
        value,
        name,
        default=None,
        current=None,
    ):
        """Validate regex and return value or fallback."""
        if not self.pattern.fullmatch(value):
            Diagnostics.regex_mismatch(
                name,
                value,
                self.pattern.pattern,
                current=current,
                default=default,
            )
            return self._fallback(current, default)

        Diagnostics.validated(
            name,
            value,
            stage=ValidationStage.REGEX,
        )
        return value


# ==============================================================
# Attribute specification holding metadata and validators
# ==============================================================


class AttributeSpec:
    """Hold metadata and validators for a single attribute."""

    def __init__(
        self,
        *,
        value=None,
        type_=None,
        default=None,
        content_validator=None,
        allow_none: bool = False,
    ):
        self.value = value
        self.default = default
        self.allow_none = allow_none
        self._type_validator = TypeValidator(type_) if type_ else None
        self._content_validator = content_validator

    def validated(
        self,
        value,
        name,
        current=None,
    ):
        """Validate through type and content validators.

        Returns validated value, possibly default or current if errors
        occur. None may short-circuit further checks when allowed.
        """
        val = value
        # Evaluate callable defaults dynamically
        default = self.default() if callable(self.default) else self.default

        # Type validation
        if self._type_validator:
            val = self._type_validator.validated(
                val,
                name,
                default=default,
                current=current,
                allow_none=self.allow_none,
            )

        # Skip further validation: Special case for None
        if val is None and self.allow_none:
            Diagnostics.none_value_skip_range(name)
            return None

        # Content validation
        if self._content_validator and val is not None:
            val = self._content_validator.validated(
                val,
                name,
                default=default,
                current=current,
            )

        return val
