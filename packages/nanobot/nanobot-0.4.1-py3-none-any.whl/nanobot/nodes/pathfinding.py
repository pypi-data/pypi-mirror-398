"""
Pathfinding Node - A* algorithm for goal-directed navigation

Uses an internal grid map to find optimal paths to target positions.
"""

import heapq
import math
from typing import Optional, List, Tuple, Set, Dict
from ..core import Node, Decision, Action, SensorData


class GridMap:
    """
    Simple 2D occupancy grid for pathfinding.

    Cells can be:
    - 0: Unknown
    - 1: Free
    - 2: Obstacle
    """

    def __init__(self, width: int = 100, height: int = 100, resolution: float = 0.1):
        """
        Args:
            width: Grid width in cells
            height: Grid height in cells
            resolution: Meters per cell
        """
        self.width = width
        self.height = height
        self.resolution = resolution
        self.grid = [[0 for _ in range(width)] for _ in range(height)]

        # Robot position in grid coordinates
        self.robot_x = width // 2
        self.robot_y = height // 2
        self.robot_angle = 0.0  # radians, 0 = facing +X

    def world_to_grid(self, wx: float, wy: float) -> Tuple[int, int]:
        """Convert world coordinates to grid coordinates."""
        gx = int(wx / self.resolution) + self.width // 2
        gy = int(wy / self.resolution) + self.height // 2
        return (max(0, min(self.width - 1, gx)),
                max(0, min(self.height - 1, gy)))

    def grid_to_world(self, gx: int, gy: int) -> Tuple[float, float]:
        """Convert grid coordinates to world coordinates."""
        wx = (gx - self.width // 2) * self.resolution
        wy = (gy - self.height // 2) * self.resolution
        return (wx, wy)

    def set_obstacle(self, gx: int, gy: int):
        """Mark cell as obstacle."""
        if 0 <= gx < self.width and 0 <= gy < self.height:
            self.grid[gy][gx] = 2

    def set_free(self, gx: int, gy: int):
        """Mark cell as free."""
        if 0 <= gx < self.width and 0 <= gy < self.height:
            self.grid[gy][gx] = 1

    def is_free(self, gx: int, gy: int) -> bool:
        """Check if cell is traversable."""
        if 0 <= gx < self.width and 0 <= gy < self.height:
            return self.grid[gy][gx] != 2
        return False

    def is_obstacle(self, gx: int, gy: int) -> bool:
        """Check if cell is an obstacle."""
        if 0 <= gx < self.width and 0 <= gy < self.height:
            return self.grid[gy][gx] == 2
        return True  # Out of bounds = obstacle

    def update_from_sensors(self, sensors: SensorData, robot_x: float, robot_y: float, robot_angle: float):
        """Update map from sensor readings."""
        self.robot_x, self.robot_y = self.world_to_grid(robot_x, robot_y)
        self.robot_angle = robot_angle

        # Mark robot position as free
        self.set_free(self.robot_x, self.robot_y)

        # Update from front sensor
        if sensors.front is not None and sensors.front < 5.0:
            self._update_ray(robot_x, robot_y, robot_angle, sensors.front)

        # Update from left sensor
        if sensors.left is not None and sensors.left < 5.0:
            self._update_ray(robot_x, robot_y, robot_angle + math.pi/2, sensors.left)

        # Update from right sensor
        if sensors.right is not None and sensors.right < 5.0:
            self._update_ray(robot_x, robot_y, robot_angle - math.pi/2, sensors.right)

    def _update_ray(self, start_x: float, start_y: float, angle: float, distance: float):
        """Update map along a sensor ray."""
        # Mark free cells along the ray
        steps = int(distance / self.resolution)
        for i in range(steps):
            d = i * self.resolution
            wx = start_x + d * math.cos(angle)
            wy = start_y + d * math.sin(angle)
            gx, gy = self.world_to_grid(wx, wy)
            self.set_free(gx, gy)

        # Mark obstacle at end of ray (if not max range)
        if distance < 4.9:
            ox = start_x + distance * math.cos(angle)
            oy = start_y + distance * math.sin(angle)
            gx, gy = self.world_to_grid(ox, oy)
            self.set_obstacle(gx, gy)

    def get_neighbors(self, gx: int, gy: int) -> List[Tuple[int, int]]:
        """Get traversable neighbor cells (8-connected)."""
        neighbors = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = gx + dx, gy + dy
                if self.is_free(nx, ny):
                    neighbors.append((nx, ny))
        return neighbors


def heuristic(a: Tuple[int, int], b: Tuple[int, int]) -> float:
    """Euclidean distance heuristic."""
    return math.sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2)


def astar(grid_map: GridMap, start: Tuple[int, int], goal: Tuple[int, int]) -> Optional[List[Tuple[int, int]]]:
    """
    A* pathfinding algorithm.

    Args:
        grid_map: The occupancy grid
        start: Start position (gx, gy)
        goal: Goal position (gx, gy)

    Returns:
        List of grid positions from start to goal, or None if no path
    """
    if not grid_map.is_free(goal[0], goal[1]):
        return None

    open_set = []
    heapq.heappush(open_set, (0, start))

    came_from = {}  # type: Dict[Tuple[int, int], Tuple[int, int]]
    g_score = {start: 0}  # type: Dict[Tuple[int, int], float]
    f_score = {start: heuristic(start, goal)}  # type: Dict[Tuple[int, int], float]

    open_set_hash = {start}  # type: Set[Tuple[int, int]]

    while open_set:
        current = heapq.heappop(open_set)[1]
        open_set_hash.discard(current)

        if current == goal:
            # Reconstruct path
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            path.reverse()
            return path

        for neighbor in grid_map.get_neighbors(current[0], current[1]):
            # Cost: 1 for cardinal, sqrt(2) for diagonal
            dx = abs(neighbor[0] - current[0])
            dy = abs(neighbor[1] - current[1])
            move_cost = math.sqrt(dx*dx + dy*dy)

            tentative_g = g_score[current] + move_cost

            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f_score[neighbor] = tentative_g + heuristic(neighbor, goal)

                if neighbor not in open_set_hash:
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))
                    open_set_hash.add(neighbor)

    return None  # No path found


