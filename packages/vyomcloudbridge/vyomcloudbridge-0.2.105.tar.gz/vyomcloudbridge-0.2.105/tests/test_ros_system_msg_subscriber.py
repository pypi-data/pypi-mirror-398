import rclpy
from rclpy.node import Node
import importlib

from vyomcloudbridge.utils.logger_setup import setup_logger


class RosSystemMsgSubscriber(Node):
    def __init__(self):
        self.logger = setup_logger(
            name=self.__class__.__module__ + "." + self.__class__.__name__,
            show_terminal=False,
        )
        try:
            rclpy.init(args=None)
        except Exception as e:
            self.logger.warning(f"Failed to initialize ROS: {e}")
        super().__init__("ros_system_msg_subscriber")
        self.logger.info("ROS System Message Subscriber Node started.")
        self._is_destroyed = False

    def get_message_class(self, msg_name):
        # Dynamically import the message class from the correct package
        module = importlib.import_module(f"vyom_msg.msg")
        return getattr(module, msg_name)

    def topic_callback(self, msg, topic_name):
        # Handle the received message and log it
        self.logger.info(f"Received on '{topic_name}': {msg}")

    def setup_subscription(self, typ):
        # Subscribe to the topic dynamically based on the type
        msg_class = self.get_message_class(typ)
        topic_name = typ.lower()

        self.create_subscription(
            msg_class, topic_name, lambda msg: self.topic_callback(msg, topic_name), 10
        )

        self.logger.info(
            f"Subscriber created for topic: '{topic_name}' with message type: '{msg_class}'"
        )

    def spin(self):
        """Spin once to allow time for ROS graph to recognize publishers."""
        if self._is_destroyed:
            self.logger.error("Cannot spin: Node has been destroyed")
            return
        try:
            rclpy.spin(self)
        except Exception as e:
            self.logger.error(f"Error in rclpy.spin: {e}")

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
    ros_msg_subscriber = RosSystemMsgSubscriber()

    # Define the message types that you want to subscribe to
    message_types = ["Access", "Accessinfo", "Ack", "Auth", "Dvid"]

    # Set up subscriptions for all the message types
    for msg_type in message_types:
        ros_msg_subscriber.setup_subscription(msg_type)

    ros_msg_subscriber.spin()
    ros_msg_subscriber.cleanup(shutdown_ros=True)


if __name__ == "__main__":
    main()
