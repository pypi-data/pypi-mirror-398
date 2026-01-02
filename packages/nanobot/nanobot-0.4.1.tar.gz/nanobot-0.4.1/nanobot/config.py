"""
NanoBot Configuration - Lite version inspired by robot/nodes/config.py

PHILOSOPHY: All thresholds are RELATIVE to chassis dimensions.
Only physical chassis dimensions are absolute values.

Features:
- Pythagore chassis geometry
- Dynamic scoring system
- Ratio-based thresholds
"""

import os
import math


class RobotConfig:
    """
    Physical robot configuration with Pythagore geometry.

    All derived values come from chassis dimensions.
    """

    # === CHASSIS DIMENSIONS (meters) - the only absolute values ===
    # maze-server.py: size = 0.4 (carré 40cm x 40cm)
    WIDTH = float(os.getenv("ROBOT_WIDTH", "0.40"))    # 40cm wide
    LENGTH = float(os.getenv("ROBOT_LENGTH", "0.40"))  # 40cm long

    # === PYTHAGORE: Derived from chassis ===
    # Diagonal = minimum space to rotate
    DIAG_CHASSIS = math.sqrt(WIDTH**2 + LENGTH**2)  # ~0.46m

    # Passage threshold = diagonal * 1.5 (comfortable passage)
    PASSAGE_THRESHOLD = DIAG_CHASSIS * 1.5  # ~0.69m

    # Wall threshold = half width * 0.7 (touching wall)
    WALL_THRESHOLD = WIDTH * 0.7  # ~0.21m

    # === DISTANCE THRESHOLDS (derived from chassis) ===
    DISTANCE_DANGER = WALL_THRESHOLD * 1.4      # ~0.30m - imminent collision
    DISTANCE_CLOSE = DIAG_CHASSIS               # ~0.46m - attention required
    DISTANCE_SAFE = PASSAGE_THRESHOLD           # ~0.69m - safe
    DISTANCE_COMFORT = PASSAGE_THRESHOLD * 1.5  # ~1.0m - comfortable
    DISTANCE_FAR = PASSAGE_THRESHOLD * 3        # ~2.0m - clear space

    # === SPEEDS (normalized 0-1) ===
    SPEED_MAX = 1.0
    SPEED_NORMAL = 0.5
    SPEED_SLOW = 0.3
    SPEED_VERY_SLOW = 0.15

    # === SCAN LOCKOUT ===
    SCAN_LOCKOUT_TICKS = 6  # Ticks to protect SCAN decisions

    @classmethod
    def can_advance(cls, front: float) -> bool:
        """Can chassis move forward? Need safe stopping distance."""
        # Need at least diagonal + some margin to stop safely
        return front >= cls.DIAG_CHASSIS * 1.5  # ~0.69m

    @classmethod
    def can_turn(cls, lateral: float, diagonal: float) -> bool:
        """
        Can chassis turn in this direction? (Pythagore check)

        Args:
            lateral: side sensor (left or right)
            diagonal: diagonal sensor (left_front or right_front)
        """
        space_max = max(lateral, diagonal)
        space_min = min(lateral, diagonal)

        # Simplified check: just need enough space on the side
        # Original Pythagore was too strict for tight spaces
        return (space_min >= cls.WALL_THRESHOLD and
                space_max >= cls.WIDTH * 1.5)  # ~0.45m - enough to turn

    @classmethod
    def adapted_speed(cls, distance: float) -> float:
        """Calculate speed adapted to distance."""
        if distance < cls.DISTANCE_DANGER:
            return cls.SPEED_VERY_SLOW
        elif distance < cls.DISTANCE_CLOSE:
            return cls.SPEED_SLOW
        elif distance < cls.DISTANCE_COMFORT:
            return cls.SPEED_NORMAL
        else:
            return cls.SPEED_MAX


class Ratios:
    """
    Universal ratios for decision making.

    All thresholds are expressed as ratios, not absolute values.
    """

    # === DANGER RATIOS (fractions of reference space) ===
    DANGER = 0.20      # < 20% = dangerous
    CLOSE = 0.40       # < 40% = close
    VIABLE = 0.60      # > 60% = viable direction
    FREE = 0.60        # > 60% = free space
    OPEN = 0.80        # > 80% = completely open

    # === COMPARISON RATIOS ===
    ASYMMETRY = 1.50        # side1 > side2 * 1.5 = significant asymmetry
    STRONG_ASYMMETRY = 1.80 # side1 > side2 * 1.8 = strong asymmetry
    CORRIDOR = 2.0          # front > lateral * 2 = corridor
    FRICTION = 0.35         # side < other * 0.35 = friction

    # === TURN RATIOS ===
    TURN_REQUIRED = 1.2  # side > front * 1.2 = must turn
    TURN_END = 1.0       # front > turn_space = end of turn


class Score:
    """
    Dynamic scoring system.

    Each category has a range [min, max].
    Higher score = more urgent/important.
    """

    RANGES = {
        "URGENT":    (95, 100),  # Contact, immediate danger
        "CRITICAL":  (85, 94),   # Wall ahead, corner blocked
        "IMPORTANT": (70, 84),   # Turn in progress, blind spot
        "NORMAL":    (50, 69),   # Friction, oscillation
        "LOW":       (30, 49),   # Corridor, exploration
        "DEFAULT":   (10, 29),   # Default forward
    }

    @classmethod
    def calculate(cls, category: str, intensity: float = 0.5) -> int:
        """
        Calculate dynamic score.

        Args:
            category: "URGENT", "CRITICAL", "IMPORTANT", "NORMAL", "LOW", "DEFAULT"
            intensity: 0.0 (min) to 1.0 (max)
        """
        if category not in cls.RANGES:
            category = "NORMAL"

        min_score, max_score = cls.RANGES[category]
        intensity = max(0.0, min(1.0, intensity))
        return int(min_score + (max_score - min_score) * intensity)

    @classmethod
    def from_distance(cls, category: str, value: float,
                      min_threshold: float, max_threshold: float) -> int:
        """
        Calculate score from distance (closer = higher score).
        """
        if max_threshold <= min_threshold:
            return cls.calculate(category, 0.5)

        value = max(min_threshold, min(max_threshold, value))
        ratio = (value - min_threshold) / (max_threshold - min_threshold)
        intensity = 1.0 - ratio  # Inverse: closer = more intense

        return cls.calculate(category, intensity)
