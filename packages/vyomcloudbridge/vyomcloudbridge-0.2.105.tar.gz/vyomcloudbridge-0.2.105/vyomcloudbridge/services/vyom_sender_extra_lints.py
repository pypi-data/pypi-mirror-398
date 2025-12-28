import threading
import time

from vyomcloudbridge.senders.awsiot_mqtt_sender import AwsiotMqttSender
from vyomcloudbridge.senders.mav_sender import MavSender
from vyomcloudbridge.utils.configs import Configs
from vyomcloudbridge.utils.logger_setup import setup_logger


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
    ):
        try:
            """Initialize the Vyom Sender client"""
            if hasattr(self, 'senders'):
                return
            self.logger = setup_logger(
                name=self.__class__.__module__ + '.' + self.__class__.__name__,
                show_terminal=False,
            )
            self.logger.info('Starting VyomSender...')
            self.machine_config = Configs.get_machine_config()
            self.machine_id = self.machine_config.get('machine_id', '-') or '-'
            self.logger.info('Setting up all senders...')
            self.senders = {'mqtt': AwsiotMqttSender(daemon=True), 'mavlink': MavSender()}
            self.logger.info('Setup of all senders Done!')
            # TODO, need to handle gcs_mav, machine,
            self.network = {
                's3': [
                    {'device_id': 's3', 'channel': 'mqtt'},
                ],
                'gcs_mav': [
                    {'device_id': 'gcs_mav', 'channel': 'mavlink', 'system_id': 255},
                ],
                'gcs_mqtt': [
                    {'device_id': 'gcs_mqtt', 'channel': 'mqtt'},
                ],
            }
            self.logger.info('VyomSender started sucessfully!')
        except Exception:
            self.logger.error('VyomSender starting failed')

    def send_message(self, message, message_type, destination_ids, data_source, topic):
        """
        Send message to the destination ids
        Args:
            message: The message to be sent, it can be binary, json, image (progressive json), etc.
            message_type: The type of the message, it can be 'binary', 'json', 'image', etc.
            destination_ids: The destination ids to send the message to
            data_source: The source of the data, it can be 'telemetry', 'front_camera_image' etc.
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
                        'device_id', None
                    )
                    target_channel = self.network.get(destination_id, None)[0].get(
                        'channel', None
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
                        f'error in sending messages to {destination_id} via {target_channel},  error: {str(e)}'
                    )
                    success = False
                    remaining_dest_ids.append(destination_id)
            else:
                self.logger.error(
                    f'Error in sending messages to {destination_id}, no target found for teh destination'
                )
                success = False
                remaining_dest_ids.append(destination_id)
        return success, remaining_dest_ids

    def cleanup(self):
        """Call cleanup function of every sender instance and reset singleton"""
        for sender_name, sender_instance in self.senders.items():
            try:
                sender_instance.cleanup()
                self.logger.info(f'Successfully cleaned up {sender_name} sender')
            except Exception as e:
                self.logger.error(f'Error cleaning up {sender_name} sender: {str(e)}')

        # VyomSender._instance = None
        # self.logger.info("VyomSender cleanup completed and singleton reference reset")


# Initialize the singleton instance
# vyom_sender = VyomSender()


def main():
    '''
    Main entry point for the queue worker service.
    '''
    vyom_sender = VyomSender()
    try:
        time.sleep(10)
    except KeyboardInterrupt:
        pass
    finally:
        vyom_sender.cleanup()


if __name__ == '__main__':
    main()
