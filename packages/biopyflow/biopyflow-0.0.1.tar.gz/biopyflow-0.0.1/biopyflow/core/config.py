from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import shlex
from typing import List, Optional, Type

import os, shutil, shlex

from .inout import safe_job_name, slurm_log_paths, make_flow_log

@dataclass
class Resource:
    """Resource requirements for a step (time in hours, mem in GB)."""

    cpu: int = 1
    mem: int = 1
    time: int = 1


@dataclass
class Config:
    """Execution configuration shared by steps."""

    runtime: str = "singularity"
    executor: str = "local"
    image: Optional[str] = None
    binds: List[str] = field(default_factory=list)
    flow_log: Optional[Path] = None


def wrap_container(cmd: str, cfg: Optional[Config]) -> str:
    """
    Wrap a shell command with the appropriate container runtime invocation.
    """
    if not cfg or not cfg.image:
        return cmd
    bind_flags = ""
    if cfg.binds:
        if cfg.runtime == "singularity":
            bind_flags = " ".join(f"--bind {mount}" for mount in cfg.binds)
        elif cfg.runtime == "docker":
            bind_flags = " ".join(f"-v {mount}" for mount in cfg.binds)

    if cfg.runtime == "singularity":
        bind_flags = f"{bind_flags} " if bind_flags else ""
        return f"singularity exec {bind_flags}{cfg.image} {cmd}"
    if cfg.runtime == "docker":
        bind_flags = f"{bind_flags} " if bind_flags else ""
        return f'docker run --rm {bind_flags}{cfg.image} sh -c "{cmd}"'
    return cmd


def wrap_slurm(
    cmd: str,
    step,
) -> str:
    """
    Wrap a command with an srun invocation using the given resources.

    Parameters
    ----------
    cmd:
        Command to wrap.
    step:
        Step class to get the resource and log directory from.
    """
    res = step.RESOURCE
    if not res:
        raise ValueError("Resource is not set for the step")
    job_name = (step.__class__.__name__ or "biopyflow").strip() or "biopyflow"
    job_name = safe_job_name(job_name)
    stdout_path, stderr_path = slurm_log_paths(job_name)
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    stderr_path.parent.mkdir(parents=True, exist_ok=True)
    return f"srun -c {res.cpu} --mem={res.mem}G --time={res.time}:00:00\
            --job-name={job_name} \
            --output={shlex.quote(str(stdout_path))} \
            --error={shlex.quote(str(stderr_path))} \
            {cmd}"
