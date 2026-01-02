"""Code packaging for vmux.

Simple approach: Bundle code + detected editables. Container auto-installs.
"""

import base64
import fnmatch
import io
import os
import zipfile
from dataclasses import dataclass
from pathlib import Path

from .deps import detect_script_deps, extract_script_from_command


# Patterns to always exclude
EXCLUDE_PATTERNS = {
    # Version control
    ".git", ".hg", ".svn",
    # Python
    "__pycache__", "*.pyc", "*.pyo", "*.egg-info",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", ".tox", ".nox",
    # Virtual environments
    ".venv", "venv", "env", ".conda",
    # Node
    "node_modules",
    # IDE
    ".idea", ".vscode", "*.swp",
    # Build artifacts
    "dist", "build", "*.so", "*.dylib",
    # Secrets
    ".env", ".env.*", "*.pem", "*.key",
    # Large data files
    "*.h5", "*.hdf5", "*.parquet", "*.arrow",
    "*.pkl", "*.pickle", "*.pt", "*.pth",
    "*.ckpt", "*.safetensors", "*.bin", "*.onnx",
    # Logs and experiment outputs
    "*.log", "logs", "wandb", "runs", "outputs", "checkpoints",
    # Visualization/notebooks
    "viz", "*.ipynb_checkpoints",
    # vmux
    ".vmux",
}


def should_exclude(path: Path, base: Path) -> bool:
    """Check if path should be excluded from bundle."""
    rel = path.relative_to(base)
    for part in rel.parts:
        if part in EXCLUDE_PATTERNS:
            return True
        for pattern in EXCLUDE_PATTERNS:
            if "*" in pattern and fnmatch.fnmatch(part, pattern):
                return True
    return False


@dataclass
class Bundle:
    """A packaged bundle ready to send to worker."""
    data: bytes
    editables: list[str]  # Names of bundled editables (for PYTHONPATH)


def package(directory: Path, command: str) -> Bundle:
    """Package a directory for the worker.

    Args:
        directory: Current working directory
        command: The command to run (e.g., "python train.py")

    Returns:
        Bundle with packaged code
    """
    from . import ui

    # Detect editables from script imports
    editables = []
    script_path = extract_script_from_command(command)
    if script_path:
        abs_script = directory / script_path if not script_path.is_absolute() else script_path
        if abs_script.exists():
            deps = detect_script_deps(abs_script)
            editables = deps.editables
            if editables:
                ui.info(f"Detected editables: {[e.name for e in editables]}")

    # Create zip
    buffer = io.BytesIO()
    total_files = 0

    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        # Add main directory
        for root, dirs, files in os.walk(directory):
            root_path = Path(root)
            dirs[:] = [d for d in dirs if not should_exclude(root_path / d, directory)]
            for filename in files:
                file_path = root_path / filename
                if should_exclude(file_path, directory):
                    continue
                arcname = str(file_path.relative_to(directory))
                zf.write(file_path, arcname)
                total_files += 1

        # Add each editable project under _editables/
        # Container will install deps via their uv.lock/pyproject.toml
        for editable in editables:
            ui.info(f"Bundling {editable.name} from {editable.path}")
            for root, dirs, files in os.walk(editable.path):
                root_path = Path(root)
                dirs[:] = [d for d in dirs if not should_exclude(root_path / d, editable.path)]
                for filename in files:
                    file_path = root_path / filename
                    if should_exclude(file_path, editable.path):
                        continue
                    rel = file_path.relative_to(editable.path)
                    arcname = f"_editables/{editable.name}/{rel}"
                    zf.write(file_path, arcname)
                    total_files += 1

    buffer.seek(0)
    ui.bundling_summary(total_files, len(buffer.getvalue()), 0)

    return Bundle(
        data=buffer.getvalue(),
        editables=[e.name for e in editables],
    )


def encode_bundle(data: bytes) -> str:
    """Encode bundle as base64."""
    return base64.b64encode(data).decode()
