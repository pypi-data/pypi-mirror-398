"""
NodeEngine - Node execution engine

CORE PRINCIPLE:
    Nodes execute IN CASCADE by priority order.
    The FIRST node that returns a Decision wins.
    No voting, no scoring, no conflict.

HOW IT WORKS:
    1. Sort nodes by priority (0 = highest priority)
    2. For each node, call evaluate(sensors)
    3. If Decision returned -> STOP, execute this action
    4. If None returned -> move to next node

Simple. Deterministic. Predictable.
"""

from typing import List, Optional, Callable
from .node import Node, Decision, Action
from .sensors import SensorData


class NodeEngine:
    """
    Node execution engine.

    Usage:
        engine = NodeEngine()
        engine.add_node(SafetyNode())
        engine.add_node(NavigationNode())
        engine.add_node(ExplorerNode())

        decision = engine.tick(sensor_data)
        if decision:
            robot.execute(decision.action, decision.speed)
    """

    def __init__(self, debug: bool = False):
        self._nodes: List[Node] = []
        self._sorted = False
        self.debug = debug
        self.last_decision: Optional[Decision] = None
        self.last_node: Optional[str] = None
        self.tick_count = 0

        # Callback for logging decisions
        self._on_decision: Optional[Callable[[Decision, str], None]] = None

    def add_node(self, node: Node) -> 'NodeEngine':
        """Add a node to the engine. Returns self for chaining."""
        self._nodes.append(node)
        self._sorted = False
        return self

    def remove_node(self, name: str) -> bool:
        """Remove a node by name. Returns True if found."""
        for i, node in enumerate(self._nodes):
            if node.name == name:
                self._nodes.pop(i)
                return True
        return False

    def get_node(self, name: str) -> Optional[Node]:
        """Get a node by name."""
        for node in self._nodes:
            if node.name == name:
                return node
        return None

    def _ensure_sorted(self):
        """Sort nodes by priority if needed."""
        if not self._sorted:
            self._nodes.sort(key=lambda n: n.priority)
            self._sorted = True

    def tick(self, sensors: SensorData) -> Optional[Decision]:
        """
        Execute one tick of the engine.

        Args:
            sensors: Current sensor data

        Returns:
            Decision from the first node that decided, or None
        """
        self._ensure_sorted()
        self.tick_count += 1

        for node in self._nodes:
            try:
                decision = node.evaluate(sensors)

                if decision is not None:
                    # This node made a decision -> stop here
                    self.last_decision = decision
                    self.last_node = node.name

                    if self.debug:
                        print(f"[{self.tick_count}] {node.name}: {decision}")

                    if self._on_decision:
                        self._on_decision(decision, node.name)

                    return decision

            except Exception as e:
                # A crashing node should not block others
                if self.debug:
                    print(f"[{self.tick_count}] ERROR {node.name}: {e}")
                continue

        # No node made a decision
        self.last_decision = None
        self.last_node = None
        return None

    def reset(self):
        """Reset all nodes."""
        for node in self._nodes:
            node.reset()
        self.last_decision = None
        self.last_node = None
        self.tick_count = 0

    def on_decision(self, callback: Callable[[Decision, str], None]):
        """Register a callback called on each decision."""
        self._on_decision = callback

    def status(self) -> dict:
        """Return engine state for debugging."""
        self._ensure_sorted()
        return {
            "tick": self.tick_count,
            "nodes": [f"{n.name}(p={n.priority})" for n in self._nodes],
            "last_node": self.last_node,
            "last_decision": str(self.last_decision) if self.last_decision else None
        }

    def __repr__(self):
        self._ensure_sorted()
        nodes_str = ", ".join(n.name for n in self._nodes)
        return f"<NodeEngine [{nodes_str}]>"
