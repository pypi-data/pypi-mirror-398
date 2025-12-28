import importlib
import json
import rclpy
from rclpy.node import Node
from rosidl_runtime_py import set_message_fields
from vyomcloudbridge.utils.logger_setup import setup_logger
import sys
import threading
from rclpy.qos import QoSProfile, QoSDurabilityPolicy

class RosSystemMsgPublisher(Node):
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(RosSystemMsgPublisher, cls).__new__(cls)
                    print("RosSystemMsgPublisher singleton initialized")
        print("RosSystemMsgPublisher client service started")
        return cls._instance
    
    def __init__(self, log_level=None):
        if getattr(self, "_initialized", False):
            return 
        if not rclpy.ok():  
            rclpy.init(args=None)
            
        self._initialized = True
        self.logger = setup_logger(
            name=self.__class__.__module__ + "." + self.__class__.__name__,
            show_terminal=False,
            log_level=log_level,
        )
        super().__init__("ros_system_msg_publisher")
        self.msg_publishers = {}  # { topic_name : (publisher, msg_instance) }
        self.logger.info("ROS System Message Publisher Node started.")
        self._msg_class_cache = {}

    def get_message_class(self, full_msg_name):
        if full_msg_name in self._msg_class_cache:
            self.logger.debug(f"Using cached message class for '{full_msg_name}'")
            self.logger.debug(
                f"Cached message class: {self._msg_class_cache[full_msg_name]}"
            )
            return self._msg_class_cache[full_msg_name]

        try:
            package, msg_name = full_msg_name.rsplit(".", 1)

            # Check if the module is already loaded
            if package in sys.modules:
                msg_module = sys.modules[package]
                self.logger.debug(f"Using already imported module '{package}'")
            else:
                msg_module = importlib.import_module(package)
                self.logger.debug(f"Imported module '{package}'")

            msg_class = getattr(msg_module, msg_name)

            if hasattr(msg_class, "_TYPE_SUPPORT"):
                self._msg_class_cache[full_msg_name] = msg_class
                self.logger.debug(
                    f"Loaded message class '{msg_name}' from '{package}'"
                )
                return msg_class

            raise AttributeError(f"'{full_msg_name}' does not have '_TYPE_SUPPORT'")

        except (ValueError, ModuleNotFoundError, AttributeError) as e:
            self.logger.error(f"Failed to import '{full_msg_name}': {e}")
            raise


    def _populate_message(self, msg_instance, msg_data):
        """Populate a message instance with data if valid."""
        self.logger.debug(f"message data: {msg_data} and msg_instance: {msg_instance}")

        # Case 0: If msg_data is already a message instance of the same type
        if type(msg_data) == type(msg_instance):
            self.logger.debug("msg_data is already a message instance. Copying fields.")
            msg_instance.__dict__.update(msg_data.__dict__)
            return True
        
        # Case 1: Handle JSON string passed as a set
        if isinstance(msg_data, set) and len(msg_data) == 1:
            try:
                string_value = next(iter(msg_data))
                msg_data = json.loads(string_value)
                self.logger.debug(f"Parsed JSON from set: {msg_data}")
            except Exception as e:
                self.logger.error(f"Failed to parse JSON from set: {e}")
                return False
                
        # Case 2: Handle empty data
        if msg_data is None or msg_data == '':
            self.logger.debug("Empty message data, using default instance")
            return False
            
        # Case 3: We have a dictionary, try to populate the message
        try:
            if isinstance(msg_data, str):
                try:
                    # When msg_data is in json format like '{"key": "value"}'
                    msg_data = json.loads(msg_data)
                except json.JSONDecodeError as e:
                    # when msg_data is not a valid JSON string
                    if hasattr(msg_instance, 'data'):
                        msg_instance.data = msg_data
                        return True
                    else:
                        self.logger.error(
                            f"msg_data is a plain string but msg_instance {type(msg_instance).__name__} "
                        )
                        return False
                        
            set_message_fields(msg_instance, msg_data)
            
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to set fields for message: {e} for msg_data: {msg_data} and msg_instance {msg_instance}")
            self.logger.debug(f"Using default-constructed message: {msg_instance}")
            return False

    def setup_publisher(self, topic_name, msg_type_str, msg_data=None, qos_profile=None):
        """Set up a publisher for a specific topic with the given message type."""
        self.logger.info(f"Got topic_name: {topic_name} msg_type_str: {msg_type_str}")
        
        try:
            # Get the message class from the message type string
            msg_class = self.get_message_class(msg_type_str)
            
            # Create a default message instance
            msg_instance = msg_class()
            
            # Populate the message instance with data if provided
            if msg_data is not None:
                self._populate_message(msg_instance, msg_data)
                # Even if population fails, we still use the default-initialized instance
