import easydiffraction as ed
from easydiffraction import Experiment
from easydiffraction import Experiments
from easydiffraction import Project
from easydiffraction import SampleModel
from easydiffraction import SampleModels
from easydiffraction.experiments.categories.background import LineSegmentBackground
from easydiffraction.experiments.categories.background import Point
from easydiffraction.experiments.categories.linked_phases import LinkedPhase
from easydiffraction.experiments.categories.linked_phases import LinkedPhases
from easydiffraction.sample_models.categories.atom_sites import AtomSite
from easydiffraction.sample_models.categories.atom_sites import AtomSites
from easydiffraction.sample_models.categories.cell import Cell
from easydiffraction.sample_models.categories.space_group import SpaceGroup

# from easydiffraction.core.parameters import BaseDescriptor, GenericDescriptor, Descriptor
# from easydiffraction.core.parameters import BaseParameter, GenericParameter, Parameter

# Logger.configure(mode=Logger.Mode.VERBOSE, level=Logger.Level.DEBUG)
# Logger.configure(mode=Logger.Mode.COMPACT, level=Logger.Level.DEBUG)


# bd = BaseDescriptor()
# gd = GenericDescriptor()
# d = Descriptor()

# bp = BaseParameter()
# gp = GenericParameter()
# p = Parameter()

project = ed.Project()


sg = SpaceGroup()
sg.name_h_m = 'P n m a'
sg.name_h_m = 33.3

sg.it_coordinate_system_code = 'cab'

cell = Cell()
cell.length_a = 5.4603
cell.length_a = '5.4603'
cell.length_a = -5.4603

cell.lengtha = -5.4603


exit()

site = AtomSite()
site.label = 'Si'
site.type_symbol = 'Si'

sites = AtomSites()
sites.add_from_args(site)


model = SampleModel(name='mdl')
model.space_group = sg
model.cell = cell
model.atom_sites = sites

site = AtomSite()
site.label = 'Tb'
site.type_symbol = 'Tb'
sites.add_from_args(site)


# model.cell = 'k'


# print(model.parameters)
for p in model.parameters:
    print(p)

# exit()

print('================================')

models = SampleModels()
# models.add_from_args(model)
models.add_from_cif_path('tutorials/data/lbco.cif')

print(models)
for p in models.parameters:
    print(p)
print(models.as_cif)

exp = Experiment(name='hrpt', data_path='tutorials/data/hrpt_lbco.xye')
print(exp)

linked_phases = LinkedPhases()
linked_phase = LinkedPhase(id='lbco', scale=10.0)
linked_phases.add_from_args(linked_phase)

exp.linked_phases = linked_phases

exp.instrument.setup_wavelength = 1.494
exp.instrument.calib_twotheta_offset = 0.6

exp.peak.broad_gauss_u = 0.1
exp.peak.broad_gauss_v = -0.1
exp.peak.broad_gauss_w = 0.1
exp.peak.broad_lorentz_y = 0.1

bkg = LineSegmentBackground()
point1 = Point(x=10, y=170)
point2 = Point(x=30, y=170)
point3 = Point(x=50, y=170)
point4 = Point(x=110, y=170)
point5 = Point(x=165, y=170)
bkg.add_from_args(point1)
bkg.add_from_args(point2)
bkg.add_from_args(point3)
bkg.add_from_args(point4)
bkg.add_from_args(point5)
# exp.background.add_from_args(bkg)
exp.background = bkg

# exp.background.add_from_args(x=10, y=170)
# exp.background.add_from_args(x=30, y=170)
# exp.background.add_from_args(x=50, y=170)
# exp.background.add_from_args(x=110, y=170)
# exp.background.add_from_args(x=165, y=170)

experiments = Experiments()
print(experiments)

experiments.add(exp)
print(experiments)
for p in experiments.parameters:
    print(p)
# print(experiments.as_cif)
# exit()

proj = Project(name='PROJ')
print(proj)

proj.sample_models = models
proj.experiments = experiments


proj.plot_meas_vs_calc(expt_name='hrpt', x_min=38, x_max=41)


def set_as_online():
    m = proj.sample_models['lbco']
    m.cell.length_a = 3.8909
    m.cell.length_b = 3.8909
    m.cell.length_c = 3.8909
    m.atom_sites['La'].b_iso = 0.5052
    m.atom_sites['Ba'].b_iso = 0.5049
    m.atom_sites['Co'].b_iso = 0.2370
    m.atom_sites['O'].b_iso = 1.3935
    e = proj.experiments['hrpt']
    e.linked_phases['lbco'].scale = 9.1351
    e.instrument.calib_twotheta_offset = 0.6226
    e.peak.broad_gauss_u = 0.0816
    e.peak.broad_gauss_v = -0.1159
    e.peak.broad_gauss_w = 0.1204
    e.peak.broad_lorentz_y = 0.0844
    e.background[10].y = 168.5585
    e.background[30].y = 164.3357
    e.background[50].y = 166.8881
    e.background[110].y = 175.4006
    e.background[165].y = 174.2813


def set_as_initial():
    m = proj.sample_models['lbco']
    m.cell.length_a.uncertainty = None
    m.cell.length_a = 3.885
    m.cell.length_b = 3.885
    m.cell.length_c = 3.885
    # m.atom_sites['La'].b_iso = 0.5052
    # m.atom_sites['Ba'].b_iso = 0.5049
    # m.atom_sites['Co'].b_iso = 0.2370
    # m.atom_sites['O'].b_iso = 1.3935
    # e = proj.experiments['hrpt']
    # e.linked_phases['lbco'].scale = 9.1351
    # e.instrument.calib_twotheta_offset = 0.6226
    # e.peak.broad_gauss_u = 0.0816
    # e.peak.broad_gauss_v = -0.1159
    # e.peak.broad_gauss_w = 0.1204
    # e.peak.broad_lorentz_y = 0.0844
    # e.background[10].y = 168.5585
    # e.background[30].y = 164.3357
    # e.background[50].y = 166.8881
    # e.background[110].y = 175.4006
    # e.background[165].y = 174.2813


set_as_online()
# set_as_initial()
proj.plotter.engine = 'plotly'
proj.plot_meas_vs_calc(expt_name='hrpt', show_residual=True)
# exit()

models['lbco'].cell.length_a.free = True

models['lbco'].atom_sites['La'].b_iso.free = True
models['lbco'].atom_sites['Ba'].b_iso.free = True
models['lbco'].atom_sites['Co'].b_iso.free = True
models['lbco'].atom_sites['O'].b_iso.free = True

exp.instrument.calib_twotheta_offset.free = True

exp.peak.broad_gauss_u.free = True
exp.peak.broad_gauss_v.free = True
exp.peak.broad_gauss_w.free = True
exp.peak.broad_lorentz_y.free = True

exp.background[10].y.free = True
exp.background[30].y.free = True
exp.background[50].y.free = True
exp.background[110].y.free = True
exp.background[165].y.free = True

exp.linked_phases['lbco'].scale.free = True


print('----', models['lbco'].cell.length_a.free)
proj.analysis.show_free_params()
proj.analysis.fit()

# proj.plotter.engine = 'plotly'
# proj.plot_meas_vs_calc(expt_name='hrpt')
proj.plot_meas_vs_calc(expt_name='hrpt', x_min=38, x_max=41)
