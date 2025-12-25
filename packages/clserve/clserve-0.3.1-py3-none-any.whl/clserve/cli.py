"""Command-line interface for clserve."""

import logging
from typing import Optional
import click
from prettytable import PrettyTable


from clserve import __version__
from clserve.submit import SubmitArgs, serve
from clserve.status import (
    list_serving_jobs,
    get_job_info,
    find_jobs_by_model,
    JobInfo,
    WorkerLoadingStage,
    CLSERVE_LOGS_DIR,
)
from clserve.stop import stop_by_job_id, stop_all
from clserve.configs import list_available_configs, load_model_config
from clserve.config import (
    UserConfig,
    load_config,
    save_config,
    get_default_account,
    CONFIG_FILE,
)


def setup_logging(verbose: bool = False):
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
    )


def select_job(jobs: list[JobInfo], action: str = "select") -> Optional[JobInfo]:
    """Prompt user to select a job from a list.

    Args:
        jobs: List of jobs to choose from
        action: Description of the action (for prompt text)

    Returns:
        Selected job or None if cancelled
    """
    if not jobs:
        return None

    if len(jobs) == 1:
        return jobs[0]

    # Multiple jobs - show selector
    click.echo(f"Multiple jobs found. Select one to {action}:")
    click.echo()

    for i, job in enumerate(jobs, 1):
        model_name = ""
        if job.model_path:
            model_name = (
                job.model_path.split("/")[-1]
                if "/" in job.model_path
                else job.model_path
            )
        state_icon = "●" if job.state == "RUNNING" else "○"
        url_info = f" - {job.endpoint_url}" if job.endpoint_url else ""
        click.echo(f"  [{i}] {state_icon} {job.job_id}: {model_name}{url_info}")

    click.echo("  [0] Cancel")
    click.echo()

    while True:
        choice = click.prompt("Enter number", type=int, default=1)
        if choice == 0:
            return None
        if 1 <= choice <= len(jobs):
            return jobs[choice - 1]
        click.echo(f"Invalid choice. Please enter 0-{len(jobs)}")


@click.group(invoke_without_command=True)
@click.version_option(version=__version__)
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose logging")
@click.option("--model", "-m", type=str, help="Model to serve")
@click.option("--workers", "-w", type=int, default=1, help="Number of workers")
@click.option("--nodes-per-worker", "-n", type=int, default=1, help="Nodes per worker")
@click.option("--partition", "-p", type=str, default=None, help="SLURM partition")
@click.option(
    "--environment",
    "-e",
    type=str,
    default=None,
    help="Container environment",
)
@click.option("--tp-size", type=int, default=1, help="Tensor parallel size")
@click.option("--ep-size", type=int, default=1, help="Expert parallel size")
@click.option(
    "--num-gpus-per-worker",
    type=click.Choice(["1", "2", "4"]),
    default="4",
    help="GPUs per worker process",
)
@click.option(
    "--cuda-graph-max-bs", type=int, default=256, help="Max batch size for CUDA graphs"
)
@click.option(
    "--grammar-backend", type=str, default="llguidance", help="Grammar backend"
)
@click.option("--router-policy", type=str, default="cache_aware", help="Router policy")
@click.option(
    "--router-environment",
    type=str,
    default=None,
    help="Router container environment",
)
@click.option(
    "--reasoning-parser", type=str, default="", help="Reasoning parser module"
)
@click.option(
    "--tool-call-parser", type=str, default="", help="Tool call parser module"
)
@click.option(
    "--time-limit", "-t", type=str, default=None, help="Job time limit (HH:MM:SS)"
)
@click.pass_context
def main(
    ctx,
    verbose: bool,
    model: Optional[str],
    workers: int,
    nodes_per_worker: int,
    partition: Optional[str],
    environment: Optional[str],
    tp_size: int,
    ep_size: int,
    num_gpus_per_worker: str,
    cuda_graph_max_bs: int,
    grammar_backend: str,
    router_policy: str,
    router_environment: Optional[str],
    reasoning_parser: str,
    tool_call_parser: str,
    time_limit: Optional[str],
):
    """clserve - CLI tool for serving LLM models on Alps.

    Serve a model:

      clserve -m deepseek-v3
      clserve -m deepseek-v3 -w 2
      clserve -m my-org/my-model --tp-size 4

    Other commands:

      clserve status            # Check status of jobs
      clserve url deepseek-v3   # Get endpoint URL
      clserve stop deepseek-v3  # Stop a job
      clserve models            # List available models
    """
    setup_logging(verbose)

    if model:
        # Serve the model
        _serve_model(
            model=model,
            workers=workers,
            nodes_per_worker=nodes_per_worker,
            partition=partition,
            environment=environment,
            tp_size=tp_size,
            ep_size=ep_size,
            num_gpus_per_worker=num_gpus_per_worker,
            cuda_graph_max_bs=cuda_graph_max_bs,
            grammar_backend=grammar_backend,
            router_policy=router_policy,
            router_environment=router_environment,
            reasoning_parser=reasoning_parser,
            tool_call_parser=tool_call_parser,
            time_limit=time_limit,
        )
    elif ctx.invoked_subcommand is None:
        # No model and no subcommand - show help
        click.echo(ctx.get_help())


