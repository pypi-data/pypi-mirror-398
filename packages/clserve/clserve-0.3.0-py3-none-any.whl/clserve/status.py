"""Job status and URL retrieval for clserve."""

import os
import re
import subprocess
import requests
from dataclasses import dataclass
from typing import Optional
from pathlib import Path
from enum import Enum


# Prefix used to identify clserve jobs
CLSERVE_JOB_PREFIX = "clserve_"

# Base directory for clserve data
CLSERVE_DIR = Path(os.path.expanduser("~/.clserve"))
CLSERVE_LOGS_DIR = CLSERVE_DIR / "logs"


class WorkerLoadingStage(Enum):
    """Stages of worker initialization."""

    UNKNOWN = "unknown"
    INITIALIZING = "initializing"
    LOADING_WEIGHTS = "loading_weights"
    CAPTURING_CUDA_GRAPH = "capturing_cuda_graph"
    READY = "ready"
    ERROR = "error"


@dataclass
class WorkerStatus:
    """Status of a single worker process."""

    worker_id: int
    node: str
    stage: WorkerLoadingStage
    log_file: Optional[Path] = None


@dataclass
class JobInfo:
    """Information about a running or completed job."""

    job_id: str
    job_name: str
    state: str
    node_list: str
    work_dir: str
    model_path: Optional[str] = None
    endpoint_url: Optional[str] = None
    workers: Optional[int] = None
    nodes_per_worker: Optional[int] = None
    tp_size: Optional[int] = None
    use_router: Optional[bool] = None
    worker_statuses: Optional[list[WorkerStatus]] = None
    router_worker_count: Optional[int] = None
    time_limit: Optional[str] = None
    time_left: Optional[str] = None


