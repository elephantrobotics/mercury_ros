import rospy
import tf
import csv
from urdf_parser_py.urdf import URDF

rospy.init_node('export_all_links_pose')

base_frame = "base"
robot = URDF.from_parameter_server()

# 获取所有link
all_links = [link.name for link in robot.links]

listener = tf.TransformListener()

# 等待TF准备好
rospy.sleep(1.0)

# 过滤出真正有TF的link（很关键！）
valid_links = []
for link in all_links:
    try:
        listener.lookupTransform(base_frame, link, rospy.Time(0))
        valid_links.append(link)
    except:
        pass

print("有效link数量:", len(valid_links))
print("有效link:", valid_links)

# 写CSV
with open("links_pose.csv", "w") as f:
    writer = csv.writer(f)
    writer.writerow(["time", "link", "x", "y", "z", "qx", "qy", "qz", "qw"])

    rate = rospy.Rate(10)
    while not rospy.is_shutdown():
        now = rospy.Time.now().to_sec()

        for link in valid_links:
            try:
                (trans, rot) = listener.lookupTransform(base_frame, link, rospy.Time(0))

                writer.writerow([
                    now,
                    link,
                    trans[0], trans[1], trans[2],
                    rot[0], rot[1], rot[2], rot[3]
                ])

                print(f"{link}: {trans}")

            except:
                pass

        rate.sleep()