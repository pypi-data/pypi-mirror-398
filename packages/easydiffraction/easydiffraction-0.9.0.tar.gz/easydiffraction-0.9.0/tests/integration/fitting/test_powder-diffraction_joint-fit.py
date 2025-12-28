# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

import tempfile

import pytest
from numpy.testing import assert_almost_equal

from easydiffraction import ExperimentFactory
from easydiffraction import Project
from easydiffraction import SampleModelFactory
from easydiffraction import download_data

TEMP_DIR = tempfile.gettempdir()


@pytest.mark.fast
def test_joint_fit_split_dataset_neutron_pd_cwl_pbso4() -> None:
    # Set sample model
    model = SampleModelFactory.create(name='pbso4')
    model.space_group.name_h_m = 'P n m a'
    model.cell.length_a = 8.47
    model.cell.length_b = 5.39
    model.cell.length_c = 6.95
    model.atom_sites.add(
        label='Pb',
        type_symbol='Pb',
        fract_x=0.1876,
        fract_y=0.25,
        fract_z=0.167,
        wyckoff_letter='c',
        b_iso=1.37,
    )
    model.atom_sites.add(
        label='S',
        type_symbol='S',
        fract_x=0.0654,
        fract_y=0.25,
        fract_z=0.684,
        wyckoff_letter='c',
        b_iso=0.3777,
    )
    model.atom_sites.add(
        label='O1',
        type_symbol='O',
        fract_x=0.9082,
        fract_y=0.25,
        fract_z=0.5954,
        wyckoff_letter='c',
        b_iso=1.9764,
    )
    model.atom_sites.add(
        label='O2',
        type_symbol='O',
        fract_x=0.1935,
        fract_y=0.25,
        fract_z=0.5432,
        wyckoff_letter='c',
        b_iso=1.4456,
    )
    model.atom_sites.add(
        label='O3',
        type_symbol='O',
        fract_x=0.0811,
        fract_y=0.0272,
        fract_z=0.8086,
        wyckoff_letter='d',
        b_iso=1.2822,
    )

    # Set experiments
    data_path = download_data(id=14, destination=TEMP_DIR)
    expt1 = ExperimentFactory.create(name='npd1', data_path=data_path)
    expt1.instrument.setup_wavelength = 1.91
    expt1.instrument.calib_twotheta_offset = -0.1406
    expt1.peak.broad_gauss_u = 0.139
    expt1.peak.broad_gauss_v = -0.4124
    expt1.peak.broad_gauss_w = 0.386
    expt1.peak.broad_lorentz_x = 0
    expt1.peak.broad_lorentz_y = 0.0878
    expt1.linked_phases.add(id='pbso4', scale=1.46)
    expt1.background_type = 'line-segment'
    for id, x, y in [
        ('1', 11.0, 206.1624),
        ('2', 15.0, 194.75),
        ('3', 20.0, 194.505),
        ('4', 30.0, 188.4375),
        ('5', 50.0, 207.7633),
        ('6', 70.0, 201.7002),
        ('7', 120.0, 244.4525),
        ('8', 153.0, 226.0595),
    ]:
        expt1.background.add(id=id, x=x, y=y)

    data_path = download_data(id=15, destination=TEMP_DIR)
    expt2 = ExperimentFactory.create(name='npd2', data_path=data_path)
    expt2.instrument.setup_wavelength = 1.91
    expt2.instrument.calib_twotheta_offset = -0.1406
    expt2.peak.broad_gauss_u = 0.139
    expt2.peak.broad_gauss_v = -0.4124
    expt2.peak.broad_gauss_w = 0.386
    expt2.peak.broad_lorentz_x = 0
    expt2.peak.broad_lorentz_y = 0.0878
    expt2.linked_phases.add(id='pbso4', scale=1.46)
    expt2.background_type = 'line-segment'
    for id, x, y in [
        ('1', 11.0, 206.1624),
        ('2', 15.0, 194.75),
        ('3', 20.0, 194.505),
        ('4', 30.0, 188.4375),
        ('5', 50.0, 207.7633),
        ('6', 70.0, 201.7002),
        ('7', 120.0, 244.4525),
        ('8', 153.0, 226.0595),
    ]:
        expt2.background.add(id=id, x=x, y=y)

    # Create project
    project = Project()
    project.sample_models.add(sample_model=model)
    project.experiments.add(experiment=expt1)
    project.experiments.add(experiment=expt2)

    # Prepare for fitting
    project.analysis.current_calculator = 'cryspy'
    project.analysis.current_minimizer = 'lmfit (leastsq)'
    project.analysis.fit_mode = 'joint'

    # Select fitting parameters
    model.cell.length_a.free = True
    model.cell.length_b.free = True
    model.cell.length_c.free = True

    # Perform fit
    project.analysis.fit()

    # Compare fit quality
    assert_almost_equal(
        project.analysis.fit_results.reduced_chi_square,
        desired=4.66,
        decimal=1,
    )


