import json
import os
import time

import rclpy
from rclpy.node import Node
from ament_index_python.packages import get_package_share_directory
from vyomcloudbridge.utils.logger_setup import setup_logger


# Gives information about the message type and its location in the package share directory.
# This is useful for debugging and understanding the message types used in the system.
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
        Get a complete list of ROS topics, their types, and .msg file locations.

        Returns:
            str: JSON string containing topic names, types, and msg file paths
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

            elapsed_time = time.time() - start_time
            if elapsed_time >= self.discovery_timeout:
                break

            time.sleep(0.1)

        # Resolve message paths for each topic
        topic_info = {}

        for topic_name, topic_types in topics:
            if not topic_types:
                continue

            msg_type = topic_types[0]
            msg_path = "Not found"

            if "/msg/" in msg_type:
                try:
                    pkg_name, relative_msg = msg_type.split("/msg/")
                    share_dir = get_package_share_directory(pkg_name)
                    full_path = os.path.join(share_dir, "msg", f"{relative_msg}.msg")
                    if os.path.exists(full_path):
                        msg_path = full_path
                    else:
                        msg_path = "Message file not found in share directory"
                except Exception as e:
                    msg_path = f"Error locating message path: {e}"

            topic_info[topic_name] = {"type": msg_type, "msg_path": msg_path}

        serialized_topics = json.dumps(topic_info, indent=2)

        print(f"Discovery complete! Found {len(topic_info)} topics.")
        for topic, info in topic_info.items():
            print(f"{topic} -> type: {info['type']}, path: {info['msg_path']}")

        return serialized_topics

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
        topics_discoverer = ROSTopic(discovery_timeout=5.0)
        topic_list_json = topics_discoverer.serialize_topic_list()

        with open("ros_topics.json", "w") as f:
            f.write(topic_list_json)

        print("Topics saved to ros_topics.json")

    finally:
        if "topics_discoverer" in locals():
            topics_discoverer.cleanup(shutdown_ros=True)
