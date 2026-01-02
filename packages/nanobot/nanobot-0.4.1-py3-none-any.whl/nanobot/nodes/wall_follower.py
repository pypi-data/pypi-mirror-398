"""
Wall Follower Node - Advanced wall following algorithms

Supports:
- Right-hand rule
- Left-hand rule
- Closest wall following
- PID-controlled distance maintenance
"""

import math
from typing import Optional
from ..core import Node, Decision, Action, SensorData


class PIDController:
    """Simple PID controller for smooth wall following."""

    def __init__(self, kp: float = 1.0, ki: float = 0.0, kd: float = 0.1):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.prev_error = 0.0
        self.integral = 0.0
        self.integral_max = 1.0  # Anti-windup

    def compute(self, error: float, dt: float = 0.1) -> float:
        """
        Compute PID output.

        Args:
            error: Current error (target - actual)
            dt: Time delta

        Returns:
            Control output
        """
        # Proportional
        p = self.kp * error

        # Integral with anti-windup
        self.integral += error * dt
        self.integral = max(-self.integral_max, min(self.integral_max, self.integral))
        i = self.ki * self.integral

        # Derivative
        d = self.kd * (error - self.prev_error) / dt if dt > 0 else 0
        self.prev_error = error

        return p + i + d

    def reset(self):
        """Reset controller state."""
        self.prev_error = 0.0
        self.integral = 0.0


class WallFollowerNode(Node):
    """
    Advanced wall following with PID control.

    Maintains a target distance from a wall while navigating.
    """

    # Wall side options
    FOLLOW_RIGHT = "right"
    FOLLOW_LEFT = "left"
    FOLLOW_CLOSEST = "closest"

    def __init__(self,
                 side: str = "right",
                 target_distance: float = 0.5,
                 priority: int = 30):
        """
        Args:
            side: Which wall to follow ("right", "left", "closest")
            target_distance: Desired distance from wall in meters
            priority: Node priority
        """
        super().__init__("WALL_FOLLOWER", priority)
        self.side = side
        self.target_distance = target_distance

        # PID controller for distance maintenance
        self.pid = PIDController(kp=2.0, ki=0.1, kd=0.5)

        # State
        self.active = False
        self.lost_wall_count = 0
        self.max_lost_count = 10  # Ticks before giving up

        # Parameters
        self.min_wall_distance = 0.15  # Too close threshold
        self.max_wall_distance = 1.5   # Too far threshold (lost wall)
        self.corner_threshold = 0.4    # Distance to detect corners
        self.forward_clearance = 0.5   # Minimum front clearance

    def start(self):
        """Activate wall following."""
        self.active = True
        self.pid.reset()
        self.lost_wall_count = 0

    def stop(self):
        """Deactivate wall following."""
        self.active = False

    def is_active(self) -> bool:
        return self.active

    def _get_wall_distance(self, sensors: SensorData) -> Optional[float]:
        """Get distance to the wall we're following."""
        if self.side == self.FOLLOW_RIGHT:
            return sensors.right
        elif self.side == self.FOLLOW_LEFT:
            return sensors.left
        else:  # FOLLOW_CLOSEST
            if sensors.left is None and sensors.right is None:
                return None
            if sensors.left is None:
                return sensors.right
            if sensors.right is None:
                return sensors.left
            return min(sensors.left, sensors.right)

    def _get_turn_direction(self, toward_wall: bool) -> Action:
        """Get turn direction based on wall side."""
        if self.side == self.FOLLOW_RIGHT:
            return Action.TURN_RIGHT if toward_wall else Action.TURN_LEFT
        elif self.side == self.FOLLOW_LEFT:
            return Action.TURN_LEFT if toward_wall else Action.TURN_RIGHT
        else:  # FOLLOW_CLOSEST - default to right
            return Action.TURN_RIGHT if toward_wall else Action.TURN_LEFT

    def evaluate(self, sensors: SensorData) -> Optional[Decision]:
        # Not active? Pass to next node
        if not self.active:
            return None

        wall_dist = self._get_wall_distance(sensors)

        # Lost the wall?
        if wall_dist is None or wall_dist > self.max_wall_distance:
            self.lost_wall_count += 1
            if self.lost_wall_count > self.max_lost_count:
                self.stop()
                return Decision(Action.STOP, 0.0, "Lost wall, stopping")

            # Try to find wall by turning toward it
            return Decision(
                self._get_turn_direction(toward_wall=True),
                0.3,
                f"Searching for wall ({self.lost_wall_count}/{self.max_lost_count})"
            )

        # Found wall again
        self.lost_wall_count = 0

        # Check front clearance
        front_blocked = sensors.front is not None and sensors.front < self.forward_clearance

        # Inside corner detection (wall ahead + wall on side)
        if front_blocked:
            return Decision(
                self._get_turn_direction(toward_wall=False),
                0.4,
                "Inside corner, turning away"
            )

        # Outside corner detection (wall suddenly far)
        # This means we passed a corner and need to turn into it
        if wall_dist > self.target_distance * 2:
            return Decision(
                self._get_turn_direction(toward_wall=True),
                0.3,
                "Outside corner, turning toward wall"
            )

        # Normal wall following with PID
        error = self.target_distance - wall_dist
        correction = self.pid.compute(error)

        # Too close to wall
        if wall_dist < self.min_wall_distance:
            return Decision(
                self._get_turn_direction(toward_wall=False),
                0.3,
                f"Too close ({wall_dist:.2f}m), moving away"
            )

        # Apply correction as turning
        if abs(correction) > 0.3:
            if correction > 0:  # Need to get closer to wall
                return Decision(
                    self._get_turn_direction(toward_wall=True),
                    0.3,
                    f"Adjusting toward wall (err={error:.2f})"
                )
            else:  # Need to get away from wall
                return Decision(
                    self._get_turn_direction(toward_wall=False),
                    0.3,
                    f"Adjusting away from wall (err={error:.2f})"
                )

        # Good distance, move forward
        # Speed based on front clearance
        speed = 0.5
        if sensors.front is not None:
            speed = min(0.5, sensors.front / 2)

        return Decision(Action.FORWARD, speed, f"Following wall at {wall_dist:.2f}m")

    def reset(self):
        """Reset node state."""
        self.active = False
        self.pid.reset()
        self.lost_wall_count = 0


class LeftWallFollowerNode(WallFollowerNode):
    """Convenience class for left wall following."""

    def __init__(self, target_distance: float = 0.5, priority: int = 30):
        super().__init__(
            side=WallFollowerNode.FOLLOW_LEFT,
            target_distance=target_distance,
            priority=priority
        )
        self.name = "LEFT_WALL_FOLLOWER"


class RightWallFollowerNode(WallFollowerNode):
    """Convenience class for right wall following."""

    def __init__(self, target_distance: float = 0.5, priority: int = 30):
        super().__init__(
            side=WallFollowerNode.FOLLOW_RIGHT,
            target_distance=target_distance,
            priority=priority
        )
        self.name = "RIGHT_WALL_FOLLOWER"
