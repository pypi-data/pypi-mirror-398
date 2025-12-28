import os

package_name = "vyomcloudbridge"
vyom_root_dir = "/etc/vyomcloudbridge"
# base_api_url = "https://test.hqapi.vyomos.org"
base_api_url = "https://api.vyomiq.io"

cert_dir = f"{vyom_root_dir}/certs/"
cert_file_name = "machine.cert.pem"
cert_file_path = os.path.join(cert_dir, cert_file_name)
pri_key_file_name = "machine.private.key"
pri_key_file_path = os.path.join(cert_dir, pri_key_file_name)
pub_key_file_name = "machine.public.key"
pub_key_file_path = os.path.join(cert_dir, pub_key_file_name)
root_ca_file_name = "root-CA.crt"
root_ca_file_path = os.path.join(cert_dir, root_ca_file_name)

log_dir = "/var/log/vyomcloudbridge"
log_file_name = "vyomcloudbridge.log"
log_file = os.path.join(log_dir, log_file_name)
pid_file = os.path.join(log_dir, "service_pids.json")
machine_config_file = os.path.join(vyom_root_dir, "machine.conf")
machine_topics_file = os.path.join(vyom_root_dir, "machine_topics.json")

# default timezone for the machine
DEFAULT_TIMEZONE = "Asia/Kolkata"

# Rabbit MQ
rabbit_mq_url = "http://0.0.0.0:15672"
rabbit_mq_username = "guest"
rabbit_mq_password = "guest"

# RESERVED data queues
main_data_queue = "data_queue"

# ENV related files
# vyom_services_env_file = os.path.join(vyom_root_dir, "vyom_services_env_file.sh") # Not in use
vyom_variables_file = os.path.join(vyom_root_dir, "vyom_variables_file.json")

# SYSTEM SERVICE's
service_dir = "/etc/systemd/system"
service_file_name = "vyomcloudbridge.service"
service_file_path = os.path.join(service_dir, service_file_name)
start_script_file = os.path.join(vyom_root_dir, "vyomcloudbridge.sh")

service_root_file_name = "vyomcloudbridge-root.service"
service_root_file_path = os.path.join(service_dir, service_root_file_name)
start_script_root_file = os.path.join(vyom_root_dir, "vyomcloudbridge_root.sh")

ssh_service_file_name = "vyom-reverse-ssh.service"
ssh_service_file_path = os.path.join(service_dir, ssh_service_file_name)

MACHINE_REGISTER_API_URL = f"{base_api_url}/device/register/"
MACHINE_MODELS_API_URL = f"{base_api_url}/machine-model/"
MACHINE_TOPICS_API_URL = f"{base_api_url}/machine-model/topic/device-list/"

UPLOAD_DATA_DIR = "/vyomos/robotics/upload_data"
MISSION_DATA_DIR = "/vyomos/robotics/mission_data"

UPLOAD_THREADS = 10  # 10 by default
MAX_FILE_SIZE = 120 * 1024  # in bytes (~120KB)
LIVE_FILE_SIZE = 70 * 1024  # in bytes (~70KB)

# default project id for non-mission related data uploads
default_upload_dir = "_uploads_"

default_project_id = "_all_"
default_mission_id = "_all_"

data_buffer_key = "_all_"  # buffer key for non-mission related data
mission_buffer_key = (
    "<mission_id>"  # buffer key for non-mission related data, <== DO NOT IMPORT ==>
)

default_machine_type = "robot"  # it could be "server, gcs"

# --- RESERVED data sources
default_dir_data_source = "_uploads_"
MACHINE_STATS_DT_SRC = "machine_stats"
MISSION_STATS_DT_SRC = "mission_stats"
MISSION_MESSAGE_DT_SRC = "mission_message"
MISSION_SUMMARY_DT_SRC = "mission_summary"
CHUNK_MERGER_DT_SRC = "chunk_merger"
ROUTED_MACHINE_DT_SRC = "routed_machine"
SPEED_TEST_DT_SRC = "speed_test"
#----
DUMMY_DATA_DT_SRC = "DUMMY_DATA"
#----
        

# from vyomcloudbridge.constants.constants import default_upload_dir, default_project_id, default_mission_id, data_buffer_key, mission_buffer_key

RESERVED_KEYS = [
    "data_queue",
    "current_mission",
    "current_user",
    "machine_buffer",
    "machine_buffer_array",
    "last_data_mission",
    "last_data_mission_id",
]

