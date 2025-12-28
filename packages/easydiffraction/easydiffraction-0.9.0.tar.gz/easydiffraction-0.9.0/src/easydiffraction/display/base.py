# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Common base classes for display components and their factories."""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import List
from typing import Tuple

import pandas as pd

from easydiffraction.core.singletons import SingletonBase
from easydiffraction.utils.logging import console
from easydiffraction.utils.logging import log


class RendererBase(SingletonBase, ABC):
    """Base class for display components with pluggable engines.

    Subclasses provide a factory and a default engine. This class
    manages the active backend instance and exposes helpers to inspect
    supported engines in a table-friendly format.
    """

    def __init__(self):
        self._engine = self._default_engine()
        self._backend = self._factory().create(self._engine)

    @classmethod
    @abstractmethod
    def _factory(cls) -> type[RendererFactoryBase]:
        """Return the factory class for this renderer type."""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def _default_engine(cls) -> str:
        """Return the default engine name for this renderer."""
        raise NotImplementedError

    @property
    def engine(self) -> str:
        return self._engine

    @engine.setter
    def engine(self, new_engine: str) -> None:
        if new_engine == self._engine:
            log.info(f"Engine is already set to '{new_engine}'. No change made.")
            return
        try:
            self._backend = self._factory().create(new_engine)
        except ValueError as exc:
            # Log a friendly message and leave engine unchanged
            log.warning(str(exc))
            return
        else:
            self._engine = new_engine
            console.paragraph('Current engine changed to')
            console.print(f"'{self._engine}'")

    @abstractmethod
    def show_config(self) -> None:
        """Display the current renderer configuration."""
        raise NotImplementedError

    def show_supported_engines(self) -> None:
        """List supported engines with descriptions in a table."""
        headers = [
            ('Engine', 'left'),
            ('Description', 'left'),
        ]
        rows = self._factory().descriptions()
        df = pd.DataFrame(rows, columns=pd.MultiIndex.from_tuples(headers))
        console.paragraph('Supported engines')
        # Delegate table rendering to the TableRenderer singleton
        from easydiffraction.display.tables import TableRenderer  # local import to avoid cycles

        TableRenderer.get().render(df)

    def show_current_engine(self) -> None:
        """Display the currently selected engine."""
        console.paragraph('Current engine')
        console.print(f"'{self._engine}'")


class RendererFactoryBase(ABC):
    """Base factory that manages discovery and creation of backends."""

    @classmethod
    def create(cls, engine_name: str) -> Any:
        """Create a backend instance for the given engine.

        Args:
            engine_name: Identifier of the engine to instantiate as
                listed in ``_registry()``.

        Returns:
            A new backend instance corresponding to ``engine_name``.

        Raises:
            ValueError: If the engine name is not supported.
        """
        registry = cls._registry()
        if engine_name not in registry:
            supported = list(registry.keys())
            raise ValueError(f"Unsupported engine '{engine_name}'. Supported engines: {supported}")
        engine_class = registry[engine_name]['class']
        return engine_class()

    @classmethod
    def supported_engines(cls) -> List[str]:
        """Return a list of supported engine identifiers."""
        return list(cls._registry().keys())

    @classmethod
    def descriptions(cls) -> List[Tuple[str, str]]:
        """Return pairs of engine name and human-friendly
        description.
        """
        items = cls._registry().items()
        return [(name, config.get('description')) for name, config in items]

    @classmethod
    @abstractmethod
    def _registry(cls) -> dict:
        """Return engine registry. Implementations must provide this.

        The returned mapping should have keys as engine names and values
        as a config dict with 'description' and 'class'. Lazy imports
        are allowed to avoid circular dependencies.
        """
        raise NotImplementedError
