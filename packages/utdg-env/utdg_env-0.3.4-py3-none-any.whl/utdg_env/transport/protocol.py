"""Message protocol schema for WebSocket communication between Godot and Python.

This module defines the message format and data structures for communication
between the Godot game engine and the Python Gym environment.

Message Format:
    All messages are JSON-encoded dictionaries with a "type" field indicating
    the message type and a "data" field containing type-specific payload.

Message Types:
    - reset: Request to reset the environment
    - reset_response: Response containing initial observation
    - step: Action to execute in the environment
    - step_response: Response containing observation, reward, done, truncated, info
    - close: Request to close the environment
    - config: Configuration parameters for the environment
    - error: Error message
"""

from dataclasses import dataclass, asdict, field
from typing import Dict, Any, List, Optional
from enum import Enum


class MessageType(str, Enum):
    """Enumeration of message types for WebSocket communication."""

    RESET = "reset"
    RESET_RESPONSE = "reset_response"
    STEP = "step"
    STEP_RESPONSE = "step_response"
    CLOSE = "close"
    CONFIG = "config"
    ERROR = "error"
    READY = "ready"
    SHUTDOWN = "shutdown"
    HELLO = "hello"
    HUMAN_ACTION = "human_action"


@dataclass
class HumanActionPayload:
    """Action performed by a human player in Godot → Python.

    Used for recording expert demonstrations.
    Attributes:
        slot_index: The slot where the human clicked.
    """
    slot_index: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HumanActionPayload":
        return cls(slot_index=int(data.get("slot_index", -1)))

    def to_dict(self) -> Dict[str, Any]:
        return {"slot_index": self.slot_index}


@dataclass
class ObservationPayload:
    """Observation from Godot → Python.

    Contains the game state observations only. Terminal flags, rewards, and
    other metadata are passed separately at the response level.

    Attributes:
        gold: Current gold/currency amount.
        enemy_count: Number of active enemies.
        tower_count: Number of active towers.
        base_health: Current base health points.
        valid_actions: List of valid slot indices (action mask).
        num_slots: Total number of tower placement slots.
        tower_positions: List of [x, y] positions for each tower.
        enemy_positions: List of [x, y] positions for each enemy.
    """
    gold: int
    enemy_count: int
    tower_count: int
    base_health: int

    # Action mask information
    valid_actions: List[int] = field(default_factory=list)
    num_slots: Optional[int] = None

    # Position arrays
    tower_positions: List[List[float]] = field(default_factory=list)
    enemy_positions: List[List[float]] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ObservationPayload":
        """Create ObservationPayload from dictionary.

        Args:
            data: Dictionary containing observation data from Godot.

        Returns:
            ObservationPayload instance with all fields populated.
        """
        return cls(
            gold=int(data.get("gold", 0)),
            enemy_count=int(data.get("enemy_count", 0)),
            tower_count=int(data.get("tower_count", 0)),
            base_health=int(data.get("base_health", 0)),
            valid_actions=[int(a) for a in data.get("valid_actions", [])],
            num_slots=data.get("num_slots"),
            tower_positions=data.get("tower_positions", []),
            enemy_positions=data.get("enemy_positions", []),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert ObservationPayload to dictionary.

        Returns:
            Dictionary containing all observation fields.
        """
        return {
            "gold": self.gold,
            "enemy_count": self.enemy_count,
            "tower_count": self.tower_count,
            "base_health": self.base_health,
            "valid_actions": self.valid_actions,
            "num_slots": self.num_slots,
            "tower_positions": self.tower_positions,
            "enemy_positions": self.enemy_positions,
        }


@dataclass
class ActionPayload:
    """
    Action from Python → Godot.

    slot_index:
        -1 → explicit noop
         0..N-1 → build tower at that grid slot
    """
    slot_index: int

    @classmethod
    def for_noop(cls) -> "ActionPayload":
        return cls(slot_index=-1)

    def to_dict(self) -> Dict[str, Any]:
        return {"slot_index": int(self.slot_index)}


@dataclass
class StepResponseData:
    """Response data for step action.
    Attributes:
        observation: Current game state observation
        reward: Reward value for the action
        done: Whether the episode is complete (win/loss)
        truncated: Whether the episode was truncated (time limit)
        info: Additional information dictionary
    """
    observation: ObservationPayload
    reward: float
    done: bool
    truncated: bool
    info: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert step response to dictionary."""
        return {
            "observation": self.observation.to_dict(),
            "reward": self.reward,
            "done": self.done,
            "truncated": self.truncated,
            "info": self.info
        }


@dataclass
class ConfigData:
    """Configuration data for the environment.
    Attributes:
        headless: Whether to run Godot in headless mode
        port: WebSocket server port
        host: WebSocket server host
        max_episode_steps: Maximum steps per episode (optional)
        starting_gold: Starting gold amount (optional)
        base_health: Starting base health (optional)
    """
    headless: bool = True
    port: int = 9876
    host: str = "127.0.0.1"
    max_episode_steps: Optional[int] = 1000
    starting_gold: Optional[int] = 150
    base_health: Optional[int] = 10

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return asdict(self)


class Message:
    """WebSocket message wrapper for structured communication."""

    def __init__(self, msg_type: MessageType, data: Optional[Any] = None):
        """Initialize message.
        Args:
            msg_type: Type of the message
            data: Message payload data (optional)
        """
        self.type = msg_type
        self.data = data

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for JSON serialization.
        Returns:
            Dictionary representation of the message
        """
        msg_dict = {"type": self.type.value}

        if self.data is not None:
            if hasattr(self.data, 'to_dict'):
                msg_dict["data"] = self.data.to_dict()
            else:
                msg_dict["data"] = self.data

        return msg_dict

    @classmethod
    def from_dict(cls, msg_dict: Dict[str, Any]) -> 'Message':
        """Create message from dictionary.
        Args:
            msg_dict: Dictionary containing message data
        Returns:
            Message instance
        Raises:
            ValueError: If message type is invalid
        """
        msg_type = MessageType(msg_dict.get("type"))
        data = msg_dict.get("data")

        return cls(msg_type, data)

    def __repr__(self) -> str:
        """String representation of message."""
        return f"Message(type={self.type}, data={self.data})"


def create_reset_message() -> Message:
    """Create a reset message.
    Returns:
        Reset message
    """
    return Message(MessageType.RESET)


def create_step_message(action: ActionPayload) -> Message:
    """Create a step message with action data.
    Args:
        action: Action data to send
    Returns:
        Step message
    """
    return Message(MessageType.STEP, action)


def create_close_message() -> Message:
    """Create a close message.
    Returns:
        Close message
    """
    return Message(MessageType.CLOSE)


def create_config_message(config: ConfigData) -> Message:
    """Create a config message.
    Args:
        config: Configuration data
    Returns:
        Config message
    """
    return Message(MessageType.CONFIG, config)


def create_error_message(error_msg: str) -> Message:
    """Create an error message.
    Args:
        error_msg: Error message string
    Returns:
        Error message
    """
    return Message(MessageType.ERROR, {"error": error_msg})
