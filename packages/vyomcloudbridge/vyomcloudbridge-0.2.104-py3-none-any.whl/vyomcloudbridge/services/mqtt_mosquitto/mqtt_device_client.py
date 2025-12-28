import time
import threading
import os
import json
import ssl
import uuid
from typing import Callable, List, Optional
import paho.mqtt.client as mqtt
import logging

# cert_dir = f"/etc/vyomcloudbridge/mosquitto/certs/"
cert_dir = f"/Users/amardeepsaini/Documents/VYOM/vyom-cloud-bridge/vyomcloudbridge/services/mqtt_mosquitto/33/"

# /etc/vyomcloudbridge/mosquitto/certs/machine.cert.pem
cert_file_name = "machine.cert.pem"
cert_file_path = os.path.join(cert_dir, cert_file_name)

# /etc/vyomcloudbridge/mosquitto/certs/machine.private.key
pri_key_file_name = "machine.private.key"
pri_key_file_path = os.path.join(cert_dir, pri_key_file_name)

# /etc/vyomcloudbridge/mosquitto/certs/root-CA.crt
root_ca_file_name = "root-CA.crt"
root_ca_file_path = os.path.join(cert_dir, root_ca_file_name)

# # Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)
# formatter = logging.Formatter(
#         "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
#     )
# stream_handler = logging.StreamHandler()
# stream_handler.setFormatter(formatter)
# logger.addHandler(stream_handler)


