# SuperBot

SuperBot is a modern, modular robotics framework designed for controlling dual-arm piper robots and other robotic systems. It provides a clean, intuitive API for robot control, sensor integration, and utility functions.

## Features

- Modular architecture with separate modules for bots, sensors, and utilities
- Dual-arm piper robot control interface
- Sensor management system
- Utility functions for robotics operations
- Clean, well-documented API

## Installation

```bash
pip install superbot
```

## Quick Start

```python
from superbot import RobotWrapper

# Initialize the robot wrapper with CAN interfaces
robot = RobotWrapper(can_interfaces=("can_left", "can_right"))

# Move to a specific pose
import numpy as np
target_pose = np.eye(4)  # 4x4 identity matrix as example
robot.move_to_pose(left_target=target_pose, right_target=target_pose)

# Close the grippers halfway
robot.set_gripper(0.5, 0.5)

# Get current robot state
state = robot.get_current_state()
print(state)
```

## Architecture

SuperBot follows a modular design:

- **bots**: Contains robot-specific implementations (dual_piper, etc.)
- **sensors**: Sensor management and interfaces
- **utils**: Common utility functions for robotics operations

## Contributing

Contributions are welcome! Please see the contributing guidelines for details.