def get_my_jobs(clserve_only: bool = True) -> list[dict]:
    """Get jobs for the current user.

    Args:
        clserve_only: If True, only return jobs with clserve_ prefix

    Returns:
        List of job info dicts from squeue
    """
    try:
        result = subprocess.run(
            [
                "squeue",
                "--me",
                "--format=%i|%j|%T|%N|%Z|%l|%L",
                "--noheader",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError:
        return []

    jobs = []
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        parts = line.split("|")
        if len(parts) >= 7:
            job_name = parts[1].strip()
            # Filter to only clserve jobs if requested
            if clserve_only and not job_name.startswith(CLSERVE_JOB_PREFIX):
                continue
            jobs.append(
                {
                    "job_id": parts[0].strip(),
                    "job_name": job_name,
                    "state": parts[2].strip(),
                    "node_list": parts[3].strip(),
                    "work_dir": parts[4].strip(),
                    "time_limit": parts[5].strip(),
                    "time_left": parts[6].strip(),
                }
            )
    return jobs


def get_job_details(job_id: str) -> Optional[dict]:
    """Get detailed information about a specific job.

    Args:
        job_id: SLURM job ID

    Returns:
        Dict with job details or None if not found
    """
    try:
        result = subprocess.run(
            ["scontrol", "show", "job", job_id],
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError:
        return None

    details = {}
    for match in re.finditer(r"(\w+)=([^\s]+)", result.stdout):
        details[match.group(1)] = match.group(2)

    return details


def get_job_time_info(job_id: str) -> tuple[Optional[str], Optional[str]]:
    """Get time limit and time left for a specific job via squeue.

    Args:
        job_id: SLURM job ID

    Returns:
        Tuple of (time_limit, time_left) or (None, None) if not found
    """
    try:
        result = subprocess.run(
            ["squeue", "-j", job_id, "--format=%l|%L", "--noheader"],
            capture_output=True,
            text=True,
            check=True,
        )
        line = result.stdout.strip()
        if line:
            parts = line.split("|")
            if len(parts) >= 2:
                return parts[0].strip(), parts[1].strip()
    except subprocess.CalledProcessError:
        pass
    return None, None


def get_log_dir(job_id: str) -> Optional[Path]:
    """Get the log directory for a job.

    Args:
        job_id: SLURM job ID

    Returns:
        Path to log directory or None if not found
    """
    log_dir = CLSERVE_LOGS_DIR / job_id
    if log_dir.exists():
        return log_dir
    return None


def parse_metadata(log_dir: Path) -> dict:
    """Parse metadata file from log directory.

    Args:
        log_dir: Path to log directory

    Returns:
        Dict with metadata values
    """
    metadata_file = log_dir / "metadata.txt"
    if not metadata_file.exists():
        return {}

    metadata = {}
    with open(metadata_file) as f:
        for line in f:
            line = line.strip()
            if "=" in line:
                key, value = line.split("=", 1)
                metadata[key] = value
    return metadata


def detect_worker_stage(log_file: Path) -> WorkerLoadingStage:
    """Detect the current loading stage of a worker from its log file.

    Args:
        log_file: Path to worker log file (.out or .err)

    Returns:
        WorkerLoadingStage indicating current stage
    """
    if not log_file.exists():
        return WorkerLoadingStage.UNKNOWN

    try:
        with open(log_file) as f:
            content = f.read()

        # Also check the corresponding .err file for errors
        err_file = log_file.with_suffix(".err")
        err_content = ""
        if err_file.exists():
            with open(err_file) as f:
                err_content = f.read()

        # Check for ready state first - if server started successfully, it's ready
        # regardless of any error-like text during startup
        if (
            "Application startup complete" in content
            or "Application startup complete" in err_content
            or "Started server process" in content
            or "Started server process" in err_content
        ):
            return WorkerLoadingStage.READY

        # Only check for errors if not ready yet
        error_patterns = [
            "Scheduler hit an exception",
            "RuntimeError:",
            "Traceback (most recent call last)",
            "CUDA error",
            "NCCL error",
            "child failed",
        ]
        for pattern in error_patterns:
            if pattern in content or pattern in err_content:
                return WorkerLoadingStage.ERROR

        # Check for CUDA graph capture
        if "Capture cuda graph" in content or "Capturing batches" in content:
            # If we see "Capture cuda graph end", it's ready
            if "Capture cuda graph end" in content:
                # But only if server startup happened after
                if "Application startup complete" in content:
                    return WorkerLoadingStage.READY
            return WorkerLoadingStage.CAPTURING_CUDA_GRAPH

        # Check for weight loading (these messages appear in stderr)
        combined = content + err_content
        if (
            "Load weight begin" in combined
            or "Loading safetensors checkpoint shards" in combined
        ):
            # If we see "Load weight end", move to next stage
            if "Load weight end" in combined:
                # Check if CUDA graph capture has started
                if "Capture cuda graph" in combined:
                    return WorkerLoadingStage.CAPTURING_CUDA_GRAPH
                # Otherwise still in loading phase (KV cache allocation, etc.)
                return WorkerLoadingStage.LOADING_WEIGHTS
            return WorkerLoadingStage.LOADING_WEIGHTS

        # Check for initialization
        if "server_args=" in content or "Init torch distributed" in content:
            return WorkerLoadingStage.INITIALIZING

        # If log exists but no markers found, assume initializing
        if len(content.strip()) > 0:
            return WorkerLoadingStage.INITIALIZING

        return WorkerLoadingStage.UNKNOWN
    except Exception:
        return WorkerLoadingStage.ERROR


def get_worker_statuses(log_dir: Path) -> list[WorkerStatus]:
    """Parse worker log files to determine loading status.

    Args:
        log_dir: Path to job log directory

    Returns:
        List of WorkerStatus objects (one per worker)
    """
    statuses = []
    seen_worker_ids = set()

    # Pattern 1: Multi-node workers (num_gpus_per_worker == 4)
    # Format: worker{worker_id}_node0_{node}.out
    for log_file in log_dir.glob("worker*_node0_*.out"):
        filename = log_file.name
        match = re.match(r"worker(\d+)_node0_(.+)\.out", filename)
        if match:
            worker_id = int(match.group(1))
            if worker_id not in seen_worker_ids:
                node = match.group(2)
                stage = detect_worker_stage(log_file)
                statuses.append(
                    WorkerStatus(
                        worker_id=worker_id, node=node, stage=stage, log_file=log_file
                    )
                )
                seen_worker_ids.add(worker_id)

    # Pattern 2: Single-GPU workers (num_gpus_per_worker < 4)
    # Format: worker{worker_id}_proc{proc_id}_{node}.out
    for log_file in log_dir.glob("worker*_proc*_*.out"):
        filename = log_file.name
        match = re.match(r"worker(\d+)_proc\d+_(.+)\.out", filename)
        if match:
            worker_id = int(match.group(1))
            if worker_id not in seen_worker_ids:
                node = match.group(2)
                stage = detect_worker_stage(log_file)
                statuses.append(
                    WorkerStatus(
                        worker_id=worker_id, node=node, stage=stage, log_file=log_file
                    )
                )
                seen_worker_ids.add(worker_id)

    # Sort by worker ID
    statuses.sort(key=lambda x: x.worker_id)
    return statuses


def extract_url_from_log(log_dir: Path) -> Optional[str]:
    """Extract endpoint URL from job logs.

    Args:
        log_dir: Path to log directory

    Returns:
        Endpoint URL or None if not found
    """
    # First try metadata file
    metadata = parse_metadata(log_dir)
    if "ENDPOINT_URL" in metadata:
        return metadata["ENDPOINT_URL"]

    # Fall back to parsing log.out
    log_file = log_dir / "log.out"
    if not log_file.exists():
        return None

    with open(log_file) as f:
        content = f.read()

    # Look for Router URL first
    router_match = re.search(r"Router URL:\s*(http://[^\s]+)", content)
    if router_match:
        return router_match.group(1)

    # Look for Endpoint URL
    endpoint_match = re.search(r"Endpoint URL:\s*(http://[^\s]+)", content)
    if endpoint_match:
        return endpoint_match.group(1)

    # Look for worker URLs
    worker_match = re.search(r"http://[\d\.]+:5000", content)
    if worker_match:
        return worker_match.group(0)

    return None


def get_router_worker_count(router_url: str) -> Optional[int]:
    """Query router to get the count of registered workers.

    Args:
        router_url: Router URL (e.g., http://host:30000)

    Returns:
        Number of workers registered with router, or None if query fails
    """
    try:
        response = requests.get(f"{router_url}/workers", timeout=2)
        response.raise_for_status()
        data = response.json()
        return data.get("stats", {}).get("regular_count", 0)
    except Exception:
        return None


def is_clserve_job(job_name: str) -> bool:
    """Check if a job name indicates a clserve job.

    Args:
        job_name: SLURM job name

    Returns:
        True if this is a clserve job
    """
    return job_name.startswith(CLSERVE_JOB_PREFIX)


def get_job_info(
    job_id: str,
    clserve_only: bool = True,
    time_limit: Optional[str] = None,
    time_left: Optional[str] = None,
) -> Optional[JobInfo]:
    """Get comprehensive information about a job.

    Args:
        job_id: SLURM job ID
        clserve_only: If True, only return info for clserve jobs
        time_limit: Optional pre-fetched time limit (avoids extra squeue call)
        time_left: Optional pre-fetched time left (avoids extra squeue call)

    Returns:
        JobInfo object or None if job not found or not a clserve job
    """
    details = get_job_details(job_id)
    if not details:
        return None

    job_name = details.get("JobName", "")

    # Filter non-clserve jobs if requested
    if clserve_only and not is_clserve_job(job_name):
        return None

    work_dir = details.get("WorkDir", "")
    log_dir = get_log_dir(job_id)

    # Parse metadata if available
    metadata = {}
    endpoint_url = None
    worker_statuses = None
    router_worker_count = None

    if log_dir:
        metadata = parse_metadata(log_dir)
        endpoint_url = extract_url_from_log(log_dir)

        # Get worker statuses if job is running
        if details.get("JobState", "") == "RUNNING":
            worker_statuses = get_worker_statuses(log_dir)

            # Query router if it's enabled and we have an endpoint
            if endpoint_url and metadata.get("USE_ROUTER", "").lower() == "true":
                router_worker_count = get_router_worker_count(endpoint_url)

    # Get time info if not provided
    if time_limit is None or time_left is None:
        time_limit, time_left = get_job_time_info(job_id)

    return JobInfo(
        job_id=job_id,
        job_name=job_name,
        state=details.get("JobState", ""),
        node_list=details.get("NodeList", ""),
        work_dir=work_dir,
        model_path=metadata.get("MODEL_PATH"),
        endpoint_url=endpoint_url,
        workers=int(metadata["WORKERS"]) if "WORKERS" in metadata else None,
        nodes_per_worker=int(metadata["NODES_PER_WORKER"])
        if "NODES_PER_WORKER" in metadata
        else None,
        tp_size=int(metadata["TP_SIZE"]) if "TP_SIZE" in metadata else None,
        use_router=metadata.get("USE_ROUTER", "").lower() == "true"
        if "USE_ROUTER" in metadata
        else None,
        worker_statuses=worker_statuses,
        router_worker_count=router_worker_count,
        time_limit=time_limit,
        time_left=time_left,
    )


def list_serving_jobs() -> list[JobInfo]:
    """List all running serving jobs for the current user.

    Returns:
        List of JobInfo objects
    """
    jobs = get_my_jobs()
    serving_jobs = []

    for job in jobs:
        job_info = get_job_info(
            job["job_id"],
            time_limit=job.get("time_limit"),
            time_left=job.get("time_left"),
        )
        if job_info:
            serving_jobs.append(job_info)

    return serving_jobs


def find_jobs_by_model(model_name: str) -> list[JobInfo]:
    """Find jobs serving a specific model.

    Args:
        model_name: Model name or path (partial match supported)

    Returns:
        List of matching JobInfo objects
    """
    jobs = list_serving_jobs()
    matches = []

    model_name_lower = model_name.lower()
    for job in jobs:
        # Check model path
        if job.model_path and model_name_lower in job.model_path.lower():
            matches.append(job)
            continue

        # Check job name
        if model_name_lower in job.job_name.lower():
            matches.append(job)
            continue

    return matches


def get_url(identifier: str) -> Optional[str]:
    """Get endpoint URL for a job by job ID or model name.

    Args:
        identifier: Job ID or model name

    Returns:
        Endpoint URL or None if not found
    """
    # Try as job ID first
    if identifier.isdigit():
        job_info = get_job_info(identifier)
        if job_info and job_info.endpoint_url:
            return job_info.endpoint_url

    # Try as model name
    matches = find_jobs_by_model(identifier)
    if matches:
        # Return URL of first running job
        for job in matches:
            if job.state == "RUNNING" and job.endpoint_url:
                return job.endpoint_url
        # Fall back to any job with URL
        for job in matches:
            if job.endpoint_url:
                return job.endpoint_url

    return None
