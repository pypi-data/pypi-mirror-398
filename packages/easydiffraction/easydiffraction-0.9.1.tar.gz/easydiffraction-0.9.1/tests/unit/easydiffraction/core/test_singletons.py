# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

import pytest


def test_uid_map_handler_rejects_non_descriptor():
    from easydiffraction.core.singletons import UidMapHandler

    h = UidMapHandler.get()
    with pytest.raises(TypeError):
        h.add_to_uid_map(object())
