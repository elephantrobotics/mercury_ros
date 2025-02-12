#!/usr/bin/env python3

"""[summary]
This file obtains the joint angle of the manipulator in ROS,
and then sends it directly to the real manipulator using `pymycobot` API.
This file is [slider_control.launch] related script.
Passable parameters:
      port1: Left arm serial port string. Default is "/dev/left_arm"
      port2: Right arm serial port string. Default is "/dev/right_arm"
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
        data_list.append(round(value, 3))
        
    # print('data_list: {}'.format(data_list))

    left_angles_list = [round(math.degrees(radian), 2) for radian in data_list[:7]]
    
    left_arm_gripper_value = map_angle_to_range(data_list[7])

    right_angles_list = [round(math.degrees(radian), 2) for radian in data_list[13:20]]
    
    right_arm_gripper_value = map_angle_to_range(data_list[20])
    
    middle_angles_list = [round(math.degrees(radian), 2) for radian in data_list[-3:]]
    # 为左臂和右臂的 J6 关节角度加上偏移量 90°
    left_angles_list[5] = left_angles_list[5] + 90
    right_angles_list[5] = right_angles_list[5] + 90
    
    print('left_angles: {}, right_angles: {}, middle_angles: {}, left_gripper_value: {}, right_gripper_value: {}'.format(left_angles_list, right_angles_list, middle_angles_list, left_arm_gripper_value, right_arm_gripper_value))

    try:
        l.send_angles(left_angles_list, 80, _async=True)
        r.send_angles(right_angles_list, 80, _async=True)
        r.send_angle(11, middle_angles_list[0], 80, _async=True)
        r.send_angle(12, middle_angles_list[1], 80, _async=True)
        r.send_angle(13, middle_angles_list[2], 80, _async=True)
        l.set_gripper_value(left_arm_gripper_value, 80)
        r.set_gripper_value(right_arm_gripper_value, 80)
    except Exception as e:
        e = traceback.format_exc()
        rospy.logerr(f"Failed to send angles: {e}")

def map_angle_to_range(angle):
    return int(((angle + 1.11) / 1.11) * 100)

def listener():
    global l, r
    rospy.init_node("control_slider", anonymous=True)

    l = Mercury("/dev/left_arm", 115200)
    r = Mercury("/dev/right_arm", 115200)
    l.set_movement_type(0) # 速度融合2 很耗时
    l.set_movement_type(0)
    time.sleep(0.05)
    rospy.Subscriber("joint_states", JointState, callback)
    # spin() simply keeps python from exiting until this node is stopped
    # spin()只是阻止python退出，直到该节点停止
    print("spin ...")
    rospy.spin()


if __name__ == "__main__":
    listener()
