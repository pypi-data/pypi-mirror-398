# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from typing import Dict
from typing import List
from typing import Optional
from typing import Type
from typing import Union

from easydiffraction.analysis.calculators.base import CalculatorBase
from easydiffraction.analysis.calculators.crysfml import CrysfmlCalculator
from easydiffraction.analysis.calculators.cryspy import CryspyCalculator
from easydiffraction.analysis.calculators.pdffit import PdffitCalculator
from easydiffraction.utils.logging import console
from easydiffraction.utils.logging import log
from easydiffraction.utils.utils import render_table


class CalculatorFactory:
    """Factory for creating calculation engine instances.

    The factory exposes discovery helpers to list and show available
    calculators in the current environment and a creator that returns an
    instantiated calculator or ``None`` if the requested one is not
    available.
    """

    _potential_calculators: Dict[str, Dict[str, Union[str, Type[CalculatorBase]]]] = {
        'crysfml': {
            'description': 'CrysFML library for crystallographic calculations',
            'class': CrysfmlCalculator,
        },
        'cryspy': {
            'description': 'CrysPy library for crystallographic calculations',
            'class': CryspyCalculator,
        },
        'pdffit': {
            'description': 'PDFfit2 library for pair distribution function calculations',
            'class': PdffitCalculator,
        },
    }

    @classmethod
    def _supported_calculators(
        cls,
    ) -> Dict[str, Dict[str, Union[str, Type[CalculatorBase]]]]:
        """Return calculators whose engines are importable.

        This filters the list of potential calculators by instantiating
        their classes and checking the ``engine_imported`` property.

        Returns:
            Mapping from calculator name to its config dict.
        """
        return {
            name: cfg
            for name, cfg in cls._potential_calculators.items()
            if cfg['class']().engine_imported  # instantiate and check the @property
        }

    @classmethod
    def list_supported_calculators(cls) -> List[str]:
        """List names of calculators available in the environment.

        Returns:
            List of calculator identifiers, e.g. ``["crysfml", ...]``.
        """
        return list(cls._supported_calculators().keys())

    @classmethod
    def show_supported_calculators(cls) -> None:
        """Pretty-print supported calculators and their descriptions."""
        columns_headers: List[str] = ['Calculator', 'Description']
        columns_alignment = ['left', 'left']
        columns_data: List[List[str]] = []
        for name, config in cls._supported_calculators().items():
            description: str = config.get('description', 'No description provided.')
            columns_data.append([name, description])

        console.paragraph('Supported calculators')
        render_table(
            columns_headers=columns_headers,
            columns_alignment=columns_alignment,
            columns_data=columns_data,
        )

    @classmethod
    def create_calculator(cls, calculator_name: str) -> Optional[CalculatorBase]:
        """Create a calculator instance by name.

        Args:
            calculator_name: Identifier of the calculator to create.

        Returns:
            A calculator instance or ``None`` if unknown or unsupported.
        """
        config = cls._supported_calculators().get(calculator_name)
        if not config:
            log.warning(
                f"Unknown calculator '{calculator_name}', "
                f'Supported calculators: {cls.list_supported_calculators()}'
            )
            return None

        return config['class']()
