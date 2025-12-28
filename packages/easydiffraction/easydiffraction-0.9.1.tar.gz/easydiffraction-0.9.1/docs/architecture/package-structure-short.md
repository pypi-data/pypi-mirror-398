# Package Structure (short)

```
📦 easydiffraction
├── 📁 analysis
│   ├── 📁 calculators
│   │   ├── 📄 __init__.py
│   │   ├── 📄 base.py
│   │   ├── 📄 crysfml.py
│   │   ├── 📄 cryspy.py
│   │   ├── 📄 factory.py
│   │   └── 📄 pdffit.py
│   ├── 📁 categories
│   │   ├── 📄 __init__.py
│   │   ├── 📄 aliases.py
│   │   ├── 📄 constraints.py
│   │   └── 📄 joint_fit_experiments.py
│   ├── 📁 fit_helpers
│   │   ├── 📄 __init__.py
│   │   ├── 📄 metrics.py
│   │   ├── 📄 reporting.py
│   │   └── 📄 tracking.py
│   ├── 📁 minimizers
│   │   ├── 📄 __init__.py
│   │   ├── 📄 base.py
│   │   ├── 📄 dfols.py
│   │   ├── 📄 factory.py
│   │   └── 📄 lmfit.py
│   ├── 📄 __init__.py
│   ├── 📄 analysis.py
│   └── 📄 fitting.py
├── 📁 core
│   ├── 📄 __init__.py
│   ├── 📄 category.py
│   ├── 📄 collection.py
│   ├── 📄 datablock.py
│   ├── 📄 diagnostic.py
│   ├── 📄 factory.py
│   ├── 📄 guard.py
│   ├── 📄 identity.py
│   ├── 📄 parameters.py
│   ├── 📄 singletons.py
│   └── 📄 validation.py
├── 📁 crystallography
│   ├── 📄 __init__.py
│   ├── 📄 crystallography.py
│   └── 📄 space_groups.py
├── 📁 display
│   ├── 📁 plotters
│   │   ├── 📄 __init__.py
│   │   ├── 📄 ascii.py
│   │   ├── 📄 base.py
│   │   └── 📄 plotly.py
│   ├── 📁 tablers
│   │   ├── 📄 __init__.py
│   │   ├── 📄 base.py
│   │   ├── 📄 pandas.py
│   │   └── 📄 rich.py
│   ├── 📄 __init__.py
│   ├── 📄 base.py
│   ├── 📄 plotting.py
│   ├── 📄 tables.py
│   └── 📄 utils.py
├── 📁 experiments
│   ├── 📁 categories
│   │   ├── 📁 background
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 base.py
│   │   │   ├── 📄 chebyshev.py
│   │   │   ├── 📄 enums.py
│   │   │   ├── 📄 factory.py
│   │   │   └── 📄 line_segment.py
│   │   ├── 📁 data
│   │   │   ├── 📄 bragg_pd.py
│   │   │   ├── 📄 bragg_sc.py
│   │   │   ├── 📄 factory.py
│   │   │   └── 📄 total.py
│   │   ├── 📁 instrument
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 base.py
│   │   │   ├── 📄 cwl.py
│   │   │   ├── 📄 factory.py
│   │   │   └── 📄 tof.py
│   │   ├── 📁 peak
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 base.py
│   │   │   ├── 📄 cwl.py
│   │   │   ├── 📄 cwl_mixins.py
│   │   │   ├── 📄 factory.py
│   │   │   ├── 📄 tof.py
│   │   │   ├── 📄 tof_mixins.py
│   │   │   ├── 📄 total.py
│   │   │   └── 📄 total_mixins.py
│   │   ├── 📄 __init__.py
│   │   ├── 📄 excluded_regions.py
│   │   ├── 📄 experiment_type.py
│   │   └── 📄 linked_phases.py
│   ├── 📁 experiment
│   │   ├── 📄 __init__.py
│   │   ├── 📄 base.py
│   │   ├── 📄 bragg_pd.py
│   │   ├── 📄 bragg_sc.py
│   │   ├── 📄 enums.py
│   │   ├── 📄 factory.py
│   │   ├── 📄 instrument_mixin.py
│   │   └── 📄 total_pd.py
│   ├── 📄 __init__.py
│   └── 📄 experiments.py
├── 📁 io
│   ├── 📁 cif
│   │   ├── 📄 __init__.py
│   │   ├── 📄 handler.py
│   │   ├── 📄 parse.py
│   │   └── 📄 serialize.py
│   └── 📄 __init__.py
├── 📁 project
│   ├── 📄 __init__.py
│   ├── 📄 project.py
│   └── 📄 project_info.py
├── 📁 sample_models
│   ├── 📁 categories
│   │   ├── 📄 __init__.py
│   │   ├── 📄 atom_sites.py
│   │   ├── 📄 cell.py
│   │   └── 📄 space_group.py
│   ├── 📁 sample_model
│   │   ├── 📄 __init__.py
│   │   ├── 📄 base.py
│   │   └── 📄 factory.py
│   ├── 📄 __init__.py
│   └── 📄 sample_models.py
├── 📁 summary
│   ├── 📄 __init__.py
│   └── 📄 summary.py
├── 📁 utils
│   ├── 📄 __init__.py
│   ├── 📄 environment.py
│   ├── 📄 logging.py
│   └── 📄 utils.py
├── 📄 __init__.py
└── 📄 __main__.py
```
