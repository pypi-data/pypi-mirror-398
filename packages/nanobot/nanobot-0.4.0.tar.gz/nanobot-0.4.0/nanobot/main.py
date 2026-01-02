#!/usr/bin/env python3
"""
NanoBot - Main entry point

Usage:
    python nanobot/main.py                    # Simulation mode
    python nanobot/main.py --server HOST:PORT # Server connection mode
    python nanobot/main.py --test             # Test nodes
    python nanobot/main.py --mode enhanced    # Use enhanced nodes
"""

import argparse
import time
import sys
import os

# Auto-fix path for direct execution
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

from nanobot.core import NodeEngine, SensorData, Action

# Navigation nodes
from nanobot.nodes.physiques import (
    StuckNode,
    WallNode,
    CornerNode,
    IntersectionNode,
    ForwardNode,
)


def create_engine_legacy(debug: bool = False) -> NodeEngine:
    """Create engine with simple navigation nodes."""
    engine = NodeEngine(debug=debug)
    engine.add_node(StuckNode())     # Priority 0 - escape from corners
    engine.add_node(WallNode())      # Priority 1 - turn when wall ahead
    engine.add_node(ForwardNode())   # Priority 3 - default forward
    return engine


def create_engine_enhanced(debug: bool = False) -> NodeEngine:
    """
    Create engine with full navigation.

    Order matters (first to decide wins):
    1. StuckNode (priority 0): escape when all blocked
    2. WallNode: react to danger (front blocked or side critical)
    3. IntersectionNode: explore open passages
    4. ForwardNode: default forward
    """
    engine = NodeEngine(debug=debug)
    engine.add_node(StuckNode())         # Has priority 0 - always first
    engine.add_node(WallNode())          # Stateless - danger reaction
    engine.add_node(IntersectionNode())  # Stateless - explore passages
    engine.add_node(ForwardNode())       # Stateless - default forward
    return engine


def create_engine(mode: str = "enhanced", debug: bool = False) -> NodeEngine:
    """
    Create engine with specified mode.

    Args:
        mode: "legacy" or "enhanced"
        debug: Enable debug output
    """
    if mode == "legacy":
        return create_engine_legacy(debug)
    else:
        return create_engine_enhanced(debug)


def run_simulation(engine: NodeEngine):
    """Simulation mode - test with mock data."""
    print("=== NanoBot Simulation ===")
    print(f"Nodes: {engine}")
    print()

    # Test scenarios
    scenarios = [
        ("Clear path", SensorData(front=2.0, left=1.0, right=1.0)),
        ("Wall ahead", SensorData(front=0.2, left=1.0, right=1.0)),
        ("Right angle", SensorData(front=1.5, left=1.0, right=0.2)),
        ("Left angle", SensorData(front=1.5, left=0.2, right=1.0)),
        ("Narrow corridor", SensorData(front=2.0, left=0.3, right=0.3)),
        ("Stuck", SensorData(front=0.2, left=0.2, right=0.2)),
        ("Intersection L", SensorData(front=0.5, left=2.0, right=0.5,
                                       left_front=1.5, right_front=0.4)),
        ("Intersection R", SensorData(front=0.5, left=0.5, right=2.0,
                                       left_front=0.4, right_front=1.5)),
    ]

    for name, sensors in scenarios:
        decision = engine.tick(sensors)
        print(f"{name:15} | {sensors} -> {decision}")

    print()
    print("Simulation complete.")


