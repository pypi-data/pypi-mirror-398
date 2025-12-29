# utdg_env/configs/config_schema.py
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from hydra.core.config_store import ConfigStore


# ------------------------------------------------------------
# Episode configuration
# ------------------------------------------------------------
@dataclass
class EpisodeConfig:
    max_episode_steps: int = 1000
    truncate_on_life_lost: bool = False
    starting_gold: int = 150
    base_health: int = 10


# ------------------------------------------------------------
# Environment configuration
# ------------------------------------------------------------
@dataclass
class EnvConfig:
    observation_space: Dict[str, Any] = field(default_factory=dict)
    action_space: Dict[str, Any] = field(default_factory=dict)
    episode: EpisodeConfig = field(default_factory=EpisodeConfig)


# ------------------------------------------------------------
# Web / build configuration
# ------------------------------------------------------------
@dataclass
class WebConfig:
    enabled: bool = False
    path: str = "builds/web"
    http_port: int = 8080


# ------------------------------------------------------------
# Launcher configuration (local only)
# ------------------------------------------------------------
@dataclass
class LauncherConfig:
    enabled: bool = False
    # allowed values: "local-dev", "local-train", null
    mode: Optional[str] = None
    auto_port: bool = True
    browser: bool = True
    headless: bool = False


# ------------------------------------------------------------
# Connection configuration (websocket)
# ------------------------------------------------------------
@dataclass
class ConnectionConfig:
    type: str = "websocket"
    role: str = "client"  # 'client' or 'server'
    url: Optional[str] = None
    timeout: float = 60.0
    reconnect_attempts: int = 3


# ------------------------------------------------------------
# Server configuration
# ------------------------------------------------------------
@dataclass
class ServerConfig:
    enabled: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    routes: Dict[str, str] = field(default_factory=lambda: {"ui": "/ws", "godot": "/godot"})


# ------------------------------------------------------------
# Runtime configuration (root)
# ------------------------------------------------------------
@dataclass
class RuntimeConfig:
    mode: str = "native"  # native | web-local | web-hf-demo | web-hf-train
    web: WebConfig = field(default_factory=WebConfig)
    launcher: LauncherConfig = field(default_factory=LauncherConfig)
    connection: ConnectionConfig = field(default_factory=ConnectionConfig)
    server: ServerConfig = field(default_factory=ServerConfig)
    # backward compatibility / convenience fields
    godot_path: Optional[str] = None
    max_episode_steps: int = 1000
    resume: bool = False
    checkpoint_path: str = "checkpoints/model.zip"


# ------------------------------------------------------------
# Model configuration
# ------------------------------------------------------------
@dataclass
class ModelConfig:
    policy: str = "MlpPolicy"
    gamma: float = 0.99
    learning_rate: float = 3e-4
    n_steps: int = 2048
    batch_size: int = 64
    n_epochs: int = 10
    clip_range: float = 0.2
    ent_coef: float = 0.0
    vf_coef: float = 0.5
    max_grad_norm: float = 0.5
    gae_lambda: float = 0.95


# ------------------------------------------------------------
# Curriculum learning configuration
# ------------------------------------------------------------
@dataclass
class CurriculumConfig:
    """Configuration for curriculum learning with adaptive episode horizons.

    Gradually increases max_episode_steps as agent performance improves.
    Updates only occur at episode boundaries.
    """
    enabled: bool = False
    initial_max_steps: Optional[int] = None  # If None, uses env.episode.max_episode_steps
    step_increase: int = 1000  # Amount to increase at each stage
    reward_thresholds: List[float] = field(default_factory=lambda: [-50, -25, 0, 25, 50, 100])
    window_size: int = 20  # Episodes to average for threshold checks
    max_steps_cap: int = 10000  # Maximum episode horizon


# ------------------------------------------------------------
# Training configuration
# ------------------------------------------------------------
@dataclass
class TrainingConfig:
    total_timesteps: int = 1_000_000
    device: str = "auto"
    log_interval: int = 2048
    progress_bar: bool = True
    verbose: int = 1
    curriculum: CurriculumConfig = field(default_factory=CurriculumConfig)


# ------------------------------------------------------------
# Checkpoint configuration
# ------------------------------------------------------------
@dataclass
class CheckpointConfig:
    enabled: bool = False
    save_path: str = "checkpoints"
    save_freq: int = 10000
    save_best_only: bool = True
    keep_last: int = 3
    name_prefix: str = "model_policy"
    save_replay_buffer: bool = False
    save_vecnormalize: bool = False


# ------------------------------------------------------------
# Callbacks configuration
# ------------------------------------------------------------
@dataclass
class WandbCallbackConfig:
    enabled: bool = True
    project: str = "utdg"
    entity: Optional[str] = None
    run_name: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    mode: str = "online"
    save_code: bool = True
    eval_enabled: bool = False


@dataclass
class HfUploadMetadataConfig:
    task: str = "reinforcement-learning"
    algorithm: str = "MaskablePPO"
    game: str = "Untitled Tower Defense Game"


@dataclass
class HfUploadLfsConfig:
    use_lfs: bool = True
    files: List[str] = field(default_factory=lambda: ["*.zip", "*.onnx"])


@dataclass
class HfUploadCallbackConfig:
    enabled: bool = False
    repo_id: Optional[str] = None
    private: bool = False
    repo_type: str = "model"
    token: Optional[str] = None
    metadata: HfUploadMetadataConfig = field(default_factory=HfUploadMetadataConfig)
    push_strategy: str = "final"
    local_model_path: str = ""
    upload_freq: int = 10000
    commit_message: str = "Upload model checkpoint"
    lfs: HfUploadLfsConfig = field(default_factory=HfUploadLfsConfig)


@dataclass
class CallbacksConfig:
    wandb: WandbCallbackConfig = field(default_factory=WandbCallbackConfig)
    hf_upload: HfUploadCallbackConfig = field(default_factory=HfUploadCallbackConfig)


# ------------------------------------------------------------
# Root configuration
# ------------------------------------------------------------
@dataclass
class UTDGConfig:
    runtime: RuntimeConfig = field(default_factory=RuntimeConfig)
    env: EnvConfig = field(default_factory=EnvConfig)
    training: TrainingConfig = field(default_factory=TrainingConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    checkpoint: CheckpointConfig = field(default_factory=CheckpointConfig)
    callbacks: CallbacksConfig = field(default_factory=CallbacksConfig)


# ------------------------------------------------------------
# Register with Hydra
# ------------------------------------------------------------
cs = ConfigStore.instance()

# Register runtime variants as individual entries so Hydra can select them
cs.store(name="native", node=RuntimeConfig, group="runtime")
cs.store(name="web-local", node=RuntimeConfig, group="runtime")
cs.store(name="web-hf-demo", node=RuntimeConfig, group="runtime")
cs.store(name="web-hf-train", node=RuntimeConfig, group="runtime")

# Register other groups (kept from previous)
cs.store(name="base_env", node=EnvConfig, group="env")
cs.store(name="base_training", node=TrainingConfig, group="training")
cs.store(name="base_model", node=ModelConfig, group="model")
cs.store(name="base_checkpoint", node=CheckpointConfig, group="checkpoint")

# Callbacks
cs.store(name="base_wandb", node=WandbCallbackConfig, group="callbacks")
cs.store(name="base_hf_upload", node=HfUploadCallbackConfig, group="callbacks")
cs.store(name="default", node=CallbacksConfig, group="callbacks")

# Root config
cs.store(name="utdg_config", node=UTDGConfig)
