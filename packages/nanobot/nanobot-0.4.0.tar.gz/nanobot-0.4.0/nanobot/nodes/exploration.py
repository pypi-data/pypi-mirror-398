"""
Exploration Node - Systematic mapping and exploration

Implements frontier-based exploration:
1. Maintains an occupancy grid map
2. Identifies frontiers (boundaries between known and unknown space)
3. Navigates to frontiers to explore new areas
4. Continues until map is complete
"""

import math
import random
from typing import Optional, List, Tuple, Set
from ..core import Node, Decision, Action, SensorData
from .pathfinding import GridMap, astar


class ExplorationMap(GridMap):
    """
    Extended grid map with exploration tracking.

    Cell values:
    - 0: Unknown
    - 1: Free (explored)
    - 2: Obstacle
    - 3: Frontier (boundary between known and unknown)
    """

    def __init__(self, width: int = 100, height: int = 100, resolution: float = 0.1):
        super().__init__(width, height, resolution)
        self.explored_cells = 0
        self.total_explorable = width * height

    def get_frontiers(self) -> List[Tuple[int, int]]:
        """
        Find all frontier cells.

        A frontier is a free cell adjacent to at least one unknown cell.
        """
        frontiers = []

        for y in range(1, self.height - 1):
            for x in range(1, self.width - 1):
                if self.grid[y][x] == 1:  # Free cell
                    # Check if adjacent to unknown
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nx, ny = x + dx, y + dy
                        if self.grid[ny][nx] == 0:  # Unknown
                            frontiers.append((x, y))
                            break

        return frontiers

    def get_frontier_clusters(self, min_size: int = 3) -> List[List[Tuple[int, int]]]:
        """
        Group frontiers into clusters.

        Returns clusters sorted by size (largest first).
        """
        frontiers = set(self.get_frontiers())
        clusters = []
        visited = set()  # type: Set[Tuple[int, int]]

        for frontier in frontiers:
            if frontier in visited:
                continue

            # BFS to find cluster
            cluster = []
            queue = [frontier]

            while queue:
                cell = queue.pop(0)
                if cell in visited:
                    continue
                if cell not in frontiers:
                    continue

                visited.add(cell)
                cluster.append(cell)

                # Add neighbors
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
                    neighbor = (cell[0] + dx, cell[1] + dy)
                    if neighbor not in visited and neighbor in frontiers:
                        queue.append(neighbor)

            if len(cluster) >= min_size:
                clusters.append(cluster)

        # Sort by size (largest first)
        clusters.sort(key=len, reverse=True)
        return clusters

    def get_exploration_progress(self) -> float:
        """
        Get exploration progress as percentage.

        Returns value between 0.0 and 1.0.
        """
        known = 0
        for row in self.grid:
            for cell in row:
                if cell != 0:  # Not unknown
                    known += 1
        return known / self.total_explorable

    def get_centroid(self, cells: List[Tuple[int, int]]) -> Tuple[int, int]:
        """Get centroid of a list of cells."""
        if not cells:
            return (self.width // 2, self.height // 2)

        cx = sum(c[0] for c in cells) // len(cells)
        cy = sum(c[1] for c in cells) // len(cells)
        return (cx, cy)


class ExplorationNode(Node):
    """
    Frontier-based exploration node.

    Systematically explores unknown space by navigating to frontiers.
    """

    def __init__(self, priority: int = 40):
        super().__init__("EXPLORATION", priority)
        self.map = ExplorationMap()

        # Robot state (should be updated externally)
        self.robot_x = 0.0
        self.robot_y = 0.0
        self.robot_angle = 0.0

        # Current target frontier
        self.target = None  # type: Optional[Tuple[int, int]]
        self.path = None  # type: Optional[List[Tuple[int, int]]]
        self.path_index = 0

        # State
        self.active = False
        self.exploration_complete = False
        self.stuck_count = 0

        # Parameters
        self.waypoint_threshold = 0.2
        self.angle_threshold = 0.4
        self.replan_interval = 20  # Ticks between replanning
        self.ticks_since_replan = 0

    def start(self):
        """Start exploration."""
        self.active = True
        self.exploration_complete = False
        self.target = None
        self.path = None

    def stop(self):
        """Stop exploration."""
        self.active = False

    def is_active(self) -> bool:
        return self.active

    def is_complete(self) -> bool:
        return self.exploration_complete

    def get_progress(self) -> float:
        """Get exploration progress (0.0 to 1.0)."""
        return self.map.get_exploration_progress()

    def update_odometry(self, x: float, y: float, angle: float):
        """Update robot position."""
        self.robot_x = x
        self.robot_y = y
        self.robot_angle = angle

    def get_map(self) -> ExplorationMap:
        """Get the exploration map."""
        return self.map

    def _select_frontier(self) -> Optional[Tuple[int, int]]:
        """Select the best frontier to explore."""
        clusters = self.map.get_frontier_clusters(min_size=2)

        if not clusters:
            return None

        robot_grid = self.map.world_to_grid(self.robot_x, self.robot_y)

        # Score each cluster by: size * 0.5 + 1/distance * 0.5
        best_score = -1
        best_target = None

        for cluster in clusters[:5]:  # Consider top 5 largest clusters
            centroid = self.map.get_centroid(cluster)

            # Distance to centroid
            dist = math.sqrt(
                (robot_grid[0] - centroid[0])**2 +
                (robot_grid[1] - centroid[1])**2
            )

            # Score: balance between size and proximity
            size_score = len(cluster) / 100.0
            dist_score = 1.0 / (dist + 1)
            score = size_score * 0.4 + dist_score * 0.6

            if score > best_score:
                best_score = score
                # Find closest cell in cluster to robot
                best_target = min(cluster, key=lambda c:
                    (c[0] - robot_grid[0])**2 + (c[1] - robot_grid[1])**2
                )

        return best_target

    def evaluate(self, sensors: SensorData) -> Optional[Decision]:
        if not self.active:
            return None

        # Update map from sensors
        self.map.update_from_sensors(
            sensors, self.robot_x, self.robot_y, self.robot_angle
        )

        self.ticks_since_replan += 1

        # Check if exploration is complete
        frontiers = self.map.get_frontiers()
        if not frontiers:
            progress = self.get_progress()
            if progress > 0.1:  # At least 10% explored
                self.exploration_complete = True
                self.active = False
                return Decision(Action.STOP, 0.0, f"Exploration complete ({progress*100:.1f}%)")

        # Select or replan target
        if self.target is None or self.ticks_since_replan > self.replan_interval:
            self.target = self._select_frontier()
            self.path = None
            self.ticks_since_replan = 0

            if self.target is None:
                # No frontiers reachable, try random movement
                self.stuck_count += 1
                if self.stuck_count > 5:
                    return Decision(Action.TURN_LEFT, 0.4, "No frontiers, rotating")
                return Decision(Action.FORWARD, 0.3, "Searching for frontiers")

        self.stuck_count = 0

        # Plan path to target
        if self.path is None:
            start = self.map.world_to_grid(self.robot_x, self.robot_y)
            self.path = astar(self.map, start, self.target)
            self.path_index = 0

            if self.path is None:
                self.target = None  # Will reselect next tick
                return Decision(Action.TURN_RIGHT, 0.3, "Path blocked, replanning")

        # Navigate along path
        if self.path_index >= len(self.path):
            self.target = None
            self.path = None
            return None

        waypoint = self.path[self.path_index]
        wp_world = self.map.grid_to_world(waypoint[0], waypoint[1])

        # Check if reached waypoint
        dist_to_wp = math.sqrt(
            (self.robot_x - wp_world[0])**2 +
            (self.robot_y - wp_world[1])**2
        )

        if dist_to_wp < self.waypoint_threshold:
            self.path_index += 1
            if self.path_index >= len(self.path):
                self.target = None
                self.path = None
            return None

        # Calculate angle to waypoint
        target_angle = math.atan2(
            wp_world[1] - self.robot_y,
            wp_world[0] - self.robot_x
        )
        angle_diff = target_angle - self.robot_angle

        # Normalize
        while angle_diff > math.pi:
            angle_diff -= 2 * math.pi
        while angle_diff < -math.pi:
            angle_diff += 2 * math.pi

        # Turn if needed
        if abs(angle_diff) > self.angle_threshold:
            if angle_diff > 0:
                return Decision(Action.TURN_LEFT, 0.4, "Turning to waypoint")
            else:
                return Decision(Action.TURN_RIGHT, 0.4, "Turning to waypoint")

        # Move forward
        progress = self.get_progress()
        return Decision(
            Action.FORWARD, 0.5,
            f"Exploring ({progress*100:.1f}% mapped)"
        )

    def reset(self):
        """Reset exploration state."""
        self.map = ExplorationMap()
        self.target = None
        self.path = None
        self.path_index = 0
        self.active = False
        self.exploration_complete = False
        self.stuck_count = 0
        self.ticks_since_replan = 0
