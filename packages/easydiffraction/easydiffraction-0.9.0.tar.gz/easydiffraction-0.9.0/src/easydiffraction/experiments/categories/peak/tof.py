# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Time-of-flight peak profile classes."""

from easydiffraction.experiments.categories.peak.base import PeakBase
from easydiffraction.experiments.categories.peak.tof_mixins import IkedaCarpenterAsymmetryMixin
from easydiffraction.experiments.categories.peak.tof_mixins import TofBroadeningMixin


class TofPseudoVoigt(
    PeakBase,
    TofBroadeningMixin,
):
    """Time-of-flight pseudo-Voigt peak shape."""

    def __init__(self) -> None:
        super().__init__()
        self._add_time_of_flight_broadening()


class TofPseudoVoigtIkedaCarpenter(
    PeakBase,
    TofBroadeningMixin,
    IkedaCarpenterAsymmetryMixin,
):
    """TOF pseudo-Voigt with Ikeda–Carpenter asymmetry."""

    def __init__(self) -> None:
        super().__init__()
        self._add_time_of_flight_broadening()
        self._add_ikeda_carpenter_asymmetry()


class TofPseudoVoigtBackToBack(
    PeakBase,
    TofBroadeningMixin,
    IkedaCarpenterAsymmetryMixin,
):
    """TOF back-to-back pseudo-Voigt with asymmetry."""

    def __init__(self) -> None:
        super().__init__()
        self._add_time_of_flight_broadening()
        self._add_ikeda_carpenter_asymmetry()
