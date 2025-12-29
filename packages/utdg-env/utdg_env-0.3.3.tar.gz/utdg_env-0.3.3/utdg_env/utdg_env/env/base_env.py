"""Gymnasium environment for Untitled Tower Defense Game (UTDG).

This module provides a Gymnasium-compatible environment that controls a Godot-based
tower defense game through a transport abstraction layer. The environment supports
multiple runtime modes (native, web, HuggingFace backend) and provides action masking
for valid tower placement locations.
"""

from __future__ import annotations

import time
import logging
from typing import Any, Dict, Optional, Tuple

import gymnasium as gym
import numpy as np
from gymnasium import spaces
from omegaconf import DictConfig

from utdg_env.transport.transport_base import (
    Transport,
    TransportDisconnected,
    TransportError,
    TransportTimeout,
)

logger = logging.getLogger(__name__)


class UntitledTowerDefenseEnv(gym.Env):
    """Gymnasium environment controlling a Godot Tower Defense game via transport.

    This environment is transport-agnostic and does not know whether the simulator
    is native or web-based. It only interacts through the synchronous Transport API:
        - transport.connect()
        - obs = transport.reset()
        - obs = transport.step(action)
        - transport.close()

    Action masking is provided through get_action_mask(), and the environment
    exposes a discrete action space derived from the dynamic number of available
    tower placement slots.

    Attributes:
        metadata: Environment metadata including render modes and FPS.
        observation_space: Dict space containing game state observations.
        action_space: Discrete action space (dynamically sized based on slots).
        MAX_TOWERS: Maximum number of towers to track in observations.
        MAX_ENEMIES: Maximum number of enemies to track in observations.
        MAX_VALID_ACTIONS: Maximum number of valid actions (slots + NOOP).
    """

    metadata = {"render_modes": ["none", "human"], "render_fps": 30}

    def __init__(
        self,
        transport: Optional[Transport] = None,
        transport_cls: Optional[type[Transport]] = None,
        transport_kwargs: Optional[Dict[str, Any]] = None,
        cfg: Optional[DictConfig] = None,
        render_mode: Optional[str] = None,
        target_fps: int = 15,
        **kwargs: Any,
    ) -> None:
        """Initialize the UTDG environment.

        Args:
            transport: Pre-instantiated Transport object (optional).
            transport_cls: Transport class to instantiate if transport is None.
            transport_kwargs: Keyword arguments for transport_cls instantiation.
            cfg: Hydra DictConfig containing runtime parameters.
            render_mode: Rendering mode hint ('none' or 'human').
            **kwargs: Additional arguments passed by Gym or wrappers.

        Raises:
            ValueError: If neither transport nor transport_cls is provided.
        """
        super().__init__()

        # =====================================================================
        # Transport Setup
        # =====================================================================
        if transport is not None:
            self.transport = transport
        elif transport_cls is not None:
            kwargs_for_transport = transport_kwargs or {}
            self.transport = transport_cls(**kwargs_for_transport)
        else:
            raise ValueError("Must provide either 'transport' or 'transport_cls'.")

        self.cfg = cfg or {}
        self.render_mode = render_mode

        # =====================================================================
        # Runtime Parameters
        # =====================================================================
        self.max_episode_steps: int = int(self.cfg.env.episode.max_episode_steps)

        self.episode_reward = 0

        # =====================================================================
        # Internal State
        # =====================================================================
        self._step_counter: int = 0
        self._num_slots: Optional[int] = None
        self._last_action_mask: Optional[np.ndarray] = None
        self._last_action_mask: Optional[np.ndarray] = None
        self._last_processed_obs: Optional[Dict[str, np.ndarray]] = None

        # =====================================================================
        # Rate Limiting
        # =====================================================================
        self.target_fps = target_fps
        self._target_step_duration = 1.0 / float(self.target_fps) if self.target_fps > 0 else 0.0
        self._last_step_time = 0.0

        # =====================================================================
        # Constants
        # =====================================================================
        self.MAX_TOWERS: int = 25
        self.MAX_ENEMIES: int = 50
        self.MAX_VALID_ACTIONS: int = (
            cfg.runtime.get("max_slots", 115) + 1
        )  # +1 for NOOP

        # =====================================================================
        # Action Space (placeholder, dynamically set after first reset)
        # =====================================================================
        self.action_space = spaces.Discrete(116)

        # =====================================================================
        # Observation Space (fixed structure)
        # =====================================================================
        self.observation_space = spaces.Dict(
            {
                "gold": spaces.Box(low=0, high=10_000, shape=(1,), dtype=np.int32),
                "enemy_count": spaces.Box(low=0, high=500, shape=(1,), dtype=np.int32),
                "tower_count": spaces.Box(low=0, high=200, shape=(1,), dtype=np.int32),
                "base_health": spaces.Box(low=0, high=100, shape=(1,), dtype=np.int32),
                "num_slots": spaces.Box(low=1, high=200, shape=(1,), dtype=np.int32),
                "valid_actions": spaces.Box(
                    low=0, high=1, shape=(self.MAX_VALID_ACTIONS,), dtype=np.int32
                ),
                "tower_positions": spaces.Box(
                    low=-2048, high=2048, shape=(self.MAX_TOWERS, 2), dtype=np.int32
                ),
                "enemy_positions": spaces.Box(
                    low=-2048, high=2048, shape=(self.MAX_ENEMIES, 2), dtype=np.int32
                ),
            }
        )

        # =====================================================================
        # Transport Initialization
        # =====================================================================
        self._initialize_transport()

    def _initialize_transport(self) -> None:
        """Initialize transport layer based on runtime mode.

        Connects the transport layer according to the configured mode:
        - hf_backend: Queue-based transport managed by FastAPI
        - web: WebSocket server waiting for client connection
        - native: Client connection to running Godot server
        """
        runtime_cfg = self.cfg.get("runtime", {})
        mode = runtime_cfg.get("mode", "native")

        logger.info("Initializing environment in %s mode", mode)

        if mode == "hf_backend":
            logger.info("HF backend mode - transport managed by FastAPI")
            self.transport.connect()

        elif mode.startswith("web"):
            logger.info("Starting WebSocket server...")
            self.transport.connect()
            logger.info("WebSocket server started, waiting for Godot client")

        else:  # native mode
            logger.info("Connecting as client to game server...")
            self.transport.connect()
            logger.info("Connected to game server")

    # =====================================================================
    #                           Gym API
    # =====================================================================

    def reset(
        self, seed: Optional[int] = None, options: Optional[Dict[str, Any]] = None
    ) -> Tuple[Dict[str, np.ndarray], Dict[str, Any]]:
        """Reset the environment and simulator to initial state.

        Args:
            seed: Random seed for reproducibility.
            options: Additional reset options (unused).

        Returns:
            Tuple containing:
                - observation: Initial observation with normalized fields.
                - info: Dictionary containing initial events.
        """
        super().reset(seed=seed)
        self._step_counter = 0
        self.episode_reward = 0
        self.episode_components = {
            "kills": 0.0,
            "damage": 0.0,
            "wave": 0.0,
            "towers_built": 0.0,  # Track tower building rewards
        }

        # Track tower count for computing towers_built delta
        self._previous_tower_count = 0

        logger.debug("Resetting environment (seed=%s)", seed)

        # Reset transport - returns full response data
        # Retry loop for robustness against page refreshes
        while True:
            try:
                response_data = self.transport.reset()
                break # Success!
            except TransportError as e:
                # Check if it's a reconnection error (by name, to avoid circular import if possible,
                # or just check exception type if we import it)
                if e.__class__.__name__ == "ReconnectionError" or "reconnection" in str(e).lower():
                    logger.warning("Client reconnected during reset. Retrying reset...")
                    # Small backoff to allow client to stabilize?
                    time.sleep(0.5)
                    continue
                raise e # Re-raise real errors

        # Extract observation from response data
        obs_dict = response_data.get("observation", {})

        # Extract metadata from response data
        info_data = response_data.get("info", {})
        events = info_data.get("events", {})

        # Update internal state from observation and fix shapes
        self._process_observation(obs_dict)

        # Store processed observation for get_action_mask()
        self._last_processed_obs = obs_dict

        # Remove non-observation fields to match observation_space
        clean_obs = self._extract_observation(obs_dict)

        # Build info dict with metadata
        info = {"events": events}

        logger.debug(
            "Reset complete: base_health=%d, gold=%d",
            clean_obs.get("base_health", [0])[0],
            clean_obs.get("gold", [0])[0],
        )

        return clean_obs, info

    def step(
        self, action: int
    ) -> Tuple[Dict[str, np.ndarray], float, bool, bool, Dict[str, Any]]:
        """Execute one step with the given action.

        Args:
            action: Index of the tower slot to build/upgrade (or NOOP).

        Returns:
            Tuple containing:
                - observation: Current observation with normalized fields.
                - reward: Scalar reward for this step.
                - terminated: Whether episode ended naturally (win/loss).
                - truncated: Whether episode was truncated (max steps).
                - info: Dictionary with events and terminal reason.
        """
        # =====================================================================
        # Rate Limiting (Throttle)
        # =====================================================================
        if self._target_step_duration > 0 and self._last_step_time > 0:
            elapsed = time.time() - self._last_step_time
            if elapsed < self._target_step_duration:
                sleep_time = self._target_step_duration - elapsed
                time.sleep(sleep_time)

        self._last_step_time = time.time()

        self._step_counter += 1

        # =====================================================================
        # Send Action to Godot
        # =====================================================================
        try:
            response_data = self.transport.step(action)
            # response_data = {
            #     "observation": {...},
            #     "reward": 0.0,
            #     "done": True,
            #     "truncated": False,
            #     "info": {"events": {...}}
            # }

            # Extract observation dict
            obs_dict = response_data.get("observation", {})

            # Extract metadata from response data
            info_data = response_data.get("info", {})
            events = info_data.get("events", {})

            # Print debug info from Godot
            debug_info = info_data.get("debug", {})
            if debug_info:
                logger.debug(f"[GODOT DEBUG] step={debug_info.get('step_count')}, "
                    f"health={debug_info.get('base_current_health')}, "
                    f"is_dead={debug_info.get('base_is_dead')}, "
                    f"enemies={debug_info.get('enemy_count')}, "
                    f"waves_done={debug_info.get('waves_done')}, "
                    f"max_steps={debug_info.get('max_steps')}")
        except (TransportError, TransportDisconnected, TransportTimeout) as e:
            logger.error("Transport error during step: %s", e)
            logger.warning("Terminating episode to trigger reset and reconnection")
            # Create dummy response data
            response_data = {
                "observation": self._get_dummy_observation(),
                "reward": 0.0,
                "done": True,
                "terminated": True,
                "truncated": False,
                "info": {}
            }
            obs_dict = response_data["observation"]

        # =====================================================================
        # Process Observation
        # =====================================================================
        self._process_observation(obs_dict)
        self._last_processed_obs = obs_dict

        # =====================================================================
        # Extract Metadata from Response Data (Not Observation)
        # =====================================================================
        # Terminal flags from response data level
        terminated = response_data.get("done", False) or response_data.get("terminated", False)
        truncated = response_data.get("truncated", False)

        # Python-side truncation check (independent of Godot)
        # This ensures we respect Python's max_episode_steps even if config protocol fails
        if not terminated and not truncated and self._step_counter >= self.max_episode_steps:
            truncated = True
            logger.info("Episode truncated by Python at %d steps (max_episode_steps=%d)",
                       self._step_counter, self.max_episode_steps)

        # Events from info dict
        info_data = response_data.get("info", {})
        events = info_data.get("events", {})

        # =====================================================================
        # Calculate Reward from Events
        # =====================================================================
        reward = 0.0

        # Compute towers_built from observation delta (tower_count change)
        current_tower_count = obs_dict.get("tower_count", 0)
        if isinstance(current_tower_count, (list, np.ndarray)):
            current_tower_count = int(current_tower_count[0])
        else:
            current_tower_count = int(current_tower_count)

        towers_built_this_step = max(0, current_tower_count - self._previous_tower_count)
        self._previous_tower_count = current_tower_count

        # Reward components for tracking
        r_kills = events.get("kills", 0) * 15.0 * 0.067  # +1.0 per kill (Experiment 1: reduced from +1.5)
        r_damage = events.get("base_damage", 0) * 10.0   # -10 per base damage (proven baseline)
        r_wave = 50.0 if events.get("wave_cleared", False) else 0.0  # +50 per wave cleared
        r_tower_built = towers_built_this_step * 5.0  # +5 per tower placed (computed from observation delta)

        reward += r_kills
        reward -= r_damage
        reward += r_wave
        reward += r_tower_built

        self.episode_components["kills"] += r_kills
        self.episode_components["damage"] += -r_damage
        self.episode_components["wave"] += r_wave
        self.episode_components["towers_built"] += r_tower_built

        self.episode_reward += reward

        # =====================================================================
        # Remove Non-Observation Fields
        # =====================================================================
        clean_obs = self._extract_observation(obs_dict)

        # =====================================================================
        # Build Info Dict
        # =====================================================================
        info: Dict[str, Any] = {
            "events": events,
            "reward_components": {
                "kills": r_kills,
                "damage": -r_damage,
                "wave": r_wave,
                "towers_built": r_tower_built,
            }
        }

        # Add episode statistics to info when episode ends
        if terminated or truncated:
            reason = info_data.get("reason", "unknown")
            info["reason"] = reason

            info["episode"] = {
                "r": self.episode_reward,  # Total episode reward
                "l": self._step_counter,   # Episode length in steps
            }

            # Add accumulated components to info for WandB logging
            info["episode_components"] = self.episode_components.copy()
            # Calculate average reward
            avg_reward = self.episode_reward / self._step_counter if self._step_counter > 0 else 0.0

            # Log for debugging
            logger.info(
                f"Episode ended: {'terminated' if terminated else 'truncated'} "
                f"(steps={self._step_counter}, reward={self.episode_reward:.2f}, "
                f"avg_reward={avg_reward:.4f})"
            )

        return clean_obs, reward, terminated, truncated, info

    # =====================================================================
    #                         Helper Methods
    # =====================================================================

    def _extract_observation(self, obs_dict: Dict[str, Any]) -> Dict[str, np.ndarray]:
        """Extract only observation space fields from full observation dict.

        Removes metadata fields (done, truncated, events, reward, reason) that
        are not part of the observation_space to ensure Gymnasium validation passes.

        Args:
            obs_dict: Full observation dictionary including metadata.

        Returns:
            Dictionary containing only observation_space fields.
        """
        # Define fields that should be in observation
        obs_keys = [
            "gold",
            "enemy_count",
            "tower_count",
            "base_health",
            "num_slots",
            "valid_actions",
            "tower_positions",
            "enemy_positions",
        ]

        # Extract only observation fields
        clean_obs = {key: obs_dict[key] for key in obs_keys if key in obs_dict}

        return clean_obs

    def _get_dummy_observation(self) -> Dict[str, Any]:
        """Create a dummy observation with default values.

        Used when transport errors occur to provide a valid observation
        that signals episode termination.

        Returns:
            Dictionary containing dummy observation with all fields zeroed
            and terminal flags set to True.
        """
        obs = {
            "gold": 0,
            "enemy_count": 0,
            "tower_count": 0,
            "base_health": 0,
            "num_slots": 1,
            "valid_actions": np.zeros(self.MAX_VALID_ACTIONS, dtype=np.int32),
            "tower_positions": [],
            "enemy_positions": [],
            "reward": 0.0,
            "done": True,
            "terminated": True,
        }
        # Ensure valid_actions has at least one valid action (NOOP)
        obs["valid_actions"][-1] = 1
        return obs

    # =====================================================================
    #                    Observation Processing
    # =====================================================================

    def _process_observation(self, obs: Dict[str, Any]) -> None:
        """Normalize observation values to match observation_space specification.

        This method modifies the observation dict in-place to ensure all fields
        have the correct shape and dtype as defined in observation_space.

        Args:
            obs: Raw observation dictionary from transport layer.

        Raises:
            ValueError: If observation fields have invalid shapes or values.
        """
        # =====================================================================
        # 1. Handle Dynamic num_slots + Valid Action Mask
        # =====================================================================
        if "num_slots" in obs:
            raw = obs["num_slots"]

            if isinstance(raw, (list, np.ndarray)):
                num_slots = int(raw[0])
            else:
                num_slots = int(raw)

            if num_slots + 1 > self.MAX_VALID_ACTIONS:
                raise ValueError(
                    f"num_slots={num_slots} exceeds MAX_VALID_ACTIONS={self.MAX_VALID_ACTIONS}"
                )

            if num_slots != self._num_slots:
                self._num_slots = num_slots
                self.action_space = spaces.Discrete(num_slots + 1)
                logger.debug("Updated action space to %d actions", num_slots + 1)

            # Check if valid_actions is already provided (e.g. from Godot logic)
            if "valid_actions" in obs:
                 # Ensure it matches the expected size (pad/clip if necessary)
                 raw_mask = obs["valid_actions"]
                 mask = np.zeros(self.MAX_VALID_ACTIONS, dtype=np.int32)

                 # Convert to numpy and clip length
                 # Note: raw_mask could be list or array
                 n = min(len(raw_mask), self.MAX_VALID_ACTIONS)
                 mask[:n] = np.array(raw_mask)[:n]

                 # Ensure NOOP is always valid
                 if num_slots < self.MAX_VALID_ACTIONS:
                    mask[num_slots] = 1 # NOOP index for this dynamic size

                 obs["valid_actions"] = mask
            else:
                # Fallback: Make all slots valid
                mask = np.zeros(self.MAX_VALID_ACTIONS, dtype=np.int32)
                mask[: num_slots + 1] = 1
                obs["valid_actions"] = mask

        # =====================================================================
        # 2. Normalize Scalar Fields to Shape (1,)
        # =====================================================================
        for key in [
            "gold",
            "enemy_count",
            "tower_count",
            "base_health",
            "num_slots",
        ]:
            if key not in obs:
                continue

            raw = obs[key]

            # Handle None values
            if raw is None:
                logger.warning("%s is None, using default value 0", key)
                obs[key] = np.array([0], dtype=np.int32)
                continue

            if isinstance(raw, np.ndarray):
                if raw.ndim == 0:
                    obs[key] = raw.reshape((1,))
                else:
                    obs[key] = np.array([raw[0]], dtype=np.int32)

            elif isinstance(raw, list):
                obs[key] = np.array([raw[0]], dtype=np.int32)

            else:
                obs[key] = np.array([int(raw)], dtype=np.int32)

        # =====================================================================
        # 3. Normalize enemy_positions to Shape (MAX_ENEMIES, 2)
        # =====================================================================
        if "enemy_positions" in obs:
            raw = obs["enemy_positions"]
            arr = np.array(raw, dtype=np.int32)

            # Handle empty array case
            if arr.size == 0:
                arr = np.zeros((0, 2), dtype=np.int32)

            if arr.ndim != 2 or arr.shape[1] != 2:
                raise ValueError(f"enemy_positions must be N x 2, got shape {arr.shape}")

            # Clip and pad to fixed length
            n = min(len(arr), self.MAX_ENEMIES)
            padded = np.zeros((self.MAX_ENEMIES, 2), dtype=np.int32)
            padded[:n] = arr[:n]

            obs["enemy_positions"] = padded

        # =====================================================================
        # 4. Normalize tower_positions to Shape (MAX_TOWERS, 2)
        # =====================================================================
        if "tower_positions" in obs:
            raw = obs["tower_positions"]
            arr = np.array(raw, dtype=np.int32)

            # Handle empty array case
            if arr.size == 0:
                arr = np.zeros((0, 2), dtype=np.int32)

            if arr.ndim != 2 or arr.shape[1] != 2:
                raise ValueError(f"tower_positions must be N x 2, got shape {arr.shape}")

            # Clip and pad to fixed length
            n = min(len(arr), self.MAX_TOWERS)
            padded = np.zeros((self.MAX_TOWERS, 2), dtype=np.int32)
            padded[:n] = arr[:n]

            obs["tower_positions"] = padded

    # =====================================================================
    #                       Action Masking
    # =====================================================================

    def get_action_mask(self) -> np.ndarray:
        """Return boolean action mask for SB3 ActionMasker wrapper.

        This method is called by the ActionMasker wrapper to determine which
        actions are valid at the current state. It uses the 'valid_actions'
        field from the most recent observation returned by Godot.

        Returns:
            Boolean array of shape (num_slots + 1,) where True indicates
            a valid action and False indicates invalid. The last element
            corresponds to the NOOP action (always valid).
        """
        if self._num_slots is None:
            # Environment not initialized yet, allow single action
            return np.ones(1, dtype=bool)

        # Initialize mask with all actions invalid
        mask = np.zeros(self._num_slots + 1, dtype=bool)

        # Get valid_actions from last processed observation
        if self._last_processed_obs is not None:
            valid_actions = self._last_processed_obs.get("valid_actions", None)

            if valid_actions is not None and len(valid_actions) > 0:
                # valid_actions is binary array from Godot (1=valid, 0=invalid)
                # Convert to boolean and apply to mask
                mask_len = min(len(mask), len(valid_actions))
                mask[:mask_len] = valid_actions[:mask_len].astype(bool)

                # NOOP action (last index) is always valid
                mask[-1] = True

                return mask

        # Fallback: allow all actions if no valid_actions data available
        logger.debug("No valid_actions data, allowing all actions")
        mask[:] = True
        return mask

    # =====================================================================
    #                         Helper Methods
    # =====================================================================

    def _get_dummy_observation(self) -> Dict[str, Any]:
        """Create a dummy observation with default values.

        Used when transport errors occur to provide a valid observation
        that signals episode termination.

        Returns:
            Dictionary containing dummy observation with all fields zeroed
            and terminal flags set to True.
        """
        obs = {
            "gold": 0,
            "enemy_count": 0,
            "tower_count": 0,
            "base_health": 0,
            "num_slots": 1,
            "valid_actions": np.zeros(self.MAX_VALID_ACTIONS, dtype=np.int32),
            "tower_positions": [],
            "enemy_positions": [],
            "reward": 0.0,
            "done": True,
            "terminated": True,
        }
        # Ensure valid_actions has at least one valid action (NOOP)
        obs["valid_actions"][-1] = 1
        return obs

    def wait_for_human_action(self) -> Optional[int]:
        """Wait for a human action from the connected client.

        Returns:
            Slot index of the human action, or None if connection lost.
        """
        logger.info("Waiting for human action...")
        return self.transport.get_human_action()

    # =====================================================================
    #                           Cleanup
    # =====================================================================

    def close(self) -> None:
        """Gracefully close the transport layer and release resources."""
        try:
            self.transport.close()
            logger.info("Environment closed successfully")
        except Exception as e:
            logger.warning("Error closing transport: %s", e)
