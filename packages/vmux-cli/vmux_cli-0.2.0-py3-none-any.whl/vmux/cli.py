"""CLI for vmux - run any command in the cloud."""

import sys
import click

from .client import TupClient
from .ui import console, success, error, warning
from .config import load_config, save_config
from .core import run_command


@click.group()
def cli() -> None:
    """Run any command in the cloud."""
    pass


@cli.command()
@click.option("--detach", "-d", is_flag=True, help="Return job ID without streaming logs")
@click.option("--env", "-e", multiple=True, help="Environment variable (KEY=VALUE)")
@click.argument("command", nargs=-1, required=True)
def run(detach: bool, env: tuple[str, ...], command: tuple[str, ...]) -> None:
    """Run a command in the cloud.

    \b
    Examples:
        vmux run python train.py
        vmux run --detach python long_job.py
        vmux run -e WANDB_KEY=xxx python train.py
    """
    env_vars = {}
    for e in env:
        if "=" not in e:
            raise click.BadParameter(f"Invalid format: {e}. Use KEY=VALUE")
        key, value = e.split("=", 1)
        env_vars[key] = value

    # Auto-detect leading KEY=VALUE args
    command = list(command)
    while command and "=" in command[0] and not command[0].startswith("-"):
        key, value = command.pop(0).split("=", 1)
        if key.isupper() or "_" in key:
            env_vars[key] = value
        else:
            command.insert(0, f"{key}={value}")
            break

    try:
        run_command(" ".join(command), env_vars=env_vars or None, detach=detach)
    except Exception as e:
        error(str(e))
        sys.exit(1)


def _list_jobs(limit: int) -> None:
    """Shared implementation for ps/ls."""
    from datetime import datetime

    config = load_config()
    with TupClient(config) as client:
        jobs = client.list_jobs(limit=limit)

        if not jobs:
            warning("No jobs found.")
            return

        # Sort by created_at ascending (oldest first, newest at bottom)
        jobs.sort(key=lambda j: j.get("created_at", ""))

        console.print()
        console.print(f"  {'ID':<12} {'STARTED':<12} {'COMMAND':<26} {'STATUS':<10}")
        console.print(f"  {'-'*12} {'-'*12} {'-'*26} {'-'*10}")

        for job in jobs:
            styles = {"running": "cyan", "completed": "green", "failed": "red", "pending": "yellow"}
            style = styles.get(job.get("status", ""), "white")
            cmd = (job.get("command", "")[:24] + "..") if len(job.get("command", "")) > 26 else job.get("command", "")

            # Format timestamp
            created = job.get("created_at", "")
            if created:
                try:
                    dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                    age = datetime.now(dt.tzinfo) - dt
                    if age.days > 0:
                        time_str = f"{age.days}d ago"
                    elif age.seconds >= 3600:
                        time_str = f"{age.seconds // 3600}h ago"
                    elif age.seconds >= 60:
                        time_str = f"{age.seconds // 60}m ago"
                    else:
                        time_str = "just now"
                except Exception:
                    time_str = created[:10]
            else:
                time_str = "-"

            console.print(f"  {job['job_id']:<12} {time_str:<12} {cmd:<26} [{style}]{job.get('status', ''):<10}[/{style}]")

        console.print()
        console.print(f"[dim]  Use 'vmux logs -f <id>' to follow, 'vmux stop <id>' to kill[/dim]")
        console.print()


@cli.command(name="ps")
@click.option("--limit", "-l", default=20, help="Number of jobs to show")
def ps_cmd(limit: int) -> None:
    """List running jobs."""
    _list_jobs(limit)


@cli.command(name="ls")
@click.option("--limit", "-l", default=20, help="Number of jobs to show")
def ls_cmd(limit: int) -> None:
    """List running jobs (alias for ps)."""
    _list_jobs(limit)


@cli.command()
@click.argument("job_id")
def stop(job_id: str) -> None:
    """Stop a running job."""
    config = load_config()
    with TupClient(config) as client:
        if client.stop_job(job_id):
            success(f"Stopped {job_id[:8]}")
        else:
            error("Failed to stop job")
            sys.exit(1)


@cli.command()
@click.argument("job_id")
@click.option("--follow", "-f", is_flag=True, help="Follow log output in real-time")
def logs(job_id: str, follow: bool) -> None:
    """View logs for a job.

    \b
    Examples:
        vmux logs abc123        # Get current logs
        vmux logs -f abc123     # Follow logs (Ctrl+C to stop)
    """
    import time

    config = load_config()
    with TupClient(config) as client:
        try:
            if follow:
                console.print(f"[cyan]Following logs for {job_id[:8]}...[/cyan]")
                console.print("[dim]Ctrl+C to stop (job keeps running)[/dim]\n")
                last_len = 0
                while True:
                    try:
                        output = client.get_logs(job_id)
                        if len(output) > last_len:
                            console.print(output[last_len:], end="")
                            last_len = len(output)
                        time.sleep(0.5)
                    except KeyboardInterrupt:
                        console.print("\n[dim]Stopped following. Job continues running.[/dim]")
                        break
            else:
                output = client.get_logs(job_id)
                console.print(output)
        except Exception as e:
            error(f"Failed to get logs: {e}")
            sys.exit(1)


@cli.command()
def login() -> None:
    """Login with GitHub."""
    from .auth import device_flow_login

    try:
        result = device_flow_login()
        cfg = load_config()
        cfg.auth_token = result["access_token"]
        save_config(cfg)
        success("Logged in!")
    except Exception as e:
        error(str(e))
        sys.exit(1)


@cli.command()
def logout() -> None:
    """Logout."""
    cfg = load_config()
    cfg.auth_token = None
    save_config(cfg)
    success("Logged out.")


@cli.command()
def whoami() -> None:
    """Show current user."""
    import httpx

    cfg = load_config()
    if not cfg.auth_token:
        warning("Not logged in.")
        return

    try:
        resp = httpx.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {cfg.auth_token}"},
        )
        if resp.status_code == 401:
            warning("Session expired. Run: vmux login")
            return
        console.print(f"Logged in as [green]{resp.json()['login']}[/green]")
    except Exception as e:
        error(str(e))


@cli.group()
def secret() -> None:
    """Manage secrets for jobs."""
    pass


@secret.command(name="set")
@click.argument("key")
def secret_set(key: str) -> None:
    """Set a secret (prompts for value)."""
    import keyring

    value = click.prompt(f"Enter value for {key}", hide_input=True)
    keyring.set_password("vmux", key, value)

    # Track key name in config (values stay in keychain)
    cfg = load_config()
    cfg.env[key] = "(keychain)"
    save_config(cfg)
    success(f"Saved {key} to system keychain")


@secret.command(name="ls")
def secret_ls() -> None:
    """List stored secrets."""
    cfg = load_config()
    keys = list(cfg.env.keys())

    if not keys:
        warning("No secrets stored. Use: vmux secret set <KEY>")
        return

    console.print()
    for key in keys:
        console.print(f"  {key}")
    console.print()


@secret.command(name="rm")
@click.argument("key")
def secret_rm(key: str) -> None:
    """Remove a secret."""
    import keyring

    try:
        keyring.delete_password("vmux", key)
    except keyring.errors.PasswordDeleteError:
        pass  # May not exist in keyring if legacy

    # Remove from config tracking
    cfg = load_config()
    if key in cfg.env:
        del cfg.env[key]
        save_config(cfg)
        success(f"Removed {key}")
    else:
        error(f"Secret '{key}' not found")


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
