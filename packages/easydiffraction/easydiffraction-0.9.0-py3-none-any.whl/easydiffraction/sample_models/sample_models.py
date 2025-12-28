# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from typeguard import typechecked

from easydiffraction.core.datablock import DatablockCollection
from easydiffraction.sample_models.sample_model.base import SampleModelBase
from easydiffraction.sample_models.sample_model.factory import SampleModelFactory
from easydiffraction.utils.logging import console


class SampleModels(DatablockCollection):
    """Collection manager for multiple SampleModel instances."""

    def __init__(self) -> None:
        super().__init__(item_type=SampleModelBase)

    # --------------------
    # Add / Remove methods
    # --------------------

    # TODO: Move to DatablockCollection?
    # TODO: Disallow args and only allow kwargs?
    def add(self, **kwargs):
        sample_model = kwargs.pop('sample_model', None)

        if sample_model is None:
            sample_model = SampleModelFactory.create(**kwargs)

        self._add(sample_model)

    # @typechecked
    # def add_from_cif_path(self, cif_path: str) -> None:
    #    """Create and add a model from a CIF file path.#
    #
    #    Args:
    #        cif_path: Path to a CIF file.
    #    """
    #    sample_model = SampleModelFactory.create(cif_path=cif_path)
    #    self.add(sample_model)

    # @typechecked
    # def add_from_cif_str(self, cif_str: str) -> None:
    #    """Create and add a model from CIF content (string).
    #
    #    Args:
    #        cif_str: CIF file content.
    #    """
    #    sample_model = SampleModelFactory.create(cif_str=cif_str)
    #    self.add(sample_model)

    # @typechecked
    # def add_minimal(self, name: str) -> None:
    #    """Create and add a minimal model (defaults, no atoms).
    #
    #    Args:
    #        name: Identifier to assign to the new model.
    #    """
    #    sample_model = SampleModelFactory.create(name=name)
    #    self.add(sample_model)

    # TODO: Move to DatablockCollection?
    @typechecked
    def remove(self, name: str) -> None:
        """Remove a sample model by its ID.

        Args:
            name: ID of the model to remove.
        """
        if name in self:
            del self[name]

    # ------------
    # Show methods
    # ------------

    # TODO: Move to DatablockCollection?
    def show_names(self) -> None:
        """List all model names in the collection."""
        console.paragraph('Defined sample models' + ' 🧩')
        console.print(self.names)

    # TODO: Move to DatablockCollection?
    def show_params(self) -> None:
        """Show parameters of all sample models in the collection."""
        for model in self.values():
            model.show_params()
