# %% [markdown]
# # Structure Refinement: LBCO, HRPT
#
# This minimalistic example is designed to be as compact as possible for
# a Rietveld refinement of a crystal structure using constant-wavelength
# neutron powder diffraction data for La0.5Ba0.5CoO3 from HRPT at PSI.
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

# %%
from easydiffraction.utils.logging import Logger
Logger.configure(
    level=Logger.Level.INFO,
    mode=Logger.Mode.VERBOSE,
    reaction=Logger.Reaction.WARN,
)

# %% [markdown]
# ## Step 1: Define Project

# %%
project = ed.Project()

# %% [markdown]
# ## Step 2: Define Sample Model

# %%
#project.sample_models.add_from_cif_path("tmp/data/lbco.cif")
project.sample_models.add(cif_path="tmp/data/lbco.cif")

# %%
project.sample_models.show_names()

# %%
# Create an alias for easier access
lbco = project.sample_models['lbco']

# %%
#print('a')
#print('lbco.cell.length_b.value', lbco.cell.length_b.value)
#print('b')
lbco.cell.length_a = 3.89
#print('c')
#print('lbco.cell.length_b.value', lbco.cell.length_b.value)
#print('d')
#print('lbco.cell.length_b.value', lbco.cell.length_b.value)
#print('e')

# %%
lbco.show_as_cif()
#exit()

# %% [markdown]
# ## Step 3: Define Experiment

# %%
#project.experiments.add_from_cif_path("tmp/data/hrpt.cif")
project.experiments.add(cif_path="tmp/data/hrpt.cif")

# %%
project.experiments.show_names()

# %%
# Create an alias for easier access
hrpt = project.experiments['hrpt']

# %%
hrpt.background['1'].y = 300

# %%
hrpt.show_as_cif()
#exit()

print('==')
print('a', hrpt.background['1'].y.value)

#exit()

# %%
print('hrpt.data.x', hrpt.data.x)
print('hrpt.data.meas', hrpt.data.meas)
print('hrpt.data.calc', hrpt.data.calc)

###project.plot_meas_vs_calc(expt_name='hrpt', show_residual=True)

print('hrpt.data.calc', hrpt.data.calc)

###hrpt.show_as_cif()

print('hrpt.data.meas[3]', hrpt.data.meas[3])
print('hrpt.data["3"].intensity_meas', hrpt.data["3"].intensity_meas)
print('hrpt.data["3"].intensity_meas', hrpt.data["3"].intensity_meas.value)

print("hrpt.background['1'].y", hrpt.background['1'].y)
print("hrpt.background['1'].y.value", hrpt.background['1'].y.value)
print("hrpt.background['1'].y.free", hrpt.background['1'].y.free)


#exit()
# %%

# %% [markdown]
# ## Step 4: Perform Analysis


# %%
project.analysis.aliases.add(
    label='biso_La',
    param_uid=lbco.atom_sites['La'].b_iso.uid,
)
project.analysis.aliases.add(
    label='biso_Ba',
    param_uid=lbco.atom_sites['Ba'].b_iso.uid,
)

# %%
project.analysis.constraints.add(
    lhs_alias='biso_Ba',
    rhs_expr='biso_La',
)

# %%
#project.analysis.apply_constraints()

# %%
# Select sample model parameters to refine
lbco.cell.length_a.free = True

lbco.atom_sites['La'].b_iso.free = True
lbco.atom_sites['Ba'].b_iso.free = True
lbco.atom_sites['Co'].b_iso.free = True
lbco.atom_sites['O'].b_iso.free = True
#for atom_site in lbco.atom_sites:
#    atom_site.b_iso.free = True

# %%
# Select experiment parameters to refine
hrpt.linked_phases['lbco'].scale.free = True

hrpt.instrument.calib_twotheta_offset.free = True

hrpt.peak.broad_gauss_u.free = True
hrpt.peak.broad_gauss_v.free = True
hrpt.peak.broad_gauss_w.free = True
hrpt.peak.broad_lorentz_y.free = True

#hrpt.background['1'].y.free = True
##hrpt.background['2'].y.free = True
#hrpt.background['3'].y.free = True
#hrpt.background['4'].y.free = True
#hrpt.background['5'].y.free = True
for line_segment in hrpt.background:
    line_segment.y.free = True

# %%
project.analysis.show_free_params()

# %%
project.analysis.fit()

# %%
project.plot_meas_vs_calc(expt_name='hrpt', show_residual=True)

# %%
#hrpt.show_as_cif()

#print(lbco.cell)

#hrpt.show_as_cif()
