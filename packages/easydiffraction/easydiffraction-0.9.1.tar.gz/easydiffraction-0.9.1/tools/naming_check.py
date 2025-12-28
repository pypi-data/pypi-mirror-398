"""Check naming consistency across the EasyDiffraction source tree.

Rules enforced:
- Concrete implementations: <variant>.py in <role>s/ directories →
    <Variant><Role>
- Abstract bases: <role>_base.py → <Role>Base
- Factories: <role>_factory.py → <Role>Factory
- Enums: <role>_enum.py → <Role>Enum
- Mixins: <role>_mixins.py → <Role>Mixin (or multiple classes)
- Directories like fit_support/, calculators/, minimizers/, etc. are
    scanned recursively.

Exit code 1 if any mismatches are found.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'src' / 'easydiffraction'
PATTERNS = {
    '_base': r'(?P<role>[A-Z][a-zA-Z0-9]*)Base',
    '_factory': r'(?P<role>[A-Z][a-zA-Z0-9]*)Factory',
    '_enum': r'(?P<role>[A-Z][a-zA-Z0-9]*)Enum',
    '_mixins?': r'(?P<role>[A-Z][a-zA-Z0-9]*)Mixin',
}


def extract_classes(file_path: Path):
    """Return a list of class names defined in the file."""
    content = file_path.read_text(encoding='utf-8', errors='ignore')
    return re.findall(r'^\s*class\s+([A-Z][A-Za-z0-9_]*)', content, flags=re.MULTILINE)


def snake_to_pascal(snake: str) -> str:
    """Convert 'crysfml_calculator' → 'CrysfmlCalculator'."""
    return ''.join(part.capitalize() for part in snake.split('_'))


def check_file(file_path: Path):
    """Validate naming conventions for a single file."""
    rel = file_path.relative_to(ROOT)
    stem = file_path.stem
    classes = extract_classes(file_path)
    problems = []

    # Ignore __init__.py and private modules
    if stem.startswith('__'):
        return []

    # Expected class names
    expected = []

    # Handle base/factory/enum/mixin
    for key, pattern in PATTERNS.items():
        if stem.endswith(key):
            role = stem.replace(key, '')
            expected.append(
                re.compile(pattern.replace('(?P<role>', f'(?P<role>{snake_to_pascal(role)}'))
            )
            break
    else:
        # Default: if file is in a known role directory, use that role
        parent = file_path.parent.name
        known_roles = ('calculators', 'minimizers', 'plotters', 'instruments', 'peaks')
        if parent in known_roles:
            role = snake_to_pascal(parent[:-1])  # remove trailing 's' for role
            if stem == 'base':
                expected_name = f'{role}Base'
            elif stem == 'factory':
                expected_name = f'{role}Factory'
            else:
                variant = snake_to_pascal(stem)
                expected_name = f'{variant}{role}'
            expected.append(re.compile(f'^{expected_name}$'))
        else:
            # Otherwise, expect class name to match the PascalCase file
            # stem
            expected_name = snake_to_pascal(stem)
            expected.append(re.compile(f'^{expected_name}$'))

    # Compare classes
    if not classes:
        problems.append(f'{rel}: No class definitions found')
        return problems

    match_found = False
    for exp in expected:
        for cls in classes:
            if exp.match(cls):
                match_found = True
                break
    if not match_found:
        problems.append(f'{rel}: Unexpected class name(s): {", ".join(classes)}')

    return problems


def main():
    problems = []
    for file_path in ROOT.rglob('*.py'):
        if any(skip in file_path.parts for skip in ('__pycache__', 'venv', '.venv', 'tests')):
            continue
        problems.extend(check_file(file_path))

    if problems:
        print('❌ Naming convention violations found:\n')
        for p in problems:
            print(' -', p)
        print(f'\nTotal issues: {len(problems)}')
        sys.exit(1)

    print('✅ All file/class names follow naming conventions.')


if __name__ == '__main__':
    main()
