"""
ForwardNode - Default forward movement - STATELESS

If nothing else triggers, go forward with speed adapted to distance.

IMPORTANT: Vérifie que le front est libre avant d'avancer!
Utilise DIAG_CHASSIS comme seuil minimum (Pythagore).
"""

from typing import Optional
from ...core.node import Node, Decision, Action
from ...core.sensors import SensorData
from ...config import RobotConfig


# Seuil minimum pour avancer = diagonale du chassis
MIN_FRONT = RobotConfig.DIAG_CHASSIS  # ~0.46m

# Seuil de friction latérale = demi-largeur + marge confortable
MIN_LATERAL = RobotConfig.WIDTH * 0.5 + 0.20  # ~0.35m


class ForwardNode(Node):
    """
    Default forward movement - STATELESS.

    VÉRIFIE que front >= DIAG_CHASSIS avant d'avancer.

    Speed based on front distance:
    - front > 1.5m: speed 1.0 (fast)
    - front > 1.0m: speed 0.7 (normal)
    - front >= DIAG_CHASSIS: speed 0.5 (slow)
    - front < DIAG_CHASSIS: REFUSE (return None → WallNode gère)
    """

    def __init__(self):
        super().__init__("FORWARD")

    def evaluate(self, sensors: SensorData) -> Optional[Decision]:
        if not sensors.is_valid():
            return None

        front = sensors.front or 1.0
        left = sensors.left or 0.5
        right = sensors.right or 0.5
        left_front = sensors.left_front or left
        right_front = sensors.right_front or right

        # === PYTHAGORE: Vérifier tous les capteurs avant d'avancer ===
        # Front bloqué?
        if front < MIN_FRONT:
            return None

        # Latéral trop proche? (friction)
        if left < MIN_LATERAL or right < MIN_LATERAL:
            return None

        # Speed based on front distance
        if front > 1.5:
            speed = 1.0
        elif front > 1.0:
            speed = 0.7
        else:
            speed = 0.5

        return Decision(
            action=Action.FORWARD,
            speed=speed,
            reason=f"FWD L={left:.1f} LF={left_front:.1f} F={front:.1f} RF={right_front:.1f} R={right:.1f}",
            score=50
        )

    def reset(self):
        pass
