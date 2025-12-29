# utdg_env/callbacks/wandb_callback.py
import numpy as np
import wandb
from stable_baselines3.common.callbacks import BaseCallback, EvalCallback


class WandbMetricsCallback(BaseCallback):
    """
    Callback that directly logs SB3 metrics to W&B.

    This callback computes rollout/* metrics directly from ep_info_buffer (the same source
    SB3 uses) and reads train/* metrics from the logger, bypassing unreliable TensorBoard sync.
    """

    def __init__(self, verbose: int = 0):
        super().__init__(verbose)
        self._last_log_step = 0

    def _on_step(self) -> bool:
        """Called after each step. Metrics are logged in _on_rollout_end()."""
        return True

    def _on_rollout_end(self) -> None:
        """
        Log all metrics after rollout collection.
        Computes rollout/* from ep_info_buffer and reads train/* from logger.
        """
        metrics = {}

        # 1. Compute rollout metrics directly from ep_info_buffer (same as SB3 does internally)
        if hasattr(self.model, 'ep_info_buffer') and len(self.model.ep_info_buffer) > 0:
            ep_rewards = [ep_info["r"] for ep_info in self.model.ep_info_buffer]
            ep_lengths = [ep_info["l"] for ep_info in self.model.ep_info_buffer]

            if len(ep_rewards) > 0:
                metrics["rollout/ep_rew_mean"] = float(np.mean(ep_rewards))
                metrics["rollout/ep_len_mean"] = float(np.mean(ep_lengths))

        # 2. Read train/* metrics from logger (these ARE available in logger.name_to_value)
        if hasattr(self.logger, 'name_to_value'):
            for key, value in self.logger.name_to_value.items():
                # Include train/* and other non-time metrics
                if not key.startswith('time/') and not key.startswith('rollout/'):
                    try:
                        metrics[key] = float(value)
                    except (TypeError, ValueError):
                        pass

        # 3. Log all metrics to W&B
        if metrics:
            # Debug: print what metrics we're logging (once per training session)
            if not hasattr(self, '_logged_once'):
                self._logged_once = True
                if self.verbose:
                    train_metrics = [k for k in metrics.keys() if k.startswith('train/')]
                    rollout_metrics = [k for k in metrics.keys() if k.startswith('rollout/')]
                    print(f"[WandbMetricsCallback] Logging {len(metrics)} metrics:")
                    if train_metrics:
                        print(f"  ✓ train/*: {train_metrics}")
                    if rollout_metrics:
                        print(f"  ✓ rollout/*: {rollout_metrics}")
                    else:
                        print(f"  ⚠ No rollout/* metrics yet (waiting for episodes to complete)")

            # Log to W&B with current timestep
            wandb.log(metrics, step=self.num_timesteps)
            self._last_log_step = self.num_timesteps

            if self.verbose > 1:
                rollout_keys = [k for k in metrics.keys() if k.startswith('rollout/')]
                train_keys = [k for k in metrics.keys() if k.startswith('train/')]
                print(f"[WandbMetricsCallback] Logged: {len(train_keys)} train/*, {len(rollout_keys)} rollout/*")



class WandbEpisodeCallback(BaseCallback):
    """
    Logs environment-specific episode-level metrics to WandB.
    Assumes a WandB run may already exist if wandb.integration.sb3.WandbCallback is used.
    """

    def __init__(
        self,
        project: str = "utdg",
        entity: str = None,
        run_name: str = None,
        tags: list = None,
        mode: str = "online",
        save_code: bool = True,
        config: dict = None,
        verbose: int = 0,
    ):
        super().__init__(verbose)
        self.project = project
        self.entity = entity
        self.run_name = run_name
        self.tags = tags or []
        self.mode = mode
        self.save_code = save_code
        self.config = config or {}
        self._initialized = False

    def _on_training_start(self) -> None:
        """
        Initialize W&B only if a run has NOT been initialized by SB3 WandbCallback.
        """
        # If WandbCallback has already run wandb.init(), reuse it.
        if wandb.run is not None:
            self._initialized = True
            if self.verbose:
                print("[WandbEpisodeCallback] Reusing existing W&B run.")
            return

        # Otherwise initialize a new run.
        wandb.init(
            project=self.project,
            entity=self.entity,
            name=self.run_name,
            tags=self.tags,
            mode=self.mode,
            save_code=self.save_code,
            config=self.config,
        )
        self._initialized = True
        if self.verbose:
            print(f"[WandbEpisodeCallback] Initialized W&B run: {wandb.run.name}")

    def _on_step(self) -> bool:
        """
        Log custom episode metrics that SB3 does NOT record.
        """
        infos = self.locals.get("infos", [{}])

        for info in infos:
            if "episode" not in info:
                continue

            # Custom metrics for this episode
            metrics = {
                "custom/episode_reward": info["episode"]["r"],
                "custom/episode_length": info["episode"]["l"],
                "custom/global_step": self.num_timesteps,
            }

            # Add custom reward components if present
            if "episode_components" in info:
                for key, value in info["episode_components"].items():
                    metrics[f"custom/reward_{key}"] = value

            elif "reward_components" in info:
                # fallback for environments that only log per-step components
                for key, value in info["reward_components"].items():
                    metrics[f"custom/reward_{key}"] = value

            wandb.log(metrics, step=self.num_timesteps)

        return True

    def _on_training_end(self) -> None:
        """
        Finish the W&B run only if we were the callback that started it.
        """
        # Do not finish the run if WandbCallback owns it.
        if self._initialized and wandb.run is not None:
            wandb.finish()
            if self.verbose:
                print("[WandbEpisodeCallback] W&B run finished.")


class WandbEvalCallback(EvalCallback):
    """
    Evaluation callback that logs evaluation metrics to W&B.
    """

    def __init__(self, eval_env, n_eval_episodes: int, eval_freq: int, verbose: int = 0):
        super().__init__(
            eval_env=eval_env,
            n_eval_episodes=n_eval_episodes,
            eval_freq=eval_freq,
            deterministic=True,
            render=False,
            verbose=verbose,
        )

    def _on_step(self) -> bool:
        result = super()._on_step()

        # Log to W&B after evaluation runs
        if self.eval_freq > 0 and self.n_calls % self.eval_freq == 0:
            if self.last_mean_reward is not None:
                wandb.log({
                    "eval/mean_reward": self.last_mean_reward,
                    "eval/mean_ep_length": (
                        float(np.mean(self.evaluations_length[-1]))
                        if self.evaluations_length else 0
                    ),
                    "eval/num_timesteps": self.num_timesteps,
                }, step=self.num_timesteps)

        return result

