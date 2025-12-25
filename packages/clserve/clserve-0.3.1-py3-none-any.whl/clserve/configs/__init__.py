"""Model configurations for clserve."""

import yaml
from typing import Optional
from dataclasses import dataclass

try:
    from importlib.resources import files
except ImportError:
    from importlib_resources import files


class Defaults:
    """Default values for model serving configuration.

    This is the single source of truth for all default values.
    """

    WORKERS: int = 1
    NODES_PER_WORKER: int = 1
    PARTITION: str = "normal"
    ENVIRONMENT: str = "/capstor/store/cscs/swissai/infra01/reasoning/imgs/projects/vs:251215/env.toml"
    TP_SIZE: int = 1
    EP_SIZE: int = 1
    NUM_GPUS_PER_WORKER: int = 4
    CUDA_GRAPH_MAX_BS: int = 256
    GRAMMAR_BACKEND: str = "llguidance"
    ROUTER_POLICY: str = "cache_aware"
    ROUTER_ENVIRONMENT: str = "/capstor/store/cscs/swissai/infra01/reasoning/imgs/projects/vs:251215/env.toml"
    REASONING_PARSER: str = ""
    TOOL_CALL_PARSER: str = ""
    TIME_LIMIT: str = "04:00:00"


@dataclass
class ModelConfig:
    """Configuration for serving a specific model."""

    model_path: str
    tp_size: int = Defaults.TP_SIZE
    ep_size: int = Defaults.EP_SIZE
    workers: int = Defaults.WORKERS
    nodes_per_worker: int = Defaults.NODES_PER_WORKER
    num_gpus_per_worker: int = Defaults.NUM_GPUS_PER_WORKER
    cuda_graph_max_bs: int = Defaults.CUDA_GRAPH_MAX_BS
    grammar_backend: str = Defaults.GRAMMAR_BACKEND
    reasoning_parser: str = Defaults.REASONING_PARSER
    tool_call_parser: str = Defaults.TOOL_CALL_PARSER
    router_policy: str = Defaults.ROUTER_POLICY


# Model aliases for convenience
MODEL_ALIASES = {
    # Qwen models
    "qwen3-235b": "Qwen/Qwen3-235B-A22B-Instruct-2507",
    "qwen3-coder-480b": "Qwen/Qwen3-Coder-480B-A35B-Instruct",
    "qwen3-32b": "Qwen/Qwen3-32B",
    "qwen3-8b": "Qwen/Qwen3-8B",
    "qwen3-embedding-4b": "Qwen/Qwen3-Embedding-4B",
    # DeepSeek models
    "deepseek-v3": "deepseek-ai/DeepSeek-V3.1",
    "deepseek-v3.2": "deepseek-ai/DeepSeek-V3.2",
    "deepseek-r1": "deepseek-ai/DeepSeek-R1",
    # OpenAI models
    "gpt-oss-120b": "openai/gpt-oss-120b",
    # MiniMax models
    "minimax-m2": "MiniMaxAI/MiniMax-M2",
    # Moonshot models
    "kimi-k2": "moonshotai/Kimi-K2-Instruct-0905",
    # Llama models
    "llama-405b": "meta-llama/Llama-3.1-405B-Instruct",
    "llama-70b": "meta-llama/Llama-3.1-70B-Instruct",
    "llama-8b": "meta-llama/Llama-3.1-8B-Instruct",
    # Swiss AI models
    "apertus-8b": "swiss-ai/Apertus-8B-Instruct-2509",
    # ServiceNow models
    "apriel-15b-thinker": "ServiceNow-AI/Apriel-1.6-15b-Thinker",
    # NVIDIA models
    "nemotron-nano-30b": "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16",
}


def get_model_path(model_name: str) -> str:
    """Resolve model alias to full path, or return as-is if not an alias."""
    return MODEL_ALIASES.get(model_name.lower(), model_name)


def load_model_config(model_name: str) -> Optional[ModelConfig]:
    """Load predefined configuration for a model.

    Args:
        model_name: Model name, alias, or full HuggingFace path

    Returns:
        ModelConfig if found, None otherwise
    """
    # Normalize the model name for config lookup
    lookup_name = model_name.lower().replace("/", "_").replace("-", "_")

    # Also try the alias name if it exists
    for alias, path in MODEL_ALIASES.items():
        if model_name == path or model_name.lower() == alias:
            lookup_name = alias.replace("-", "_")
            break

    try:
        config_content = (
            files("clserve") / "configs" / "models" / f"{lookup_name}.yaml"
        ).read_text()
        config_dict = yaml.safe_load(config_content)
        return ModelConfig(**config_dict)
    except (FileNotFoundError, TypeError):
        return None


def list_available_configs() -> list[str]:
    """List all available predefined model configurations."""
    try:
        models_dir = files("clserve") / "configs" / "models"
        return [
            f.name.replace(".yaml", "")
            for f in models_dir.iterdir()
            if f.name.endswith(".yaml")
        ]
    except (FileNotFoundError, TypeError):
        return []
