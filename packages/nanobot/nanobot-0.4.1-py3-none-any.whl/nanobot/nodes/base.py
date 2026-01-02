"""
Base classes for NanoBot nodes - Lite version inspired by robot/nodes/base.py

Features:
- SensorEvaluator: Comprehensive sensor analysis
- NavigationMemory: Navigation memory with odometry
"""

import math
from typing import Dict, List, Tuple, Optional, Set
from ..config import RobotConfig, Ratios


class SensorEvaluator:
    """
    Sensor analysis hub - evaluates all sensors and returns structured data.

    Usage:
        analysis = SensorEvaluator.analyze(sensors)
        if analysis['wall_ahead']:
            ...
    """

    @staticmethod
    def analyze(sensors) -> Dict:
        """
        Comprehensive sensor analysis.

        Returns dict with:
        - Raw values: front, left, right, left_front, right_front
        - Derived: min_left, min_right, max_lateral, etc.
        - Flags: wall_ahead, corner_blocked, corridor, etc.
        - Pythagore: can_advance, can_turn_left, can_turn_right
        """
        # Extract raw values
        front = getattr(sensors, 'front', 1.0) or 1.0
        left = getattr(sensors, 'left', 1.0) or 1.0
        right = getattr(sensors, 'right', 1.0) or 1.0
        left_front = getattr(sensors, 'left_front', left) or left
        right_front = getattr(sensors, 'right_front', right) or right

        # Derived values
        min_left = min(left, left_front)
        min_right = min(right, right_front)
        max_left = max(left, left_front)
        max_right = max(right, right_front)
        max_lateral = max(max_left, max_right)
        min_all = min(front, min_left, min_right)
        max_all = max(front, max_left, max_right)

        # Ratios
        ratio_front = front / max_all if max_all > 0 else 1.0
        ratio_left = max_left / max_all if max_all > 0 else 0.5
        ratio_right = max_right / max_all if max_all > 0 else 0.5

        # Pythagore checks
        can_advance = RobotConfig.can_advance(front)
        can_turn_left = RobotConfig.can_turn(left, left_front)
        can_turn_right = RobotConfig.can_turn(right, right_front)

        # Situation flags
        wall_ahead = front < RobotConfig.DIAG_CHASSIS
        corner_blocked = (not can_advance and
                          not can_turn_left and
                          not can_turn_right)
        corridor = (front > max_lateral * Ratios.CORRIDOR and
                    front > RobotConfig.DISTANCE_SAFE)
        intersection = (max_left > front * 0.8 or max_right > front * 0.8)
        # Friction = side is CLOSE to wall (< WALL_THRESHOLD) AND much closer than other side
        friction_left = (min_left < RobotConfig.WALL_THRESHOLD and
                         min_left < min_right * 0.5)
        friction_right = (min_right < RobotConfig.WALL_THRESHOLD and
                          min_right < min_left * 0.5)

        return {
            # Raw values
            'front': front,
            'left': left,
            'right': right,
            'left_front': left_front,
            'right_front': right_front,

            # Derived
            'min_left': min_left,
            'min_right': min_right,
            'max_left': max_left,
            'max_right': max_right,
            'max_lateral': max_lateral,
            'min_all': min_all,
            'max_all': max_all,

            # Ratios
            'ratio_front': ratio_front,
            'ratio_left': ratio_left,
            'ratio_right': ratio_right,

            # Pythagore
            'can_advance': can_advance,
            'can_turn_left': can_turn_left,
            'can_turn_right': can_turn_right,

            # Situation flags
            'wall_ahead': wall_ahead,
            'corner_blocked': corner_blocked,
            'corridor': corridor,
            'intersection': intersection,
            'friction_left': friction_left,
            'friction_right': friction_right,
        }


# Alias for backward compatibility
CapteurEvaluator = SensorEvaluator


