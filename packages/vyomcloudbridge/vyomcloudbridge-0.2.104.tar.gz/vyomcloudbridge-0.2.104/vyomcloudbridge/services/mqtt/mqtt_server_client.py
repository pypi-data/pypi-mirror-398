import time
import threading
import os
import json
import uuid
from typing import Callable, List
import paho.mqtt.client as mqtt
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


class MqttServerClient:
    def __init__(
        self,
        host: str = "3.110.9.183",
        port: int = 8883,
        username: str = "vyom_iq",
        password: str = "vyomiqpassword",
        callback: Callable = None,
        client_id_prefix: str = "server"
    ):
        try:
            self.host = host
            self.port = port
            self.username = username
            self.password = password
            self.message_callback = callback
            self.client_id = f"{client_id_prefix}_{uuid.uuid4().hex[:8]}"

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
            self.mqtt_connection = None
            self._create_mqtt_client()

            # Start connection monitoring
            self._start_backgd_conn_monitor()

        except Exception as e:
            logger.error(f"Error initializing MqttServerClient: {str(e)}")
            raise

    def _create_mqtt_client(self):
        """Create and configure MQTT client"""
        try:
            # Create MQTT client
            self.mqtt_connection = mqtt.Client(
                client_id=self.client_id,
                clean_session=False,
                protocol=mqtt.MQTTv311
            )

            # Set username and password if provided
            if self.username and self.password:
                self.mqtt_connection.username_pw_set(self.username, self.password)

            # Set callbacks
            self.mqtt_connection.on_connect = self._on_connection_resumed
            self.mqtt_connection.on_disconnect = self._on_connection_interrupted
            self.mqtt_connection.on_message = self._message_callback
            self.mqtt_connection.on_subscribe = self._on_subscribe
            self.mqtt_connection.on_publish = self._on_publish
            self.mqtt_connection.on_log = self._on_log

            # Configure client options
            self.mqtt_connection.max_inflight_messages_set(100)
            self.mqtt_connection.max_queued_messages_set(1000)

            logger.info("MQTT server client created successfully")

        except Exception as e:
            logger.error(f"Failed to create MQTT client: {str(e)}")
            raise

    def _on_connection_resumed(self, client, userdata, flags, rc):
        """Callback for when client connects to broker"""
        if rc == 0:
            logger.info(f"Server client connected successfully to {self.host}:{self.port}")
            with self.connection_lock:
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
                5: "Connection refused - not authorised"
            }
            logger.error(f"Failed to connect: {error_messages.get(rc, f'Unknown error code: {rc}')}")
            with self.connection_lock:
                self.is_connected = False
                self._connection_in_progress = False

    def _on_connection_interrupted(self, client, userdata, rc):
        """Callback for when client disconnects from broker"""
        if rc != 0:
            logger.warning(f"Server client disconnected unexpectedly, return code: {rc}")
        else:
            logger.info("Server client disconnected gracefully")
        
        with self.connection_lock:
            self.is_connected = False


    def _message_callback(self, client, userdata, msg):
        """Callback for when message is received"""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            logger.info(f"Received message from topic '{topic}': {payload}")
            
            if self.message_callback:
                self.message_callback(topic, payload)
            else:
                logger.debug("No callback provided, skipping callback execution")
                
        except Exception as e:
            logger.error(f"Error processing received message: {str(e)}")

    def _on_subscribe(self, client, userdata, mid, granted_qos):
        """Callback for when subscription is confirmed"""
        logger.info(f"Subscription confirmed with mid: {mid}, QoS: {granted_qos}")

    def _on_publish(self, client, userdata, mid):
        """Callback for when message is published"""
        logger.debug(f"Message published with mid: {mid}")

    def _on_log(self, client, userdata, level, buf):
        """Callback for MQTT client logs"""
        logger.debug(f"MQTT Log: {buf}")

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

        try:
            for attempt in range(self.max_reconnect_attempts):
                try:
                    delay = min(self.base_reconnect_delay * (2 ** attempt), self.max_reconnect_delay)
                    
                    if attempt > 0:
                        logger.info(f"Reconnection attempt {attempt + 1}/{self.max_reconnect_attempts}")
                        time.sleep(delay)

                    # Connect to broker
                    self.mqtt_connection.connect(self.host, self.port, 60)
                    self.mqtt_connection.loop_start()
                    
                    # Wait for connection
                    timeout = 10
                    start_time = time.time()
                    while not self.is_connected and (time.time() - start_time) < timeout:
                        time.sleep(0.1)
                    
                    if self.is_connected:
                        logger.info("Successfully connected to MQTT broker")
                        return True
                    else:
                        logger.warning(f"Connection attempt {attempt + 1} timed out")
                        
                except Exception as e:
                    logger.error(f"Connection attempt {attempt + 1} failed: {str(e)}")
            
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

    def subscribe_to_topic(self, topic: str, qos: int = 1):
        """Subscribe to any topic (server has full permissions)"""
        try:
            if not self.is_connected:
                if not self.connect():
                    raise ConnectionError("Failed to connect to MQTT broker")

            result = self.mqtt_connection.subscribe(topic, qos=qos)
            if result[0] == mqtt.MQTT_ERR_SUCCESS:
                self.subscribed_topics.add(topic)
                logger.info(f"Subscribed to topic: {topic} with QoS: {qos}")
            else:
                logger.error(f"Failed to subscribe to topic: {topic}")
                raise Exception(f"Subscription failed with code: {result[0]}")

        except Exception as e:
            logger.error(f"Subscription to {topic} failed: {str(e)}")
            raise

    def subscribe_to_multiple_topics(self, topics: List[tuple]):
        """
        Subscribe to multiple topics at once
        topics: List of tuples (topic, qos)
        """
        try:
            if not self.is_connected:
                if not self.connect():
                    raise ConnectionError("Failed to connect to MQTT broker")

            # Convert to format expected by paho-mqtt
            topic_list = [(topic, qos) for topic, qos in topics]
            
            result = self.mqtt_connection.subscribe(topic_list)
            if result[0] == mqtt.MQTT_ERR_SUCCESS:
                for topic, qos in topics:
                    self.subscribed_topics.add(topic)
                logger.info(f"Subscribed to {len(topics)} topics")
            else:
                logger.error(f"Failed to subscribe to multiple topics")
                raise Exception(f"Multiple subscription failed with code: {result[0]}")

        except Exception as e:
            logger.error(f"Multiple subscription failed: {str(e)}")
            raise

    def publish_message(self, topic: str, payload, qos: int = 1, retain: bool = False):
        """Publish message to any topic (server has full permissions)"""
        try:
            if not self.is_connected:
                if not self.connect():
                    logger.error("Failed to connect to MQTT broker for publishing")
                    return False

            # Convert payload to string if it's a dict
            if isinstance(payload, dict):
                payload = json.dumps(payload)

            logger.info(f"Publishing message to topic: {topic}")
            result = self.mqtt_connection.publish(topic, payload, qos=qos, retain=retain)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Message published successfully to topic: {topic}")
                return True
            else:
                logger.error(f"Failed to publish message, return code: {result.rc}")
                return False

        except Exception as e:
            logger.error(f"Publish to {topic} failed: {str(e)}")
            return False

    def publish_batch_messages(self, messages: List[dict]):
        """
        Publish multiple messages at once
        messages: List of dicts with keys: topic, payload, qos (optional), retain (optional)
        """
        try:
            if not self.is_connected:
                if not self.connect():
                    logger.error("Failed to connect to MQTT broker for batch publishing")
                    return False

            success_count = 0
            for msg in messages:
                topic = msg['topic']
                payload = msg['payload']
                qos = msg.get('qos', 1)
                retain = msg.get('retain', False)
                
                if self.publish_message(topic, payload, qos, retain):
                    success_count += 1

            logger.info(f"Batch publish completed: {success_count}/{len(messages)} messages sent")
            return success_count == len(messages)

        except Exception as e:
            logger.error(f"Batch publishing failed: {str(e)}")
            return False

    def unsubscribe_from_topic(self, topic: str):
        """Unsubscribe from a topic"""
        try:
            if not self.is_connected:
                logger.warning("Not connected to broker")
                return False

            result = self.mqtt_connection.unsubscribe(topic)
            if result[0] == mqtt.MQTT_ERR_SUCCESS:
                self.subscribed_topics.discard(topic)
                logger.info(f"Unsubscribed from topic: {topic}")
                return True
            else:
                logger.error(f"Failed to unsubscribe from topic: {topic}")
                return False

        except Exception as e:
            logger.error(f"Unsubscribe from {topic} failed: {str(e)}")
            return False

    def get_connection_status(self):
        """Get current connection status and statistics"""
        return {
            "is_connected": self.is_connected,
            "host": self.host,
            "port": self.port,
            "client_id": self.client_id,
            "subscribed_topics": list(self.subscribed_topics),
            "topic_count": len(self.subscribed_topics)
        }

    def _start_backgd_conn_monitor(self):
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
                
            logger.info("MQTT server client disconnected successfully")
            
        except Exception as e:
            logger.error(f"Failed to disconnect MQTT client: {str(e)}")

    # Administrative methods for server client
    def broadcast_message(self, topic_pattern: str, payload, qos: int = 1):
        """Broadcast message to all devices matching pattern"""
        try:
            # This would typically be used with topics like "broadcast/all" or "commands/all"
            return self.publish_message(topic_pattern, payload, qos, retain=False)
        except Exception as e:
            logger.error(f"Broadcast failed: {str(e)}")
            return False

    def send_command_to_device(self, device_id: str, command: dict):
        """Send command to specific device"""
        try:
            topic = f"commands/{device_id}"
            payload = json.dumps(command)
            return self.publish_message(topic, payload, qos=1)
        except Exception as e:
            logger.error(f"Failed to send command to device {device_id}: {str(e)}")
            return False

    def get_device_status(self, device_id: str, timeout: int = 5):
        """Request status from specific device"""
        try:
            # Subscribe to response topic
            response_topic = f"status/{device_id}/response"
            self.subscribe_to_topic(response_topic)
            
            # Send status request
            command_topic = f"commands/{device_id}"
            command = {"type": "status_request", "timestamp": time.time()}
            
            return self.publish_message(command_topic, json.dumps(command))
        except Exception as e:
            logger.error(f"Failed to request status from device {device_id}: {str(e)}")
            return False
        

