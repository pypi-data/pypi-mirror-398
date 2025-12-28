from vyomcloudbridge.senders.mav_sender import MavSender
from pymavlink import mavutil
import time


test_obj = MavSender()

print(len(test_obj.create_chunks("Kinematics and dynamics: kinematics and dynamics are two fundamental aspects that deal with the motion and behavior of robotic systems. Kinematics is the study of the motion of objects without considering the forces that cause the motion, focusing on describing the position, velocity, and acceleration of robotic systems without regard to the forces and torques that produce those motions. To completely define the pose of a robot we need to know the position and orientation of each link coordinate frame with respect to the base frame or a world coordinate system. Computing kinematics can be declined in two different sub problems in case of a robot manipulator: finding the pose of the end effector (hand) given the joint variables values of the robot, and this goes by the name Forward Kinematics; or, with increased complexity, to calculate the joint variables values of the robot given the pose of the end effector, namely computing its Inverse Kinematics. Dynamics, on the other hand, is concerned with the forces and torques that cause motion in robotic systems. It involves the study of how forces and torques affect the motion of robots, including their accelerations and resulting velocities.")[0][5]))
print(test_obj.create_chunks("Kinematics and dynamics: kinematics and dynamics are two fundamental aspects that deal with the motion and behavior of robotic systems. Kinematics is the study of the motion of objects without considering the forces that cause the motion, focusing on describing the position, velocity, and acceleration of robotic systems without regard to the forces and torques that produce those motions. To completely define the pose of a robot we need to know the position and orientation of each link coordinate frame with respect to the base frame or a world coordinate system. Computing kinematics can be declined in two different sub problems in case of a robot manipulator: finding the pose of the end effector (hand) given the joint variables values of the robot, and this goes by the name Forward Kinematics; or, with increased complexity, to calculate the joint variables values of the robot given the pose of the end effector, namely computing its Inverse Kinematics. Dynamics, on the other hand, is concerned with the forces and torques that cause motion in robotic systems. It involves the study of how forces and torques affect the motion of robots, including their accelerations and resulting velocities.")[0][0])
test_obj.listener.ack_data_received ={"abcd": {str(1):1, str(3): 1 }}
print(test_obj.msgid_generator())
print(test_obj.missing_chunk_indexes("abcd", 7))



# MAVLink connection setup
master = mavutil.mavlink_connection(
    # vyom_settings.MAVLINK_COMMANDER_IP,
    "udp:127.0.0.1:14556",
    source_system=101,
    source_component=191,
)
master.wait_heartbeat(timeout=5)

print("Heartbeat received. MavSender initialized successfully!")

# For testing purpose if needed
is_test_publishing = False
while is_test_publishing:
    print("sending msg")
    master.mav.vyom_message_send(
        255,
        0,
        "MSG001".encode("utf-8"),
        "Testing communication".encode("utf-8"),
        1,
        0,
        int(time.time()),
    )