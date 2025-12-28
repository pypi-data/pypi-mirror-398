# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Project facade to orchestrate models, experiments, and analysis."""

import pathlib
import tempfile

from typeguard import typechecked
from varname import varname

from easydiffraction.analysis.analysis import Analysis
from easydiffraction.core.guard import GuardedBase
from easydiffraction.display.plotting import Plotter
from easydiffraction.display.tables import TableRenderer
from easydiffraction.experiments.experiments import Experiments
from easydiffraction.io.cif.serialize import project_to_cif
from easydiffraction.project.project_info import ProjectInfo
from easydiffraction.sample_models.sample_models import SampleModels
from easydiffraction.summary.summary import Summary
from easydiffraction.utils.logging import console
from easydiffraction.utils.logging import log


class Project(GuardedBase):
    """Central API for managing a diffraction data analysis project.

    Provides access to sample models, experiments, analysis, and
    summary.
    """

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------
    def __init__(
        self,
        name: str = 'untitled_project',
        title: str = 'Untitled Project',
        description: str = '',
    ) -> None:
        super().__init__()

        self._info: ProjectInfo = ProjectInfo(name, title, description)
        self._sample_models = SampleModels()
        self._experiments = Experiments()
        self._tabler = TableRenderer.get()
        self._plotter = Plotter()
        self._analysis = Analysis(self)
        self._summary = Summary(self)
        self._saved = False
        self._varname = varname()

    # ------------------------------------------------------------------
    # Dunder methods
    # ------------------------------------------------------------------
    def __str__(self) -> str:
        """Human-readable representation."""
        class_name = self.__class__.__name__
        project_name = self.name
        sample_models_count = len(self.sample_models)
        experiments_count = len(self.experiments)
        return (
            f"{class_name} '{project_name}' "
            f'({sample_models_count} sample models, '
            f'{experiments_count} experiments)'
        )

    # ------------------------------------------------------------------
    # Public read-only properties
    # ------------------------------------------------------------------

    @property
    def info(self) -> ProjectInfo:
        """Project metadata container."""
        return self._info

    @property
    def name(self) -> str:
        """Convenience property to access the project's name
        directly.
        """
        return self._info.name

    @property
    def full_name(self) -> str:
        return self.name

    @property
    def sample_models(self) -> SampleModels:
        """Collection of sample models in the project."""
        return self._sample_models

    @sample_models.setter
    @typechecked
    def sample_models(self, sample_models: SampleModels) -> None:
        self._sample_models = sample_models

    @property
    def experiments(self):
        """Collection of experiments in the project."""
        return self._experiments

    @experiments.setter
    @typechecked
    def experiments(self, experiments: Experiments):
        self._experiments = experiments

    @property
    def plotter(self):
        """Plotting facade bound to the project."""
        return self._plotter

    @property
    def tabler(self):
        """Tables rendering facade bound to the project."""
        return self._tabler

    @property
    def analysis(self):
        """Analysis entry-point bound to the project."""
        return self._analysis

    @property
    def summary(self):
        """Summary report builder bound to the project."""
        return self._summary

    @property
    def parameters(self):
        """Return parameters from all components (TBD)."""
        # To be implemented: return all parameters in the project
        return []

    @property
    def as_cif(self):
        """Export whole project as CIF text."""
        # Concatenate sections using centralized CIF serializers
        return project_to_cif(self)

    # ------------------------------------------
    #  Project File I/O
    # ------------------------------------------

    def load(self, dir_path: str) -> None:
        """Load a project from a given directory.

        Loads project info, sample models, experiments, etc.
        """
        console.paragraph('Loading project 📦 from')
        console.print(dir_path)
        self._info.path = dir_path
        # TODO: load project components from files inside dir_path
        console.print('Loading project is not implemented yet.')
        self._saved = True

    def save(self) -> None:
        """Save the project into the existing project directory."""
        if not self._info.path:
            log.error('Project path not specified. Use save_as() to define the path first.')
            return

        console.paragraph(f"Saving project 📦 '{self.name}' to")
        console.print(self.info.path.resolve())

        # Ensure project directory exists
        self._info.path.mkdir(parents=True, exist_ok=True)

        # Save project info
        with (self._info.path / 'project.cif').open('w') as f:
            f.write(self._info.as_cif())
            console.print('├── 📄 project.cif')

        # Save sample models
        sm_dir = self._info.path / 'sample_models'
        sm_dir.mkdir(parents=True, exist_ok=True)
        # Iterate over sample model objects (MutableMapping iter gives
        # keys)
        for model in self.sample_models.values():
            file_name: str = f'{model.name}.cif'
            file_path = sm_dir / file_name
            console.print('├── 📁 sample_models')
            with file_path.open('w') as f:
                f.write(model.as_cif)
                console.print(f'│   └── 📄 {file_name}')

        # Save experiments
        expt_dir = self._info.path / 'experiments'
        expt_dir.mkdir(parents=True, exist_ok=True)
        for experiment in self.experiments.values():
            file_name: str = f'{experiment.name}.cif'
            file_path = expt_dir / file_name
            console.print('├── 📁 experiments')
            with file_path.open('w') as f:
                f.write(experiment.as_cif)
                console.print(f'│   └── 📄 {file_name}')

        # Save analysis
        with (self._info.path / 'analysis.cif').open('w') as f:
            f.write(self.analysis.as_cif())
            console.print('├── 📄 analysis.cif')

        # Save summary
        with (self._info.path / 'summary.cif').open('w') as f:
            f.write(self.summary.as_cif())
            console.print('└── 📄 summary.cif')

        self._info.update_last_modified()
        self._saved = True

    def save_as(
        self,
        dir_path: str,
        temporary: bool = False,
    ) -> None:
        """Save the project into a new directory."""
        if temporary:
            tmp: str = tempfile.gettempdir()
            dir_path = pathlib.Path(tmp) / dir_path
        self._info.path = dir_path
        self.save()

    # ------------------------------------------
    # Plotting
    # ------------------------------------------

    def _update_categories(self, expt_name) -> None:
        for sample_model in self.sample_models:
            sample_model._update_categories()
        self.analysis._update_categories()
        experiment = self.experiments[expt_name]
        experiment._update_categories()

    def plot_meas(
        self,
        expt_name,
        x_min=None,
        x_max=None,
        d_spacing=False,
    ):
        self._update_categories(expt_name)
        experiment = self.experiments[expt_name]

        self.plotter.plot_meas(
            experiment.data,
            expt_name,
            experiment.type,
            x_min=x_min,
            x_max=x_max,
            d_spacing=d_spacing,
        )

    def plot_calc(
        self,
        expt_name,
        x_min=None,
        x_max=None,
        d_spacing=False,
    ):
        self._update_categories(expt_name)
        experiment = self.experiments[expt_name]

        self.plotter.plot_calc(
            experiment.data,
            expt_name,
            experiment.type,
            x_min=x_min,
            x_max=x_max,
            d_spacing=d_spacing,
        )

    def plot_meas_vs_calc(
        self,
        expt_name,
        x_min=None,
        x_max=None,
        show_residual=False,
        d_spacing=False,
    ):
        self._update_categories(expt_name)
        experiment = self.experiments[expt_name]

        self.plotter.plot_meas_vs_calc(
            experiment.data,
            expt_name,
            experiment.type,
            x_min=x_min,
            x_max=x_max,
            show_residual=show_residual,
            d_spacing=d_spacing,
        )
