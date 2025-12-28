# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

import pytest


def test_background_factory_default_and_errors():
    from easydiffraction.experiments.categories.background.enums import BackgroundTypeEnum
    from easydiffraction.experiments.categories.background.factory import BackgroundFactory

    # Default should produce a LineSegmentBackground
    obj = BackgroundFactory.create()
    assert obj.__class__.__name__.endswith('LineSegmentBackground')

    # Explicit type
    obj2 = BackgroundFactory.create(BackgroundTypeEnum.CHEBYSHEV)
    assert obj2.__class__.__name__.endswith('ChebyshevPolynomialBackground')

    # Unsupported enum (fake) should raise ValueError
    class FakeEnum:
        value = 'x'

    with pytest.raises(ValueError):
        BackgroundFactory.create(FakeEnum)  # type: ignore[arg-type]
