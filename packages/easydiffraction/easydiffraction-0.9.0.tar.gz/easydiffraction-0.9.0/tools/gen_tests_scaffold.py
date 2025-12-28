# SPDX-FileCopyrightText: 2025 EasyDiffraction contributors
# SPDX-License-Identifier: BSD-3-Clause

"""Generate a one-to-one unit test scaffold mirroring src/ folder
structure.
- Creates tests/unit/<package path>/test_<module>.py for each Python
    file in src
- Inserts a minimal, consistent pytest skeleton with TODO markers.

Usage:
  pixi run python tools/gen_tests_scaffold.py
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'src'
TESTS_ROOT = ROOT / 'tests' / 'unit'

IGNORED_DIRS = {'__pycache__'}
IGNORED_FILES = {'__init__.py'}

HEADER = """# Auto-generated scaffold. Replace TODOs with concrete tests.
import pytest
import numpy as np

# expected vs actual helpers

def _assert_equal(expected, actual):
    assert expected == actual

"""

TEMPLATE = """
# Module under test: {module_import}

# TODO: Replace with real, small tests per class/method.
# Keep names explicit: expected_*, actual_*; compare in a single assert.

def test_module_import():
    import {module_import} as MUT
    expected_module_name = "{module_import}"
    actual_module_name = MUT.__name__
    _assert_equal(expected_module_name, actual_module_name)
"""


def module_import_from_path(py_path: Path) -> str:
    rel = py_path.relative_to(SRC)
    parts = list(rel.parts)
    parts[-1] = parts[-1].removesuffix('.py')
    # Build import path directly from src-relative parts; do not prefix
    # with the top-level package name to avoid duplication when the
    # first part is already the package (e.g., 'easydiffraction').
    return '.'.join(parts)


def ensure_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # Always (re)write to keep scaffold in sync when the generator
    # evolves
    path.write_text(content)


def ensure_package_dirs(dir_path: Path) -> None:
    """Ensure every directory from TESTS_ROOT to dir_path has an
    __init__.py.

    This makes each folder a package so pytest assigns unique module
    names and avoids import file mismatch when multiple files share the
    same basename (e.g., test_base.py) across different subdirectories.
    """
    # Walk from TESTS_ROOT down to dir_path, creating __init__.py at
    # each level
    dir_path.mkdir(parents=True, exist_ok=True)
    current = TESTS_ROOT
    # If dir_path is the same as TESTS_ROOT, the loop will be skipped,
    # but we still want to ensure __init__.py at TESTS_ROOT
    for part in dir_path.relative_to(TESTS_ROOT).parts:
        (current / '__init__.py').touch(exist_ok=True)
        current = current / part
    # Ensure the final directory also has __init__.py
    (current / '__init__.py').touch(exist_ok=True)


def main():
    for py in SRC.rglob('*.py'):
        if py.name in IGNORED_FILES:
            continue
        if any(p in IGNORED_DIRS for p in py.parts):
            continue
        module_import = module_import_from_path(py)
        rel_dir = py.parent.relative_to(SRC)
        test_dir = TESTS_ROOT / rel_dir
        # Ensure package __init__.py files exist to avoid name
        # collisions
        ensure_package_dirs(test_dir)
        test_file = test_dir / f'test_{py.stem}.py'
        content = HEADER + TEMPLATE.format(module_import=module_import)
        ensure_file(test_file, content)
    print(f'Scaffold created/updated under: {TESTS_ROOT}')


if __name__ == '__main__':
    main()