def run_server_mode(engine: NodeEngine, server: str):
    """Server mode - connect to maze-server."""
    if not HAS_REQUESTS:
        print("ERROR: requests module required. Install with: pip install requests")
        sys.exit(1)

    print(f"=== NanoBot Server Mode ===", flush=True)
    print(f"Connecting to: {server}", flush=True)
    print(f"Nodes: {engine}", flush=True)
    print(flush=True)

    base_url = f"http://{server}"
    tick_interval = 0.05  # 50ms between ticks

    # Session HTTP persistante (reuses TCP connection)
    session = requests.Session()
    # Connection pooling for better reuse
    adapter = requests.adapters.HTTPAdapter(
        pool_connections=1,
        pool_maxsize=1,
        max_retries=0  # No retries, we handle manually
    )
    session.mount('http://', adapter)

    # Get memory reference if using enhanced engine
    memory = getattr(engine, '_memory', None)

    timeout_count = 0
    last_decision = None

    while True:
        try:
            # 1. Get sensors (WiFi needs longer timeout)
            resp = session.get(f"{base_url}/sensors", timeout=0.5)
            if resp.status_code != 200:
                print(f"Sensors error: {resp.status_code}", flush=True)
                time.sleep(0.1)
                continue

            data = resp.json()
            sensors = SensorData.from_dict(data)
            timeout_count = 0  # Reset on success

            # 2. Evaluate with engine
            decision = engine.tick(sensors)

            # DEBUG: Print sensor values when no decision
            if not decision:
                print(f"[{engine.tick_count}] NO DECISION! sensors: F={sensors.front:.2f} L={sensors.left:.2f} R={sensors.right:.2f}", flush=True)

            if decision:
                # 3. Send command (fire and forget style - short timeout)
                action_name = decision.action.name.lower()
                cmd = {
                    "action": action_name,
                    "speed": decision.speed
                }

                try:
                    session.post(f"{base_url}/command", json=cmd, timeout=0.3)
                except requests.exceptions.Timeout:
                    pass  # Command sent, don't wait for response

                # 4. Record action in memory for loop/dead-end tracking
                if memory:
                    memory.record_action(action_name, decision.speed)

                if engine.debug:
                    print(f"[{engine.tick_count}] {decision}", flush=True)

                last_decision = decision

            time.sleep(tick_interval)

        except requests.exceptions.Timeout:
            timeout_count += 1
            if timeout_count % 20 == 1:  # Print less often
                print(f"Timeout x{timeout_count}, retrying...")
            time.sleep(0.1)  # Wait before retry
        except requests.exceptions.ConnectionError:
            print("Connection lost, retrying...")
            time.sleep(0.5)
        except KeyboardInterrupt:
            print("\nStopping...")
            try:
                session.post(f"{base_url}/command",
                    json={"action": "stop", "speed": 0}, timeout=0.5)
            except:
                pass
            session.close()
            break


def run_tests(engine: NodeEngine):
    """Test mode - verify node behavior."""
    print("=== NanoBot Tests ===")
    print()

    tests_passed = 0
    tests_failed = 0

    def test(name: str, sensors: SensorData, expected_action: Action):
        nonlocal tests_passed, tests_failed
        engine.reset()
        decision = engine.tick(sensors)

        if decision and decision.action == expected_action:
            print(f"[PASS] {name}")
            tests_passed += 1
        else:
            actual = decision.action if decision else "None"
            print(f"[FAIL] {name}: expected {expected_action.name}, got {actual}")
            tests_failed += 1

    # Safety tests
    test("Safety: front blocked -> turn",
         SensorData(front=0.2, left=1.0, right=0.5),
         Action.TURN_LEFT)

    test("Safety: front blocked, right has space -> turn right",
         SensorData(front=0.2, left=0.5, right=1.0),
         Action.TURN_RIGHT)

    test("Safety: all blocked -> backward",
         SensorData(front=0.2, left=0.2, right=0.2),
         Action.BACKWARD)

    # Navigation tests
    test("Navigation: angle right -> turn left",
         SensorData(front=1.5, left=1.0, right=0.25),
         Action.TURN_LEFT)

    test("Navigation: angle left -> turn right",
         SensorData(front=1.5, left=0.25, right=1.0),
         Action.TURN_RIGHT)

    # Explorer tests
    test("Explorer: clear path -> forward",
         SensorData(front=3.0, left=1.0, right=1.0),
         Action.FORWARD)

    print()
    print(f"Results: {tests_passed} passed, {tests_failed} failed")

    return tests_failed == 0


def main():
    parser = argparse.ArgumentParser(
        description="NanoBot - Robot navigation framework"
    )
    parser.add_argument(
        "--server", "-s",
        help="Server address (HOST:PORT)"
    )
    parser.add_argument(
        "--test", "-t",
        action="store_true",
        help="Run tests"
    )
    parser.add_argument(
        "--debug", "-d",
        action="store_true",
        help="Enable debug output"
    )
    parser.add_argument(
        "--mode", "-m",
        choices=["legacy", "enhanced"],
        default="enhanced",
        help="Engine mode: legacy (basic) or enhanced (new nodes)"
    )

    args = parser.parse_args()

    engine = create_engine(mode=args.mode, debug=args.debug)

    if args.test:
        success = run_tests(engine)
        sys.exit(0 if success else 1)
    elif args.server:
        run_server_mode(engine, args.server)
    else:
        run_simulation(engine)


if __name__ == "__main__":
    main()
