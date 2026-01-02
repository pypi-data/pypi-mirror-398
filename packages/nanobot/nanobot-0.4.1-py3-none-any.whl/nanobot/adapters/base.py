"""
Base Adapters - Abstract hardware interfaces

Implement these classes to connect your real robot.
"""

from abc import ABC, abstractmethod
from typing import Optional, Tuple, List
from ..core import Action, SensorData


class MotorAdapter(ABC):
    """
    Interface for motor control.

    Implement this class for your specific hardware:
    - Jetson GPIO + PWM
    - Arduino via Serial
    - ROS
    - etc.
    """

    @abstractmethod
    def execute(self, action: Action, speed: float) -> bool:
        """
        Execute a motor action.

        Args:
            action: Action to execute (FORWARD, BACKWARD, etc.)
            speed: Normalized speed [0.0, 1.0]

        Returns:
            True if success, False otherwise
        """
        pass

    @abstractmethod
    def stop(self) -> bool:
        """Emergency stop motors."""
        pass

    def get_speed(self) -> Tuple[float, float]:
        """Return (left_speed, right_speed). Override if available."""
        return (0.0, 0.0)

    def cleanup(self):
        """Release resources. Override if needed."""
        pass


class SensorAdapter(ABC):
    """
    Interface for sensor reading.

    Implement this class for your hardware:
    - LIDAR (RPLidar, YDLidar, etc.)
    - Ultrasonic (HC-SR04)
    - Infrared
    - etc.
    """

    @abstractmethod
    def read(self) -> SensorData:
        """
        Read sensors and return data.

        Returns:
            SensorData with measured distances
        """
        pass

    def is_ready(self) -> bool:
        """Check if sensors are ready. Override if needed."""
        return True

    def calibrate(self) -> bool:
        """Calibrate sensors. Override if needed."""
        return True

    def cleanup(self):
        """Release resources. Override if needed."""
        pass


class CameraAdapter(ABC):
    """
    Interface for image capture.

    Implement this class for:
    - CSI Camera (Jetson)
    - USB Webcam
    - Realsense
    - etc.
    """

    @abstractmethod
    def capture(self) -> Optional[bytes]:
        """
        Capture an image.

        Returns:
            Image data (JPEG/PNG) or None if error
        """
        pass

    def get_resolution(self) -> Tuple[int, int]:
        """Return (width, height). Override if available."""
        return (640, 480)

    def set_resolution(self, width: int, height: int) -> bool:
        """Change resolution. Override if supported."""
        return False

    def cleanup(self):
        """Release resources. Override if needed."""
        pass


class RobotAdapter:
    """
    Facade combining motors and sensors.

    Usage:
        robot = RobotAdapter(
            motor=JetsonMotor(),
            sensor=LidarSensor()
        )

        sensors = robot.read_sensors()
        robot.execute(Action.FORWARD, 0.5)
    """

    def __init__(self,
                 motor: Optional[MotorAdapter] = None,
                 sensor: Optional[SensorAdapter] = None,
                 camera: Optional[CameraAdapter] = None):
        self.motor = motor
        self.sensor = sensor
        self.camera = camera

    def read_sensors(self) -> SensorData:
        """Read sensors or return empty data."""
        if self.sensor:
            return self.sensor.read()
        return SensorData()

    def execute(self, action: Action, speed: float) -> bool:
        """Execute action or return False if no motor."""
        if self.motor:
            return self.motor.execute(action, speed)
        return False

    def stop(self) -> bool:
        """Emergency stop."""
        if self.motor:
            return self.motor.stop()
        return False

    def capture(self) -> Optional[bytes]:
        """Capture image or return None."""
        if self.camera:
            return self.camera.capture()
        return None

    def cleanup(self):
        """Release all resources."""
        if self.motor:
            self.motor.cleanup()
        if self.sensor:
            self.sensor.cleanup()
        if self.camera:
            self.camera.cleanup()