class MqttClient:
    def __init__(
        self,
        broker_host: str = "3.110.9.183",
        broker_port: int = 8884,  # SSL/TLS port
        message_callback: Optional[Callable] = None,
        daemon: bool = False,
    ):
        try:
            self.machine_id = "32"
            self.broker_host = broker_host
            self.broker_port = broker_port
            self.message_callback = message_callback
            self.daemon = daemon
            self.client_id = f"machine_33"

            # Certificate paths
            self.cert_path = cert_file_path
            self.pri_key_path = pri_key_file_path
            self.root_ca_path = root_ca_file_path

            # check credentials
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

            # Initialize MQTT client
            self.mqtt_client = None
            self._create_mqtt_connection()

            # Start connection monitoring
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

    def _create_mqtt_connection(self):
        """Connect to MQTT broker with exponential backoff"""
        with self.connection_lock:
            if self.is_connected:
                self._connection_in_progress = False
                print("Already connected to MQTT broker")
                return

            self._connection_in_progress = True
            try:
                for attempt in range(self.max_reconnect_attempts):
                    try:
                        delay = min(
                            self.base_reconnect_delay * (2**attempt),
                            self.max_reconnect_delay,
                        )
                        # Always recreate the client object
                        self.mqtt_client = mqtt.Client(
                            client_id=self.client_id,
                            clean_session=False,
                            protocol=mqtt.MQTTv311,
                        )
                        # SSL/TLS setup
                        self.mqtt_client.tls_set(
                            ca_certs=self.root_ca_path,
                            certfile=self.cert_path,
                            keyfile=self.pri_key_path,
                            cert_reqs=ssl.CERT_REQUIRED,
                            tls_version=ssl.PROTOCOL_TLS,
                            ciphers=None,
                        )
                        # self.mqtt_client.tls_insecure_set(True) # if Subject Alternative Name (SAN) is not configured
                        # Set callbacks
                        self.mqtt_client.on_connect = self._on_connection_resumed
                        self.mqtt_client.on_disconnect = self._on_connection_interrupted
                        self.mqtt_client.on_message = self._message_callback
                        self.mqtt_client.on_subscribe = self._on_subscribe
                        self.mqtt_client.on_publish = self._on_publish
                        self.mqtt_client.on_log = self._on_log
                        self.mqtt_client.max_inflight_messages_set(100)
                        self.mqtt_client.max_queued_messages_set(1000)
                        print("MQTT client created, now connecting...")

                        # Connect to broker
                        self.mqtt_client.connect(self.broker_host, self.broker_port, 60)
                        self.mqtt_client.loop_start()

                        # Wait for connection
                        timeout = 10
                        start_time = time.time()
                        while (
                            not self.is_connected
                            and (time.time() - start_time) < timeout
                        ):
                            time.sleep(0.1)

                        if self.is_connected:
                            print("Successfully connected to MQTT broker")
                            self._resubscribe_to_topics()
                            return True
                        else:
                            print(
                                f"Warning -Connection attempt {attempt + 1} timed out"
                            )
                            if self.mqtt_client:
                                self.mqtt_client.loop_stop()
                    except Exception as e:
                        print(
                            f"Error- Connection attempt {attempt + 1} failed: {str(e)}"
                        )
                        if self.mqtt_client:
                            try:
                                self.mqtt_client.loop_stop()
                            except:
                                pass
                        if attempt < self.max_reconnect_attempts - 1:
                            time.sleep(delay)
                raise ConnectionError(
                    f"Could not connect to MQTT broker after {self.max_reconnect_attempts} attempts"
                )
            finally:
                self._connection_in_progress = False

    def _on_connection_interrupted(self, client, userdata, rc):
        """Callback for when client disconnects from broker"""
        if rc != 0:
            print(
                f"Warning -Server client disconnected unexpectedly, return code: {rc}"
            )
        else:
            print("Server client disconnected gracefully")

        with self.connection_lock:
            self.is_connected = False

    def _on_connection_resumed(self, client, userdata, flags, rc):
        """Callback for when client connects to broker"""
        if rc == 0:
            print(
                f"Server client connected successfully to {self.broker_host}:{self.broker_port}"
            )

            self.is_connected = True
            self._connection_in_progress = False

            # Resubscribe to topics
            self._resubscribe_to_topics()
        else:
            error_messages = {
                1: "Connection refused - incorrect protocol version",
                2: "Connection refused - invalid client identifier",
                3: "Connection refused - server unavailable",
                4: "Connection refused - bad username or password",
                5: "Connection refused - not authorised",
            }
            print(
                f"Error- Failed to connect: {error_messages.get(rc, f'Unknown error code: {rc}')}"
            )
            with self.connection_lock:
                self.is_connected = False
                self._connection_in_progress = False

    def _message_callback(self, client, userdata, msg):
        """Callback for when message is received"""
        try:
            topic = msg.topic
            payload = msg.payload.decode("utf-8")
            print(f"Received message from topic '{topic}': {payload}")

            if self.message_callback:
                self.message_callback(topic, payload)
            else:
                print(f"Debug - No callback provided, skipping callback execution")

        except Exception as e:
            print(f"Error- Error processing received message: {str(e)}")

    def _on_subscribe(self, client, userdata, mid, granted_qos):
        """Callback for when subscription is confirmed"""
        print(f"Subscription confirmed with mid: {mid}, QoS: {granted_qos}")

    def _on_publish(self, client, userdata, mid):
        """Callback for when message is published"""
        print(f"Debug - Message published with mid: {mid}")

    def _on_log(self, client, userdata, level, buf):
        """Callback for MQTT client logs"""
        pass
        # print(f"Debug - MQTT Log: {buf}")

    def _resubscribe_to_topics(self):
        """Resubscribe to all previously subscribed topics"""
        if not self.mqtt_client:
            print("Error: MQTT client is not initialized for resubscribe")
            return
        for topic in self.subscribed_topics.copy():
            try:
                result = self.mqtt_client.subscribe(topic, qos=1)
                if result[0] == mqtt.MQTT_ERR_SUCCESS:
                    print(f"Resubscribed to topic: {topic}")
                else:
                    print(f"Error: Failed to resubscribe to topic: {topic}")
            except Exception as e:
                print(f"Error: Error resubscribing to {topic}: {str(e)}")

    def subscribe_to_topic(self, topic: str, qos: int = 1):
        """Subscribe to any topic (server has full permissions)"""
        try:
            if not self.is_connected:
                self.subscribed_topics.add(topic)
                print(
                    "Warning: MQTT connection not established, skipping subscription for now, will get auto subscribed later..."
                )
                return

            if self.mqtt_client is None:
                print("Error- MQTT client is not initialized")
                raise RuntimeError("MQTT client is not initialized")

            result = self.mqtt_client.subscribe(topic, qos=qos)
            if result[0] == mqtt.MQTT_ERR_SUCCESS:
                self.subscribed_topics.add(topic)
                print(f"Subscribed to topic: {topic} with QoS: {qos}")
            else:
                print(f"Error- Failed to subscribe to topic: {topic}")
                raise Exception(f"Subscription failed with code: {result[0]}")

        except Exception as e:
            print(f"Error- Subscription to {topic} failed: {str(e)}")
            raise

    def subscribe_to_multiple_topics(self, topics: List[tuple]):
        """
        Subscribe to multiple topics at once
        topics: List of tuples (topic, qos)
        """
        try:
            if not self.is_connected:
                print(  # debug
                    "Warning: MQTT connection not established, skipping subscriptions for now, will get auto subscribed later..."
                )
                for topic, qos in topics:
                    self.subscribed_topics.add(topic)
                return False

            if self.mqtt_client is None:
                print("Error- MQTT client is not initialized")
                raise RuntimeError("MQTT client is not initialized")

            # Convert to format expected by paho-mqtt
            topic_list = [(topic, qos) for topic, qos in topics]

            result = self.mqtt_client.subscribe(topic_list)
            if result[0] == mqtt.MQTT_ERR_SUCCESS:
                for topic, qos in topics:
                    self.subscribed_topics.add(topic)
                print(f"Subscribed to {len(topics)} topics")
            else:
                print(f"Error- Failed to subscribe to multiple topics")
                raise Exception(f"Multiple subscription failed with code: {result[0]}")

        except Exception as e:
            print(f"Error- Multiple subscription failed: {str(e)}")
            raise

    def publish_message(self, topic: str, payload, qos: int = 1, retain: bool = False):
        """Publish message to any topic (server has full permissions)"""
        try:
            if not self.is_connected:
                print(  # debug
                    "Warning: MQTT connection not established, skipping publishing msg..."
                )
                return False

            if self.mqtt_client is None:
                print("Error- MQTT client is not initialized")
                return False

            # Convert payload to string if it's a dict
            if isinstance(payload, dict):
                payload = json.dumps(payload)

            result = self.mqtt_client.publish(topic, payload, qos=qos, retain=retain)

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"Message published successfully to topic: {topic}")
                return True
            else:
                print(f"Error- Failed to publish message, return code: {result.rc}")
                return False

        except Exception as e:
            print(f"Error- Publish to {topic} failed: {str(e)}")
            return False

    def publish_batch_messages(self, messages: List[dict]):
        """
        Publish multiple messages at once
        messages: List of dicts with keys: topic, payload, qos (optional), retain (optional)
        """
        try:
            if not self.is_connected:
                print(  # debug
                    "Warning: MQTT connection not established, skipping publishing msgs..."
                )
                return False

            success_count = 0
            for msg in messages:
                topic = msg["topic"]
                payload = msg["payload"]
                qos = msg.get("qos", 1)
                retain = msg.get("retain", False)

                if self.publish_message(topic, payload, qos, retain):
                    success_count += 1

            print(
                f"Batch publish completed: {success_count}/{len(messages)} messages sent"
            )
            return success_count == len(messages)

        except Exception as e:
            print(f"Error- Batch publishing failed: {str(e)}")
            return False

    def unsubscribe_from_topic(self, topic: str):
        """Unsubscribe from a topic"""
        try:
            if not self.is_connected:
                print("Warning -Not connected to broker")
                return False

            if self.mqtt_client is None:
                print("Error- MQTT client is not initialized")
                return False

            result = self.mqtt_client.unsubscribe(topic)
            if result[0] == mqtt.MQTT_ERR_SUCCESS:
                self.subscribed_topics.discard(topic)
                print(f"Unsubscribed from topic: {topic}")
                return True
            else:
                print(f"Error- Failed to unsubscribe from topic: {topic}")
                return False

        except Exception as e:
            print(f"Error- Unsubscribe from {topic} failed: {str(e)}")
            return False

    def _start_backgd_conn_monitor(self):
        """Start background thread to monitor connection"""

        def monitor_connection():
            while True:
                try:
                    if not self.is_connected and not self._connection_in_progress:
                        print("Warning - Connection lost. Attempting to reconnect...")
                        self._create_mqtt_connection()
                    time.sleep(30)  # Check every 30 seconds
                except Exception as e:
                    print(f"Error- Connection monitoring failed: {str(e)}")
                    time.sleep(30)

        monitor_thread = threading.Thread(target=monitor_connection, daemon=True)
        monitor_thread.start()

    def disconnect(self):
        """Gracefully disconnect from MQTT broker"""
        try:
            if self.mqtt_client:
                self.mqtt_client.loop_stop()
                self.mqtt_client.disconnect()

            with self.connection_lock:
                self.is_connected = False

            print("MQTT server client disconnected successfully")

        except Exception as e:
            print(f"Error- Failed to disconnect MQTT client: {str(e)}")

    # Administrative methods for server client
    def broadcast_message(self, topic_pattern: str, payload, qos: int = 1):
        """Broadcast message to all devices matching pattern"""
        try:
            # This would typically be used with topics like "broadcast/all" or "commands/all"
            return self.publish_message(topic_pattern, payload, qos, retain=False)
        except Exception as e:
            print(f"Error- Broadcast failed: {str(e)}")
            return False

    def cleanup(self):
        """Gracefully close the MQTT connection"""
        try:
            if self.mqtt_client:
                self.mqtt_client.loop_stop()
                self.mqtt_client.disconnect()
                self.mqtt_client = None

            with self.connection_lock:
                self.is_connected = False

            print("MQTT connection closed successfully")

        except Exception as e:
            print(f"Error - Failed to close MQTT connection: {str(e)}")


