"""
FrictionNode - Avoid wall friction

Priority 2: Same as CornerNode.

When robot is too close to a wall on one side (< chassis diagonal),
turn slightly away to avoid friction and see corners better.
"""

from typing import Optional
from ...core.node import Node, Decision, Action
from ...core.sensors import SensorData
from ...config import RobotConfig


# Threshold for "too close" - chassis diagonal
TOO_CLOSE = RobotConfig.DIAG_CHASSIS  # ~0.46m


class FrictionNode(Node):
    """
    Avoid wall friction.

    Detection: one side < TOO_CLOSE while front is clear
    Action: TURN slightly away from wall (just a few ticks)

    Only triggers in narrow corridors (no open space detected recently).
    """

    def __init__(self):
        super().__init__("FRICTION", priority=2)
        self.state = "IDLE"  # IDLE, TURNING
        self.turn_direction = None
        self.tick_count = 0
        self.open_space_cooldown = 0  # Ticks since open space was seen

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

        # === Continue turning ===
        if self.state == "TURNING":
            self.tick_count += 1

            # Short turn - just 2-3 ticks to adjust
            timeout = self.tick_count >= 3

            # Stop if side is now clear enough
            if self.turn_direction == Action.TURN_RIGHT:
                side_clear = min_left >= TOO_CLOSE
            else:
                side_clear = min_right >= TOO_CLOSE

            if timeout or side_clear:
                self.state = "IDLE"
                self.tick_count = 0
                self.turn_direction = None
                return None

            dir_name = "L" if self.turn_direction == Action.TURN_LEFT else "R"
            return Decision(
                action=self.turn_direction,
                speed=0.3,  # Slow turn
                reason=f"FRICTION_{dir_name} {self.tick_count}/3 L={left:.1f} LF={left_front:.1f} F={front:.1f} RF={right_front:.1f} R={right:.1f}",
                score=75
            )

        # === Only check if front is clear ===
        if front < RobotConfig.PASSAGE_THRESHOLD:
            return None  # WallNode will handle this

        # === Detect friction ===
        left_friction = min_left < TOO_CLOSE
        right_friction = min_right < TOO_CLOSE

        max_left = max(left, left_front)
        max_right = max(right, right_front)

        # Don't trigger friction if there's any open space (intersection/corner territory)
        # Use a lower threshold - if any sensor sees > 2m, let other nodes handle
        OPEN_SPACE = 2.0
        if max_left > OPEN_SPACE or max_right > OPEN_SPACE:
            return None  # Open space detected, not a corridor friction case

        # Only one side in friction (not both = stuck situation)
        if left_friction and not right_friction:
            self.turn_direction = Action.TURN_RIGHT  # Turn away from left wall
            self.state = "TURNING"
            self.tick_count = 0
            return Decision(
                action=Action.TURN_RIGHT,
                speed=0.3,
                reason=f"FRICTION_R L={left:.1f} LF={left_front:.1f} F={front:.1f} RF={right_front:.1f} R={right:.1f}",
                score=75
            )

        if right_friction and not left_friction:
            self.turn_direction = Action.TURN_LEFT  # Turn away from right wall
            self.state = "TURNING"
            self.tick_count = 0
            return Decision(
                action=Action.TURN_LEFT,
                speed=0.3,
                reason=f"FRICTION_L L={left:.1f} LF={left_front:.1f} F={front:.1f} RF={right_front:.1f} R={right:.1f}",
                score=75
            )

        return None

    def reset(self):
        self.state = "IDLE"
        self.turn_direction = None
        self.tick_count = 0
