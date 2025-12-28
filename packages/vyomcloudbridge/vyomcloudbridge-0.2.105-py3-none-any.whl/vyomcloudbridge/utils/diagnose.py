from datetime import datetime, timezone
import threading
import time
import os
from vyomcloudbridge.utils.logger_setup import setup_logger
from typing import Dict, Any, Optional, Union
from vyomcloudbridge.constants.constants import (
    DUMMY_DATA_DT_SRC,
    SPEED_TEST_DT_SRC,
    default_mission_id,
    main_data_queue,
)
from vyomcloudbridge.utils.configs import Configs
from vyomcloudbridge.services.rabbit_mq_utils import RabbitMQUtils
from vyomcloudbridge.services.queue_writer_json import QueueWriterJson
import requests
from urllib.parse import urlparse


class Diagnose:
    """
    A diagnostic service that performs speed tests by uploading data to queues
    and measuring upload performance. Uses RabbitMQ for queue management.
    """

    def __init__(self, show_log=False, log_level=None):
        """
        Initialize the diagnostic service with RabbitMQ connection and configuration.
        """
        self.logger = setup_logger(
            name=self.__class__.__module__ + "." + self.__class__.__name__,
            show_terminal=show_log,
            log_level=log_level,
        )
        self.priority_data = 1  # Priority for data messages
        self.priority_response = 2  # Priority for response messages

        self.machine_config = Configs.get_machine_config()
        self.machine_id = self.machine_config.get("machine_id", "-") or "-"
        self.organization_id = self.machine_config.get("organization_id", "-") or "-"
        self.rabbit_mq_utils = RabbitMQUtils()
        self.rabbit_mq_api_sync_delay = 5  # Seconds to wait for queue sync
        self.destination_ids = ["s3"]
        self.speed_test_thread = None
        self.speed_test_timeout = 10 * 60 * 1000  # milliseconds, 10 minutes max
        self.writer = QueueWriterJson(log_level=log_level)

        self.file_size = 1.054  # in MB
        self.data_source_testing = SPEED_TEST_DT_SRC
        self.data_size_test = 100

    def send_fail_message(self, data_source: str, filename: str, error_msg: str):
        """
        Send a failure message to the queue with error details.

        Args:
            data_source: Source identifier for the data
            filename: Name of the file being processed
            error_msg: Error message to include
        """
        data = {"data": None, "error": error_msg}
        self.writer.write_message(
            message_data=data,
            filename=filename,
            data_source=data_source,
            data_type="json",
            mission_id=default_mission_id,
            priority=self.priority_response,
            destination_ids=self.destination_ids,
            merge_chunks=True,
        )

    def send_success_message(
        self,
        data_source: str,
        filename: str,
        start_time: int,
        end_time: int,
        time_taken: int = None,
    ):
        """
        Send a success message to the queue with timing information.

        Args:
            data_source: Source identifier for the data
            filename: Name of the file being processed
            start_time: Start timestamp in epoch milliseconds
            end_time: End timestamp in epoch milliseconds
            time_taken: Time taken in milliseconds (optional, will be calculated if not provided)
        """
        if time_taken is None:
            time_taken = end_time - start_time

        data = {
            "data": {
                "start_time": start_time,
                "end_time": end_time,
                "time_taken": time_taken,
            },
            "error": None,
        }
        self.writer.write_message(
            message_data=data,
            filename=filename,
            data_source=data_source,
            data_type="json",
            mission_id=default_mission_id,
            priority=self.priority_response,
            destination_ids=self.destination_ids,
            merge_chunks=True,
        )

    def insert_data_to_queue(self, size: int):
        """
        Insert test data of specified size into the queue for speed testing.

        Args:
            size: Size of data to insert in MB (default: 100)
            data_source: Source identifier for the test data

        Returns:
            tuple: (actual_size_inserted_mb, error_message)
                - actual_size_inserted_mb: Actual size of data inserted in MB
                - error_message: None if successful, error string if failed
        """
        try:
            # Resolve local sample file path in constants directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            constants_dir = os.path.normpath(
                os.path.join(current_dir, "..", "constants")
            )
            sample_file_path = os.path.join(constants_dir, "sample_image.jpg")

            if not os.path.exists(sample_file_path):
                return (0, f"Sample file not found at {sample_file_path}")

            with open(sample_file_path, "rb") as f:
                file_data = f.read()

            # Determine file parameters
            file_size_mb_actual = len(file_data) / (1024 * 1024)
            file_extension = os.path.splitext(sample_file_path)[1].lstrip(".") or "bin"

            # Compute how many chunks to reach requested size
            effective_unit_size_mb = (
                file_size_mb_actual if file_size_mb_actual > 0 else self.file_size
            )
            loop_len = int(size / effective_unit_size_mb)
            if size % effective_unit_size_mb:
                loop_len = loop_len + 1

            padding_length = len(str(loop_len))
            epoch_ms = int(time.time() * 1000)

            self.logger.info(
                f"Using local sample file {sample_file_path} (~{file_size_mb_actual:.3f} MB) for speed test"
            )

            for i in range(loop_len):
                formatted_index = str(i + 1).zfill(padding_length)
                filename = f"{epoch_ms}_{formatted_index}.{file_extension}"
                self.writer.write_message(
                    message_data=file_data,
                    filename=filename,
                    data_source=DUMMY_DATA_DT_SRC,
                    data_type="binary",
                    mission_id=default_mission_id,
                    priority=self.priority_data,
                    destination_ids=self.destination_ids,
                    merge_chunks=True,
                    background=False,
                )

            return loop_len * effective_unit_size_mb, None
        except Exception as e:
            self.logger.error(f"Error writing test messages: {e}")
            return 0, f"Error writing test messages: {e}"

    def speed_test(
        self,
        id: Optional[Union[str, int]] = None,
        filename: Optional[str] = None,
        data_size: Optional[int] = None,
    ):
        """
        Perform the actual speed test by inserting data and measuring upload time.
        This method runs in a separate thread and measures how long it takes
        to upload a specified amount of data through the queue system.
        """
        try:
            epoch_ms = int(time.time() * 1000)
            if id is None:
                id = epoch_ms
            if filename is None:
                filename = f"{epoch_ms}.json"
            if data_size is None:
                data_size = self.data_size_test

            self.logger.info("Starting speed test...")

            # Check current queue status
            queue_info, error = self.rabbit_mq_utils.get_queue_info(main_data_queue)
            if error:
                self.logger.error(f"Error getting queue info: {error}")
                self.send_fail_message(
                    id=id,
                    data_source=self.data_source_testing,
                    filename=filename,
                    error_msg=f"Error in checking device current buffer: {error}",
                )
                return

            # Only proceed if queue is empty (or nearly empty)
            if queue_info.get("messages", 0) <= 1:
                # Insert test data
                data_enqueued, error = self.insert_data_to_queue(size=data_size)
                if error:
                    self.logger.error(f"Error inserting data to queue: {error}")
                    self.send_fail_message(
                        data_source=self.data_source_testing,
                        filename=filename,
                        error_msg=f"Error in inserting data to queue: {error}",
                    )
                    return

                # Start timing the upload process
                self.logger.info(
                    f"Inserted {data_enqueued} MB data to queue, waiting for upload..."
                )
                start_time_epoch_ms = int(time.time() * 1000)
                time.sleep(
                    self.rabbit_mq_api_sync_delay
                )  # Wait for all enqueued messages to reflect in data queue

                # Monitor queue until empty or timeout
                while True:
                    queue_info, error = self.rabbit_mq_utils.get_queue_info(
                        main_data_queue
                    )
                    if error:
                        self.logger.error(
                            f"Error getting queue info during speed test: {error}"
                        )
                        time.sleep(5)
                        continue

                    if queue_info.get("messages", 0) <= 1:  # Queue is empty
                        end_time_epoch_ms = int(time.time() * 1000)
                        time_taken = end_time_epoch_ms - start_time_epoch_ms
                        self.logger.info(
                            f"All data uploaded, time taken: {time_taken} ms"
                        )
                        self.send_success_message(
                            data_source=self.data_source_testing,
                            filename=filename,
                            start_time=start_time_epoch_ms,
                            end_time=end_time_epoch_ms,
                            time_taken=time_taken,
                        )
                        return

                    # Check for timeout
                    if (
                        int(time.time() * 1000) - start_time_epoch_ms
                        > self.speed_test_timeout
                    ):
                        self.logger.error(f"Data upload timed out after 10 minutes")
                        self.send_fail_message(
                            data_source=self.data_source_testing,
                            filename=filename,
                            error_msg=f"Data upload timed out after 10 minutes",
                        )
                        return

                    # Wait before checking again
                    time.sleep(5)
            else:
                self.logger.error(
                    f"Queue {main_data_queue} not empty, current messages: {queue_info.get('messages', 0)}"
                )
                self.send_fail_message(
                    data_source=self.data_source_testing,
                    filename=filename,
                    error_msg=f"Request failed, queue {main_data_queue} not empty, current messages: {queue_info.get('messages', 0)}",
                )
                return

        except Exception as e:
            self.logger.error(f"Error during speed test: {str(e)}")
            self.send_fail_message(
                data_source=self.data_source_testing,
                filename="983493444.json",
                error_msg=f"Error during speed test: {str(e)}",
            )

    def start_speed_test(
        self,
        data: Optional[Dict[str, Union[str, int]]] = None,
    ):
        """
        Start the speed test in a separate daemon thread.
        You may pass a single optional dictionary `data` containing keys
        `id`, `filename`, and `data_size` (string or int values). If not provided,
        new defaults are created every time.

        Backwards compatible: explicit `id`, `filename`, `data_size` args still work.
        """
        try:
            data = data or {}
            try:
                id = data.get("id", None)  # type: ignore[arg-type]
                filename = data.get("filename", None)  # type: ignore[arg-type]
                data_size = data.get("data_size", None)  # type: ignore[arg-type]
            except Exception as e:
                pass

            self.logger.info("Starting diagnostic speed test service...")
            epoch_ms = int(time.time() * 1000)
            if id is None:
                id = epoch_ms
            if filename is None:
                filename = f"{epoch_ms}.json"
            if data_size is None:
                data_size = self.data_size_test

            self.speed_test_thread = threading.Thread(
                target=self.speed_test, args=(id, filename, data_size), daemon=True
            )
            self.speed_test_thread.start()
            self.logger.info("Diagnostic speed test service started!")
        except Exception as e:
            self.logger.error(f"Error starting diagnostic service: {str(e)}")

    def cleanup(self):
        """
        Clean up resources, closing connections and threads.
        """
        if (
            hasattr(self, "speed_test_thread")
            and self.speed_test_thread
            and self.speed_test_thread.is_alive()
        ):
            try:
                self.speed_test_thread.join(timeout=5)
            except Exception as e:
                self.logger.error(f"Error joining speed_test_thread: {str(e)}")
        self.writer.cleanup()

    def __del__(self):
        """
        Destructor called by garbage collector to ensure resources are cleaned up
        when object is about to be destroyed.
        """
        try:
            self.cleanup()
        except Exception as e:
            pass  # Ignore cleanup errors in destructor


def main():
    """Example of how to use the Diagnose service for speed testing"""
    diagnose_service = Diagnose(show_log=True)
    epoch_ms = int(time.time() * 1000)
    id = epoch_ms
    filename = f"{epoch_ms}.json"
    data_size = 10
    print(f"Starting diagnostic speed test service example for {data_size} MB data")
    data = {
        "id": id,
        "filename": filename,
        "data_size": data_size,
    }
    try:
        # diagnose_service.start_speed_test()
        # OR
        diagnose_service.start_speed_test(data=data)
        # Keep the main thread alive while speed test runs
        time.sleep(20 * 60)  # Wait up to 20 minutes for test completion
    except KeyboardInterrupt:
        print("\nInterrupted by user, shutting down...")
    finally:
        print("Test Diagnosis finished")
        diagnose_service.cleanup()


if __name__ == "__main__":
    main()
