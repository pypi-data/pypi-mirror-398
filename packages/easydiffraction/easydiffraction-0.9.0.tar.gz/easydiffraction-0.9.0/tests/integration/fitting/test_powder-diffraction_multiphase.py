# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

import tempfile

from numpy.testing import assert_almost_equal

from easydiffraction import ExperimentFactory
from easydiffraction import Project
from easydiffraction import SampleModelFactory
from easydiffraction import download_data

TEMP_DIR = tempfile.gettempdir()


def test_single_fit_neutron_pd_tof_mcstas_lbco_si() -> None:
    # Set sample models
    model_1 = SampleModelFactory.create(name='lbco')
    model_1.space_group.name_h_m = 'P m -3 m'
    model_1.space_group.it_coordinate_system_code = '1'
    model_1.cell.length_a = 3.8909
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

    model_2 = SampleModelFactory.create(name='si')
    model_2.space_group.name_h_m = 'F d -3 m'
    model_2.space_group.it_coordinate_system_code = '2'
    model_2.cell.length_a = 5.43146
    model_2.atom_sites.add(
        label='Si',
        type_symbol='Si',
        fract_x=0.0,
        fract_y=0.0,
        fract_z=0.0,
        wyckoff_letter='a',
        b_iso=0.0,
    )

    # Set experiment
    data_path = download_data(id=8, destination=TEMP_DIR)
    expt = ExperimentFactory.create(
        name='mcstas',
        data_path=data_path,
        beam_mode='time-of-flight',
    )
    expt.instrument.setup_twotheta_bank = 94.90931761529106
    expt.instrument.calib_d_to_tof_offset = 0.0
    expt.instrument.calib_d_to_tof_linear = 58724.76869981215
    expt.instrument.calib_d_to_tof_quad = -0.00001
    expt.peak_profile_type = 'pseudo-voigt * ikeda-carpenter'
    expt.peak.broad_gauss_sigma_0 = 45137
    expt.peak.broad_gauss_sigma_1 = -52394
    expt.peak.broad_gauss_sigma_2 = 22998
    expt.peak.broad_mix_beta_0 = 0.0055
    expt.peak.broad_mix_beta_1 = 0.0041
    expt.peak.asym_alpha_0 = 0.0
    expt.peak.asym_alpha_1 = 0.0097
    expt.linked_phases.add(id='lbco', scale=4.0)
    expt.linked_phases.add(id='si', scale=0.2)
    for x in range(45000, 115000, 5000):
        expt.background.add(id=str(x), x=x, y=0.2)

    # Create project
    project = Project()
    project.sample_models.add(sample_model=model_1)
    project.sample_models.add(sample_model=model_2)
    project.experiments.add(experiment=expt)

    # Exclude regions from fitting
    project.experiments['mcstas'].excluded_regions.add(start=108000, end=200000)

    # Prepare for fitting
    project.analysis.current_calculator = 'cryspy'
    project.analysis.current_minimizer = 'lmfit (leastsq)'

    # Select fitting parameters
    model_1.cell.length_a.free = True
    model_1.atom_sites['La'].b_iso.free = True
    model_1.atom_sites['Ba'].b_iso.free = True
    model_1.atom_sites['Co'].b_iso.free = True
    model_1.atom_sites['O'].b_iso.free = True
    model_2.cell.length_a.free = True
    model_2.atom_sites['Si'].b_iso.free = True
    expt.linked_phases['lbco'].scale.free = True
    expt.linked_phases['si'].scale.free = True
    expt.peak.broad_gauss_sigma_0.free = True
    expt.peak.broad_gauss_sigma_1.free = True
    expt.peak.broad_gauss_sigma_2.free = True
    expt.peak.asym_alpha_1.free = True
    expt.peak.broad_mix_beta_0.free = True
    expt.peak.broad_mix_beta_1.free = True
    for point in expt.background:
        point.y.free = True

    # Perform fit
    project.analysis.fit()

    # Compare fit quality
    assert_almost_equal(
        project.analysis.fit_results.reduced_chi_square,
        desired=2.87,
        decimal=1,
    )


if __name__ == '__main__':
    test_single_fit_neutron_pd_tof_mcstas_lbco_si()
