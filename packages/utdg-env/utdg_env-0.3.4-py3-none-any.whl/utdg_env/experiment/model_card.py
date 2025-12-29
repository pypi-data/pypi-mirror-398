# utdg_env/experiment/model_card.py
"""
ModelCardBuilder
Creates README.md for the Hugging Face Hub upload with comprehensive metadata
and documentation following HF model card best practices.
"""
from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import Any

from omegaconf import OmegaConf

from .utils import indent_block


class ModelCardBuilder:
    """Builds comprehensive Hugging Face model cards for UTDG trained agents."""

    def __init__(self, manager) -> None:
        self.manager = manager

    # ------------------------------------------------------------
    # Build YAML frontmatter with HF metadata
    # ------------------------------------------------------------
    def _build_yaml_frontmatter(self, model_filename: str) -> str:
        """Build the YAML frontmatter with all required HF metadata."""
        cfg = self.manager.cfg
        hf_meta = self.manager.hf.metadata

        # Extract training hyperparameters
        model_cfg = getattr(cfg, "model", {})
        total_timesteps = int(getattr(model_cfg, "total_timesteps", 0))
        learning_rate = getattr(model_cfg, "learning_rate", "3e-4")
        n_steps = getattr(model_cfg, "n_steps", 2048)
        batch_size = getattr(model_cfg, "batch_size", 64)
        n_epochs = getattr(model_cfg, "n_epochs", 10)
        gamma = getattr(model_cfg, "gamma", 0.99)
        gae_lambda = getattr(model_cfg, "gae_lambda", 0.95)
        clip_range = getattr(model_cfg, "clip_range", 0.2)
        ent_coef = getattr(model_cfg, "ent_coef", 0.0)
        vf_coef = getattr(model_cfg, "vf_coef", 0.5)

        # Build comprehensive metadata
        metadata = {
            "utc_timestamp": datetime.datetime.utcnow().isoformat(),
            "env_name": getattr(cfg, "env_name", "UTDGEnv-v0"),
            "model_file": model_filename,
            "total_timesteps": total_timesteps,
            "learning_rate": learning_rate,
            "n_steps": n_steps,
            "batch_size": batch_size,
            "n_epochs": n_epochs,
            "gamma": gamma,
            "gae_lambda": gae_lambda,
            "clip_range": clip_range,
            "ent_coef": ent_coef,
            "vf_coef": vf_coef,
            **hf_meta,
        }

        # Convert Hydra config to JSON for embedding
        hydra_config = OmegaConf.to_container(cfg, resolve=True)
        hydra_json = json.dumps(hydra_config, indent=2)
        hydra_yaml_block = indent_block(hydra_json, 4)

        # Format metadata entries
        metadata_yaml = "\n".join(f"  {k}: {v}" for k, v in metadata.items())

        # Get repo info from hf_meta with defaults
        repo_id = hf_meta.get("repo_id", "chrisjcc/utdg-maskableppo-policy")

        frontmatter = f"""---
language: en
license: mit
library_name: stable-baselines3
tags:
  - reinforcement-learning
  - stable-baselines3
  - sb3-contrib
  - gymnasium
  - maskable-ppo
  - utdg
  - tower-defense
  - game-ai
  - deep-reinforcement-learning
datasets:
  - custom-utdg-env
metrics:
  - episode_reward
  - episode_length
model-index:
  - name: MaskablePPO-UTDG
    results:
      - task:
          type: reinforcement-learning
          name: Tower Defense
        dataset:
          type: custom
          name: UTDG Environment
        metrics:
          - type: episode_reward
            name: Mean Episode Reward
            value: TBD
pipeline_tag: reinforcement-learning
metadata:
{metadata_yaml}
  hydra_config: |
{hydra_yaml_block}
---"""
        return frontmatter, repo_id, model_filename, metadata

    # ------------------------------------------------------------
    # Build Model Details section with training hyperparameters
    # ------------------------------------------------------------
    def _build_model_details_section(self, metadata: dict[str, Any]) -> str:
        """Build the Model Details section with training hyperparameters."""
        return f"""
## Model Details

### Description

This model is a **MaskablePPO** (Proximal Policy Optimization with invalid action masking) agent trained on the UTDG (Untitled Tower Defense Game) environment. The agent learns to strategically place and upgrade towers to defend against waves of enemies.

### Model Architecture

- **Algorithm**: MaskablePPO from [sb3-contrib](https://github.com/Stable-Baselines-Contrib/stable-baselines3-contrib)
- **Policy Network**: MlpPolicy (Multi-layer Perceptron)
- **Framework**: [Stable-Baselines3](https://stable-baselines3.readthedocs.io/)
- **Environment**: Custom UTDG Gymnasium environment with action masking

### Training Hyperparameters

| Parameter | Value |
|-----------|-------|
| Total Timesteps | {metadata.get('total_timesteps', 'N/A'):,} |
| Learning Rate | {metadata.get('learning_rate', '3e-4')} |
| N Steps | {metadata.get('n_steps', 2048)} |
| Batch Size | {metadata.get('batch_size', 64)} |
| N Epochs | {metadata.get('n_epochs', 10)} |
| Gamma (γ) | {metadata.get('gamma', 0.99)} |
| GAE Lambda (λ) | {metadata.get('gae_lambda', 0.95)} |
| Clip Range | {metadata.get('clip_range', 0.2)} |
| Entropy Coefficient | {metadata.get('ent_coef', 0.0)} |
| Value Function Coefficient | {metadata.get('vf_coef', 0.5)} |
"""

    # ------------------------------------------------------------
    # Build Usage section with code examples
    # ------------------------------------------------------------
    def _build_usage_section(self, repo_id: str, model_filename: str) -> str:
        """Build the Usage section with code examples."""
        return f'''
## Usage

### Quick Start

```python
from huggingface_hub import hf_hub_download
from sb3_contrib import MaskablePPO

# Download the model from Hugging Face Hub
model_path = hf_hub_download(
    repo_id="{repo_id}",
    filename="{model_filename}"
)

# Load the trained model
model = MaskablePPO.load(model_path)
```

### Inference with Action Masking

```python
import gymnasium as gym
from sb3_contrib import MaskablePPO

# Assuming you have the UTDG environment installed
# from utdg_env import UTDGEnv

# Load model
model = MaskablePPO.load(model_path)

# Create environment
env = gym.make("UTDGEnv-v0")
obs, info = env.reset()

# Run inference loop
done = False
total_reward = 0

while not done:
    # Get action mask from environment info
    action_masks = info.get("action_mask", None)

    # Predict action with masking
    action, _states = model.predict(
        obs,
        action_masks=action_masks,
        deterministic=True  # Set False for stochastic behavior
    )

    # Step environment
    obs, reward, terminated, truncated, info = env.step(action)
    done = terminated or truncated
    total_reward += reward

print(f"Episode reward: {{total_reward}}")
env.close()
```

### Load Specific Revision

```python
from sb3_contrib import MaskablePPO

# Load from a specific branch/revision
model = MaskablePPO.load(
    "{repo_id}",
    revision="production"  # or "main", specific commit hash, etc.
)
```
'''

    # ------------------------------------------------------------
    # Build Environment section describing the UTDG env
    # ------------------------------------------------------------
    def _build_environment_section(self) -> str:
        """Build the Environment section describing the UTDG env."""
        return """
## Environment

### UTDG (Untitled Tower Defense Game)

The agent is trained on a custom tower defense environment with the following characteristics:

#### Observation Space
- Grid-based game state representation
- Tower positions and types
- Enemy positions and health
- Player resources (gold, lives)
- Wave information

#### Action Space
- Discrete action space with invalid action masking
- Actions include: place tower, upgrade tower, sell tower, skip turn
- Action masking prevents invalid actions (e.g., placing towers on occupied tiles)

#### Reward Structure
- Positive rewards for defeating enemies
- Negative rewards for losing lives
- Bonus rewards for completing waves
- Efficiency bonuses for resource management
"""

    # ------------------------------------------------------------
    # Build Training section with methodology details
    # ------------------------------------------------------------
    def _build_training_section(self) -> str:
        """Build the Training section with methodology details."""
        return """
## Training

### Methodology

The model was trained using the MaskablePPO algorithm, which extends standard PPO with support for invalid action masking. This is crucial for the tower defense domain where many actions are contextually invalid (e.g., placing a tower on an occupied cell).

### Key Features

1. **Action Masking**: Prevents the agent from selecting invalid actions, improving sample efficiency
2. **Curriculum Learning**: Progressive difficulty increase through wave complexity
3. **Reward Shaping**: Carefully designed reward function to encourage strategic play

### Training Infrastructure

- Trained using [Stable-Baselines3](https://stable-baselines3.readthedocs.io/) and [sb3-contrib](https://sb3-contrib.readthedocs.io/)
- Configuration managed via [Hydra](https://hydra.cc/)
- Experiment tracking and model versioning via Hugging Face Hub
"""

    # ------------------------------------------------------------
    # Build Repository Contents section
    # ------------------------------------------------------------
    def _build_files_section(self, model_filename: str) -> str:
        """Build the Repository Contents section."""
        return f"""
## Repository Contents

| File | Description |
|------|-------------|
| `{model_filename}` | Trained MaskablePPO model checkpoint (SB3 format) |
| `README.md` | This model card with full documentation |
| `config.yaml` | Hydra configuration snapshot (if included) |
"""

    # ------------------------------------------------------------
    # Build Citation section
    # ------------------------------------------------------------
    def _build_citation_section(self) -> str:
        """Build the Citation section."""
        return """
## Citation

If you use this model in your research, please cite:

```bibtex
@misc{utdg-maskableppo,
  author = {Chris Cadonic},
  title = {UTDG MaskablePPO Agent},
  year = {2025},
  publisher = {Hugging Face},
  howpublished = {\\url{https://huggingface.co/chrisjcc/utdg-maskableppo-policy}}
}
```

## Acknowledgments

- [Stable-Baselines3](https://github.com/DLR-RM/stable-baselines3) team for the RL framework
- [sb3-contrib](https://github.com/Stable-Baselines-Contrib/stable-baselines3-contrib) for MaskablePPO implementation
- [Hugging Face](https://huggingface.co/) for model hosting infrastructure
"""

    # ------------------------------------------------------------
    # Build Limitations and Intended Use section
    # ------------------------------------------------------------
    def _build_limitations_section(self) -> str:
        """Build the Limitations and Intended Use section."""
        return """
## Limitations and Intended Use

### Intended Use
- Research and experimentation with RL agents in game environments
- Baseline comparisons for tower defense AI development
- Educational purposes for understanding action-masked RL

### Limitations
- Trained on a specific map configuration; may not generalize to significantly different layouts
- Performance may vary with different enemy compositions not seen during training
- Requires the UTDG environment to be installed for inference

### Ethical Considerations
This model is designed for entertainment and research purposes in a game simulation context.
"""

    # ------------------------------------------------------------
    # Write README.md into HF repo directory
    # ------------------------------------------------------------
    def write(self, repo_dir: Path, model_filename: str) -> None:
        """
        Write comprehensive README.md into HF repo directory.

        Args:
            repo_dir: Path to the repository directory
            model_filename: Name of the model file (e.g., 'model_policy.zip')
        """
        # Build all sections
        frontmatter, repo_id, model_filename, metadata = self._build_yaml_frontmatter(
            model_filename
        )

        readme_content = f"""{frontmatter}

# UTDG MaskablePPO Agent

[![Hugging Face](https://img.shields.io/badge/🤗%20Hugging%20Face-Model-yellow)](https://huggingface.co/{repo_id})
[![Stable-Baselines3](https://img.shields.io/badge/SB3-contrib-blue)](https://sb3-contrib.readthedocs.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

> A trained reinforcement learning agent for the Untitled Tower Defense Game using MaskablePPO.
{self._build_model_details_section(metadata)}
{self._build_usage_section(repo_id, model_filename)}
{self._build_environment_section()}
{self._build_training_section()}
{self._build_files_section(model_filename)}
{self._build_limitations_section()}
{self._build_citation_section()}
---

*Generated on {metadata.get('utc_timestamp', datetime.datetime.utcnow().isoformat())} UTC*
"""

        readme = repo_dir / "README.md"
        readme.write_text(readme_content, encoding="utf-8")
