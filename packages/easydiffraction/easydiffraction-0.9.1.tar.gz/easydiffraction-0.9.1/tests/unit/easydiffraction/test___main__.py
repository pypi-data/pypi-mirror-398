# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from typer.testing import CliRunner

runner = CliRunner()


def test_module_import():
    import easydiffraction.__main__ as MUT

    expected_module_name = 'easydiffraction.__main__'
    actual_module_name = MUT.__name__
    assert expected_module_name == actual_module_name


def test_cli_version_invokes_show_version(monkeypatch, capsys):
    import easydiffraction as ed
    import easydiffraction.__main__ as main_mod

    called = {'ok': False}

    def fake_show_version():
        print('VERSION_OK')
        called['ok'] = True

    monkeypatch.setattr(ed, 'show_version', fake_show_version)
    result = runner.invoke(main_mod.app, ['--version'])
    assert result.exit_code == 0
    assert called['ok']
    assert 'VERSION_OK' in result.stdout


def test_cli_help_shows_and_exits_zero():
    import easydiffraction.__main__ as main_mod

    result = runner.invoke(main_mod.app, ['--help'])
    assert result.exit_code == 0
    assert 'EasyDiffraction command-line interface' in result.stdout


def test_cli_subcommands_call_utils(monkeypatch):
    import easydiffraction as ed
    import easydiffraction.__main__ as main_mod

    logs = []
    monkeypatch.setattr(ed, 'list_tutorials', lambda: logs.append('LIST'))
    monkeypatch.setattr(
        ed,
        'download_all_tutorials',
        lambda destination='tutorials', overwrite=False: logs.append('DOWNLOAD_ALL'),
    )
    monkeypatch.setattr(
        ed,
        'download_tutorial',
        lambda id, destination='tutorials', overwrite=False: logs.append(f'DOWNLOAD_{id}'),
    )

    res1 = runner.invoke(main_mod.app, ['list-tutorials'])
    res2 = runner.invoke(main_mod.app, ['download-all-tutorials'])
    res3 = runner.invoke(main_mod.app, ['download-tutorial', '1'])

    assert res1.exit_code == 0
    assert res2.exit_code == 0
    assert res3.exit_code == 0
    assert logs == ['LIST', 'DOWNLOAD_ALL', 'DOWNLOAD_1']
