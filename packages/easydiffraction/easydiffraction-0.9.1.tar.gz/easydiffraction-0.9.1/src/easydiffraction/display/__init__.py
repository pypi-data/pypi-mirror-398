# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Display subsystem for tables and plots.

This package contains user-facing facades and backend implementations
to render tabular data and plots in different environments.

- Tables: see :mod:`easydiffraction.display.tables` and the engines in
        :mod:`easydiffraction.display.tablers`.
- Plots: see :mod:`easydiffraction.display.plotting` and the engines in
        :mod:`easydiffraction.display.plotters`.
"""

# TODO: The following works in Jupyter, but breaks MkDocs builds.
#  Disable for now.
# from easydiffraction.display.utils import JupyterScrollManager
# JupyterScrollManager.disable_jupyter_scroll()
