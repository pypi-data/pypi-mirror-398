"""
Scan nodes - Lite version inspired by robot/nodes/stop.py

Predictive intersection scanning:
- ScanNode: Detect and handle intersections
"""

from typing import Optional
from ..core.node import Node, Decision, Action
from ..core.sensors import SensorData
from ..config import RobotConfig, Score
from .base import SensorEvaluator


class ScanNode(Node):
    """
    Intersection scanner - chooses best direction at intersections.

    At intersections (carrefours), evaluates all viable directions
    and chooses the one with most space.

    Priority: 5 (medium - after safety nodes)
    Score: IMPORTANT (70-84)
    """

    def __init__(self):
        super().__init__("SCAN", priority=5)
        self.lockout_remaining = 0
        self.last_direction = None

    def evaluate(self, sensors: SensorData) -> Optional[Decision]:
        if not sensors.is_valid():
            return None

        # During lockout, continue last decision
        if self.lockout_remaining > 0:
            self.lockout_remaining -= 1
            if self.last_direction:
                return Decision(
                    action=self.last_direction,
                    speed=RobotConfig.SPEED_SLOW,
                    reason=f"SCAN: lockout {self.lockout_remaining}",
                    score=Score.calculate("IMPORTANT", 0.7)
                )

        analysis = SensorEvaluator.analyze(sensors)

        # In corridor (front >> sides)? Don't intervene
        if analysis['corridor']:
            self.last_direction = None
            return None

        # No intersection? Don't intervene
        if not analysis['intersection']:
            self.last_direction = None
            return None

        # We're at an intersection - evaluate directions
        front = analysis['front']
        max_left = analysis['max_left']
        max_right = analysis['max_right']

        # Build list of viable directions with scores
        directions = []

        # Forward (if can advance)
        if analysis['can_advance']:
            directions.append(('forward', Action.FORWARD, front))

        # Left (if can turn)
        if analysis['can_turn_left']:
            directions.append(('left', Action.TURN_LEFT, max_left))

        # Right (if can turn)
        if analysis['can_turn_right']:
            directions.append(('right', Action.TURN_RIGHT, max_right))

        if not directions:
            return None

        # Sort by space (most space first)
        directions.sort(key=lambda x: x[2], reverse=True)
        best_name, best_action, best_space = directions[0]

        # Forward bias: only turn if side has significantly more space (50%+)
        if analysis['can_advance']:
            if best_action != Action.FORWARD and best_space < front * 1.5:
                # Not worth turning, continue forward
                self.last_direction = None
                return None

        # If best is forward, let CorridorNode handle it
        if best_action == Action.FORWARD:
            self.last_direction = None
            return None

        # Turn decision - apply lockout to complete the turn
        self.last_direction = best_action
        self.lockout_remaining = RobotConfig.SCAN_LOCKOUT_TICKS

        return Decision(
            action=best_action,
            speed=RobotConfig.SPEED_SLOW,
            reason=f"SCAN: {best_name} has {best_space:.1f}m (F={front:.1f})",
            score=Score.calculate("IMPORTANT", 0.8)
        )

    def reset(self):
        self.lockout_remaining = 0
        self.last_direction = None
