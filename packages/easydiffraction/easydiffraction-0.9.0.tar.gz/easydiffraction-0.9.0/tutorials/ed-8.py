# %% [markdown]
# # Structure Refinement: NCAF, WISH
#
# This example demonstrates a Rietveld refinement of Na2Ca3Al2F14
# crystal structure using time-of-flight neutron powder diffraction data
# from WISH at ISIS.
#
# Two datasets from detector banks 5+6 and 4+7 are used for joint
# fitting.

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
# This section covers how to add sample models and modify their
# parameters.
#
# #### Create Sample Model

# %%
model = SampleModelFactory.create(name='ncaf')

# %% [markdown]
# #### Set Space Group

# %%
model.space_group.name_h_m = 'I 21 3'
model.space_group.it_coordinate_system_code = '1'

# %% [markdown]
# #### Set Unit Cell

# %%
model.cell.length_a = 10.250256

# %% [markdown]
# #### Set Atom Sites

# %%
model.atom_sites.add(
    label='Ca',
    type_symbol='Ca',
    fract_x=0.4663,
    fract_y=0.0,
    fract_z=0.25,
    wyckoff_letter='b',
    b_iso=0.92,
)
model.atom_sites.add(
    label='Al',
    type_symbol='Al',
    fract_x=0.2521,
    fract_y=0.2521,
    fract_z=0.2521,
    wyckoff_letter='a',
    b_iso=0.73,
)
model.atom_sites.add(
    label='Na',
    type_symbol='Na',
    fract_x=0.0851,
    fract_y=0.0851,
    fract_z=0.0851,
    wyckoff_letter='a',
    b_iso=2.08,
)
model.atom_sites.add(
    label='F1',
    type_symbol='F',
    fract_x=0.1377,
    fract_y=0.3054,
    fract_z=0.1195,
    wyckoff_letter='c',
    b_iso=0.90,
)
model.atom_sites.add(
    label='F2',
    type_symbol='F',
    fract_x=0.3625,
    fract_y=0.3633,
    fract_z=0.1867,
    wyckoff_letter='c',
    b_iso=1.37,
)
model.atom_sites.add(
    label='F3',
    type_symbol='F',
    fract_x=0.4612,
    fract_y=0.4612,
    fract_z=0.4612,
    wyckoff_letter='a',
    b_iso=0.88,
)

# %% [markdown]
# ## Define Experiment
#
# This section shows how to add experiments, configure their parameters,
# and link the sample models defined in the previous step.
#
# #### Download Measured Data

# %%
data_path56 = download_data(id=9, destination='data')

# %%
data_path47 = download_data(id=10, destination='data')

# %% [markdown]
# #### Create Experiment

# %%
expt56 = ExperimentFactory.create(
    name='wish_5_6',
    data_path=data_path56,
    beam_mode='time-of-flight',
)

# %%
expt47 = ExperimentFactory.create(
    name='wish_4_7',
    data_path=data_path47,
    beam_mode='time-of-flight',
)

# %% [markdown]
# #### Set Instrument

# %%
expt56.instrument.setup_twotheta_bank = 152.827
expt56.instrument.calib_d_to_tof_offset = -13.5
expt56.instrument.calib_d_to_tof_linear = 20773.0
expt56.instrument.calib_d_to_tof_quad = -1.08308

# %%
expt47.instrument.setup_twotheta_bank = 121.660
expt47.instrument.calib_d_to_tof_offset = -15.0
expt47.instrument.calib_d_to_tof_linear = 18660.0
expt47.instrument.calib_d_to_tof_quad = -0.47488

# %% [markdown]
# #### Set Peak Profile

# %%
expt56.peak.broad_gauss_sigma_0 = 0.0
expt56.peak.broad_gauss_sigma_1 = 0.0
expt56.peak.broad_gauss_sigma_2 = 15.5
expt56.peak.broad_mix_beta_0 = 0.007
expt56.peak.broad_mix_beta_1 = 0.01
expt56.peak.asym_alpha_0 = -0.0094
expt56.peak.asym_alpha_1 = 0.1

# %%
expt47.peak.broad_gauss_sigma_0 = 0.0
expt47.peak.broad_gauss_sigma_1 = 29.8
expt47.peak.broad_gauss_sigma_2 = 18.0
expt47.peak.broad_mix_beta_0 = 0.006
expt47.peak.broad_mix_beta_1 = 0.015
expt47.peak.asym_alpha_0 = -0.0115
expt47.peak.asym_alpha_1 = 0.1

