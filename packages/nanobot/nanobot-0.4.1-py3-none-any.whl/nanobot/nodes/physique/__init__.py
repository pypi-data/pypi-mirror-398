"""
Physical navigation nodes - PYTHAGORE based

NODES (by priority):
0. StuckNode - Corner stuck → BACKUP + ESCAPE
1. WallNode - Front blocked → TURN toward max sensor
2. FrictionNode - Wall friction → TURN away (uses DIAG_CHASSIS)
2. CornerNode - Exterior corner detected → TURN toward it
2. IntersectionNode - Side passage detected → TURN toward it
3. ForwardNode - Default → FORWARD

Each node uses Pythagore chassis geometry for decisions.
"""

from .stuck import StuckNode
from .wall import WallNode
from .friction import FrictionNode
from .corner import CornerNode
from .intersection import IntersectionNode
from .forward import ForwardNode

__all__ = [
    "StuckNode",
    "WallNode",
    "FrictionNode",
    "CornerNode",
    "IntersectionNode",
    "ForwardNode",
]
