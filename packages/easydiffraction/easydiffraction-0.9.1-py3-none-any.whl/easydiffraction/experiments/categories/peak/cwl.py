# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Constant-wavelength peak profile classes."""

from easydiffraction.experiments.categories.peak.base import PeakBase
from easydiffraction.experiments.categories.peak.cwl_mixins import CwlBroadeningMixin
from easydiffraction.experiments.categories.peak.cwl_mixins import EmpiricalAsymmetryMixin
from easydiffraction.experiments.categories.peak.cwl_mixins import FcjAsymmetryMixin


class CwlPseudoVoigt(
    PeakBase,
    CwlBroadeningMixin,
):
    """Constant-wavelength pseudo-Voigt peak shape."""

    def __init__(self) -> None:
        super().__init__()
        self._add_constant_wavelength_broadening()


class CwlSplitPseudoVoigt(
    PeakBase,
    CwlBroadeningMixin,
    EmpiricalAsymmetryMixin,
):
    """Split pseudo-Voigt (empirical asymmetry) for CWL mode."""

    def __init__(self) -> None:
        super().__init__()
        self._add_constant_wavelength_broadening()
        self._add_empirical_asymmetry()


class CwlThompsonCoxHastings(
    PeakBase,
    CwlBroadeningMixin,
    FcjAsymmetryMixin,
):
    """Thompson–Cox–Hastings with FCJ asymmetry for CWL mode."""

    def __init__(self) -> None:
        super().__init__()
        self._add_constant_wavelength_broadening()
        self._add_fcj_asymmetry()
