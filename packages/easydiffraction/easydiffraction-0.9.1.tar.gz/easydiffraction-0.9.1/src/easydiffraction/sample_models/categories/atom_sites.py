# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Atom site category.

Defines AtomSite items and AtomSites collection used in sample models.
Only documentation was added; behavior remains unchanged.
"""

from cryspy.A_functions_base.database import DATABASE

from easydiffraction.core.category import CategoryCollection
from easydiffraction.core.category import CategoryItem
from easydiffraction.core.parameters import Parameter
from easydiffraction.core.parameters import StringDescriptor
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import DataTypes
from easydiffraction.core.validation import MembershipValidator
from easydiffraction.core.validation import RangeValidator
from easydiffraction.core.validation import RegexValidator
from easydiffraction.crystallography import crystallography as ecr
from easydiffraction.io.cif.handler import CifHandler


class AtomSite(CategoryItem):
    """Single atom site with fractional coordinates and ADP.

    Attributes are represented by descriptors to support validation and
    CIF serialization.
    """

    def __init__(
        self,
        *,
        label=None,
        type_symbol=None,
        fract_x=None,
        fract_y=None,
        fract_z=None,
        wyckoff_letter=None,
        occupancy=None,
        b_iso=None,
        adp_type=None,
    ) -> None:
        super().__init__()

        self._label: StringDescriptor = StringDescriptor(
            name='label',
            description='Unique identifier for the atom site.',
            value_spec=AttributeSpec(
                value=label,
                type_=DataTypes.STRING,
                default='Si',
                # TODO: the following pattern is valid for dict key
                #  (keywords are not checked). CIF label is less strict.
                #  Do we need conversion between CIF and internal label?
                content_validator=RegexValidator(pattern=r'^[A-Za-z_][A-Za-z0-9_]*$'),
            ),
            cif_handler=CifHandler(
                names=[
                    '_atom_site.label',
                ]
            ),
        )
        self._type_symbol: StringDescriptor = StringDescriptor(
            name='type_symbol',
            description='Chemical symbol of the atom at this site.',
            value_spec=AttributeSpec(
                value=type_symbol,
                type_=DataTypes.STRING,
                default='Tb',
                content_validator=MembershipValidator(allowed=self._type_symbol_allowed_values),
            ),
            cif_handler=CifHandler(
                names=[
                    '_atom_site.type_symbol',
                ]
            ),
        )
        self._fract_x: Parameter = Parameter(
            name='fract_x',
            description='Fractional x-coordinate of the atom site within the unit cell.',
            value_spec=AttributeSpec(
                value=fract_x,
                type_=DataTypes.NUMERIC,
                default=0.0,
                content_validator=RangeValidator(),
            ),
            cif_handler=CifHandler(
                names=[
                    '_atom_site.fract_x',
                ]
            ),
        )
        self._fract_y: Parameter = Parameter(
            name='fract_y',
            description='Fractional y-coordinate of the atom site within the unit cell.',
            value_spec=AttributeSpec(
                value=fract_y,
                type_=DataTypes.NUMERIC,
                default=0.0,
                content_validator=RangeValidator(),
            ),
            cif_handler=CifHandler(
                names=[
                    '_atom_site.fract_y',
                ]
            ),
        )
        self._fract_z: Parameter = Parameter(
            name='fract_z',
            description='Fractional z-coordinate of the atom site within the unit cell.',
            value_spec=AttributeSpec(
                value=fract_z,
                type_=DataTypes.NUMERIC,
                default=0.0,
                content_validator=RangeValidator(),
            ),
            cif_handler=CifHandler(
                names=[
                    '_atom_site.fract_z',
                ]
            ),
        )
        self._wyckoff_letter: StringDescriptor = StringDescriptor(
            name='wyckoff_letter',
            description='Wyckoff letter indicating the symmetry of the '
            'atom site within the space group.',
            value_spec=AttributeSpec(
                value=wyckoff_letter,
                type_=DataTypes.STRING,
                default=self._wyckoff_letter_default_value,
                content_validator=MembershipValidator(allowed=self._wyckoff_letter_allowed_values),
            ),
            cif_handler=CifHandler(
                names=[
                    '_atom_site.Wyckoff_letter',
                    '_atom_site.Wyckoff_symbol',
                ]
            ),
        )
        self._occupancy: Parameter = Parameter(
            name='occupancy',
            description='Occupancy of the atom site, representing the '
            'fraction of the site occupied by the atom type.',
            value_spec=AttributeSpec(
                value=occupancy,
                type_=DataTypes.NUMERIC,
                default=1.0,
                content_validator=RangeValidator(),
            ),
            cif_handler=CifHandler(
                names=[
                    '_atom_site.occupancy',
                ]
            ),
        )
        self._b_iso: Parameter = Parameter(
            name='b_iso',
            description='Isotropic atomic displacement parameter (ADP) for the atom site.',
            value_spec=AttributeSpec(
                value=b_iso,
                type_=DataTypes.NUMERIC,
                default=0.0,
                content_validator=RangeValidator(ge=0.0),
            ),
            units='Å²',
            cif_handler=CifHandler(
                names=[
                    '_atom_site.B_iso_or_equiv',
                ]
            ),
        )
        self._adp_type: StringDescriptor = StringDescriptor(
            name='adp_type',
            description='Type of atomic displacement parameter (ADP) '
            'used (e.g., Biso, Uiso, Uani, Bani).',
            value_spec=AttributeSpec(
                value=adp_type,
                type_=DataTypes.STRING,
                default='Biso',
                content_validator=MembershipValidator(allowed=['Biso']),
            ),
            cif_handler=CifHandler(
                names=[
                    '_atom_site.adp_type',
                ]
            ),
        )

        self._identity.category_code = 'atom_site'
        self._identity.category_entry_name = lambda: str(self.label.value)

    @property
    def _type_symbol_allowed_values(self):
        return list({key[1] for key in DATABASE['Isotopes']})

    @property
    def _wyckoff_letter_allowed_values(self):
        # TODO: Need to now current space group. How to access it? Via
        #  parent Cell? Then letters =
        #  list(SPACE_GROUPS[62, 'cab']['Wyckoff_positions'].keys())
        #  Temporarily return hardcoded list:
        return ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i']

    @property
    def _wyckoff_letter_default_value(self):
        # TODO: What to pass as default?
        return self._wyckoff_letter_allowed_values[0]

    @property
    def label(self):
        """Label descriptor for the site (unique key)."""
        return self._label

    @label.setter
    def label(self, value):
        self._label.value = value

    @property
    def type_symbol(self):
        """Chemical symbol descriptor (e.g. 'Si')."""
        return self._type_symbol

    @type_symbol.setter
    def type_symbol(self, value):
        self._type_symbol.value = value

    @property
    def adp_type(self):
        """ADP type descriptor (e.g. 'Biso')."""
        return self._adp_type

    @adp_type.setter
    def adp_type(self, value):
        self._adp_type.value = value

    @property
    def wyckoff_letter(self):
        """Wyckoff letter descriptor (space-group position)."""
        return self._wyckoff_letter

    @wyckoff_letter.setter
    def wyckoff_letter(self, value):
        self._wyckoff_letter.value = value

    @property
    def fract_x(self):
        """Fractional x coordinate descriptor."""
        return self._fract_x

    @fract_x.setter
    def fract_x(self, value):
        self._fract_x.value = value

    @property
    def fract_y(self):
        """Fractional y coordinate descriptor."""
        return self._fract_y

    @fract_y.setter
    def fract_y(self, value):
        self._fract_y.value = value

    @property
    def fract_z(self):
        """Fractional z coordinate descriptor."""
        return self._fract_z

    @fract_z.setter
    def fract_z(self, value):
        self._fract_z.value = value

    @property
    def occupancy(self):
        """Occupancy descriptor (0..1)."""
        return self._occupancy

    @occupancy.setter
    def occupancy(self, value):
        self._occupancy.value = value

    @property
    def b_iso(self):
        """Isotropic ADP descriptor in Å²."""
        return self._b_iso

    @b_iso.setter
    def b_iso(self, value):
        self._b_iso.value = value


class AtomSites(CategoryCollection):
    """Collection of AtomSite instances."""

    def __init__(self):
        super().__init__(item_type=AtomSite)

    def _apply_atomic_coordinates_symmetry_constraints(self):
        """Apply symmetry rules to fractional coordinates of atom
        sites.
        """
        sample_model = self._parent
        space_group_name = sample_model.space_group.name_h_m.value
        space_group_coord_code = sample_model.space_group.it_coordinate_system_code.value
        for atom in self._items:
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

    def _update(self, called_by_minimizer=False):
        """Update atom sites by applying symmetry constraints."""
        del called_by_minimizer

        self._apply_atomic_coordinates_symmetry_constraints()
