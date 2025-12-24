"""
Utils module for SuperBot
Contains utility functions and classes for common robotic operations.
"""

import numpy as np
from scipy.spatial.transform import Rotation as R
import json
import yaml
from typing import Union, Dict, Any, Tuple
import time
import logging
from pathlib import Path


def skew_symmetric(v):
    """
    Create skew-symmetric matrix from vector
    For a vector v = [v1, v2, v3], returns:
    [[0, -v3, v2],
     [v3, 0, -v1],
     [-v2, v1, 0]]
    """
    return np.array([
        [0, -v[2], v[1]],
        [v[2], 0, -v[0]],
        [-v[1], v[0], 0]
    ])


def rotation_matrix_to_euler(R_mat: np.ndarray, sequence: str = 'xyz') -> np.ndarray:
    """Convert rotation matrix to Euler angles."""
    r = R.from_matrix(R_mat)
    return r.as_euler(sequence, degrees=True)


def euler_to_rotation_matrix(euler_angles: np.ndarray, sequence: str = 'xyz') -> np.ndarray:
    """Convert Euler angles to rotation matrix."""
    r = R.from_euler(sequence, euler_angles, degrees=True)
    return r.as_matrix()


def quaternion_to_rotation_matrix(quat: np.ndarray) -> np.ndarray:
    """Convert quaternion [x, y, z, w] to rotation matrix."""
    r = R.from_quat(quat)
    return r.as_matrix()


def rotation_matrix_to_quaternion(R_mat: np.ndarray) -> np.ndarray:
    """Convert rotation matrix to quaternion [x, y, z, w]."""
    r = R.from_matrix(R_mat)
    return r.as_quat()


def transformation_matrix(rotation: np.ndarray, translation: np.ndarray) -> np.ndarray:
    """Create a 4x4 transformation matrix from rotation matrix and translation vector."""
    T = np.eye(4)
    T[:3, :3] = rotation
    T[:3, 3] = translation
    return T


def get_inverse_transform(T: np.ndarray) -> np.ndarray:
    """Compute inverse of a transformation matrix."""
    R_inv = T[:3, :3].T
    t_inv = -R_inv @ T[:3, 3]
    T_inv = np.eye(4)
    T_inv[:3, :3] = R_inv
    T_inv[:3, 3] = t_inv
    return T_inv


def interpolate_positions(start_pos: np.ndarray, end_pos: np.ndarray, t: float) -> np.ndarray:
    """
    Linearly interpolate between two positions.
    t should be between 0 and 1, where 0 is start_pos and 1 is end_pos.
    """
    if not 0 <= t <= 1:
        raise ValueError("Interpolation parameter t must be between 0 and 1")
    return start_pos + t * (end_pos - start_pos)


def normalize_quaternion(quat: np.ndarray) -> np.ndarray:
    """Normalize a quaternion."""
    return quat / np.linalg.norm(quat)


def compute_jacobian(robot_model, joint_angles: np.ndarray, link_idx: int) -> np.ndarray:
    """
    Compute the Jacobian matrix for a given robot configuration.
    This is a simplified version - a full implementation would depend on the specific kinematic model.
    """
    # This is a placeholder implementation
    # Real implementation would require forward kinematics and geometric Jacobian calculation
    num_joints = len(joint_angles)
    jacobian = np.zeros((6, num_joints))  # [linear_velocities, angular_velocities]
    
    # Placeholder computation
    return jacobian


def load_config(config_path: Union[str, Path]) -> Dict[str, Any]:
    """Load configuration from YAML or JSON file."""
    config_path = Path(config_path)
    
    if config_path.suffix.lower() in ['.yaml', '.yml']:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    elif config_path.suffix.lower() == '.json':
        with open(config_path, 'r') as f:
            return json.load(f)
    else:
        raise ValueError(f"Unsupported config file format: {config_path.suffix}")


def save_config(config: Dict[str, Any], config_path: Union[str, Path]):
    """Save configuration to YAML or JSON file."""
    config_path = Path(config_path)
    
    if config_path.suffix.lower() in ['.yaml', '.yml']:
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
    elif config_path.suffix.lower() == '.json':
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
    else:
        raise ValueError(f"Unsupported config file format: {config_path.suffix}")


class Timer:
    """Simple timer utility for measuring execution time."""
    
    def __init__(self):
        self.start_time = None
        self.elapsed_time = 0
        
    def start(self):
        """Start the timer."""
        self.start_time = time.time()
        
    def stop(self) -> float:
        """Stop the timer and return elapsed time in seconds."""
        if self.start_time is None:
            raise RuntimeError("Timer not started")
        self.elapsed_time = time.time() - self.start_time
        self.start_time = None
        return self.elapsed_time
        
    def reset(self):
        """Reset the timer."""
        self.start_time = None
        self.elapsed_time = 0


def setup_logging(level: str = "INFO", log_file: str = None):
    """Setup logging configuration."""
    level_enum = getattr(logging, level.upper())
    
    handlers = []
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level_enum)
    console_handler.setFormatter(formatter)
    handlers.append(console_handler)
    
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level_enum)
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)
    
    logging.basicConfig(level=level_enum, handlers=handlers)


def validate_pose(pose: np.ndarray) -> bool:
    """Validate that the input is a valid 4x4 pose matrix."""
    if pose.shape != (4, 4):
        return False
    
    # Check if upper-left 3x3 is a valid rotation matrix
    R = pose[:3, :3]
    if not np.allclose(R @ R.T, np.eye(3)):
        return False
    
    if not np.isclose(np.linalg.det(R), 1.0):
        return False
    
    return True


def smooth_trajectory(waypoints: np.ndarray, smoothing_factor: float = 0.1) -> np.ndarray:
    """Apply smoothing to a trajectory defined by waypoints."""
    if len(waypoints) < 3:
        return waypoints
    
    smoothed = np.copy(waypoints)
    
    for i in range(1, len(waypoints) - 1):
        smoothed[i] = (1 - smoothing_factor) * waypoints[i] + \
                     smoothing_factor * 0.5 * (waypoints[i-1] + waypoints[i+1])
    
    return smoothed