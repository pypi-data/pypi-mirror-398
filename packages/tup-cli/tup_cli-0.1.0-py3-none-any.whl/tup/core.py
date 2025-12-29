"""Core functionality for tup - launch_swarm and helpers."""

import sys
from pathlib import Path

from termcolor import colored

from .client import TupClient
from .config import load_config
from .packager import (
    create_job_config,
    encode_package,
    package_directory,
    serialize_job_config,
)
from .types import JobSpec, SwarmConfig


def launch_swarm(
    job_specs: list[JobSpec],
    config: SwarmConfig,
    *,
    instance_type: str = "standard-1",
    env_vars: dict[str, str] | None = None,
) -> list[str]:
    """Launch a swarm of jobs to Cloudflare Containers.

    This is the main entry point for the Python API, designed to be a
    drop-in replacement for xmux.launch_swarm.

    Args:
        job_specs: List of JobSpec objects defining the jobs to run
        config: SwarmConfig with sweep settings
        instance_type: Container instance type (lite, basic, standard-1, etc.)
        env_vars: Additional environment variables to inject

    Returns:
        List of job IDs for the created jobs

    Example:
        from tup import JobSpec, SwarmConfig, launch_swarm

        job_specs = [
            JobSpec(
                main_fn=train_model,
                log_relpath="sweep/lr0.001",
                entrypoint_config={"lr": 0.001}
            ),
            JobSpec(
                main_fn=train_model,
                log_relpath="sweep/lr0.01",
                entrypoint_config={"lr": 0.01}
            ),
        ]

        config = SwarmConfig(sweep_name="lr-sweep")
        job_ids = launch_swarm(job_specs, config)
    """
    if not job_specs:
        print(colored("No jobs to launch.", "yellow"))
        return []

    if config.dry_run:
        _print_dry_run(job_specs, config)
        return []

    # Print header
    print(colored(f"\n{'='*60}", "blue"))
    print(colored(f"  tup - Launching {len(job_specs)} jobs to cloud", "blue", attrs=["bold"]))
    print(colored(f"  Sweep: {config.sweep_name}", "blue"))
    print(colored(f"{'='*60}\n", "blue"))

    # Package current directory
    if config.verbose:
        print(colored("Packaging code...", "cyan"))

    cwd = Path.cwd()
    bundle_bytes = package_directory(cwd)
    bundle_b64 = encode_package(bundle_bytes)

    if config.verbose:
        size_kb = len(bundle_bytes) / 1024
        print(colored(f"  Bundle size: {size_kb:.1f} KB", "cyan"))

    # Prepare job configs
    jobs_payload = []
    for i, job_spec in enumerate(job_specs, 1):
        job_config = create_job_config(job_spec)
        config_bytes = serialize_job_config(job_config)
        config_b64 = encode_package(config_bytes)

        jobs_payload.append({
            "config": config_b64,
            "log_relpath": job_spec.log_relpath,
            "group": job_spec.get_group_name(f"job-{i}"),
        })

        if config.verbose:
            print(colored(f"  [{i}/{len(job_specs)}] {job_spec.log_relpath}", "cyan"))

    # Submit to API
    print(colored("Submitting jobs...", "cyan"))

    tup_config = load_config()
    with TupClient(tup_config) as client:
        responses = client.create_swarm_jobs(
            sweep_name=config.sweep_name,
            jobs=jobs_payload,
            bundle=bundle_b64,
            instance_type=instance_type,
            env_vars=env_vars,
            max_concurrent=config.max_concurrent,
        )

    # Print results
    job_ids = []
    print()
    for i, (job_spec, response) in enumerate(zip(job_specs, responses, strict=True), 1):
        job_ids.append(response.job_id)
        status_color = "green" if response.status == "pending" else "yellow"
        print(
            f"  {colored('✓', 'green')} "
            f"{job_spec.log_relpath} → "
            f"{colored(response.job_id[:8], 'cyan')} "
            f"[{colored(response.status, status_color)}]"
        )

    print()
    print(colored(f"Launched {len(job_ids)} jobs.", "green", attrs=["bold"]))
    print(colored(f"View status: tup status", "blue"))
    print(colored(f"View logs:   tup logs <job-id>", "blue"))
    print()

    return job_ids


def _print_dry_run(job_specs: list[JobSpec], config: SwarmConfig) -> None:
    """Print what would happen in a dry run."""
    print(colored("\n[DRY RUN] Would launch the following jobs:\n", "yellow", attrs=["bold"]))

    print(f"  Sweep: {config.sweep_name}")
    print(f"  Max concurrent: {config.max_concurrent}")
    print()

    for i, job_spec in enumerate(job_specs, 1):
        print(f"  [{i}] {job_spec.log_relpath}")
        print(f"      Function: {job_spec.main_fn.__module__}:{job_spec.main_fn.__name__}")
        print(f"      Config: {job_spec.entrypoint_config}")
        if job_spec.container_group:
            print(f"      Group: {job_spec.container_group}")
        print()


def run_command(
    command: str,
    *,
    name: str | None = None,
    instance_type: str = "standard-1",
    env_vars: dict[str, str] | None = None,
    timeout: str | None = None,
    detach: bool = False,
    directory: Path | str | None = None,
) -> str:
    """Run a shell command in the cloud.

    This is the programmatic interface for `tup <command>`.

    Args:
        command: Shell command to run (e.g., "python train.py")
        name: Optional job name
        instance_type: Container instance type
        env_vars: Additional environment variables
        timeout: Max runtime (e.g., "2h", "1d")
        detach: If True, return immediately without streaming logs
        directory: Directory to package (default: current directory)

    Returns:
        Job ID

    Example:
        from tup import run_command

        job_id = run_command(
            "python train.py --epochs 100",
            name="training-v1",
            detach=True
        )
    """
    directory = Path(directory) if directory else Path.cwd()

    # Package directory
    bundle_bytes = package_directory(directory)
    bundle_b64 = encode_package(bundle_bytes)

    # Submit job
    tup_config = load_config()
    with TupClient(tup_config) as client:
        response = client.create_command_job(
            command=command,
            bundle=bundle_b64,
            name=name,
            instance_type=instance_type,
            env_vars=env_vars,
            timeout=timeout,
        )

        job_id = response.job_id

        if detach:
            print(colored(f"Job started: {job_id}", "green"))
            print(colored(f"View logs: tup logs {job_id}", "blue"))
            return job_id

        # Stream logs
        print(colored(f"Job {job_id[:8]} started. Streaming logs...\n", "cyan"))

        try:
            for line in client.stream_logs(job_id):
                print(line)
        except KeyboardInterrupt:
            print(colored("\n\nDetached from logs. Job continues running.", "yellow"))
            print(colored(f"Reattach: tup logs {job_id}", "blue"))
            print(colored(f"Stop job: tup stop {job_id}", "blue"))

        # Get final status
        status = client.get_job(job_id)
        if status.status == "completed":
            print(colored(f"\nJob completed.", "green"))
        elif status.status == "failed":
            print(colored(f"\nJob failed.", "red"))
            sys.exit(1)

        return job_id
