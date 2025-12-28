# vyomcloudbridge/queue_writer_file.py
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import time
import random
import configparser
import os
import signal
import threading
import sys
from typing import Dict, Any, List, Tuple, Union, Optional
from datetime import datetime, timezone
import json
import io
import csv
import base64
from vyomcloudbridge.services.rabbit_queue.queue_main import RabbitMQ
from vyomcloudbridge.utils.common import get_file_info, get_mission_upload_dir
from vyomcloudbridge.utils.configs import Configs
from vyomcloudbridge.utils.logger_setup import setup_logger
from vyomcloudbridge.constants.constants import (
    DUMMY_DATA_DT_SRC,
    MAX_FILE_SIZE,
    ROUTED_MACHINE_DT_SRC,
    data_buffer_key,
    default_project_id,
    DEFAULT_TIMEZONE,
)


class StreamFormatter:
    """Main class for handling message queue writing operations."""

    # Mapping file extensions to data types
    def __init__(
        self,
        multi_machine: bool = False,
        machine_key: Optional[str] = None,
        log_level=None,
    ):
        self.logger = setup_logger(
            name=self.__class__.__module__ + "." + self.__class__.__name__,
            show_terminal=False,
            log_level=log_level,
        )
        self.rabbit_mq = RabbitMQ(log_level=log_level)
        self.machine_config = Configs.get_machine_config()
        self.machine_id = self.machine_config.get("machine_id", "-") or "-"
        self.organization_id = self.machine_config.get("organization_id", "-") or "-"
        self.machine_timezone = (
            self.machine_config.get("timezone", DEFAULT_TIMEZONE) or DEFAULT_TIMEZONE
        )
        self.machine_timezone_info = self._get_timezone_info()
        self._setup_signal_handlers()

        # Initialize configuration before starting publisher loop
        self.multi_machine: bool = multi_machine
        self.machine_key: Optional[str] = machine_key
        self.project_id = "_all_"  # TODO later
        self.mission_id = "_all_"  # TODO later
        self.destination_ids = ["s3"]  # TODO later
        self.priority = 1  # Default priority for messages

        self.is_publishing = False
        self.data = (
            {}
        )  # data[machine_id][date][data_source]["value"], data[machine_id][date][data_source]=["json array"]
        self.data_upload_time = (
            {}
        )  # data[machine_id][date][data_source]["value"], data[machine_id][date][data_source]=timestamp
        self.data_object_lock = threading.Lock()
        self.key_seperator = "__"
        self.publisher_loop_delay = 1  # 1 second
        self.auto_publish_intrl = 19000  # milisecond
        self.max_array_len = 100  # later we will do by size # TODO
        self._init_data_publisher_loop()

        # in save self.multi_machine = True
        self.routed_machine_lock = threading.Lock()
        self.routed_machine_ids = set()
        self.routed_machine_loop_delay = 60  # 6 second
        self.routed_machine_data_source = ROUTED_MACHINE_DT_SRC
        if self.multi_machine:
            self._init_routed_device_list_loop()

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""

        def signal_handler(signum, frame):
            self.logger.info("Shutting down...")
            self.cleanup()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def _get_timezone_info(self):
        """
        Get timezone info for the machine, with fallback to default.

        Returns:
            ZoneInfo object for the machine timezone
        """
        try:
            return ZoneInfo(self.machine_timezone)
        except Exception as e:
            self.logger.warning(
                f"Invalid timezone '{self.machine_timezone}', falling back to default: {e}"
            )
            return ZoneInfo(DEFAULT_TIMEZONE)

    def sort_json_array(self, array: list, key):
        """
        Sorts a list of dictionaries (JSON array) in ascending order of a given key.
        Missing keys are treated as having value None and placed at the end.
        """
        if not array or not isinstance(array, list):
            return []

        try:
            sorted_array = sorted(
                array,
                key=lambda x: x.get(
                    key, float("inf")
                ),  # use infinity for missing key (so they go last)
            )
            return sorted_array
        except Exception as e:
            print(f"Error sorting JSON array by key '{key}': {e}")
            return array  # return unsorted if something goes wrong

    def _init_routed_device_list_loop(
        self,
    ):  # TODO this is not persistent data, published every minute only
        """
        Start a background thread to monitor connection health
        Uses built-in AWS IoT SDK reconnection mechanisms
        """
        self.is_publishing = True

        def routed_device_loop(routed_machine_loop_delay):
            while self.is_publishing:
                with self.routed_machine_lock:
                    try:
                        # Get current date in machine timezone
                        current_utc = datetime.now(timezone.utc)
                        current_date = current_utc.astimezone(
                            self.machine_timezone_info
                        ).strftime("%Y-%m-%d")
                        for machine_id in list(self.routed_machine_ids):  # TODO
                            filename = f"{machine_id}.json"

                            # Build upload directory
                            mission_upload_dir: str = get_mission_upload_dir(
                                organization_id=self.organization_id,
                                machine_id=self.machine_id,
                                mission_id=self.mission_id,
                                data_source=self.routed_machine_data_source,
                                date=current_date,
                                project_id=self.project_id,
                            )
                            topic = f"{mission_upload_dir}/{filename}"

                            message_body = json.dumps({})
                            buffer_size = len(message_body.encode("utf-8"))
                            try:
                                headers = {
                                    "message_type": "json",
                                    "topic": topic,
                                    "destination_ids": self.destination_ids,
                                    "data_source": self.routed_machine_data_source,
                                    # meta data
                                    "buffer_key": self.mission_id,
                                    "buffer_size": buffer_size,
                                    "data_type": "json",
                                }
                                self.rabbit_mq.enqueue_message(
                                    message=message_body,
                                    headers=headers,
                                    priority=self.priority,
                                )
                                self.logger.info(
                                    f"Data enqueued to {topic}, with priority: {self.priority}"
                                )

                            except Exception as e:
                                self.logger.error(
                                    f"Error routed_device_loop for topic {topic}: {e}"
                                )
                        self.routed_machine_ids = set()
                        self.logger.info(f"routed_device_loop success")
                    except Exception as e:
                        self.logger.error(f"routed_device_loop failed: {str(e)}")

                time.sleep(routed_machine_loop_delay)

        # Start monitoring in a daemon thread
        routed_device_loop_thread = threading.Thread(
            target=routed_device_loop,
            args=(self.routed_machine_loop_delay,),
            daemon=True,
        )

        routed_device_loop_thread.start()

    def _init_data_publisher_loop(self):
        """
        Start a background thread to monitor connection health
        Uses built-in AWS IoT SDK reconnection mechanisms
        """
        self.is_publishing = True

        def publisher_loop(publisher_loop_delay):
            while self.is_publishing:
                with self.data_object_lock:
                    try:
                        # convert all json array to csv and print the binary object, and make the self.data  = {}
                        for machine_id in self.data.keys():
                            for date in self.data[machine_id].keys():
                                for data_source in self.data[machine_id][date].keys():
                                    try:
                                        last_upload_time = self.data_upload_time[
                                            machine_id
                                        ][date][data_source]
                                    except Exception as e:
                                        last_upload_time = (
                                            int(time.time() * 1000)
                                            - self.auto_publish_intrl
                                        )
                                    curr_time = int(time.time() * 1000)

                                    json_array = self.data[machine_id][date][
                                        data_source
                                    ]

                                    if (
                                        curr_time - last_upload_time
                                        >= self.auto_publish_intrl
                                        and len(json_array)
                                    ):
                                        json_array = self.sort_json_array(
                                            json_array, "timestamp_epoch"
                                        )
                                        # Create CSV filename using first timestamp
                                        # filename = f"{str(json_array[0]['timestamp_epoch'])}.csv"
                                        filename = f"{str(json_array[0]['timestamp_epoch'])}_{str(json_array[len(json_array)-1]['timestamp_epoch'])}_{len(json_array)}.csv"

                                        # Build upload directory
                                        mission_upload_dir: str = (
                                            get_mission_upload_dir(
                                                organization_id=self.organization_id,
                                                machine_id=machine_id,
                                                mission_id=self.mission_id,
                                                data_source=data_source,
                                                date=date,
                                                project_id=self.project_id,
                                            )
                                        )

                                        topic = f"{mission_upload_dir}/{filename}"

                                        # Convert JSON array to CSV (binary)
                                        output = io.StringIO()

                                        # Collect all unique fieldnames from all records
                                        all_fieldnames = set()
                                        flat_records = []

                                        for record in json_array:
                                            # Flatten nested dicts if needed
                                            flat_record = record  # self.flatten_json(record) if hasattr(self, 'flatten_json') else record
                                            all_fieldnames.update(flat_record.keys())
                                            flat_records.append(flat_record)

                                        # Convert to sorted list for consistent column order
                                        sorted_fieldnames = sorted(all_fieldnames)

                                        # Create CSV writer with all fieldnames
                                        csv_writer = csv.DictWriter(
                                            output,
                                            fieldnames=sorted_fieldnames,
                                        )
                                        csv_writer.writeheader()

                                        # Write all records, ensuring each has all fields
                                        for flat_record in flat_records:
                                            # Create a new record with all fields, filling missing ones with empty string
                                            complete_record = {
                                                field: flat_record.get(field, "")
                                                for field in sorted_fieldnames
                                            }
                                            csv_writer.writerow(complete_record)

                                        csv_data = output.getvalue()
                                        output.close()
                                        # Convert to binary data for upload
                                        csv_binary_data = csv_data.encode("utf-8")

                                        try:
                                            headers = {
                                                "message_type": "binary",  # message_type = "json" if data_type == "json" else "binary"
                                                "topic": topic,  # TODO 1
                                                "destination_ids": self.destination_ids,
                                                "data_source": data_source,  # TODO 2
                                                # meta data
                                                "buffer_key": self.mission_id,
                                                "buffer_size": len(
                                                    csv_binary_data
                                                ),  # TODO 2
                                                "data_type": "csv",
                                            }
                                            self.rabbit_mq.enqueue_message(
                                                message=csv_binary_data,
                                                headers=headers,
                                                priority=self.priority,
                                            )
                                            self.logger.info(
                                                f"Data enqueued to {topic}, with priority: {self.priority}"
                                            )
                                            self.data[machine_id][date][
                                                data_source
                                            ] = []
                                            if machine_id not in self.data_upload_time:
                                                self.data_upload_time[machine_id] = {}
                                            if (
                                                date
                                                not in self.data_upload_time[machine_id]
                                            ):
                                                self.data_upload_time[machine_id][
                                                    date
                                                ] = {}
                                            self.data_upload_time[machine_id][date][
                                                data_source
                                            ] = int(time.time() * 1000)

                                        except Exception as e:
                                            self.logger.error(
                                                f"Error publisher_loop for topic {topic}: {e}"
                                            )
                        self.logger.info(f"All data published")
                    except Exception as e:
                        self.logger.error(f"publisher_loop failed: {str(e)}")

                time.sleep(publisher_loop_delay)

        # Start monitoring in a daemon thread
        publisher_loop_thread = threading.Thread(
            target=publisher_loop, args=(self.publisher_loop_delay,), daemon=True
        )

        publisher_loop_thread.start()

    def _publish_on_limit_hit(self, machine_id, date, data_source):
        json_array = self.data[machine_id][date][data_source]
        if len(json_array) >= self.max_array_len:  # TODO later we will do by size
            with self.data_object_lock:
                json_array = self.sort_json_array(
                    self.data[machine_id][date][data_source], "timestamp_epoch"
                )
                if len(json_array):  # as data might get publish when it was locked
                    # Create CSV filename using first timestamp
                    # filename = f"{str(json_array[0]['timestamp_epoch'])}.csv"
                    filename = f"{str(json_array[0]['timestamp_epoch'])}_{str(json_array[len(json_array)-1]['timestamp_epoch'])}_{len(json_array)}.csv"

                    # Build upload directory
                    mission_upload_dir: str = get_mission_upload_dir(
                        organization_id=self.organization_id,
                        machine_id=machine_id,
                        mission_id=self.mission_id,
                        data_source=data_source,
                        date=date,
                        project_id=self.project_id,
                    )

                    topic = f"{mission_upload_dir}/{filename}"

                    # Convert JSON array to CSV (binary)
                    output = io.StringIO()

                    # Collect all unique fieldnames from all records
                    all_fieldnames = set()
                    flat_records = []

                    for record in json_array:
                        # Flatten nested dicts if needed
                        flat_record = record  # self.flatten_json(record) if hasattr(self, 'flatten_json') else record
                        all_fieldnames.update(flat_record.keys())
                        flat_records.append(flat_record)

                    # Convert to sorted list for consistent column order
                    sorted_fieldnames = sorted(all_fieldnames)

                    # Create CSV writer with all fieldnames
                    csv_writer = csv.DictWriter(
                        output,
                        fieldnames=sorted_fieldnames,
                    )
                    csv_writer.writeheader()

                    # Write all records, ensuring each has all fields
                    for flat_record in flat_records:
                        # Create a new record with all fields, filling missing ones with empty string
                        complete_record = {
                            field: flat_record.get(field, "")
                            for field in sorted_fieldnames
                        }
                        csv_writer.writerow(complete_record)

                    csv_data = output.getvalue()
                    output.close()
                    # Convert to binary data for upload
                    csv_binary_data = csv_data.encode("utf-8")

                    try:
                        headers = {
                            "message_type": "binary",  # message_type = "json" if data_type == "json" else "binary"
                            "topic": topic,  # TODO 1
                            "destination_ids": self.destination_ids,
                            "data_source": data_source,  # TODO 2
                            # meta data
                            "buffer_key": self.mission_id,
                            "buffer_size": len(csv_binary_data),  # TODO 2
                            "data_type": "csv",
                        }
                        self.rabbit_mq.enqueue_message(
                            message=csv_binary_data,
                            headers=headers,
                            priority=self.priority,
                        )
                        self.logger.info(
                            f"Data enqueued to {topic}, with priority: {self.priority}"
                        )
                        self.data[machine_id][date][data_source] = []
                        if machine_id not in self.data_upload_time:
                            self.data_upload_time[machine_id] = {}
                        if date not in self.data_upload_time[machine_id]:
                            self.data_upload_time[machine_id][date] = {}
                        self.data_upload_time[machine_id][date][data_source] = int(
                            time.time() * 1000
                        )
                    except Exception as e:
                        self.logger.error(
                            f"Error in _publish_on_limit_hit for topic {topic}: {e}"
                        )

    def update_json_data(self, machine_id, data_source, json_data):
        """
        Update the data structure with new JSON data for a specific machine and data source.
        Data structure: data[machine_id][date][data_source] = [json_array]
        Uses machine timezone for date calculation.
        """
        # Extract date from timestamp_epoch in json_data
        timestamp_epoch = json_data.get("timestamp_epoch", int(time.time() * 1000))

        # Convert to datetime in UTC first, then convert to machine timezone
        dt_utc = datetime.fromtimestamp(timestamp_epoch / 1000, tz=timezone.utc)
        dt_local = dt_utc.astimezone(self.machine_timezone_info)
        date = dt_local.strftime("%Y-%m-%d")

        with self.data_object_lock:
            try:
                if machine_id not in self.data:
                    self.data[machine_id] = {}
                if date not in self.data[machine_id]:
                    self.data[machine_id][date] = {}
                if data_source not in self.data[machine_id][date]:
                    self.data[machine_id][date][data_source] = []

                # Append the json_data to the list
                self.data[machine_id][date][data_source].append(json_data)

                self.logger.debug(
                    f"Added data for machine_id: {machine_id}, date: {date}, data_source: {data_source}"
                )
            except Exception as e:
                self.logger.error(f"update_json_data failed: {str(e)}")
        if self.multi_machine:
            with self.routed_machine_lock:
                try:
                    self.routed_machine_ids.add(machine_id)
                except Exception as e:
                    self.logger.error(f"routed_machine_ids update failed: {str(e)}")

        self._publish_on_limit_hit(machine_id, date, data_source)

    # def _read_file(self, filepath: str) -> Tuple[bytes, str]:
    #     """
    #     Read file in chunks and calculate MD5.
    #     Returns: (file_data, MD5 hash)
    #     """
    #     try:
    #         with open(filepath, "rb") as file:
    #             file_data = file.read()
    #         file_md5 = hashlib.md5(file_data).hexdigest()
    #         return file_data, file_md5
    #     except Exception as e:
    #         self.logger.error("Error reading file-", {filepath})
    #         raise IOError(f"Error reading file {filepath}: {str(e)}")

    def flatten_json(self, obj, parent_key="", sep=None):
        """Recursively flatten a JSON object"""
        if sep is None:
            sep = self.key_seperator
        items = {}
        if isinstance(obj, dict):
            for k, v in obj.items():
                new_key = f"{parent_key}{sep}{k}" if parent_key else k
                items.update(self.flatten_json(v, new_key, sep=sep))
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                new_key = f"{parent_key}{sep}{i}" if parent_key else str(i)
                items.update(self.flatten_json(v, new_key, sep=sep))
            if len(obj) == 0 and parent_key:
                items[parent_key] = None
        else:
            items[parent_key] = None if obj is None else obj
        return items

    def _read_flatten_json(self, filepath: str, timestamp_epoch: int) -> Dict[str, Any]:
        """
        Return a flattened JSON dict with an added 'timestamp_epoch' field.
        """
        try:
            with open(filepath, "r") as file:
                json_data = json.load(file)
                file_data = self.flatten_json(json_data)
                file_data["timestamp_epoch"] = timestamp_epoch
            return file_data
        except Exception as e:
            self.logger.error("Error reading file-", {filepath})
            raise IOError(f"Error reading file {filepath}: {str(e)}")

    def consume_file(
        self,
        filepath: str,
        timestamp_epoch: int,
        data_source: str,
        file_dir: str,
        buffer_key: str,
        priority: int,
        destination_ids: Optional[List[Union[str, int]]] = None,
    ) -> None:
        try:
            # Assuming only json file path arrving
            # Validate filepath
            if not os.path.exists(filepath):
                raise FileNotFoundError(f"File not found: {filepath}")

            # Get file information
            filename, file_extension, data_type, file_size = get_file_info(filepath)
            file_data = self._read_flatten_json(filepath, timestamp_epoch)
            if self.multi_machine and self.machine_key:
                try:
                    machine_id = file_data[self.machine_key]
                    # TODO later we will remove this
                    if self.machine_id == 285 and len(str(machine_id)) <= 5:
                        machine_id = f"DHL-{machine_id}"
                    if self.machine_id == 291 and len(str(machine_id)) <= 5:
                        machine_id = f"ALG-{machine_id}"

                except Exception as e:
                    machine_id = self.machine_id
            else:
                machine_id = self.machine_id
            self.update_json_data(machine_id, data_source, file_data)

            # Send the entire file for small files
        except Exception as e:
            self.logger.error(f"Error in consume_file: {e}")
            raise

    def cleanup(self):
        """Clean up resources."""

        try:
            self.is_publishing = False
            self.rabbit_mq.close()
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

    def is_healthy(self):
        """
        Override health check to add additional service-specific checks.
        """
        return self.rabbit_mq.is_healthy()

    def __del__(self):
        """Destructor called by garbage collector to ensure resources are cleaned up, when object is about to be destroyed"""
        try:
            if self.is_healthy():
                self.logger.error(
                    "Destructor called by garbage collector to cleanup StreamFormatter"
                )
                self.cleanup()
        except Exception as e:
            pass


