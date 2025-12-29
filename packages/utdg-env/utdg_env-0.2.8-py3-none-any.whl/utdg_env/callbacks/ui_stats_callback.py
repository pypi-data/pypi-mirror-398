"""
Minimal UI Stats Callback for SB3 Training.

Bridges SB3 training metrics to FastAPI state object for WebSocket UI updates.
"""

import logging
import time
from typing import Callable, Optional
from collections import deque

import numpy as np
from stable_baselines3.common.callbacks import BaseCallback

logger = logging.getLogger(__name__)


class UIStatsCallback(BaseCallback):
    """
    Minimal callback that updates a state object with training metrics.
    
    Reads from:
    - self.num_timesteps: Current total timesteps
    - self.model.ep_info_buffer: Episode rewards/lengths (requires Monitor wrapper)
    
    Updates the provided state object which is read by WebSocket endpoint.
    
    IMPORTANT: Requires environment wrapped with Monitor for ep_info_buffer to be populated.
    """
    
    def __init__(
        self,
        training_state=None,  # FastAPI TrainingState dataclass/object (for compatibility)
        state=None,  # Alternative parameter name
        total_timesteps: Optional[int] = None,
        update_freq: int = 100,
        verbose: int = 0,
    ):
        super().__init__(verbose)
        # Support both parameter names for backward compatibility
        self.training_state = training_state or state
        if self.training_state is None:
            raise ValueError("Either training_state or state parameter must be provided")

        # For code clarity, also expose as state
        self.state = self.training_state

        self.total_timesteps = total_timesteps or getattr(self.state, 'total_timesteps', 100000)
        self.update_freq = update_freq

        # Internal tracking
        self._start_time: Optional[float] = None
        self._last_time: float = 0
        self._last_timestep: int = 0
        self._ep_rewards: deque = deque(maxlen=50)  # Rolling window for 250 total episodes
        self._ep_lengths: deque = deque(maxlen=50)
    
    def _on_training_start(self) -> None:
        """Called when training starts."""
        self._start_time = time.time()
        self._last_time = self._start_time
        
        self.state.status = "training"
        self.state.training_started = True
        self.state.total_timesteps = self.total_timesteps
        
        logger.info("[UIStatsCallback] Training started")
    
    def _on_step(self) -> bool:
        """Called after each environment step."""
        # Always update timestep
        self.state.current_timestep = self.num_timesteps

        # Check for new completed episodes via 'infos'
        # This is more robust than tracking ep_info_buffer indices
        dones = self.locals.get("dones", [False])
        infos = self.locals.get("infos", [{}])

        for i, done in enumerate(dones):
            if done:
                info = infos[i]
                if "episode" in info:
                    ep_info = info["episode"]
                    reward = float(ep_info["r"])
                    length = int(ep_info["l"])

                    # Update rolling buffers
                    self._ep_rewards.append(reward)
                    self._ep_lengths.append(length)

                    # Update state
                    self.state.episodes_completed += 1
                    self.state.current_episode_reward = reward

                    # Update history for charts
                    if hasattr(self.state, 'reward_history'):
                        self.state.reward_history.append(reward)
                        # Keep history bounded
                        if len(self.state.reward_history) > 1000:
                            self.state.reward_history = self.state.reward_history[-500:]

                    if hasattr(self.state, 'length_history'):
                        self.state.length_history.append(length)
                        # Keep history bounded
                        if len(self.state.length_history) > 1000:
                            self.state.length_history = self.state.length_history[-500:]

                    # Update rolling averages immediately
                    if len(self._ep_rewards) > 0:
                        self.state.mean_episode_reward = float(np.mean(self._ep_rewards))
                        self.state.mean_episode_length = float(np.mean(self._ep_lengths))

                        # Track best mean reward
                        if self.state.mean_episode_reward > getattr(self.state, 'best_mean_reward', float('-inf')):
                            self.state.best_mean_reward = self.state.mean_episode_reward

        # Periodic performance metrics update
        if self.num_timesteps % self.update_freq == 0:
            self._update_performance()

        return True
    
    def _update_performance(self) -> None:
        """Update steps/sec and ETA."""
        now = time.time()
        dt = now - self._last_time
        ds = self.num_timesteps - self._last_timestep
        
        if dt > 0:
            self.state.steps_per_second = ds / dt
        
        remaining = self.total_timesteps - self.num_timesteps
        if self.state.steps_per_second > 0:
            self.state.eta_seconds = remaining / self.state.steps_per_second
        
        self._last_time = now
        self._last_timestep = self.num_timesteps
    
    def _on_training_end(self) -> None:
        """Called when training ends."""
        self.state.status = "complete"
        self.state.training_complete = True
        self._update_performance()
        
        logger.info(
            f"[UIStatsCallback] Training complete: "
            f"{self.state.episodes_completed} episodes, "
            f"mean_reward={self.state.mean_episode_reward:.2f}"
        )


class LoggerStatsCallback(BaseCallback):
    """
    Alternative callback that reads from SB3's logger.
    
    NOTE: This only updates after full rollouts (every n_steps), not per-step.
    Use UIStatsCallback for more frequent updates.
    """
    
    def __init__(self, state, verbose: int = 0):
        super().__init__(verbose)
        self.state = state
    
    def _on_step(self) -> bool:
        self.state.current_timestep = self.num_timesteps
        
        # Try to get logger values (only populated after rollout)
        if hasattr(self, 'logger') and self.logger is not None:
            try:
                logger_vals = self.logger.name_to_value
                
                if "rollout/ep_rew_mean" in logger_vals:
                    self.state.mean_episode_reward = logger_vals["rollout/ep_rew_mean"]
                
                if "rollout/ep_len_mean" in logger_vals:
                    self.state.mean_episode_length = logger_vals["rollout/ep_len_mean"]
                
                if "time/fps" in logger_vals:
                    self.state.steps_per_second = logger_vals["time/fps"]
                    
            except Exception:
                pass
        
        return True
