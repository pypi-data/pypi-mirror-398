# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

"""Generate project package structure markdown files.

Outputs two docs under docs/architecture/:
 - package-structure-short.md  (folders/files only)
 - package-structure-full.md   (folders/files and classes)

Run (from repo root):
    pixi run python tools/generate_package_docs.py
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import List

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / 'src' / 'easydiffraction'
DOCS_OUT_DIR = REPO_ROOT / 'docs' / 'architecture'


IGNORE_DIRS = {
    '__pycache__',
    '.pytest_cache',
    '.mypy_cache',
    '.ruff_cache',
    '.ipynb_checkpoints',
}


@dataclass
class Node:
    name: str
    path: Path
    type: str  # 'dir' | 'file'
    children: List['Node'] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)


def parse_classes(py_path: Path) -> List[str]:
    try:
        src = py_path.read_text(encoding='utf-8')
    except Exception:
        return []
    try:
        tree = ast.parse(src)
    except Exception:
        return []
    classes: List[str] = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            classes.append(node.name)
    return classes


def build_tree(root: Path) -> Node:
    def _walk(p: Path) -> Node:
        if p.is_dir():
            node = Node(name=p.name, path=p, type='dir')
            try:
                entries = sorted(p.iterdir(), key=lambda q: (q.is_file(), q.name.lower()))
            except PermissionError:
                entries = []
            for child in entries:
                if child.name in IGNORE_DIRS:
                    continue
                if child.is_dir():
                    node.children.append(_walk(child))
                elif child.suffix == '.py':
                    file_node = Node(name=child.name, path=child, type='file')
                    file_node.classes = parse_classes(child)
                    node.children.append(file_node)
            return node
        else:
            n = Node(name=p.name, path=p, type='file')
            n.classes = parse_classes(p) if p.suffix == '.py' else []
            return n

    return _walk(root)


def _branch(prefix: str, is_last: bool) -> str:
    return f'{prefix}{"└── " if is_last else "├── "}'


def render_short(root: Node) -> List[str]:
    lines: List[str] = []
    lines.append(f'📦 {root.name}')

    def _render(node: Node, prefix: str = '') -> None:
        for idx, child in enumerate(node.children):
            is_last = idx == len(node.children) - 1
            line_prefix = _branch(prefix, is_last)
            if child.type == 'dir':
                lines.append(f'{line_prefix}📁 {child.name}')
                _render(child, prefix + ('    ' if is_last else '│   '))
            else:
                lines.append(f'{line_prefix}📄 {child.name}')

    _render(root)
    return lines


def render_full(root: Node) -> List[str]:
    lines: List[str] = []
    lines.append(f'📦 {root.name}')

    def _render(node: Node, prefix: str = '') -> None:
        for idx, child in enumerate(node.children):
            is_last = idx == len(node.children) - 1
            line_prefix = _branch(prefix, is_last)
            if child.type == 'dir':
                lines.append(f'{line_prefix}📁 {child.name}')
                _render(child, prefix + ('    ' if is_last else '│   '))
            else:
                lines.append(f'{line_prefix}📄 {child.name}')
                # Classes under file
                for c_idx, cls in enumerate(child.classes):
                    c_last = c_idx == len(child.classes) - 1
                    sub_prefix = prefix + ('    ' if is_last else '│   ')
                    lines.append(f'{_branch(sub_prefix, c_last)}🏷️ class {cls}')

    _render(root)
    return lines


def write_markdown(short_lines: List[str], full_lines: List[str]) -> None:
    DOCS_OUT_DIR.mkdir(parents=True, exist_ok=True)

    short_md = DOCS_OUT_DIR / 'package-structure-short.md'
    full_md = DOCS_OUT_DIR / 'package-structure-full.md'

    short_content = [
        '# Package Structure (short)',
        '',
        '```',
        *short_lines,
        '```',
        '',
    ]
    full_content = [
        '# Package Structure (full)',
        '',
        '```',
        *full_lines,
        '```',
        '',
    ]

    short_md.write_text('\n'.join(short_content), encoding='utf-8')
    full_md.write_text('\n'.join(full_content), encoding='utf-8')

    print(f'Wrote: {short_md.relative_to(REPO_ROOT)}')
    print(f'Wrote: {full_md.relative_to(REPO_ROOT)}')


def main() -> None:
    if not SRC_ROOT.exists():
        raise SystemExit(f'Source root not found: {SRC_ROOT}')
    root = build_tree(SRC_ROOT)
    short_lines = render_short(root)
    full_lines = render_full(root)
    write_markdown(short_lines, full_lines)


if __name__ == '__main__':
    main()
