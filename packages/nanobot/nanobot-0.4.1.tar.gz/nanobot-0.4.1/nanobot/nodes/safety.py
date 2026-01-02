"""
SafetyNode - Priority 0 (ABSOLUTE)

MISSION: Prevent collisions. Period.

This node has maximum priority. If it decides, no one can
override it. It's the ultimate safeguard.

FEATURES (inspired by robot/nodes):
- VETO persistence: maintains decision for N ticks even without sensors
- Pythagore chassis calculations
- Anti-alternance: prevents zigzag oscillations
- Diagonal collision detection

RULES:
1. If diagonal < CLOSE -> turn away (corner detection)
2. If front < DANGER -> turn or backward
3. If completely stuck -> cycle backup/turn (never stop)
4. Otherwise -> None (let others decide)
"""

from typing import Optional
from ..core.node import Node, Decision, Action
from ..core.sensors import SensorData
from ..config import RobotConfig


class SafetyNode(Node):
    """
    Safety node - Collision avoidance with VETO persistence.

    Priority 0 = Executes first, ALWAYS.
    """

    # VETO persistence: maintain decision for N ticks
    VETO_PERSISTENCE = 5

    def __init__(self):
        super().__init__("SAFETY", priority=0)
        self.stuck_count = 0

        # VETO system (from robot/nodes)
        self.last_veto = None
        self.veto_persistence = 0

        # Anti-alternance
        self.last_direction = None
        self.direction_lockout = 0

    def evaluate(self, sensors: SensorData) -> Optional[Decision]:
        # Decrease lockout each tick
        if self.direction_lockout > 0:
            self.direction_lockout -= 1

        # No sensors -> maintain VETO if active
        if not sensors.is_valid():
            if self.last_veto and self.veto_persistence > 0:
                self.veto_persistence -= 1
                return Decision(
                    action=self.last_veto.action,
                    speed=self.last_veto.speed,
                    reason=f"{self.last_veto.reason} [PERSIST {self.veto_persistence}]"
                )
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

        # RULE 0: Diagonal collision - chassis corner will hit wall
        # Use DISTANCE_CLOSE (0.50m) for early detection
        if left_front < RobotConfig.DISTANCE_CLOSE and right_front >= RobotConfig.DISTANCE_CLOSE:
            return self._veto(Action.TURN_RIGHT,
                f"SAFETY: left_front={left_front:.2f}m, avoid corner")

        if right_front < RobotConfig.DISTANCE_CLOSE and left_front >= RobotConfig.DISTANCE_CLOSE:
            return self._veto(Action.TURN_LEFT,
                f"SAFETY: right_front={right_front:.2f}m, avoid corner")

        # Both diagonals close - turn toward more space
        if left_front < RobotConfig.DISTANCE_CLOSE and right_front < RobotConfig.DISTANCE_CLOSE:
            if max_right > max_left:
                return self._veto(Action.TURN_RIGHT,
                    f"SAFETY: both diag close, right has {max_right:.2f}m")
            else:
                return self._veto(Action.TURN_LEFT,
                    f"SAFETY: both diag close, left has {max_left:.2f}m")

        # RULE 1: Imminent frontal collision
        if front < RobotConfig.DISTANCE_DANGER:
            # Check if we can turn using Pythagore-style logic
            left_viable = min_left > RobotConfig.DISTANCE_DANGER
            right_viable = min_right > RobotConfig.DISTANCE_DANGER

            if left_viable and right_viable:
                # Both viable - choose larger space (with anti-alternance)
                if max_left > max_right:
                    return self._veto_with_anti_alt(Action.TURN_LEFT,
                        f"SAFETY: front={front:.2f}m, turn left")
                else:
                    return self._veto_with_anti_alt(Action.TURN_RIGHT,
                        f"SAFETY: front={front:.2f}m, turn right")
            elif left_viable:
                return self._veto(Action.TURN_LEFT,
                    f"SAFETY: front={front:.2f}m, only left viable")
            elif right_viable:
                return self._veto(Action.TURN_RIGHT,
                    f"SAFETY: front={front:.2f}m, only right viable")
            else:
                # No viable direction -> back up
                return self._veto(Action.BACKWARD,
                    "SAFETY: blocked, backing up")

        # RULE 2: Completely stuck (all sides blocked)
        if (front < RobotConfig.DISTANCE_CLOSE and
            min_left < RobotConfig.DISTANCE_CLOSE and
            min_right < RobotConfig.DISTANCE_CLOSE):

            self.stuck_count += 1

            # Cycle: backup(2x) -> turn(2x) -> repeat (never stop)
            cycle = self.stuck_count % 4
            if cycle < 2:
                # Backup first
                return self._veto(Action.BACKWARD,
                    f"SAFETY: trapped ({self.stuck_count}x), backing up")
            else:
                # Then turn toward more space
                if max_left > max_right:
                    return self._veto(Action.TURN_LEFT,
                        f"SAFETY: trapped ({self.stuck_count}x), turning left")
                else:
                    return self._veto(Action.TURN_RIGHT,
                        f"SAFETY: trapped ({self.stuck_count}x), turning right")
        else:
            # Only reset if front is really clear
            if front > RobotConfig.DISTANCE_SAFE:
                self.stuck_count = 0
                # Clear VETO when truly safe
                self.last_veto = None
                self.veto_persistence = 0

        # No immediate danger -> let other nodes decide
        return None

    def _veto(self, action: Action, reason: str) -> Decision:
        """Create a VETO decision with persistence."""
        decision = Decision(
            action=action,
            speed=RobotConfig.SPEED_SLOW,
            reason=reason
        )
        self.last_veto = decision
        self.veto_persistence = self.VETO_PERSISTENCE
        return decision

    def _veto_with_anti_alt(self, action: Action, reason: str) -> Decision:
        """Create a VETO with anti-alternance check."""
        # Check for zigzag pattern
        if self.direction_lockout > 0:
            if action == Action.TURN_LEFT and self.last_direction == "right":
                # Would zigzag - keep previous direction
                return self._veto(Action.TURN_RIGHT, reason + " [ANTI-ALT]")
            elif action == Action.TURN_RIGHT and self.last_direction == "left":
                # Would zigzag - keep previous direction
                return self._veto(Action.TURN_LEFT, reason + " [ANTI-ALT]")

        # No zigzag - record direction
        if action == Action.TURN_LEFT:
            self.last_direction = "left"
            self.direction_lockout = 3
        elif action == Action.TURN_RIGHT:
            self.last_direction = "right"
            self.direction_lockout = 3

        return self._veto(action, reason)

    def reset(self):
        self.stuck_count = 0
        self.last_veto = None
        self.veto_persistence = 0
        self.last_direction = None
        self.direction_lockout = 0
