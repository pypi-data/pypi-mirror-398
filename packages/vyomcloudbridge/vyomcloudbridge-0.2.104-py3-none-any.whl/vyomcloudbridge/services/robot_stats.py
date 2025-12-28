import time
import threading

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSReliabilityPolicy
from sensor_msgs.msg import NavSatFix

from vyomcloudbridge.utils.common import ServiceAbstract
from vyomcloudbridge.services.root_store import RootStore


class RobotPosition(Node, ServiceAbstract):

    def __init__(self):
        super().__init__("robot_position")
        self.pos_subscription = None
        self.root_store = None

    def pos_listener_callback(self, msg):
        print(
            f"Received Global Position -> lat: {msg.latitude:.6f}, lon: {msg.longitude:.6f}, alt: {msg.altitude:.2f}"
        )
        try:
            epoch_ms = int(time.time() * 1000)
            location = {
                "lat": msg.latitude,
                "long": msg.longitude,
                "alt": msg.altitude,
                "timestamp": epoch_ms,
            }
            self.root_store.set_data("location", location)
        except Exception as e:
            print("Error occurred -", str(e))

    def start(self):
        qos_profile = QoSProfile(reliability=QoSReliabilityPolicy.BEST_EFFORT, depth=10)
        self.pos_subscription = self.create_subscription(
            NavSatFix,
            "/drone0/mavros/global_position/global",
            self.pos_listener_callback,
            qos_profile,
        )
        self.root_store = RootStore()
        self.get_logger().info("RobotPosition started")

    def stop(self):
        self.get_logger().info("Stopping RobotPosition service...")
        self.cleanup()

    def cleanup(self):
        if self.root_store:
            self.root_store.cleanup()
        self.get_logger().info("RobotPosition service stopped.")
        self.pos_subscription = None
        self.root_store = None


class RobotStat(ServiceAbstract):

    def __init__(self, log_level=None):
        super().__init__(log_level=log_level)
        self.logger.info("Initializing RobotStat...")
        self.is_running = False
        self.spin_thread = None

        try:
            rclpy.init(args=None)
        except Exception as e:
            self.logger.warning(f"Failed to initialize ROS: {e}")

        self.robot_pos = RobotPosition()
        self.logger.info("RobotStat Initialized successfully")

    def start(self):
        try:
            self.logger.info("Starting RobotStat service...")
            self.is_running = True
            self.robot_pos.start()

            def spin_loop():
                while rclpy.ok() and self.is_running:
                    rclpy.spin_once(self.robot_pos, timeout_sec=0.1)
                    time.sleep(0.1)

            self.spin_thread = threading.Thread(target=spin_loop, daemon=True)
            self.spin_thread.start()
            self.logger.info("RobotStat service started!")

        except Exception as e:
            self.logger.error(f"Error starting RobotStat service: {str(e)}")
            self.stop()

    def stop(self):
        try:
            self.logger.info("Stopping RobotStat service...")
            self.is_running = False
            time.sleep(0.2)  # Let spin_once loop exit
            self.robot_pos.stop()
            rclpy.shutdown()
            if self.spin_thread:
                self.spin_thread.join()
            self.logger.info("RobotStat service stopped!")
        except Exception as e:
            self.logger.error(f"Error stopping RobotStat: {str(e)}")

    def cleanup(self):
        pass

    def is_healthy(self):
        return self.is_running

    def __del__(self):
        try:
            self.logger.error("Destructor called. Cleaning up RobotStat")
            self.stop()
        except Exception:
            pass


def main(args=None):
    robot_stat = RobotStat()
    try:
        robot_stat.start()
        time.sleep(10)
        robot_stat.stop()

    finally:
        print("Completed RobotStat service example")


if __name__ == "__main__":
    main()
