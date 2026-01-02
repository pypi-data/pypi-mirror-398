"""
Sensors - Robot sensor abstraction

Simple and clear:
- SensorData contains raw distances
- No complex calculations here, just data
"""

from typing import Optional, Dict, Any


class SensorData:
    """
    Robot sensor data.

    All distances are in meters.
    None = sensor not available or timeout.
    """

    def __init__(self, front=None, left=None, right=None,
                 left_front=None, right_front=None, back=None, timestamp=0.0):
        self.front = front
        self.left = left
        self.right = right
        self.left_front = left_front
        self.right_front = right_front
        self.back = back
        self.timestamp = timestamp

    @classmethod
    def from_dict(cls, data):
        """Create SensorData from a dictionary (e.g., server JSON)"""
        return cls(
            front=data.get('front'),
            left=data.get('left'),
            right=data.get('right'),
            left_front=data.get('left_front'),
            right_front=data.get('right_front'),
            back=data.get('back'),
            timestamp=data.get('timestamp', 0.0)
        )

    @classmethod
    def from_lidar(cls, ranges: list, angles: list) -> 'SensorData':
        """
        Create SensorData from raw LIDAR data.

        Extracts distances at key angles:
        - front: 0°
        - left: 90°
        - right: -90° (or 270°)
        - left_front: 45°
        - right_front: -45° (or 315°)
        """
        def get_range_at_angle(target_angle: float) -> Optional[float]:
            """Find distance at closest angle"""
            if not ranges or not angles:
                return None

            # Normalize target angle
            target = target_angle % 360

            best_idx = None
            best_diff = float('inf')

            for i, angle in enumerate(angles):
                diff = abs((angle % 360) - target)
                diff = min(diff, 360 - diff)  # Shortest path
                if diff < best_diff:
                    best_diff = diff
                    best_idx = i

            if best_idx is not None and best_diff < 10:  # 10° tolerance
                return ranges[best_idx]
            return None

        return cls(
            front=get_range_at_angle(0),
            left=get_range_at_angle(90),
            right=get_range_at_angle(270),
            left_front=get_range_at_angle(45),
            right_front=get_range_at_angle(315),
            back=get_range_at_angle(180)
        )

    def is_valid(self) -> bool:
        """Check that essential sensors are present"""
        return self.front is not None

    def min_distance(self) -> float:
        """Return minimum distance across all sensors"""
        distances = [d for d in [
            self.front, self.left, self.right,
            self.left_front, self.right_front, self.back
        ] if d is not None]
        return min(distances) if distances else float('inf')

    def __repr__(self):
        parts = []
        if self.front is not None:
            parts.append(f"F={self.front:.2f}")
        if self.left is not None:
            parts.append(f"L={self.left:.2f}")
        if self.right is not None:
            parts.append(f"R={self.right:.2f}")
        return f"Sensors({', '.join(parts)})"
