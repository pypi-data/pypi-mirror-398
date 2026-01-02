"""
ExplorerNode - Priority 50

MISSION: Explore when path is clear.

This node is the default behavior:
- If other nodes didn't decide, move forward
- Speed adapted to available space

SIMPLE RULE:
    Move forward at speed proportional to space ahead.
"""

from typing import Optional
from ..core.node import Node, Decision, Action
from ..core.sensors import SensorData
from ..config import RobotConfig


class ExplorerNode(Node):
    """
    Exploration node - Move forward when safe.

    Priority 50 = Default behavior (lowest priority).
    """

    def __init__(self):
        super().__init__("EXPLORER", priority=50)

    def evaluate(self, sensors: SensorData) -> Optional[Decision]:
        if not sensors.is_valid():
            # Without sensors, don't move blindly
            return Decision(
                action=Action.STOP,
                speed=0,
                reason="EXPLORER: no sensors, stopping"
            )

        front = sensors.front

        # If we get here, safety and navigation didn't intervene
        # So path is clear -> move forward!

        if front > RobotConfig.DISTANCE_FAR:
            # Lots of space -> max speed
            return Decision(
                action=Action.FORWARD,
                speed=RobotConfig.SPEED_MAX,
                reason=f"EXPLORER: clear path {front:.2f}m, full speed"
            )

        elif front > RobotConfig.DISTANCE_COMFORT:
            # Comfortable space -> normal speed
            return Decision(
                action=Action.FORWARD,
                speed=RobotConfig.SPEED_NORMAL,
                reason=f"EXPLORER: good space {front:.2f}m"
            )

        elif front > RobotConfig.DISTANCE_CLOSE:
            # Limited space -> slow speed
            return Decision(
                action=Action.FORWARD,
                speed=RobotConfig.SPEED_SLOW,
                reason=f"EXPLORER: limited space {front:.2f}m, slowing down"
            )

        else:
            # Very little space -> very slow
            return Decision(
                action=Action.FORWARD,
                speed=RobotConfig.SPEED_VERY_SLOW,
                reason=f"EXPLORER: tight space {front:.2f}m, careful"
            )

    def reset(self):
        pass
