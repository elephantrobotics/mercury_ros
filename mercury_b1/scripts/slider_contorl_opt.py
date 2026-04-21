#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Optimized slider control node for Mercury dual-arm robot.

Key improvements:
1. Control rate limiting (20Hz)
2. Change threshold filtering (avoid redundant commands)
3. Replace print with rospy logging
4. Add exception handling for robustness
"""

import math
import time
import rospy
from sensor_msgs.msg import JointState
from pymycobot.mercury import Mercury


class SliderController:
    """ROS node for controlling dual-arm robot using joint_states topic."""

    def __init__(self):
        """Initialize ROS node, robot connections, and subscriber."""
        rospy.init_node("control_slider", anonymous=True)

        # Load parameters
        port1 = rospy.get_param("~port1", "/dev/left_arm")
        port2 = rospy.get_param("~port2", "/dev/right_arm")
        baud = rospy.get_param("~baud", 115200)

        rospy.loginfo(f"Left arm: {port1}, baud: {baud}")
        rospy.loginfo(f"Right arm: {port2}, baud: {baud}")

        # Initialize robot connections
        self.left_arm = Mercury(port1, baud)
        self.right_arm = Mercury(port2, baud)

        time.sleep(0.05)
        self.left_arm.set_movement_type(2)
        self.right_arm.set_movement_type(2)

        time.sleep(0.05)
        self.left_arm.set_vr_mode(1)
        self.right_arm.set_vr_mode(1)

        time.sleep(0.05)
        self.left_arm.set_filter_len(3, 20)
        self.right_arm.set_filter_len(3, 20)

        # Control parameters
        self.last_time = time.time()
        self.last_left = None
        self.last_right = None

        # Subscribe to joint_states
        rospy.Subscriber("joint_states", JointState, self.callback)

        rospy.loginfo("Slider control node started.")
        rospy.spin()

    def callback(self, msg: JointState):
        """
        Callback function for joint_states topic.

        Args:
            msg (JointState): Incoming joint state message (radians)
        """

        now = time.time()

        # 1. Limit control frequency to ~20Hz
        if now - self.last_time < 0.05:
            return

        try:
            # Convert radians to degrees
            data_list = [round(math.degrees(v), 2) for v in msg.position]

            # Split joint groups
            left_arm = data_list[:7]
            right_arm = data_list[7:-3]
            middle_arm = data_list[-3:]

            # Apply joint offset correction
            left_arm[5] += 90
            right_arm[5] += 90

            # 2. Skip command if change is too small
            if self.last_left and self._is_small_change(left_arm, self.last_left):
                return

            if self.last_right and self._is_small_change(right_arm, self.last_right):
                return

            # Send commands to robot
            self.left_arm.send_angles(left_arm, 16, _async=True)
            self.right_arm.send_angles(right_arm, 16, _async=True)

            # Control middle joints individually
            self.right_arm.send_angle(11, middle_arm[2], 16, _async=True)
            self.right_arm.send_angle(12, middle_arm[1], 16, _async=True)
            self.right_arm.send_angle(13, middle_arm[0], 16, _async=True)

            # Update last state
            self.last_left = left_arm
            self.last_right = right_arm
            self.last_time = now

        except Exception as e:
            rospy.logerr(f"Control error: {e}")

    @staticmethod
    def _is_small_change(new, old, threshold=1.0):
        """
        Check if joint change is below threshold.

        Args:
            new (list): New joint values
            old (list): Previous joint values
            threshold (float): Minimum change threshold (degrees)

        Returns:
            bool: True if change is small, False otherwise
        """
        return max(abs(a - b) for a, b in zip(new, old)) < threshold


if __name__ == "__main__":
    SliderController()