"""Dependency detection for vmux.

Magic detection flow:
1. If directory has pyproject.toml + uv.lock → it's a uv project, use uv run
2. Else, parse script imports → find editable installs → bundle them
"""

import ast
import importlib.util
import subprocess
import sys
import tomllib
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class EditablePackage:
    """An editable-installed package."""
    name: str
    path: Path  # Source directory
    has_uv_lock: bool


@dataclass
class ScriptDeps:
    """Dependencies detected from a script."""
    editables: list[EditablePackage] = field(default_factory=list)
    requirements: str | None = None  # From editable's uv.lock


def _resolve_editable_project_root(pkg_name: str, editable_project_location: Path) -> Path:
    """Best-effort resolution of the installable project root for an editable.

    Some monorepos report the repo root as the editable project location, but the
    actual installable project (with pyproject.toml) lives in a subdirectory.
    """
    editable_project_location = editable_project_location.resolve()

    if (editable_project_location / "pyproject.toml").exists():
        return editable_project_location

    candidates = [
        editable_project_location / pkg_name,
        editable_project_location / pkg_name.replace("-", "_"),
        editable_project_location / pkg_name.replace("_", "-"),
    ]
    for candidate in candidates:
        if (candidate / "pyproject.toml").exists():
            return candidate

    return editable_project_location


def is_uv_project(directory: Path) -> bool:
    """Check if directory is a uv project (has pyproject.toml + uv.lock)."""
    return (directory / "pyproject.toml").exists() and (directory / "uv.lock").exists()


def parse_imports(script_path: Path) -> list[str]:
    """Extract third-party imports from a Python script."""
    try:
        with open(script_path) as f:
            tree = ast.parse(f.read())
    except (SyntaxError, FileNotFoundError):
        return []

    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split('.')[0])

    # Filter out stdlib
    stdlib = set(sys.stdlib_module_names)
    return [i for i in imports if i not in stdlib]


def scan_imports_in_tree(root: Path) -> set[str]:
    """Scan all .py files under root for imported top-level modules."""
    skip_dirs = {".venv", "__pycache__", "node_modules", ".git", "venv", "env", "wandb"}
    imports: set[str] = set()

    for py_file in root.rglob("*.py"):
        if any(part in skip_dirs for part in py_file.parts):
            continue
        try:
            tree = ast.parse(py_file.read_text())
        except (SyntaxError, UnicodeDecodeError, OSError):
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])

    stdlib = set(sys.stdlib_module_names)
    return {i for i in imports if i and i not in stdlib}


def find_editable(pkg_name: str) -> EditablePackage | None:
    """Check if a package is an editable install."""
    spec = importlib.util.find_spec(pkg_name)
    if not spec:
        return None

    # Get pip metadata
    result = subprocess.run(
        ['pip', 'show', pkg_name],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return None

    # Parse output
    info = {}
    for line in result.stdout.splitlines():
        if ':' in line:
            key, value = line.split(':', 1)
            info[key.strip().lower().replace(' ', '_')] = value.strip()

    editable_loc = info.get('editable_project_location')
    if not editable_loc:
        return None

    editable_path = _resolve_editable_project_root(pkg_name, Path(editable_loc))
    return EditablePackage(
        name=pkg_name,
        path=editable_path,
        has_uv_lock=(editable_path / 'uv.lock').exists(),
    )


def detect_script_deps(script_path: Path) -> ScriptDeps:
    """Detect dependencies for a standalone script.

    Parses imports, finds editable installs.
    The container will install dependencies from the editable's uv.lock/pyproject.toml.
    """
    imports = set(parse_imports(script_path))

    editables: list[EditablePackage] = []
    to_scan: list[EditablePackage] = []
    scanned_paths: set[Path] = set()
    find_cache: dict[str, EditablePackage | None] = {}

    def cached_find(name: str) -> EditablePackage | None:
        if name not in find_cache:
            find_cache[name] = find_editable(name)
        return find_cache[name]

    # Direct editables imported by the script
    for pkg_name in sorted(imports):
        editable = cached_find(pkg_name)
        if editable and all(e.name != editable.name for e in editables):
            editables.append(editable)
            to_scan.append(editable)

    # Transitive editables imported by those editables
    while to_scan:
        editable = to_scan.pop()
        editable_path = editable.path.resolve()
        if editable_path in scanned_paths:
            continue
        scanned_paths.add(editable_path)

        for dep_name in sorted(scan_imports_in_tree(editable_path)):
            dep_editable = cached_find(dep_name)
            if dep_editable and all(e.name != dep_editable.name for e in editables):
                editables.append(dep_editable)
                to_scan.append(dep_editable)

    # Don't bundle requirements.lock - let container auto-install handle it based on
    # the workspace/dep pyproject.toml/uv.lock. We only need the editable sources.
    return ScriptDeps(editables=editables, requirements=None)


def extract_script_from_command(command: str) -> Path | None:
    """Extract the Python script path from a command.

    'python train.py --arg' → Path('train.py')
    'ENVVAR=x python foo.py' → Path('foo.py')
    """
    parts = command.split()

    # Skip env vars at start
    while parts and '=' in parts[0]:
        parts.pop(0)

    # Find python followed by .py file
    for i, part in enumerate(parts):
        if part in ('python', 'python3') and i + 1 < len(parts):
            next_part = parts[i + 1]
            if next_part.endswith('.py'):
                return Path(next_part)

    return None