SERVICE_ID = {
    "queueworker": "que-wr",
    "dirwatcher": "dir-wt",
    "streamconsumer": "str-cm",
    "missionstats": "mis-st",
    "machinestats": "mch-st",
    "mavproxyhq": "mav-hq",
    "robotstat": "rob-st",
}

DEFAULT_RABBITMQ_URL = "amqp://guest:guest@localhost:5672/%2F"
MQTT_ENTPOINT = "a1k0jxthwpkkce-ats.iot.ap-south-1.amazonaws.com"

machine_topics_list = [  # not in use
    {
        "name": "RELATIVE_ALTITUDE_PUBLISHER_TOPIC",
        "data_type": "std_msgs.msg.Float64",
        "topic": "drone0/mavros/global_position/rel_alt",
    },
    {
        "name": "SETPOINT_POSITION_TOPIC",
        "data_type": "geometry_msgs.msg.PoseStamped",
        "topic": "/drone0/mavros/setpoint_position/local",
    },
    {
        "name": "SETPOINT_POSITION_TOPIC_GLOBAL",
        "data_type": "sensor_msgs.msg.NavSatFix",
        "topic": "/drone0/mavros/global_position/global",
    },
    {
        "name": "DRONE_VELOCITY_TOPIC",
        "data_type": "geometry_msgs.msg.TwistStamped",
        "topic": "/drone0/mavros/local_position/velocity_body",
    },
    {
        "name": "DRONE_POSE_TOPIC",
        "data_type": "geometry_msgs.msg.PoseStamped",
        "topic": "/drone0/mavros/local_position/pose",
    },
    {
        "name": "DRONE_MAVROS_STATE_TOPIC",
        "data_type": "mavros_msgs.msg.State",
        "topic": "/drone0/mavros/state",
    },
    {
        "name": "SETPOINT_VELOCITY_TOPIC",
        "data_type": "geometry_msgs.msg.Twist",
        "topic": "/drone0/mavros/setpoint_velocity/cmd_vel",
    },
    {
        "name": "BATTERY_TOPIC",
        "data_type": "sensor_msgs.msg.BatteryState",
        "topic": "/drone0/mavros/battery",
    },
    {
        "name": "GPS_TOPIC",
        "data_type": "mavros_msgs.msg.GPSRAW",
        "topic": "/drone0/mavros/gpsstatus/gps1/raw",
    },
    {
        "name": "AIRSIM_POINTCLOUD_TOPIC",
        "data_type": "sensor_msgs.msg.PointCloud2",
        "topic": "/airsim/pointcloud",
    },
    {
        "name": "RANGEFINDER_TOPIC",
        "data_type": "std_msgs.msg.Float32",
        "topic": "/vyom/rangefinder",
    },
    {
        "name": "AIRSIM_CAMERA_DOWN",
        "data_type": "sensor_msgs.msg.Image",
        "topic": "/camera_down/down_cam/image_raw",
    },
    {
        "name": "AIRSIM_CAMERA_FRONT",
        "data_type": "sensor_msgs.msg.Image",
        "topic": "/camera/color/image_raw",
    },
    {
        "name": "CAMERA_FRONT_TOPIC",
        "data_type": "sensor_msgs.msg.Image",
        "topic": "/depth/image_raw",
    },
    {
        "name": "CAMERA_BOTTOM_TOPIC",
        "data_type": "sensor_msgs.msg.Image",
        "topic": "/down_camera/image_raw",
    },
    {
        "name": "JETSON_POINTCLOUD_TOPIC",
        "data_type": "sensor_msgs.msg.PointCloud2",
        "topic": "/airsim/pointcloud",
    },
    {
        "name": "MISSION_TOPIC",
        "data_type": "vyom_mission_msgs.msg.MissionStatus",
        "topic": "mission_status_topic",
    },
    {
        "name": "MAVLINK_TOPIC",
        "data_type": "std_msgs.msg.String",
        "topic": "mavlink_topic",
    },
    {
        "name": "IPC_MSG_TOPIC",
        "data_type": "std_msgs.msg.String",
        "topic": "ipc_msg_topic",
    },
    {"name": "BT_START_TOPIC", "data_type": "std_msgs.msg.String", "topic": "bt_start"},
    {"name": "VYOM_MSG_TOPIC", "data_type": "std_msgs.msg.String", "topic": "vyom_msg"},
]
sample_mission_telemetry = [
    {
        "label": "GPS Data",
        "key": "gps_data",
        "timestamp": 1733487847,
        "data": {
            "latitude": 37.7749,
            "longitude": -122.4194,
            "altitude": 154.3,
        },
        "unit": "meter",
    },
    {
        "label": "Orientation",
        "key": "orientation",
        "timestamp": 1733487847,
        "data": {
            "x": 0.032,
            "y": 0.741,
            "z": 0.127,
            "w": 0.658,
        },
        "data": {
            "x": 0.032,
            "y": 0.741,
            "z": 0.127,
            "w": 0.658,
        },
        "unit": "quat",
    },
    {
        "label": "Angular Velocity",
        "key": "angular_velocity",
        "timestamp": 1733487847,
        "data": {
            "x": 0.021,
            "y": -0.015,
            "z": 0.032,
        },
        "unit": "rad/s",
    },
    {
        "label": "Linear Acceleration",
        "key": "linear_acceleration",
        "timestamp": 1733487847,
        "data": {
            "x": 0.27,
            "y": 0.18,
            "z": 9.81,
        },
        "unit": "m/s²",
    },
    {
        "label": "Local Position",
        "key": "local_position",
        "timestamp": 1733487847,
        "data": {
            "x": 15.4,
            "y": 23.7,
            "z": -2.1,
        },
        "unit": "meter",
    },
    {
        "label": "Velocity",
        "key": "velocity",
        "timestamp": 1733487847,
        "data": {
            "x": 1.2,
            "y": -0.5,
            "z": 0.1,
        },
        "unit": "m/s",
    },
    {
        "label": "Orientation Pose",
        "key": "orientation_pose",
        "timestamp": 1733487847,
        "data": {
            "x": 0.033,
            "y": 0.738,
            "z": 0.129,
            "w": 0.661,
        },
        "unit": "quat",
    },
]


