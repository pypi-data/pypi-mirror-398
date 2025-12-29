import os
import logging
from stable_baselines3.common.callbacks import BaseCallback

class SaveModelCallback(BaseCallback):
    """
    Callback for saving the final model to a local file at the end of training.
    """

    def __init__(self, save_path: str, verbose: int = 1):
        super().__init__(verbose)
        self.save_path = save_path

    def _on_step(self) -> bool:
        return True

    def _on_training_end(self) -> None:
        logger = logging.getLogger(__name__)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.save_path), exist_ok=True)
        
        if self.verbose > 0:
            logger.info(f"Saving final model to {self.save_path}")
        
        self.model.save(self.save_path)
