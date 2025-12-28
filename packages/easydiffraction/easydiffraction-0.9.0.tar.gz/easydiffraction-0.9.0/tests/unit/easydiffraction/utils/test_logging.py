# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

def test_module_import():
    import easydiffraction.utils.logging as MUT

    expected_module_name = 'easydiffraction.utils.logging'
    actual_module_name = MUT.__name__
    assert expected_module_name == actual_module_name


def test_logger_configure_and_warn_reaction():
    import easydiffraction.utils.logging as MUT

    # configure to WARN so .error produces warnings and not exceptions
    MUT.log.configure(reaction=MUT.log.Reaction.WARN)
    MUT.log.debug('d')
    MUT.log.info('i')
    MUT.log.warning('w')
    MUT.log.error('e')
    # switch mode/level
    MUT.log.set_level(MUT.log.Level.INFO)
    MUT.log.set_mode(MUT.log.Mode.VERBOSE)
    # nothing to assert; absence of exception is success
    assert True
