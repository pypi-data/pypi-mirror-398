from easydiffraction import Experiment
from easydiffraction import Experiments
from easydiffraction.utils.logging import logger
from easydiffraction import Project
from easydiffraction import SampleModel
from easydiffraction import SampleModels
from easydiffraction.experiments.categories.linked_phases import LinkedPhase
from easydiffraction.experiments.categories.linked_phases import LinkedPhases
from easydiffraction.sample_models.categories.atom_sites import AtomSite
from easydiffraction.sample_models.categories.atom_sites import AtomSites
from easydiffraction.sample_models.categories.cell import Cell
from easydiffraction.sample_models.categories.space_group import SpaceGroup

Logger.configure(mode=Logger.Mode.LOG, level=Logger.Level.DEBUG)
# Logger.configure(mode=Logger.Mode.RAISE, level=Logger.Level.DEBUG)

sg = SpaceGroup()
sg.name_h_m = 'P n m a'
sg.it_coordinate_system_code = 'cab'

cell = Cell()
cell.length_a = 5.4603

site = AtomSite()
site.type_symbol = 'Si'

sites = AtomSites()
sites.add_from_args(site)

model = SampleModel(name='mdl')
model.space_group = sg
model.cell = cell
model.atom_sites = sites


print(model.parameters)

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


proj = Project(name='PROJ')
print(proj)

proj.sample_models = models
proj.experiments = experiments


# proj.plotter.engine = 'plotly'

proj.plot_meas_vs_calc(expt_name='hrpt', x_min=38, x_max=41)


models['lbco'].cell.length_a.free = True
print('----', models['lbco'].cell.length_a.free)
# proj.analysis.show_free_params()
