# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional

import numpy as np

from easydiffraction.analysis.fit_helpers.reporting import FitResults
from easydiffraction.analysis.fit_helpers.tracking import FitProgressTracker


class MinimizerBase(ABC):
    """Abstract base for concrete minimizers.

    Contract:
    - Subclasses must implement ``_prepare_solver_args``,
        ``_run_solver``, ``_sync_result_to_parameters`` and
        ``_check_success``.
    - The ``fit`` method orchestrates the full workflow and returns
        :class:`FitResults`.
    """

    def __init__(
        self,
        name: Optional[str] = None,
        method: Optional[str] = None,
        max_iterations: Optional[int] = None,
    ) -> None:
        self.name: Optional[str] = name
        self.method: Optional[str] = method
        self.max_iterations: Optional[int] = max_iterations
        self.result: Optional[FitResults] = None
        self._previous_chi2: Optional[float] = None
        self._iteration: Optional[int] = None
        self._best_chi2: Optional[float] = None
        self._best_iteration: Optional[int] = None
        self._fitting_time: Optional[float] = None
        self.tracker: FitProgressTracker = FitProgressTracker()

    def _start_tracking(self, minimizer_name: str) -> None:
        """Initialize progress tracking and timer.

        Args:
            minimizer_name: Human-readable name shown in progress.
        """
        self.tracker.reset()
        self.tracker.start_tracking(minimizer_name)
        self.tracker.start_timer()

    def _stop_tracking(self) -> None:
        """Stop timer and finalize tracking."""
        self.tracker.stop_timer()
        self.tracker.finish_tracking()

    @abstractmethod
    def _prepare_solver_args(self, parameters: List[Any]) -> Dict[str, Any]:
        """Prepare keyword-arguments for the underlying solver.

        Args:
            parameters: List of free parameters to be fitted.

        Returns:
            Mapping of keyword arguments to pass into ``_run_solver``.
        """
        pass

    @abstractmethod
    def _run_solver(
        self,
        objective_function: Callable[..., Any],
        engine_parameters: Dict[str, Any],
    ) -> Any:
        """Execute the concrete solver and return its raw result."""
        pass

    @abstractmethod
    def _sync_result_to_parameters(
        self,
        raw_result: Any,
        parameters: List[Any],
    ) -> None:
        """Copy values from ``raw_result`` back to ``parameters`` in-
        place.
        """
        pass

    def _finalize_fit(
        self,
        parameters: List[Any],
        raw_result: Any,
    ) -> FitResults:
        """Build :class:`FitResults` and store it on ``self.result``.

        Args:
            parameters: Parameters after the solver finished.
            raw_result: Backend-specific solver output object.

        Returns:
            FitResults: Aggregated outcome of the fit.
        """
        self._sync_result_to_parameters(parameters, raw_result)
        success = self._check_success(raw_result)
        self.result = FitResults(
            success=success,
            parameters=parameters,
            reduced_chi_square=self.tracker.best_chi2,
            engine_result=raw_result,
            starting_parameters=parameters,
            fitting_time=self.tracker.fitting_time,
        )
        return self.result

    @abstractmethod
    def _check_success(self, raw_result: Any) -> bool:
        """Determine whether the fit was successful."""
        pass

    def fit(
        self,
        parameters: List[Any],
        objective_function: Callable[..., Any],
    ) -> FitResults:
        """Run the full minimization workflow.

        Args:
            parameters: Free parameters to optimize.
            objective_function: Callable returning residuals for a given
                set of engine arguments.

        Returns:
            FitResults with success flag, best chi2 and timing.
        """
        minimizer_name = self.name or 'Unnamed Minimizer'
        if self.method is not None:
            minimizer_name += f' ({self.method})'

        self._start_tracking(minimizer_name)

        solver_args = self._prepare_solver_args(parameters)
        raw_result = self._run_solver(objective_function, **solver_args)

        self._stop_tracking()

        result = self._finalize_fit(parameters, raw_result)

        return result

    def _objective_function(
        self,
        engine_params: Dict[str, Any],
        parameters: List[Any],
        sample_models: Any,
        experiments: Any,
        calculator: Any,
    ) -> np.ndarray:
        """Default objective helper computing residuals array."""
        return self._compute_residuals(
            engine_params,
            parameters,
            sample_models,
            experiments,
            calculator,
        )

    def _create_objective_function(
        self,
        parameters: List[Any],
        sample_models: Any,
        experiments: Any,
        calculator: Any,
    ) -> Callable[[Dict[str, Any]], np.ndarray]:
        """Return a closure capturing problem context for the solver."""
        return lambda engine_params: self._objective_function(
            engine_params,
            parameters,
            sample_models,
            experiments,
            calculator,
        )