def message_callback(topic, payload):
    try:
        print(f"Received message in callback topic '{topic}'")
        if isinstance(payload, dict):
            print(f"Received message in callback dict data - {type(payload)}")
            msg = payload
        if isinstance(payload, str):
            try:
                msg = json.loads(payload)
                print(f"Received message in callback json data - {msg}")
            except Exception as e:
                msg = payload
                print(f"Received message in callback string data - ', {msg}")
        if isinstance(payload, bytes):
            print(f"Received message in callback bytes data.")
    except Exception as e:
        print(f"Error in calling callback, {str(e)}")


def main():
    try:
        import signal

        mqtt_client = MqttClient(
            message_callback=message_callback,
        )

        # Subscribe to a test machine_id
        subscribe_topic_1 = f"vyom-mqtt-msg/{mqtt_client.machine_id}/"
        mqtt_client.subscribe_to_topic(subscribe_topic_1)

        subscribe_topic_2 = f"vyom-mqtt-msg/{mqtt_client.machine_id}/#"
        mqtt_client.subscribe_to_topic(subscribe_topic_2)

        # try:
        #     publish_topic = f"vyom-mqtt-msg/{mqtt_client.machine_id}/hello.json"
        #     mqtt_client.publish_message(publish_topic, "Test message using client cert")
        #     mqtt_client.publish_message(
        #         publish_topic, {"message": "JSON payload", "timestamp": time.time()}
        #     )
        # except Exception as e:
        #     print(f"Error: Error in main execution: {str(e)}")

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
