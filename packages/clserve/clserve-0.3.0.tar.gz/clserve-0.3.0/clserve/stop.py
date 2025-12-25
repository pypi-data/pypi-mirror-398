"""Stop running serving jobs."""

import subprocess
import logging

from clserve.status import get_job_info, find_jobs_by_model, list_serving_jobs

logger = logging.getLogger(__name__)


def cancel_job(job_id: str) -> bool:
    """Cancel a SLURM job.

    Args:
        job_id: SLURM job ID

    Returns:
        True if job was cancelled successfully
    """
    try:
        subprocess.run(
            ["scancel", job_id],
            capture_output=True,
            text=True,
            check=True,
        )
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to cancel job {job_id}: {e.stderr}")
        return False


def stop_by_job_id(job_id: str) -> bool:
    """Stop a job by its job ID.

    Args:
        job_id: SLURM job ID

    Returns:
        True if job was stopped successfully
    """
    job_info = get_job_info(job_id)
    if not job_info:
        logger.error(f"Job {job_id} not found")
        return False

    if job_info.state not in ["RUNNING", "PENDING"]:
        logger.warning(f"Job {job_id} is not running (state: {job_info.state})")
        return False

    return cancel_job(job_id)


def stop_by_model(model_name: str, all_matches: bool = False) -> list[str]:
    """Stop jobs serving a specific model.

    Args:
        model_name: Model name or path (partial match)
        all_matches: If True, stop all matching jobs; if False, only stop first match

    Returns:
        List of job IDs that were stopped
    """
    matches = find_jobs_by_model(model_name)
    running = [job for job in matches if job.state in ["RUNNING", "PENDING"]]

    if not running:
        logger.warning(f"No running jobs found for model '{model_name}'")
        return []

    stopped = []
    jobs_to_stop = running if all_matches else running[:1]

    for job in jobs_to_stop:
        if cancel_job(job.job_id):
            stopped.append(job.job_id)
            logger.info(f"Stopped job {job.job_id} ({job.model_path or job.job_name})")

    return stopped


def stop_all() -> list[str]:
    """Stop all running serving jobs.

    Returns:
        List of job IDs that were stopped
    """
    jobs = list_serving_jobs()
    running = [job for job in jobs if job.state in ["RUNNING", "PENDING"]]

    stopped = []
    for job in running:
        if cancel_job(job.job_id):
            stopped.append(job.job_id)
            logger.info(f"Stopped job {job.job_id} ({job.model_path or job.job_name})")

    return stopped


def stop(identifier: str, all_matches: bool = False) -> list[str]:
    """Stop jobs by job ID or model name.

    Args:
        identifier: Job ID or model name
        all_matches: If True, stop all matching jobs (only applies to model name)

    Returns:
        List of job IDs that were stopped
    """
    # Try as job ID first
    if identifier.isdigit():
        success = stop_by_job_id(identifier)
        return [identifier] if success else []

    # Try as model name
    return stop_by_model(identifier, all_matches=all_matches)