sample_mission_summary = [
    {
        "label": "Planned Path",
        "key": "planned_path",
        "timestamp": None,
        "data": [[]],
        "unit": None,
    },
    {
        "label": "Actual Path",
        "key": "actual_path",
        "timestamp": None,
        "unit": None,
    },
    {
        "label": "Total Time",
        "key": "total_time",
        "timestamp": None,
        "data": 2323,
        "unit": "ms",
    },
    {
        "label": "Animals Found",
        "key": "animals_found",
        "timestamp": None,
        "data": 32,
        "unit": "int",
    },
]

#  Summary for topic: RELATIVE_ALTITUDE_PUBLISHER_TOPIC
#   data: min=0.010, max=0.012, avg=0.011, count=11
#  topic: "SETPOINT_POSITION_TOPIC_GLOBAL",
#   latitude: {
#       min: -35.363,
#       max: -35.363,
#       avg: -35.363,
#       count: 11
#       },
#   longitude: {
#       min: 149.165,
#       max: 149.165,
#       avg: 149.165,
#       count: 11
#       },
#   altitude: min=602.579, max=602.579, avg=602.579, count=11

sample_mission = {
    "id": 301360,  # [Compulsory integer] - unique mission identifier
    "name": "Navigate To",  # [Compulsory string] - custom mission name OR Command Name
    "mission_type": "Navigate To",  # [Compulsory string] - Command Name
    "machine_id": 12,  # [Compulsory integer] - ID of associated machine
    "mission_status": 1,  # [Compulsory string] created-0, in_progress-1, completed-2, terminated-3, unknown-4, failed-5
    "description": "",  # [Optional string] - mission description (can be empty string or None)
    "json_data": {},  # [Optional JSON object] - additional data (can be empty dict)
    "creator_id": 1,  # [Compulsory integer] - ID of user who created the mission
    "owner_id": 1,  # [Compulsory integer] - ID of user who owns the mission
    "campaign_id": None,  # [Optional integer] - ID of associated campaign (or None)
    "mission_date": None,  # [Optional ISO date format] - (YYYY-MM-DD) in UTC, e.g., "2025-03-21"
    "start_time": None,  # [Optional ISO datetime format] - in UTC, e.g., "2025-03-21T14:30:00Z"
    "end_time": None,  # [Optional ISO datetime format] - in UTC, e.g., "2025-03-21T16:45:00Z"
}
