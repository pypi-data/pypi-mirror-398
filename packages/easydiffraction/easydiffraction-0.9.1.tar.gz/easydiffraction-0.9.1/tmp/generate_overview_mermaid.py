# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

"""Generate an overview Mermaid class diagram dynamically from code.

This script scans the source tree with Python's AST to discover:
 - Classes and their inheritance
 - Key composition relationships (via __init__ assignments or property
     return annotations)
 - Collection "contains" relationships for DatablockCollection

It renders an overview Mermaid classDiagram that automatically adapts
to project structure changes. Analysis internals are intentionally
omitted; we only keep the top-level link from Project to Analysis.

Output: docs/architecture/overview-diagram.md

Run (from repo root):
        pixi run python tools/generate_overview_mermaid.py
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional
from typing import Set
from typing import Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / 'src' / 'easydiffraction'
DOCS_OUT_DIR = REPO_ROOT / 'docs' / 'architecture'
OUT_MD = DOCS_OUT_DIR / 'overview-diagram.md'


@dataclass
class ClassInfo:
    name: str
    module: str  # e.g., experiments/experiment_types/powder.py
    bases: List[str]  # base class names (unqualified)
    category: Optional[str] = None  # container | collection | baseclass | measurement | model
    compositions: Set[str] = field(default_factory=set)  # composed-with class names
    contains: Set[str] = field(default_factory=set)  # collection element types


INCLUDE_FILES = [
    # Project and Summary
    SRC_ROOT / 'project' / 'project.py',
    SRC_ROOT / 'project' / 'project_info.py',
    SRC_ROOT / 'summary' / 'summary.py',
    SRC_ROOT / 'analysis' / 'analysis.py',
    # Sample models
    SRC_ROOT / 'sample_models' / 'sample_models.py',
    SRC_ROOT / 'sample_models' / 'sample_model.py',
    SRC_ROOT / 'sample_models' / 'sample_model_types' / 'base.py',
    # Experiments
    SRC_ROOT / 'experiments' / 'experiments.py',
    SRC_ROOT / 'experiments' / 'experiment.py',
    SRC_ROOT / 'experiments' / 'experiment_types' / 'base.py',
]


def iter_experiment_type_files() -> Iterable[Path]:
    expt_dir = SRC_ROOT / 'experiments' / 'experiment_types'
    if not expt_dir.exists():
        return []
    skip = {'__init__.py', 'base.py', 'enums.py', 'instrument_mixin.py'}
    for py in sorted(expt_dir.glob('*.py')):
        if py.name in skip:
            continue
        yield py


def parse_file(py_path: Path) -> Optional[ast.Module]:
    try:
        src = py_path.read_text(encoding='utf-8')
        return ast.parse(src)
    except Exception:
        return None


def name_from_node(n: ast.AST) -> Optional[str]:
    if isinstance(n, ast.Name):
        return n.id
    if isinstance(n, ast.Attribute):
        # Return attribute tail (unqualified)
        return n.attr
    return None


def discover_classes() -> Dict[str, ClassInfo]:
    files = list(INCLUDE_FILES) + list(iter_experiment_type_files())
    classes: Dict[str, ClassInfo] = {}

    for py in files:
        mod = parse_file(py)
        if not mod:
            continue
        rel_module = str(py.relative_to(SRC_ROOT))
        for node in mod.body:
            if isinstance(node, ast.ClassDef):
                base_names = [name_from_node(b) for b in node.bases]
                base_names = [n for n in base_names if n]
                ci = ClassInfo(name=node.name, module=rel_module, bases=base_names)
                classes[ci.name] = ci

        # Second pass: gather compositions and contains
        for node in mod.body:
            if isinstance(node, ast.ClassDef):
                ci = classes.get(node.name)
                if not ci:
                    continue
                for inner in node.body:
                    # __init__ assignments: self.attr = SomeClass(...)
                    if isinstance(inner, ast.FunctionDef) and inner.name == '__init__':
                        for stmt in ast.walk(inner):
                            if isinstance(stmt, ast.Assign):
                                # Look for Call on RHS
                                if isinstance(stmt.value, ast.Call):
                                    callee = name_from_node(stmt.value.func)
                                    if callee:
                                        ci.compositions.add(callee)
                            if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                                # super().__init__(item_type=SomeClass)
                                call = stmt.value
                                func_name = name_from_node(call.func)
                                if func_name == '__init__' and isinstance(call, ast.Call):
                                    for kw in call.keywords:
                                        if kw.arg == 'item_type':
                                            n = name_from_node(kw.value)
                                            if n:
                                                ci.contains.add(n)
                    # @property return annotation: def x(self) -> SomeClass
                    if isinstance(inner, ast.FunctionDef):
                        if inner.returns is not None:
                            ann = name_from_node(inner.returns)
                            if ann:
                                ci.compositions.add(ann)

    # Categorize
    for ci in classes.values():
        path = ci.module
        # Collections
        if 'DatablockCollection' in ci.bases:
            ci.category = 'collection'
        # Measurement (concrete experiment types)
        elif (
            'experiments/experiment_types/' in path
            and ci.name.endswith('Experiment')
            and not ci.name.startswith('Base')
        ):
            ci.category = 'measurement'
        # Base classes (heuristic)
        elif ci.name.startswith('Base'):
            ci.category = 'baseclass'
        # Models
        elif 'sample_models/' in path and ci.name in {'BaseSampleModel', 'SampleModel'}:
            ci.category = 'model'
        # Containers
        elif path.endswith('project.py') and ci.name == 'Project' or path.endswith('project_info.py') and ci.name == 'ProjectInfo' or path.endswith('summary.py') and ci.name == 'Summary' or path.endswith('analysis/analysis.py') and ci.name == 'Analysis':
            ci.category = 'container'
        # Keep others uncategorized (they will still participate via edges)

    return classes


# -----------------
# Mermaid rendering
# -----------------


def mermaid_header() -> str:
    return 'classDiagram\n'


def mermaid_classes(classes: Dict[str, ClassInfo]) -> str:
    lines: List[str] = []
    for ci in classes.values():
        # Limit to overview classes: containers, collections, models, baseclasses, measurements
        if ci.category in {'container', 'collection', 'model', 'baseclass', 'measurement'}:
            style = f':::{ci.category}' if ci.category else ''
            lines.append(f'    class {ci.name}{style}')
    return '\n'.join(lines) + ('\n\n' if lines else '')


def build_edges(classes: Dict[str, ClassInfo]) -> Tuple[List[str], List[str], List[str]]:
    """Return (inheritance, composition, contains) edge lists."""
    # Work only with classes we render as overview categories
    showable = {
        name
        for name, ci in classes.items()
        if ci.category in {'container', 'collection', 'model', 'baseclass', 'measurement'}
    }

    inheritance: List[str] = []
    composition: List[str] = []
    contains: List[str] = []

    # Inheritance: Parent <|-- Child
    for child_name, ci in classes.items():
        for base in ci.bases:
            if base in showable and child_name in showable:
                inheritance.append(f'    {base} <|-- {child_name}')

    # Composition: A *-- B (if A composes B)
    for a_name, ci in classes.items():
        if a_name not in showable:
            continue
        for b in ci.compositions:
            if b in showable:
                # Special-case: hide Analysis internals; keep only Project *-- Analysis
                if b == 'Analysis' and a_name != 'Project':
                    continue
                composition.append(f'    {a_name} *-- {b}')

    # Contains: Collections "1" -- "*" T : contains
    for a_name, ci in classes.items():
        if ci.category != 'collection':
            continue
        for t in ci.contains:
            if t in classes:
                # Expand Experiments contains Experiment into all concrete measurements
                if a_name == 'Experiments' and t == 'Experiment':
                    for name, c2 in classes.items():
                        if c2.category == 'measurement':
                            contains.append(f'    {a_name} "1" -- "*" {name} : contains')
                else:
                    contains.append(f'    {a_name} "1" -- "*" {t} : contains')

    return inheritance, composition, contains


def mermaid_relationships(classes: Dict[str, ClassInfo]) -> str:
    inh, comp, cont = build_edges(classes)
    lines: List[str] = []
    lines.append('    %% Relationships %%\n')
    if comp or cont or inh:
        lines.append('')
    lines.extend(inh)
    if inh and (comp or cont):
        lines.append('')
    lines.extend(cont)
    if cont and comp:
        lines.append('')
    lines.extend(comp)
    lines.append('\n')
    return '\n'.join(lines)


def mermaid_styles() -> str:
    return (
        '    %%%%%%%%%%%%%\n'
        '    %% STYLING %%\n'
        '    %%%%%%%%%%%%%\n\n'
        '    %% Abstract Base Classes\n'
        '    classDef baseclass fill:#6A5ACD,stroke:#333,stroke-width:1px,color:white;\n\n'
        '    %% Containers (Project, ProjectInfo, Summary, Analysis)\n'
        '    classDef container fill:#455A64,stroke:#333,stroke-width:1px,color:white;\n\n'
        '    %% Collections (SampleModels, Experiments)\n'
        '    classDef collection fill:#607D8B,stroke:#333,stroke-width:1px,color:white;\n\n'
        '    %% Concrete Experiments\n'
        '    classDef measurement fill:#4682B4,stroke:#0D47A1,stroke-width:1px,color:white;\n\n'
        '    %% Models (SampleModel, StructuralModel)\n'
        '    classDef model fill:#009688,stroke:#004D40,stroke-width:1px,color:white;\n'
    )


def build_mermaid() -> str:
    classes = discover_classes()
    parts = [
        mermaid_header(),
        mermaid_classes(classes),
        mermaid_relationships(classes),
        mermaid_styles(),
    ]
    return ''.join(parts)


def write_markdown(mermaid: str) -> None:
    DOCS_OUT_DIR.mkdir(parents=True, exist_ok=True)
    content = [
        '# Architecture Overview',
        '',
        '```mermaid',
        mermaid,
        '```',
        '',
        '> Note: This diagram is auto-generated. Edit tools/generate_overview_mermaid.py to change structure or style.',
        '',
    ]
    OUT_MD.write_text('\n'.join(content), encoding='utf-8')
    rel = OUT_MD.relative_to(REPO_ROOT)
    print(f'Wrote: {rel}')


def main() -> None:
    if not SRC_ROOT.exists():
        raise SystemExit(f'Source root not found: {SRC_ROOT}')
    mermaid = build_mermaid()
    write_markdown(mermaid)


if __name__ == '__main__':
    main()
