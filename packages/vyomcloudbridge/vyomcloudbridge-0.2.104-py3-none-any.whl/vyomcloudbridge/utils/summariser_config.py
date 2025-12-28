# ============================ CONFIG ============================

CONFIG = [
    {
        "topic": "/drone0/mavros/local_position/velocity_local",
        "type": "geometry_msgs/msg/TwistStamped",
    },
    {
        "topic": "/drone0/mavros/global_position/rel_alt",
        "type": "std_msgs/msg/Float64",
    },
    {
        "topic": "/drone0/mavros/battery",
        "type": "sensor_msgs/msg/BatteryState",
    },
    {
        "topic": "/drone0/mavros/setpoint_position/local",
        "type": "",
    },
    {
        "topic": "/drone0/mavros/setpoint_velocity/cmd_vel",
        "type": "geometry_msgs/msg/TwistStamped",
    },
]