def _serve_model(
    model: str,
    workers: int,
    nodes_per_worker: int,
    partition: Optional[str],
    environment: Optional[str],
    tp_size: int,
    ep_size: int,
    num_gpus_per_worker: str,
    cuda_graph_max_bs: int,
    grammar_backend: str,
    router_policy: str,
    router_environment: Optional[str],
    reasoning_parser: str,
    tool_call_parser: str,
    time_limit: Optional[str],
):
    """Serve a model (internal function)."""
    # Load user config for defaults
    user_config = load_config()

    args = SubmitArgs(
        model=model,
        workers=workers,
        nodes_per_worker=nodes_per_worker,
        partition=partition if partition is not None else user_config.partition,
        environment=environment if environment is not None else user_config.environment,
        tp_size=tp_size,
        ep_size=ep_size,
        num_gpus_per_worker=int(num_gpus_per_worker),
        cuda_graph_max_bs=cuda_graph_max_bs,
        grammar_backend=grammar_backend,
        router_policy=router_policy,
        router_environment=router_environment
        if router_environment is not None
        else user_config.router_environment,
        reasoning_parser=reasoning_parser,
        tool_call_parser=tool_call_parser,
        time_limit=time_limit if time_limit is not None else user_config.time_limit,
    )

    # Show config info if using predefined config
    config = load_model_config(model)
    if config:
        click.echo(f"Using predefined config for {model}:")
        click.echo(f"  Model: {config.model_path}")
        click.echo(f"  TP size: {config.tp_size}")
        click.echo(f"  Nodes per worker: {config.nodes_per_worker}")
        click.echo(f"  GPUs per worker: {config.num_gpus_per_worker}")
        click.echo()

    try:
        job_id = serve(args)
        click.echo("Job submitted successfully!")
        click.echo(f"  Job ID: {job_id}")
        click.echo(f"  Logs: {CLSERVE_LOGS_DIR / job_id}/log.out")
        click.echo()
        click.echo("Check status with:")
        click.echo("  clserve status")
        click.echo()
        click.echo("Get endpoint URL with:")
        click.echo(f"  clserve url {model}")
        click.echo()
        click.echo("Stop the job with:")
        click.echo(f"  clserve stop {model}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@main.command()
@click.argument("identifier", required=False)
def status(identifier: str = None):
    """Show status of serving jobs.

    IDENTIFIER is optional - can be a job ID or model name.
    If not provided, shows all running jobs.

    Examples:

      # Show all running jobs
      clserve status

      # Show status for a specific job
      clserve status 12345

      # Show status for jobs serving a model
      clserve status deepseek-v3
    """
    if identifier:
        # Show specific job(s)
        if identifier.isdigit():
            job = get_job_info(identifier)
            if job:
                _print_job_details(job)
            else:
                click.echo(f"Job {identifier} not found")
        else:
            jobs = find_jobs_by_model(identifier)
            if jobs:
                _print_jobs_table(jobs)
            else:
                click.echo(f"No jobs found for model '{identifier}'")
    else:
        # Show all jobs
        jobs = list_serving_jobs()
        if jobs:
            _print_jobs_table(jobs)
        else:
            click.echo("No running jobs found")
            click.echo()
            click.echo("Start a new job with:")
            click.echo("  clserve -m <model>")


def _format_stage(stage: WorkerLoadingStage) -> str:
    """Format worker loading stage for display with colored text."""
    stage_map = {
        WorkerLoadingStage.UNKNOWN: ("white", "UNKNOWN"),
        WorkerLoadingStage.INITIALIZING: ("blue", "INITIALIZING"),
        WorkerLoadingStage.LOADING_WEIGHTS: ("yellow", "LOADING WEIGHTS"),
        WorkerLoadingStage.CAPTURING_CUDA_GRAPH: ("magenta", "CAPTURING CUDA GRAPH"),
        WorkerLoadingStage.READY: ("green", "READY"),
        WorkerLoadingStage.ERROR: ("red", "ERROR"),
    }
    color, text = stage_map.get(stage, ("white", stage.value.upper()))
    return click.style(text, fg=color, bold=True)


def _print_job_details(job):
    """Print detailed info for a single job."""
    click.echo(f"Job ID: {job.job_id}")
    click.echo(f"Name: {job.job_name}")
    click.echo(f"State: {job.state}")
    click.echo(f"Nodes: {job.node_list}")
    if job.model_path:
        click.echo(f"Model: {job.model_path}")
    if job.endpoint_url:
        click.echo(f"Endpoint URL: {job.endpoint_url}")
    if job.time_limit:
        click.echo(f"Time limit: {job.time_limit}")
    if job.time_left:
        click.echo(f"Time left: {job.time_left}")
    if job.workers:
        click.echo(f"Workers: {job.workers}")
    if job.nodes_per_worker:
        click.echo(f"Nodes per worker: {job.nodes_per_worker}")
    if job.tp_size:
        click.echo(f"TP size: {job.tp_size}")
    if job.use_router is not None:
        click.echo(f"Router: {'enabled' if job.use_router else 'disabled'}")

    # Show worker statuses if available
    if job.worker_statuses:
        click.echo()
        click.echo("Worker Status:")

        # Group by stage
        stage_counts = {}
        for ws in job.worker_statuses:
            stage_counts[ws.stage] = stage_counts.get(ws.stage, 0) + 1

        # Display summary
        for stage, count in sorted(stage_counts.items(), key=lambda x: x[0].value):
            click.echo(f"  {_format_stage(stage)}: {count} worker(s)")

        # Show router info if available
        if job.use_router and job.router_worker_count is not None:
            total_workers = len(job.worker_statuses)
            click.echo()
            click.echo(
                f"Router Status: {job.router_worker_count}/{total_workers} workers registered"
            )

        # Show individual worker details
        click.echo()
        click.echo("Worker Details:")
        for ws in job.worker_statuses:
            click.echo(
                f"  Worker {ws.worker_id} ({ws.node}): {_format_stage(ws.stage)}"
            )


def _get_loading_status_summary(job: JobInfo) -> str:
    """Get a short summary of worker loading status."""
    if not job.worker_statuses:
        return ""

    # Count workers in each stage
    ready = sum(1 for ws in job.worker_statuses if ws.stage == WorkerLoadingStage.READY)
    total = len(job.worker_statuses)

    if ready == total:
        return click.style("READY", fg="green", bold=True)
    elif ready == 0:
        # Find the most common non-ready stage
        stages = [ws.stage for ws in job.worker_statuses]
        if all(s == WorkerLoadingStage.INITIALIZING for s in stages):
            return click.style("INITIALIZING", fg="blue", bold=True)
        elif any(s == WorkerLoadingStage.LOADING_WEIGHTS for s in stages):
            return click.style("LOADING", fg="yellow", bold=True)
        elif any(s == WorkerLoadingStage.CAPTURING_CUDA_GRAPH for s in stages):
            return click.style("CUDA GRAPH", fg="magenta", bold=True)
        elif any(s == WorkerLoadingStage.ERROR for s in stages):
            return click.style("ERROR", fg="red", bold=True)
        else:
            return click.style("STARTING", fg="white", bold=True)
    else:
        return click.style(f"{ready}/{total} READY", fg="yellow", bold=True)


def _print_jobs_table(jobs):
    """Print jobs as a table."""
    table = PrettyTable()
    table.field_names = ["Job ID", "Name", "State", "Status", "Time Left", "Model", "Endpoint URL"]
    table.align = "l"

    for job in jobs:
        model_name = job.model_path or ""
        endpoint = job.endpoint_url or "(pending)"
        if len(endpoint) > 35:
            endpoint = endpoint[:32] + "..."

        # Get loading status
        status = _get_loading_status_summary(job) if job.state == "RUNNING" else "-"

        # Get time left
        time_left = job.time_left or "-"

        table.add_row(
            [
                job.job_id,
                job.job_name,
                job.state,
                status,
                time_left,
                model_name,
                endpoint,
            ]
        )

    click.echo(table)


@main.command()
@click.argument("model")
def url(model: str):
    """Get the endpoint URL for a serving job.

    MODEL is the model name or alias (e.g., deepseek-v3, llama-405b).
    If multiple jobs are serving the same model, you'll be prompted to select one.

    Examples:

      # Get URL by model name
      clserve url deepseek-v3

      # Get URL by full model path
      clserve url deepseek-ai/DeepSeek-V3.1
    """
    jobs = find_jobs_by_model(model)
    if not jobs:
        click.echo(f"No jobs found for model '{model}'", err=True)
        raise SystemExit(1)

    # Filter to running jobs with URLs first
    running_with_url = [j for j in jobs if j.state == "RUNNING" and j.endpoint_url]
    if len(running_with_url) == 1:
        click.echo(running_with_url[0].endpoint_url)
        return

    # If multiple running jobs or none with URL, use selector
    running_jobs = [j for j in jobs if j.state == "RUNNING"]
    if not running_jobs:
        click.echo(f"No running jobs found for model '{model}'", err=True)
        raise SystemExit(1)

    job = select_job(running_jobs, action="get URL")
    if job is None:
        return  # User cancelled

    if job.endpoint_url:
        click.echo(job.endpoint_url)
    else:
        click.echo(f"Job {job.job_id} does not have an endpoint URL yet", err=True)
        click.echo("The job may still be starting up. Check status with:", err=True)
        click.echo("  clserve status", err=True)
        raise SystemExit(1)


@main.command()
@click.argument("model", required=False)
@click.option(
    "--all", "-a", "stop_all_flag", is_flag=True, help="Stop all matching jobs"
)
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
def stop_cmd(model: str = None, stop_all_flag: bool = False, force: bool = False):
    """Stop serving jobs.

    MODEL is the model name or alias (e.g., deepseek-v3, llama-405b).
    If multiple jobs are serving the same model, you'll be prompted to select one
    (unless --all is used).

    Examples:

      # Stop by model name (selector if multiple)
      clserve stop deepseek-v3

      # Stop all jobs for a model
      clserve stop deepseek-v3 --all

      # Stop all running jobs
      clserve stop all
      clserve stop --all
    """
    # Treat "all" as a special keyword to stop all jobs
    if model is not None and model.lower() == "all":
        model = None
        stop_all_flag = True

    if model is None and not stop_all_flag:
        click.echo(
            "Error: Please provide a model name, or use --all to stop all jobs",
            err=True,
        )
        raise SystemExit(1)

    if stop_all_flag and model is None:
        # Stop all clserve jobs
        jobs = list_serving_jobs()
        running = [j for j in jobs if j.state in ["RUNNING", "PENDING"]]
        if not running:
            click.echo("No running jobs to stop")
            return

        if not force:
            click.echo(f"This will stop {len(running)} job(s):")
            for job in running:
                model_name = job.model_path or job.job_name
                if "/" in model_name:
                    model_name = model_name.split("/")[-1]
                click.echo(f"  {job.job_id}: {model_name}")
            if not click.confirm("Continue?"):
                return

        stopped = stop_all()
        if stopped:
            click.echo(f"Stopped {len(stopped)} job(s): {', '.join(stopped)}")
        else:
            click.echo("No jobs were stopped")
    else:
        # Stop job(s) for specific model
        jobs = find_jobs_by_model(model)
        running = [j for j in jobs if j.state in ["RUNNING", "PENDING"]]

        if not running:
            click.echo(f"No running jobs found for model '{model}'", err=True)
            raise SystemExit(1)

        if stop_all_flag:
            # Stop all matching jobs
            if not force:
                click.echo(f"This will stop {len(running)} job(s) for '{model}':")
                for job in running:
                    click.echo(f"  {job.job_id}")
                if not click.confirm("Continue?"):
                    return

            stopped = []
            for job in running:
                if stop_by_job_id(job.job_id):
                    stopped.append(job.job_id)

            if stopped:
                click.echo(f"Stopped {len(stopped)} job(s): {', '.join(stopped)}")
            else:
                click.echo("No jobs were stopped")
        else:
            # Select single job to stop
            job = select_job(running, action="stop")
            if job is None:
                return  # User cancelled

            if stop_by_job_id(job.job_id):
                click.echo(f"Stopped job {job.job_id}")
            else:
                click.echo(f"Failed to stop job {job.job_id}", err=True)
                raise SystemExit(1)


# Alias 'stop' command
main.add_command(stop_cmd, name="stop")


@main.command()
def models():
    """List available predefined model configurations.

    These models have optimized configurations for the cluster.

    Example:

      clserve -m deepseek-v3
      clserve -m Qwen/Qwen3-235B-A22B-Instruct-2507
    """
    table = PrettyTable()
    table.field_names = ["Alias", "Model Path", "TP", "Nodes/Worker"]
    table.align = "l"

    configs = list_available_configs()

    for config_name in sorted(configs):
        # Convert config filename to alias
        alias = config_name.replace("_", "-")
        config = load_model_config(alias)
        if config:
            table.add_row(
                [
                    alias,
                    config.model_path,
                    config.tp_size,
                    config.nodes_per_worker,
                ]
            )

    if configs:
        click.echo("Available predefined model configurations:")
        click.echo()
        click.echo(table)
        click.echo()
        click.echo(
            "Use 'clserve -m <alias>' to serve a model with its predefined config."
        )
        click.echo()
        click.echo(
            "Don't see the model you need? Request it with: clserve request <model>"
        )
    else:
        click.echo("No predefined model configurations found.")


@main.command()
@click.argument("model")
def request(model: str):
    """Request a new model to be added to clserve.

    Opens a GitHub issue URL with pre-filled information to request
    adding a new model configuration.

    MODEL is the HuggingFace model path (e.g., meta-llama/Llama-3.1-70B-Instruct)
    or a model name you'd like to see supported.

    Examples:

      clserve request meta-llama/Llama-3.1-70B-Instruct
      clserve request mistral-large
    """
    import urllib.parse

    # Check if model already exists
    config = load_model_config(model)
    if config:
        click.echo(f"Model '{model}' is already available!")
        click.echo(f"  Use: clserve -m {model}")
        return

    # Build the GitHub issue URL
    title = f"Add model: {model}"
    body = f"""## Model Request

**Model name/path:** {model}

**HuggingFace URL:** https://huggingface.co/{model}

## Details

<!-- Please fill in the following information -->

**Why do you need this model?**


**Suggested configuration (if known):**
- Tensor Parallel Size (TP):
- Nodes per worker:
- Any special requirements:

---
*Requested via `clserve request`*
"""

    params = urllib.parse.urlencode({
        "title": title,
        "body": body,
        "labels": "model-request",
    })

    issue_url = f"https://github.com/nathanrchn/clserve/issues/new?{params}"

    click.echo("To request this model, open the following URL:")
    click.echo()
    click.echo(f"  {issue_url}")
    click.echo()
    click.echo("This will create a GitHub issue to request adding the model.")


@main.command()
@click.argument("model")
@click.option(
    "--revision", "-r", type=str, default=None, help="Specific model revision/branch"
)
def download(model: str, revision: str = None):
    """Download a model from HuggingFace Hub.

    MODEL is the model name or alias (e.g., deepseek-v3, llama-405b)
    or a full HuggingFace path (e.g., meta-llama/Llama-3.1-70B-Instruct).

    Examples:

      # Download using alias
      clserve download deepseek-v3

      # Download using full path
      clserve download meta-llama/Llama-3.1-70B-Instruct

      # Download specific revision
      clserve download deepseek-v3 --revision main
    """
    from clserve.configs import get_model_path, load_model_config

    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        click.echo(
            "Error: huggingface_hub is required for downloading models", err=True
        )
        click.echo("Install it with: pip install huggingface_hub", err=True)
        raise SystemExit(1)

    # Resolve alias to full path
    model_path = get_model_path(model)

    # Show config info if using predefined config
    config = load_model_config(model)
    if config:
        click.echo(f"Downloading model: {config.model_path}")
    else:
        click.echo(f"Downloading model: {model_path}")

    try:
        path = snapshot_download(
            repo_id=model_path,
            revision=revision,
        )
        click.echo(f"Downloaded to: {path}")
    except Exception as e:
        click.echo(f"Error downloading model: {e}", err=True)
        raise SystemExit(1)


@main.command()
@click.argument("model")
def logs(model: str):
    """Show the log file path for a job.

    MODEL is the model name or alias (e.g., deepseek-v3, llama-405b).
    If multiple jobs are serving the same model, you'll be prompted to select one.

    Example:

      clserve logs deepseek-v3
      tail -f $(clserve logs deepseek-v3)/log.out
    """
    jobs = find_jobs_by_model(model)
    if not jobs:
        click.echo(f"No jobs found for model '{model}'", err=True)
        raise SystemExit(1)

    # If only one job, use it directly
    if len(jobs) == 1:
        job = jobs[0]
    else:
        # Prefer running jobs
        running = [j for j in jobs if j.state == "RUNNING"]
        if len(running) == 1:
            job = running[0]
        else:
            # Multiple jobs - use selector
            job = select_job(running if running else jobs, action="view logs")
            if job is None:
                return  # User cancelled

    log_path = CLSERVE_LOGS_DIR / job.job_id
    click.echo(log_path)


@main.command()
@click.option("--show", "-s", is_flag=True, help="Show current configuration")
@click.option("--account", "-a", type=str, help="Set cluster account")
@click.option("--partition", "-p", type=str, help="Set default partition")
@click.option("--environment", "-e", type=str, help="Set default container environment")
@click.option("--router-environment", type=str, help="Set router container environment")
@click.option("--time-limit", "-t", type=str, help="Set default time limit (HH:MM:SS)")
def config(
    show: bool,
    account: str,
    partition: str,
    environment: str,
    router_environment: str,
    time_limit: str,
):
    """Configure clserve defaults.

    Configuration is stored in ~/.clserve/config.toml and provides
    default values for common options.

    Examples:

      # Show current configuration
      clserve config --show

      # Set cluster account
      clserve config --account myproject

      # Set multiple values
      clserve config --partition normal --time-limit 08:00:00

      # Interactive configuration (no options)
      clserve config
    """
    current = load_config()

    # If --show flag, just display current config
    if show:
        _show_config(current)
        return

    # If any option is provided, update that value
    if any([account, partition, environment, router_environment, time_limit]):
        if account is not None:
            current.account = account
        if partition is not None:
            current.partition = partition
        if environment is not None:
            current.environment = environment
        if router_environment is not None:
            current.router_environment = router_environment
        if time_limit is not None:
            current.time_limit = time_limit

        save_config(current)
        click.echo("Configuration updated:")
        _show_config(current)
        return

    # Interactive mode - prompt for each value
    click.echo("Configure clserve defaults")
    click.echo(f"Config file: {CONFIG_FILE}")
    click.echo()

    # Account
    default_account = current.account or get_default_account() or ""
    account_prompt = "Cluster account"
    if default_account:
        account_prompt += f" [{default_account}]"
    new_account = click.prompt(
        account_prompt, default=default_account, show_default=False
    )
    current.account = new_account

    # Partition
    new_partition = click.prompt(
        "Default partition",
        default=current.partition,
    )
    current.partition = new_partition

    # Environment
    new_environment = click.prompt(
        "Default container environment",
        default=current.environment,
    )
    current.environment = new_environment

    # Router environment
    new_router_env = click.prompt(
        "Router container environment",
        default=current.router_environment,
    )
    current.router_environment = new_router_env

    # Time limit
    new_time_limit = click.prompt(
        "Default time limit (HH:MM:SS)",
        default=current.time_limit,
    )
    current.time_limit = new_time_limit

    save_config(current)
    click.echo()
    click.echo("Configuration saved!")
    _show_config(current)


def _show_config(config: UserConfig):
    """Display current configuration."""
    click.echo()
    click.echo(f"Config file: {CONFIG_FILE}")
    click.echo()
    click.echo(f"  account:            {config.account or '(not set)'}")
    click.echo(f"  partition:          {config.partition}")
    click.echo(f"  environment:        {config.environment}")
    click.echo(f"  router_environment: {config.router_environment}")
    click.echo(f"  time_limit:         {config.time_limit}")


if __name__ == "__main__":
    main()
