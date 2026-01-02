"""
Node - Base class for all nodes

A node is simple:
- It receives sensor data
- It returns an Action or None
- If it returns None, the next node is consulted
"""

from enum import Enum, auto
from typing import Optional, TYPE_CHECKING
from abc import ABC, abstractmethod

if TYPE_CHECKING:
    from .sensors import SensorData


class Action(Enum):
    """Available robot actions"""
    FORWARD = auto()
    BACKWARD = auto()
    TURN_LEFT = auto()
    TURN_RIGHT = auto()
    STOP = auto()


class Decision:
    """Decision made by a node"""

    def __init__(self, action: Action, speed: float = 0.5, reason: str = "", score: int = 50):
        self.action = action
        self.speed = speed
        self.reason = reason
        self.score = score  # Priority score (higher = more urgent)

    def __repr__(self):
        return f"{self.action.name}({self.speed:.1f}) [{self.score}] - {self.reason}"


class Node(ABC):
    """
    Base class for all nodes.

    Rules:
    1. A node has a priority (0 = highest priority)
    2. evaluate() returns Decision or None
    3. If None, the next node is consulted
    4. No scoring, no voting - first to decide wins
    """

    def __init__(self, name: str, priority: int = 50):
        self.name = name
        self.priority = priority

    @abstractmethod
    def evaluate(self, sensors: 'SensorData') -> Optional[Decision]:
        """
        Evaluate sensors and return a decision.

        Args:
            sensors: Sensor data

        Returns:
            Decision if the node makes a decision
            None if the node passes
        """
        pass

    def reset(self):
        """Reset internal node state (optional)"""
        pass

    def __repr__(self):
        return f"<Node {self.name} p={self.priority}>"