def main():
    writer = StreamFormatter()
    machine_config = Configs.get_machine_config()

    try:
        print(f"pushing all files")
        # Example usage with actual files
        # test_files = [
        #     ("/path/to/image.jpg", "camera1", "34556", 1),
        #     ("/path/to/video.mp4", "camera2", "34556", 2),
        #     ("/path/to/document.pdf", "event", "34556", 1),
        # ]

        test_files = [
            # ("/Users/amardeepsaini/Documents/VYOM/vyom-mqtt/mqtt_pub_sub/file/232561_small.mp4", "camera1", "34556", 2),
            # ("/Users/amardeepsaini/Documents/VYOM/vyom-mqtt/mqtt_pub_sub/file/elephant_istockphoto.jpg", "camera1", "34556", 1),
            # ("/Users/amardeepsaini/Documents/VYOM/vyom-mqtt/mqtt_pub_sub/file/elephant_maximus.jpg", "camera1", "34556", 1),
            # (
            #     "/Users/amardeepsaini/Documents/VYOM/vyom-mqtt/mqtt_pub_sub/file/Equine_Trot_400fps_Right.avi",
            #     "camera1",
            #     "34556",
            #     1,
            # ),
            (
                "/Users/amardeepsaini/Documents/VYOM/vyom-mqtt/mqtt_pub_sub/file/sample_20.mp4",
                "camera1",
                "34556",
                1,
            ),
            # (
            #     "/Users/amardeepsaini/Documents/VYOM/vyom-mqtt/mqtt_pub_sub/file/sample_70.mp4",
            #     "camera1",
            #     "34556",
            #     1,
            # ),
            # (
            #     "/Users/amardeepsaini/Documents/VYOM/vyom-mqtt/mqtt_pub_sub/file/sample_140.mp4",
            #     "camera1",
            #     "34556",
            #     1,
            # ),
        ]
        machine_id = machine_config.get("machine_id", "-") or "-"

        for file_path in test_files:
            try:
                writer.consume_file(
                    filepath=file_path,
                    timestamp_epoch=int(time.time() * 1000),
                    data_source=DUMMY_DATA_DT_SRC,
                    file_dir=f"1/{default_project_id}/2025-02-21/{machine_id}/23444/camera1/",
                    buffer_key=str(33444),
                    priority=2,
                    destination_ids=["s3"],
                )

            except FileNotFoundError as e:
                print(f"File not found: {file_path}", str(e))
            except Exception as e:
                print(f"Error processing file {file_path}: {e}")

    except Exception as e:
        print(f"Error in main execution: {e}")
    finally:
        writer.cleanup()


if __name__ == "__main__":
    main()
