#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Optimized slider control node for Mercury dual-arm robot (ROS1).

Key features:
1. Control rate limiting (~20Hz)
2. Independent control for left/right/middle joints
3. Change threshold filtering to avoid redundant commands
4. Proper logging (no print in high-frequency loop)
5. Robust exception handling
"""

import math
import time
import rospy
from sensor_msgs.msg import JointState
from pymycobot.mercury import Mercury


class SliderController:
    """ROS node for controlling dual-arm robot using joint_states."""

    def __init__(self):
        """Initialize ROS node, robot connections, and subscriber."""
        rospy.init_node("control_slider", anonymous=True)

        # Parameters
        port1 = rospy.get_param("~port1", "/dev/left_arm")
        port2 = rospy.get_param("~port2", "/dev/right_arm")
        baud = rospy.get_param("~baud", 115200)

        rospy.loginfo(f"Left arm: {port1}, baud: {baud}")
        rospy.loginfo(f"Right arm: {port2}, baud: {baud}")

        # Initialize robot connections
        self.left_arm = Mercury(port1, baud)
        self.right_arm = Mercury(port2, baud)
        if self.left_arm.is_power_on() != 1:
            self.left_arm.power_on()
        if self.right_arm.is_power_on() != 1:
            self.right_arm.power_on()

        time.sleep(0.05)
        self.left_arm.set_movement_type(1)
        time.sleep(0.05)
        self.right_arm.set_movement_type(1)
        #
        time.sleep(0.05)
        self.left_arm.set_vr_mode(1)
        self.right_arm.set_vr_mode(1)
        #
        # time.sleep(0.05)
        # self.left_arm.set_filter_len(3, 20)
        # self.right_arm.set_filter_len(3, 20)

        # Control state
        self.last_time = time.time()
        self.last_left = None
        self.last_right = None
        self.last_middle = None

        # Threshold settings (degrees)
        self.arm_threshold = 1.0
        self.middle_threshold = 0.5

        # Subscriber
        rospy.Subscriber("joint_states", JointState, self.callback)

        rospy.loginfo("Slider control node started.")
        rospy.spin()

    def callback(self, msg: JointState):
        """
        Callback for joint_states topic.

        Args:
            msg (JointState): Joint positions in radians
        """
        now = time.time()

        # 1. Limit control frequency to ~20Hz
        if now - self.last_time < 0.05:
            return

        try:
            # Convert radians to degrees
            data_list = [round(math.degrees(v), 2) for v in msg.position]

            # Split joints
            left_arm = data_list[:7]
            right_arm = data_list[7:-3]
            middle_arm = data_list[-3:]

            # Apply offset correction
            left_arm[5] += 90
            right_arm[5] += 90

            # -----------------------------
            # LEFT ARM CONTROL
            # -----------------------------
            if self._should_send(left_arm, self.last_left, self.arm_threshold):
                self.left_arm.send_angles(left_arm, 25, _async=True)
                self.last_left = left_arm

            # -----------------------------
            # RIGHT ARM CONTROL
            # -----------------------------
            if self._should_send(right_arm, self.last_right, self.arm_threshold):
                self.right_arm.send_angles(right_arm, 25, _async=True)
                self.last_right = right_arm

            # -----------------------------
            # MIDDLE JOINTS (11, 12, 13)
            # -----------------------------
            if self._should_send(middle_arm, self.last_middle, self.middle_threshold):
                self.right_arm.send_angle(11, middle_arm[2], 16, _async=True)
                self.right_arm.send_angle(12, middle_arm[1], 16, _async=True)
                self.right_arm.send_angle(13, middle_arm[0], 16, _async=True)
                self.last_middle = middle_arm

            # Update timestamp
            self.last_time = now

        except Exception as e:
            rospy.logerr(f"Control error: {e}")

    @staticmethod
    def _should_send(new, last, threshold):
        """
        Determine whether to send command based on change threshold.

        Args:
            new (list): New joint values
            last (list): Previous joint values
            threshold (float): Minimum change in degrees

        Returns:
            bool: True if command should be sent
        """
        if last is None:
            return True
        return max(abs(a - b) for a, b in zip(new, last)) >= threshold


if __name__ == "__main__":
    SliderController()