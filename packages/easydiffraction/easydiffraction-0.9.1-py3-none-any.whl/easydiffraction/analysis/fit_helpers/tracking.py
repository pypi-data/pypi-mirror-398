# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

import time
from contextlib import suppress
from typing import Any
from typing import List
from typing import Optional

import numpy as np

from easydiffraction.utils.logging import console

try:
    from IPython.display import HTML
    from IPython.display import DisplayHandle
    from IPython.display import display
except ImportError:
    display = None
    clear_output = None

from easydiffraction.analysis.fit_helpers.metrics import calculate_reduced_chi_square
from easydiffraction.utils.environment import in_jupyter
from easydiffraction.utils.utils import render_table

try:
    from rich.live import Live
except Exception:  # pragma: no cover - rich always available in app env
    Live = None  # type: ignore[assignment]

from easydiffraction.utils.logging import ConsoleManager

SIGNIFICANT_CHANGE_THRESHOLD = 0.01  # 1% threshold
DEFAULT_HEADERS = ['iteration', 'χ²', 'improvement [%]']
DEFAULT_ALIGNMENTS = ['center', 'center', 'center']


class _TerminalLiveHandle:
    """Adapter that exposes update()/close() for terminal live updates.

    Wraps a rich.live.Live instance but keeps the tracker decoupled from
    the underlying UI mechanism.
    """

    def __init__(self, live) -> None:
        self._live = live

    def update(self, renderable) -> None:
        self._live.update(renderable, refresh=True)

    def close(self) -> None:
        with suppress(Exception):
            self._live.stop()


def _make_display_handle() -> Any | None:
    """Create and initialize a display/update handle for the
    environment.

    - In Jupyter, returns an IPython DisplayHandle and creates a
        placeholder.
    - In terminal, returns a _TerminalLiveHandle backed by rich Live.
    - If neither applies, returns None.
    """
    if in_jupyter() and display is not None and HTML is not None:
        h = DisplayHandle()
        # Create an empty placeholder area to update in place
        h.display(HTML(''))
        return h
    if Live is not None:
        # Reuse the shared Console to coordinate with logging output
        # and keep consistent width
        live = Live(console=ConsoleManager.get(), auto_refresh=True)
        live.start()
        return _TerminalLiveHandle(live)
    return None


class FitProgressTracker:
    """Track and report reduced chi-square during optimization.

    The tracker keeps iteration counters, remembers the best observed
    reduced chi-square and when it occurred, and can display progress as
    a table in notebooks or a text UI in terminals.
    """

    def __init__(self) -> None:
        self._iteration: int = 0
        self._previous_chi2: Optional[float] = None
        self._last_chi2: Optional[float] = None
        self._last_iteration: Optional[int] = None
        self._best_chi2: Optional[float] = None
        self._best_iteration: Optional[int] = None
        self._fitting_time: Optional[float] = None

        self._df_rows: List[List[str]] = []
        self._display_handle: Optional[Any] = None
        self._live: Optional[Any] = None

    def reset(self) -> None:
        """Reset internal state before a new optimization run."""
        self._iteration = 0
        self._previous_chi2 = None
        self._last_chi2 = None
        self._last_iteration = None
        self._best_chi2 = None
        self._best_iteration = None
        self._fitting_time = None

    def track(
        self,
        residuals: np.ndarray,
        parameters: List[float],
    ) -> np.ndarray:
        """Update progress with current residuals and parameters.

        Args:
            residuals: Residuals between measured and calculated data.
            parameters: Current free parameters being fitted.

        Returns:
            Residuals unchanged, for optimizer consumption.
        """
        self._iteration += 1

        reduced_chi2 = calculate_reduced_chi_square(residuals, len(parameters))

        row: List[str] = []

        # First iteration, initialize tracking
        if self._previous_chi2 is None:
            self._previous_chi2 = reduced_chi2
            self._best_chi2 = reduced_chi2
            self._best_iteration = self._iteration

            row = [
                str(self._iteration),
                f'{reduced_chi2:.2f}',
                '',
            ]

        # Subsequent iterations, check for significant changes
        else:
            change = (self._previous_chi2 - reduced_chi2) / self._previous_chi2

            # Improvement check
            if change > SIGNIFICANT_CHANGE_THRESHOLD:
                change_in_percent = change * 100

                row = [
                    str(self._iteration),
                    f'{reduced_chi2:.2f}',
                    f'{change_in_percent:.1f}% ↓',
                ]

                self._previous_chi2 = reduced_chi2

        # Output if there is something new to display
        if row:
            self.add_tracking_info(row)

        # Update best chi-square if better
        if reduced_chi2 < self._best_chi2:
            self._best_chi2 = reduced_chi2
            self._best_iteration = self._iteration

        # Store last chi-square and iteration
        self._last_chi2 = reduced_chi2
        self._last_iteration = self._iteration

        return residuals

    @property
    def best_chi2(self) -> Optional[float]:
        """Best recorded reduced chi-square value or None."""
        return self._best_chi2

    @property
    def best_iteration(self) -> Optional[int]:
        """Iteration index at which the best chi-square was observed."""
        return self._best_iteration

    @property
    def iteration(self) -> int:
        """Current iteration counter."""
        return self._iteration

    @property
    def fitting_time(self) -> Optional[float]:
        """Elapsed time of the last run in seconds, if available."""
        return self._fitting_time

    def start_timer(self) -> None:
        """Begin timing of a fit run."""
        self._start_time = time.perf_counter()

    def stop_timer(self) -> None:
        """Stop timing and store elapsed time for the run."""
        self._end_time = time.perf_counter()
        self._fitting_time = self._end_time - self._start_time

    def start_tracking(self, minimizer_name: str) -> None:
        """Initialize display and headers and announce the minimizer.

        Args:
            minimizer_name: Name of the minimizer used for the run.
        """
        console.print(f"🚀 Starting fit process with '{minimizer_name}'...")
        console.print('📈 Goodness-of-fit (reduced χ²) change:')

        # Reset rows and create an environment-appropriate handle
        self._df_rows = []
        self._display_handle = _make_display_handle()

        # Initial empty table; subsequent updates will reuse the handle
        render_table(
            columns_headers=DEFAULT_HEADERS,
            columns_alignment=DEFAULT_ALIGNMENTS,
            columns_data=self._df_rows,
            display_handle=self._display_handle,
        )

    def add_tracking_info(self, row: List[str]) -> None:
        """Append a formatted row to the progress display.

        Args:
            row: Columns corresponding to DEFAULT_HEADERS.
        """
        # Append and update via the active handle (Jupyter or
        # terminal live)
        self._df_rows.append(row)
        render_table(
            columns_headers=DEFAULT_HEADERS,
            columns_alignment=DEFAULT_ALIGNMENTS,
            columns_data=self._df_rows,
            display_handle=self._display_handle,
        )

    def finish_tracking(self) -> None:
        """Finalize progress display and print best result summary."""
        # Add last iteration as last row
        row: List[str] = [
            str(self._last_iteration),
            f'{self._last_chi2:.2f}' if self._last_chi2 is not None else '',
            '',
        ]
        self.add_tracking_info(row)

        # Close terminal live if used
        if self._display_handle is not None and hasattr(self._display_handle, 'close'):
            with suppress(Exception):
                self._display_handle.close()

        # Print best result
        console.print(
            f'🏆 Best goodness-of-fit (reduced χ²) is {self._best_chi2:.2f} '
            f'at iteration {self._best_iteration}'
        )
        console.print('✅ Fitting complete.')
