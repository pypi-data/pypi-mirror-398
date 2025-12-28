# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

def test_minimizer_factory_list_and_show(capsys):
    from easydiffraction.analysis.minimizers.factory import MinimizerFactory

    lst = MinimizerFactory.list_available_minimizers()
    assert isinstance(lst, list) and len(lst) >= 1
    MinimizerFactory.show_available_minimizers()
    out = capsys.readouterr().out
    assert 'Supported minimizers' in out


def test_minimizer_factory_unknown_raises():
    from easydiffraction.analysis.minimizers.factory import MinimizerFactory

    try:
        MinimizerFactory.create_minimizer('___unknown___')
    except ValueError as e:
        assert 'Unknown minimizer' in str(e)
    else:
        assert False, 'Expected ValueError'


def test_minimizer_factory_create_known_and_register(monkeypatch):
    from easydiffraction.analysis.minimizers.base import MinimizerBase
    from easydiffraction.analysis.minimizers.factory import MinimizerFactory

    # Create a known minimizer instance (lmfit (leastsq) exists)
    m = MinimizerFactory.create_minimizer('lmfit (leastsq)')
    assert isinstance(m, MinimizerBase)

    # Register a custom minimizer and create it
    class Custom(MinimizerBase):
        def _prepare_solver_args(self, parameters):
            return {}

        def _run_solver(self, objective_function, **kwargs):
            return None

        def _sync_result_to_parameters(self, raw_result, parameters):
            pass

        def _check_success(self, raw_result):
            return True

    MinimizerFactory.register_minimizer(
        name='custom-test', minimizer_cls=Custom, method=None, description='x'
    )
    created = MinimizerFactory.create_minimizer('custom-test')
    assert isinstance(created, Custom)
