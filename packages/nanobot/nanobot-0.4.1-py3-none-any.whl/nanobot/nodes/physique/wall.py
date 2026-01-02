"""
WallNode - Évitement mur avec Pythagore - STATELESS

Inspiré de robot/nodes/physiques.py NodeMurDevant

Logique Pythagore:
- SEUIL_MUR = LARGEUR * 0.7 = 0.21m (chassis touche le mur)
- DIAG_CHASSIS = sqrt(L² + l²) = 0.46m (diagonale chassis)
- peut_tourner = min_capteur >= SEUIL_MUR AND diag_espace >= DIAG_CHASSIS
"""

from typing import Optional
import math
from ...core.node import Node, Decision, Action
from ...core.sensors import SensorData
from ...config import RobotConfig


# Seuils Pythagore
SEUIL_MUR = RobotConfig.WIDTH * 0.7  # ~0.21m - chassis touche le mur
DIAG_CHASSIS = RobotConfig.DIAG_CHASSIS  # ~0.46m
BLOCKED = RobotConfig.PASSAGE_THRESHOLD  # ~0.69m

# Seuil de friction : si un côté < FRICTION, on frotte le mur
# = demi-largeur + marge confortable (même que ForwardNode)
FRICTION = RobotConfig.WIDTH * 0.5 + 0.20  # ~0.40m for L/R sensors

# Seuil friction diagonale : plus bas car LF/RF sont à 30°
FRICTION_DIAG = RobotConfig.WIDTH * 0.5  # ~0.20m - only trigger when really close


def peut_tourner(capteur: float, capteur_front: float) -> bool:
    """
    Pythagore: vérifie si le chassis peut tourner dans cette direction.

    Returns True si:
    - min(capteur, capteur_front) >= SEUIL_MUR (pas collé au mur)
    - diagonale de l'espace >= DIAG_CHASSIS (assez de place)
    """
    espace_min = min(capteur, capteur_front)
    espace_max = max(capteur, capteur_front)
    diag_espace = math.sqrt(espace_max**2 + espace_min**2)

    return espace_min >= SEUIL_MUR and diag_espace >= DIAG_CHASSIS


class WallNode(Node):
    """
    Évitement mur Pythagore - STATELESS.

    Détection:
    - Front bloqué (< BLOCKED)
    - OU un côté ne peut pas tourner (peut_tourner = False)

    Action: Tourner vers le côté qui PEUT tourner
    """

    def __init__(self):
        super().__init__("WALL")

    def evaluate(self, sensors: SensorData) -> Optional[Decision]:
        if not sensors.is_valid():
            return None

        front = sensors.front or 1.0
        left = sensors.left or 0.5
        right = sensors.right or 0.5
        left_front = sensors.left_front or left
        right_front = sensors.right_front or right

        # Pythagore: peut-on tourner de chaque côté?
        gauche_viable = peut_tourner(left, left_front)
        droite_viable = peut_tourner(right, right_front)

        front_blocked = front < BLOCKED

        # === FRICTION: un côté trop proche pour avancer droit ===
        # Check both lateral (L, R) with normal threshold
        # AND diagonal (LF, RF) with lower threshold to avoid zigzag
        left_friction = left <= FRICTION or left_front <= FRICTION_DIAG
        right_friction = right <= FRICTION or right_front <= FRICTION_DIAG

        # Si friction à gauche, tourner à droite (s'éloigner du mur)
        if left_friction and not right_friction:
            return Decision(
                action=Action.TURN_RIGHT,
                speed=0.5,
                reason=f"FRIC_L L={left:.1f} LF={left_front:.1f} F={front:.1f} RF={right_front:.1f} R={right:.1f}",
                score=80
            )

        # Si friction à droite, tourner à gauche
        if right_friction and not left_friction:
            return Decision(
                action=Action.TURN_LEFT,
                speed=0.5,
                reason=f"FRIC_R L={left:.1f} LF={left_front:.1f} F={front:.1f} RF={right_front:.1f} R={right:.1f}",
                score=80
            )

        # Pas de problème si front OK et les deux côtés viables
        if not front_blocked and gauche_viable and droite_viable:
            return None

        # === CORNER: un côté bloqué, l'autre viable ===
        if not droite_viable and gauche_viable:
            return Decision(
                action=Action.TURN_LEFT,
                speed=0.5,
                reason=f"WALL_R L={left:.1f} LF={left_front:.1f} F={front:.1f} RF={right_front:.1f} R={right:.1f}",
                score=90
            )

        if not gauche_viable and droite_viable:
            return Decision(
                action=Action.TURN_RIGHT,
                speed=0.5,
                reason=f"WALL_L L={left:.1f} LF={left_front:.1f} F={front:.1f} RF={right_front:.1f} R={right:.1f}",
                score=90
            )

        # === FRONT BLOCKED: tourner vers le côté avec plus d'espace ===
        if front_blocked:
            max_left = max(left, left_front)
            max_right = max(right, right_front)

            if max_left >= max_right:
                return Decision(
                    action=Action.TURN_LEFT,
                    speed=0.5,
                    reason=f"WALL_F L={left:.1f} LF={left_front:.1f} F={front:.1f} RF={right_front:.1f} R={right:.1f}",
                    score=90
                )
            else:
                return Decision(
                    action=Action.TURN_RIGHT,
                    speed=0.5,
                    reason=f"WALL_F L={left:.1f} LF={left_front:.1f} F={front:.1f} RF={right_front:.1f} R={right:.1f}",
                    score=90
                )

        return None

    def reset(self):
        pass
