import time
import threading
import json
import uuid
import logging
from typing import Callable, Optional
import paho.mqtt.client as mqtt
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"


class MosquittoMqttClient:
    def __init__(
        self,
        host: str = "localhost",
        port: int = 8883,
        username: Optional[str] = None,
        password: Optional[str] = None,
        machine_id: str = "default",
        callback: Optional[Callable] = None,
        keep_alive: int = 60,
        clean_session: bool = True,
    ):
        """
        Initialize Mosquitto MQTT Client
        
        Args:
            host: MQTT broker hostname/IP
            port: MQTT broker port (default 8883)
            username: Username for authentication (optional)
            password: Password for authentication (optional)
            machine_id: Machine identifier
            callback: Callback function for received messages
            keep_alive: Keep alive interval in seconds
            clean_session: Whether to use clean session
        """
        try:
            self.host = host
            self.port = port
            self.username = username
            self.password = password
            self.machine_id = machine_id
            self.message_callback = callback
            self.keep_alive = keep_alive
            self.clean_session = clean_session
            
            # Generate unique client ID
            self.client_id = f"machine_{self.machine_id}_{uuid.uuid4().hex[:8]}"
            
            # Connection state tracking
            self.connection_state = ConnectionState.DISCONNECTED
            self.connection_lock = threading.Lock()
            
            # Subscription tracking
            self.subscribed_topics = set()
            
            # Reconnection parameters
            self.max_reconnect_attempts = 5
            self.base_reconnect_delay = 1  # Base delay in seconds
            self.max_reconnect_delay = 60
            self.reconnect_attempt = 0
            
            # Create MQTT client
            self.client = mqtt.Client(
                client_id=self.client_id,
                clean_session=self.clean_session,
                protocol=mqtt.MQTTv311
            )
            
            # Set up authentication if provided
            if self.username and self.password:
                self.client.username_pw_set(self.username, self.password)
            
            # Set up callbacks
            self.client.on_connect = self._on_connection_resumed
            self.client.on_disconnect = self._on_connection_interrupted
            self.client.on_message = self._on_message
            self.client.on_subscribe = self._on_subscribe
            self.client.on_publish = self._on_publish
            self.client.on_log = self._on_log
            
            # Set will message (optional)
            will_topic = f"status/{self.machine_id}/offline"
            will_payload = json.dumps({
                "machine_id": self.machine_id,
                "status": "offline",
                "timestamp": time.time()
            })
            self.client.will_set(will_topic, will_payload, qos=1, retain=True)
            
            # Start connection
            self._connect()
            
            print(f"MosquittoMqttClient initialized with client_id: {self.client_id}")
            
        except Exception as e:
            print(f"Error-Error initializing MosquittoMqttClient: {str(e)}")
            raise
    
    def _connect(self):
        """Connect to MQTT broker with retry logic"""
        with self.connection_lock:
            if self.connection_state in [ConnectionState.CONNECTING, ConnectionState.CONNECTED]:
                print("Connection already in progress or established")
                return
            
            self.connection_state = ConnectionState.CONNECTING
        
        try:
            print(f"Connecting to MQTT broker at {self.host}:{self.port}")
            self.client.connect(self.host, self.port, self.keep_alive)
            
            # Start the network loop in a separate thread
            self.client.loop_start()
            
        except Exception as e:
            print(f"Error-Failed to connect to MQTT broker: {str(e)}")
            with self.connection_lock:
                self.connection_state = ConnectionState.DISCONNECTED
            self._schedule_reconnect()
    
    def _on_connection_resumed(self, client, userdata, flags, rc):
        """Callback for when client connects to broker"""
        if rc == 0:
            print("Successfully connected to MQTT broker")
            with self.connection_lock:
                self.connection_state = ConnectionState.CONNECTED
                self.reconnect_attempt = 0
            
            # Publish online status
            self._publish_status("online")
            
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
            error_msg = error_messages.get(rc, f"Connection refused - unknown error {rc}")
            print(f"Error-Failed to connect to MQTT broker: {error_msg}")
            
            with self.connection_lock:
                self.connection_state = ConnectionState.DISCONNECTED
            self._schedule_reconnect()
    
    def _on_connection_interrupted(self, client, userdata, rc):
        """Callback for when client disconnects from broker"""
        with self.connection_lock:
            self.connection_state = ConnectionState.DISCONNECTED
        
        if rc != 0:
            print(f"Warning-Unexpected disconnection from MQTT broker (rc: {rc})")
            self._schedule_reconnect()
        else:
            print("Disconnected from MQTT broker")
    
    def _on_message(self, client, userdata, message):
        """Callback for when a message is received"""
        try:
            topic = message.topic
            payload = message.payload.decode('utf-8')
            
            print(f"Received message from topic '{topic}': {payload}")
            
            # Try to parse JSON payload
            try:
                parsed_payload = json.loads(payload)
            except json.JSONDecodeError:
                parsed_payload = payload
            
            # Call user callback if provided
            if self.message_callback:
                self.message_callback(topic, parsed_payload)
            else:
                print("No callback provided, skipping callback execution")
                
        except Exception as e:
            print(f"Error-Error processing received message: {str(e)}")
    
    def _on_subscribe(self, client, userdata, mid, granted_qos):
        """Callback for when subscription is completed"""
        print(f"Subscription completed with QoS: {granted_qos}")
    
    def _on_publish(self, client, userdata, mid):
        """Callback for when publish is completed"""
        print(f"Message published successfully (mid: {mid})")
    
    def _on_log(self, client, userdata, level, buf):
        """Callback for MQTT client logging"""
        print(f"MQTT Client Log: {buf}")
    
    def _schedule_reconnect(self):
        """Schedule reconnection attempt"""
        if self.reconnect_attempt >= self.max_reconnect_attempts:
            print("Error- Maximum reconnection attempts reached")
            return
        
        delay = self.base_reconnect_delay * (2 ** self.reconnect_attempt)
        self.reconnect_attempt += 1
        
        print(f"Scheduling reconnection attempt {self.reconnect_attempt} in {delay} seconds")
        
        def reconnect():
            time.sleep(delay)
            with self.connection_lock:
                self.connection_state = ConnectionState.RECONNECTING
            self._connect()
        
        threading.Thread(target=reconnect, daemon=True).start()
    
    def _resubscribe_to_topics(self):
        """Resubscribe to all previously subscribed topics"""
        for topic in self.subscribed_topics:
            try:
                result, mid = self.client.subscribe(topic, qos=1)
                if result == mqtt.MQTT_ERR_SUCCESS:
                    print(f"Resubscribed to topic: {topic}")
                else:
                    print(f"Error-Failed to resubscribe to topic {topic}: {result}")
            except Exception as e:
                print(f"Error-Error resubscribing to topic {topic}: {str(e)}")
    
    def _publish_status(self, status: str):
        """Publish machine status"""
        try:
            topic = f"status/{self.machine_id}/{status}"
            payload = json.dumps({
                "machine_id": self.machine_id,
                "status": status,
                "timestamp": time.time()
            })
            self.publish_message(topic, payload, retain=True)
        except Exception as e:
            print(f"Error-Failed to publish status: {str(e)}")
    
    def subscribe_to_topic(self, topic: str, qos: int = 1):
        """
        Subscribe to a topic
        
        Args:
            topic: Topic to subscribe to
            qos: Quality of Service level (0, 1, or 2)
        """
        try:
            if self.connection_state != ConnectionState.CONNECTED:
                print(f"Error-Cannot subscribe to {topic}: Not connected to broker")
                # Store topic for later subscription
                self.subscribed_topics.add(topic)
                return False
            
            result, mid = self.client.subscribe(topic, qos=qos)
            
            if result == mqtt.MQTT_ERR_SUCCESS:
                self.subscribed_topics.add(topic)
                print(f"Subscribed to topic: {topic} with QoS: {qos}")
                return True
            else:
                print(f"Error-Failed to subscribe to topic {topic}: {result}")
                return False
                
        except Exception as e:
            print(f"Error-Error subscribing to topic {topic}: {str(e)}")
            return False
    
    def publish_message(self, topic: str, payload, qos: int = 1, retain: bool = False):
        """
        Publish a message to a topic
        
        Args:
            topic: Topic to publish to
            payload: Message payload (string, dict, or bytes)
            qos: Quality of Service level (0, 1, or 2)
            retain: Whether to retain the message
        """
        try:
            # Check topic length (AWS IoT Core limit similar check)
            path_parts = topic.split("/")
            if len(path_parts) > 8:
                print("Error- Topic length exceeded - maximum of 8 sub-parts allowed")
                return False
            
            if self.connection_state != ConnectionState.CONNECTED:
                print(f"Error-Cannot publish to {topic}: Not connected to broker")
                return False
            
            # Convert payload to string if it's a dict
            if isinstance(payload, dict):
                payload = json.dumps(payload)
            elif isinstance(payload, (int, float, bool)):
                payload = str(payload)
            
            print(f"Publishing message to topic: {topic}")
            
            result = self.client.publish(topic, payload, qos=qos, retain=retain)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"Message published successfully to topic: {topic}")
                return True
            else:
                print(f"Error-Failed to publish message to {topic}: {result.rc}")
                return False
                
        except Exception as e:
            print(f"Error-Error publishing message to {topic}: {str(e)}")
            return False
    
    def unsubscribe_from_topic(self, topic: str):
        """Unsubscribe from a topic"""
        try:
            if self.connection_state != ConnectionState.CONNECTED:
                print(f"Error-Cannot unsubscribe from {topic}: Not connected to broker")
                return False
            
            result, mid = self.client.unsubscribe(topic)
            
            if result == mqtt.MQTT_ERR_SUCCESS:
                self.subscribed_topics.discard(topic)
                print(f"Unsubscribed from topic: {topic}")
                return True
            else:
                print(f"Error-Failed to unsubscribe from topic {topic}: {result}")
                return False
                
        except Exception as e:
            print(f"Error-Error unsubscribing from topic {topic}: {str(e)}")
            return False
    
    def is_connected(self) -> bool:
        """Check if client is connected to broker"""
        return self.connection_state == ConnectionState.CONNECTED
    
    def get_connection_state(self) -> ConnectionState:
        """Get current connection state"""
        return self.connection_state
    
    def close_connection(self):
        """Gracefully close the MQTT connection"""
        try:
            # Publish offline status
            self._publish_status("offline")
            
            # Wait a moment for the message to be sent
            time.sleep(1)
            
            # Stop the network loop
            self.client.loop_stop()
            
            # Disconnect from broker
            self.client.disconnect()
            
            with self.connection_lock:
                self.connection_state = ConnectionState.DISCONNECTED
            
            print("MQTT connection closed successfully")
            
        except Exception as e:
            print(f"Error-Error closing MQTT connection: {str(e)}")


# Example usage and test functions
def example_callback(topic: str, payload):
    """Example callback function for handling received messages"""
    print(f"Callback received - Topic: {topic}, Payload: {payload}")


def main():
    """Example usage of MosquittoMqttClient"""
    
    # Initialize client
    client = MosquittoMqttClient(
        host="localhost",  # Change to your EC2 instance IP for remote access
        port=8883,
        machine_id="test_machine_001",
        callback=example_callback,
        # username="your_username",  # Uncomment if authentication is enabled
        # password="your_password",  # Uncomment if authentication is enabled
    )
    
    # Wait for connection
    time.sleep(2)
    
    # Subscribe to topics
    client.subscribe_to_topic("test/topic")
    client.subscribe_to_topic(f"commands/{client.machine_id}")
    
    # Publish some test messages
    client.publish_message("test/topic", "Hello from Mosquitto client!")
    client.publish_message("test/topic", {"message": "JSON payload", "timestamp": time.time()})
    
    # Keep the client running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")
        client.close_connection()


if __name__ == "__main__":
    main()