class PathfindingNode(Node):
    """
    A* pathfinding navigation node.

    Maintains an internal map and navigates to goal positions.
    """

    def __init__(self, priority: int = 20):
        super().__init__("PATHFINDING", priority)
        self.grid_map = GridMap()

        # Current goal in world coordinates
        self.goal_x = None  # type: Optional[float]
        self.goal_y = None  # type: Optional[float]

        # Current path (list of grid coords)
        self.path = None  # type: Optional[List[Tuple[int, int]]]
        self.path_index = 0

        # Robot odometry (should be updated externally)
        self.robot_x = 0.0
        self.robot_y = 0.0
        self.robot_angle = 0.0

        # Parameters
        self.waypoint_threshold = 0.15  # meters
        self.angle_threshold = 0.3  # radians (~17 degrees)

    def set_goal(self, x: float, y: float):
        """Set navigation goal in world coordinates."""
        self.goal_x = x
        self.goal_y = y
        self.path = None  # Force replan

    def clear_goal(self):
        """Clear current goal."""
        self.goal_x = None
        self.goal_y = None
        self.path = None

    def update_odometry(self, x: float, y: float, angle: float):
        """Update robot position (call this before tick)."""
        self.robot_x = x
        self.robot_y = y
        self.robot_angle = angle

    def has_goal(self) -> bool:
        """Check if a goal is set."""
        return self.goal_x is not None and self.goal_y is not None

    def evaluate(self, sensors: SensorData) -> Optional[Decision]:
        # No goal? Pass to next node
        if not self.has_goal():
            return None

        # Update map from sensors
        self.grid_map.update_from_sensors(
            sensors, self.robot_x, self.robot_y, self.robot_angle
        )

        # Check if we reached the goal
        dist_to_goal = math.sqrt(
            (self.robot_x - self.goal_x)**2 +
            (self.robot_y - self.goal_y)**2
        )
        if dist_to_goal < self.waypoint_threshold:
            self.clear_goal()
            return Decision(Action.STOP, 0.0, "Goal reached")

        # Plan path if needed
        if self.path is None:
            start = self.grid_map.world_to_grid(self.robot_x, self.robot_y)
            goal = self.grid_map.world_to_grid(self.goal_x, self.goal_y)
            self.path = astar(self.grid_map, start, goal)
            self.path_index = 0

            if self.path is None:
                return Decision(Action.STOP, 0.0, "No path found")

        # Get next waypoint
        if self.path_index >= len(self.path):
            self.path = None  # Replan
            return None

        waypoint = self.path[self.path_index]
        wp_world = self.grid_map.grid_to_world(waypoint[0], waypoint[1])

        # Check if we reached the waypoint
        dist_to_wp = math.sqrt(
            (self.robot_x - wp_world[0])**2 +
            (self.robot_y - wp_world[1])**2
        )
        if dist_to_wp < self.waypoint_threshold:
            self.path_index += 1
            return None  # Continue to next waypoint

        # Calculate angle to waypoint
        target_angle = math.atan2(
            wp_world[1] - self.robot_y,
            wp_world[0] - self.robot_x
        )
        angle_diff = target_angle - self.robot_angle

        # Normalize to [-pi, pi]
        while angle_diff > math.pi:
            angle_diff -= 2 * math.pi
        while angle_diff < -math.pi:
            angle_diff += 2 * math.pi

        # Turn if not facing waypoint
        if abs(angle_diff) > self.angle_threshold:
            if angle_diff > 0:
                return Decision(Action.TURN_LEFT, 0.4, f"Turn to waypoint ({angle_diff:.2f}rad)")
            else:
                return Decision(Action.TURN_RIGHT, 0.4, f"Turn to waypoint ({angle_diff:.2f}rad)")

        # Move forward
        speed = min(0.6, dist_to_wp)  # Slow down near waypoint
        return Decision(Action.FORWARD, speed, f"Moving to waypoint {self.path_index}/{len(self.path)}")

    def reset(self):
        """Reset node state."""
        self.goal_x = None
        self.goal_y = None
        self.path = None
        self.path_index = 0
        self.grid_map = GridMap()
