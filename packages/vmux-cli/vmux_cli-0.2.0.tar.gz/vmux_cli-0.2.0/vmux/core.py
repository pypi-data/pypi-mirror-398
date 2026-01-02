"""Core functionality for vmux."""

import signal
import sys
from pathlib import Path

import keyring

from .client import TupClient
from .config import load_config
from .packager import package, encode_bundle
from .ui import console, success, error


def get_secrets() -> dict[str, str]:
    """Load secrets from system keychain."""
    config = load_config()
    secrets = {}
    for key in config.env.keys():
        value = keyring.get_password("vmux", key)
        if value:
            secrets[key] = value
    return secrets


def run_command(
    command: str,
    *,
    env_vars: dict[str, str] | None = None,
    detach: bool = False,
    directory: Path | str | None = None,
) -> str:
    """Run a command in the cloud.

    Returns job_id.
    """
    directory = Path(directory) if directory else Path.cwd()

    # Package project (detects editables automatically)
    bundle = package(directory, command)
    bundle_b64 = encode_bundle(bundle.data)

    config = load_config()

    # Merge secrets from keychain with passed env vars (passed takes precedence)
    merged_env = get_secrets()
    if env_vars:
        merged_env.update(env_vars)
    env_vars = merged_env or None

    with TupClient(config) as client:
        job_id = None

        def handle_interrupt(sig: int, frame: object) -> None:
            """Handle Ctrl+C gracefully."""
            console.print()
            if job_id:
                console.print(f"\n[yellow]Detached from job {job_id[:8]}[/yellow]")
                console.print(f"[dim]Job is still running in the cloud.[/dim]\n")
                console.print(f"  [blue]vmux logs -f {job_id}[/blue]  - follow logs")
                console.print(f"  [blue]vmux ps[/blue]               - list jobs")
                console.print(f"  [blue]vmux stop {job_id}[/blue]     - stop job")
                console.print()
            sys.exit(0)

        signal.signal(signal.SIGINT, handle_interrupt)

        try:
            for event in client.run(
                command=command,
                bundle=bundle_b64,
                env_vars=env_vars,
                editables=bundle.editables,
            ):
                if "job_id" in event:
                    job_id = event["job_id"]
                    if detach:
                        success(f"Job started: {job_id}")
                        console.print(f"[blue]Follow: vmux logs -f {job_id}[/blue]")
                        return job_id
                    console.print(f"\n[cyan]Job {job_id[:8]} running...[/cyan]\n")

                elif "log" in event:
                    console.print(event["log"], end="")

                elif "status" in event:
                    status = event["status"]
                    if status in ("provisioning", "initializing", "extracting", "installing", "starting"):
                        console.print(f"[dim]→ {status}...[/dim]")
                    elif status == "completed":
                        console.print()
                        success("Done.")
                    elif status == "failed":
                        console.print()
                        error(f"Failed (exit {event.get('exit_code', '?')})")
                        sys.exit(1)

                elif "error" in event:
                    error(event["error"])
                    sys.exit(1)
        finally:
            signal.signal(signal.SIGINT, signal.SIG_DFL)

        return job_id or ""
