from __future__ import annotations

from typing import ParamSpec
from typing import TypeVar

from easydiffraction.analysis.categories.constraints import Constraint
from easydiffraction.analysis.categories.constraints import Constraints
from easydiffraction.sample_models.categories.atom_sites import AtomSite  # type: ignore
from easydiffraction.sample_models.categories.atom_sites import AtomSites  # type: ignore
from easydiffraction.sample_models.categories.cell import Cell  # type: ignore
from easydiffraction.sample_models.categories.space_group import SpaceGroup  # type: ignore
from easydiffraction.sample_models.sample_model.base import SampleModelBase
from easydiffraction.sample_models.sample_model.factory import SampleModel
from easydiffraction.sample_models.sample_models import SampleModels
from easydiffraction.utils.logging import log  # type: ignore

P = ParamSpec('P')
R = TypeVar('R')


# ---------------------------------------------------------------------
# Example usage
# ---------------------------------------------------------------------
if __name__ == '__main__':

    log.info('-------- Types --------')

    s1 = AtomSite(label='La', type_symbol='La')
    s1.fract_x.value = 1.234
    assert s1.fract_x.value == 1.234
    s1.fract_x.value = 'xyz'
    assert s1.fract_x.value == 1.234
    s1.fract_x = 'qwe'
    assert s1.fract_x.value == 1.234

    assert s1.fract_x.free == False
    s1.fract_x.free = True
    assert s1.fract_x.free == True
    s1.fract_x.free = 'abc'
    assert s1.fract_x.free == True

    s1 = AtomSite(label='Si', type_symbol='Si', fract_x='uuuu')
    assert s1.fract_x.value == 0.0

    log.info('-------- Cell --------')

    c = Cell()
    assert c.length_b.value == 10.0
    c = Cell(length_b=-8.8)
    assert c.length_b.value == 10.0
    c = Cell(length_b='7.7')  # type: ignore
    assert c.length_b.value == 10.0
    c = Cell(length_b=6.6)
    assert c.length_b.value == 6.6
    c.length_b.value = -5.5
    assert c.length_b.value == 6.6
    c.length_b = -4.4
    assert c.length_b.value == 6.6
    c.length_b = 3.3
    assert c.length_b.value == 3.3
    c.length_b = 2222.2
    assert c.length_b.value == 3.3
    c.length_b.free = 'qwe'  # type: ignore
    assert c.length_b.free is False
    c.length_b.fre = 'fre'  # type: ignore
    assert getattr(c.length_b, 'fre', None) is None
    c.length_b.qwe = 'qwe'  # type: ignore
    assert getattr(c.length_b, 'qwe', None) is None
    c.length_b.description = 'desc'  # type: ignore
    assert c.length_b.description == 'Length of the b axis of the unit cell.'  # type: ignore
    assert c.length_b._public_readonly_attrs() == {'as_cif', 'constrained',
                                                   'description',
                                                   'unique_name', 'name', 'parameters',
                                                   'uid', 'units'}
    assert c.length_b._public_writable_attrs() == {'fit_max', 'fit_min', 'free', 'uncertainty',
                                                   'value'}
    c.qwe = 'qwe'
    assert getattr(c.length_b, 'qwe', None) is None
    assert c.length_b._cif_handler.names == ['_cell.length_b']
    assert len(c.length_b._minimizer_uid) == 16
    assert (c.parameters[1].value == 3.3)  # type: ignore

    log.info('-------- SpaceGroup --------')

    sg = SpaceGroup()
    assert sg.name_h_m.value == 'P 1'
    sg = SpaceGroup(name_h_m='qwe')
    assert sg.name_h_m.value == 'P 1'
    sg = SpaceGroup(name_h_m='P b n m', it_coordinate_system_code='cab')
    assert sg.name_h_m.value == 'P 1'
    assert sg.it_coordinate_system_code.value == ''
    sg = SpaceGroup(name_h_m='P n m a', it_coordinate_system_code='cab')
    assert sg.name_h_m.value == 'P n m a'
    assert sg.it_coordinate_system_code.value == 'cab'
    sg.name_h_m = 34.9
    assert sg.name_h_m.value == 'P n m a'
    sg.name_h_m = 'P 1'
    assert sg.name_h_m.value == 'P 1'
    assert sg.it_coordinate_system_code.value == ''
    sg.name_h_m = 'P n m a'
    assert sg.name_h_m.value == 'P n m a'
    assert sg.it_coordinate_system_code.value == 'abc'

    log.info('-------- AtomSites --------')

    s1 = AtomSite(label='La', type_symbol='La')
    assert s1.label.value == 'La'
    assert s1.type_symbol.value == 'La'
    s2 = AtomSite(label='Si', type_symbol='Si')
    assert s2.label.value == 'Si'
    assert s2.type_symbol.value == 'Si'
    sites = AtomSites()
    assert len(sites) == 0
    sites.add(s1)
    sites.add(s2)
    assert len(sites) == 2
    s1.label = 'Tb'
    assert s1.label.value == 'Tb'
    assert list(sites.keys()) == ['Tb', 'Si']
    assert sites['Tb'] is s1
    assert sites['Tb'].fract_x.value == 0.0
    s2.fract_x.value = 0.123
    assert s2.fract_x.value == 0.123
    s2.fract_x = 0.456
    assert s2.fract_x.value == 0.456
    sites['Tb'].fract_x = 0.789
    assert sites['Tb'].fract_x.value == 0.789
    sites['Tb'].qwe = 'qwe'  # type: ignore
    assert getattr(sites['Tb'], 'qwe', None) is None
    sites.abc = 'abc'  # type: ignore
    assert getattr(sites, 'abc', None) is None
    sites['Tb'].label = 'a b c'
    assert sites['Tb'].label.value == 'Tb'

    assert sites['Tb']._label.value == 'Tb'
    assert sites['Tb'].label.value == 'Tb'
    assert sites['Tb'].name is None

    log.info('-------- SampleModel --------')

    model = SampleModel(name='lbco')
    assert model.name == 'lbco'
    assert model.cell.length_b.value == 10.0
    assert len(model.atom_sites) == 0
    model.atom_sites.add(s1)
    model.atom_sites.add(s2)
    assert len(model.atom_sites) == 2
    assert model.atom_sites.names == ['Tb', 'Si']
    assert model.atom_sites._items[0].label.value == 'Tb'
    assert model.atom_sites._items[1].label.value == 'Si'

    log.info('-------- SampleModels --------')

    models = SampleModels()
    assert len(models) == 0
    models.add(model)
    assert len(models) == 1
    assert models._items[0].name == 'lbco'

    log.info('-------- PARENTS --------')

    assert models._parent is None
    assert type(models['lbco']._parent) is SampleModels
    assert type(models['lbco'].cell._parent) is SampleModelBase
    assert type(models['lbco'].cell.length_b._parent) is Cell
    assert type(models['lbco'].atom_sites._parent) is SampleModelBase
    assert type(models['lbco'].atom_sites['Tb']._parent) is AtomSites
    assert type(models['lbco'].atom_sites['Tb'].fract_x._parent) is AtomSite

    assert type(s1._parent) is AtomSites
    assert type(models['lbco'].atom_sites) is AtomSites
    assert len(models['lbco'].atom_sites) == 2
    del models['lbco'].atom_sites['Tb']
    assert len(models['lbco'].atom_sites) == 1
    assert s1._parent is None
    assert type(models['lbco'].atom_sites) is AtomSites

    log.info('-------- PARAMETERS --------')

    assert len(models['lbco'].atom_sites['Si'].parameters) == 9
    assert models['lbco'].atom_sites['Si'].parameters[0].value == 'Si'
    assert len(models['lbco'].atom_sites.parameters) == 9
    assert len(models['lbco'].cell.parameters) == 6
    assert len(models['lbco'].parameters) == 17
    assert len(models.parameters) == 17

    log.info('-------- CIF HANDLERS --------')

    s3 = AtomSite(label='La', type_symbol='La')
    assert s3.label.value == 'La'
    assert s3.type_symbol.value == 'La'

    assert len(models['lbco'].atom_sites) == 1
    models['lbco'].atom_sites.add(s3)
    assert len(models['lbco'].atom_sites) == 2
    assert models['lbco'].cell.length_b.as_cif == '_cell.length_b 10.0'
    assert models['lbco'].cell.as_cif == """_cell.length_a 10.0
_cell.length_b 10.0
_cell.length_c 10.0
_cell.angle_alpha 90.0
_cell.angle_beta 90.0
_cell.angle_gamma 90.0"""

    assert models['lbco'].atom_sites.as_cif == """loop_
_atom_site.label
_atom_site.type_symbol
_atom_site.fract_x
_atom_site.fract_y
_atom_site.fract_z
_atom_site.Wyckoff_letter
_atom_site.occupancy
_atom_site.B_iso_or_equiv
_atom_site.adp_type
Si Si 0.456 0.0 0.0 a 1.0 0.0 Biso
La La 0.0 0.0 0.0 a 1.0 0.0 Biso"""

    print(models['lbco'].as_cif)

    assert models['lbco'].as_cif == """data_lbco

_cell.length_a 10.0
_cell.length_b 10.0
_cell.length_c 10.0
_cell.angle_alpha 90.0
_cell.angle_beta 90.0
_cell.angle_gamma 90.0

_space_group.name_H-M_alt "P 1"
_space_group.IT_coordinate_system_code 

loop_
_atom_site.label
_atom_site.type_symbol
_atom_site.fract_x
_atom_site.fract_y
_atom_site.fract_z
_atom_site.Wyckoff_letter
_atom_site.occupancy
_atom_site.B_iso_or_equiv
_atom_site.adp_type
Si Si 0.456 0.0 0.0 a 1.0 0.0 Biso
La La 0.0 0.0 0.0 a 1.0 0.0 Biso"""

    assert models.as_cif == """data_lbco

_cell.length_a 10.0
_cell.length_b 10.0
_cell.length_c 10.0
_cell.angle_alpha 90.0
_cell.angle_beta 90.0
_cell.angle_gamma 90.0

_space_group.name_H-M_alt "P 1"
_space_group.IT_coordinate_system_code 

loop_
_atom_site.label
_atom_site.type_symbol
_atom_site.fract_x
_atom_site.fract_y
_atom_site.fract_z
_atom_site.Wyckoff_letter
_atom_site.occupancy
_atom_site.B_iso_or_equiv
_atom_site.adp_type
Si Si 0.456 0.0 0.0 a 1.0 0.0 Biso
La La 0.0 0.0 0.0 a 1.0 0.0 Biso"""

    log.info('-------- Full Names --------')

    cell = Cell()
    assert cell.unique_name == 'cell'

    assert cell.length_b.unique_name == 'cell.length_b'

    site = AtomSite(label='Tb', type_symbol='Tb')
    assert site.unique_name == 'atom_site.Tb'

    sites = AtomSites()  #
    assert sites.unique_name is None

    sites.add(site)
    assert site.unique_name == 'atom_site.Tb'
    assert sites['Tb'].unique_name == 'atom_site.Tb'

    model = SampleModel(name='lbco')  #
    assert model.unique_name == 'lbco'

    model.cell = cell
    assert cell.unique_name == 'lbco.cell'
    assert cell.length_b.unique_name == 'lbco.cell.length_b'
    assert model.cell.unique_name == 'lbco.cell'
    assert model.cell.length_b.unique_name == 'lbco.cell.length_b'

    model.atom_sites = sites
    assert sites.unique_name is None
    assert model.atom_sites.unique_name is None
    assert model.atom_sites['Tb'].unique_name == 'lbco.atom_site.Tb'

    models = SampleModels()  #
    assert models.unique_name is None

    models.add(model)
    assert models['lbco'].cell.unique_name == 'lbco.cell'
    assert models['lbco'].cell.length_b.unique_name == 'lbco.cell.length_b'
    assert models['lbco'].atom_sites.unique_name is None
    assert models['lbco'].atom_sites['Tb'].unique_name == 'lbco.atom_site.Tb'

    log.info('-------- Constraints --------')
    con = Constraint(lhs_alias='cell.length_a', rhs_expr='2 * cell.length_b + 1.0')
    assert con.lhs_alias.value == 'cell.length_a'
    assert con.rhs_expr.value == '2 * cell.length_b + 1.0'
    cons = Constraints()
    assert len(cons) == 0
    cons.add(con)
    assert len(cons) == 1
