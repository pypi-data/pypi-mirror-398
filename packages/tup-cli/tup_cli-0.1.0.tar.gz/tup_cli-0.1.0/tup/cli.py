"""CLI for tup - run any command in the cloud."""

import sys
from pathlib import Path

import click
from termcolor import colored

from .client import TupClient
from .config import TupConfig, ensure_config_dir, load_config, save_config
from .core import run_command
from .packager import encode_package, package_directory


@click.group(invoke_without_command=True)
@click.option("--detach", "-d", is_flag=True, help="Run in background, return job ID")
@click.option("--name", "-n", help="Job name for easy reference")
@click.option(
    "--instance",
    "-i",
    default="standard-1",
    help="Instance type: lite, basic, standard-1, standard-2, standard-3, standard-4",
)
@click.option("--env", "-e", multiple=True, help="Environment variable (KEY=VALUE)")
@click.option("--timeout", "-t", help="Max runtime (e.g., '2h', '30m', '1d')")
@click.argument("command", nargs=-1)
@click.pass_context
def cli(
    ctx: click.Context,
    detach: bool,
    name: str | None,
    instance: str,
    env: tuple[str, ...],
    timeout: str | None,
    command: tuple[str, ...],
) -> None:
    """Run any command in the cloud.

    \b
    Examples:
        tup python train.py --epochs 100
        tup uv run python train.py
        tup --detach python long_training.py
        tup --name "exp-v1" python train.py
    """
    # If no command and no subcommand, show help
    if not command and ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        return

    # If we have a command, run it
    if command:
        # Parse env vars
        env_vars = {}
        for e in env:
            if "=" not in e:
                raise click.BadParameter(f"Invalid env var format: {e}. Use KEY=VALUE")
            key, value = e.split("=", 1)
            env_vars[key] = value

        cmd_str = " ".join(command)

        try:
            run_command(
                cmd_str,
                name=name,
                instance_type=instance,
                env_vars=env_vars if env_vars else None,
                timeout=timeout,
                detach=detach,
            )
        except ValueError as e:
            click.echo(colored(f"Error: {e}", "red"), err=True)
            sys.exit(1)
        except Exception as e:
            click.echo(colored(f"Error: {e}", "red"), err=True)
            sys.exit(1)


@cli.command()
@click.argument("job_id", required=False)
def logs(job_id: str | None) -> None:
    """Stream logs from a job.

    If no JOB_ID is provided, streams logs from the most recent job.
    """
    try:
        config = load_config()
        with TupClient(config) as client:
            # Get job ID if not provided
            if not job_id:
                job_id = client.get_latest_job_id()
                if not job_id:
                    click.echo(colored("No jobs found.", "yellow"))
                    return
                click.echo(colored(f"Streaming logs for latest job: {job_id[:8]}...\n", "cyan"))

            # Stream logs
            try:
                for line in client.stream_logs(job_id):
                    click.echo(line)
            except KeyboardInterrupt:
                click.echo(colored("\n\nDetached from logs.", "yellow"))

    except ValueError as e:
        click.echo(colored(f"Error: {e}", "red"), err=True)
        sys.exit(1)


@cli.command()
@click.option("--limit", "-l", default=20, help="Number of jobs to show")
def status(limit: int) -> None:
    """Show status of all jobs."""
    try:
        config = load_config()
        with TupClient(config) as client:
            jobs = client.list_jobs(limit=limit)

            if not jobs:
                click.echo(colored("No jobs found.", "yellow"))
                return

            # Print header
            click.echo()
            click.echo(
                f"  {'ID':<10} {'NAME':<20} {'STATUS':<12} {'CREATED':<20}"
            )
            click.echo(f"  {'-'*10} {'-'*20} {'-'*12} {'-'*20}")

            # Print jobs
            for job in jobs:
                status_colors = {
                    "pending": "yellow",
                    "running": "cyan",
                    "completed": "green",
                    "failed": "red",
                }
                status_color = status_colors.get(job.status, "white")

                job_name = job.log_relpath[:20] if job.log_relpath else "-"
                click.echo(
                    f"  {job.job_id[:10]:<10} "
                    f"{job_name:<20} "
                    f"{colored(job.status, status_color):<12} "
                    f"{job.created_at[:20]:<20}"
                )

            click.echo()

    except ValueError as e:
        click.echo(colored(f"Error: {e}", "red"), err=True)
        sys.exit(1)


@cli.command()
@click.argument("job_id")
def stop(job_id: str) -> None:
    """Stop a running job."""
    try:
        config = load_config()
        with TupClient(config) as client:
            success = client.stop_job(job_id)
            if success:
                click.echo(colored(f"Job {job_id[:8]} stopped.", "green"))
            else:
                click.echo(colored(f"Failed to stop job {job_id[:8]}.", "red"))
                sys.exit(1)

    except ValueError as e:
        click.echo(colored(f"Error: {e}", "red"), err=True)
        sys.exit(1)


@cli.command()
@click.argument("job_id")
def attach(job_id: str) -> None:
    """Reattach to a running job's logs."""
    # Same as logs command
    logs.callback(job_id)  # type: ignore


@cli.group()
def config() -> None:
    """Manage tup configuration."""
    pass


@config.command("set")
@click.argument("key")
@click.argument("value")
def config_set(key: str, value: str) -> None:
    """Set a configuration value.

    \b
    Keys:
        api_url     - URL of your tup worker
        auth_token  - Authentication token (optional)

    \b
    Examples:
        tup config set api_url https://tup-api.example.workers.dev
        tup config set auth_token your-token
    """
    cfg = load_config()

    if key == "api_url":
        cfg.api_url = value
    elif key == "auth_token":
        cfg.auth_token = value
    else:
        click.echo(colored(f"Unknown config key: {key}", "red"), err=True)
        click.echo("Valid keys: api_url, auth_token")
        sys.exit(1)

    save_config(cfg)
    click.echo(colored(f"Set {key} = {value}", "green"))


@config.command("get")
@click.argument("key", required=False)
def config_get(key: str | None) -> None:
    """Get configuration value(s).

    If no KEY is provided, shows all configuration.
    """
    cfg = load_config()

    if key:
        if key == "api_url":
            click.echo(cfg.api_url or "(not set)")
        elif key == "auth_token":
            click.echo(cfg.auth_token or "(not set)")
        else:
            click.echo(colored(f"Unknown config key: {key}", "red"), err=True)
            sys.exit(1)
    else:
        click.echo(f"api_url: {cfg.api_url or '(not set)'}")
        click.echo(f"auth_token: {'***' if cfg.auth_token else '(not set)'}")
        if cfg.env:
            click.echo("\nEnvironment variables:")
            for k, v in cfg.env.items():
                # Mask sensitive values
                display_v = "***" if "KEY" in k or "SECRET" in k or "TOKEN" in k else v
                click.echo(f"  {k}: {display_v}")


@config.command("path")
def config_path() -> None:
    """Show the path to the config file."""
    from .config import get_config_path

    path = get_config_path()
    click.echo(path)
    if not path.exists():
        click.echo(colored("(file does not exist yet)", "yellow"))


@cli.command()
@click.argument("key")
@click.argument("value")
def env(key: str, value: str) -> None:
    """Set an environment variable for all jobs.

    These are stored in ~/.tup/config.toml under [env].

    \b
    Examples:
        tup env WANDB_API_KEY your-key
        tup env TINKER_API_KEY sk-...
    """
    cfg = load_config()
    cfg.env[key] = value
    save_config(cfg)
    click.echo(colored(f"Set env {key}", "green"))


def main() -> None:
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