@pytest.mark.fast
def test_joint_fit_neutron_xray_pd_cwl_pbso4() -> None:
    # Set sample model
    model = SampleModelFactory.create(name='pbso4')
    model.space_group.name_h_m = 'P n m a'
    model.cell.length_a = 8.47
    model.cell.length_b = 5.39
    model.cell.length_c = 6.95
    model.atom_sites.add(
        label='Pb',
        type_symbol='Pb',
        fract_x=0.1876,
        fract_y=0.25,
        fract_z=0.167,
        wyckoff_letter='c',
        b_iso=1.37,
    )
    model.atom_sites.add(
        label='S',
        type_symbol='S',
        fract_x=0.0654,
        fract_y=0.25,
        fract_z=0.684,
        wyckoff_letter='c',
        b_iso=0.3777,
    )
    model.atom_sites.add(
        label='O1',
        type_symbol='O',
        fract_x=0.9082,
        fract_y=0.25,
        fract_z=0.5954,
        wyckoff_letter='c',
        b_iso=1.9764,
    )
    model.atom_sites.add(
        label='O2',
        type_symbol='O',
        fract_x=0.1935,
        fract_y=0.25,
        fract_z=0.5432,
        wyckoff_letter='c',
        b_iso=1.4456,
    )
    model.atom_sites.add(
        label='O3',
        type_symbol='O',
        fract_x=0.0811,
        fract_y=0.0272,
        fract_z=0.8086,
        wyckoff_letter='d',
        b_iso=1.2822,
    )

    # Set experiments
    data_path = download_data(id=13, destination=TEMP_DIR)
    expt1 = ExperimentFactory.create(
        name='npd',
        data_path=data_path,
        radiation_probe='neutron',
    )
    expt1.instrument.setup_wavelength = 1.91
    expt1.instrument.calib_twotheta_offset = -0.1406
    expt1.peak.broad_gauss_u = 0.139
    expt1.peak.broad_gauss_v = -0.412
    expt1.peak.broad_gauss_w = 0.386
    expt1.peak.broad_lorentz_x = 0
    expt1.peak.broad_lorentz_y = 0.088
    expt1.linked_phases.add(id='pbso4', scale=1.5)
    for id, x, y in [
        ('1', 11.0, 206.1624),
        ('2', 15.0, 194.75),
        ('3', 20.0, 194.505),
        ('4', 30.0, 188.4375),
        ('5', 50.0, 207.7633),
        ('6', 70.0, 201.7002),
        ('7', 120.0, 244.4525),
        ('8', 153.0, 226.0595),
    ]:
        expt1.background.add(id=id, x=x, y=y)

    data_path = download_data(id=16, destination=TEMP_DIR)
    expt2 = ExperimentFactory.create(
        name='xrd',
        data_path=data_path,
        radiation_probe='xray',
    )
    expt2.instrument.setup_wavelength = 1.540567
    expt2.instrument.calib_twotheta_offset = -0.05181
    expt2.peak.broad_gauss_u = 0.304138
    expt2.peak.broad_gauss_v = -0.112622
    expt2.peak.broad_gauss_w = 0.021272
    expt2.peak.broad_lorentz_x = 0
    expt2.peak.broad_lorentz_y = 0.057691
    expt2.linked_phases.add(id='pbso4', scale=0.001)
    for id, x, y in [
        ('1', 11.0, 141.8516),
        ('2', 13.0, 102.8838),
        ('3', 16.0, 78.0551),
        ('4', 20.0, 124.0121),
        ('5', 30.0, 123.7123),
        ('6', 50.0, 120.8266),
        ('7', 90.0, 113.7473),
        ('8', 110.0, 132.4643),
    ]:
        expt2.background.add(id=id, x=x, y=y)

    # Create project
    project = Project()
    project.sample_models.add(sample_model=model)
    project.experiments.add(experiment=expt1)
    project.experiments.add(experiment=expt2)

    # Prepare for fitting
    project.analysis.current_calculator = 'cryspy'
    project.analysis.current_minimizer = 'lmfit (leastsq)'

    # Select fitting parameters
    model.cell.length_a.free = True
    model.cell.length_b.free = True
    model.cell.length_c.free = True
    expt1.linked_phases['pbso4'].scale.free = True
    expt2.linked_phases['pbso4'].scale.free = True

    # ------------ 1st fitting ------------

    # Perform fit
    project.analysis.fit_mode = 'single'  # Default
    project.analysis.fit()

    # Compare fit quality
    assert_almost_equal(
        project.analysis.fit_results.reduced_chi_square,
        desired=26.05,
        decimal=1,
    )

    # ------------ 2nd fitting ------------

    # Perform fit
    project.analysis.fit_mode = 'joint'
    project.analysis.fit()

    # Compare fit quality
    assert_almost_equal(
        project.analysis.fit_results.reduced_chi_square,
        desired=21.09,
        decimal=1,
    )

    # ------------ 3rd fitting ------------

    # Perform fit
    project.analysis.joint_fit_experiments['xrd'].weight = 0.5  # Default
    project.analysis.joint_fit_experiments['npd'].weight = 0.5  # Default
    project.analysis.fit_mode = 'joint'
    project.analysis.fit()

    # Compare fit quality
    assert_almost_equal(
        project.analysis.fit_results.reduced_chi_square,
        desired=21.09,
        decimal=1,
    )

    # ------------ 4th fitting ------------

    # Perform fit
    project.analysis.joint_fit_experiments['xrd'].weight = 0.3
    project.analysis.joint_fit_experiments['npd'].weight = 0.7
    project.analysis.fit_mode = 'joint'
    project.analysis.fit()

    # Compare fit quality
    assert_almost_equal(
        project.analysis.fit_results.reduced_chi_square,
        desired=14.39,
        decimal=1,
    )


if __name__ == '__main__':
    test_joint_fit_split_dataset_neutron_pd_cwl_pbso4()
    test_joint_fit_neutron_xray_pd_cwl_pbso4()
