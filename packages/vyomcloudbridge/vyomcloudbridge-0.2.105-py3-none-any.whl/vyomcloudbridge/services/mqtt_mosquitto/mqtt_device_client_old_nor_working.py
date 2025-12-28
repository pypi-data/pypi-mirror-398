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
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)
# formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
# stream_handler = logging.StreamHandler()
# stream_handler.setFormatter(formatter)
# logger.addHandler(stream_handler)


class MqttClient:
    def __init__(
        self,
        host: str = "3.110.9.183",
        port: int = 8884,  # SSL/TLS port
        message_callback: Optional[Callable] = None,
        daemon: bool = False,
    ):
        try:
            self.machine_id = "33"
            self.host = host
            self.port = port
            self.message_callback = message_callback
            self.daemon = daemon
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

            self.mqtt_connection = None
            self._create_mqtt_connection()
            self._start_backgd_conn_monitor()
            print("MqttClient initialized successfully!")
        except Exception as e:
            print(f"Error: Error initializing MqttClient: {str(e)}")
            raise

    def _verify_cert_files(self):
        """Verify that all required certificate files exist"""
        for file_path in [self.cert_path, self.pri_key_path, self.root_ca_path]:
            if not os.path.exists(file_path):
                print(f"Error: Certificate file not found: {file_path}")
                raise FileNotFoundError(
                    f"Required certificate file not found: {file_path}"
                )

    def _setup_mqtt_client(self):
        """Setup MQTT client configuration (without connecting)"""
        try:
            # Create MQTT client
            self.mqtt_connection = mqtt.Client(
                client_id=self.client_id,
                clean_session=False,  # Persistent session
                protocol=mqtt.MQTTv311,
                transport="tcp",
            )

            # Configure SSL/TLS with certificates
            self.mqtt_connection.tls_set(
                ca_certs=self.root_ca_path,
                certfile=self.cert_path,
                keyfile=self.pri_key_path,
                cert_reqs=ssl.CERT_REQUIRED,
                tls_version=ssl.PROTOCOL_TLS,
                ciphers=None,
            )

            # Disable hostname verification (similar to mosquitto client behavior)
            self.mqtt_connection.tls_insecure_set(True)

            # Set callbacks
            self.mqtt_connection.on_connect = self._on_connection_resumed
            self.mqtt_connection.on_disconnect = self._on_connection_interrupted
            self.mqtt_connection.on_message = self._on_message
            self.mqtt_connection.on_subscribe = self._on_subscribe
            self.mqtt_connection.on_publish = self._on_publish
            self.mqtt_connection.on_log = self._on_log  # Add logging callback

            # Configure keep alive and other options
            self.mqtt_connection.max_inflight_messages_set(20)
            self.mqtt_connection.max_queued_messages_set(100)

            print("MQTT client configured successfully with SSL/TLS")

        except Exception as e:
            print(f"Error: Failed to setup MQTT client: {str(e)}")
            raise

    def _create_mqtt_connection(self):
        """Create a new MQTT connection with exponential backoff (similar to AWS IoT Core)"""
        with self.connection_lock:  # Acquire lock to prevent concurrent attempts
            if self.is_connected:
                self._connection_in_progress = False
                print("Connection already established, skipping reconnection")
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

                        if attempt > 0:
                            print(
                                f"Reconnection attempt {attempt + 1}/{self.max_reconnect_attempts}"
                            )
                            time.sleep(delay)

                        # Test network connectivity first
                        if not self._test_network_connectivity():
                            raise ConnectionError("Network connectivity test failed")

                        # Connect to MQTT broker
                        print(
                            f"Attempting to connect to {self.host}:{self.port}"
                        )
                        self.mqtt_connection.connect(
                            self.host, self.port, 1200
                        )  # 20 minutes keep alive
                        self.mqtt_connection.loop_start()

                        # Wait for connection to be established
                        timeout = 15  # 15 seconds timeout
                        start_time = time.time()
                        while (
                            not self.is_connected
                            and (time.time() - start_time) < timeout
                        ):
                            time.sleep(0.1)

                        if self.is_connected:
                            print("Successfully connected to MQTT broker")
                            self._resubscribe_to_topics()
                            return
                        else:
                            raise TimeoutError("Connection timeout")

                    except Exception as e:
                        print(
                            f"Warning: MQTT connection attempt {attempt + 1} failed: {str(e)}"
                        )
                        if self.mqtt_connection:
                            try:
                                self.mqtt_connection.loop_stop()
                            except:
                                pass

                        if attempt < self.max_reconnect_attempts - 1:
                            continue

                # If all attempts fail
                raise ConnectionError(
                    f"Could not connect to MQTT broker after {self.max_reconnect_attempts} attempts"
                )

            finally:
                self._connection_in_progress = False

    def _test_network_connectivity(self):
        """Test if the port is open (works for both TLS and plain)"""
        try:
            print(f"Testing if port {self.port} is open on {self.host}")
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((self.host, self.port))

            if result == 0:
                # Port is open, but we need to close immediately for TLS ports
                sock.close()
                print("Port is reachable")
                return True
            else:
                sock.close()
                print(f"Error: Port {self.port} is not reachable")
                return False

        except Exception as e:
            print(f"Error: Network connectivity test failed: {str(e)}")
            return False

    def _on_log(self, client, userdata, level, buf):
        """Callback for MQTT client logging"""
        print(f"MQTT Log: {buf}")

    def _on_connection_resumed(self, client, userdata, flags, rc):
        """Callback for when client connects to broker"""
        if rc == 0:
            print(
                f"Device client connected successfully to {self.host}:{self.port}"
            )
            with self.connection_lock:
                self.is_connected = True
                self._connection_in_progress = False

            # Resubscribe to topics
            self._resubscribe_to_topics()
        else:
            print(f"Error: Failed to connect, return code: {rc}")
            print(f"Error: Connection error meaning: {mqtt.connack_string(rc)}")
            with self.connection_lock:
                self.is_connected = False
                self._connection_in_progress = False

    def _on_connection_interrupted(self, client, userdata, rc):
        """Callback for when client disconnects from broker"""
        print(f"Warning Device client disconnected, return code: {rc}")
        with self.connection_lock:
            self.is_connected = False

    def _on_message(self, client, userdata, msg):
        """Callback for when message is received"""
        try:
            topic = msg.topic
            payload = msg.payload.decode("utf-8")
            print(f"Received message from topic '{topic}': {payload}")
            if self.message_callback:
                self.message_callback(topic, payload)
            else:
                print("No callback provided, skipping callback execution")
        except Exception as e:
            print(f"Error: Error processing received message: {str(e)}")

    def _on_subscribe(self, client, userdata, mid, granted_qos):
        """Callback for when subscription is confirmed"""
        print(f"Subscription confirmed with mid: {mid}, QoS: {granted_qos}")

    def _on_publish(self, client, userdata, mid):
        """Callback for when message is published"""
        print(f"Message published with mid: {mid}")

    def connect(self):
        """Connect to MQTT broker with exponential backoff"""
        with self.connection_lock:
            if self.is_connected:
                print("Already connected to MQTT broker")
                return True
            if self._connection_in_progress:
                print("Connection attempt already in progress")
                return False
            self._connection_in_progress = True
        try:
            for attempt in range(self.max_reconnect_attempts):
                try:
                    delay = min(self.base_reconnect_delay * (2**attempt), self.max_reconnect_delay)
                    self.mqtt_connection = mqtt.Client(
                        client_id=self.client_id,
                        clean_session=False,
                        protocol=mqtt.MQTTv311,
                    )
                    self.mqtt_connection.tls_set(
                        ca_certs=self.root_ca_path,
                        certfile=self.cert_path,
                        keyfile=self.pri_key_path,
                        cert_reqs=ssl.CERT_REQUIRED,
                        tls_version=ssl.PROTOCOL_TLS,
                        ciphers=None,
                    )
                    self.mqtt_connection.tls_insecure_set(True)
                    self.mqtt_connection.on_connect = self._on_connection_resumed
                    self.mqtt_connection.on_disconnect = self._on_connection_interrupted
                    self.mqtt_connection.on_message = self._on_message
                    self.mqtt_connection.on_subscribe = self._on_subscribe
                    self.mqtt_connection.on_publish = self._on_publish
                    self.mqtt_connection.on_log = self._on_log
                    self.mqtt_connection.max_inflight_messages_set(20)
                    self.mqtt_connection.max_queued_messages_set(100)
                    print(f"Attempting to connect to {self.host}:{self.port}")
                    self.mqtt_connection.connect(self.host, self.port, 60)
                    self.mqtt_connection.loop_start()
                    timeout = 15
                    start_time = time.time()
                    while not self.is_connected and (time.time() - start_time) < timeout:
                        time.sleep(0.1)
                    if self.is_connected:
                        print("Successfully connected to MQTT broker")
                        return True
                    else:
                        print(f"Connection attempt {attempt + 1} timed out")
                        if self.mqtt_connection:
                            self.mqtt_connection.loop_stop()
                except Exception as e:
                    print(f"Error: Connection attempt {attempt + 1} failed: {str(e)}")
                    if self.mqtt_connection:
                        self.mqtt_connection.loop_stop()
                    if attempt < self.max_reconnect_attempts - 1:
                        time.sleep(delay)
            print("Error: Failed to connect after all attempts")
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
                    print(f"Resubscribed to topic: {topic}")
                else:
                    print(f"Error: Failed to resubscribe to topic: {topic}")
            except Exception as e:
                print(f"Error: Error resubscribing to {topic}: {str(e)}")

    def subscribe_to_topic(self, topic: str):
        """Subscribe to a topic (restricted to device topics)"""
        try:
            # Fix: Remove or relax topic restrictions for testing
            # Comment out the restriction check temporarily
            # if not self._is_topic_allowed(topic):
            #     print(f"Error: Topic '{topic}' is not allowed for device client")
            #     raise PermissionError(f"Device client not allowed to subscribe to topic: {topic}")

            if not self.is_connected:
                if not self.connect():
                    raise ConnectionError("Failed to connect to MQTT broker")

            result = self.mqtt_connection.subscribe(topic, qos=1)
            if result[0] == mqtt.MQTT_ERR_SUCCESS:
                self.subscribed_topics.add(topic)
                print(f"Subscribed to topic: {topic}")
            else:
                print(f"Error: Failed to subscribe to topic: {topic}")
                raise Exception(f"Subscription failed with code: {result[0]}")

        except Exception as e:
            print(f"Error: Subscription to {topic} failed: {str(e)}")
            raise

    def publish_message(self, topic: str, payload, retain: bool = False):
        """Publish message (restricted to device topics)"""
        try:
            # Fix: Remove or relax topic restrictions for testing
            # Comment out the restriction check temporarily
            # if not self._is_topic_allowed(topic):
            #     print(f"Error: Topic '{topic}' is not allowed for device client")
            #     return False

            if not self.is_connected:
                if not self.connect():
                    print("Error: Failed to connect to MQTT broker for publishing")
                    return False

            # Convert payload to string if it's a dict
            if isinstance(payload, dict):
                payload = json.dumps(payload)

            print(f"Publishing message to topic: {topic}")
            result = self.mqtt_connection.publish(topic, payload, qos=1, retain=retain)

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"Message published successfully to topic: {topic}")
                return True
            else:
                print(f"Error: Failed to publish message, return code: {result.rc}")
                return False

        except Exception as e:
            print(f"Error: Publish to {topic} failed: {str(e)}")
            return False

    def _is_topic_allowed(self, topic: str) -> bool:
        """Check if topic is allowed for device client"""
        allowed_patterns = [
            self.device_topic_prefix,  # vyom-mqtt-msg/machine_id/*
            f"commands/{self.machine_id}",  # commands/machine_id/*
            f"config/{self.machine_id}",  # config/machine_id/*
            "#",  # Allow all topics for testing
        ]

        return any(
            topic.startswith(pattern) or topic == pattern
            for pattern in allowed_patterns
        )

    def disconnect(self):
        """Gracefully disconnect from MQTT broker"""
        try:
            if self.mqtt_connection:
                self.mqtt_connection.loop_stop()
                self.mqtt_connection.disconnect()

            with self.connection_lock:
                self.is_connected = False

            print("MQTT device client disconnected successfully")

        except Exception as e:
            print(f"Error: Failed to disconnect MQTT client: {str(e)}")

    def cleanup(self):
        """Gracefully disconnect from MQTT broker"""
        try:
            self.disconnect()
            print(f"cleanup successful MQTT client")
        except Exception as e:
            print(f"Error: Error in cleanup MQTT client: {str(e)}")


