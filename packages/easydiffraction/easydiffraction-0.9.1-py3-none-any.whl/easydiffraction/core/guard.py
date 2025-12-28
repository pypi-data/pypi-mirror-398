# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from abc import ABC
from abc import abstractmethod

from easydiffraction.core.diagnostic import Diagnostics
from easydiffraction.core.identity import Identity


class GuardedBase(ABC):
    """Base class enforcing controlled attribute access and parent
    linkage.
    """

    _diagnoser = Diagnostics()

    def __init__(self):
        self._identity = Identity(owner=self)

    def __str__(self) -> str:
        return f'<{self.unique_name}>'

    def __repr__(self) -> str:
        return self.__str__()

    def __getattr__(self, key: str):
        cls = type(self)
        allowed = cls._public_attrs()
        if key not in allowed:
            type(self)._diagnoser.attr_error(
                self._log_name,
                key,
                allowed,
                label='Allowed readable/writable',
            )

    def __setattr__(self, key: str, value):
        # Always allow private or special attributes without diagnostics
        if key.startswith('_'):
            object.__setattr__(self, key, value)
            # Also maintain parent linkage for nested objects
            if key != '_parent' and isinstance(value, GuardedBase):
                object.__setattr__(value, '_parent', self)
            return

        # Handle public attributes with diagnostics
        cls = type(self)
        # Prevent modification of read-only attributes
        if key in cls._public_readonly_attrs():
            cls._diagnoser.readonly_error(
                self._log_name,
                key,
            )
            return
        # Prevent assignment to unknown attributes
        # Show writable attributes only as allowed
        if key not in cls._public_attrs():
            allowed = cls._public_writable_attrs()
            cls._diagnoser.attr_error(
                self._log_name,
                key,
                allowed,
                label='Allowed writable',
            )
            return

        self._assign_attr(key, value)

    def _assign_attr(self, key, value):
        """Low-level assignment with parent linkage."""
        object.__setattr__(self, key, value)
        if key != '_parent' and isinstance(value, GuardedBase):
            object.__setattr__(value, '_parent', self)

    @classmethod
    def _iter_properties(cls):
        """Iterate over all public properties defined in the class
        hierarchy.

        Yields:
            tuple[str, property]: Each (key, property) pair for public
            attributes.
        """
        for base in cls.mro():
            for key, attr in base.__dict__.items():
                if key.startswith('_') or not isinstance(attr, property):
                    continue
                yield key, attr

    @classmethod
    def _public_attrs(cls):
        """All public properties (read-only + writable)."""
        return {key for key, _ in cls._iter_properties()}

    @classmethod
    def _public_readonly_attrs(cls):
        """Public properties without a setter."""
        return {key for key, prop in cls._iter_properties() if prop.fset is None}

    @classmethod
    def _public_writable_attrs(cls) -> set[str]:
        """Public properties with a setter."""
        return {key for key, prop in cls._iter_properties() if prop.fset is not None}

    def _allowed_attrs(self, writable_only=False):
        cls = type(self)
        if writable_only:
            return cls._public_writable_attrs()
        return cls._public_attrs()

    @property
    def _log_name(self):
        return self.unique_name or type(self).__name__

    @property
    def unique_name(self):
        return type(self).__name__

    # @property
    # def identity(self):
    #    """Expose a limited read-only view of identity attributes."""
    #    return SimpleNamespace(
    #        datablock_entry_name=self._identity.datablock_entry_name,
    #        category_code=self._identity.category_code,
    #        category_entry_name=self._identity.category_entry_name,
    #    )

    @property
    @abstractmethod
    def parameters(self):
        """Return a list of parameter objects (to be implemented by
        subclasses).
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def as_cif(self) -> str:
        """Return CIF representation of this object (to be implemented
        by subclasses).
        """
        raise NotImplementedError
