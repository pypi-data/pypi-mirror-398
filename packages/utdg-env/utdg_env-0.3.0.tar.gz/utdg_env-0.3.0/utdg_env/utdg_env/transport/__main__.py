"""
CLI entry point for testing transport connectivity.

Run examples:

    python -m utdg_env.transport check
    python -m utdg_env.transport check mode=native
    python -m utdg_env.transport check mode=web

This tool verifies:

    ✓ WebSocket connection established
    ✓ Reset → response received
    ✓ Step → response received
    ✓ Round-trip protocol integrity

Useful before running PPO training or HF deployment.
"""

from __future__ import annotations

import argparse
import sys
import time

from omegaconf import OmegaConf

from utdg_env.utils.hydra_loader import load_config
from utdg_env.transport.transport_native import NativeTransport
from utdg_env.transport.transport_web import WebTransport
from utdg_env.transport.transport_base import TransportError, TransportTimeout


def _select_transport(cfg) -> object:
    """Return a configured transport instance based on cfg.mode."""
    mode = cfg.get("mode", "native")

    env_cfg = cfg.get("env", {})
    host = env_cfg.get("host", "127.0.0.1")
    port = env_cfg.get("port", 9876)
    timeout = env_cfg.get("timeout", 30)
    reconnect_attempts = env_cfg.get("max_reconnect_attempts", 3)

    print(f"[validator] Runtime mode: {mode}")

    if mode == "native":
        return NativeTransport(
            host=host,
            port=port,
            timeout=timeout,
            reconnect_attempts=reconnect_attempts,
        )

    if mode == "web":
        return WebTransport(
            host=host,
            port=port,
            timeout=timeout,
            reconnect_attempts=reconnect_attempts,
            max_connections=env_cfg.get("max_connections", 1),
        )

    raise ValueError(f"Unknown mode: {mode}")


def run_connectivity_check(cfg) -> int:
    """Perform a full simulation roundtrip using only the transport layer."""
    print("\n=== UTDG Transport Diagnostic ===\n")
    print(OmegaConf.to_yaml(cfg))

    transport = _select_transport(cfg)

    try:
        print("\n[validator] Connecting...")
        transport.connect()
        print("[validator] ✓ Connected.")

        print("\n[validator] Sending RESET...")
        obs_reset = transport.reset()
        print("[validator] ✓ RESET acknowledged.")
        print(f"[validator] Reset observation keys: {list(obs_reset.keys())}")

        time.sleep(0.25)

        print("\n[validator] Sending STEP(action=-1)...")
        obs_step = transport.step(-1)
        print("[validator] ✓ STEP acknowledged.")
        print(f"[validator] Step observation keys: {list(obs_step.keys())}")

        print("\n[validator] SUCCESS — roundtrip confirmed.\n")
        return 0

    except TransportTimeout:
        print("\n[validator] ERROR: Timeout — Godot did not respond in expected time.\n")
        return 2

    except TransportError as e:
        print(f"\n[validator] ERROR: Transport failure → {e}\n")
        return 3

    except Exception as e:
        print(f"\n[validator] Unexpected error: {e}\n")
        return 10

    finally:
        print("[validator] Closing transport...")
        try:
            transport.close()
        except Exception:
            pass
        print("[validator] Terminated cleanly.\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="UTDG WebSocket transport diagnostic tool.")
    parser.add_argument("action", nargs="?", default="check", help="Supported: check")
    parser.add_argument("mode", nargs="?", default=None, help="Override e.g. mode=native or mode=web")

    args = parser.parse_args()

    if args.action != "check":
        print(f"Unknown command: {args.action}")
        sys.exit(1)

    overrides = []
    if args.mode:
        overrides.append(args.mode)

    cfg = load_config(config_name="default", overrides=overrides)

    exit_code = run_connectivity_check(cfg)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
