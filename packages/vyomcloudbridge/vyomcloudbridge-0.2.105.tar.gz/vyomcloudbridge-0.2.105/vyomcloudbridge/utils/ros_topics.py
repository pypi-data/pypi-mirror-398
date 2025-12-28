import json
import time
import rclpy
from rclpy.node import Node
from vyomcloudbridge.utils.logger_setup import setup_logger


class ROSTopic:
    def __init__(self, discovery_timeout=5.0, log_level=None):
        """
        Initialize the ROS topic discoverer.

        Args:
            discovery_timeout: Time in seconds to wait for topic discovery
        """
        self.logger = setup_logger(
            name=self.__class__.__module__ + "." + self.__class__.__name__,
            show_terminal=False,
            log_level=log_level,
        )
        try:
            if not rclpy.ok():  
                rclpy.init(args=None)
        except Exception as e:
            self.logger.warning(f"Failed to initialize ROS: {e}")
        self.topic_node = Node("topic_discoverer")
        self.discovery_timeout = discovery_timeout

    def serialize_topic_list(self):
        """
        Get a complete list of ROS topics and their types, formatted as a list of dictionaries.

        Returns:
            str: JSON string containing topic info dictionaries
        """
        # Allow time for topic discovery
        start_time = time.time()
        prev_topic_count = 0

        print(f"Starting topic discovery (timeout: {self.discovery_timeout}s)...")

        while True:
            rclpy.spin_once(self.topic_node, timeout_sec=0.1)
            topics = self.topic_node.get_topic_names_and_types()
            current_topic_count = len(topics)

            if current_topic_count > prev_topic_count:
                print(f"Discovered {current_topic_count} topics so far...")
                prev_topic_count = current_topic_count

            if time.time() - start_time >= self.discovery_timeout:
                break

            time.sleep(0.1)

        # Format topics as a list of dictionaries
        topic_list = []
        for topic_name, topic_types in topics:
            for topic_type in topic_types:
                formatted_type = topic_type.replace("/", ".")
                topic_list.append(
                    {"name": None, "data_type": formatted_type, "topic": topic_name}
                )

        print(f"Discovery complete! Found {len(topic_list)} topic entries.")

        return topic_list

    def cleanup(self, shutdown_ros=False):  # dont shutdown rclpy by default
        """Clean up resources. Optionally shut down ROS."""
        try:
            self.topic_node.destroy_node()
            self.logger.info("Node destroyed successfully")
        except Exception as e:
            self.logger.error(f"Error in destroying node: {e}")

        if shutdown_ros:
            try:
                rclpy.shutdown()
                self.logger.info("ROS shutdown completed")
            except Exception as e:
                self.logger.error(f"Error during ROS shutdown: {e}")


if __name__ == "__main__":
    try:
        # Create the topic discoverer with a 5 second discovery timeout
        topics_discoverer = ROSTopic(discovery_timeout=5.0)

        # Get the topic list with sufficient discovery time
        topic_list = topics_discoverer.serialize_topic_list()
        print("topic_list-", topic_list)

    except Exception as e:
        print("errpor in fetching ros packages", str(e))
    finally:
        topics_discoverer.cleanup(shutdown_ros=True)
