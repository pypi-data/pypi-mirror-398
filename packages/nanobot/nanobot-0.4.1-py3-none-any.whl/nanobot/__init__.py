"""
NanoBot - Minimalist robot navigation framework

Simple architecture using cascading decision nodes:
1. SafetyNode (priority 0) - Collision avoidance
2. NavigationNode (priority 10) - Handle turns
3. ExplorerNode (priority 50) - Move forward when safe

Usage:
    from nanobot import NodeEngine, SensorData
    from nanobot.nodes import SafetyNode, NavigationNode, ExplorerNode

    engine = NodeEngine(debug=True)
    engine.add_node(SafetyNode())
    engine.add_node(NavigationNode())
    engine.add_node(ExplorerNode())

    # Main loop:
    sensors = SensorData(front=1.5, left=0.8, right=0.6)
    decision = engine.tick(sensors)
    if decision:
        robot.execute(decision.action, decision.speed)
"""

from .core import Node, Action, Decision, NodeEngine, SensorData
from .config import RobotConfig
from .async_engine import AsyncNodeEngine, SensorThread, DecisionExecutor

__version__ = "0.3.5"
__all__ = [
    'Node', 'Action', 'Decision',
    'NodeEngine', 'SensorData',
    'RobotConfig',
    'AsyncNodeEngine', 'SensorThread', 'DecisionExecutor'
]
