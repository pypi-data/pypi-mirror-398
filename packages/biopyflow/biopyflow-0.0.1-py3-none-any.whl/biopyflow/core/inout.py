from datetime import datetime
from pathlib import Path
from typing import Tuple

def safe_job_name(name: str) -> str:
    return "".join(c if c.isalnum() or c in ("-", "_", ".") else "_" for c in name)

def log_directory(name: str) -> Path:
    return Path(f"{name}_log")

def slurm_log_paths(name: str) -> Tuple[Path, Path]:
    return log_directory(name) / f"{name}-%j.out", log_directory(name) / f"{name}-%j.err"

def local_log_paths(name: str) -> Tuple[Path, Path]:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    return log_directory(name) / f"{name}-{timestamp}.out", log_directory(name) / f"{name}-{timestamp}.err"

# function to make a log file for Flow
def make_flow_log(name: str) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    return Path(f"{name}-{timestamp}-flow.log")

# function to write cmd of each steps to a log file with timestamp
def write_cmd_log(cmd: str, log_file: Path):
    with open(log_file, "a") as f:
        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {cmd}\n")