def message_callback(topic, payload):
    try:
        logger.info(f"Received message in callback '{topic}': {json.loads(payload)}")
    except Exception as e:
        logger.error("Error in calling callback")

def main():
    try:
        # Connect to AWS IoT Core
        client = MqttServerClient(
            host="3.110.9.183",  # Change to your EC2 instance IP for remote access
            port=8883,
            username="vyom_iq",  # Uncomment if authentication is enabled
            password="vyomiqpassword",  # Uncomment if authentication is enabled
            callback=message_callback,
        )
        
        client = MqttServerClient()
        machine_id = "32"
        server_id = "hq"

        # Publish a test message
        publish_topic_1 = f"vyom-mqtt-msg/{machine_id}/gcs/connect_message/34343434.json"
        message_connect = {
            "type": "CONNECT_DRONE",
            "data": {"droneId": machine_id, "timestamp": "number", "parameters": {}},
        }
        client.publish_message(
            topic=publish_topic_1, message=json.dumps(message_connect)
        )

        # Subscribe to a test topic
        subscribe_topic_3 = f"vyom-mqtt-msg/{server_id}/"
        client.subscribe_to_topic(subscribe_topic_3)

        subscribe_topic_4 = f"vyom-mqtt-msg/{server_id}/#"
        client.subscribe_to_topic(subscribe_topic_4)

        # Keep the connection alive to receive messages
        print("Listening for messages... Press Ctrl+C to exit")
        while True:
            time.sleep(10)

    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Error in main: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
