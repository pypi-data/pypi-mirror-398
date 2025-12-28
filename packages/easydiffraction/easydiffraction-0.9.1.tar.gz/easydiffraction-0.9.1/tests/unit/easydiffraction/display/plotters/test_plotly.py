# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

def test_module_import():
    import easydiffraction.display.plotters.plotly as MUT

    expected_module_name = 'easydiffraction.display.plotters.plotly'
    actual_module_name = MUT.__name__
    assert expected_module_name == actual_module_name


def test_get_trace_and_plot(monkeypatch):
    import easydiffraction.display.plotters.plotly as pp

    # Arrange: force non-PyCharm branch and stub fig.show/HTML/display so nothing opens
    monkeypatch.setattr(pp, 'in_pycharm', lambda: False)

    shown = {'count': 0}

    class DummyFig:
        def update_xaxes(self, **kwargs):
            pass

        def update_yaxes(self, **kwargs):
            pass

        def show(self, **kwargs):
            shown['count'] += 1

    # Patch go.Scatter and go.Figure to minimal dummies
    class DummyScatter:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class DummyGO:
        class Scatter(DummyScatter):
            pass

        class Figure(DummyFig):
            def __init__(self, data=None, layout=None):
                self.data = data
                self.layout = layout

        class Layout:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

    class DummyPIO:
        @staticmethod
        def to_html(fig, include_plotlyjs=None, full_html=None, config=None):
            return '<div>plot</div>'

    dummy_display_calls = {'count': 0}

    def dummy_display(obj):
        dummy_display_calls['count'] += 1

    class DummyHTML:
        def __init__(self, html):
            self.html = html

    monkeypatch.setattr(pp, 'go', DummyGO)
    monkeypatch.setattr(pp, 'pio', DummyPIO)
    monkeypatch.setattr(pp, 'display', dummy_display)
    monkeypatch.setattr(pp, 'HTML', DummyHTML)

    plotter = pp.PlotlyPlotter()

    # Exercise _get_trace
    x = [0, 1, 2]
    y = [1, 2, 3]
    trace = plotter._get_trace(x, y, label='calc')
    assert hasattr(trace, 'kwargs')
    assert trace.kwargs['x'] == x and trace.kwargs['y'] == y

    # Exercise plot (non-PyCharm, display path)
    plotter.plot(
        x,
        y_series=[y],
        labels=['calc'],
        axes_labels=['x', 'y'],
        title='t',
        height=None,
    )

    # One HTML display call expected
    assert dummy_display_calls['count'] == 1 or shown['count'] == 1
