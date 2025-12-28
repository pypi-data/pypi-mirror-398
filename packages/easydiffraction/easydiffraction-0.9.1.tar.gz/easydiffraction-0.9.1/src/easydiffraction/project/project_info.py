# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Project metadata container used by Project."""

import datetime
import pathlib

from easydiffraction.core.guard import GuardedBase
from easydiffraction.io.cif.serialize import project_info_to_cif
from easydiffraction.utils.logging import console
from easydiffraction.utils.utils import render_cif


class ProjectInfo(GuardedBase):
    """Stores metadata about the project, such as name, title,
    description, and file paths.
    """

    def __init__(
        self,
        name: str = 'untitled_project',
        title: str = 'Untitled Project',
        description: str = '',
    ) -> None:
        super().__init__()

        self._name = name
        self._title = title
        self._description = description
        self._path: pathlib.Path = pathlib.Path.cwd()
        self._created: datetime.datetime = datetime.datetime.now()
        self._last_modified: datetime.datetime = datetime.datetime.now()

    @property
    def name(self) -> str:
        """Return the project name."""
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._name = value

    @property
    def unique_name(self) -> str:
        """Unique name for GuardedBase diagnostics."""
        return self.name

    @property
    def title(self) -> str:
        """Return the project title."""
        return self._title

    @title.setter
    def title(self, value: str) -> None:
        self._title = value

    @property
    def description(self) -> str:
        """Return sanitized description with single spaces."""
        return ' '.join(self._description.split())

    @description.setter
    def description(self, value: str) -> None:
        self._description = ' '.join(value.split())

    @property
    def path(self) -> pathlib.Path:
        """Return the project path as a Path object."""
        return self._path

    @path.setter
    def path(self, value) -> None:
        # Accept str or Path; normalize to Path
        self._path = pathlib.Path(value)

    @property
    def created(self) -> datetime.datetime:
        """Return the creation timestamp."""
        return self._created

    @property
    def last_modified(self) -> datetime.datetime:
        """Return the last modified timestamp."""
        return self._last_modified

    def update_last_modified(self) -> None:
        """Update the last modified timestamp."""
        self._last_modified = datetime.datetime.now()

    def parameters(self):
        """Placeholder for parameter listing."""
        pass

    # TODO: Consider moving to io.cif.serialize
    def as_cif(self) -> str:
        """Export project metadata to CIF."""
        return project_info_to_cif(self)

    # TODO: Consider moving to io.cif.serialize
    def show_as_cif(self) -> None:
        """Pretty-print CIF via shared utilities."""
        paragraph_title: str = f"Project 📦 '{self.name}' info as CIF"
        cif_text: str = self.as_cif()
        console.paragraph(paragraph_title)
        render_cif(cif_text)
