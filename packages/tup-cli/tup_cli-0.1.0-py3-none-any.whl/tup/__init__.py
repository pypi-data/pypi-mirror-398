"""tup - Run any command in the cloud

Close your laptop, keep running. Two ways to use:

1. CLI wrapper (simple):
    $ tup python train.py --epochs 100
    $ tup uv run python sweep.py

2. Python API (xmux-compatible):
    from tup import JobSpec, SwarmConfig, launch_swarm

    job_specs = [
        JobSpec(
            main_fn=train_model,
            log_relpath="sweep/model1/lr0.001",
            entrypoint_config={"model": "bert", "lr": 0.001}
        ),
    ]

    config = SwarmConfig(sweep_name="my-lr-sweep")
    launch_swarm(job_specs, config)
"""

from .types import JobSpec, SwarmConfig, JobStatus, JobConfig
from .core import launch_swarm, run_command

__version__ = "0.1.0"
__all__ = [
    "JobSpec",
    "SwarmConfig",
    "JobStatus",
    "JobConfig",
    "launch_swarm",
    "run_command",
]
