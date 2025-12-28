import time
import threading
import os
import json
import ssl
import uuid
from typing import Callable, Optional
import paho.mqtt.client as mqtt
import logging
import socket

mosquito_cert_dir = f"/etc/vyomcloudbridge/certs_mosquitto/"
mosquito_cert_fname = "cert.pem"
mosquito_cert_fpath = os.path.join(mosquito_cert_dir, mosquito_cert_fname)
mosquito_pri_key_fname = "pri.key"
mosquito_pri_key_fpath = os.path.join(mosquito_cert_dir, mosquito_pri_key_fname)
mosquito_pub_key_fname = "pub.key"
mosquito_pub_key_fpath = os.path.join(mosquito_cert_dir, mosquito_pub_key_fname)
mosquito_ca_cert_fname = "ca_cert.crt"
mosquito_ca_cert_fpath = os.path.join(mosquito_cert_dir, mosquito_ca_cert_fname)


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


class MqttClient:
    def __init__(
        self,
        host: str = "3.110.9.183",
        port: int = 8884,  # SSL/TLS port
        message_callback: Optional[Callable] = None,
    ):
        try:
            self.machine_id = "32"
            self.host = host
            self.port = port
            self.message_callback = message_callback
            self.client_id = f"machine_{self.machine_id}"

            # Certificate paths
            self.cert_path = mosquito_cert_fpath
            self.pri_key_path = mosquito_pri_key_fpath
            self.root_ca_path = mosquito_ca_cert_fpath

            self._verify_cert_files()

            # Connection state tracking
            self.is_connected = False
            self.connection_lock = threading.Lock()
            self._connection_in_progress = False

            # Subscription tracking
            self.subscribed_topics = set()

            # Connection and reconnection parameters
            self.max_reconnect_attempts = 5
            self.base_reconnect_delay = 1
            self.max_reconnect_delay = 60

            # Device topic prefix (restricted to device-specific topics)
            self.device_topic_prefix = f"vyom-mqtt-msg/{self.machine_id}"

            # Initialize MQTT client
            self.mqtt_connection = None
            self._create_mqtt_connection()

            # Start connection monitoring
            # self._start_connection_monitor()

        except Exception as e:
            logger.error(f"Error initializing MqttClient: {str(e)}")
            raise

    def _verify_cert_files(self):
        """Verify that all required certificate files exist"""
        for file_path in [self.cert_path, self.pri_key_path, self.root_ca_path]:
            if not os.path.exists(file_path):
                logger.error(f"Certificate file not found: {file_path}")
                raise FileNotFoundError(
                    f"Required certificate file not found: {file_path}"
                )

    def _create_mqtt_connection(self):
        """Create and configure MQTT client with SSL/TLS"""
        try:
            # Create MQTT client with callback API version 2
            self.mqtt_connection = mqtt.Client(
                client_id=self.client_id, clean_session=False, protocol=mqtt.MQTTv311
            )

            # Configure SSL/TLS with certificates
            context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            context.check_hostname = False
            context.verify_mode = ssl.CERT_REQUIRED

            # Load certificates
            context.load_verify_locations(self.root_ca_path)
            context.load_cert_chain(self.cert_path, self.pri_key_path)

            self.mqtt_connection.tls_set_context(context)

            # Set callbacks
            self.mqtt_connection.on_connect = self._on_connection_resumed
            self.mqtt_connection.on_disconnect = self._on_connection_interrupted
            self.mqtt_connection.on_message = self._on_message
            self.mqtt_connection.on_subscribe = self._on_subscribe
            self.mqtt_connection.on_publish = self._on_publish

            # Configure keep alive and other options
            self.mqtt_connection.max_inflight_messages_set(20)
            self.mqtt_connection.max_queued_messages_set(100)

            logger.info("MQTT client created successfully with SSL/TLS configuration")

        except Exception as e:
            logger.error(f"Failed to create MQTT client: {str(e)}")
            raise

    def _test_network_connectivity(self):
        """Test if the port is open (works for both TLS and plain)"""
        try:
            logger.info(
                f"Testing if port {self.port} is open on {self.host}"
            )
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((self.host, self.port))

            if result == 0:
                # Port is open, but we need to close immediately for TLS ports
                sock.close()
                logger.info("Port is reachable")
                return True
            else:
                sock.close()
                logger.error(f"Port {self.port} is not reachable")
                return False

        except Exception as e:
            logger.error(f"Network connectivity test failed: {str(e)}")
            return False

    def _on_connection_resumed(self, client, userdata, flags, rc, properties=None):
        """Callback for when client connects to broker (API v2)"""
        if rc == 0:
            logger.info(
                f"Device client connected successfully to {self.host}:{self.port}"
            )
            with self.connection_lock:
                self.is_connected = True
                self._connection_in_progress = False

            # Resubscribe to topics
            self._resubscribe_to_topics()
        else:
            logger.error(f"Failed to connect, return code: {rc}")
            with self.connection_lock:
                self.is_connected = False
                self._connection_in_progress = False

    def _on_connection_interrupted(self, client, userdata, rc, properties=None):
        """Callback for when client disconnects from broker (API v2)"""
        logger.warning(f"Device client disconnected, return code: {rc}")
        with self.connection_lock:
            self.is_connected = False

    def _on_message(self, client, userdata, msg):
        """Callback for when message is received"""
        try:
            topic = msg.topic
            payload = msg.payload.decode("utf-8")
            logger.info(f"Received message from topic '{topic}': {payload}")

            if self.message_callback:
                self.message_callback(topic, payload)
            else:
                logger.info("No callback provided, skipping callback execution")

        except Exception as e:
            logger.error(f"Error processing received message: {str(e)}")

    def _on_subscribe(self, client, userdata, mid, granted_qos, properties=None):
        """Callback for when subscription is confirmed (API v2)"""
        logger.info(f"Subscription confirmed with QoS: {granted_qos}")

    def _on_publish(self, client, userdata, mid, properties=None):
        """Callback for when message is published (API v2)"""
        logger.debug(f"Message published with mid: {mid}")

    def connect(self):
        """Connect to MQTT broker with exponential backoff"""
        with self.connection_lock:
            if self.is_connected:
                logger.info("Already connected to MQTT broker")
                return True

            if self._connection_in_progress:
                logger.info("Connection attempt already in progress")
                return False

            self._connection_in_progress = True

        # Test network connectivity first
        if not self._test_network_connectivity():
            with self.connection_lock:
                self._connection_in_progress = False
            return False

        try:
            for attempt in range(self.max_reconnect_attempts):
                try:
                    delay = min(
                        self.base_reconnect_delay * (2**attempt),
                        self.max_reconnect_delay,
                    )

                    if attempt > 0:
                        logger.info(
                            f"Reconnection attempt {attempt + 1}/{self.max_reconnect_attempts}"
                        )
                        time.sleep(delay)

                    # Connect to broker
                    logger.info(
                        f"Attempting to connect to {self.host}:{self.port}"
                    )
                    self.mqtt_connection.connect(self.host, self.port, 60)
                    self.mqtt_connection.loop_start()

                    # Wait for connection
                    timeout = 15  # Increased timeout
                    start_time = time.time()
                    while (
                        not self.is_connected and (time.time() - start_time) < timeout
                    ):
                        time.sleep(0.1)

                    if self.is_connected:
                        logger.info("Successfully connected to MQTT broker")
                        return True
                    else:
                        logger.warning(f"Connection attempt {attempt + 1} timed out")
                        self.mqtt_connection.loop_stop()

                except Exception as e:
                    logger.error(f"Connection attempt {attempt + 1} failed: {str(e)}")
                    if self.mqtt_connection:
                        self.mqtt_connection.loop_stop()

            logger.error("Failed to connect after all attempts")
            return False

        finally:
            with self.connection_lock:
                self._connection_in_progress = False

    def _resubscribe_to_topics(self):
        """Resubscribe to all previously subscribed topics"""
        for topic in self.subscribed_topics.copy():
            try:
                result = self.mqtt_connection.subscribe(topic, qos=1)
                if result[0] == mqtt.MQTT_ERR_SUCCESS:
                    logger.info(f"Resubscribed to topic: {topic}")
                else:
                    logger.error(f"Failed to resubscribe to topic: {topic}")
            except Exception as e:
                logger.error(f"Error resubscribing to {topic}: {str(e)}")

    def subscribe_to_topic(self, topic: str):
        """Subscribe to a topic (restricted to device topics)"""
        try:
            # Enforce topic restrictions for device clients
            if not self._is_topic_allowed(topic):
                logger.error(f"Topic '{topic}' is not allowed for device client")
                raise PermissionError(
                    f"Device client not allowed to subscribe to topic: {topic}"
                )

            if not self.is_connected:
                if not self.connect():
                    raise ConnectionError("Failed to connect to MQTT broker")

            result = self.mqtt_connection.subscribe(topic, qos=1)
            if result[0] == mqtt.MQTT_ERR_SUCCESS:
                self.subscribed_topics.add(topic)
                logger.info(f"Subscribed to topic: {topic}")
            else:
                logger.error(f"Failed to subscribe to topic: {topic}")
                raise Exception(f"Subscription failed with code: {result[0]}")

        except Exception as e:
            logger.error(f"Subscription to {topic} failed: {str(e)}")
            raise

    def publish_message(self, topic: str, payload, retain: bool = False):
        """Publish message (restricted to device topics)"""
        try:
            # Enforce topic restrictions for device clients
            if not self._is_topic_allowed(topic):
                logger.error(f"Topic '{topic}' is not allowed for device client")
                return False

            if not self.is_connected:
                if not self.connect():
                    logger.error("Failed to connect to MQTT broker for publishing")
                    return False

            # Convert payload to string if it's a dict
            if isinstance(payload, dict):
                payload = json.dumps(payload)

            logger.info(f"Publishing message to topic: {topic}")
            result = self.mqtt_connection.publish(topic, payload, qos=1, retain=retain)

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Message published successfully to topic: {topic}")
                return True
            else:
                logger.error(f"Failed to publish message, return code: {result.rc}")
                return False

        except Exception as e:
            logger.error(f"Publish to {topic} failed: {str(e)}")
            return False

    def _is_topic_allowed(self, topic: str) -> bool:
        """Check if topic is allowed for device client"""
        allowed_patterns = [
            self.device_topic_prefix,  # device/machine_id/*
            f"commands/{self.machine_id}",  # commands/machine_id/*
            f"config/{self.machine_id}",  # config/machine_id/*
        ]

        return any(topic.startswith(pattern) for pattern in allowed_patterns)

    def _start_connection_monitor(self):
        """Start background thread to monitor connection"""

        def monitor_connection():
            while True:
                try:
                    if not self.is_connected and not self._connection_in_progress:
                        logger.warning("Connection lost. Attempting to reconnect...")
                        self.connect()
                    time.sleep(30)  # Check every 30 seconds
                except Exception as e:
                    logger.error(f"Connection monitoring failed: {str(e)}")
                    time.sleep(30)

        monitor_thread = threading.Thread(target=monitor_connection, daemon=True)
        monitor_thread.start()

    def disconnect(self):
        """Gracefully disconnect from MQTT broker"""
        try:
            if self.mqtt_connection:
                self.mqtt_connection.loop_stop()
                self.mqtt_connection.disconnect()

            with self.connection_lock:
                self.is_connected = False

            logger.info("MQTT device client disconnected successfully")

        except Exception as e:
            logger.error(f"Failed to disconnect MQTT client: {str(e)}")

    def cleanup(self):
        """Gracefully disconnect from MQTT broker"""
        try:
            self.disconnect()
            logger.info(f"cleanup successful MQTT client")
        except Exception as e:
            logger.error(f"Error in cleanup MQTT client: {str(e)}")


