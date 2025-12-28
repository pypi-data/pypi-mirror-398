# === Standard Library ===
import importlib
import json
import math
import os
import sys
import threading
import time
from collections import defaultdict
from typing import Callable

# === Third-party / ROS 2 Libraries ===
import rclpy
from rclpy.callback_groups import ReentrantCallbackGroup, MutuallyExclusiveCallbackGroup
from rclpy.node import Node
from rclpy.qos import (
    QoSProfile,
    QoSReliabilityPolicy,
    HistoryPolicy,
    QoSDurabilityPolicy,
)
from rosidl_runtime_py import set_message_fields
import sensor_msgs.msg
from std_msgs.msg import String
from datetime import datetime, timezone

# === Local Application Imports ===
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.generate_summary import Summariser
from vyomcloudbridge.constants.constants import (
    MISSION_SUMMARY_DT_SRC,
    default_mission_id,
)
from vyomcloudbridge.utils.mission_utils import MissionUtils
from vyomcloudbridge.services.queue_writer_json import QueueWriterJson
from vyomcloudbridge.utils.common import ServiceAbstract
from vyomcloudbridge.utils.logger_setup import setup_logger
import vyomcloudbridge.utils.converter as converter
from vyomcloudbridge.utils.throttle_utils import should_throttle


class SendDataToServer(Node, ServiceAbstract):
    """
    SendDataToServer is a ROS2 node responsible for subscribing to various topics, processing the received data,
    and writing the processed data to a queue in JSON format. The node dynamically creates subscribers based on
    a configuration file and handles different message types, including JSON and images.

    Attributes:
        callback_group (ReentrantCallbackGroup): A callback group to ensure reentrant callbacks.
        extracted_data_list (list): A list to store extracted data.
        subscribers (list): A list to store dynamically created subscribers.
        m_qos (QoSProfile): Quality of Service profile for the subscribers.
        mission_id (int): Identifier for the mission, used in the processed data.
        writer (QueueWriterJson): An instance of QueueWriterJson to handle writing messages to a queue.

    Methods:
        __init__(): Initializes the node, loads topics from a configuration file, and creates subscribers.
        get_subcribed_topics(): Retrieves the list of topics to subscribe to based on the configuration file.
        load_topic_list_from_file(): Loads the topic list from a JSON configuration file.
        create_listener_function(msg_type, f_topic): Creates a listener function for a specific topic and message type.
        import_class_from_string(class_string): Dynamically imports a class from its string representation.
        create_dynamic_subscribers(f_topic): Dynamically creates a subscriber for a given topic.
    """

    def __init__(
        self,
        get_current_mission: Callable = None,
        start_mission: Callable = None,
        end_current_mission: Callable = None,
        generate_mission_id: Callable = None,
        log_level=None,
    ):
        Node.__init__(self, "senddatatoserver")
        ServiceAbstract.__init__(self)

        self.logger.info("senddatatoserver node has started.")
        self.callback_group = ReentrantCallbackGroup()

        # Initialize extracted data list
        self.machine_subscribers = []
        self.mission_subscribers = []

        self.m_qos = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=50,
            durability=QoSDurabilityPolicy.VOLATILE,
        )
        self.camera_qos = QoSProfile(
            reliability=QoSReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_ALL,
            depth=100,
            durability=QoSDurabilityPolicy.VOLATILE,
        )

        self.writer = QueueWriterJson(log_level=log_level)

        self.mission_id = default_mission_id
        self.is_running = False
        self.mission_triggers = {}
        current_mission, error = get_current_mission()
        self.current_mission = current_mission
        self.get_current_mission = get_current_mission
        self.start_mission = start_mission
        self.end_current_mission = end_current_mission
        self.generate_mission_id = generate_mission_id
        self.update_mission_thread = None

        self.summariser = Summariser(log_level=log_level)

        # ros topic used to trigger updation of subscriber list
        self.topic_list_sub = self.create_subscription(
            String, "update_topic_list", self.update_topic_list_machine_callback, 10
        )
        self.topic_list_sub

        self.topic_list_sub_os = self.create_subscription(
            String, "update_topic_list_os", self.update_topic_list_mission_callback, 10
        )
        self.topic_list_sub_os

        self._freq_tracker = defaultdict(lambda: {"last_time": None})
        self.logger.info("SendDataToServer node initialized successfully.")

    def initiate_mission(self):
        try:
            current_mission_message, current_mission_error = self.get_current_mission()

            if current_mission_message is not None:
                current_mission_id = current_mission_message.get("id")
                self.logger.debug(
                    f"Mission already in progress. Current mission: {current_mission_message}"
                )
                return

            new_id = self.generate_mission_id()
            self.logger.info(f"Trying to start mission with ID: {new_id}")

            start_time = datetime.now(timezone.utc).isoformat()
            mission_detail, start_mission_error = self.start_mission(
                id=new_id, start_time=start_time
            )

            if start_mission_error:
                self.logger.error(f"Error starting mission: {start_mission_error}")
            else:
                self.logger.info("Mission started successfully.")

        except Exception as e:
            self.logger.error(f"Unexpected error while starting mission: {str(e)}")

    def terminate_mission(self):
        try:
            current_mission_message, current_mission_error = self.get_current_mission()

            if current_mission_message is None:
                self.logger.debug(f"Skipping: No mission ongoing")
                return

            success, error = self.end_current_mission()
            if error:
                self.logger.error(f"Failed to end current mission: {error}")
            else:
                self.logger.info("Current mission ended successfully.")
        except Exception as e:
            self.logger.error(
                f"An error occurred while ending current mission: {str(e)}"
            )

    def send_data(
        self,
        f_extracted_data,
        f_filename,
        f_topic_name,
        f_data_type,
        f_destination,
        f_send_persistent,
    ):
        self.logger.debug(
            f"data: extracted_data={f_extracted_data}, filename={f_filename}, "
            f"topic_name={f_topic_name}, destination={f_destination}"
        )

        if f_destination == "gcs":
            success, error = self.writer.write_message(
            message_data=f_extracted_data,  # json data
            filename=f_filename,  # nullable or epoch time
            data_source=f_topic_name,  # telemetry, mission_summary
            data_type=f_data_type,  # file, video, image
            mission_id=self.mission_id,  # mission_id
            priority=4,
            destination_ids=[f_destination],  # ["s3"]
            merge_chunks=True,  # True for telemetry data
            expiry_time_ms=5000,
            send_persistent=True,  # True if buffered mode
            send_live=False,  # True if live mode
        )
        else:
            
            success, error = self.writer.write_message(
                message_data=f_extracted_data,  # json data
                filename=f_filename,  # nullable or epoch time
                data_source=f_topic_name,  # telemetry, mission_summary
                data_type=f_data_type,  # file, video, image
                mission_id=self.mission_id,  # mission_id
                priority=1,  # 1 for velocity data, battery topic, and ROS data
                destination_ids=[f_destination],  # ["s3"]
                merge_chunks=True,  # True for telemetry data
                send_persistent=f_send_persistent,  # True if buffered mode
                send_live=(not f_send_persistent),  # True if live mode
            )
        if success:
            self.logger.debug(f"Successfully sent {success} for topic: {f_topic_name}")
        elif error:
            self.logger.error(f"Not sent. Error {error} for topic: {f_topic_name}")
        else:
            self.logger.debug(f"Not sent. Status unknown for topic: {f_topic_name}")

    def update_topic_list_mission_callback(self, msg):
        try:
            # Parse JSON array from message
            new_topics_list = json.loads(msg.data)
            if not isinstance(new_topics_list, list):
                self.logger.error("Expected a JSON list of topic objects.")
                return
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON from /update_topic_list_os: {e}")
            return

        self.logger.info(f"Received new_topics mission: {new_topics_list}")
        available_topics = self.load_topic_list_from_file()

        # Build the final list of topics we will subscribe to
        updated_subscription_list = []
        for received_topic in new_topics_list:
            matching_topic_config = next(
                (
                    topic
                    for topic in available_topics
                    if topic["name"] == received_topic["name"]
                ),
                None,
            )
            if matching_topic_config:
                # Merge is_subscribed and destinations
                updated_config = dict(matching_topic_config)  # start from file
                updated_config["is_subscribed"] = received_topic.get(
                    "is_subscribed", matching_topic_config.get("is_subscribed", False)
                )

                # Merge destinations per destination type
                if "destinations" in received_topic:
                    for dest_key, dest_vals in received_topic["destinations"].items():
                        if dest_key in updated_config["destinations"]:
                            updated_config["destinations"][dest_key].update(dest_vals)
                        else:
                            updated_config["destinations"][dest_key] = dest_vals

                updated_subscription_list.append(updated_config)

        new_topics = {topic["topic"] for topic in updated_subscription_list}
        self.logger.info(f"New topics set: {new_topics}")

        # Get current mission_subscribers
        current_subscriber_map = {
            sub.topic_name: sub for sub in self.mission_subscribers
        }
        current_topics = set(current_subscriber_map.keys())

        if current_topics == new_topics:
            self.logger.info("Topic list unchanged. No update needed.")
            return

        self.logger.info(f"New topics: {new_topics}, Current topics: {current_topics}")

        # Keep existing subs for still-needed topics
        self.mission_subscribers = [
            sub for sub in self.mission_subscribers if sub.topic_name in new_topics
        ]

        # Unsubscribe from removed topics
        for topic_name in current_topics - new_topics:
            self.logger.info(f"Unsubscribing from topic: {topic_name}")
            self.destroy_subscription(current_subscriber_map[topic_name])

        # Subscribe to newly added topics
        for topic in updated_subscription_list:
            if topic["topic"] not in current_topics:
                self.logger.info(
                    f"Subscribing to: {topic['name']} | {topic['data_type']} | {topic['topic']} "
                    f"| destinations: {topic['destinations']}"
                )
                self.create_dynamic_subscribers(topic, self.mission_subscribers)

    def update_topic_list_machine_callback(self, msg):
        new_topic_list = self.get_subcribed_topics()
        # new_mission_topic_list = self.get_mission_subcribed_topics()
        # self.logger.info(f"[Machine] Received new topic list: {new_mission_topic_list}")

        new_topics = {topic["topic"] for topic in new_topic_list}
        current_subscriber_map = {
            sub.topic_name: sub for sub in self.machine_subscribers
        }
        current_topics = set(current_subscriber_map.keys())

        # Early exit if no changes
        if current_topics == new_topics:
            self.logger.debug("[Machine] Topic list unchanged. No update needed.")
            return

        # Build the new subscriber list before destroying any
        self.machine_subscribers = [
            sub for sub in self.machine_subscribers if sub.topic_name in new_topics
        ]

        # Unsubscribe from topics that are no longer needed
        for topic_name in current_topics - new_topics:
            self.logger.debug(f"[Machine] Unsubscribing from topic: {topic_name}")
            self.destroy_subscription(current_subscriber_map[topic_name])

        # Subscribe to new topics
        for topic in new_topic_list:
            if topic["topic"] not in current_topics:
                self.logger.info(
                    f"[Machine] Subscribing to new topic: {topic['topic']}"
                )
                self.create_dynamic_subscribers(topic, self.machine_subscribers)

    def create_subscribers(self):
        self.is_running = True
        self.logger.debug(f"topics {self.get_subcribed_topics()}")

        self.update_mission_thread = threading.Thread(
            target=self.update_mission_loop, daemon=True
        )
        self.update_mission_thread.start()

        mission_triggers = self.get_mission_triggers()
        if len(mission_triggers) > 0:
            self.mission_triggers = mission_triggers
            self.logger.info(f"Mission triggers: {self.mission_triggers}")
        else:
            self.logger.info(f"No mission triggers")

        for topic_details in self.get_subcribed_topics():
            self.logger.info(f"Subscribing to topic: {topic_details}")
            self.create_dynamic_subscribers(topic_details, self.machine_subscribers)

    def get_mission_triggers(self):
        """
        Retrieve the list of mission trigger topics.

        This method loads a list of topics from a file and filters them to return
        only those topics that are marked as mission triggers.

        Returns:
            tuple: (bool, dict)
                - bool: True if at least one mission trigger found
                - dict: Mapping topic -> {start_mission_trigger, stop_mission_trigger}
        """
        topic_list = self.load_topic_list_from_file()

        mission_triggers = {}
        for entry in topic_list:
            topic_name = entry.get("topic")
            start_trigger = entry.get("start_mission_trigger")
            stop_trigger = entry.get("stop_mission_trigger")

            if start_trigger and stop_trigger:
                mission_triggers[topic_name] = {
                    "start_mission_trigger": start_trigger,
                    "stop_mission_trigger": stop_trigger,
                }

        return mission_triggers

    def get_subcribed_topics(self):
        """
        Retrieve the list of subscribed topics.

        This method loads a list of topics from a file and filters them to return
        only those topics that are marked as subscribed.

        Returns:
            list: A list of dictionaries representing the subscribed topics.
        """

        topic_list = self.load_topic_list_from_file()
        return [
            topics
            for topics in topic_list
            if topics.get("is_subscribed", False)
            or topics.get("is_subscribe_on_mission", False)
        ]

    def load_topic_list_from_file(self):
        """
        Loads a list of topics from a JSON file.

        This method reads the file located at '/etc/vyomcloudbridge/machine_topics.json',
        deserializes its JSON content, and returns the resulting list of topics.

        Returns:
            list: A list of topics loaded from the JSON file.
        """
        with open("/etc/vyomcloudbridge/machine_topics.json", "r") as f:
            serialised_topic_list = json.load(f)
        return serialised_topic_list

    def replace_nan_with_null(self, obj):
        """
        Recursively traverse the input object and replace all float NaN values with None.
        This ensures compatibility with JSON serialization, where None is converted to null.
        """
        if isinstance(obj, dict):
            return {k: self.replace_nan_with_null(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self.replace_nan_with_null(item) for item in obj]
        elif isinstance(obj, float) and math.isnan(obj):
            return None
        else:
            return obj

    def send_summary(self, summary):
        self.logger.debug(f"Summary {summary}")

        self.writer.write_message(
            background=True,
            data_source=MISSION_SUMMARY_DT_SRC,
            data_type="json",
            destination_ids=["gcs"],
            expiry_time_ms=5000,
            filename=None,
            merge_chunks=True,
            message_data=summary,
            mission_id=self.mission_id,
            priority=3,
        )
        success, error = self.writer.write_message(
            background=True,
            data_source=MISSION_SUMMARY_DT_SRC,
            data_type="json",
            destination_ids=["s3"],  # ["s3"]
            filename=None,  # nullable or epoch time
            merge_chunks=True,  # True for telemetry data
            message_data=summary,  # json data
            mission_id=self.mission_id,  # mission_id
            priority=3,
            send_live=True,
        )
        if success:
            self.logger.debug(f"Successfully sent {success} for topic: mission_summary")
        elif error:
            self.logger.error(f"Not sent. Error {error} for topic: mission_summary")
        else:
            self.logger.info(f"Not sent. Status unknown for topic: mission_summary")

    def get_mission_id(self):

        if self.current_mission is None:
            return default_mission_id
        self.logger.debug(f"self.current_mission: {self.current_mission}")

        if self.current_mission.get("mission_status") == 1:
            self.summariser.set_mission_mode(1)
            return self.current_mission.get("id") or default_mission_id

        if self.current_mission.get("mission_status") == 2:
            if self.summariser.get_mission_mode() == 1:
                self.logger.debug("stopped")
                self.summariser.print_summary()
                self.send_summary(self.summariser.print_summary())
                self.summariser.set_mission_mode(2)
                self.summariser.reset()

        return default_mission_id

    def update_mission_loop(self):
        while self.is_running:
            current_mission, error = self.get_current_mission()
            if error:
                self.logger.error(f"Error getting current mission: {error}")
            else:
                self.current_mission = current_mission
            time.sleep(0.5)

    def get_or_preprocess_message(self, f_msg, f_topic_name, f_msg_data_type):
        """
        Returns cached preprocessed data if within max_age_ms, otherwise regenerates.
        """
        current_value = converter.convert(f_msg_data_type, 1, f_msg)

        cleaned_value = self.replace_nan_with_null(current_value)
        epoch_ms = int(time.time() * 1000)

        if f_msg_data_type == "sensor_msgs.msg.Image":
            filename = f"{epoch_ms}.jpeg"
            data_type = "image"
            extracted_data = cleaned_value
        else:
            filename = f"{epoch_ms}.json"
            data_type = "json"

            timenow = time.time()
            timestamp_sec = int(timenow)
            timestamp_nsec = int((timenow - timestamp_sec) * 1_000_000_000)

            extracted_data = {
                "timestamp": {
                    "seconds": timestamp_sec,
                    "nanoseconds": timestamp_nsec,
                },
                "key": f_topic_name,
                "mission_id": self.mission_id,
                "data": {},
            }
            extracted_data["data"] = cleaned_value

        self.logger.debug(
            f"Logs data type: {type(cleaned_value)}, filename: {filename}, data_type: {data_type} epoch_ms"
        )

        # Get mission id
        self.mission_id = self.get_mission_id()
        self.logger.debug(f"self.mission_id: {self.mission_id}")

        return {
            "filename": filename,
            "data_type": data_type,
            "extracted_data": extracted_data,
            "topic_name": f_topic_name,
        }

    def save_locally_or_send(
        self,
        f_processed_payload,
        f_can_send_buffered,
        f_can_send_live,
        f_destination,
        f_is_local,
    ):
        """
        Saves the message locally or sends it to a remote server based on the configuration.
        Args:
            msg: The incoming message to be processed.
            f_topic_name (str): The name of the topic from which the message was received.
            f_msg_data_type: The data type of the message.
            upload_freq (float): The frequency at which data should be uploaded.
            msg_freq (float): The frequency of incoming messages.
        """
        filename = f_processed_payload["filename"]
        data_type = f_processed_payload["data_type"]
        extracted_data = f_processed_payload["extracted_data"]
        f_topic_name = f_processed_payload["topic_name"]

        self.logger.debug(f"Processing message for topic: {f_topic_name}")

        if f_is_local:
            self.logger.debug(f"Saving locally for: {f_topic_name}")
            now = datetime.now()
            local_path = f"/var/log/vyomcloudbridge/mission_data/{self.mission_id}/{now.strftime('%Y-%m-%d')}/{now.strftime('%H')}/{f_topic_name}"
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            self.logger.debug(f"Local path: {local_path}")

            if data_type == "image":
                ts = int(time.time() * 1000)
                filename = f"{ts}.jpeg"

                os.makedirs(local_path, exist_ok=True)
                full_path = os.path.join(local_path, filename)

                with open(full_path, "wb") as image_file:
                    image_file.write(extracted_data)
                self.logger.debug(f"Image saved locally at: {full_path}")

            else:
                with open(local_path, "a") as file:
                    json.dump(extracted_data, file)
                    file.write("\n")

        elif f_can_send_buffered or f_can_send_live:
            self.logger.debug(f"Sending data for: {f_topic_name} to {f_destination} extracted_data: {extracted_data}")
            if f_can_send_buffered:
                self.logger.debug(f"Buffered sending enabled for: {f_topic_name}")
                self.send_data(
                    extracted_data,
                    filename,
                    f_topic_name,
                    data_type,
                    f_destination,
                    True,
                )

            if f_can_send_live:
                self.logger.debug(f"Live sending enabled for: {f_topic_name}")
                self.send_data(
                    extracted_data,
                    filename,
                    f_topic_name,
                    data_type,
                    f_destination,
                    False,
                )

        else:
            self.logger.warning(f"Cannot send or save data for: {f_topic_name}")

    def mission_trigger_action(self, msg, topic):
        """
        Print mission trigger values and corresponding message fields.
        """
        triggers = self.mission_triggers[topic]
        self.logger.info(f"Mission triggers configured: {triggers}")

        # Check both start and stop triggers
        for trigger_type, trigger_fields in triggers.items():
            if not trigger_fields:
                self.logger.info(f"trigger_fields {trigger_fields} empty, skipping")
                continue
            for field, expected_value in trigger_fields.items():
                actual_value = getattr(msg, field, None)
                self.logger.info(
                    f"[{trigger_type}] field='{field}', expected='{expected_value}', actual='{actual_value}'"
                )

                if str(expected_value) == str(actual_value):
                    if trigger_type == "start_mission_trigger":
                        self.logger.info(
                            f"Start mission triggered by {field}={actual_value}"
                        )
                        self.initiate_mission()
                        return True
                    elif trigger_type == "stop_mission_trigger":
                        self.logger.info(
                            f"Stop mission triggered by {field}={actual_value}"
                        )
                        self.terminate_mission()
                        return False

    def create_listener_function(self, f_topic_details):
        """
        Creates a listener function for processing incoming messages of a specific type and topic.
        The generated listener function performs the following:
            - Converts the incoming message to the desired format using a converter.
            - Extracts a timestamp from the message header if available.
            - Constructs a filename based on the current epoch time and a padding value.
            - Differentiates between image and JSON data types.
            - Prepares the extracted data for writing, including metadata such as timestamp,
              topic, mission ID, and the converted data.
            - Writes the processed data to a destination using the `self.writer.write_message` method.
        """
        f_msg_data_type = f_topic_details["data_type"]
        f_topic_name = f_topic_details["name"]
        f_topic = f_topic_details["topic"]
        f_destinations = f_topic_details["destinations"]
        f_is_subscribed = f_topic_details["is_subscribed"]
        f_is_subscribe_on_mission = f_topic_details["is_subscribe_on_mission"]

        # eg: f_msg_data_type=vyom_mission_msgs.msg.MissionStatus, f_topic_name=MISSION_TOPIC
        def callback(msg):
            self.mission_id = self.get_mission_id()
            
            self.logger.debug(f"message came for topic : {f_topic_name} msg {msg}")

            if len(self.mission_triggers) > 0:
                if f_topic not in self.mission_triggers:
                    self.logger.debug(
                        f"No mission triggers defined for topic {f_topic}"
                    )
                else:
                    if self.mission_trigger_action(msg, f_topic):
                        self.logger.debug("Start mission triggered")
                    else:
                        self.logger.debug("Stop mission triggered")

            if self.current_mission is None:
                l_current_mission = -1
            else:
                l_current_mission = self.current_mission.get("mission_status")

            if l_current_mission == 1:
                self.logger.debug("Mission is in progress, updating summariser")
                self.summariser.update(f_topic, msg)

            if f_is_subscribed:
                self.logger.debug(
                    f"Processing and sending data for topic: {f_topic_name}"
                )
            else:
                self.logger.debug(f"Checking if is_subscribe_on_mission")
                self.logger.debug(
                    f"self.current_mission.get('mission_status'): {l_current_mission}"
                )

                if f_is_subscribe_on_mission and l_current_mission == 1:
                    self.logger.debug(
                        f"Processing and sending data for topic: {f_topic_name} during mission"
                    )
                else:
                    self.logger.debug(
                        f"Not processing data for topic: {f_topic_name} as not subscribed and not during mission"
                    )
                    return callback

            self.logger.debug(f"Ros data processing for ros_topic: {f_topic_name}")

            tracker = self._freq_tracker[f_topic_name]
            now = self._clock.now().nanoseconds / 1e9

            self.logger.debug(f"Destinations: {f_destinations}")

            eligible_destinations = []

            # iterate over the destinations
            for destination, rates in f_destinations.items():
                self.logger.debug(f"topic: {f_topic_name} Processing destination: {destination} -> {rates}")
                (
                    can_send_buffered,
                    can_send_live,
                    buf_freq,
                    live_freq,
                    msg_freq,
                    is_local,
                ) = should_throttle(
                    tracker, destination, rates["live"], rates["buffered"], now
                )
                self.logger.debug(
                    f"topic: {f_topic_name} can_send_buffered: {can_send_buffered}, can_send_live: {can_send_live}, "
                    f"buf_freq: {buf_freq}, live_freq: {live_freq}, msg_freq: {msg_freq}, is_local: {is_local}"
                )

                # Collect only those destinations we can send to
                if is_local or can_send_buffered or can_send_live:
                    eligible_destinations.append(
                        {
                            "destination": destination,
                            "can_send_buffered": can_send_buffered,
                            "can_send_live": can_send_live,
                            "is_local": is_local,
                        }
                    )

            # Only preprocess if there’s something to send
            if eligible_destinations:
                processed_payload = self.get_or_preprocess_message(
                    msg, f_topic_name, f_msg_data_type
                )

                for dest_info in eligible_destinations:
                    self.save_locally_or_send(
                        processed_payload,
                        dest_info["can_send_buffered"],
                        dest_info["can_send_live"],
                        dest_info["destination"],
                        dest_info["is_local"],
                    )
            else:
                self.logger.info(
                    "No eligible destinations this cycle — skipping preprocessing."
                )

            self.logger.debug(f"Ros data processed for ros_topic: {f_topic_name}")

        return callback

    def import_class_from_string(self, class_string):
        """
        Dynamically imports and returns a class from its string representation.

        Args:
            class_string (str): A string representation of the class to import.
                The string can be in the format "<class 'module.submodule.ClassName'>"
                or simply "module.submodule.ClassName".

        Returns:
            type: The class object corresponding to the given string representation.
        """
        class_string = class_string.strip()
        if class_string.startswith("<class '") and class_string.endswith("'>"):
            # Extract the part between the quotes
            class_path = class_string[8:-2]  # Remove "<class '" and "'>"
        else:
            class_path = class_string

        # Split into module path and class name
        parts = class_path.split(".")
        module_path = ".".join(parts[:-1])
        class_name = parts[-1]

        # Import the module dynamically
        module = importlib.import_module(module_path)

        return getattr(module, class_name)

    def create_dynamic_subscribers(self, f_topic_details, f_subscribers):
        """
        Dynamically creates and adds a subscriber to the list of subscribers.
        This method takes a topic configuration, creates a subscription for the
        specified data type and topic path, and appends it to the `subscribers` list.

        Args:
            f_topic_details (dict): A dictionary containing the topic configuration with the following keys:
                - "data_type" (str): The fully qualified class name of the data type to subscribe to.
                - "path" (str): The topic path to subscribe to.
                - "name" (str): The name of the topic.
        """
        try:
            if "camera" in f_topic_details["topic"].lower():
                qos_profile = self.camera_qos
            else:
                qos_profile = self.m_qos

            f_subscribers.append(
                self.create_subscription(
                    self.import_class_from_string(f_topic_details["data_type"]),
                    f_topic_details["topic"],
                    self.create_listener_function(f_topic_details),
                    callback_group=self.callback_group,
                    qos_profile=qos_profile,
                )
            )
            self.logger.info(
                f"Subscribed to topic: {f_topic_details['topic']} with type: {f_topic_details['data_type']}"
            )
        except Exception as e:
            self.logger.error(
                f"Failed to subscribe to topic: {f_topic_details['topic']} with type: {f_topic_details['data_type']}. Error: {e}"
            )

    def subscriber_shutdown(self):
        """Shuts down all active subscribers and resets related variables."""
        self.is_running = False
        self.logger.info("Shutting down all subscribers.")

        # Explicitly destroy all subscriptions
        for subscriber in self.machine_subscribers:
            self.destroy_subscription(subscriber)

        self.machine_subscribers.clear()

        if (
            hasattr(self, "update_mission_thread")
            and self.update_mission_thread
            and self.update_mission_thread.is_alive()
        ):
            self.update_mission_thread.join(timeout=5)

    def start(self):
        pass

    def stop(self):
        pass

    def cleanup(self):
        pass


class RosPublisher(ServiceAbstract):
    def __init__(self, log_level=None):
        super().__init__(log_level=log_level)
        self.log_level = log_level
        self.logger.info("Initializing RosPublisher..")
        self.is_running = False
        self.spin_thread = None
        self.mission_utils = MissionUtils(log_level=log_level)
        self.get_current_mission = self.mission_utils.get_current_mission
        self.start_mission = self.mission_utils.start_mission
        self.end_current_mission = self.mission_utils.end_current_mission
        self.generate_mission_id = self.mission_utils.generate_mission_id

        try:
            rclpy.init(args=None)
        except Exception as e:
            self.logger.warning(f"Failed to initialize ROS: {e}")

        self.send_data_to_server = SendDataToServer(
            self.get_current_mission,
            self.start_mission,
            self.end_current_mission,
            self.generate_mission_id,
            log_level=self.log_level,
        )
        self.logger.info("RosPublisher Initialized successfully")

    def start(self):
        try:
            self.logger.info("Starting RosPublisher service...")
            self.is_running = True

            self.send_data_to_server.create_subscribers()

            def start_proccess():
                rclpy.spin(self.send_data_to_server)
                while self.is_running:
                    time.sleep(10)

            self.stats_thread = threading.Thread(target=start_proccess, daemon=True)
            self.stats_thread.start()
            self.logger.info("RosPublisher service started!")

        except Exception as e:
            self.logger.error(f"Error starting RosPublisher service: {str(e)}")
            self.stop()

    def stop(self):
        try:
            self.is_running = False
            self.send_data_to_server.subscriber_shutdown()
            rclpy.shutdown()
            self.spin_thread.join()
            self.logger.info("Shutdown complete. RosPublisher service stopped!")
        except Exception as e:
            self.logger.error(f"Error in stoping RosPublisher: {str(e)}")

    def cleanup(self):
        try:
            self.mission_utils.cleanup()
        except Exception as e:
            self.logger.error(f"Failed to cleanup mission utils: {e}")

    def is_healthy(self):
        return self.is_running

    def __del__(self):
        """Destructor called by garbage collector to ensure resources are cleaned up, when object is about to be destroyed"""
        try:
            self.logger.error(
                "Destructor called by garbage collector to cleanup RosPublisher"
            )
            self.stop()
        except Exception as e:
            pass


def main(args=None):
    data_streamer = RosPublisher()
    try:
        data_streamer.start()
        time.sleep(100)
    finally:
        data_streamer.stop()
    print("Completed SendDataToServer service example")


if __name__ == "__main__":
    main()