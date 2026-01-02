# NanoBot

Minimalist robot navigation framework using **cascading decision nodes**.

For **NVIDIA Jetson** robots (Nano, Orin, Xavier, TX2) - Python 3.6+

## Principle

Nodes execute in cascade by priority. First to return a decision wins.

```
SafetyNode (0)      -> Avoid collisions
NavigationNode (10) -> Handle turns
ExplorerNode (50)   -> Move forward
```

## Install

```bash
pip install nanobot
```

## Quick Start

```python
from nanobot import NodeEngine, SensorData
from nanobot.nodes import SafetyNode, NavigationNode, ExplorerNode

engine = NodeEngine()
engine.add_node(SafetyNode())
engine.add_node(NavigationNode())
engine.add_node(ExplorerNode())

while True:
    sensors = SensorData(front=1.5, left=0.8, right=0.6)
    decision = engine.tick(sensors)
    if decision:
        robot.execute(decision.action, decision.speed)
```

## CLI

```bash
python -m nanobot                    # Local simulation
python -m nanobot -s 192.168.1.1:8777  # Connect to server
```

## Custom Node

```python
from nanobot.core import Node, Decision, Action

class MyNode(Node):
    def __init__(self):
        super().__init__("MY_NODE", priority=25)

    def evaluate(self, sensors):
        if sensors.front < 0.5:
            return Decision(Action.STOP, 0.0, "Too close")
        return None  # Pass to next node
```

## Available Nodes

- `SafetyNode` (0) - Collision avoidance
- `NavigationNode` (10) - Turn handling
- `PathfindingNode` (20) - A* navigation
- `WallFollowerNode` (30) - Wall following with PID
- `ExplorationNode` (40) - Frontier exploration
- `ExplorerNode` (50) - Basic forward movement

## Actions

`FORWARD`, `BACKWARD`, `TURN_LEFT`, `TURN_RIGHT`, `STOP`

## License

MIT
