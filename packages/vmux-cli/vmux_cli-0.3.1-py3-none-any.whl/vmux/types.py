"""Core data structures for vmux - mirrors xmux API"""

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel


class JobSpec(BaseModel):
    """Specification for a single job in the swarm.

    Mirrors xmux.JobSpec for drop-in compatibility.
    """

    model_config = {"arbitrary_types_allowed": True}

    main_fn: Callable[..., object]  # Function to run
    log_relpath: str  # Path to log directory (e.g., "sweep/model1/lr0.001")
    entrypoint_config: Any  # Argument to pass to main_fn
    container_group: str | None = None  # Group jobs together (like tmux_window_name)

    def get_group_name(self, default_name: str) -> str:
        """Get the container group name for this job."""
        return self.container_group or default_name


class SwarmConfig(BaseModel):
    """Configuration for launching a swarm of jobs.

    Mirrors xmux.SwarmConfig for drop-in compatibility.
    """

    sweep_name: str  # Name for this sweep (becomes job prefix)
    max_concurrent: int = 10  # Max concurrent containers
    dry_run: bool = False  # If True, print what would happen without running
    verbose: bool = False  # Enable verbose logging

    def get_sweep_id(self) -> str:
        """Get sanitized sweep ID."""
        return "".join(
            c if c.isalnum() or c in ["_", "-"] else "_"
            for c in self.sweep_name
        )[:50]


class JobStatus(BaseModel):
    """Status of a running job."""

    job_id: str
    status: str  # "pending", "running", "completed", "failed"
    created_at: str
    name: str | None = None  # For command jobs
    sweep_name: str | None = None  # For swarm jobs
    log_relpath: str | None = None  # For swarm jobs
    started_at: str | None = None
    ended_at: str | None = None


class JobConfig(BaseModel):
    """Internal job configuration (serialized to container)."""

    log_relpath: str
    entrypoint: str  # Module path to main_fn
    entrypoint_config: Any
