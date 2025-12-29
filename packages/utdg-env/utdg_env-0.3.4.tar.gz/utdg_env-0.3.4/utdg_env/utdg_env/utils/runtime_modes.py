# utdg_env/utdg_env/utils/runtime_modes.py
from enum import Enum


class RuntimeMode(str, Enum):
    RUNTIME_NATIVE = "RUNTIME_NATIVE"          # Local desktop Godot, can be auto-launched
    RUNTIME_ATTACH = "RUNTIME_ATTACH"          # Attach to already-running Godot
    RUNTIME_HEADLESS = "RUNTIME_HEADLESS"      # Headless desktop Godot (no window)
    RUNTIME_WEB = "RUNTIME_WEB"                # Local WebGL build in browser
    RUNTIME_HF_BACKEND = "RUNTIME_HF_BACKEND"  # HF Spaces backend (browser client)
    RUNTIME_HUMAN = "RUNTIME_HUMAN"            # Human play w/ AI assist
