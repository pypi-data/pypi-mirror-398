# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

import pytest

from easydiffraction.core.diagnostic import Diagnostics


class DummyLogger:
    def __init__(self):
        self.last = None

    def error(self, message, exc_type):
        self.last = ('error', message, exc_type)

    def debug(self, message):
        self.last = ('debug', message)


def test_diagnostics_error_and_debug_monkeypatch(monkeypatch: pytest.MonkeyPatch):
    dummy = DummyLogger()
    # Patch module-level log used by Diagnostics
    import easydiffraction.core.diagnostic as diag_mod

    monkeypatch.setattr(diag_mod, 'log', dummy, raising=True)

    Diagnostics.no_value('x', default=1)
    assert dummy.last[0] == 'debug'

    Diagnostics.type_mismatch('x', value=3, expected_type=int)
    kind, msg, exc = dummy.last
    assert kind == 'error'
    assert issubclass(exc, TypeError)
