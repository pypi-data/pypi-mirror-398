"""
StuckNode - Escape from corners

Priority 0: Highest priority - safety first.

Detects when robot is stuck (all sensors blocked, no clear direction).
BACKUP then ESCAPE in random direction.
"""

import random
from typing import Optional
from ...core.node import Node, Decision, Action
from ...core.sensors import SensorData
from ...config import RobotConfig


# Threshold for "blocked"
BLOCKED = RobotConfig.PASSAGE_THRESHOLD  # ~0.69m


class StuckNode(Node):
    """
    Escape from corners.

    Detection: front blocked AND sides similar AND all blocked
    Action: BACKUP 6 ticks, then ESCAPE (random direction) 6-12 ticks
    """

    def __init__(self):
        super().__init__("STUCK", priority=0)
        self.state = "IDLE"  # IDLE, BACKUP, ESCAPE
        self.tick_count = 0
        self.escape_direction = None

    def evaluate(self, sensors: SensorData) -> Optional[Decision]:
        if not sensors.is_valid():
            return None

        front = sensors.front or 1.0
        left = sensors.left or 0.5
        right = sensors.right or 0.5
        left_front = sensors.left_front or left
        right_front = sensors.right_front or right

        # === Continue current state ===
        if self.state == "BACKUP":
            self.tick_count += 1
            if self.tick_count >= 6:
                self.state = "ESCAPE"
                self.tick_count = 0
                # Turn toward the side with most space
                max_left = max(left, left_front)
                max_right = max(right, right_front)
                if max_left > max_right:
                    self.escape_direction = Action.TURN_LEFT
                elif max_right > max_left:
                    self.escape_direction = Action.TURN_RIGHT
                else:
                    self.escape_direction = random.choice([Action.TURN_LEFT, Action.TURN_RIGHT])
            return Decision(
                action=Action.BACKWARD,
                speed=0.4,
                reason=f"BACKUP {self.tick_count}/6 L={left:.1f} LF={left_front:.1f} F={front:.1f} RF={right_front:.1f} R={right:.1f}",
                score=100
            )

        if self.state == "ESCAPE":
            self.tick_count += 1
            min_done = self.tick_count >= 6
            front_clear = front >= BLOCKED
            timeout = self.tick_count >= 12

            if timeout or (min_done and front_clear):
                self.state = "IDLE"
                self.tick_count = 0
                return None  # Let other nodes decide

            dir_name = "L" if self.escape_direction == Action.TURN_LEFT else "R"
            return Decision(
                action=self.escape_direction,
                speed=0.5,
                reason=f"ESCAPE_{dir_name} {self.tick_count}/12 L={left:.1f} LF={left_front:.1f} F={front:.1f} RF={right_front:.1f} R={right:.1f}",
                score=100
            )

        # === Detect stuck situation ===
        max_left = max(left, left_front)
        max_right = max(right, right_front)
        max_all = max(front, max_left, max_right)

        # Stuck = front blocked AND no clear direction (sides similar) AND everything blocked
        sides_similar = (max_left < max_right * 1.5 and max_right < max_left * 1.5)
        front_blocked = front < BLOCKED
        all_blocked = max_all < BLOCKED

        if front_blocked and sides_similar and all_blocked:
            self.state = "BACKUP"
            self.tick_count = 0
            return Decision(
                action=Action.BACKWARD,
                speed=0.4,
                reason=f"STUCK L={left:.1f} LF={left_front:.1f} F={front:.1f} RF={right_front:.1f} R={right:.1f}",
                score=100
            )

        return None

    def reset(self):
        self.state = "IDLE"
        self.tick_count = 0
        self.escape_direction = None
