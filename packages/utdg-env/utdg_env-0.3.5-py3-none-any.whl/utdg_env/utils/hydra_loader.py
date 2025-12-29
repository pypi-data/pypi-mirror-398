from __future__ import annotations

from typing import Optional, List

from hydra import compose, initialize_config_module
from hydra.core.global_hydra import GlobalHydra
from omegaconf import DictConfig, OmegaConf
import utdg_env.configs.config_schema


class ConfigError(RuntimeError):
    pass


REQUIRED_TOP_KEYS = ["runtime", "env", "agent"]


def load_config(
    config_name: str = "default",
    overrides: Optional[List[str]] = None,
) -> DictConfig:
    """Load Hydra configuration from utdg_env.configs module.

    Args:
        config_name: Name of config file (without .yaml)
        overrides: List of Hydra overrides (e.g., ["runtime=native", "env.episode.max_episode_steps=1000"])

    Returns:
        DictConfig with all overrides applied

    Note:
        Uses initialize_config_module() for package-relative config loading.
        This is more robust than file-path-based loading as it works
        regardless of working directory and in installed packages.
    """
    # Clear any existing Hydra instance to ensure clean state
    if GlobalHydra.instance().is_initialized():
        GlobalHydra.instance().clear()

    # Use module-based initialization (package-relative)
    initialize_config_module("utdg_env.configs", version_base=None)
    cfg = compose(config_name=config_name, overrides=overrides or [])

    # Validation
    missing = [k for k in REQUIRED_TOP_KEYS if k not in cfg]
    if missing:
        raise ConfigError(f"Invalid config: missing required sections → {missing}")

    return cfg


def pretty_print_cfg(cfg: DictConfig) -> str:
    """Return readable simplified config summary for logging."""
    runtime = cfg.runtime.mode
    agent = cfg.agent.type
    train_algo = cfg.model

    header = [
        "========== Loaded Config ==========",
        f"Runtime:        {runtime}",
        f"Agent:          {agent}",
        f"Policy:      {train_algo}",
        "===================================\n",
    ]
    return "\n".join(header) + OmegaConf.to_yaml(cfg, resolve=True)
