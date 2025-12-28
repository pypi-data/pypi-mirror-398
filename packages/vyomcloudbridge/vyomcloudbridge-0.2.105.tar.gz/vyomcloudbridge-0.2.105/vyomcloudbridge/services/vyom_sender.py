import threading
import time
import json
import os
from vyomcloudbridge.utils.configs import Configs
from vyomcloudbridge.utils.logger_setup import setup_logger
from vyomcloudbridge.senders.awsiot_mqtt_sender import AwsiotMqttSender
from vyomcloudbridge.utils.install_specs import InstallSpecs


class VyomSender:
    _instance = None
    _lock = threading.Lock()

    # def __new__(cls, *args, **kwargs):
    #     if cls._instance is None:
    #         with cls._lock:
    #             if cls._instance is None:
    #                 cls._instance = super(VyomSender, cls).__new__(cls)
    #                 print("VyomSender singleton initialized")
    #     print("Vyom Sender client service started")
    #     return cls._instance

    def __init__(
        self,
        log_level=None,
    ):
        try:
            """Initialize the Vyom Sender client"""
            if hasattr(self, "senders"):
                return
            self.logger = setup_logger(
                name=self.__class__.__module__ + "." + self.__class__.__name__,
                show_terminal=False,
                log_level=log_level,
            )
            self.logger.info("Starting VyomSender...")
            self.install_specs = InstallSpecs()
            self.machine_config = Configs.get_machine_config()
            self.machine_id = self.machine_config.get("machine_id", "-") or "-"
            self.logger.info("Setting up all senders...")
            self.senders = {"mqtt": AwsiotMqttSender(daemon=True, log_level=log_level)}
            if self.install_specs.is_full_install:
                from vyomcloudbridge.senders.mav_sender import MavSender

                self.senders["mavlink"] = MavSender(log_level=log_level)
            self.logger.info("Setup of all senders Done!")
            # TODO, need to handle gcs_mav, machine,
            self.network = self._load_network_config()
            self.logger.info("VyomSender started sucessfully!")
        except Exception as e:
            self.logger.error("VyomSender starting failed")

    def _load_network_config(self):
        """Load network configuration from networks.json file"""
        try:
            # Get the path to the constants directory relative to this file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            constants_dir = os.path.join(current_dir, "..", "constants")
            networks_file = os.path.join(constants_dir, "networks.json")

            with open(networks_file, "r") as f:
                network_config = json.load(f)
                self.logger.info(
                    "Successfully loaded network configuration from networks.json"
                )
                return network_config
        except FileNotFoundError:
            self.logger.error(
                f"Networks configuration file not found at {networks_file}"
            )
            return {
                "s3": [{"device_id": "s3", "channel": "mqtt"}],
                "gcs_mqtt": [{"device_id": "gcs_mqtt", "channel": "mqtt"}],
            }
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing networks.json: {str(e)}")
            return {
                "s3": [{"device_id": "s3", "channel": "mqtt"}],
                "gcs_mqtt": [{"device_id": "gcs_mqtt", "channel": "mqtt"}],
            }
        except Exception as e:
            self.logger.error(
                f"Unexpected error loading network configuration: {str(e)}"
            )
            return {
                "s3": [{"device_id": "s3", "channel": "mqtt"}],
                "gcs_mqtt": [{"device_id": "gcs_mqtt", "channel": "mqtt"}],
            }

    def send_message(self, message, message_type, destination_ids, data_source, topic):
        """
        Send message to the destination ids
        Args:
            message: The message to be sent, it can be binary, json, image (progressive json), etc.
            message_type: The type of the message, it can be "binary", "json", "image", etc.
            destination_ids: The destination ids to send the message to
            data_source: The source of the data, it can be "telemetry", "front_camera_image" etc.
            topic: The topic to send the message to
        Returns:
            success: True if the message is sent successfully, False otherwise
            remaining_dest_ids: The destination ids that the message is not sent to
        """
        success = True
        remaining_dest_ids = []
        for destination_id in destination_ids:
            if self.network.get(destination_id, None) is not None and len(
                self.network.get(destination_id, None)
            ):
                try:
                    target_des_id = self.network.get(destination_id, None)[0].get(
                        "device_id", None
                    )
                    target_channel = self.network.get(destination_id, None)[0].get(
                        "channel", None
                    )
                    communicator = self.senders.get(target_channel)
                    result = communicator.send_message(
                        message=message,
                        message_type=message_type,
                        data_source=data_source,
                        target_des_id=target_des_id,
                        destination_id=destination_id,
                        source_id=self.machine_id,
                        topic=topic,
                    )
                    if not result:
                        success = False
                        remaining_dest_ids.append(destination_id)
                except Exception as e:
                    self.logger.error(
                        f"error in sending messages to {destination_id} via {target_channel},  error: {str(e)}"
                    )
                    success = False
                    remaining_dest_ids.append(destination_id)
            else:
                self.logger.error(
                    f"Error in sending messages to {destination_id}, no target found for teh destination"
                )
                success = False
                remaining_dest_ids.append(destination_id)
        return success, remaining_dest_ids

    def cleanup(self):
        """Call cleanup function of every sender instance and reset singleton"""
        for sender_name, sender_instance in self.senders.items():
            try:
                sender_instance.cleanup()
                self.logger.info(f"Successfully cleaned up {sender_name} sender")
            except Exception as e:
                self.logger.error(f"Error cleaning up {sender_name} sender: {str(e)}")

        # VyomSender._instance = None
        # self.logger.info("VyomSender cleanup completed and singleton reference reset")


# Initialize the singleton instance


def main():
    """
    Main entry point for the queue worker service.
    """
    vyom_sender = VyomSender()
    try:
        time.sleep(10)
    except KeyboardInterrupt:
        pass
    finally:
        vyom_sender.cleanup()


if __name__ == "__main__":
    main()
