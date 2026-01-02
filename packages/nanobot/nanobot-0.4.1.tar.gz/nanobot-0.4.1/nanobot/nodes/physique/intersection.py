"""
IntersectionNode - Turn at intersections WITH LOCKOUT

Priority 2: Explore side passages.

STATEFUL: Once a turn is initiated, continue for LOCKOUT_TICKS to prevent oscillation.
Uses high score (95) during lockout to override WallNode friction.
"""

from typing import Optional
from ...core.node import Node, Decision, Action
from ...core.sensors import SensorData
from ...config import RobotConfig


# Threshold for "blocked"
BLOCKED = RobotConfig.PASSAGE_THRESHOLD  # ~0.85m

# Minimum space to consider as "open passage"
OPEN_PASSAGE = 2.0  # Must see at least 2m to consider it a passage worth exploring

# Lockout ticks - continue turning for this many ticks after initiating
# 8 ticks @ 50ms = 400ms was too short for 90° turn
# 15 ticks @ 50ms = 750ms should complete the turn
LOCKOUT_TICKS = 15

# Cooldown after lockout - don't trigger another intersection immediately
# Prevents spinning in open areas
COOLDOWN_TICKS = 10


class IntersectionNode(Node):
    """
    Turn at intersections - WITH LOCKOUT STATE.

    Detection: front is clear AND one side sees open passage (>2m)
    Action: TURN toward the open side

    LOCKOUT: Once turn initiated, continue for LOCKOUT_TICKS with high score (95)
    to prevent WallNode friction from interrupting the turn.
    """

    def __init__(self):
        super().__init__("INTERSECTION")
        self._lockout_remaining = 0
        self._locked_action = None
        self._locked_direction = None  # 'left' or 'right'
        self._cooldown_remaining = 0  # Cooldown after lockout

    def evaluate(self, sensors: SensorData) -> Optional[Decision]:
        if not sensors.is_valid():
            return None

        front = sensors.front or 1.0
        left = sensors.left or 0.5
        right = sensors.right or 0.5
        left_front = sensors.left_front or left
        right_front = sensors.right_front or right

        # === LOCKOUT: Continue previous turn with high priority ===
        if self._lockout_remaining > 0:
            self._lockout_remaining -= 1

            # Just run the full lockout - no early termination
            # Early termination was causing issues (front temporarily opens during turn)
            if self._lockout_remaining <= 0:
                self._lockout_remaining = 0
                self._locked_action = None
                self._locked_direction = None
                self._cooldown_remaining = COOLDOWN_TICKS  # Start cooldown
                return None  # Let other nodes take over

            # Continue turning with HIGH score to override friction
            return Decision(
                action=self._locked_action,
                speed=0.5,
                reason=f"INTER_LOCK({self._lockout_remaining}) L={left:.1f} LF={left_front:.1f} F={front:.1f} RF={right_front:.1f} R={right:.1f}",
                score=95  # Higher than WALL (90) and FRIC (80)
            )

        # === COOLDOWN: Don't trigger new intersection right after lockout ===
        if self._cooldown_remaining > 0:
            self._cooldown_remaining -= 1
            return None  # Let other nodes handle during cooldown

        # === Check for open passage on sides ===
        max_left = max(left, left_front)
        max_right = max(right, right_front)

        # Need a clear open passage (>2m) to trigger
        left_open = max_left >= OPEN_PASSAGE
        right_open = max_right >= OPEN_PASSAGE

        if not left_open and not right_open:
            return None  # No open passage, let ForwardNode handle

        # === Decide: turn into passage OR continue straight ===
        # Only skip if front is significantly more open than the side passage
        # This ensures we explore side passages even when front seems open
        best_side = max(max_left, max_right)
        if front > best_side * 1.5:
            return None  # Front is much more open, continue straight

        # === Decide direction and initiate lockout ===
        if left_open and (not right_open or max_left >= max_right):
            self._lockout_remaining = LOCKOUT_TICKS
            self._locked_action = Action.TURN_LEFT
            self._locked_direction = 'left'
            return Decision(
                action=Action.TURN_LEFT,
                speed=0.5,
                reason=f"INTER_L L={left:.1f} LF={left_front:.1f} F={front:.1f} RF={right_front:.1f} R={right:.1f}",
                score=95
            )
        elif right_open:
            self._lockout_remaining = LOCKOUT_TICKS
            self._locked_action = Action.TURN_RIGHT
            self._locked_direction = 'right'
            return Decision(
                action=Action.TURN_RIGHT,
                speed=0.5,
                reason=f"INTER_R L={left:.1f} LF={left_front:.1f} F={front:.1f} RF={right_front:.1f} R={right:.1f}",
                score=95
            )

        return None

    def reset(self):
        self._lockout_remaining = 0
        self._locked_action = None
        self._locked_direction = None
        self._cooldown_remaining = 0
