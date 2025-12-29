"""
HFUploadCallback: Upload final SB3 model + metadata to Hugging Face Hub.

This version is fully integrated with the ExperimentManager.

Features:
- Upload triggered after training finishes (push_strategy="final").
- Saves model automatically before upload (via self.model from BaseCallback)
- Uses ExperimentManager for:
    - model paths
    - metadata
    - model card generation
    - snapshot capture
    - unified output directories
- Proper Git LFS configuration
- Repo auto-creation with correct repo_type/private flags
- Branch pinning ("production")
- Optional training log upload

Updated for huggingface_hub >= 0.14 (no deprecated Repository class).
"""

import os
import shutil
from pathlib import Path
from typing import Optional

from huggingface_hub import (
    HfApi,
    create_repo,
    upload_folder,
    upload_file,
)

from stable_baselines3.common.callbacks import BaseCallback


class HFUploadCallback(BaseCallback):
    """
    HuggingFace Upload Callback with ExperimentManager integration.

    Parameters
    ----------
    manager : ExperimentManager
        Central manager for paths, metadata, and model card generation.
    push_strategy : str
        Upload strategy, currently only "final" is supported.
    verbose : int
        Verbosity level.
    """

    def __init__(
        self,
        manager,
        push_strategy: str = "final",
        verbose: int = 1,
    ):
        super().__init__(verbose)
        self.manager = manager
        self.push_strategy = push_strategy
        self.api = HfApi()

    # ------------------------------------------------------------
    # Helper: Get HF token from various sources
    # ------------------------------------------------------------
    def _get_token(self) -> Optional[str]:
        """
        Get HF token from various sources.

        Checks in order:
        1. HfApi cached token
        2. Environment variables (HF_TOKEN, HUGGING_FACE_HUB_TOKEN)
        3. .env file via python-dotenv (for local development)
        4. huggingface-cli stored token

        Returns
        -------
        str or None
            The token if found, None otherwise.
        """
        # 1. Check if already set in HfApi
        if self.api.token:
            return self.api.token

        # 2. Check environment variables
        token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
        if token:
            return token

        # 3. Try loading from .env file (local dev)
        try:
            from dotenv import load_dotenv
            load_dotenv()
            token = os.environ.get("HF_TOKEN")
            if token:
                return token
        except ImportError:
            pass

        # 4. Check huggingface-cli stored token
        try:
            from huggingface_hub import HfFolder
            token = HfFolder.get_token()
            if token:
                return token
        except Exception:
            pass

        return None

    # ------------------------------------------------------------
    # SB3: Callback step hook
    # ------------------------------------------------------------
    def _on_step(self) -> bool:
        return True

    # ------------------------------------------------------------
    # SB3: Called when training ends
    # ------------------------------------------------------------
    def _on_training_end(self) -> None:
        import logging
        logger = logging.getLogger("UTDG.HFUploadCallback")

        if self.push_strategy != "final":
            return

        logger.info("[HFUploadCallback] Training complete. Beginning upload...")

        try:
            # ------------------------------------------------------------
            # Validate HF token
            # ------------------------------------------------------------
            token = self._get_token()

            if token is None:
                raise RuntimeError(
                    "No HuggingFace token found. Options:\n"
                    "  1. Run `huggingface-cli login`\n"
                    "  2. Set HF_TOKEN in .env file (requires python-dotenv)\n"
                    "  3. Export HF_TOKEN environment variable"
                )

            repo_id = self.manager.hf.repo_id
            repo_type = self.manager.hf.repo_type
            private = self.manager.hf.private
            lfs_patterns = self.manager.hf.lfs_files

            logger.info(f"[HFUploadCallback] Target repo: {repo_id}")

            # ------------------------------------------------------------
            # Model should already be saved by SaveModelCallback
            # (which must run BEFORE this callback)
            # ------------------------------------------------------------
            model_file = Path(self.manager.paths.model_file)

            if not model_file.exists():
                raise FileNotFoundError(
                    f"[HFUploadCallback] Model file not found at {model_file}. "
                    "Ensure SaveModelCallback runs before HFUploadCallback."
                )

            logger.info(f"[HFUploadCallback] Found model file: {model_file}")

            # ------------------------------------------------------------
            # Ensure repo exists
            # ------------------------------------------------------------
            create_repo(
                repo_id=repo_id,
                exist_ok=True,
                repo_type=repo_type,
                private=private,
                token=token,
            )

            # ------------------------------------------------------------
            # Prepare upload directory
            # ------------------------------------------------------------
            upload_dir = self.manager.paths.hf_repo_tmp

            if upload_dir.exists():
                shutil.rmtree(upload_dir)
            upload_dir.mkdir(parents=True, exist_ok=True)

            # ------------------------------------------------------------
            # Copy model checkpoint into upload directory
            # ------------------------------------------------------------
            models_dir = upload_dir / "models"
            models_dir.mkdir(parents=True, exist_ok=True)

            dst = models_dir / model_file.name
            logger.info(f"[HFUploadCallback] Copying model → {dst}")
            shutil.copy2(model_file, dst)

            # ------------------------------------------------------------
            # Also copy as "latest" generic filename (e.g. model_policy.zip)
            # ------------------------------------------------------------
            checkpoint_cfg = self.manager.cfg.get("checkpoint", {})
            name_prefix = checkpoint_cfg.get("name_prefix", "final_model")
            latest_filename = f"{name_prefix}.zip"

            if model_file.name != latest_filename:
                dst_latest = models_dir / latest_filename
                logger.info(f"[HFUploadCallback] Copying model as latest → {dst_latest}")
                shutil.copy2(model_file, dst_latest)

            # ------------------------------------------------------------
            # Configure .gitattributes for LFS
            # ------------------------------------------------------------
            self._configure_lfs(upload_dir, lfs_patterns)

            # ------------------------------------------------------------
            # Generate README model card using manager
            # ------------------------------------------------------------
            logger.info("[HFUploadCallback] Writing model card...")

            self.manager.model_card.write(
                repo_dir=upload_dir,
                model_filename=model_file.name,
            )

            # ------------------------------------------------------------
            # Upload folder to HF Hub
            # ------------------------------------------------------------
            logger.info("[HFUploadCallback] Uploading to Hugging Face Hub...")

            upload_folder(
                repo_id=repo_id,
                folder_path=str(upload_dir),
                repo_type=repo_type,
                commit_message="Upload final trained model",
                token=token,
            )

            logger.info(f"[HFUploadCallback] ✓ Model uploaded to https://huggingface.co/{repo_id}")

            # ------------------------------------------------------------
            # Logs upload (optional)
            # ------------------------------------------------------------
            if self.manager.hf.upload_logs:
                logs_dir = self.manager.paths.logs_dir
                if logs_dir.exists() and any(logs_dir.iterdir()):
                    logger.info("[HFUploadCallback] Uploading training logs...")
                    upload_folder(
                        repo_id=repo_id,
                        folder_path=str(logs_dir),
                        path_in_repo="logs",
                        repo_type=repo_type,
                        commit_message="Add training logs",
                        token=token,
                    )

            # ------------------------------------------------------------
            # Create pinned "production" branch
            # ------------------------------------------------------------
            if self.manager.hf.create_branch:
                logger.info("[HFUploadCallback] Creating 'production' branch...")

                try:
                    self.api.create_branch(
                        repo_id=repo_id,
                        branch="production",
                        repo_type=repo_type,
                        exist_ok=True,
                        token=token,
                    )

                    upload_file(
                        repo_id=repo_id,
                        path_or_fileobj=str(model_file),
                        path_in_repo=model_file.name,
                        repo_type=repo_type,
                        commit_message="Pin model to production branch",
                        revision="production",
                        token=token,
                    )

                    logger.info("[HFUploadCallback] ✓ Model pinned to 'production' branch")

                except Exception as e:
                    logger.warning(f"[HFUploadCallback] ⚠ Failed to create production branch: {e}")

            # ------------------------------------------------------------
            # Cleanup temporary directory
            # ------------------------------------------------------------
            if upload_dir.exists():
                shutil.rmtree(upload_dir)

            logger.info("[HFUploadCallback] Upload completed.")

        except Exception as e:
            logger.error(f"[HFUploadCallback] Upload FAILED: {e}")
            import traceback
            logger.error(traceback.format_exc())

    # ------------------------------------------------------------
    # Helper: Configure Git LFS via .gitattributes
    # ------------------------------------------------------------
    def _configure_lfs(self, repo_dir: Path, patterns: list[str]) -> None:
        """Create .gitattributes file with LFS patterns."""
        gitattributes = repo_dir / ".gitattributes"
        lines = [f"{p} filter=lfs diff=lfs merge=lfs -text" for p in patterns]
        content = "\n".join(lines) + "\n"

        with open(gitattributes, "w") as f:
            f.write(content)
