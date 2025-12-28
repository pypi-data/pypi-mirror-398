# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from textwrap import wrap
from typing import List

from easydiffraction.utils.logging import console
from easydiffraction.utils.utils import render_table


class Summary:
    """Generates reports and exports results from the project.

    This class collects and presents all relevant information about the
    fitted model, experiments, and analysis results.
    """

    def __init__(self, project) -> None:
        """Initialize the summary with a reference to the project.

        Args:
            project: The Project instance this summary belongs to.
        """
        self.project = project

    # ------------------------------------------
    #  Report Generation
    # ------------------------------------------

    def show_report(self) -> None:
        self.show_project_info()
        self.show_crystallographic_data()
        self.show_experimental_data()
        self.show_fitting_details()

    def show_project_info(self) -> None:
        """Print the project title and description."""
        console.section('Project info')

        console.paragraph('Title')
        console.print(self.project.info.title)

        if self.project.info.description:
            console.paragraph('Description')
            # log.print('\n'.join(wrap(self.project.info.description,
            # width=80)))
            # TODO: Fix the following lines
            # Ensure description wraps with explicit newlines for tests
            desc_lines = wrap(self.project.info.description, width=60)
            # Use plain print to avoid Left padding that would break
            # newline adjacency checks
            print('\n'.join(desc_lines))

    def show_crystallographic_data(self) -> None:
        """Print crystallographic data including phase datablocks, space
        groups, cell parameters, and atom sites.
        """
        console.section('Crystallographic data')

        for model in self.project.sample_models.values():
            console.paragraph('Phase datablock')
            console.print(f'🧩 {model.name}')

            console.paragraph('Space group')
            console.print(model.space_group.name_h_m.value)

            console.paragraph('Cell parameters')
            columns_headers = ['Parameter', 'Value']
            columns_alignment: List[str] = ['left', 'right']
            cell_data = [
                [p.name.replace('length_', '').replace('angle_', ''), f'{p.value:.5f}']
                for p in model.cell.parameters
            ]
            render_table(
                columns_headers=columns_headers,
                columns_alignment=columns_alignment,
                columns_data=cell_data,
            )

            console.paragraph('Atom sites')
            columns_headers = [
                'label',
                'type',
                'x',
                'y',
                'z',
                'occ',
                'Biso',
            ]
            columns_alignment = [
                'left',
                'left',
                'right',
                'right',
                'right',
                'right',
                'right',
            ]
            atom_table = []
            for site in model.atom_sites:
                atom_table.append([
                    site.label.value,
                    site.type_symbol.value,
                    f'{site.fract_x.value:.5f}',
                    f'{site.fract_y.value:.5f}',
                    f'{site.fract_z.value:.5f}',
                    f'{site.occupancy.value:.5f}',
                    f'{site.b_iso.value:.5f}',
                ])
            render_table(
                columns_headers=columns_headers,
                columns_alignment=columns_alignment,
                columns_data=atom_table,
            )

    def show_experimental_data(self) -> None:
        """Print experimental data including experiment datablocks,
        types, instrument settings, and peak profile information.
        """
        console.section('Experiments')

        for expt in self.project.experiments.values():
            console.paragraph('Experiment datablock')
            console.print(f'🔬 {expt.name}')

            console.paragraph('Experiment type')
            console.print(
                f'{expt.type.sample_form.value}, '
                f'{expt.type.radiation_probe.value}, '
                f'{expt.type.beam_mode.value}'
            )

            if 'instrument' in expt._public_attrs():
                if 'setup_wavelength' in expt.instrument._public_attrs():
                    console.paragraph('Wavelength')
                    console.print(f'{expt.instrument.setup_wavelength.value:.5f}')
                if 'calib_twotheta_offset' in expt.instrument._public_attrs():
                    console.paragraph('2θ offset')
                    console.print(f'{expt.instrument.calib_twotheta_offset.value:.5f}')

            if 'peak_profile_type' in expt._public_attrs():
                console.paragraph('Profile type')
                console.print(expt.peak_profile_type)

            if 'peak' in expt._public_attrs():
                if 'broad_gauss_u' in expt.peak._public_attrs():
                    console.paragraph('Peak broadening (Gaussian)')
                    columns_headers = ['Parameter', 'Value']
                    columns_alignment = ['left', 'right']
                    columns_data = [
                        ['U', f'{expt.peak.broad_gauss_u.value:.5f}'],
                        ['V', f'{expt.peak.broad_gauss_v.value:.5f}'],
                        ['W', f'{expt.peak.broad_gauss_w.value:.5f}'],
                    ]
                    render_table(
                        columns_headers=columns_headers,
                        columns_alignment=columns_alignment,
                        columns_data=columns_data,
                    )
                if 'broad_lorentz_x' in expt.peak._public_attrs():
                    console.paragraph('Peak broadening (Lorentzian)')
                    # TODO: Some headers capitalize, some don't -
                    #  be consistent
                    columns_headers = ['Parameter', 'Value']
                    columns_alignment = ['left', 'right']
                    columns_data = [
                        ['X', f'{expt.peak.broad_lorentz_x.value:.5f}'],
                        ['Y', f'{expt.peak.broad_lorentz_y.value:.5f}'],
                    ]
                    render_table(
                        columns_headers=columns_headers,
                        columns_alignment=columns_alignment,
                        columns_data=columns_data,
                    )

    def show_fitting_details(self) -> None:
        """Print fitting details including calculation and minimization
        engines, and fit quality metrics.
        """
        console.section('Fitting')

        console.paragraph('Calculation engine')
        console.print(self.project.analysis.current_calculator)

        console.paragraph('Minimization engine')
        console.print(self.project.analysis.current_minimizer)

        console.paragraph('Fit quality')
        columns_headers = ['metric', 'value']
        columns_alignment = ['left', 'right']
        fit_metrics = [
            [
                'Goodness-of-fit (reduced χ²)',
                f'{self.project.analysis.fit_results.reduced_chi_square:.2f}',
            ]
        ]
        render_table(
            columns_headers=columns_headers,
            columns_alignment=columns_alignment,
            columns_data=fit_metrics,
        )

    # ------------------------------------------
    #  Exporting
    # ------------------------------------------

    def as_cif(self) -> str:
        """Export the final fitted data and analysis results as CIF
        format.
        """
        from easydiffraction.io.cif.serialize import summary_to_cif

        return summary_to_cif(self)