# %% [markdown]
# #### Set Background

# %%
expt56.background_type = 'line-segment'
for idx, (x, y) in enumerate(
    [
        (9162, 465),
        (11136, 593),
        (13313, 497),
        (14906, 546),
        (16454, 533),
        (17352, 496),
        (18743, 428),
        (20179, 452),
        (21368, 397),
        (22176, 468),
        (22827, 477),
        (24644, 380),
        (26439, 381),
        (28257, 378),
        (31196, 343),
        (34034, 328),
        (37265, 310),
        (41214, 323),
        (44827, 283),
        (49830, 273),
        (52905, 257),
        (58204, 260),
        (62916, 261),
        (70186, 262),
        (74204, 262),
        (82103, 268),
        (91958, 268),
        (102712, 262),
    ],
    start=1,
):
    expt56.background.add(id=str(idx), x=x, y=y)

# %%
expt47.background_type = 'line-segment'
for idx, (x, y) in enumerate(
    [
        (9090, 488),
        (10672, 566),
        (12287, 494),
        (14037, 559),
        (15451, 529),
        (16764, 445),
        (18076, 460),
        (19456, 413),
        (20466, 511),
        (21880, 396),
        (23798, 391),
        (25447, 385),
        (28073, 349),
        (30058, 332),
        (32583, 309),
        (34804, 355),
        (37160, 318),
        (40324, 290),
        (46895, 260),
        (50631, 256),
        (54602, 246),
        (58439, 264),
        (66520, 250),
        (75002, 258),
        (83649, 257),
        (92770, 255),
        (101524, 260),
    ],
    start=1,
):
    expt47.background.add(id=str(idx), x=x, y=y)

# %% [markdown]
# #### Set Linked Phases

# %%
expt56.linked_phases.add(id='ncaf', scale=1.0)

# %%
expt47.linked_phases.add(id='ncaf', scale=2.0)

# %% [markdown]
# #### Set Excluded Regions

# %%
expt56.excluded_regions.add(id='1', start=0, end=10010)
expt56.excluded_regions.add(id='2', start=100010, end=200000)

# %%
expt47.excluded_regions.add(id='1', start=0, end=10006)
expt47.excluded_regions.add(id='2', start=100004, end=200000)

# %% [markdown]
# ## Define Project
#
# The project object is used to manage the sample model, experiments,
# and analysis
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
project.experiments.add(experiment=expt56)
project.experiments.add(experiment=expt47)

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
# #### Set Fit Mode

# %%
project.analysis.fit_mode = 'joint'

# %% [markdown]
# #### Set Free Parameters

# %%
model.atom_sites['Ca'].b_iso.free = True
model.atom_sites['Al'].b_iso.free = True
model.atom_sites['Na'].b_iso.free = True
model.atom_sites['F1'].b_iso.free = True
model.atom_sites['F2'].b_iso.free = True
model.atom_sites['F3'].b_iso.free = True

# %%
expt56.linked_phases['ncaf'].scale.free = True
expt56.instrument.calib_d_to_tof_offset.free = True
expt56.instrument.calib_d_to_tof_linear.free = True
expt56.peak.broad_gauss_sigma_2.free = True
expt56.peak.broad_mix_beta_0.free = True
expt56.peak.broad_mix_beta_1.free = True
expt56.peak.asym_alpha_1.free = True

expt47.linked_phases['ncaf'].scale.free = True
expt47.instrument.calib_d_to_tof_linear.free = True
expt47.instrument.calib_d_to_tof_offset.free = True
expt47.peak.broad_gauss_sigma_2.free = True
expt47.peak.broad_mix_beta_0.free = True
expt47.peak.broad_mix_beta_1.free = True
expt47.peak.asym_alpha_1.free = True

# %% [markdown]
# #### Plot Measured vs Calculated

# %%
project.plot_meas_vs_calc(expt_name='wish_5_6', show_residual=True)

# %%
project.plot_meas_vs_calc(expt_name='wish_4_7', show_residual=True)

# %% [markdown]
# #### Run Fitting

# %%
project.analysis.fit()

# %% [markdown]
# #### Plot Measured vs Calculated

# %%
project.plot_meas_vs_calc(expt_name='wish_5_6', show_residual=True)

# %%
project.plot_meas_vs_calc(expt_name='wish_4_7', show_residual=True)

# %% [markdown]
# ## Summary
#
# This final section shows how to review the results of the analysis.

# %% [markdown]
# #### Show Project Summary

# %%
project.summary.show_report()
