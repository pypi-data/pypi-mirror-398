# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

def test_how_to_access_parameters_prints_paths_and_uids(capsys, monkeypatch):
    from easydiffraction.analysis.analysis import Analysis
    from easydiffraction.core.parameters import Parameter
    from easydiffraction.core.validation import AttributeSpec
    from easydiffraction.core.validation import DataTypes
    from easydiffraction.io.cif.handler import CifHandler
    import easydiffraction.analysis.analysis as analysis_mod

    # Build two parameters with identity metadata set directly
    def make_param(db, cat, entry, name, val):
        p = Parameter(
            name=name,
            value_spec=AttributeSpec(value=val, type_=DataTypes.NUMERIC, default=0.0),
            cif_handler=CifHandler(names=[f'_{cat}.{name}']),
        )
        # Inject identity metadata (avoid parent chain)
        p._identity.datablock_entry_name = lambda: db
        p._identity.category_code = cat
        if entry:
            p._identity.category_entry_name = lambda: entry
        else:
            p._identity.category_entry_name = lambda: ''
        return p

    p1 = make_param('db1', 'catA', '', 'alpha', 1.0)
    p2 = make_param('db2', 'catB', 'row1', 'beta', 2.0)

    class Coll:
        def __init__(self, params):
            self.parameters = params

    class Project:
        _varname = 'proj'

        def __init__(self):
            self.sample_models = Coll([p1])
            self.experiments = Coll([p2])

    # Capture the table payload by monkeypatching render_table to avoid
    # terminal wrapping/ellipsis affecting string matching.
    captured = {}

    def fake_render_table(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(analysis_mod, 'render_table', fake_render_table)
    a = Analysis(Project())
    a.how_to_access_parameters()

    out = capsys.readouterr().out
    assert 'How to access parameters' in out

    # Validate headers and row contents independent of terminal renderer
    headers = captured.get('columns_headers') or []
    data = captured.get('columns_data') or []

    assert 'How to Access in Python Code' in headers

    # Flatten rows to strings for simple membership checks
    flat_rows = [' '.join(map(str, row)) for row in data]

    # Python access paths
    assert any("proj.sample_models['db1'].catA.alpha" in r for r in flat_rows)
    assert any("proj.experiments['db2'].catB['row1'].beta" in r for r in flat_rows)

    # Now check CIF unique identifiers via the new API
    captured2 = {}

    def fake_render_table2(**kwargs):
        captured2.update(kwargs)

    monkeypatch.setattr(analysis_mod, 'render_table', fake_render_table2)
    a.show_parameter_cif_uids()
    headers2 = captured2.get('columns_headers') or []
    data2 = captured2.get('columns_data') or []
    assert 'Unique Identifier for CIF Constraints' in headers2
    flat_rows2 = [' '.join(map(str, row)) for row in data2]
    # Unique names are datablock.category[.entry].parameter
    assert any('db1 catA  alpha' in r.replace('.', ' ') for r in flat_rows2)
    assert any('db2 catB row1 beta' in r.replace('.', ' ') for r in flat_rows2)