# Create publisher if it doesn't exist
            if topic_name not in self.msg_publishers:
                self.logger.debug(
                    f"Creating publisher for topic: '{topic_name}' with message type: '{msg_class.__name__}'"
                )
                            # Use the provided QoS or default to 10
                qos = qos_profile if qos_profile else 10
                publisher = self.create_publisher(msg_class, topic_name, qos)
            else:
                self.logger.debug(
                    f"Already created publisher for topic: '{topic_name}' with message type: '{msg_class.__name__}'"
                )
                publisher, _ = self.msg_publishers[topic_name]
            
            # Store the publisher and message class
            self.msg_publishers[topic_name] = (publisher, msg_class)
            
            return msg_instance
            
        except Exception as e:
            self.logger.error(f"Failed to set up publisher: {e}")
            return None
    
    def publish_data(self, topic_name, msg_data=None):
        """Publish data to a specific topic."""
        try:
            self.logger.debug(
                f"In publish_data Got topic_name: {topic_name} msg_data: '{msg_data}'"
            )
            
            if topic_name in self.msg_publishers:
                publisher, msg_class = self.msg_publishers[topic_name]
                
                # Create a new message instance with default values
                msg_instance = msg_class()
                
                # Populate the message instance with data if provided
                if msg_data is not None:
                    self._populate_message(msg_instance, msg_data)
                
                # Publish the message
                publisher.publish(msg_instance)
                self.logger.info(f"Published on '{topic_name}': {msg_instance}")
                return True
            else:
                self.logger.error(f"No publisher found for topic: '{topic_name}'")
                return False
        except Exception as e:
            self.logger.error(f"Failed to publish data: {e}")
            return False

            
    # def publish_all(self):
    #     for topic, (publisher, msg_instance) in self.msg_publishers.items():
    #         publisher.publish(msg_instance)
    #         self.logger.info(f"Published on '{topic}': {msg_instance}")

    def spin_once(self, timeout_sec=1.0):
        """Spin once to allow time for ROS graph to recognize publishers."""
        if self._is_destroyed:
            self.logger.error("Cannot spin: Node has been destroyed")
            return
        try:
            rclpy.spin_once(self, timeout_sec=timeout_sec)
        except Exception as e:
            self.logger.error(f"Error in rclpy.spin_once: {e}")

    def cleanup(self, shutdown_ros=False):  # dont shutdown rclpy by default
        """Clean up resources. Optionally shut down ROS."""
        try:
            self.destroy_node()
            self._is_destroyed = True
            self.logger.info("Node destroyed successfully")
        except Exception as e:
            self.logger.error(f"Error in destroying node: {e}")

        if shutdown_ros:
            try:
                rclpy.shutdown()
                self.logger.info("ROS shutdown completed")
            except Exception as e:
                self.logger.error(f"Error during ROS shutdown: {e}")


