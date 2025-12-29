# utdg_env/experiment/manager.py

"""
ExperimentManager
Coordinates paths, metadata, model card generation, and
experiment bookkeeping for RL training runs.

This class is constructed once in the training script and
shared with callbacks such as HFUploadCallback.
"""

from __future__ import annotations

import os
import json
import shutil
from pathlib import Path
from dataclasses import dataclass, field

from omegaconf import DictConfig, OmegaConf

from .. import __version__
from .model_card import ModelCardBuilder
from .utils import ensure_dir, timestamp_utc


# ------------------------------------------------------------
# Structured path container
# ------------------------------------------------------------
@dataclass
class PathRegistry:
    root: Path
    run_dir: Path
    logs_dir: Path
    model_dir: Path
    model_file: Path
    hf_repo_tmp: Path


# ------------------------------------------------------------
# Structured HF settings container
# ------------------------------------------------------------
@dataclass
class HFSettings:
    repo_id: str
    repo_type: str
    private: bool
    lfs_files: list[str]
    metadata: dict
    upload_logs: bool
    create_branch: bool


# ------------------------------------------------------------
# Experiment Manager
# ------------------------------------------------------------
class ExperimentManager:
    """
    Responsible for run directory setup, path bookkeeping,
    metadata preparation, and model card generation.

    Not a callback. Callbacks receive a reference to this manager.
    """

    def __init__(self, cfg: DictConfig):
        """
        Parameters
        ----------
        cfg : DictConfig
            Complete Hydra config for this training run.
        """
        self.cfg = cfg

        # ------------------------------------------------------------
        # Setup run directory
        # ------------------------------------------------------------
        exp_root = Path("experiments")
        ensure_dir(exp_root)

        run_name = cfg.get("run_name", None)
        if run_name is None:
            run_name = timestamp_utc()

        run_dir = exp_root / run_name
        ensure_dir(run_dir)

        # model directory + model file path
        model_dir = run_dir / "model"
        ensure_dir(model_dir)

        # Extract model filename from checkpoint config (name_prefix)
        checkpoint_cfg = cfg.get("checkpoint", {})
        name_prefix = checkpoint_cfg.get("name_prefix", "final_model")
        model_filename = f"{name_prefix}_v{__version__}.zip"
        model_file = model_dir / model_filename

        # logs directory
        logs_dir = run_dir / "logs"
        ensure_dir(logs_dir)

        # temporary HF repo clone directory
        hf_repo_tmp = run_dir / "hf_repo_tmp"

        self.paths = PathRegistry(
            root=exp_root,
            run_dir=run_dir,
            logs_dir=logs_dir,
            model_dir=model_dir,
            model_file=model_file,
            hf_repo_tmp=hf_repo_tmp,
        )

        # ------------------------------------------------------------
        # Load HF metadata and settings from config
        # ------------------------------------------------------------
        hf_cfg = cfg.get("callbacks", {}).get("hf_upload", {})

        self.hf = HFSettings(
            repo_id=hf_cfg.get("repo_id", "unknown/repo"),
            repo_type=hf_cfg.get("repo_type", "model"),
            private=hf_cfg.get("private", True),
            lfs_files=hf_cfg.get("lfs", {}).get("files", ["*.zip"]),
            metadata=hf_cfg.get("metadata", {}),
            upload_logs=hf_cfg.get("upload_logs", True),
            create_branch=hf_cfg.get("create_branch", True),
        )

        # ------------------------------------------------------------
        # Model card generator
        # ------------------------------------------------------------
        self.model_card = ModelCardBuilder(self)

    # ------------------------------------------------------------
    # Save final SB3 model here
    # ------------------------------------------------------------
    def save_model(self, model) -> Path:
        """
        Save final SB3 model to the experiment directory.
        """
        path = self.paths.model_file
        model.save(str(path))
        return path

    # ------------------------------------------------------------
    # Optional: dump Hydra config for reproducibility
    # ------------------------------------------------------------
    def save_config_snapshot(self) -> None:
        snapshot_path = self.paths.run_dir / "hydra_config.json"
        os.makedirs(self.paths.run_dir, exist_ok=True)

        cfg_dict = OmegaConf.to_container(self.cfg, resolve=True)

        with open(snapshot_path, "w") as f:
            json.dump(cfg_dict, f, indent=2)

    # ------------------------------------------------------------
    # Cleanup temporary HF directory if used before
    # ------------------------------------------------------------
    def clear_hf_tmp(self) -> None:
        tmp = self.paths.hf_repo_tmp
        if tmp.exists():
            shutil.rmtree(tmp)
