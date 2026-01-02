"""
Async Engine - Threaded node execution for real-time applications

Provides AsyncNodeEngine for non-blocking sensor reads and decision making.
Compatible with Python 3.6+.

Usage:
    from nanobot.async_engine import AsyncNodeEngine

    engine = AsyncNodeEngine(debug=True)
    engine.add_node(SafetyNode())
    engine.add_node(NavigationNode())

    # Start background processing
    engine.start(sensor_callback=my_sensor_read, tick_rate=10)

    # Get latest decision (non-blocking)
    decision = engine.get_decision()

    # Stop when done
    engine.stop()
"""

import threading
import time
from typing import Optional, Callable, List
from .core import Node, NodeEngine, SensorData, Decision


class AsyncNodeEngine:
    """
    Threaded wrapper around NodeEngine.

    Runs sensor reading and decision making in a background thread,
    allowing the main thread to remain responsive.
    """

    def __init__(self, debug: bool = False):
        """
        Args:
            debug: Enable debug output
        """
        self._engine = NodeEngine(debug=debug)
        self._thread = None  # type: Optional[threading.Thread]
        self._running = False
        self._lock = threading.Lock()

        # Latest values
        self._latest_sensors = None  # type: Optional[SensorData]
        self._latest_decision = None  # type: Optional[Decision]

        # Callbacks
        self._sensor_callback = None  # type: Optional[Callable[[], SensorData]]
        self._decision_callback = None  # type: Optional[Callable[[Decision], None]]

        # Stats
        self._tick_count = 0
        self._errors = 0

    def add_node(self, node: Node):
        """Add a node to the engine."""
        self._engine.add_node(node)

    def remove_node(self, name: str) -> bool:
        """Remove a node by name."""
        return self._engine.remove_node(name)

    @property
    def debug(self) -> bool:
        return self._engine.debug

    @debug.setter
    def debug(self, value: bool):
        self._engine.debug = value

    @property
    def tick_count(self) -> int:
        return self._tick_count

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self,
              sensor_callback: Callable[[], SensorData],
              tick_rate: float = 10.0,
              decision_callback: Optional[Callable[[Decision], None]] = None):
        """
        Start background processing.

        Args:
            sensor_callback: Function that returns SensorData
            tick_rate: Ticks per second (default 10 Hz)
            decision_callback: Optional callback when decision changes
        """
        if self._running:
            return

        self._sensor_callback = sensor_callback
        self._decision_callback = decision_callback
        self._running = True

        tick_interval = 1.0 / tick_rate

        def loop():
            while self._running:
                try:
                    # Read sensors
                    sensors = self._sensor_callback()

                    with self._lock:
                        self._latest_sensors = sensors

                    # Get decision
                    decision = self._engine.tick(sensors)

                    with self._lock:
                        self._latest_decision = decision
                        self._tick_count += 1

                    # Callback if provided
                    if decision and self._decision_callback:
                        try:
                            self._decision_callback(decision)
                        except Exception as e:
                            if self._engine.debug:
                                print(f"[ASYNC] Callback error: {e}")

                except Exception as e:
                    self._errors += 1
                    if self._engine.debug:
                        print(f"[ASYNC] Tick error: {e}")

                time.sleep(tick_interval)

        self._thread = threading.Thread(target=loop, daemon=True)
        self._thread.start()

    def stop(self, timeout: float = 2.0):
        """
        Stop background processing.

        Args:
            timeout: Max seconds to wait for thread
        """
        self._running = False
        if self._thread:
            self._thread.join(timeout=timeout)
            self._thread = None

    def get_decision(self) -> Optional[Decision]:
        """Get the latest decision (thread-safe)."""
        with self._lock:
            return self._latest_decision

    def get_sensors(self) -> Optional[SensorData]:
        """Get the latest sensor reading (thread-safe)."""
        with self._lock:
            return self._latest_sensors

    def tick_sync(self, sensors: SensorData) -> Optional[Decision]:
        """
        Synchronous tick (bypasses background thread).

        Useful for testing or when you want manual control.
        """
        return self._engine.tick(sensors)

    def reset(self):
        """Reset engine state."""
        self._engine.reset()
        with self._lock:
            self._latest_sensors = None
            self._latest_decision = None
            self._tick_count = 0
            self._errors = 0

    def __str__(self):
        status = "running" if self._running else "stopped"
        return f"AsyncNodeEngine({status}, ticks={self._tick_count}, nodes={len(self._engine._nodes)})"


