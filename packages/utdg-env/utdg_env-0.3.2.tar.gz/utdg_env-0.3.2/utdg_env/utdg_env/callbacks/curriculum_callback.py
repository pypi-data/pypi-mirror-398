"""Curriculum Learning Callback for Adaptive Episode Horizon.

Gradually increases max_episode_steps as agent performance improves,
allowing faster initial learning with short horizons while eventually
revealing full temporal structure for strategic planning.
"""

import logging
from collections import deque
from typing import Optional

import numpy as np
from stable_baselines3.common.callbacks import BaseCallback

logger = logging.getLogger(__name__)


class CurriculumCallback(BaseCallback):
    """Curriculum learning callback that increases episode horizon based on performance.

    This callback monitors the rolling average episode reward and increases
    max_episode_steps when performance crosses predefined thresholds. Updates
    only occur at episode boundaries to maintain MDP consistency.

    Example:
        Start with 500 steps, increase by 1000 when avg reward crosses -50, -25, 0, 25, etc.
        This lets the agent learn basic tower placement quickly, then gradually see
        longer-term consequences of its strategy.

    Args:
        initial_max_steps: Starting episode horizon (default: from env config)
        step_increase: Amount to increase horizon at each threshold (default: 1000)
        reward_thresholds: List of reward values that trigger increases
        window_size: Number of episodes to average for threshold checks (default: 20)
        max_steps_cap: Maximum episode horizon (prevents unbounded growth)
        verbose: Logging verbosity (0=none, 1=info, 2=debug)
    """

    def __init__(
        self,
        initial_max_steps: Optional[int] = None,
        step_increase: int = 1000,
        reward_thresholds: Optional[list[float]] = None,
        window_size: int = 20,
        max_steps_cap: int = 10000,
        verbose: int = 1,
    ):
        super().__init__(verbose)

        # Curriculum parameters
        self.initial_max_steps = initial_max_steps
        self.step_increase = step_increase
        self.reward_thresholds = reward_thresholds or [-50, -25, 0, 25, 50, 100]
        self.window_size = window_size
        self.max_steps_cap = max_steps_cap

        # State tracking
        self.reward_window = deque(maxlen=window_size)
        self.current_threshold_idx = 0
        self.current_max_steps: Optional[int] = None
        self.episode_rewards = []
        self.episode_count = 0

        # Ensure thresholds are sorted
        self.reward_thresholds = sorted(self.reward_thresholds)

    def _init_callback(self) -> None:
        """Initialize callback after training starts."""
        # Get initial max_steps from environment
        if self.initial_max_steps is None:
            # Access the underlying environment (unwrap vectorized env)
            env = self.training_env.envs[0]
            while hasattr(env, "env"):
                env = env.env
            self.current_max_steps = env.max_episode_steps
            logger.info(f"[Curriculum] Initialized with max_episode_steps={self.current_max_steps} from environment")
        else:
            self.current_max_steps = self.initial_max_steps
            self._update_env_max_steps(self.current_max_steps)
            logger.info(f"[Curriculum] Initialized with max_episode_steps={self.current_max_steps}")

        logger.info(f"[Curriculum] Thresholds: {self.reward_thresholds}")
        logger.info(f"[Curriculum] Step increase: {self.step_increase}, Cap: {self.max_steps_cap}")
        logger.info(f"[Curriculum] Window size: {self.window_size} episodes")

    def _on_step(self) -> bool:
        """Called after each environment step.

        We only check for curriculum updates at episode boundaries,
        so this primarily accumulates episode rewards.

        Returns:
            True to continue training.
        """
        # Check if any episode finished in this step
        for idx, done in enumerate(self.locals.get("dones", [])):
            if done:
                # Get episode reward from info (SB3 includes it in episode info)
                infos = self.locals.get("infos", [])
                if idx < len(infos) and "episode" in infos[idx]:
                    episode_reward = infos[idx]["episode"]["r"]
                    self.reward_window.append(episode_reward)
                    self.episode_count += 1

                    # Check if we should update curriculum
                    self._check_and_update_curriculum()

        return True

    def _check_and_update_curriculum(self) -> None:
        """Check if reward threshold is crossed and update max_episode_steps.

        Only called at episode boundaries to ensure clean updates.
        """
        # Need enough episodes to compute rolling average
        if len(self.reward_window) < self.window_size:
            return

        # Check if we've exhausted all thresholds
        if self.current_threshold_idx >= len(self.reward_thresholds):
            return

        # Compute rolling average reward
        avg_reward = np.mean(self.reward_window)

        # Check if we crossed the next threshold
        next_threshold = self.reward_thresholds[self.current_threshold_idx]
        if avg_reward >= next_threshold:
            # Increase max_episode_steps
            new_max_steps = min(
                self.current_max_steps + self.step_increase,
                self.max_steps_cap
            )

            # Only update if there's an actual increase (respect cap)
            if new_max_steps > self.current_max_steps:
                old_max_steps = self.current_max_steps
                self.current_max_steps = new_max_steps
                self.current_threshold_idx += 1

                # Update environment (at episode boundary)
                self._update_env_max_steps(new_max_steps)

                # Log the curriculum stage transition
                logger.info("")
                logger.info("=" * 60)
                logger.info("[Curriculum] 🎓 Stage %d reached!", self.current_threshold_idx)
                logger.info(f"[Curriculum] Avg reward: {avg_reward:.2f} >= {next_threshold:.2f}")
                logger.info(f"[Curriculum] max_episode_steps: {old_max_steps} → {new_max_steps}")
                logger.info(f"[Curriculum] Episode: {self.episode_count}")
                logger.info("=" * 60)
                logger.info("")

                # Log to WandB if available
                if self.logger:
                    self.logger.record("curriculum/stage", self.current_threshold_idx)
                    self.logger.record("curriculum/max_episode_steps", new_max_steps)
                    self.logger.record("curriculum/threshold_crossed", next_threshold)
                    self.logger.record("curriculum/avg_reward_at_transition", avg_reward)
            elif new_max_steps == self.max_steps_cap:
                # Hit the cap, still advance threshold index
                logger.info(f"[Curriculum] Threshold {next_threshold} crossed but already at cap ({self.max_steps_cap})")
                self.current_threshold_idx += 1

    def _update_env_max_steps(self, new_max_steps: int) -> None:
        """Update max_episode_steps in all environments.

        This is called at episode boundaries only, ensuring that the new
        horizon takes effect for the next episode, not mid-episode.

        Args:
            new_max_steps: New maximum episode length.
        """
        # Update all vectorized environments
        for env in self.training_env.envs:
            # Unwrap to get base environment
            base_env = env
            while hasattr(base_env, "env"):
                base_env = base_env.env

            # Update max_episode_steps
            base_env.max_episode_steps = new_max_steps

            # Send updated config to Godot
            if hasattr(base_env, "transport") and hasattr(base_env.transport, "send_config"):
                try:
                    config_msg = {
                        "max_episode_steps": new_max_steps,
                        "starting_gold": base_env.cfg.env.episode.starting_gold,
                        "base_health": base_env.cfg.env.episode.base_health,
                    }
                    base_env.transport.send_config(config_msg)
                    logger.info(f"[Curriculum] Config update sent to Godot: max_episode_steps={new_max_steps}")
                except Exception as e:
                    logger.warning(f"[Curriculum] Failed to send config update to Godot: {e}")

    def _on_rollout_end(self) -> None:
        """Called at the end of each rollout."""
        # Log current curriculum status
        if self.logger and len(self.reward_window) >= self.window_size:
            avg_reward = np.mean(self.reward_window)
            self.logger.record("curriculum/current_max_steps", self.current_max_steps)
            self.logger.record("curriculum/avg_reward_window", avg_reward)

            # Log next threshold if not exhausted
            if self.current_threshold_idx < len(self.reward_thresholds):
                next_threshold = self.reward_thresholds[self.current_threshold_idx]
                self.logger.record("curriculum/next_threshold", next_threshold)
                self.logger.record("curriculum/distance_to_threshold", next_threshold - avg_reward)
