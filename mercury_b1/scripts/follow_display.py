#!/usr/bin/env python3
import time
import math
import traceback
import rospy
from sensor_msgs.msg import JointState
from std_msgs.msg import Header

from pymycobot.mercury import Mercury


def talker():
    rospy.init_node("display", anonymous=True)

    print("Try connect real Mercury...")
    try:
        # left arm
        l = Mercury("/dev/left_arm", 115200)
        # right arm
        r = Mercury("/dev/right_arm", 115200)
        if l.is_power_on() != 1:
            l.power_on()
        if r.is_power_on() != 1:
            r.power_on()
        r.set_movement_type(1)
        l.set_movement_type(1)
    except Exception as e:
        print(e)
        print(
            """\
            \rTry connect Mercury failed!
            \rPlease check wether connected with Mercury.
            \rPlease chckt wether the port or baud is right.
        """
        )
        exit(1)
    l.release_all_servos()
    time.sleep(0.05)
    r.release_all_servos()
    time.sleep(0.05)
    print("Rlease all servos over.\n")

    pub = rospy.Publisher("joint_states", JointState, queue_size=10)
    rate = rospy.Rate(30)  # 30hz

    # pub joint state
    joint_state_send = JointState()
    joint_state_send.header = Header()

    joint_state_send.name = [
        "L1_joint",
        "L2_joint",
        "L3_joint",
        "L4_joint",
        "L5_joint",
        "L6_joint",
        "L7_joint",
        "R1_joint",
        "R2_joint",
        "R3_joint",
        "R4_joint",
        "R5_joint",
        "R6_joint",
        "R7_joint",
        "body",
        "head",
        "camera",
    ]
    
    joint_state_send.velocity = [0]
    joint_state_send.effort = []

    print("publishing ...")
    while not rospy.is_shutdown():
        joint_state_send.header.stamp = rospy.Time.now()
        try:
            left_angles = l.get_angles()
            right_angles = r.get_angles()
            eye_angle = r.get_angle(11)
            head_angle = r.get_angle(12)
            body_angle = r.get_angle(13)
   
            if left_angles is None or right_angles is None:
                # rospy.logwarn("Received None from get_angles, skip frame")
                rate.sleep()
                continue

            if len(left_angles) != 7 or len(right_angles) != 7:
                # rospy.logwarn("Invalid joint length, skip frame")
                rate.sleep()
                continue

            if None in left_angles or None in right_angles:
                # rospy.logwarn("Joint contains None, skip frame")
                rate.sleep()
                continue

            if None in [eye_angle, head_angle, body_angle]:
                # rospy.logwarn("Middle joint read failed, skip frame")
                rate.sleep()
                continue         
            
            left_angles[5] -= 90
            right_angles[5] -= 90
            
            # print('left: {}'.format(left_angles))
            # print('right: {}'.format(right_angles))
            # print('body: {}'.format(body_angle))
            # print('head: {}'.format(head_angle))
            # print('camera: {}'.format(eye_angle))
            
            all_angles = left_angles + right_angles + [body_angle] + [head_angle] + [eye_angle]
            data_list = []
            for index, value in enumerate(all_angles):
                radians = math.radians(value)
                data_list.append(radians)

            # rospy.loginfo('{}'.format(data_list))
            joint_state_send.position = data_list

            pub.publish(joint_state_send)

            rate.sleep()
        except Exception as e:
            e = traceback.format_exc()
            print(str(e))


if __name__ == "__main__":
    try:
        talker()
    except rospy.ROSInterruptException:
        pass