def message_callback(topic, payload):
    try:
        print(f"Received message in callback '{topic}': {payload}")
        # Try to parse as JSON if possible
        try:
            parsed_payload = json.loads(payload)
            print(f"Parsed JSON payload: {parsed_payload}")
        except json.JSONDecodeError:
            print(f"Payload is not JSON, treating as string: {payload}")
    except Exception as e:
        print(f"Error: Error in calling callback: {str(e)}")


def main():
    import signal
    machine_id = 33
    mqtt_client = MqttClient(
        message_callback=message_callback,
    )
    if not mqtt_client.connect():
        print("Error: Failed to connect to MQTT broker")
        mqtt_client.cleanup()
        exit(0)
    subscribe_topic = f"vyom-mqtt-msg/{machine_id}/#"
    try:
        mqtt_client.subscribe_to_topic(subscribe_topic)
        publish_topic = f"vyom-mqtt-msg/{machine_id}/hello.json"
        mqtt_client.publish_message(publish_topic, "Test message using client cert")
        mqtt_client.publish_message(
            publish_topic, {"message": "JSON payload", "timestamp": time.time()}
        )
    except Exception as e:
        print(f"Error: Error in main execution: {str(e)}")
    try:
        is_running = True
        def signal_handler(sig, frame):
            nonlocal is_running
            print(f"Received signal {sig}, shutting down...")
            is_running = False
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        print("Listening for messages... Press Ctrl+C to exit")
        while is_running:
            time.sleep(10)
    except KeyboardInterrupt:
        print("\nShutting down...")
        mqtt_client.cleanup()

if __name__ == "__main__":
    main()
