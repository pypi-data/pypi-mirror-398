# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

import pytest


def test_cell_defaults_and_overrides():
    from easydiffraction.sample_models.categories.cell import Cell

    c = Cell()
    # Defaults from AttributeSpec in implementation
    assert pytest.approx(c.length_a.value) == 10.0
    assert pytest.approx(c.length_b.value) == 10.0
    assert pytest.approx(c.length_c.value) == 10.0
    assert pytest.approx(c.angle_alpha.value) == 90.0
    assert pytest.approx(c.angle_beta.value) == 90.0
    assert pytest.approx(c.angle_gamma.value) == 90.0

    # Override through constructor
    c2 = Cell(length_a=12.3, angle_beta=100.0)
    assert pytest.approx(c2.length_a.value) == 12.3
    assert pytest.approx(c2.angle_beta.value) == 100.0


def test_cell_setters_apply_validation_and_units():
    from easydiffraction.sample_models.categories.cell import Cell

    c = Cell()
    # Set valid values within range
    c.length_a = 5.5
    c.angle_gamma = 120.0
    assert pytest.approx(c.length_a.value) == 5.5
    assert pytest.approx(c.angle_gamma.value) == 120.0
    # Check units are preserved on parameter objects
    assert c.length_a.units == 'Å'
    assert c.angle_gamma.units == 'deg'


def test_cell_identity_category_code():
    from easydiffraction.sample_models.categories.cell import Cell

    c = Cell()
    assert c._identity.category_code == 'cell'
