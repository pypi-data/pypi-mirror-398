# utdg_env/env/registry.py

from __future__ import annotations
from typing import Optional, Dict, Any
from gymnasium.envs.registration import register, registry

from omegaconf import DictConfig
from utdg_env.utils.hydra_loader import load_config

from utdg_env.transport.transport_native import NativeTransport
from utdg_env.transport.transport_web import WebTransport
from utdg_env.transport.transport_hf import HFTransport

# Gym environment name
ENV_ID = "UTDGEnv-v0"
ENTRY_POINT = "utdg_env.env.base_env:UntitledTowerDefenseEnv"


def _extract_kwargs(cfg: DictConfig) -> Dict[str, Any]:
    """Convert Hydra config to constructor kwargs."""
    import urllib.parse
    from queue import Queue

    # Extract runtime config
    runtime_cfg = cfg.get("runtime", {})
    connection_cfg = runtime_cfg.get("connection", {})
    server_cfg = runtime_cfg.get("server", {})

    mode = runtime_cfg.get("mode", "native")
    url = connection_cfg.get("url", None)
    timeout = connection_cfg.get("timeout", 30.0)
    reconnect_attempts = connection_cfg.get("reconnect_attempts", 3)

    # Parse URL for host/port (only if URL is provided)
    if url:
        parsed = urllib.parse.urlparse(url)
        host = parsed.hostname or "127.0.0.1"
        port = parsed.port or 9876
    else:
        # Use server config for web modes
        host = server_cfg.get("host", "0.0.0.0")
        port = server_cfg.get("port", 8000)

    target_fps = runtime_cfg.get("target_fps", 15)
    print(f"[registry] Target FPS: {target_fps}")

    print(f"[registry] Detected runtime mode: {mode}")

    if mode in ("web-hf-demo", "web-hf-train"):
        # HuggingFace Space mode with queue-based transport
        # These queues will be replaced by the actual app.py queues
        transport_cls = HFTransport
        transport_kwargs = {
            "to_godot": Queue(),
            "from_godot": Queue(),
            "timeout": timeout,
            "reconnect_attempts": reconnect_attempts,
            "cfg": cfg,
        }
        print(f"[registry] Using HFTransport (FastAPI/queue-based)")

    elif mode.startswith("web"):
        # Web mode: Python acts as WebSocket server
        transport_cls = WebTransport
        transport_kwargs = {
            "host": host,
            "port": port,
            "timeout": timeout,
            "reconnect_attempts": reconnect_attempts,
            "cfg": cfg,
        }
        print(f"[registry] Using WebTransport (server mode on {port})")

    elif mode == "native":
        # Native mode: Python acts as WebSocket client
        transport_cls = NativeTransport
        transport_kwargs = {
            "host": host,
            "port": port,
            "timeout": timeout,
            "reconnect_attempts": reconnect_attempts,
            "cfg": cfg,
        }
        print(f"[registry] Using NativeTransport (client mode to {host}:{port})")

    else:
        raise ValueError(
            f"Unknown runtime mode: '{mode}'. "
            f"Supported modes: native, web-local, web-hf-demo, web-hf-train"
        )

    return {
        "transport_cls": transport_cls,
        "transport_kwargs": transport_kwargs,
        "cfg": cfg,
        "target_fps": target_fps,
    }


def register_env(cfg_overrides: Optional[list[str]] = None) -> None:
    """Register UTDG environment with Gymnasium registry if not already loaded.

    Args:
        cfg_overrides: Optional list of Hydra CLI-style overrides.

    Notes:
        Calling register() twice with the same ID will raise an error,
        so this function safely skips registration if it already exists.
    """

    if ENV_ID in registry:
        # Already registered → do nothing.
        return

    # Load Hydra config
    cfg = load_config(overrides=cfg_overrides)

    # Build kwargs dynamically from Hydra configuration
    kwargs = _extract_kwargs(cfg)

    # Register with Gym
    register(id=ENV_ID, entry_point=ENTRY_POINT, kwargs=kwargs)


def make_env(cfg: Optional[DictConfig] = None):
    """Factory ensuring registration and returning gym.make result."""
    import gymnasium as gym

    if cfg is None:
        register_env()
        return gym.make(ENV_ID)

    # Apply config explicitly
    kwargs = _extract_kwargs(cfg)

    register_env()
    return gym.make(ENV_ID, **kwargs)
