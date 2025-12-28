# %% [markdown]
# # Structure Refinement: LBCO+Si, McStas
#
# This example demonstrates a Rietveld refinement of La0.5Ba0.5CoO3
# crystal structure with a small amount of Si phase using time-of-flight
# neutron powder diffraction data simulated with McStas.

# %% [markdown]
# ## Import Library

# %%
from easydiffraction import ExperimentFactory
from easydiffraction import Project
from easydiffraction import SampleModelFactory
from easydiffraction import download_data

# %% [markdown]
# ## Define Sample Models
#
# This section shows how to add sample models and modify their
# parameters.
#
# ### Create Sample Model 1: LBCO

# %%
model_1 = SampleModelFactory.create(name='lbco')

# %% [markdown]
# #### Set Space Group

# %%
model_1.space_group.name_h_m = 'P m -3 m'
model_1.space_group.it_coordinate_system_code = '1'

# %% [markdown]
# #### Set Unit Cell

# %%
model_1.cell.length_a = 3.8909

# %% [markdown]
# #### Set Atom Sites

# %%
model_1.atom_sites.add(
    label='La',
    type_symbol='La',
    fract_x=0,
    fract_y=0,
    fract_z=0,
    wyckoff_letter='a',
    b_iso=0.2,
    occupancy=0.5,
)
model_1.atom_sites.add(
    label='Ba',
    type_symbol='Ba',
    fract_x=0,
    fract_y=0,
    fract_z=0,
    wyckoff_letter='a',
    b_iso=0.2,
    occupancy=0.5,
)
model_1.atom_sites.add(
    label='Co',
    type_symbol='Co',
    fract_x=0.5,
    fract_y=0.5,
    fract_z=0.5,
    wyckoff_letter='b',
    b_iso=0.2567,
)
model_1.atom_sites.add(
    label='O',
    type_symbol='O',
    fract_x=0,
    fract_y=0.5,
    fract_z=0.5,
    wyckoff_letter='c',
    b_iso=1.4041,
)

# %% [markdown]
# ### Create Sample Model 2: Si

# %%
model_2 = SampleModelFactory.create(name='si')

# %% [markdown]
# #### Set Space Group

# %%
model_2.space_group.name_h_m = 'F d -3 m'
model_2.space_group.it_coordinate_system_code = '2'

# %% [markdown]
# #### Set Unit Cell

# %%
model_2.cell.length_a = 5.43146

# %% [markdown]
# #### Set Atom Sites

# %%
model_2.atom_sites.add(
    label='Si',
    type_symbol='Si',
    fract_x=0.0,
    fract_y=0.0,
    fract_z=0.0,
    wyckoff_letter='a',
    b_iso=0.0,
)

# %% [markdown]
# ## Define Experiment
#
# This section shows how to add experiments, configure their parameters,
# and link the sample models defined in the previous step.
#
# #### Download Data

# %%
data_path = download_data(id=8, destination='data')

# %% [markdown]
# #### Create Experiment

# %%
experiment = ExperimentFactory.create(
    name='mcstas',
    data_path=data_path,
    sample_form='powder',
    beam_mode='time-of-flight',
    radiation_probe='neutron',
    scattering_type='bragg',
)

# %% [markdown]
# #### Set Instrument

# %%
experiment.instrument.setup_twotheta_bank = 94.90931761529106
experiment.instrument.calib_d_to_tof_offset = 0.0
experiment.instrument.calib_d_to_tof_linear = 58724.76869981215
experiment.instrument.calib_d_to_tof_quad = -0.00001

# %% [markdown]
# #### Set Peak Profile

# %%
# experiment.peak_profile_type = 'pseudo-voigt * ikeda-carpenter'
experiment.peak.broad_gauss_sigma_0 = 45137
experiment.peak.broad_gauss_sigma_1 = -52394
experiment.peak.broad_gauss_sigma_2 = 22998
experiment.peak.broad_mix_beta_0 = 0.0055
experiment.peak.broad_mix_beta_1 = 0.0041
experiment.peak.asym_alpha_0 = 0
experiment.peak.asym_alpha_1 = 0.0097

# %% [markdown]
# #### Set Background

# %% [markdown]
# Select the background type.

# %%
experiment.background_type = 'line-segment'

# %% [markdown]
# Add background points.

# %%
experiment.background.add(id='1', x=45000, y=0.2)
experiment.background.add(id='2', x=50000, y=0.2)
experiment.background.add(id='3', x=55000, y=0.2)
experiment.background.add(id='4', x=65000, y=0.2)
experiment.background.add(id='5', x=70000, y=0.2)
experiment.background.add(id='6', x=75000, y=0.2)
experiment.background.add(id='7', x=80000, y=0.2)
experiment.background.add(id='8', x=85000, y=0.2)
experiment.background.add(id='9', x=90000, y=0.2)
experiment.background.add(id='10', x=95000, y=0.2)
experiment.background.add(id='11', x=100000, y=0.2)
experiment.background.add(id='12', x=105000, y=0.2)
experiment.background.add(id='13', x=110000, y=0.2)

# %% [markdown]
# #### Set Linked Phases

# %%
experiment.linked_phases.add(id='lbco', scale=4.0)
experiment.linked_phases.add(id='si', scale=0.2)

# %% [markdown]
# ## Define Project
#
# The project object is used to manage sample models, experiments, and
# analysis.
#
# #### Create Project

# %%
project = Project()

# %% [markdown]
# #### Add Sample Models

# %%
project.sample_models.add(sample_model=model_1)
project.sample_models.add(sample_model=model_2)

# %% [markdown]
# #### Show Sample Models

# %%
project.sample_models.show_names()

# %% [markdown]
# #### Add Experiments

# %%
project.experiments.add(experiment=experiment)

# %% [markdown]
# #### Set Excluded Regions
#
# Show measured data as loaded from the file.

# %%
project.plot_meas(expt_name='mcstas')

# %% [markdown]
# Add excluded regions.

# %%
experiment.excluded_regions.add(id='1', start=0, end=40000)
experiment.excluded_regions.add(id='2', start=108000, end=200000)

# %% [markdown]
# Show excluded regions.

# %%
experiment.excluded_regions.show()

# %% [markdown]
# Show measured data after adding excluded regions.

# %%
project.plot_meas(expt_name='mcstas')

# %% [markdown]
# Show experiment as CIF.

# %%
project.experiments['mcstas'].show_as_cif()

# %% [markdown]
# ## Perform Analysis
#
# This section outlines the analysis process, including how to configure
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
# #### Set Fitting Parameters
#
# Set sample model parameters to be optimized.

# %%
model_1.cell.length_a.free = True
model_1.atom_sites['Co'].b_iso.free = True
model_1.atom_sites['O'].b_iso.free = True

model_2.cell.length_a.free = True

# %% [markdown]
# Set experiment parameters to be optimized.

# %%
experiment.linked_phases['lbco'].scale.free = True
experiment.linked_phases['si'].scale.free = True

experiment.peak.broad_gauss_sigma_0.free = True
experiment.peak.broad_gauss_sigma_1.free = True
experiment.peak.broad_gauss_sigma_2.free = True

experiment.peak.asym_alpha_1.free = True
experiment.peak.broad_mix_beta_0.free = True
experiment.peak.broad_mix_beta_1.free = True

for point in experiment.background:
    point.y.free = True

# %% [markdown]
# #### Perform Fit

# %%
project.analysis.fit()

# %% [markdown]
# #### Plot Measured vs Calculated

# %%
project.plot_meas_vs_calc(expt_name='mcstas')

# %%
