"""
Mock Adapters - For testing and simulation

Use these adapters to test your code without hardware.
"""

import random
from typing import Tuple
from ..core import Action, SensorData
from .base import MotorAdapter, SensorAdapter


class MockMotor(MotorAdapter):
    """
    Simulated motor for testing.

    Records received commands for verification.
    """

    def __init__(self):
        self.commands = []
        self.current_action = Action.STOP
        self.current_speed = 0.0
        self._left_speed = 0.0
        self._right_speed = 0.0

    def execute(self, action: Action, speed: float) -> bool:
        self.commands.append((action, speed))
        self.current_action = action
        self.current_speed = speed

        # Simulate wheel speeds
        if action == Action.FORWARD:
            self._left_speed = speed
            self._right_speed = speed
        elif action == Action.BACKWARD:
            self._left_speed = -speed
            self._right_speed = -speed
        elif action == Action.TURN_LEFT:
            self._left_speed = -speed
            self._right_speed = speed
        elif action == Action.TURN_RIGHT:
            self._left_speed = speed
            self._right_speed = -speed
        else:  # STOP
            self._left_speed = 0.0
            self._right_speed = 0.0

        return True

    def stop(self) -> bool:
        return self.execute(Action.STOP, 0.0)

    def get_speed(self) -> Tuple[float, float]:
        return (self._left_speed, self._right_speed)

    def clear_history(self):
        """Clear command history."""
        self.commands = []


class MockSensor(SensorAdapter):
    """
    Simulated sensors for testing.

    Can return fixed or random values.
    """

    def __init__(self,
                 front: float = 2.0,
                 left: float = 1.0,
                 right: float = 1.0,
                 randomize: bool = False,
                 noise: float = 0.0):
        """
        Args:
            front: Default front distance
            left: Default left distance
            right: Default right distance
            randomize: If True, generate random values
            noise: Noise to add (e.g., 0.1 = ±10%)
        """
        self._front = front
        self._left = left
        self._right = right
        self._randomize = randomize
        self._noise = noise

    def read(self) -> SensorData:
        if self._randomize:
            return SensorData(
                front=random.uniform(0.1, 5.0),
                left=random.uniform(0.1, 3.0),
                right=random.uniform(0.1, 3.0),
                left_front=random.uniform(0.1, 4.0),
                right_front=random.uniform(0.1, 4.0)
            )

        front = self._front
        left = self._left
        right = self._right

        # Add noise
        if self._noise > 0:
            front *= random.uniform(1 - self._noise, 1 + self._noise)
            left *= random.uniform(1 - self._noise, 1 + self._noise)
            right *= random.uniform(1 - self._noise, 1 + self._noise)

        return SensorData(front=front, left=left, right=right)

    def set_values(self, front: float = None, left: float = None, right: float = None):
        """Change returned values."""
        if front is not None:
            self._front = front
        if left is not None:
            self._left = left
        if right is not None:
            self._right = right


class ScenarioSensor(SensorAdapter):
    """
    Sensors with predefined scenario.

    Returns different values at each call
    according to a defined sequence.
    """

    def __init__(self, scenario: list):
        """
        Args:
            scenario: List of SensorData to return in order
        """
        self._scenario = scenario
        self._index = 0

    def read(self) -> SensorData:
        if not self._scenario:
            return SensorData()

        data = self._scenario[self._index]
        self._index = (self._index + 1) % len(self._scenario)
        return data

    def reset(self):
        """Reset scenario to beginning."""
        self._index = 0