def main(args=None):
    ros_msg_publisher = RosSystemMsgPublisher()

    input_json = (
        input_json
    ) = """[
        {
            "id": 373,
            "name": "AIRSIM_CAMERA_DOWN",
            "data_type": "sensor_msgs.msg.Image",
            "topic": "/camera/color/image_raw",
            "frequency": 12,
            "machine_model_id": 2,
            "is_subscribed": true,
            "msg": {
                "header": {
                    "stamp": {"sec": 0, "nanosec": 0},
                    "frame_id": "camera_down"
                },
                "height": 480,
                "width": 640,
                "encoding": "rgb8",
                "is_bigendian": 0,
                "step": 1920,
                "data": []
            }
        },
        {
            "id": 374,
            "name": "AIRSIM_CAMERA_FRONT",
            "data_type": "sensor_msgs.msg.Image",
            "topic": "/camera/color/image_raw",
            "frequency": 12,
            "machine_model_id": 2,
            "is_subscribed": true,
            "msg": {
                "header": {
                    "stamp": {"sec": 0, "nanosec": 0},
                    "frame_id": "camera_front"
                },
                "height": 480,
                "width": 640,
                "encoding": "rgb8",
                "is_bigendian": 0,
                "step": 1920,
                "data": []
            }
        },
        {
            "id": 375,
            "name": "BATTERY_TOPIC",
            "data_type": "sensor_msgs.msg.BatteryState",
            "topic": "/drone0/mavros/battery",
            "frequency": 12,
            "machine_model_id": 2,
            "is_subscribed": true,
            "msg": {
                "voltage": 11.1,
                "current": 5.2,
                "charge": 500.0,
                "capacity": 1000.0,
                "percentage": 0.5,
                "power_supply_status": 2,
                "power_supply_health": 1,
                "power_supply_technology": 3,
                "present": true
            }
        },
        {
            "id": 376,
            "name": "DRONE_MAVROS_STATE_TOPIC",
            "data_type": "mavros_msgs.msg.State",
            "topic": "/drone0/mavros/state",
            "frequency": 12,
            "machine_model_id": 2,
            "is_subscribed": true,
            "msg": {
                "connected": true,
                "armed": false,
                "guided": true,
                "mode": "AUTO.LOITER",
                "system_status": 4
            }
        },
        {
            "id": 377,
            "name": "DRONE_POSE_TOPIC",
            "data_type": "geometry_msgs.msg.PoseStamped",
            "topic": "/drone0/mavros/local_position/pose",
            "frequency": 12,
            "machine_model_id": 2,
            "is_subscribed": true,
            "msg": {
                "header": {
                    "stamp": {"sec": 0, "nanosec": 0},
                    "frame_id": "map"
                },
                "pose": {
                    "position": {"x": 1.0, "y": 2.0, "z": 3.0},
                    "orientation": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0}
                }
            }
        },
        {
            "id": 378,
            "name": "DRONE_VELOCITY_TOPIC",
            "data_type": "geometry_msgs.msg.TwistStamped",
            "topic": "/drone0/mavros/local_position/velocity_body",
            "frequency": 12,
            "machine_model_id": 2,
            "is_subscribed": true,
            "msg": {
                "header": {
                    "stamp": {"sec": 0, "nanosec": 0},
                    "frame_id": "base_link"
                },
                "twist": {
                    "linear": {"x": 0.5, "y": 0.0, "z": 0.1},
                    "angular": {"x": 0.0, "y": 0.0, "z": 0.01}
                }
            }
        },
        {
            "id": 379,
            "name": "MISSION_TOPIC",
            "data_type": "vyom_mission_msgs.msg.MissionStatus",
            "topic": "mission_status_topic",
            "frequency": 12,
            "machine_model_id": 2,
            "is_subscribed": true,
            "msg": {
                "mission_id": 8,
                "mission_status": 1
            }
        },
        {
            "id": 380,
            "name": "RELATIVE_ALTITUDE_PUBLISHER_TOPIC",
            "data_type": "std_msgs.msg.Float64",
            "topic": "drone0/mavros/global_position/rel_alt",
            "frequency": 12,
            "machine_model_id": 2,
            "is_subscribed": true,
            "msg": {
                "data": 10.5
            }
        },
        {
            "id": 381,
            "name": "DVID",
            "data_type": "vyom_msg.msg.Dvid",
            "topic": "Dvid",
            "frequency": 12,
            "machine_model_id": 2,
            "is_subscribed": true,
            "msg": {
                "device_id": 5005
            }
        },
        {
            "id": 382,
            "name": "ACCESS",
            "data_type": "vyom_msg.msg.Access",
            "topic": "access",
            "frequency": 12,
            "machine_model_id": 2,
            "is_subscribed": true,
            "msg": {
                "encrypted": "sample_encrypted_text"
            }
        },
        {
            "id": 383,
            "name": "SETPOINT_POSITION_TOPIC_GLOBAL",
            "data_type": "sensor_msgs.msg.NavSatFix",
            "topic": "/drone0/mavros/global_position/global",
            "frequency": 12,
            "machine_model_id": 2,
            "is_subscribed": true,
            "msg": {
                "latitude": 37.7749,
                "longitude": -122.4194,
                "altitude": 30.0,
                "position_covariance": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                "position_covariance_type": 0
            }
        }
    ]"""

    input_data = json.loads(input_json)

    for item in input_data:
        if item.get("is_subscribed", False):
            topic = item.get("topic")
            data_type = item.get("data_type") or item.get("typ")  # fallback check

            if not data_type:
                print(f"Skipping item due to missing 'data_type' or 'typ': {item}")
                continue

            msg_data = item.get("msg", {})

            try:
                latching_qos = QoSProfile(
                    depth=10,
                    durability=QoSDurabilityPolicy.TRANSIENT_LOCAL
                )
                ros_msg_publisher.setup_publisher(topic, data_type, msg_data, qos_profile=latching_qos)
            except Exception as e:
                print(
                    f"Failed to set up publisher for topic '{topic}' with data_type '{data_type}': {e}"
                )

    # Allow time for ROS graph to recognize publishers before publishing
    # rclpy.spin_once(ros_msg_publisher, timeout_sec=1.0) # TODO deepak, check on this, all functionality should be inside functions

    ros_msg_publisher.publish_all()
    ros_msg_publisher.cleanup(shutdown_ros=True)


if __name__ == "__main__":
    main()
