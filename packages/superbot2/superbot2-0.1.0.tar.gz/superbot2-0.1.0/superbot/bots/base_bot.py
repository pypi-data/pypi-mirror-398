"""
Base robot class with shared control API
All specific robot implementations should inherit from this class
"""

import threading
import time
from abc import ABC, abstractmethod
from typing import Optional
import numpy as np
from scipy.spatial.transform import Rotation as R
from loguru import logger


class BaseRobot(ABC):
    """
    Abstract base class for all robots with shared control API.
    Each specific robot implementation should inherit from this class.
    """

    def __init__(self):
        self._state_cache = {}
        self._running = False
        self.connected = False
        self._state_thread = None

    @abstractmethod
    def connect(self):
        """Connect to the robot hardware."""
        pass

    @abstractmethod
    def disconnect(self):
        """Disconnect from the robot hardware."""
        pass

    @abstractmethod
    def _state_update_loop(self):
        """Continuously update the robot state in a background thread."""
        pass

    def start_state_monitoring(self):
        """Start the background thread for state monitoring."""
        if self._state_thread is None or not self._state_thread.is_alive():
            self._running = True
            self._state_thread = threading.Thread(
                target=self._state_update_loop, daemon=True
            )
            self._state_thread.start()

    def stop_state_monitoring(self):
        """Stop the background thread for state monitoring."""
        self._running = False
        if self._state_thread:
            self._state_thread.join(
                timeout=1.0
            )  # Wait up to 1 second for thread to finish

    @abstractmethod
    def set_gripper(
        self,
        left_value: float,
        right_value: float,
        speed: int = 1000,
        force: int = 0,
    ):
        """Control the grippers of the robot."""
        pass

    @abstractmethod
    def move_to_joint(self, action_joint):
        """Move the robot to specific joint positions."""
        pass

    @abstractmethod
    def move_to_pose(
        self,
        left_target: Optional[np.ndarray] = None,
        right_target: Optional[np.ndarray] = None,
        duration: float = 1,
    ):
        """Move the robot to specific end-effector poses."""
        pass

    @abstractmethod
    def go_home(self):
        """Move the robot to its home position."""
        pass

    @abstractmethod
    def safe_stop(self):
        """Safely stop the robot motion."""
        pass

    @abstractmethod
    def get_state_pos(self):
        """Get the current joint positions."""
        pass

    @abstractmethod
    def get_current_state(self):
        """Get the complete current state of the robot."""
        pass
