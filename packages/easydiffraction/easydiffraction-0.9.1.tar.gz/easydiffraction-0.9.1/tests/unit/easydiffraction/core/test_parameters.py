# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

import numpy as np
import pytest


def test_module_import():
    import easydiffraction.core.parameters as MUT

    assert MUT.__name__ == 'easydiffraction.core.parameters'


def test_string_descriptor_type_override_raises_type_error():
    # Creating a StringDescriptor with a NUMERIC spec should raise via Diagnostics
    from easydiffraction.core.parameters import StringDescriptor
    from easydiffraction.core.validation import AttributeSpec
    from easydiffraction.core.validation import DataTypes
    from easydiffraction.io.cif.handler import CifHandler

    with pytest.raises(TypeError):
        StringDescriptor(
            name='title',
            value_spec=AttributeSpec(value='abc', type_=DataTypes.NUMERIC, default='x'),
            description='Title text',
            cif_handler=CifHandler(names=['_proj.title']),
        )


def test_numeric_descriptor_str_includes_units():
    from easydiffraction.core.parameters import NumericDescriptor
    from easydiffraction.core.validation import AttributeSpec
    from easydiffraction.core.validation import DataTypes
    from easydiffraction.io.cif.handler import CifHandler

    d = NumericDescriptor(
        name='w',
        value_spec=AttributeSpec(value=1.23, type_=DataTypes.NUMERIC, default=0.0),
        units='deg',
        cif_handler=CifHandler(names=['_x.w']),
    )
    s = str(d)
    assert s.startswith('<') and s.endswith('>') and 'deg' in s and 'w' in s


def test_parameter_string_repr_and_as_cif_and_flags():
    from easydiffraction.core.parameters import Parameter
    from easydiffraction.core.validation import AttributeSpec
    from easydiffraction.core.validation import DataTypes
    from easydiffraction.io.cif.handler import CifHandler

    p = Parameter(
        name='a',
        value_spec=AttributeSpec(value=2.5, type_=DataTypes.NUMERIC, default=0.0),
        units='A',
        cif_handler=CifHandler(names=['_param.a']),
    )
    # Update extra attributes
    p.uncertainty = 0.1
    p.free = True

    s = str(p)
    assert '± 0.1' in s and 'A' in s and '(free=True)' in s

    # CIF line is `<tag> <value>`
    assert p.as_cif == '_param.a   2.5000'

    # CifHandler uid is owner's unique_name (parameter name here)
    assert p._cif_handler.uid == p.unique_name == 'a'


def test_parameter_uncertainty_must_be_non_negative():
    from easydiffraction.core.parameters import Parameter
    from easydiffraction.core.validation import AttributeSpec
    from easydiffraction.core.validation import DataTypes
    from easydiffraction.io.cif.handler import CifHandler

    p = Parameter(
        name='b',
        value_spec=AttributeSpec(value=1.0, type_=DataTypes.NUMERIC, default=0.0),
        cif_handler=CifHandler(names=['_param.b']),
    )
    with pytest.raises(TypeError):
        p.uncertainty = -0.5


def test_parameter_fit_bounds_assign_and_read():
    from easydiffraction.core.parameters import Parameter
    from easydiffraction.core.validation import AttributeSpec
    from easydiffraction.core.validation import DataTypes
    from easydiffraction.io.cif.handler import CifHandler

    p = Parameter(
        name='c',
        value_spec=AttributeSpec(value=0.0, type_=DataTypes.NUMERIC, default=0.0),
        cif_handler=CifHandler(names=['_param.c']),
    )
    p.fit_min = -1.0
    p.fit_max = 10.0
    assert np.isclose(p.fit_min, -1.0) and np.isclose(p.fit_max, 10.0)
