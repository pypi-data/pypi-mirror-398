"""
IntersectionNode - Turn at intersections

Priority 2: Explore side passages.

STATELESS: If a side sees significantly more space than front, turn toward it.
No internal state - just react to current sensor values.
"""

from typing import Optional
from ...core.node import Node, Decision, Action
from ...core.sensors import SensorData
from ...config import RobotConfig


# Threshold for "blocked"
BLOCKED = RobotConfig.PASSAGE_THRESHOLD  # ~0.69m

# Minimum space to consider as "open passage"
OPEN_PASSAGE = 2.0  # Must see at least 2m to consider it a passage worth exploring


class IntersectionNode(Node):
    """
    Turn at intersections - STATELESS.

    Detection: front is clear AND one side sees open passage (>2m)
    Action: TURN toward the open side

    No state = no conflicts with other nodes.
    """

    def __init__(self):
        super().__init__("INTERSECTION")  # No priority - stateless reaction

    def evaluate(self, sensors: SensorData) -> Optional[Decision]:
        if not sensors.is_valid():
            return None

        front = sensors.front or 1.0
        left = sensors.left or 0.5
        right = sensors.right or 0.5
        left_front = sensors.left_front or left
        right_front = sensors.right_front or right

        # Danger threshold
        DANGER = RobotConfig.DIAG_CHASSIS  # ~0.46m

        # === Only check if front is clear (WallNode handles blocked front) ===
        if front < BLOCKED:
            return None

        # === Don't trigger if any side is in danger (WallNode handles that) ===
        min_left = min(left, left_front)
        min_right = min(right, right_front)
        if min_left < DANGER or min_right < DANGER:
            return None  # Let WallNode handle danger

        # === Check for open passage on sides ===
        max_left = max(left, left_front)
        max_right = max(right, right_front)

        # Need a clear open passage (>2m) to trigger
        left_open = max_left >= OPEN_PASSAGE
        right_open = max_right >= OPEN_PASSAGE

        if not left_open and not right_open:
            return None  # No open passage, let ForwardNode handle

        # === Turn toward the more open side ===
        if left_open and (not right_open or max_left >= max_right):
            return Decision(
                action=Action.TURN_LEFT,
                speed=0.5,
                reason=f"INTER_L L={left:.1f} LF={left_front:.1f} F={front:.1f} RF={right_front:.1f} R={right:.1f}",
                score=85
            )
        elif right_open:
            return Decision(
                action=Action.TURN_RIGHT,
                speed=0.5,
                reason=f"INTER_R L={left:.1f} LF={left_front:.1f} F={front:.1f} RF={right_front:.1f} R={right:.1f}",
                score=85
            )

        return None

    def reset(self):
        pass  # No state to reset
