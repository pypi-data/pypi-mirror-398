"""Runner for vmux jobs inside the container.

This module is the entrypoint for jobs created via launch_swarm().
It loads a pickled JobConfig and executes the specified function.

Usage:
    python -m vmux.runner /app/job_config.pickle
"""

import asyncio
import importlib
import os
import pickle
import sys
from pathlib import Path

from .types import JobConfig


def get_module_member(path_with_colon: str) -> object:
    """Import a module and get a member from it.

    Args:
        path_with_colon: String like "module.submodule:FunctionName"

    Returns:
        The imported member (usually a function)
    """
    if ":" not in path_with_colon:
        raise ValueError(f"Invalid symbol path: {path_with_colon}. Expected 'module:name'")

    module_path, member_name = path_with_colon.rsplit(":", 1)

    # Handle nested attributes (e.g., "module:Class.method")
    parts = member_name.split(".")

    module = importlib.import_module(module_path)
    result = module

    for part in parts:
        result = getattr(result, part)

    return result


def load_config(config_path: str | Path) -> JobConfig:
    """Load a JobConfig from a pickle file.

    Args:
        config_path: Path to the pickle file

    Returns:
        Loaded JobConfig
    """
    config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "rb") as f:
        config = pickle.load(f)

    if not isinstance(config, JobConfig):
        raise TypeError(f"Expected JobConfig, got {type(config)}")

    return config


def setup_logging(log_relpath: str) -> Path:
    """Set up logging directory and return the log path.

    Creates ~/experiments/{log_relpath}/ directory structure.
    """
    # In container, we use /app/logs instead of ~/experiments
    log_dir = Path("/app/logs") / log_relpath
    log_dir.mkdir(parents=True, exist_ok=True)

    # Also set up a symlink at ~/experiments for compatibility
    experiments_dir = Path.home() / "experiments" / log_relpath
    experiments_dir.parent.mkdir(parents=True, exist_ok=True)

    if not experiments_dir.exists():
        try:
            experiments_dir.symlink_to(log_dir)
        except OSError:
            pass  # Symlink already exists or permission denied

    return log_dir


def run_job(config: JobConfig) -> int:
    """Run a job from its config.

    Args:
        config: JobConfig with entrypoint and arguments

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    print(f"[vmux] Starting job: {config.log_relpath}")
    print(f"[vmux] Entrypoint: {config.entrypoint}")

    # Set up logging
    log_dir = setup_logging(config.log_relpath)
    print(f"[vmux] Log directory: {log_dir}")

    # Import the entrypoint function
    try:
        main_fn = get_module_member(config.entrypoint)
    except Exception as e:
        print(f"[vmux] Failed to import entrypoint: {e}")
        return 1

    print(f"[vmux] Running {main_fn.__name__}...")
    print("-" * 60)

    # Run the function
    try:
        result = main_fn(config.entrypoint_config)

        # Handle async functions
        if asyncio.iscoroutine(result):
            asyncio.run(result)

        print("-" * 60)
        print(f"[vmux] Job completed successfully")

        # Create completion marker
        (log_dir / ".completed").touch()

        return 0

    except Exception as e:
        print("-" * 60)
        print(f"[vmux] Job failed with error: {e}")
        import traceback
        traceback.print_exc()

        # Create failure marker
        (log_dir / ".failed").touch()

        return 1


def main() -> None:
    """Main entrypoint for the runner."""
    if len(sys.argv) < 2:
        print("Usage: python -m vmux.runner <config_path>")
        sys.exit(1)

    config_path = sys.argv[1]

    # Add /app to Python path so imports work
    app_dir = Path("/app")
    if app_dir.exists() and str(app_dir) not in sys.path:
        sys.path.insert(0, str(app_dir))

    # Also add current directory
    cwd = os.getcwd()
    if cwd not in sys.path:
        sys.path.insert(0, cwd)

    try:
        config = load_config(config_path)
        exit_code = run_job(config)
        sys.exit(exit_code)
    except Exception as e:
        print(f"[vmux] Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