class NavigationMemory:
    """
    Navigation memory with odometry tracking.

    Features:
    - Position estimation from actions
    - Visit counting per cell
    - Dead-end marking
    - Action history for pattern detection
    """

    # Odometry constants
    DISTANCE_PER_FORWARD = 0.3  # meters per forward action
    ANGLE_PER_TURN = 15.0       # degrees per turn action
    CELL_SIZE = 0.5             # meters per cell

    def __init__(self):
        # Odometry
        self.x = 0.0
        self.y = 0.0
        self.angle = 0.0
        self.cumulative_error = 0.0

        # Memory
        self.visits: Dict[Tuple[int, int], int] = {}
        self.dead_ends: Set[Tuple[int, int]] = set()
        self.actions: List[str] = []
        self.max_history = 20

    def record_action(self, action: str, speed: float = 0.5):
        """Record action and update odometry."""
        # Update odometry
        if action == "forward":
            rad = math.radians(self.angle)
            self.x += math.cos(rad) * self.DISTANCE_PER_FORWARD * speed
            self.y += math.sin(rad) * self.DISTANCE_PER_FORWARD * speed
            self.cumulative_error += 0.02 * speed
        elif action == "backward":
            rad = math.radians(self.angle)
            self.x -= math.cos(rad) * self.DISTANCE_PER_FORWARD * speed * 0.5
            self.y -= math.sin(rad) * self.DISTANCE_PER_FORWARD * speed * 0.5
            self.cumulative_error += 0.03 * speed
        elif action == "turn_left":
            self.angle = (self.angle - self.ANGLE_PER_TURN * speed) % 360
            self.cumulative_error += 0.01 * speed
        elif action == "turn_right":
            self.angle = (self.angle + self.ANGLE_PER_TURN * speed) % 360
            self.cumulative_error += 0.01 * speed

        # Record action
        self.actions.append(action)
        if len(self.actions) > self.max_history:
            self.actions.pop(0)

        # Update visit count
        cell = self.get_cell()
        self.visits[cell] = self.visits.get(cell, 0) + 1

    def get_cell(self) -> Tuple[int, int]:
        """Get current cell from position."""
        return (int(self.x / self.CELL_SIZE), int(self.y / self.CELL_SIZE))

    def get_cell_ahead(self) -> Tuple[int, int]:
        """Get cell ahead of current position."""
        rad = math.radians(self.angle)
        ahead_x = self.x + math.cos(rad) * self.CELL_SIZE
        ahead_y = self.y + math.sin(rad) * self.CELL_SIZE
        return (int(ahead_x / self.CELL_SIZE), int(ahead_y / self.CELL_SIZE))

    def mark_dead_end(self, cell: Optional[Tuple[int, int]] = None):
        """Mark a cell as dead-end."""
        if cell is None:
            cell = self.get_cell()
        self.dead_ends.add(cell)

    def is_dead_end(self, cell: Optional[Tuple[int, int]] = None) -> bool:
        """Check if cell is marked as dead-end."""
        if cell is None:
            cell = self.get_cell_ahead()
        return cell in self.dead_ends

    def get_visit_count(self, cell: Optional[Tuple[int, int]] = None) -> int:
        """Get visit count for a cell."""
        if cell is None:
            cell = self.get_cell()
        return self.visits.get(cell, 0)

    def detect_loop(self) -> bool:
        """Detect if robot is stuck in a loop."""
        if len(self.actions) < 10:
            return False

        # Count unique cells in recent history
        recent_cells = set()
        for _ in range(min(10, len(self.actions))):
            cell = self.get_cell()
            recent_cells.add(cell)

        # If current cell visited 4+ times with few unique cells = loop
        current_visits = self.get_visit_count()
        return current_visits >= 4 and len(recent_cells) <= 5

    def detect_zigzag(self) -> bool:
        """Detect zigzag pattern (L-R-L-R or R-L-R-L)."""
        if len(self.actions) < 4:
            return False

        recent = self.actions[-4:]
        pattern1 = ["turn_left", "turn_right", "turn_left", "turn_right"]
        pattern2 = ["turn_right", "turn_left", "turn_right", "turn_left"]

        return recent == pattern1 or recent == pattern2

    def get_estimated_position(self) -> Tuple[float, float, float]:
        """Get estimated position (x, y, angle)."""
        return (self.x, self.y, self.angle)

    def recalibrate(self, x: float, y: float, angle: float, alpha: float = 0.3):
        """Recalibrate position with external data (fusion)."""
        self.x = self.x * (1 - alpha) + x * alpha
        self.y = self.y * (1 - alpha) + y * alpha
        self.angle = self.angle * (1 - alpha) + angle * alpha
        self.cumulative_error *= (1 - alpha)

    def clear(self):
        """Reset all memory."""
        self.x = 0.0
        self.y = 0.0
        self.angle = 0.0
        self.cumulative_error = 0.0
        self.visits.clear()
        self.dead_ends.clear()
        self.actions.clear()


# Alias for backward compatibility
MemoireNavigateur = NavigationMemory
