"""
Sensors module for SuperBot
Contains classes and utilities for managing robot sensors.
"""

from abc import ABC, abstractmethod
import time
from typing import Dict, Any, Optional
import numpy as np


class BaseSensor(ABC):
    """Abstract base class for all sensors."""

    def __init__(self, name: str, sensor_type: str):
        self.name = name
        self.sensor_type = sensor_type
        self.last_reading_time = 0
        self.is_connected = False

    @abstractmethod
    def connect(self):
        """Connect to the sensor."""
        pass

    @abstractmethod
    def disconnect(self):
        """Disconnect from the sensor."""
        pass

    @abstractmethod
    def read(self) -> Dict[str, Any]:
        """Read data from the sensor."""
        pass

    def get_status(self) -> Dict[str, Any]:
        """Get sensor status information."""
        return {
            "name": self.name,
            "type": self.sensor_type,
            "connected": self.is_connected,
            "last_reading_time": self.last_reading_time,
        }