def message_callback(topic, payload):
    try:
        logger.info(f"Received message in callback '{topic}': {json.loads(payload)}")
    except Exception as e:
        logger.error("Error in calling callback")


def main():
    """Example usage of MqttClient"""
    # Initialize client
    machine_id = 32
    mqtt_client = MqttClient(
        message_callback=message_callback,
        # username="your_username",  # Uncomment if authentication is enabled
        # password="your_password",  # Uncomment if authentication is enabled
    )

    # Wait for connection
    time.sleep(2)
    subscribe_topic_1 = f"vyom-mqtt-msg/{machine_id}/"
    subscribe_topic_2 = f"vyom-mqtt-msg/{machine_id}/#"

    # Subscribe to topics
    mqtt_client.subscribe_to_topic(subscribe_topic_1)
    mqtt_client.subscribe_to_topic(subscribe_topic_2)

    # publish_topic_1 = f"1/2025-02-11/33/44/{machine_id}/99/10/hello.json"
    # # Publish some test messages
    # mqtt_client.publish_message(publish_topic_1, "Hello from Mosquitto mqtt_client!")
    # mqtt_client.publish_message(publish_topic_1, {"message": "JSON payload", "timestamp": time.time()})

    # Keep the mqtt_client running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")
        mqtt_client.cleanup()


if __name__ == "__main__":
    main()
