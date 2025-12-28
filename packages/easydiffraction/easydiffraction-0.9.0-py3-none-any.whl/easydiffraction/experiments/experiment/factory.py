# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from typing import TYPE_CHECKING

from easydiffraction.core.factory import FactoryBase
from easydiffraction.experiments.categories.experiment_type import ExperimentType
from easydiffraction.experiments.experiment import BraggPdExperiment
from easydiffraction.experiments.experiment import BraggScExperiment
from easydiffraction.experiments.experiment import TotalPdExperiment
from easydiffraction.experiments.experiment.enums import BeamModeEnum
from easydiffraction.experiments.experiment.enums import RadiationProbeEnum
from easydiffraction.experiments.experiment.enums import SampleFormEnum
from easydiffraction.experiments.experiment.enums import ScatteringTypeEnum
from easydiffraction.io.cif.parse import document_from_path
from easydiffraction.io.cif.parse import document_from_string
from easydiffraction.io.cif.parse import name_from_block
from easydiffraction.io.cif.parse import pick_sole_block

if TYPE_CHECKING:
    import gemmi

    from easydiffraction.experiments.experiment.base import ExperimentBase


class ExperimentFactory(FactoryBase):
    """Creates Experiment instances with only relevant attributes."""

    _ALLOWED_ARG_SPECS = [
        {'required': ['cif_path'], 'optional': []},
        {'required': ['cif_str'], 'optional': []},
        {
            'required': ['name', 'data_path'],
            'optional': ['sample_form', 'beam_mode', 'radiation_probe', 'scattering_type'],
        },
        {
            'required': ['name'],
            'optional': ['sample_form', 'beam_mode', 'radiation_probe', 'scattering_type'],
        },
    ]

    _SUPPORTED = {
        ScatteringTypeEnum.BRAGG: {
            SampleFormEnum.POWDER: BraggPdExperiment,
            SampleFormEnum.SINGLE_CRYSTAL: BraggScExperiment,
        },
        ScatteringTypeEnum.TOTAL: {
            SampleFormEnum.POWDER: TotalPdExperiment,
        },
    }

    @classmethod
    def _make_experiment_type(cls, kwargs):
        """Helper to construct an ExperimentType from keyword arguments,
        using defaults as needed.
        """
        # TODO: Defaults are already in the experiment type...
        # TODO: Merging with experiment_type_from_block from
        #  io.cif.parse
        return ExperimentType(
            sample_form=kwargs.get('sample_form', SampleFormEnum.default().value),
            beam_mode=kwargs.get('beam_mode', BeamModeEnum.default().value),
            radiation_probe=kwargs.get('radiation_probe', RadiationProbeEnum.default().value),
            scattering_type=kwargs.get('scattering_type', ScatteringTypeEnum.default().value),
        )

    # TODO: Move to a common CIF utility module? io.cif.parse?
    @classmethod
    def _create_from_gemmi_block(
        cls,
        block: gemmi.cif.Block,
    ) -> ExperimentBase:
        """Build a model instance from a single CIF block."""
        name = name_from_block(block)

        # TODO: move to io.cif.parse?
        expt_type = ExperimentType()
        for param in expt_type.parameters:
            param.from_cif(block)

        # Create experiment instance of appropriate class
        # TODO: make helper method to create experiment from type
        scattering_type = expt_type.scattering_type.value
        sample_form = expt_type.sample_form.value
        expt_class = cls._SUPPORTED[scattering_type][sample_form]
        expt_obj = expt_class(name=name, type=expt_type)

        # Read all categories from CIF block
        # TODO: move to io.cif.parse?
        for category in expt_obj.categories:
            category.from_cif(block)

        return expt_obj

    @classmethod
    def _create_from_cif_path(
        cls,
        cif_path: str,
    ) -> ExperimentBase:
        """Create an experiment from a CIF file path."""
        doc = document_from_path(cif_path)
        block = pick_sole_block(doc)
        return cls._create_from_gemmi_block(block)

    @classmethod
    def _create_from_cif_str(
        cls,
        cif_str: str,
    ) -> ExperimentBase:
        """Create an experiment from a CIF string."""
        doc = document_from_string(cif_str)
        block = pick_sole_block(doc)
        return cls._create_from_gemmi_block(block)

    @classmethod
    def _create_from_data_path(cls, kwargs):
        """Create an experiment from a raw data ASCII file.

        Loads the experiment and attaches measured data from the
        specified file.
        """
        expt_type = cls._make_experiment_type(kwargs)
        scattering_type = expt_type.scattering_type.value
        sample_form = expt_type.sample_form.value
        expt_class = cls._SUPPORTED[scattering_type][sample_form]
        expt_name = kwargs['name']
        expt_obj = expt_class(name=expt_name, type=expt_type)
        data_path = kwargs['data_path']
        expt_obj._load_ascii_data_to_experiment(data_path)
        return expt_obj

    @classmethod
    def _create_without_data(cls, kwargs):
        """Create an experiment without measured data.

        Returns an experiment instance with only metadata and
        configuration.
        """
        expt_type = cls._make_experiment_type(kwargs)
        scattering_type = expt_type.scattering_type.value
        sample_form = expt_type.sample_form.value
        expt_class = cls._SUPPORTED[scattering_type][sample_form]
        expt_name = kwargs['name']
        expt_obj = expt_class(name=expt_name, type=expt_type)
        return expt_obj

    @classmethod
    def create(cls, **kwargs):
        """Create an `ExperimentBase` using a validated argument
        combination.
        """
        # TODO: move to FactoryBase
        # Check for valid argument combinations
        user_args = {k for k, v in kwargs.items() if v is not None}
        cls._validate_args(
            present=user_args,
            allowed_specs=cls._ALLOWED_ARG_SPECS,
            factory_name=cls.__name__,  # TODO: move to FactoryBase
        )

        # Validate enum arguments if provided
        if 'sample_form' in kwargs:
            SampleFormEnum(kwargs['sample_form'])
        if 'beam_mode' in kwargs:
            BeamModeEnum(kwargs['beam_mode'])
        if 'radiation_probe' in kwargs:
            RadiationProbeEnum(kwargs['radiation_probe'])
        if 'scattering_type' in kwargs:
            ScatteringTypeEnum(kwargs['scattering_type'])

        # Dispatch to the appropriate creation method
        if 'cif_path' in kwargs:
            return cls._create_from_cif_path(kwargs['cif_path'])
        elif 'cif_str' in kwargs:
            return cls._create_from_cif_str(kwargs['cif_str'])
        elif 'data_path' in kwargs:
            return cls._create_from_data_path(kwargs)
        elif 'name' in kwargs:
            return cls._create_without_data(kwargs)
