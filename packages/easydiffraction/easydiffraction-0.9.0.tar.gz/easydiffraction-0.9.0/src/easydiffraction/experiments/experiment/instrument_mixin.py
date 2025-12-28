# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from typing import TYPE_CHECKING

from typeguard import typechecked

from easydiffraction.experiments.categories.instrument.factory import InstrumentFactory

if TYPE_CHECKING:
    from easydiffraction.experiments.categories.instrument.base import InstrumentBase


class InstrumentMixin:
    """Mixin that wires an experiment to an instrument category.

    Creates a default instrument via `InstrumentFactory` using the
    experiment type (scattering type and beam mode) at initialization.
    """

    def __init__(self, *args, **kwargs):
        expt_type = kwargs.get('type')
        super().__init__(*args, **kwargs)
        self._instrument = InstrumentFactory.create(
            scattering_type=expt_type.scattering_type.value,
            beam_mode=expt_type.beam_mode.value,
        )

    @property
    def instrument(self):
        """Instrument category object associated with the experiment."""
        return self._instrument

    @instrument.setter
    @typechecked
    def instrument(self, new_instrument: InstrumentBase):
        """Replace the instrument and re-parent it to this experiment.

        Args:
            new_instrument: Instrument instance compatible with the
                experiment type.
        """
        self._instrument = new_instrument
        self._instrument._parent = self
