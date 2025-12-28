import importlib
import rclpy
from rclpy.node import Node

class RosSystemMsgSubscriber(Node):
    def __init__(self):
        super().__init__("ros_system_msg_subscriber")
        self.msg_subscribers = {}  # { topic_name : subscriber }
        self.get_logger().info("ROS System Message Subscriber Node started.")
        self._msg_class_cache = {}

    def get_message_class(self, full_msg_name):
        if full_msg_name in self._msg_class_cache:
            self.get_logger().info(f"Using cached message class for '{full_msg_name}'")
            return self._msg_class_cache[full_msg_name]

        try:
            package, msg_name = full_msg_name.rsplit(".", 1)
            msg_module = importlib.import_module(f"{package}")
            msg_class = getattr(msg_module, msg_name)
            if hasattr(msg_class, "_TYPE_SUPPORT"):
                self._msg_class_cache[full_msg_name] = msg_class
                self.get_logger().info(f"Loaded message class '{msg_name}' from '{package}'")
                return msg_class
        except (ValueError, ModuleNotFoundError, AttributeError) as e:
            self.get_logger().error(f"Failed to import '{full_msg_name}': {e}")
            raise

    def setup_subscriber(self, topic_name, msg_type_str):
        msg_class = self.get_message_class(msg_type_str)
        topic = topic_name.lower()
        if topic not in self.msg_subscribers:
            self.get_logger().info(f"Creating subscriber for topic: '{topic}' with message type: '{msg_class.__name__}'")
            subscriber = self.create_subscription(
                msg_class, topic, self.message_callback(topic), 10
            )
            self.msg_subscribers[topic] = subscriber

    def message_callback(self, topic_name):
        def callback(msg):
            self.get_logger().info(f"Received message on '{topic_name}': {msg}")
        return callback

    def subscribe_to_topics(self):
        # Example topics to subscribe to (directly specified in the code)
        topics = [
            ("/camera/color/image_raw", "sensor_msgs.msg.Image"),
            ("/drone0/mavros/battery", "sensor_msgs.msg.BatteryState"),
            ("/drone0/mavros/state", "mavros_msgs.msg.State"),
            ("/drone0/mavros/local_position/pose", "geometry_msgs.msg.PoseStamped"),
            ("/drone0/mavros/local_position/velocity_body", "geometry_msgs.msg.TwistStamped"),
            ("mission_status_topic", "vyom_mission_msgs.msg.MissionStatus"),
            ("drone0/mavros/global_position/rel_alt", "std_msgs.msg.Float64"),
            ("Dvid", "vyom_msg.msg.Dvid"),
            ("access", "vyom_msg.msg.Access")
        ]

        for topic, msg_type in topics:
            self.setup_subscriber(topic, msg_type)


def main(args=None):
    rclpy.init(args=args)
    ros_msg_subscriber = RosSystemMsgSubscriber()

    # Subscribe to topics defined directly in the code
    ros_msg_subscriber.subscribe_to_topics()

    # Spin to keep the subscriber node active and listening for messages
    rclpy.spin(ros_msg_subscriber)

    ros_msg_subscriber.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
