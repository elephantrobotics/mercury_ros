#!/usr/bin/env python3

"""[summary]
This file obtains the joint angle of the manipulator in ROS,
and then sends it directly to the real manipulator using `pymycobot` API.
This file is [slider_control.launch] related script.
Passable parameters:
      port1: Left arm serial port string. Default is "/dev/ttyTHS1"
      port2: Right arm serial port string. Default is "/dev/ttyS0"
      Baud rate: Left and right arm serial port baud rate. The default value is 115200.
"""
import math
import time
import rospy
from sensor_msgs.msg import JointState

from pymycobot.mercury import Mercury


def callback(data):
    # rospy.loginfo(rospy.get_caller_id() + "%s", data.position)

    data_list = []
    for index, value in enumerate(data.position):
        radians_to_angles = round(math.degrees(value), 2)
        data_list.append(radians_to_angles)
        
    print('data_list: {}'.format(data_list))
    left_arm = data_list[:7]
    right_arm = data_list[7:-3]
    middle_arm = data_list[-3:]
    
    print('left_angles: {}'.format(left_arm))
    print('right_angles: {}'.format(right_arm))
    print('middle_angles: {}'.format(middle_arm))
    
    l.send_angles(left_arm, 25, _async=True)
    r.send_angles(right_arm, 25)
    r.send_angle(11, middle_arm[0], 25, _async=True)
    r.send_angle(12, middle_arm[1], 25, _async=True)
    r.send_angle(13, middle_arm[2], 25, _async=True)


def listener():
    global l, r
    rospy.init_node("control_slider", anonymous=True)

    l = Mercury("/dev/left_arm", 115200)
    r = Mercury("/dev/right_arm", 115200)
    time.sleep(0.05)
    rospy.Subscriber("joint_states", JointState, callback)
    # spin() simply keeps python from exiting until this node is stopped
    # spin()只是阻止python退出，直到该节点停止
    print("spin ...")
    rospy.spin()


if __name__ == "__main__":
    listener()
