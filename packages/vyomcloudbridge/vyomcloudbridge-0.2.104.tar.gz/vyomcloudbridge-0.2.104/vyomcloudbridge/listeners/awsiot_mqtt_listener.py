# vyomcloudbridge/listeners/awsiot_mqtt_listener.py
import base64
import json
import logging
import os
import threading
import time
import uuid
from typing import Callable
from awscrt import mqtt
from awsiot import mqtt_connection_builder
from concurrent.futures import TimeoutError
from vyomcloudbridge.utils.configs import Configs
from vyomcloudbridge.utils.logger_setup import setup_logger

# import sys
# import os
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../utils')))
# from abc_listener import AbcListener
from vyomcloudbridge.utils.abc_listener import AbcListener

from vyomcloudbridge.constants.constants import (
    cert_file_path,
    pri_key_file_path,
    root_ca_file_path,
    MQTT_ENTPOINT,
)


class AwsiotMqttListener(AbcListener):
    def __init__(self, daemon: bool = False, log_level=None):
        try:
            super().__init__(
                multi_thread=False, daemon=daemon, log_level=log_level
            )  # TODO: we can remove multi_thread later
            self.logger.info("AwsiotMqttListener initializing...")
            # compulsory
            self.channel = "mavlink"

            self.endpoint = MQTT_ENTPOINT
            self.cert_path = cert_file_path
            self.pri_key_path = pri_key_file_path
            self.root_ca_path = root_ca_file_path

            # machine configs
            self.machine_config = Configs.get_machine_config()
            self.machine_id = self.machine_config.get("machine_id", "-") or "-"
            self.client_id = f"machine{self.machine_id}Prod-vyomlistener"  # using fixed client_id for listener
            self.subscribe_topic_1 = f"vyom-mqtt-msg/{self.machine_id}/"
            self.subscribe_topic_2 = f"vyom-mqtt-msg/{self.machine_id}/#"
            self._verify_cert_files()

            # Connection state tracking
            self.daemon = daemon
            self.is_connected = False
            self.connection_lock = threading.Lock()
            self._connection_in_progress = False

            # Subscription tracking
            self.subscribed_topics = set()

            # Connection and reconnection parameters
            self.max_reconnect_attempts = 3
            self.base_reconnect_delay = 2  # Base delay in seconds
            self.max_reconnect_delay = 60

            self.connection_health_check_delay = 30  # seconds

            # Initialize the MQTT connection
            self.mqtt_connection = None
            if self.daemon:
                # self._start_background_connection()
                self._start_backgd_conn_monitor()
                self.logger.info(
                    "AwsiotMqttListener initialization in background thread started..."
                )
            else:
                self._create_mqtt_connection()
                self._start_backgd_conn_monitor()
                self.logger.info("AwsiotMqttListener initialized successfully!")

        except Exception as e:
            self.logger.error(f"Error init AwsiotMqttListener: {str(e)}")
            raise

    def _create_mqtt_connection(self):
        """Create a new MQTT connection with exponential backoff"""
        with self.connection_lock:  # Acquire lock to prevent concurrent attempts
            if self.is_connected:
                self._connection_in_progress = False
                self.logger.info(
                    "Connection already established, skipping reconnection"
                )
                return

            self._connection_in_progress = True
            try:
                for attempt in range(self.max_reconnect_attempts):
                    try:
                        # Use exponential backoff for reconnection attempts
                        delay = min(
                            self.base_reconnect_delay * (2**attempt),
                            self.max_reconnect_delay,
                        )

                        # Create MQTT connection with keep-alive and will message
                        self.mqtt_connection = mqtt_connection_builder.mtls_from_path(
                            endpoint=self.endpoint,
                            cert_filepath=self.cert_path,
                            pri_key_filepath=self.pri_key_path,
                            ca_filepath=self.root_ca_path,
                            client_id=self.client_id,
                            clean_session=False,
                            keep_alive_secs=10,  # 10 seconds - PING every 10 seconds
                            ping_timeout_ms=2000,  # 2 seconds - If no PONG response within 2 seconds, connection is considered lost
                            on_connection_interrupted=self._on_connection_interrupted,
                            on_connection_resumed=self._on_connection_resumed,
                        )

                        # Connect to AWS IoT Core
                        connect_future = self.mqtt_connection.connect()
                        connect_future.result()  # Wait for connection
                        self.is_connected = True
                        self.logger.info("Successfully connected to AWS IoT Core")

                        self._resubscribe_to_topics()
                        return

                    except Exception as e:
                        self.logger.debug(
                            f"Warning: aws_mqtt_listener connection attempt {attempt + 1} failed: {str(e)}"
                        )
                        if attempt < self.max_reconnect_attempts - 1:
                            time.sleep(delay)

                # If all attempts fail
                raise ConnectionError(
                    f"Could not connect to AWS IoT Core after {self.max_reconnect_attempts} attempts"
                )

            finally:
                self._connection_in_progress = False

    # def _start_background_connection(self):
    #     """Start connection attempts in a background thread"""

    #     def connection_thread():
    #         while True:
    #             try:
    #                 if not self.is_connected and not self._connection_in_progress:
    #                     self._create_mqtt_connection()
    #                     self._start_backgd_conn_monitor()
    #                 time.sleep(self.connection_health_check_delay)
    #             except Exception as e:
    #                 self.logger.error(f"Background connection thread error: {str(e)}")
    #                 time.sleep(self.connection_health_check_delay)

    #     # Start connection thread
    #     connection_thread = threading.Thread(target=connection_thread, daemon=True)
    #     connection_thread.start()

    def _start_backgd_conn_monitor(self):
        """
        Start a background thread to monitor connection health
        Uses built-in AWS IoT SDK reconnection mechanisms
        """

        def monitor_connection():
            while True:
                try:
                    if not self.is_connected:
                        self._create_mqtt_connection()
                    time.sleep(self.connection_health_check_delay)
                except Exception as e:
                    self.logger.error(
                        f"aws_mqtt_listener connection monitoring failed: {str(e)}"
                    )
                    time.sleep(self.connection_health_check_delay)

        # Start monitoring in a daemon thread
        monitor_thread = threading.Thread(target=monitor_connection, daemon=True)
        monitor_thread.start()

    def _verify_cert_files(self):
        for file_path in [self.cert_path, self.pri_key_path, self.root_ca_path]:
            if not os.path.exists(file_path):
                self.logger.error(f"ERROR: File not found: {file_path}")
                raise FileNotFoundError(f"Required file not found: {file_path}")
            else:
                with open(file_path, "r") as f:
                    pass

    def _on_connection_interrupted(self, connection, error, **kwargs):
        """
        Callback when connection is interrupted
        This method is called automatically by AWS IoT SDK
        """
        self.logger.warning(f"Connection interrupted: {error}")
        with self.connection_lock:
            self.is_connected = False

    def _on_connection_resumed(
        self, connection, return_code, session_present, **kwargs
    ):
        """
        Callback when connection is resumed
        This method is called automatically by AWS IoT SDK
        """
        if return_code == mqtt.ConnectReturnCode.ACCEPTED:
            self.logger.info("Connection resumed successfully")

            with self.connection_lock:
                self.is_connected = True

            # Resubscribe to topics if session is not persistent
            if not session_present:
                self._resubscribe_to_topics()

        else:
            self.logger.error(
                f"Connection resume failed with return code: {return_code}"
            )

    def _resubscribe_to_topics(self):
        """
        Resubscribe to all previously subscribed topics
        """
        for topic in self.subscribed_topics:
            try:
                subscribe_future, _ = self.mqtt_connection.subscribe(
                    topic=topic,
                    qos=mqtt.QoS.AT_LEAST_ONCE,
                    callback=self.message_callback,
                )
                subscribe_future.result()
                self.logger.info(f"Resubscribed to topic: {topic}")
            except Exception as e:
                self.logger.error(f"Failed to resubscribe to {topic}: {str(e)}")

    def message_callback(self, topic: str, payload, **kwargs):
        """
        @brief Callback function to handle incoming MQTT messages.

        This method is invoked when a message is received on a subscribed MQTT topic.
        It parses the payload, logs relevant information, extracts the machine ID from the topic,
        and delegates the message to the appropriate handler for further processing.

        @param topic (str): The MQTT topic from which the message was received.
        @param payload: The message payload, which can be a dictionary or a JSON-encoded string.
        @param **kwargs: Additional keyword arguments.

        @details
            - If the payload is not a dictionary, attempts to parse it as JSON.
            - Logs the received message and its type and data.
            - Extracts the machine ID from the topic (expects topic to have 5 parts).
            - Calls `handle_message` with the message type, data, machine ID, and a default value.
            - Handles and logs any exceptions that occur during processing.
        """
        # self.logger.debug(f"Received message from topic: {topic} type: {type(payload)}")
        try:
            if isinstance(payload, dict):
                msg = payload
            else:
                try:
                    if isinstance(payload, bytes):
                        msg = payload.decode("utf-8")
                    if isinstance(payload, str):
                        msg = json.loads(payload)

                except Exception as e:
                    self.logger.error(f"Error parsing payload: {e}")
                    return

            # Split the topic and check the machine ID
            # Sample out vyom-mqtt-msg/157/gcs_mav/velocity_topic/1747301291667.json
            topic_parts = topic.split("/")
            self.logger.debug(f"incoming machine id: {topic_parts[1]}")

            if len(topic_parts) == 5:
                self.logger.debug(
                    f"topic_parts 1 {topic_parts[1]} 2: {topic_parts[2]} 3: {topic_parts[3]}"
                )
                self.logger.debug(f"type-{type(msg)}, msg-{msg}")
                self.handle_message(
                    topic_parts[3], json.loads(msg), topic_parts[1], topic_parts[2]
                )

        except Exception as e:
            self.logger.error(f"Error in calling callback AwsiotMqttListener: {str(e)}")

    def subscribe_to_topic(self, topic):
        """
        Subscribe to a topic with connection state awareness
        """
        try:
            is_connection_tried = self._connection_in_progress
            with self.connection_lock:
                if not self.is_connected and is_connection_tried:
                    self.logger.error(
                        f"Subscription to {topic} failed:: aws iot core is not connected"
                    )
                    raise

            if not self.is_connected:
                self._create_mqtt_connection()

            subscribe_future, _ = self.mqtt_connection.subscribe(
                topic=topic, qos=mqtt.QoS.AT_LEAST_ONCE, callback=self.message_callback
            )
            subscribe_future.result(timeout=10)

            # Track subscribed topics
            self.subscribed_topics.add(topic)
            self.logger.info(f"Subscribed to topic: {topic}")

        except Exception as e:
            self.logger.error(f"Subscription to {topic} failed: {str(e)}")
            raise

    def start(self):
        try:
            self.is_running = True
            self.subscribe_to_topic(self.subscribe_topic_1)
            self.subscribe_to_topic(self.subscribe_topic_2)
            # self.subscribe_to_topic(self.subscribe_topic_3)
            # self.subscribe_to_topic(self.subscribe_topic_4)
            self.logger.info("Listening for messages... Press Ctrl+C to exit")
        except Exception as e:
            self.logger.error(f"Failed to close mqtt cleanup cleanup: {str(e)}")

    def stop(self):
        self.is_running = False
        try:
            self.cleanup()
        except Exception as e:
            self.logger.error(f"Failed to close mqtt cleanup cleanup: {str(e)}")

    def cleanup(self):
        """Gracefully close the MQTT connection"""
        try:
            if self.mqtt_connection:
                disconnect_future = self.mqtt_connection.disconnect()
                disconnect_future.result(timeout=10)
                self.mqtt_connection = None

            with self.connection_lock:
                self.is_connected = False

            self.logger.info("MQTT AWS IoT Core connection closed successfully")

        except Exception as e:
            self.logger.error(f"Failed to close MQTT connection: {str(e)}")
        super().cleanup()


