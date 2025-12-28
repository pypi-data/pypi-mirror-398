# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from typing import Iterable
from typing import Mapping


class FactoryBase:
    """Reusable argument validation mixin."""

    @staticmethod
    def _validate_args(
        present: set[str],
        allowed_specs: Iterable[Mapping[str, Iterable[str]]],
        factory_name: str,
    ) -> None:
        """Validate provided arguments against allowed combinations."""
        for spec in allowed_specs:
            required = set(spec.get('required', []))
            optional = set(spec.get('optional', []))
            if required.issubset(present) and present <= (required | optional):
                return  # valid combo
        # build readable error message
        combos = []
        for spec in allowed_specs:
            req = ', '.join(spec.get('required', []))
            opt = ', '.join(spec.get('optional', []))
            if opt:
                combos.append(f'({req}[, {opt}])')
            else:
                combos.append(f'({req})')
        raise ValueError(
            f'Invalid argument combination for {factory_name} creation.\n'
            f'Provided: {sorted(present)}\n'
            f'Allowed combinations:\n  ' + '\n  '.join(combos)
        )
