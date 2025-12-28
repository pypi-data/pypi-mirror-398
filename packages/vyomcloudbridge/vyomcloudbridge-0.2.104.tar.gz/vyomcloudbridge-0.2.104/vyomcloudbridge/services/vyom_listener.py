# vyomcloudbridge/services/vyom_listener.py
import threading
import time
from vyomcloudbridge.utils.configs import Configs
from vyomcloudbridge.utils.logger_setup import setup_logger
from vyomcloudbridge.listeners.awsiot_mqtt_listener import AwsiotMqttListener
from vyomcloudbridge.utils.install_specs import InstallSpecs

# import sys
# import os
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../listeners')))
# from mqtt_listener import AwsiotMqttListener


class VyomListener:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(VyomListener, cls).__new__(cls)
                    print("VyomListener singleton initialized")
        print("Vyom Listener client service started")
        return cls._instance

    def __init__(self, log_level=None):
        """Initialize the Vyom Listener client"""
        if hasattr(self, "listeners"):
            return

        self.logger = setup_logger(
            name=self.__class__.__module__ + "." + self.__class__.__name__,
            show_terminal=False,
            log_level=log_level,
        )
        self.install_specs = InstallSpecs()
        self.machine_config = Configs.get_machine_config()
        self.machine_id = self.machine_config.get("machine_id", "-") or "-"

        # Corrected listener mapping
        self.logger.info("initializing all listeners...")
        self.listeners = {"mqtt": AwsiotMqttListener(daemon=True)}
        if self.install_specs.is_full_install:
            from vyomcloudbridge.listeners.mav_listener import MavListener

            self.listeners["mavlink"] = MavListener(log_level=log_level)
        self.logger.info("All listeners initialized!")

        self.is_running = False

    def start(self):
        """
        Start all listener services
        """
        if self.is_running:
            self.logger.info("Listeners are already running")
            return

        self.logger.info("Starting all listeners...")

        try:
            for channel, listener in self.listeners.items():
                try:
                    self.logger.info(f"Starting {channel} listener...")
                    listener.start()
                    self.logger.info(f"{channel.upper()} listener started successfully")
                except Exception as e:
                    self.logger.error(f"Failed to start {channel} listener: {str(e)}")

            self.is_running = True
            self.logger.info("All available listeners started successfully")
        except Exception as e:
            self.logger.error(f"Error starting listeners: {str(e)}")
            # Attempt to stop any listeners that might have started
            self.stop()

    def stop(self):
        """
        Stop all listener services
        """
        self.logger.info("Stopping all listeners...")

        for channel, listener in self.listeners.items():
            try:
                self.logger.info(f"Stopping {channel} listener...")
                listener.stop()
                self.logger.info(f"{channel.upper()} listener stopped successfully")
            except Exception as e:
                self.logger.error(f"Failed to stop {channel} listener: {str(e)}")

        self.is_running = False
        self.logger.info("All listeners stopped")

    def is_healthy(self):
        """
        Check if all listeners are healthy
        """
        all_healthy = True
        for channel, listener in self.listeners.items():
            try:
                if hasattr(listener, "is_healthy") and callable(listener.is_healthy):
                    if not listener.is_healthy():
                        self.logger.warning(
                            f"{channel.upper()} listener is not healthy"
                        )
                        all_healthy = False
            except Exception as e:
                self.logger.error(
                    f"Error checking health of {channel} listener: {str(e)}"
                )
                all_healthy = False

        return all_healthy


# Initialize the singleton instance
# vyom_listener = VyomListener()


def main():
    """
    Main entry point for the queue worker service.
    """
    vyom_listener = VyomListener()
    try:
        vyom_listener.start()

        # Keep the main thread running
        while vyom_listener.is_running:
            time.sleep(10)
    except KeyboardInterrupt:
        pass
    finally:
        vyom_listener.stop()


if __name__ == "__main__":
    main()
