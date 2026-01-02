"""
Memory nodes - Lite version inspired by robot/nodes/memoire.py

Temporal pattern detection:
- LoopNode: Detect spatial loops (revisiting same cells)
- DeadEndNode: Avoid known dead-ends
- HistoryNode: Favor less visited directions
"""

from typing import Optional
from ..core.node import Node, Decision, Action
from ..core.sensors import SensorData
from ..config import RobotConfig, Score
from .base import SensorEvaluator, NavigationMemory


class LoopNode(Node):
    """
    Loop detection - escape when stuck in spatial loop.

    Detects when robot revisits same cells repeatedly.
    Forces escape when 4+ visits to same cell with few unique cells.

    Priority: 6
    Score: IMPORTANT (70-84)
    """

    def __init__(self, memory: NavigationMemory):
        super().__init__("LOOP", priority=6)
        self.memory = memory
        self.escape_cooldown = 0

    def evaluate(self, sensors: SensorData) -> Optional[Decision]:
        if not sensors.is_valid():
            return None

        # Cooldown to avoid spam
        if self.escape_cooldown > 0:
            self.escape_cooldown -= 1
            return None

        # Need enough history
        if len(self.memory.actions) < 6:
            return None

        # Check for loop using memory
        if not self.memory.detect_loop():
            return None

        # Loop detected - escape
        self.escape_cooldown = 10

        analysis = SensorEvaluator.analyze(sensors)
        front = analysis['front']
        max_left = analysis['max_left']
        max_right = analysis['max_right']
        max_all = analysis['max_all']

        # Choose escape direction
        if analysis['can_advance'] and front >= max_all * 0.4:
            action = Action.FORWARD
            escape = "forward"
        elif analysis['can_turn_right'] and max_right >= max_left:
            action = Action.TURN_RIGHT
            escape = "right"
        elif analysis['can_turn_left']:
            action = Action.TURN_LEFT
            escape = "left"
        else:
            action = Action.BACKWARD
            escape = "backward"

        # Clear recent history to break loop
        self.memory.actions = self.memory.actions[-5:]

        score = Score.calculate("IMPORTANT", 0.7)

        return Decision(
            action=action,
            speed=RobotConfig.SPEED_SLOW,
            reason=f"LOOP: escaping {escape}",
            score=score
        )

    def reset(self):
        self.escape_cooldown = 0


class DeadEndNode(Node):
    """
    Dead-end avoidance - don't go into known dead-ends.

    Uses memory to track dead-end cells.
    Avoids returning to marked dead-ends.

    Priority: 8
    Score: NORMAL (50-69)
    """

    # Cardinal direction deltas
    DELTAS = {0: (1, 0), 90: (0, 1), 180: (-1, 0), 270: (0, -1)}

    def __init__(self, memory: NavigationMemory):
        super().__init__("DEAD_END", priority=8)
        self.memory = memory

    def evaluate(self, sensors: SensorData) -> Optional[Decision]:
        if not sensors.is_valid():
            return None

        # Get current position from odometry
        x, y, angle = self.memory.get_estimated_position()
        cell_x, cell_y = int(round(x / self.memory.CELL_SIZE)), int(round(y / self.memory.CELL_SIZE))
        cardinal = int(angle) // 90 * 90

        # Calculate cell ahead
        dx, dy = self.DELTAS.get(cardinal, (1, 0))
        front_cell = (cell_x + dx, cell_y + dy)

        # Check if front cell is dead-end
        if not self.memory.is_dead_end(front_cell):
            return None

        # Front is dead-end - find alternative
        analysis = SensorEvaluator.analyze(sensors)

        # Check left and right cells
        right_cardinal = (cardinal + 90) % 360
        left_cardinal = (cardinal - 90) % 360

        dx_r, dy_r = self.DELTAS.get(right_cardinal, (0, 1))
        dx_l, dy_l = self.DELTAS.get(left_cardinal, (0, -1))

        right_cell = (cell_x + dx_r, cell_y + dy_r)
        left_cell = (cell_x + dx_l, cell_y + dy_l)

        right_ok = (not self.memory.is_dead_end(right_cell) and
                    analysis['can_turn_right'])
        left_ok = (not self.memory.is_dead_end(left_cell) and
                   analysis['can_turn_left'])

        score = Score.calculate("NORMAL", 0.6)

        if right_ok and (not left_ok or analysis['max_right'] >= analysis['max_left']):
            return Decision(
                action=Action.TURN_RIGHT,
                speed=RobotConfig.SPEED_SLOW,
                reason="DEAD_END: avoiding front, going right",
                score=score
            )
        elif left_ok:
            return Decision(
                action=Action.TURN_LEFT,
                speed=RobotConfig.SPEED_SLOW,
                reason="DEAD_END: avoiding front, going left",
                score=score
            )
        else:
            return Decision(
                action=Action.BACKWARD,
                speed=RobotConfig.SPEED_VERY_SLOW,
                reason="DEAD_END: all blocked, backing up",
                score=Score.calculate("NORMAL", 0.4)
            )


