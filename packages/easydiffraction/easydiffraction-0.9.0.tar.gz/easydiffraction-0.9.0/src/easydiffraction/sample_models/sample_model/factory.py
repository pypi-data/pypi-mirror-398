# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Factory for creating sample models from simple inputs or CIF.

Supports three argument combinations: ``name``, ``cif_path``, or
``cif_str``. Returns a minimal ``SampleModelBase`` populated from CIF
when provided, or an empty model with the given name.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from easydiffraction.core.factory import FactoryBase
from easydiffraction.io.cif.parse import document_from_path
from easydiffraction.io.cif.parse import document_from_string
from easydiffraction.io.cif.parse import name_from_block
from easydiffraction.io.cif.parse import pick_sole_block
from easydiffraction.sample_models.sample_model.base import SampleModelBase

if TYPE_CHECKING:
    import gemmi


class SampleModelFactory(FactoryBase):
    """Create ``SampleModelBase`` instances from supported inputs."""

    _ALLOWED_ARG_SPECS = [
        {'required': ['name'], 'optional': []},
        {'required': ['cif_path'], 'optional': []},
        {'required': ['cif_str'], 'optional': []},
    ]

    @classmethod
    def _create_from_gemmi_block(
        cls,
        block: gemmi.cif.Block,
    ) -> SampleModelBase:
        """Build a model instance from a single CIF block."""
        name = name_from_block(block)
        sample_model = SampleModelBase(name=name)
        for category in sample_model.categories:
            category.from_cif(block)
        return sample_model

    @classmethod
    def _create_from_cif_path(
        cls,
        cif_path: str,
    ) -> SampleModelBase:
        """Create a model by reading and parsing a CIF file."""
        doc = document_from_path(cif_path)
        block = pick_sole_block(doc)
        return cls._create_from_gemmi_block(block)

    @classmethod
    def _create_from_cif_str(
        cls,
        cif_str: str,
    ) -> SampleModelBase:
        """Create a model by parsing a CIF string."""
        doc = document_from_string(cif_str)
        block = pick_sole_block(doc)
        return cls._create_from_gemmi_block(block)

    @classmethod
    def _create_minimal(
        cls,
        name: str,
    ) -> SampleModelBase:
        """Create a minimal default model with just a name."""
        return SampleModelBase(name=name)

    @classmethod
    def create(cls, **kwargs):
        """Create a model based on a validated argument combination.

        Keyword Args:
            name: Name of the sample model to create.
            cif_path: Path to a CIF file to parse.
            cif_str: Raw CIF string to parse.
            **kwargs: Extra args are ignored if None; only the above
                three keys are supported.

        Returns:
            SampleModelBase: A populated or empty model instance.
        """
        # TODO: move to FactoryBase
        # Check for valid argument combinations
        user_args = {k for k, v in kwargs.items() if v is not None}
        cls._validate_args(
            present=user_args,
            allowed_specs=cls._ALLOWED_ARG_SPECS,
            factory_name=cls.__name__,  # TODO: move to FactoryBase
        )

        # Dispatch to the appropriate creation method
        if 'cif_path' in kwargs:
            return cls._create_from_cif_path(kwargs['cif_path'])
        elif 'cif_str' in kwargs:
            return cls._create_from_cif_str(kwargs['cif_str'])
        elif 'name' in kwargs:
            return cls._create_minimal(kwargs['name'])
