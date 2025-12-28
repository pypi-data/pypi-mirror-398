import os
import tempfile

from numpy.testing import assert_almost_equal

from easydiffraction import Project
from easydiffraction import download_from_repository

TEMP_DIR = tempfile.gettempdir()


def single_fit_neutron_pd_cwl_lbco() -> None:
    # Create project
    project = Project()

    # Set sample model
    project.sample_models.add_minimal(name='lbco')
    model = project.sample_models['lbco']
    model.space_group.name_h_m = 'P m -3 m'
    model.cell.length_a = 3.88
    model.atom_sites.add_from_args(
        label='La',
        type_symbol='La',
        fract_x=0,
        fract_y=0,
        fract_z=0,
        wyckoff_letter='a',
        occupancy=0.5,
        b_iso=0.1,
    )
    model.atom_sites.add_from_args(
        label='Ba',
        type_symbol='Ba',
        fract_x=0,
        fract_y=0,
        fract_z=0,
        wyckoff_letter='a',
        occupancy=0.5,
        b_iso=0.1,
    )
    model.atom_sites.add_from_args(
        label='Co',
        type_symbol='Co',
        fract_x=0.5,
        fract_y=0.5,
        fract_z=0.5,
        wyckoff_letter='b',
        b_iso=0.1,
    )
    model.atom_sites.add_from_args(
        label='O',
        type_symbol='O',
        fract_x=0,
        fract_y=0.5,
        fract_z=0.5,
        wyckoff_letter='c',
        b_iso=0.1,
    )

    # Set experiment
    data_file = 'hrpt_lbco.xye'
    download_from_repository(data_file, destination=TEMP_DIR)
    project.experiments.add_from_data_path(name='hrpt', data_path=os.path.join(TEMP_DIR, data_file))
    expt = project.experiments['hrpt']
    expt.instrument.setup_wavelength = 1.494
    expt.instrument.calib_twotheta_offset = 0
    expt.peak.broad_gauss_u = 0.1
    expt.peak.broad_gauss_v = -0.1
    expt.peak.broad_gauss_w = 0.2
    expt.peak.broad_lorentz_x = 0
    expt.peak.broad_lorentz_y = 0
    expt.linked_phases.add_from_args(id='lbco', scale=5.0)
    expt.background.add_from_args(x=10, y=170)
    expt.background.add_from_args(x=165, y=170)

    expt.show_as_cif()

    # Prepare for fitting
    project.analysis.current_calculator = 'cryspy'
    project.analysis.current_minimizer = 'lmfit (leastsq)'

    # ------------ 1st fitting ------------

    # Select fitting parameters
    model.cell.length_a.free = True
    expt.linked_phases['lbco'].scale.free = True
    expt.instrument.calib_twotheta_offset.free = True
    expt.background['10'].y.free = True
    expt.background['165'].y.free = True

    # Perform fit
    project.analysis.fit()

    # Compare fit quality
    assert_almost_equal(project.analysis.fit_results.reduced_chi_square, desired=5.79, decimal=1)

    # ------------ 2nd fitting ------------

    # Select fitting parameters
    expt.peak.broad_gauss_u.free = True
    expt.peak.broad_gauss_v.free = True
    expt.peak.broad_gauss_w.free = True
    expt.peak.broad_lorentz_y.free = True

    # Perform fit
    project.analysis.fit()

    # Compare fit quality
    assert_almost_equal(project.analysis.fit_results.reduced_chi_square, desired=4.41, decimal=1)

    # ------------ 3rd fitting ------------

    # Select fitting parameters
    model.atom_sites['La'].b_iso.free = True
    model.atom_sites['Ba'].b_iso.free = True
    model.atom_sites['Co'].b_iso.free = True
    model.atom_sites['O'].b_iso.free = True

    # Perform fit
    project.analysis.fit()

    # Show chart
    project.plot_meas_vs_calc(expt_name='hrpt')

    # Compare fit quality
    assert_almost_equal(project.analysis.fit_results.reduced_chi_square, desired=1.3, decimal=1)


single_fit_neutron_pd_cwl_lbco()
