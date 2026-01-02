"""Tests for code packaging."""

import tempfile
import zipfile
from pathlib import Path

import pytest

from vmux.packager import (
    encode_package,
    decode_package,
    get_symbol_path,
    package_directory,
    package_single_file,
    should_exclude,
)


def test_should_exclude_git():
    """Test that .git directories are excluded."""
    base = Path("/project")
    assert should_exclude(base / ".git", base)
    assert should_exclude(base / ".git" / "config", base)


def test_should_exclude_pycache():
    """Test that __pycache__ directories are excluded."""
    base = Path("/project")
    assert should_exclude(base / "__pycache__", base)
    assert should_exclude(base / "src" / "__pycache__", base)


def test_should_exclude_env():
    """Test that .env files are excluded."""
    base = Path("/project")
    assert should_exclude(base / ".env", base)
    assert should_exclude(base / ".env.local", base)


def test_should_not_exclude_regular_files():
    """Test that regular files are not excluded."""
    base = Path("/project")
    assert not should_exclude(base / "train.py", base)
    assert not should_exclude(base / "src" / "model.py", base)
    assert not should_exclude(base / "requirements.txt", base)


def test_get_symbol_path():
    """Test symbol path extraction."""

    def my_function():
        pass

    path = get_symbol_path(my_function)
    assert ":" in path
    assert path.endswith("my_function")


def test_package_directory():
    """Test directory packaging."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test files
        tmppath = Path(tmpdir)
        (tmppath / "train.py").write_text("print('hello')")
        (tmppath / "config.yaml").write_text("lr: 0.001")
        (tmppath / "__pycache__").mkdir()
        (tmppath / "__pycache__" / "train.cpython-311.pyc").write_bytes(b"")

        # Package
        bundle = package_directory(tmppath)

        # Verify it's a valid zip
        import io

        with zipfile.ZipFile(io.BytesIO(bundle)) as zf:
            names = zf.namelist()
            assert "train.py" in names
            assert "config.yaml" in names
            # __pycache__ should be excluded
            assert not any("__pycache__" in n for n in names)


def test_package_single_file():
    """Test single file packaging."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        (tmppath / "train.py").write_text("print('hello')")
        (tmppath / "requirements.txt").write_text("numpy")

        bundle = package_single_file(tmppath / "train.py")

        import io

        with zipfile.ZipFile(io.BytesIO(bundle)) as zf:
            names = zf.namelist()
            assert "train.py" in names
            assert "requirements.txt" in names


def test_encode_decode_package():
    """Test base64 encoding/decoding."""
    original = b"test data"
    encoded = encode_package(original)
    decoded = decode_package(encoded)
    assert decoded == original
