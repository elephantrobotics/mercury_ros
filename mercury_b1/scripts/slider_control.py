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
import traceback
from pymycobot.mercury import Mercury

# 限制频率的时间间隔
UPDATE_INTERVAL = 0.1  # 10 Hz

# 上一次更新的时间戳
last_update_time = 0

def callback(data):
    global last_update_time

    current_time = time.time()
    if current_time - last_update_time < UPDATE_INTERVAL:
        return  # 如果间隔时间不足，跳过此次更新

    last_update_time = current_time
    # rospy.loginfo(rospy.get_caller_id() + "%s", data.position)

    data_list = []
    for index, value in enumerate(data.position):
        radians_to_angles = round(math.degrees(value), 2)
        data_list.append(radians_to_angles)
        
    # print('data_list: {}'.format(data_list))
    left_arm = data_list[:7]
    right_arm = data_list[7:-3]
    middle_arm = data_list[-3:]
    
    print('left_angles: {}, right_angles: {}, middle_angles: {}'.format(left_arm, right_arm, middle_arm))

    try:
        l.send_angles(left_arm, 80, _async=True)
        r.send_angles(right_arm, 80, _async=True)
        r.send_angle(11, middle_arm[0], 80, _async=True)
        r.send_angle(12, middle_arm[1], 80, _async=True)
        r.send_angle(13, middle_arm[2], 80, _async=True)
    except Exception as e:
        e = traceback.format_exc()
        rospy.logerr(f"Failed to send angles: {e}")


def listener():
    global l, r
    rospy.init_node("control_slider", anonymous=True)

    l = Mercury("/dev/left_arm", 115200)
    r = Mercury("/dev/right_arm", 115200)
    l.set_movement_type(0) # 速度融合2 很耗时
    r.set_movement_type(0)
    time.sleep(0.05)
    rospy.Subscriber("joint_states", JointState, callback)
    # spin() simply keeps python from exiting until this node is stopped
    # spin()只是阻止python退出，直到该节点停止
    print("spin ...")
    rospy.spin()


if __name__ == "__main__":
    listener()
