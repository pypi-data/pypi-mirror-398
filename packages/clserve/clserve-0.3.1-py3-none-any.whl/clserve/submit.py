"""Core job submission logic for clserve."""

import os
import random
import string
import tempfile
import subprocess
import logging
from dataclasses import dataclass

from jinja2 import Template

try:
    from importlib.resources import files
except ImportError:
    from importlib_resources import files

from clserve.configs import load_model_config, get_model_path, Defaults
from clserve.config import get_account

logger = logging.getLogger(__name__)


@dataclass
class SubmitArgs:
    """Arguments for submitting a serving job."""

    model: str
    workers: int = Defaults.WORKERS
    nodes_per_worker: int = Defaults.NODES_PER_WORKER
    partition: str = Defaults.PARTITION
    environment: str = Defaults.ENVIRONMENT
    tp_size: int = Defaults.TP_SIZE
    ep_size: int = Defaults.EP_SIZE
    num_gpus_per_worker: int = Defaults.NUM_GPUS_PER_WORKER
    cuda_graph_max_bs: int = Defaults.CUDA_GRAPH_MAX_BS
    grammar_backend: str = Defaults.GRAMMAR_BACKEND
    router_policy: str = Defaults.ROUTER_POLICY
    router_environment: str = Defaults.ROUTER_ENVIRONMENT
    reasoning_parser: str = Defaults.REASONING_PARSER
    tool_call_parser: str = Defaults.TOOL_CALL_PARSER
    time_limit: str = Defaults.TIME_LIMIT


def nanoid(length: int = 6) -> str:
    """Generate a random alphanumeric ID."""
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))


def generate_job_name(model_path: str) -> str:
    """Generate a job name with clserve prefix and nanoid.

    Format: clserve_{nanoid}

    Args:
        model_path: Full model path (unused, kept for API compatibility)

    Returns:
        Job name with clserve prefix for easy filtering
    """
    return f"clserve_{nanoid()}"


def validate_args(args: SubmitArgs) -> None:
    """Validate submission arguments.

    Args:
        args: Submission arguments to validate

    Raises:
        ValueError: If arguments are invalid
    """
    if args.num_gpus_per_worker not in [1, 2, 4]:
        raise ValueError("--num-gpus-per-worker must be 1, 2, or 4")

    if args.num_gpus_per_worker < 4:
        if args.nodes_per_worker > 1:
            raise ValueError(
                "--num-gpus-per-worker < 4 requires --nodes-per-worker=1 "
                "(multi-node distributed not supported with split GPUs)"
            )
        if args.tp_size > args.num_gpus_per_worker:
            raise ValueError(
                f"--tp-size ({args.tp_size}) cannot be greater than "
                f"--num-gpus-per-worker ({args.num_gpus_per_worker})"
            )


def merge_with_config(args: SubmitArgs) -> SubmitArgs:
    """Merge user args with predefined model config if available.

    User-provided arguments take precedence over config defaults.

    Args:
        args: User-provided arguments

    Returns:
        SubmitArgs with config defaults applied for unset values
    """
    config = load_model_config(args.model)
    if config is None:
        # No predefined config, just resolve the model path
        model_path = get_model_path(args.model)
        return SubmitArgs(
            model=model_path,
            workers=args.workers,
            nodes_per_worker=args.nodes_per_worker,
            partition=args.partition,
            environment=args.environment,
            tp_size=args.tp_size,
            ep_size=args.ep_size,
            num_gpus_per_worker=args.num_gpus_per_worker,
            cuda_graph_max_bs=args.cuda_graph_max_bs,
            grammar_backend=args.grammar_backend,
            router_policy=args.router_policy,
            router_environment=args.router_environment,
            reasoning_parser=args.reasoning_parser,
            tool_call_parser=args.tool_call_parser,
            time_limit=args.time_limit,
        )

    # Use config values as defaults, but user args override
    return SubmitArgs(
        model=config.model_path,
        workers=(
            args.workers if args.workers != Defaults.WORKERS else config.workers
        ),
        nodes_per_worker=(
            args.nodes_per_worker
            if args.nodes_per_worker != Defaults.NODES_PER_WORKER
            else config.nodes_per_worker
        ),
        partition=args.partition,
        environment=args.environment,
        tp_size=(
            args.tp_size if args.tp_size != Defaults.TP_SIZE else config.tp_size
        ),
        ep_size=(
            args.ep_size if args.ep_size != Defaults.EP_SIZE else config.ep_size
        ),
        num_gpus_per_worker=(
            args.num_gpus_per_worker
            if args.num_gpus_per_worker != Defaults.NUM_GPUS_PER_WORKER
            else config.num_gpus_per_worker
        ),
        cuda_graph_max_bs=(
            args.cuda_graph_max_bs
            if args.cuda_graph_max_bs != Defaults.CUDA_GRAPH_MAX_BS
            else config.cuda_graph_max_bs
        ),
        grammar_backend=(
            args.grammar_backend
            if args.grammar_backend != Defaults.GRAMMAR_BACKEND
            else config.grammar_backend
        ),
        router_policy=(
            args.router_policy
            if args.router_policy != Defaults.ROUTER_POLICY
            else config.router_policy
        ),
        router_environment=args.router_environment,
        reasoning_parser=args.reasoning_parser or config.reasoning_parser,
        tool_call_parser=args.tool_call_parser or config.tool_call_parser,
        time_limit=args.time_limit,
    )


