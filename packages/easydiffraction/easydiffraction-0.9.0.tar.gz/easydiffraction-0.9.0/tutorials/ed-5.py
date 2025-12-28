# %% [markdown]
# # Structure Refinement: Co2SiO4, D20
#
# This example demonstrates a Rietveld refinement of Co2SiO4 crystal
# structure using constant wavelength neutron powder diffraction data
# from D20 at ILL.

# %% [markdown]
# ## Import Library

# %%
from easydiffraction import ExperimentFactory
from easydiffraction import Project
from easydiffraction import SampleModelFactory
from easydiffraction import download_data

# %% [markdown]
# ## Define Sample Model
#
# This section shows how to add sample models and modify their
# parameters.
#
# #### Create Sample Model

# %%
model = SampleModelFactory.create(name='cosio')

# %% [markdown]
# #### Set Space Group

# %%
model.space_group.name_h_m = 'P n m a'
model.space_group.it_coordinate_system_code = 'abc'

# %% [markdown]
# #### Set Unit Cell

# %%
model.cell.length_a = 10.3
model.cell.length_b = 6.0
model.cell.length_c = 4.8

# %% [markdown]
# #### Set Atom Sites

# %%
model.atom_sites.add(
    label='Co1',
    type_symbol='Co',
    fract_x=0,
    fract_y=0,
    fract_z=0,
    wyckoff_letter='a',
    b_iso=0.5,
)
model.atom_sites.add(
    label='Co2',
    type_symbol='Co',
    fract_x=0.279,
    fract_y=0.25,
    fract_z=0.985,
    wyckoff_letter='c',
    b_iso=0.5,
)
model.atom_sites.add(
    label='Si',
    type_symbol='Si',
    fract_x=0.094,
    fract_y=0.25,
    fract_z=0.429,
    wyckoff_letter='c',
    b_iso=0.5,
)
model.atom_sites.add(
    label='O1',
    type_symbol='O',
    fract_x=0.091,
    fract_y=0.25,
    fract_z=0.771,
    wyckoff_letter='c',
    b_iso=0.5,
)
model.atom_sites.add(
    label='O2',
    type_symbol='O',
    fract_x=0.448,
    fract_y=0.25,
    fract_z=0.217,
    wyckoff_letter='c',
    b_iso=0.5,
)
model.atom_sites.add(
    label='O3',
    type_symbol='O',
    fract_x=0.164,
    fract_y=0.032,
    fract_z=0.28,
    wyckoff_letter='d',
    b_iso=0.5,
)

# %% [markdown]
# ## Define Experiment
#
# This section shows how to add experiments, configure their parameters,
# and link the sample models defined in the previous step.
#
# #### Download Measured Data

# %%
data_path = download_data(id=12, destination='data')

# %% [markdown]
# #### Create Experiment

# %%
expt = ExperimentFactory.create(name='d20', data_path=data_path)

# %% [markdown]
# #### Set Instrument

# %%
expt.instrument.setup_wavelength = 1.87
expt.instrument.calib_twotheta_offset = 0.1

# %% [markdown]
# #### Set Peak Profile

# %%
expt.peak.broad_gauss_u = 0.3
expt.peak.broad_gauss_v = -0.5
expt.peak.broad_gauss_w = 0.4

# %% [markdown]
# #### Set Background

# %%
expt.background.add(id='1', x=8, y=500)
expt.background.add(id='2', x=9, y=500)
expt.background.add(id='3', x=10, y=500)
expt.background.add(id='4', x=11, y=500)
expt.background.add(id='5', x=12, y=500)
expt.background.add(id='6', x=15, y=500)
expt.background.add(id='7', x=25, y=500)
expt.background.add(id='8', x=30, y=500)
expt.background.add(id='9', x=50, y=500)
expt.background.add(id='10', x=70, y=500)
expt.background.add(id='11', x=90, y=500)
expt.background.add(id='12', x=110, y=500)
expt.background.add(id='13', x=130, y=500)
expt.background.add(id='14', x=150, y=500)

