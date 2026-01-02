"""
NavigationNode - Priority 10

MISSION: Navigate intelligently through space.

FEATURES (inspired by robot/nodes):
- Corridor detection: front >> sides = go straight
- Turn persistence: maintain turn for N ticks
- Minimum difference threshold: avoid zigzag in narrow corridors

RULES:
1. If in corridor (front > sides * 2) -> go forward (let explorer)
2. If angle detected (one side close, other free) -> turn
3. If both sides close -> turn toward more space (if significant diff)
4. If diagonal danger -> turn away
5. Otherwise -> None (let explorer decide)
"""

from typing import Optional
from ..core.node import Node, Decision, Action
from ..core.sensors import SensorData
from ..config import RobotConfig


class NavigationNode(Node):
    """
    Navigation node - Handles turns and corridors.

    Priority 10 = After safety, before exploration.
    """

    # Turn persistence: maintain turn for N ticks
    TURN_PERSISTENCE = 4

    # Minimum difference to trigger a turn (avoid zigzag)
    MIN_DIFF = 0.20  # 20cm difference minimum

    # Corridor ratio: front > sides * RATIO = corridor
    CORRIDOR_RATIO = 1.8

    def __init__(self):
        super().__init__("NAVIGATION", priority=10)
        self.last_turn: Optional[Action] = None
        self.turn_persistence = 0

    def evaluate(self, sensors: SensorData) -> Optional[Decision]:
        # Maintain turn persistence
        if self.turn_persistence > 0:
            self.turn_persistence -= 1
            if self.last_turn:
                return Decision(
                    action=self.last_turn,
                    speed=RobotConfig.SPEED_SLOW,
                    reason=f"NAV: persisting turn ({self.turn_persistence})"
                )

        if not sensors.is_valid():
            return None

        front = sensors.front
        left = sensors.left or float('inf')
        right = sensors.right or float('inf')
        left_front = sensors.left_front or left
        right_front = sensors.right_front or right

        # Calculate min/max spaces
        min_left = min(left, left_front)
        min_right = min(right, right_front)
        max_left = max(left, left_front)
        max_right = max(right, right_front)
        max_lateral = max(max_left, max_right)

        threshold = RobotConfig.DISTANCE_DANGER  # 0.30m

        # RULE 0: Corridor detection - front >> sides = go forward
        # Let ExplorerNode handle forward movement
        if front > max_lateral * self.CORRIDOR_RATIO and front > RobotConfig.DISTANCE_SAFE:
            self._reset_turn()
            return None  # Let explorer decide

        # RULE 1: Angle detected - one side close, other free (with margin)
        if min_right < threshold and min_left >= threshold + self.MIN_DIFF:
            return self._turn(Action.TURN_LEFT,
                f"NAV: angle right={min_right:.2f}m, turning left")

        if min_left < threshold and min_right >= threshold + self.MIN_DIFF:
            return self._turn(Action.TURN_RIGHT,
                f"NAV: angle left={min_left:.2f}m, turning right")

        # RULE 2: Both sides close -> only turn if significant difference
        if min_left < threshold and min_right < threshold:
            diff = abs(max_right - max_left)
            if diff > self.MIN_DIFF:
                if max_right > max_left:
                    return self._turn(Action.TURN_RIGHT,
                        f"NAV: narrow, right has {diff:.2f}m more space")
                else:
                    return self._turn(Action.TURN_LEFT,
                        f"NAV: narrow, left has {diff:.2f}m more space")
            # Similar space on both sides -> don't turn, go forward
            self._reset_turn()
            return None

        # RULE 3: Diagonal danger (already handled by safety, but backup here)
        if left_front < threshold and right_front >= threshold + self.MIN_DIFF:
            return self._turn(Action.TURN_RIGHT,
                f"NAV: diagonal left_front={left_front:.2f}m")

        if right_front < threshold and left_front >= threshold + self.MIN_DIFF:
            return self._turn(Action.TURN_LEFT,
                f"NAV: diagonal right_front={right_front:.2f}m")

        # RULE 4: Front blocked but sides free
        if front < RobotConfig.DIAG_CHASSIS:
            diff = abs(max_right - max_left)
            if diff > self.MIN_DIFF:
                if max_right > max_left:
                    return self._turn(Action.TURN_RIGHT,
                        f"NAV: front blocked={front:.2f}m, right has space")
                else:
                    return self._turn(Action.TURN_LEFT,
                        f"NAV: front blocked={front:.2f}m, left has space")
            else:
                # No clear winner - turn toward last known good direction
                if self.last_turn:
                    return self._turn(self.last_turn,
                        f"NAV: front blocked, continuing {self.last_turn.name}")

        # No turn needed -> reset and let explorer handle
        self._reset_turn()
        return None

    def _turn(self, action: Action, reason: str) -> Decision:
        """Create a turn decision with persistence."""
        self.last_turn = action
        self.turn_persistence = self.TURN_PERSISTENCE
        return Decision(
            action=action,
            speed=RobotConfig.SPEED_SLOW,
            reason=reason
        )

    def _reset_turn(self):
        """Reset turn state."""
        self.last_turn = None
        self.turn_persistence = 0

    def reset(self):
        self._reset_turn()