def main():
    """
    Main entry point for the queue worker service.
    """
    time.sleep(1)

    vyom_listener = AwsiotMqttListener()
    try:
        # vyom_listener.message_callback("mission", {'type': 'mission', 'data': {'id': 202504291862, 'owner_data': {'id': 9, 'account_id': 'a-ufd75sv4iv', 'name': 'Caleb', 'email': 'caleb@vyomos.org'}, 'created_at': '2025-05-01T14:08:35.238569Z', 'updated_at': '2025-05-01T14:08:35.238593Z', 'name': 'Start Mission', 'mission_type': 'start_mission', 'mission_status': 1, 'description': 'Initiate a Start Mission.', 'json_data': {'source_command': 'HQ'}, 'mission_date': '2025-05-01', 'start_time': '2025-05-01T14:08:35.103000Z', 'end_time': None, 'creator': 9, 'owner': 9, 'campaign': 1, 'machine': 85, 'machine_id': 85, 'machine_uid': '1234'}})

        test_payload = {
            "type": "mission",
            "data": {
                "id": 202504291862,
                "owner_data": {
                    "id": 9,
                    "account_id": "a-ufd75sv4iv",
                    "name": "Caleb",
                    "email": "caleb@vyomos.org",
                },
                "created_at": "2025-05-01T14:08:35.238569Z",
                "updated_at": "2025-05-01T14:08:35.238593Z",
                "name": "Start Mission",
                "mission_type": "start_mission",
                "mission_status": 2,
                "description": "Initiate a Start Mission.",
                "json_data": {"source_command": "HQ"},
                "mission_date": "2025-05-01",
                "start_time": "2025-05-01T14:08:35.238569Z",
                "end_time": None,
                "creator": 9,
                "owner": 9,
                "campaign": 1,
                "machine": 85,
                "machine_id": 85,
                "machine_uid": "1234",
            },
        }

        vyom_listener.message_callback(
            "vyom-mqtt-msg/85/hq-1/velocity_topic/1746108515103.json",
            json.dumps(test_payload),
        )

        # Received message from topic 'vyom-mqtt-msg/85/hq-1/velocity_topic/1746108515103.json': {'type': 'mission', 'data': {'id': 202504291862, 'owner_data': {'id': 9, 'account_id': 'a-ufd75sv4iv', 'name': 'Caleb', 'email': 'caleb@vyomos.org'}, 'created_at': '2025-05-01T14:08:35.238569Z', 'updated_at': '2025-05-01T14:08:35.238593Z', 'name': 'Start Mission', 'mission_type': 'start_mission', 'mission_status': 1, 'description': 'Initiate a Start Mission.', 'json_data': {'source_command': 'HQ'}, 'mission_date': '2025-05-01', 'start_time': '2025-05-01T14:08:35.103000Z', 'end_time': None, 'creator': 9, 'owner': 9, 'campaign': 1, 'machine': 85, 'machine_id': 85, 'machine_uid': '1234'}}
        # vyom_listener.start()

        # Keep the main thread running
        while vyom_listener.is_running:
            time.sleep(10)
    except KeyboardInterrupt:
        pass
    finally:
        vyom_listener.stop()


if __name__ == "__main__":
    main()