# %% [markdown]
# #### Set Linked Phases

# %%
expt.linked_phases.add(id='cosio', scale=1.0)

# %% [markdown]
# ## Define Project
#
# The project object is used to manage the sample model, experiment, and
# analysis.
#
# #### Create Project

# %%
project = Project()

# %% [markdown]
# #### Set Plotting Engine

# %%
# Keep the auto-selected engine. Alternatively, you can uncomment the
# line below to explicitly set the engine to the required one.
# project.plotter.engine = 'plotly'

# %% [markdown]
# #### Add Sample Model

# %%
project.sample_models.add(sample_model=model)

# %% [markdown]
# #### Add Experiment

# %%
project.experiments.add(experiment=expt)

# %% [markdown]
# ## Perform Analysis
#
# This section shows the analysis process, including how to set up
# calculation and fitting engines.
#
# #### Set Calculator

# %%
project.analysis.current_calculator = 'cryspy'

# %% [markdown]
# #### Set Minimizer

# %%
project.analysis.current_minimizer = 'lmfit (leastsq)'

# %% [markdown]
# #### Plot Measured vs Calculated

# %%
project.plot_meas_vs_calc(expt_name='d20', show_residual=True)

# %%
project.plot_meas_vs_calc(expt_name='d20', x_min=41, x_max=54, show_residual=True)

# %% [markdown]
# #### Set Free Parameters

# %%
model.cell.length_a.free = True
model.cell.length_b.free = True
model.cell.length_c.free = True

model.atom_sites['Co2'].fract_x.free = True
model.atom_sites['Co2'].fract_z.free = True
model.atom_sites['Si'].fract_x.free = True
model.atom_sites['Si'].fract_z.free = True
model.atom_sites['O1'].fract_x.free = True
model.atom_sites['O1'].fract_z.free = True
model.atom_sites['O2'].fract_x.free = True
model.atom_sites['O2'].fract_z.free = True
model.atom_sites['O3'].fract_x.free = True
model.atom_sites['O3'].fract_y.free = True
model.atom_sites['O3'].fract_z.free = True

model.atom_sites['Co1'].b_iso.free = True
model.atom_sites['Co2'].b_iso.free = True
model.atom_sites['Si'].b_iso.free = True
model.atom_sites['O1'].b_iso.free = True
model.atom_sites['O2'].b_iso.free = True
model.atom_sites['O3'].b_iso.free = True

# %%
expt.linked_phases['cosio'].scale.free = True

expt.instrument.calib_twotheta_offset.free = True

expt.peak.broad_gauss_u.free = True
expt.peak.broad_gauss_v.free = True
expt.peak.broad_gauss_w.free = True
expt.peak.broad_lorentz_y.free = True

for point in expt.background:
    point.y.free = True

# %% [markdown]
# #### Set Constraints
#
# Set aliases for parameters.

# %%
project.analysis.aliases.add(
    label='biso_Co1',
    param_uid=project.sample_models['cosio'].atom_sites['Co1'].b_iso.uid,
)
project.analysis.aliases.add(
    label='biso_Co2',
    param_uid=project.sample_models['cosio'].atom_sites['Co2'].b_iso.uid,
)

# %% [markdown]
# Set constraints.

# %%
project.analysis.constraints.add(
    lhs_alias='biso_Co2',
    rhs_expr='biso_Co1',
)

# %% [markdown]
# Apply constraints.

# %%
project.analysis.apply_constraints()

# %% [markdown]
# #### Run Fitting

# %%
project.analysis.fit()

# %% [markdown]
# #### Plot Measured vs Calculated

# %%
project.plot_meas_vs_calc(expt_name='d20', show_residual=True)

# %%
project.plot_meas_vs_calc(expt_name='d20', x_min=41, x_max=54, show_residual=True)

# %% [markdown]
# ## Summary
#
# This final section shows how to review the results of the analysis.

# %% [markdown]
# #### Show Project Summary

# %%
project.summary.show_report()