def render_job_script(args: SubmitArgs) -> str:
    """Render the SLURM job script from template.

    Args:
        args: Submission arguments

    Returns:
        Rendered job script content
    """
    template_content = (files("clserve") / "templates" / "job.jinja").read_text()
    template = Template(template_content)

    # Calculate total nodes
    # When num_gpus_per_worker < 4, multiple workers can share a single node
    if args.num_gpus_per_worker == 4:
        total_nodes = args.nodes_per_worker * args.workers
    else:
        # Multiple workers per node (only valid when nodes_per_worker == 1)
        workers_per_node = 4 // args.num_gpus_per_worker
        total_nodes = (args.workers + workers_per_node - 1) // workers_per_node

    # Generate job name
    job_name = generate_job_name(args.model)

    # Format reasoning parser argument
    reasoning_parser_arg = ""
    if args.reasoning_parser:
        reasoning_parser_arg = f"--reasoning-parser {args.reasoning_parser}"

    # Format tool call parser argument
    tool_call_parser_arg = ""
    if args.tool_call_parser:
        tool_call_parser_arg = f"--tool-call-parser {args.tool_call_parser}"

    # Get home directory for log path
    home = os.path.expanduser("~")

    # Get cluster account from config or system
    cluster_account = get_account()

    return template.render(
        job_name=job_name,
        cluster_account=cluster_account,
        nodes=total_nodes,
        nodes_per_worker=args.nodes_per_worker,
        workers=args.workers,
        partition=args.partition,
        environment=args.environment,
        model_path=args.model,
        tp_size=args.tp_size,
        ep_size=args.ep_size,
        num_gpus_per_worker=args.num_gpus_per_worker,
        cuda_graph_max_bs=args.cuda_graph_max_bs,
        grammar_backend=args.grammar_backend,
        router_policy=args.router_policy,
        router_environment=args.router_environment,
        reasoning_parser=reasoning_parser_arg,
        tool_call_parser=tool_call_parser_arg,
        time_limit=args.time_limit,
        home=home,
    )


def submit_job(script_content: str) -> str:
    """Submit job script to SLURM.

    Args:
        script_content: Rendered job script

    Returns:
        Job ID

    Raises:
        RuntimeError: If job submission fails
    """
    with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
        f.write(script_content)
        script_path = f.name

    try:
        result = subprocess.run(
            ["sbatch", script_path],
            capture_output=True,
            text=True,
            check=True,
        )
        output_lines = result.stdout.strip().split("\n")
        job_id = output_lines[-1].split()[-1]
        return job_id
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to submit job: {e.stderr}")
    finally:
        os.unlink(script_path)


def ensure_clserve_dir() -> None:
    """Ensure the ~/.clserve/logs directory exists."""
    clserve_dir = os.path.expanduser("~/.clserve/logs")
    os.makedirs(clserve_dir, exist_ok=True)


def serve(args: SubmitArgs) -> str:
    """Submit a model serving job.

    This is the main entry point for submitting serving jobs.

    Args:
        args: Submission arguments

    Returns:
        Job ID of submitted job
    """
    # Ensure clserve directory exists
    ensure_clserve_dir()

    # Merge with predefined config if available
    merged_args = merge_with_config(args)

    # Validate arguments
    validate_args(merged_args)

    # Render and submit job
    script = render_job_script(merged_args)
    job_id = submit_job(script)

    return job_id
