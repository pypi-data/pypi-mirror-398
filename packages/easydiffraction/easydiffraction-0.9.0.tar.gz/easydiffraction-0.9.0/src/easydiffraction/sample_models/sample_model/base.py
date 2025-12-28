# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from easydiffraction.core.datablock import DatablockItem
from easydiffraction.crystallography import crystallography as ecr
from easydiffraction.sample_models.categories.atom_sites import AtomSites
from easydiffraction.sample_models.categories.cell import Cell
from easydiffraction.sample_models.categories.space_group import SpaceGroup
from easydiffraction.utils.logging import console
from easydiffraction.utils.utils import render_cif


class SampleModelBase(DatablockItem):
    """Base sample model and container for structural information.

    Holds space group, unit cell and atom-site categories. The
    factory is responsible for creating rich instances from CIF;
    this base accepts just the ``name`` and exposes helpers for
    applying symmetry.
    """

    def __init__(
        self,
        *,
        name,
    ) -> None:
        super().__init__()
        self._name = name
        self._cell: Cell = Cell()
        self._space_group: SpaceGroup = SpaceGroup()
        self._atom_sites: AtomSites = AtomSites()
        self._identity.datablock_entry_name = lambda: self.name

    def __str__(self) -> str:
        """Human-readable representation of this component."""
        name = self._log_name
        items = ', '.join(
            f'{k}={v}'
            for k, v in {
                'cell': self.cell,
                'space_group': self.space_group,
                'atom_sites': self.atom_sites,
            }.items()
        )
        return f'<{name} ({items})>'

    @property
    def name(self) -> str:
        """Model name.

        Returns:
            The user-facing identifier for this model.
        """
        return self._name

    @name.setter
    def name(self, new: str) -> None:
        """Update model name."""
        self._name = new

    @property
    def cell(self) -> Cell:
        """Unit-cell category object."""
        return self._cell

    @cell.setter
    def cell(self, new: Cell) -> None:
        """Replace the unit-cell category object."""
        self._cell = new

    @property
    def space_group(self) -> SpaceGroup:
        """Space-group category object."""
        return self._space_group

    @space_group.setter
    def space_group(self, new: SpaceGroup) -> None:
        """Replace the space-group category object."""
        self._space_group = new

    @property
    def atom_sites(self) -> AtomSites:
        """Atom-sites collection for this model."""
        return self._atom_sites

    @atom_sites.setter
    def atom_sites(self, new: AtomSites) -> None:
        """Replace the atom-sites collection."""
        self._atom_sites = new

    # --------------------
    # Symmetry constraints
    # --------------------

    def _apply_cell_symmetry_constraints(self):
        """Apply symmetry rules to unit-cell parameters in place."""
        dummy_cell = {
            'lattice_a': self.cell.length_a.value,
            'lattice_b': self.cell.length_b.value,
            'lattice_c': self.cell.length_c.value,
            'angle_alpha': self.cell.angle_alpha.value,
            'angle_beta': self.cell.angle_beta.value,
            'angle_gamma': self.cell.angle_gamma.value,
        }
        space_group_name = self.space_group.name_h_m.value
        ecr.apply_cell_symmetry_constraints(cell=dummy_cell, name_hm=space_group_name)
        self.cell.length_a.value = dummy_cell['lattice_a']
        self.cell.length_b.value = dummy_cell['lattice_b']
        self.cell.length_c.value = dummy_cell['lattice_c']
        self.cell.angle_alpha.value = dummy_cell['angle_alpha']
        self.cell.angle_beta.value = dummy_cell['angle_beta']
        self.cell.angle_gamma.value = dummy_cell['angle_gamma']

    def _apply_atomic_coordinates_symmetry_constraints(self):
        """Apply symmetry rules to fractional coordinates of atom
        sites.
        """
        space_group_name = self.space_group.name_h_m.value
        space_group_coord_code = self.space_group.it_coordinate_system_code.value
        for atom in self.atom_sites:
            dummy_atom = {
                'fract_x': atom.fract_x.value,
                'fract_y': atom.fract_y.value,
                'fract_z': atom.fract_z.value,
            }
            wl = atom.wyckoff_letter.value
            if not wl:
                # TODO: Decide how to handle this case
                #  For now, we just skip applying constraints if wyckoff
                #  letter is not set. Alternatively, could raise an
                #  error or warning
                #  print(f"Warning: Wyckoff letter is not ...")
                #  raise ValueError("Wyckoff letter is not ...")
                continue
            ecr.apply_atom_site_symmetry_constraints(
                atom_site=dummy_atom,
                name_hm=space_group_name,
                coord_code=space_group_coord_code,
                wyckoff_letter=wl,
            )
            atom.fract_x.value = dummy_atom['fract_x']
            atom.fract_y.value = dummy_atom['fract_y']
            atom.fract_z.value = dummy_atom['fract_z']

    def _apply_atomic_displacement_symmetry_constraints(self):
        """Placeholder for ADP symmetry constraints (not
        implemented).
        """
        pass

    def _apply_symmetry_constraints(self):
        """Apply all available symmetry constraints to this model."""
        self._apply_cell_symmetry_constraints()
        self._apply_atomic_coordinates_symmetry_constraints()
        self._apply_atomic_displacement_symmetry_constraints()

    # ------------
    # Show methods
    # ------------

    def show_structure(self):
        """Show an ASCII projection of the structure on a 2D plane."""
        console.paragraph(f"Sample model 🧩 '{self.name}' structure view")
        console.print('Not implemented yet.')

    def show_params(self):
        """Display structural parameters (space group, cell, atom
        sites).
        """
        console.print(f'\nSampleModel ID: {self.name}')
        console.print(f'Space group: {self.space_group.name_h_m}')
        console.print(f'Cell parameters: {self.cell.as_dict}')
        console.print('Atom sites:')
        self.atom_sites.show()

    def show_as_cif(self) -> None:
        """Render the CIF text for this model in a terminal-friendly
        view.
        """
        cif_text: str = self.as_cif
        paragraph_title: str = f"Sample model 🧩 '{self.name}' as cif"
        console.paragraph(paragraph_title)
        render_cif(cif_text)