class HistoryNode(Node):
    """
    History-based exploration - favor less visited directions.

    Uses visit counts to prefer unexplored areas.
    Only activates when multiple viable options exist.

    Priority: 9 (low - exploration preference)
    Score: LOW (30-49)
    """

    DELTAS = {0: (1, 0), 90: (0, 1), 180: (-1, 0), 270: (0, -1)}

    def __init__(self, memory: NavigationMemory):
        super().__init__("HISTORY", priority=9)
        self.memory = memory

    def evaluate(self, sensors: SensorData) -> Optional[Decision]:
        if not sensors.is_valid():
            return None

        analysis = SensorEvaluator.analyze(sensors)

        # Get current position
        x, y, angle = self.memory.get_estimated_position()
        cell_x, cell_y = int(round(x / self.memory.CELL_SIZE)), int(round(y / self.memory.CELL_SIZE))
        cardinal = int(angle) // 90 * 90

        options = []

        # Evaluate forward
        if analysis['can_advance']:
            dx, dy = self.DELTAS.get(cardinal, (1, 0))
            target = (cell_x + dx, cell_y + dy)
            if not self.memory.is_dead_end(target):
                visits = self.memory.visits.get(target, 0)
                options.append(('forward', Action.FORWARD, visits, analysis['front']))

        # Evaluate right
        if analysis['can_turn_right']:
            right_cardinal = (cardinal + 90) % 360
            dx, dy = self.DELTAS.get(right_cardinal, (0, 1))
            target = (cell_x + dx, cell_y + dy)
            if not self.memory.is_dead_end(target):
                visits = self.memory.visits.get(target, 0)
                options.append(('right', Action.TURN_RIGHT, visits, analysis['max_right']))

        # Evaluate left
        if analysis['can_turn_left']:
            left_cardinal = (cardinal - 90) % 360
            dx, dy = self.DELTAS.get(left_cardinal, (0, -1))
            target = (cell_x + dx, cell_y + dy)
            if not self.memory.is_dead_end(target):
                visits = self.memory.visits.get(target, 0)
                options.append(('left', Action.TURN_LEFT, visits, analysis['max_left']))

        if len(options) < 2:
            return None

        # Sort by visits (fewer = better), then by space
        options.sort(key=lambda x: (x[2], -x[3]))

        best = options[0]
        second = options[1]

        # Only decide if significant difference in visits
        if best[2] < second[2]:
            name, action, visits, space = best
            speed = RobotConfig.SPEED_NORMAL if space >= 1.0 else RobotConfig.SPEED_SLOW

            # Score based on visit difference
            visit_diff = second[2] - best[2]
            intensity = min(0.5 + visit_diff * 0.1, 1.0)
            score = Score.calculate("LOW", intensity)

            return Decision(
                action=action,
                speed=speed,
                reason=f"HISTORY: {name} less visited ({visits}x)",
                score=score
            )

        return None
