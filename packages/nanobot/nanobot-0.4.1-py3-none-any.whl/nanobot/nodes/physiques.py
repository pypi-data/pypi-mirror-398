"""
Physical navigation nodes - PYTHAGORE based

Re-exports from physique/ folder for backwards compatibility.
See physique/__init__.py for the actual node implementations.
"""

# Import from physique folder
from .physique import (
    StuckNode,
    WallNode,
    FrictionNode,
    CornerNode,
    IntersectionNode,
    ForwardNode,
)

# Aliases for compatibility
CornerTrappedNode = StuckNode
CorridorNode = ForwardNode
ExploreNode = ForwardNode
NavigateNode = ForwardNode
EscapeNode = StuckNode
SimpleNav = ForwardNode
WallAheadNode = WallNode
OscillationNode = StuckNode
SecureNav = WallNode

# Export all
__all__ = [
    # Main nodes
    "StuckNode",
    "WallNode",
    "FrictionNode",
    "CornerNode",
    "IntersectionNode",
    "ForwardNode",
    # Aliases
    "CorridorNode",
    "ExploreNode",
    "NavigateNode",
    "EscapeNode",
    "SimpleNav",
    "WallAheadNode",
    "CornerTrappedNode",
    "OscillationNode",
    "SecureNav",
]
