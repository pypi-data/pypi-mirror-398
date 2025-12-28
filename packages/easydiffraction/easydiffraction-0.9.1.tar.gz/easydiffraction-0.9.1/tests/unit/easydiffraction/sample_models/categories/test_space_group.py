# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from easydiffraction.sample_models.categories.space_group import SpaceGroup


def test_space_group_name_updates_it_code():
    sg = SpaceGroup()
    # default name 'P 1' should set code to the first available
    default_code = sg.it_coordinate_system_code.value
    sg.name_h_m = 'P 1'
    assert sg.it_coordinate_system_code.value == sg._it_coordinate_system_code_allowed_values[0]
    # changing name resets the code again
    sg.name_h_m = 'P -1'
    assert sg.it_coordinate_system_code.value == sg._it_coordinate_system_code_allowed_values[0]
