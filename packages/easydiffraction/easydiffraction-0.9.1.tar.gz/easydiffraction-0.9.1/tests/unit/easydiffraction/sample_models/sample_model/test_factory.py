# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

import pytest

from easydiffraction.sample_models.sample_model.factory import SampleModelFactory


def test_create_minimal_by_name():
    m = SampleModelFactory.create(name='abc')
    assert m.name == 'abc'


def test_invalid_arg_combo_raises():
    with pytest.raises(ValueError):
        SampleModelFactory.create(name=None, cif_path=None)
