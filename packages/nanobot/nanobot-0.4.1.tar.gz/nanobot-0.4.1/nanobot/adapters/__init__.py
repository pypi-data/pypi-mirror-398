"""
NanoBot Adapters - Hardware abstractions

Interfaces to connect the framework to real components:
- MotorAdapter: Motor control
- SensorAdapter: Sensor reading (lidar, ultrasonic, etc.)
- CameraAdapter: Image capture

Each adapter is optional and replaceable.
"""

from .base import MotorAdapter, SensorAdapter, CameraAdapter
from .mock import MockMotor, MockSensor

__all__ = [
    'MotorAdapter', 'SensorAdapter', 'CameraAdapter',
    'MockMotor', 'MockSensor'
]
