"""
NanoBot Nodes - Robot behaviors

Node Priority Guide:
- Priority 0-10: Safety/Emergency (CornerTrappedNode, WallAheadNode)
- Priority 10-20: Physical (FrictionNode, ScanNode)
- Priority 20-30: Memory (LoopNode, DeadEndNode)
- Priority 30-50: Navigation (NavigationNode, ExplorerNode)
- Priority 50+: Low priority (CorridorNode, HistoryNode)

New Architecture (inspired by robot/nodes):
- SensorEvaluator: Centralized sensor analysis with Pythagore
- NavigationMemory: Odometry, visit tracking, dead-ends
- Score system: URGENT/CRITICAL/IMPORTANT/NORMAL/LOW/DEFAULT
"""

# Legacy nodes
from .safety import SafetyNode
from .navigation import NavigationNode
from .explorer import ExplorerNode
from .pathfinding import PathfindingNode, GridMap, astar
from .wall_follower import WallFollowerNode, LeftWallFollowerNode, RightWallFollowerNode, PIDController
from .exploration import ExplorationNode, ExplorationMap

# New nodes (lite version inspired by robot/nodes)
from .base import SensorEvaluator, NavigationMemory
from .physiques import (
    WallAheadNode,
    CornerTrappedNode,
    OscillationNode,
    CorridorNode,
    FrictionNode,
)
from .scan import ScanNode
from .memory import LoopNode, DeadEndNode, HistoryNode

__all__ = [
    # Base utilities
    'SensorEvaluator',
    'NavigationMemory',

    # Physical nodes (high priority)
    'CornerTrappedNode',   # Priority 1 - corner escape
    'WallAheadNode',       # Priority 2 - wall ahead
    'OscillationNode',     # Priority 3 - zigzag detection
    'FrictionNode',        # Priority 4 - wall friction
    'ScanNode',            # Priority 5 - intersection scan

    # Memory nodes (medium priority)
    'LoopNode',            # Priority 6 - loop detection
    'DeadEndNode',         # Priority 8 - dead-end avoidance
    'HistoryNode',         # Priority 9 - exploration history

    # Legacy nodes
    'SafetyNode',
    'NavigationNode',
    'ExplorerNode',
    'PathfindingNode',
    'WallFollowerNode',
    'LeftWallFollowerNode',
    'RightWallFollowerNode',
    'ExplorationNode',

    # Low priority
    'CorridorNode',        # Priority 50 - corridor acceleration

    # Utilities
    'GridMap',
    'ExplorationMap',
    'PIDController',
    'astar',
]
