# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import os
import sys
from importlib.util import find_spec


def in_pytest() -> bool:
    return 'pytest' in sys.modules


def in_warp() -> bool:
    return os.getenv('TERM_PROGRAM') == 'WarpTerminal'


def in_pycharm() -> bool:
    """Determines if the current environment is PyCharm.

    Returns:
        bool: True if running inside PyCharm, False otherwise.
    """
    return os.environ.get('PYCHARM_HOSTED') == '1'


def in_colab() -> bool:
    """Determines if the current environment is Google Colab.

    Returns:
        bool: True if running in Google Colab, False otherwise.
    """
    try:
        return find_spec('google.colab') is not None
    except ModuleNotFoundError:  # pragma: no cover - importlib edge case
        return False


def in_jupyter() -> bool:
    """Return True when running inside a Jupyter Notebook.

    Returns:
        bool: True if inside a Jupyter Notebook, False otherwise.
    """
    try:
        import IPython  # type: ignore[import-not-found]
    except ImportError:  # pragma: no cover - optional dependency
        ipython_mod = None
    else:
        ipython_mod = IPython
    if ipython_mod is None:
        return False
    if in_pycharm():
        return False
    if in_colab():
        return True

    try:
        ip = ipython_mod.get_ipython()  # type: ignore[attr-defined]
        if ip is None:
            return False
        # Prefer config-based detection when available (works with
        # tests).
        has_cfg = hasattr(ip, 'config') and isinstance(ip.config, dict)
        if has_cfg and 'IPKernelApp' in ip.config:  # type: ignore[index]
            return True
        shell = ip.__class__.__name__
        if shell == 'ZMQInteractiveShell':  # Jupyter or qtconsole
            return True
        if shell == 'TerminalInteractiveShell':
            return False
        return False
    except Exception:
        return False


def in_github_ci() -> bool:
    """Return True when running under GitHub Actions CI.

    Returns:
        bool: True if env var ``GITHUB_ACTIONS`` is set, False
        otherwise.
    """
    return os.environ.get('GITHUB_ACTIONS') is not None


# ----------------------------------------------------------------------
# IPython/Jupyter helpers
# ----------------------------------------------------------------------


def is_ipython_display_handle(obj: object) -> bool:
    """Return True if ``obj`` is an IPython DisplayHandle instance.

    Tries to import ``IPython.display.DisplayHandle`` and uses
    ``isinstance`` when available. Falls back to a conservative
    module name heuristic if IPython is missing. Any errors result
    in ``False``.
    """
    try:  # Fast path when IPython is available
        from IPython.display import DisplayHandle  # type: ignore[import-not-found]

        try:
            return isinstance(obj, DisplayHandle)
        except Exception:
            return False
    except Exception:
        # Fallback heuristic when IPython is unavailable
        try:
            mod = getattr(getattr(obj, '__class__', None), '__module__', '')
            return isinstance(mod, str) and mod.startswith('IPython')
        except Exception:
            return False


def can_update_ipython_display() -> bool:
    """Return True if IPython HTML display utilities are available.

    This indicates we can safely construct ``IPython.display.HTML`` and
    update a display handle.
    """
    try:
        from IPython.display import HTML  # type: ignore[import-not-found]  # noqa: F401

        return True
    except Exception:
        return False


def can_use_ipython_display(handle: object) -> bool:
    """Return True if we can update the given IPython DisplayHandle.

    Combines type checking of the handle with availability of IPython
    HTML utilities.
    """
    try:
        return is_ipython_display_handle(handle) and can_update_ipython_display()
    except Exception:
        return False