class SensorThread:
    """
    Dedicated thread for sensor reading.

    Use when sensor reading is slow (e.g., LIDAR scan)
    and you don't want to block the decision loop.
    """

    def __init__(self, read_func: Callable[[], SensorData], rate: float = 20.0):
        """
        Args:
            read_func: Function that reads and returns SensorData
            rate: Read rate in Hz
        """
        self._read_func = read_func
        self._rate = rate
        self._thread = None  # type: Optional[threading.Thread]
        self._running = False
        self._lock = threading.Lock()
        self._latest = None  # type: Optional[SensorData]
        self._read_count = 0
        self._errors = 0

    def start(self):
        """Start sensor reading thread."""
        if self._running:
            return

        self._running = True
        interval = 1.0 / self._rate

        def loop():
            while self._running:
                try:
                    data = self._read_func()
                    with self._lock:
                        self._latest = data
                        self._read_count += 1
                except Exception as e:
                    self._errors += 1

                time.sleep(interval)

        self._thread = threading.Thread(target=loop, daemon=True)
        self._thread.start()

    def stop(self, timeout: float = 2.0):
        """Stop sensor reading."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=timeout)
            self._thread = None

    def read(self) -> Optional[SensorData]:
        """Get latest reading (thread-safe)."""
        with self._lock:
            return self._latest

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def read_count(self) -> int:
        return self._read_count


class DecisionExecutor:
    """
    Executes decisions in a separate thread.

    Useful when motor commands are slow or need
    to be rate-limited.
    """

    def __init__(self,
                 execute_func: Callable[[Decision], bool],
                 rate_limit: float = 20.0):
        """
        Args:
            execute_func: Function that executes a Decision, returns success
            rate_limit: Max executions per second
        """
        self._execute_func = execute_func
        self._rate_limit = rate_limit
        self._thread = None  # type: Optional[threading.Thread]
        self._running = False
        self._lock = threading.Lock()
        self._queue = []  # type: List[Decision]
        self._last_decision = None  # type: Optional[Decision]
        self._exec_count = 0

    def start(self):
        """Start executor thread."""
        if self._running:
            return

        self._running = True
        min_interval = 1.0 / self._rate_limit

        def loop():
            last_exec = 0.0
            while self._running:
                decision = None

                with self._lock:
                    if self._queue:
                        decision = self._queue.pop(0)

                if decision:
                    # Rate limiting
                    elapsed = time.time() - last_exec
                    if elapsed < min_interval:
                        time.sleep(min_interval - elapsed)

                    try:
                        self._execute_func(decision)
                        self._exec_count += 1
                        self._last_decision = decision
                        last_exec = time.time()
                    except Exception:
                        pass
                else:
                    time.sleep(0.01)  # Small sleep when idle

        self._thread = threading.Thread(target=loop, daemon=True)
        self._thread.start()

    def stop(self, timeout: float = 2.0):
        """Stop executor."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=timeout)
            self._thread = None

    def submit(self, decision: Decision):
        """Queue a decision for execution."""
        with self._lock:
            self._queue.append(decision)

    def submit_replace(self, decision: Decision):
        """Replace queue with single decision (latest wins)."""
        with self._lock:
            self._queue = [decision]

    @property
    def queue_size(self) -> int:
        with self._lock:
            return len(self._queue)

    @property
    def is_running(self) -> bool:
        return self._running
