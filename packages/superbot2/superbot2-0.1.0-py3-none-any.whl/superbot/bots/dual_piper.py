"""
Dual Piper robot implementation.
This module implements the Dual Piper robot using the Piper SDK.
"""

import time
from typing import Optional
import numpy as np
from scipy.spatial.transform import Rotation as R
from loguru import logger

from .base_bot import BaseRobot


class DualPiperRobot(BaseRobot):
    """
    Dual Piper Robot implementation using Piper SDK.
    Implements the shared control API from BaseRobot.
    """

    def __init__(
        self,
        can_interfaces=("can_left", "can_right"),
    ):
        super().__init__()

        # Attempt to import the Piper SDK
        try:
            from piper_sdk import C_PiperInterface_V2

            self.piper_sdk_available = True
        except ImportError:
            logger.warning(
                "Piper SDK not found. Please install piper_sdk for full functionality."
            )
            logger.warning("Using mock implementation for demonstration.")
            # Use mock implementation
            from .dual_piper_mock import C_PiperInterface_V2

            self.piper_sdk_available = False

        self.left_arm = None
        self.right_arm = None
        self.can_interfaces = can_interfaces

        for can_if in can_interfaces:
            arm = C_PiperInterface_V2(can_if)
            arm.ConnectPort()
            while not arm.EnablePiper():
                time.sleep(0.01)

            if "left" in can_if:
                self.left_arm = arm
                logger.info("Left arm connected on CAN interface: {}".format(can_if))
            elif "right" in can_if:
                self.right_arm = arm
                logger.info("Right arm connected on CAN interface: {}".format(can_if))

        if self.left_arm is None or self.right_arm is None:
            raise RuntimeError("左右臂 CAN 接口未正确配置")

        self._state_cache = {
            "left_arm": {"qpos": [0.0] * 6},
            "right_arm": {"qpos": [0.0] * 6},
            "left_joint": {"qpos": [0.0] * 6},
            "right_joint": {"qpos": [0.0] * 6},
            "left_ctrl": {"qpos": [0.0] * 6},
            "right_ctrl": {"qpos": [0.0] * 6},
            "left_vr_pose": {"qpos": [0.0] * 7},
            "right_vr_pose": {"qpos": [0.0] * 7},
            "left_gripper": [0.0],
            "right_gripper": [0.0],
        }

        self.connected = True
        self.set_gripper(0.0, 0.0)
        time.sleep(0.5)

    def connect(self):
        """Connect to the Dual Piper robot hardware."""
        if not self.connected:
            for can_if in self.can_interfaces:
                arm = C_PiperInterface_V2(can_if)
                arm.ConnectPort()
                while not arm.EnablePiper():
                    time.sleep(0.01)

                if "left" in can_if:
                    self.left_arm = arm
                    logger.info(
                        "Left arm connected on CAN interface: {}".format(can_if)
                    )
                elif "right" in can_if:
                    self.right_arm = arm
                    logger.info(
                        "Right arm connected on CAN interface: {}".format(can_if)
                    )

            self.connected = True
            self.start_state_monitoring()
        return True

    def disconnect(self):
        """Disconnect from the Dual Piper robot hardware."""
        self._running = False
        self.safe_stop()
        time.sleep(0.5)
        if self.left_arm:
            self.left_arm.DisConnectPort()
        if self.right_arm:
            self.right_arm.DisConnectPort()
        self.connected = False

    def _state_update_loop(self):
        """Continuously update the robot state in a background thread."""
        while self._running:
            try:
                left_pose = self.left_arm.GetArmEndPoseMsgs().end_pose
                right_pose = self.right_arm.GetArmEndPoseMsgs().end_pose
                left_joint = self.left_arm.GetArmJointMsgs().joint_state

                right_joint = self.right_arm.GetArmJointMsgs().joint_state
                left_ctrl = self.left_arm.GetArmJointCtrl().joint_ctrl
                right_ctrl = self.right_arm.GetArmJointCtrl().joint_ctrl
                # print(left_ctrl)
                if left_pose:
                    self._state_cache["left_arm"]["qpos"] = [
                        left_pose.X_axis / 1000000,
                        left_pose.Y_axis / 1000000,
                        left_pose.Z_axis / 1000000,
                        left_pose.RX_axis / 57295.7795,
                        left_pose.RY_axis / 57295.7795,
                        left_pose.RZ_axis / 57295.7795,
                    ]
                if left_ctrl:
                    self._state_cache["left_ctrl"]["qpos"] = [
                        left_ctrl.joint_1 / 57295.7795,
                        left_ctrl.joint_2 / 57295.7795,
                        left_ctrl.joint_3 / 57295.7795,
                        left_ctrl.joint_4 / 57295.7795,
                        left_ctrl.joint_5 / 57295.7795,
                        left_ctrl.joint_6 / 57295.7795,
                    ]
                if left_joint:
                    self._state_cache["left_joint"]["qpos"] = [
                        left_joint.joint_1 / 57295.7795,
                        left_joint.joint_2 / 57295.7795,
                        left_joint.joint_3 / 57295.7795,
                        left_joint.joint_4 / 57295.7795,
                        left_joint.joint_5 / 57295.7795,
                        left_joint.joint_6 / 57295.7795,
                    ]
                if right_pose:
                    self._state_cache["right_arm"]["qpos"] = [
                        right_pose.X_axis / 1000000,
                        right_pose.Y_axis / 1000000,
                        right_pose.Z_axis / 1000000,
                        right_pose.RX_axis / 57295.7795,
                        right_pose.RY_axis / 57295.7795,
                        right_pose.RZ_axis / 57295.7795,
                    ]
                if right_ctrl:
                    self._state_cache["right_ctrl"]["qpos"] = [
                        right_ctrl.joint_1 / 57295.7795,
                        right_ctrl.joint_2 / 57295.7795,
                        right_ctrl.joint_3 / 57295.7795,
                        right_ctrl.joint_4 / 57295.7795,
                        right_ctrl.joint_5 / 57295.7795,
                        right_ctrl.joint_6 / 57295.7795,
                    ]
                if right_joint:
                    self._state_cache["right_joint"]["qpos"] = [
                        right_joint.joint_1 / 57295.7795,
                        right_joint.joint_2 / 57295.7795,
                        right_joint.joint_3 / 57295.7795,
                        right_joint.joint_4 / 57295.7795,
                        right_joint.joint_5 / 57295.7795,
                        right_joint.joint_6 / 57295.7795,
                    ]
                left_grip = self.left_arm.GetArmGripperMsgs().gripper_state
                right_grip = self.right_arm.GetArmGripperMsgs().gripper_state

                if left_grip:
                    self._state_cache["left_gripper"] = [left_grip.grippers_angle / 1e6]

                if right_grip:
                    self._state_cache["right_gripper"] = [
                        right_grip.grippers_angle / 1e6
                    ]

            except Exception as e:
                logger.error(f"Error updating robot state: {e}")
                pass

            time.sleep(0.02)

    def set_gripper(
        self,
        left_value: float,
        right_value: float,
        speed: int = 1000,
        force: int = 0,
    ):
        """Control the grippers of the robot."""
        max_open_um = 50000

        left_pos = int((1.0 - left_value) * max_open_um)
        right_pos = int((1.0 - right_value) * max_open_um)
        self._state_cache["left_vr_pose"]["qpos"][6] = left_pos / 1000000.0
        self._state_cache["right_vr_pose"]["qpos"][6] = right_pos / 1000000.0
        self.left_arm.GripperCtrl(abs(left_pos), speed, 0x01, force)
        self.right_arm.GripperCtrl(abs(right_pos), speed, 0x01, force)

    def move_to_joint(self, action_joint):
        """Move the robot to specific joint positions."""
        factor = 57295.7795
        if action_joint is not None:
            joint_0 = round(action_joint[0] * factor)
            joint_1 = round(action_joint[1] * factor)
            joint_2 = round(action_joint[2] * factor)
            joint_3 = round(action_joint[3] * factor)
            joint_4 = round(action_joint[4] * factor)
            joint_5 = round(action_joint[5] * factor)
            joint_6 = round(action_joint[6] * 1000 * 1000)
            self.left_arm.MotionCtrl_2(0x01, 0x01, 100, 0x00)
            self.left_arm.JointCtrl(
                joint_0, joint_1, joint_2, joint_3, joint_4, joint_5
            )
            self.left_arm.GripperCtrl(abs(joint_6), 1000, 0x01, 0)
            joint_0 = round(action_joint[7] * factor)
            joint_1 = round(action_joint[8] * factor)
            joint_2 = round(action_joint[9] * factor)
            joint_3 = round(action_joint[10] * factor)
            joint_4 = round(action_joint[11] * factor)
            joint_5 = round(action_joint[12] * factor)
            joint_6 = round(action_joint[13] * 1000 * 1000)
            self.right_arm.MotionCtrl_2(0x01, 0x01, 100, 0x00)
            self.right_arm.JointCtrl(
                joint_0, joint_1, joint_2, joint_3, joint_4, joint_5
            )
            self.right_arm.GripperCtrl(abs(joint_6), 1000, 0x01, 0)

    def move_to_pose(
        self,
        left_target: Optional[np.ndarray] = None,
        right_target: Optional[np.ndarray] = None,
        duration: float = 1,
    ):
        """Move the robot to specific end-effector poses."""
        factor = 1000.0

        if left_target is not None:
            pos = left_target[:3, 3] * 1000.0
            rot = np.dot(
                left_target[:3, :3], np.array([[0, 0, 1], [0, 1, 0], [-1, 0, 0]])
            )
            rot = R.from_matrix(rot).as_euler("xyz", degrees=True)
            # print(f"pos:{pos}, rot: {rot}")
            self._state_cache["left_vr_pose"]["qpos"] = [
                pos[0] / 1000.0,
                pos[1] / 1000.0,
                pos[2] / 1000.0,
                rot[0],
                rot[1],
                rot[2],
                self._state_cache["left_vr_pose"]["qpos"][6],
            ]
            # rot = [0, 85, 0]

            self.left_arm.MotionCtrl_2(0x01, 0x00, int(duration * 100), 0x00)
            self.left_arm.EndPoseCtrl(
                int(pos[0] * factor),
                int(pos[1] * factor),
                int(pos[2] * factor),
                int(rot[0] * factor),
                int(rot[1] * factor),
                int(rot[2] * factor),
            )

        if right_target is not None:
            pos = right_target[:3, 3] * 1000.0
            rot = np.dot(
                right_target[:3, :3], np.array([[0, 0, 1], [0, 1, 0], [-1, 0, 0]])
            )
            rot = R.from_matrix(rot).as_euler("xyz", degrees=True)
            self._state_cache["right_vr_pose"]["qpos"] = [
                pos[0] / 1000.0,
                pos[1] / 1000.0,
                pos[2] / 1000.0,
                rot[0],
                rot[1],
                rot[2],
                self._state_cache["right_vr_pose"]["qpos"][6],
            ]
            # print(f"pos_R:{pos}, rot_R: {rot}")
            self.right_arm.MotionCtrl_2(0x01, 0x00, int(duration * 100), 0x00)
            self.right_arm.EndPoseCtrl(
                int(pos[0] * factor),
                int(pos[1] * factor),
                int(pos[2] * factor),
                int(rot[0] * factor),
                int(rot[1] * factor),
                int(rot[2] * factor),
            )

    def go_home(self):
        """Move the robot to its home position."""
        self.left_arm.MotionCtrl_2(0x01, 0x01, 30, 0x00)
        self.left_arm.JointCtrl(0, 0, 0, 0, 0, 0)
        self.right_arm.MotionCtrl_2(0x01, 0x01, 30, 0x00)
        self.right_arm.JointCtrl(0, 0, 0, 0, 0, 0)
        self._state_cache["left_vr_pose"]["qpos"] = [
            0.057,
            0,
            0.215,
            0,
            1.4835,
            0,
            0.05,
        ]
        self._state_cache["right_vr_pose"]["qpos"] = [
            0.057,
            0,
            0.215,
            0,
            1.4835,
            0,
            0.05,
        ]

    def safe_stop(self):
        """Safely stop the robot motion."""
        self.left_arm.EmergencyStop()
        self.right_arm.EmergencyStop()

    def get_state_pos(self):
        """Get the current joint positions."""
        # print(f"self.jstate_cache{self._state_cache}")
        return (
            self._state_cache["left_joint"]["qpos"]
            + self._state_cache["left_gripper"]
            + self._state_cache["right_joint"]["qpos"]
            + self._state_cache["right_gripper"]
        )

    def get_current_state(self):
        """Get the complete current state of the robot."""
        return {
            "left_arm": self._state_cache["left_arm"],
            "right_arm": self._state_cache["right_arm"],
            "left_gripper": self._state_cache["left_gripper"],
            "right_gripper": self._state_cache["right_gripper"],
            "left_joint": self._state_cache["left_joint"],
            "right_joint": self._state_cache["right_joint"],
            "left_ctrl": self._state_cache["left_ctrl"],
            "right_ctrl": self._state_cache["right_ctrl"],
            "left_vr_pose": self._state_cache["left_vr_pose"],
            "right_vr_pose": self._state_cache["right_vr_pose"],
            "body": {"qpos": []},
        }
