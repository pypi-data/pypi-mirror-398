# utdg_env/__init__.py
"""UTDG Gymnasium environment."""

from utdg_env.__version__ import __version__
from utdg_env.env.base_env import UntitledTowerDefenseEnv
from utdg_env.env.registry import register_env

from utdg_env.experiment.manager import ExperimentManager
from utdg_env.callbacks.hf_upload_callback import HFUploadCallback
from utdg_env.callbacks.wandb_callback import WandbEpisodeCallback, WandbEvalCallback

__all__ = [
    "__version__",
    "UntitledTowerDefenseEnv",
    "register_env",
    "ExperimentManager",
    "HFUploadCallback",
    "WandbEpisodeCallback",
    "WandbEvalCallback"
]
