import time
import threading
import os
import json
import base64
import uuid
from typing import Callable, Optional
from awscrt import mqtt
from awsiot import mqtt_connection_builder
from concurrent.futures import TimeoutError
from vyomcloudbridge.utils.configs import Configs
from vyomcloudbridge.utils.logger_setup import setup_logger
from vyomcloudbridge.constants.constants import (
    cert_file_path,
    pri_key_file_path,
    root_ca_file_path,
    MQTT_ENTPOINT,
)



class MqttMachineClient:
    def __init__(
        self,
        message_callback: Optional[Callable] = None,
        log_level=None,
    ):
        try:
            self.logger = setup_logger(name=__name__, show_terminal=False, log_level=log_level)
            self.machine_config = Configs.get_machine_config()
            self.machine_id = self.machine_config.get("machine_id", "-") or "-"
            self.endpoint = MQTT_ENTPOINT
            self.cert_path = cert_file_path
            self.pri_key_path = pri_key_file_path
            self.root_ca_path = root_ca_file_path
            self.message_callback = message_callback
            self.client_id = f"machine{self.machine_id}Prod-{uuid.uuid4().hex[:8]}"

            self._verify_cert_files()

            # Connection state tracking
            self.is_connected = False
            self.connection_lock = threading.Lock()
            self._connection_in_progress = False

            # Subscription tracking
            self.subscribed_topics = set()

            # Connection and reconnection parameters
            self.max_reconnect_attempts = 5
            self.base_reconnect_delay = 1  # Base delay in seconds
            self.max_reconnect_delay = 60

            # Initialize the MQTT connection
            self.mqtt_connection = None
            self._create_mqtt_connection()

            # Start a connection monitoring thread
            self._start_backgd_conn_monitor()
        except Exception as e:
            self.logger.error(f"Error init MqttMachineClient: {str(e)}")
            raise

    def _verify_cert_files(self):
        for file_path in [self.cert_path, self.pri_key_path, self.root_ca_path]:
            if not os.path.exists(file_path):
                self.logger.error(f"ERROR: File not found: {file_path}")
                raise FileNotFoundError(f"Required file not found: {file_path}")
            else:
                with open(file_path, "r") as f:
                    pass

    def _create_mqtt_connection(self):
        """Create a new MQTT connection with exponential backoff"""
        with self.connection_lock:  # Acquire lock to prevent concurrent attempts
            if self.is_connected:
                self._connection_in_progress = False
                self.logger.info("Connection already established, skipping reconnection")
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
                            keep_alive_secs=1200,  # 20 minutes
                            ping_timeout_ms=3000,
                            on_connection_interrupted=self._on_connection_interrupted,
                            on_connection_resumed=self._on_connection_resumed,
                        )

                        # Connect to AWS IoT Core
                        connect_future = self.mqtt_connection.connect()
                        connect_future.result(timeout=10)  # Wait for connection
                        self.is_connected = True
                        self.logger.info("Successfully connected to AWS IoT Core")

                        self._resubscribe_to_topics()
                        return

                    except Exception as e:
                        self.logger.error(
                            f"AWS IoT core connection attempt {attempt + 1} failed: {str(e)}"
                        )
                        if attempt < self.max_reconnect_attempts - 1:
                            time.sleep(delay)

                # If all attempts fail
                self.logger.error(
                    "Failed to establish MQTT connection after multiple attempts"
                )
                raise ConnectionError("Could not connect to AWS IoT Core")

            finally:
                self._connection_in_progress = False

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
            self.logger.error(f"Connection resume failed with return code: {return_code}")

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
                subscribe_future.result(timeout=10)
                self.logger.info(f"Resubscribed to topic: {topic}")
            except Exception as e:
                self.logger.error(f"Failed to resubscribe to {topic}: {str(e)}")

    def _start_backgd_conn_monitor(self):
        """
        Start a background thread to monitor connection health
        Uses built-in AWS IoT SDK reconnection mechanisms
        """

        def monitor_connection():
            while True:
                try:
                    if not self.is_connected:
                        self.logger.warning("Connection is down. Attempting to reconnect...")
                        self._create_mqtt_connection()
                    time.sleep(30)
                except Exception as e:
                    self.logger.error(f"Connection monitoring failed: {str(e)}")

        # Start monitoring in a daemon thread
        monitor_thread = threading.Thread(target=monitor_connection, daemon=True)
        monitor_thread.start()

    def message_callback(self, topic, payload, **kwargs):
        try:
            self.logger.info(f"Received message from topic '{topic}': {json.loads(payload)}")
            if self.message_callback:
                self.message_callback(topic, payload)
            else:
                self.logger.info("No callback provided, skipping callback execution")
        except Exception as e:
            self.logger.error(f"Error in calling callback MqttMachineClient: {str(e)}")

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
                self.subscribed_topics.add(topic)
                self.logger.debug(
                    "Warning: MQTT connection not established, skipping for now, will get auto subscribed later..."
                )
                return

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

    def publish_message(self, topic: str, payload, retain: bool = False):
        """
        Publish message with connection state check
        """
        try:
            path_parts = topic.split("/")
            if len(path_parts) > 8:
                self.logger.error(
                    "Topic length exceeded - a maximum of 8 sub-parts are allowed in a topic."
                )
                return False

            is_connection_tried = self._connection_in_progress
            with self.connection_lock:
                if not self.is_connected and is_connection_tried:
                    self.logger.error(
                        f"Publish to {topic} failed: aws iot core is not connected"
                    )
                    return False

            # Outside the lock, create connection if needed
            if not self.is_connected:
                self._create_mqtt_connection()
            self.logger.info(f"mqtt data publishing...... to topic: {topic}")
            publish_future, _ = self.mqtt_connection.publish(
                topic=topic, payload=payload, qos=mqtt.QoS.AT_LEAST_ONCE, retain=retain
            )
            publish_future.result(timeout=10)

            self.logger.info(f"mqtt data published to topic: {topic}")
            return True
        except TimeoutError:
            self.logger.error(f"Publish to {topic} failed: TimeoutError")
            return False
        except Exception as e:
            self.logger.error(
                f"Publish to {topic} failed: {str(e)} , message_type={type(payload)}"
            )
            return False

    def close_connection(self):
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
