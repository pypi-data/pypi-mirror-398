# %% [markdown]
# # Structure Refinement: LBCO, HRPT
#
# This minimalistic example is designed to show how Rietveld refinement
# of a crystal structure can be performed when both the sample model and
# experiment are defined using CIF files.
#
# For this example, constant-wavelength neutron powder diffraction data
# for La0.5Ba0.5CoO3 from HRPT at PSI is used.
#
# It does not contain any advanced features or options, and includes no
# comments or explanations—these can be found in the other tutorials.
# Default values are used for all parameters if not specified. Only
# essential and self-explanatory code is provided.
#
# The example is intended for users who are already familiar with the
# EasyDiffraction library and want to quickly get started with a simple
# refinement. It is also useful for those who want to see what a
# refinement might look like in code. For a more detailed explanation of
# the code, please refer to the other tutorials.

# %% [markdown]
# ## Import Library

# %%
import easydiffraction as ed

# %% [markdown]
# ## Step 1: Define Project

# %%
# Create minimal project without name and description
project = ed.Project()

# %% [markdown]
# ## Step 2: Define Sample Model

# %%
# Download CIF file from repository
model_path = ed.download_data(id=1, destination='data')

# %%
project.sample_models.add(cif_path=model_path)

# %% [markdown]
# ## Step 3: Define Experiment

# %%
# Download CIF file from repository
expt_path = ed.download_data(id=2, destination='data')

# %%
project.experiments.add(cif_path=expt_path)

# %% [markdown]
# ## Step 4: Perform Analysis

# %%
# Start refinement. All parameters, which have standard uncertainties
# in the input CIF files, are refined by default.
project.analysis.fit()

# %%
project.experiments.show_names()

# %%
project.plot_meas_vs_calc(expt_name='hrpt', show_residual=True)

# %% [markdown]
# ## Step 5: Show Project Summary

# %%
project.summary.show_report()
