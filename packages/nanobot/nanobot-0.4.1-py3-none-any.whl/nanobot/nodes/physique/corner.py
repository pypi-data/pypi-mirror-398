"""
CornerNode - Turn at exterior corners

Priority 2: Same as IntersectionNode.

Detects when robot was following a wall and the wall disappears (exterior corner).
Turn toward the side where the wall was.
"""

from typing import Optional
from ...core.node import Node, Decision, Action
from ...core.sensors import SensorData
from ...config import RobotConfig


# Threshold for "blocked" / "wall nearby"
BLOCKED = RobotConfig.PASSAGE_THRESHOLD  # ~0.69m
WALL_CLOSE = 0.5  # Consider as "following wall" if < 0.5m


class CornerNode(Node):
    """
    Turn at exterior corners.

    Detection: was following wall (side < WALL_CLOSE) and now side >= BLOCKED
    Action: TURN toward the side where wall was, for at least 6 ticks
    """

    def __init__(self):
        super().__init__("CORNER", priority=2)
        self.state = "IDLE"  # IDLE, TURNING
        self.turn_direction = None
        self.tick_count = 0
        # Track which side had wall recently
        self.left_wall_ticks = 0
        self.right_wall_ticks = 0

    def evaluate(self, sensors: SensorData) -> Optional[Decision]:
        if not sensors.is_valid():
            return None

        front = sensors.front or 1.0
        left = sensors.left or 0.5
        right = sensors.right or 0.5
        left_front = sensors.left_front or left
        right_front = sensors.right_front or right

        min_left = min(left, left_front)
        min_right = min(right, right_front)

        # === Track wall following ===
        if min_left < WALL_CLOSE:
            self.left_wall_ticks += 1
        else:
            self.left_wall_ticks = max(0, self.left_wall_ticks - 1)

        if min_right < WALL_CLOSE:
            self.right_wall_ticks += 1
        else:
            self.right_wall_ticks = max(0, self.right_wall_ticks - 1)

        # === Continue turning ===
        if self.state == "TURNING":
            self.tick_count += 1

            # Minimum 6 ticks for 90° corner
            min_done = self.tick_count >= 6
            front_clear = front >= BLOCKED
            timeout = self.tick_count >= 16

            if timeout or (min_done and front_clear):
                self.state = "IDLE"
                self.tick_count = 0
                self.turn_direction = None
                return None

            dir_name = "L" if self.turn_direction == Action.TURN_LEFT else "R"
            return Decision(
                action=self.turn_direction,
                speed=0.5,
                reason=f"CORNER_{dir_name} {self.tick_count}/16 L={left:.1f} LF={left_front:.1f} F={front:.1f} RF={right_front:.1f} R={right:.1f}",
                score=85
            )

        # === Only check if front is clear ===
        if front < BLOCKED:
            return None

        # === Detect exterior corner ===
        # Was following left wall (3+ ticks) and now left is clear
        left_corner = (self.left_wall_ticks >= 3 and min_left >= BLOCKED)
        # Was following right wall (3+ ticks) and now right is clear
        right_corner = (self.right_wall_ticks >= 3 and min_right >= BLOCKED)

        if left_corner and not right_corner:
            self.turn_direction = Action.TURN_LEFT
            self.state = "TURNING"
            self.tick_count = 0
            self.left_wall_ticks = 0  # Reset
            return Decision(
                action=Action.TURN_LEFT,
                speed=0.5,
                reason=f"CORNER_L L={left:.1f} LF={left_front:.1f} F={front:.1f} RF={right_front:.1f} R={right:.1f}",
                score=85
            )

        if right_corner and not left_corner:
            self.turn_direction = Action.TURN_RIGHT
            self.state = "TURNING"
            self.tick_count = 0
            self.right_wall_ticks = 0  # Reset
            return Decision(
                action=Action.TURN_RIGHT,
                speed=0.5,
                reason=f"CORNER_R L={left:.1f} LF={left_front:.1f} F={front:.1f} RF={right_front:.1f} R={right:.1f}",
                score=85
            )

        return None

    def reset(self):
        self.state = "IDLE"
        self.turn_direction = None
        self.tick_count = 0
        self.left_wall_ticks = 0
        self.right_wall_ticks = 0
