# vyomcloudbridge/dir_watcher.py
import json
import os
import sys
import time
from datetime import datetime, timezone
import threading
from pathlib import Path
import logging
from typing import Optional, Dict, Any, Union
from numbers import Number
import signal
from vyomcloudbridge.services.mission_stats import MissionStats
from vyomcloudbridge.services.queue_writer_file import QueueWriterFile
from vyomcloudbridge.utils.common import get_file_info, parse_bool
from vyomcloudbridge.utils.logger_setup import setup_logger
from vyomcloudbridge.utils.configs import Configs
from vyomcloudbridge.constants.constants import MAX_FILE_SIZE
from vyomcloudbridge.utils.common import (
    get_mission_upload_dir,
    get_data_upload_dir,
    default_dir_data_source,
)
from vyomcloudbridge.constants.constants import data_buffer_key
import traceback


class DirWatcher:
    REQUIRED_KEYS = {"mission_id", "message_type", "priority"}

    def __init__(
        self,
        mission_dir: bool,
        dir: str,
        dir_properties: Optional[
            Union[Dict, str]
        ] = None,  # Properties for the directory or path to a JSON file
        send_live: bool = False,
        merge_chunks: bool = False,
        priority: int = 1,
        preserve_file: bool = False,  # this we will implement, move it to <dir>_preserve
        log_level=None,
    ):
        """
        Initialize the DirWatcher with the specified watch directory.

        Args:
            watch_dir (str): Path to the directory to watch
        """
        # missing_keys = self.REQUIRED_KEYS - properties.keys()
        # if missing_keys:
        #     raise ValueError(f"Missing required keys in properties: {missing_keys}")

        try:
            self.log_level = log_level
            self.logger = setup_logger(
                name=self.__class__.__module__ + "." + self.__class__.__name__,
                show_terminal=False,
                log_level=log_level,
            )
            self.watch_dir = Path(dir)
            self.is_mission_dir: bool = parse_bool(mission_dir)
            self.send_live: bool = False
            if parse_bool(send_live):
                if self.is_mission_dir:
                    self.send_live = True
                else:
                    self.logger.info(
                        f"parameter --send-live is ignored, only cosidered in case of --mission-dir"
                    )
                    print(
                        f"parameter --send-live is ignored, only cosidered in case of --mission-dir"
                    )
            self.merge_chunks = merge_chunks
            self.priority = priority
            self.destination_ids = ["s3"]

            self.watching_live = True  # if a watcher is available to watch live data
            if dir_properties is None:
                self.properties = None
            elif isinstance(dir_properties, dict):
                self.properties = dir_properties
            elif isinstance(dir_properties, str):
                try:
                    with open(dir_properties, "r") as f:
                        self.properties = json.loads(f.read())
                except Exception as e:
                    error_msg = (
                        f"Error reading properties file {dir_properties}: {str(e)}"
                    )
                    self.logger.error(error_msg)
                    raise ValueError(error_msg)
            else:
                error_msg = f"Invalid dir_properties type: {type(dir_properties)}"
                self.logger.error(error_msg)
                raise TypeError(error_msg)
            self.watch_dir.mkdir(mode=0o755, exist_ok=True)
            self.processing_lock = threading.Lock()
            self.is_running = False

            self.max_retries = 3
            self.retry_delay = 5
            self.empty_dir_delay = 0.1
            self.queue_writer_client = None

            self.proccess_thread = None  # Thread for processing files
            self.failed_cleanup_thread = None  # Thread for cleaning files
            self.failed_cleanup_delay = (
                0  # (int): Time in seconds between cleanup runs. 0 means don't clean
            )

            self.file_status = {}  # Status of file being processed
            self.machine_config = Configs.get_machine_config()
            self.machine_id = self.machine_config.get("machine_id", "-") or "-"
            self.organization_id = (
                self.machine_config.get("organization_id", "-") or "-"
            )
            self.mission_stats = MissionStats()
            self._setup_signal_handlers()  # for graceful shutdown
            self.logger.info(f"Queue directory initialized at: {self.watch_dir}")

        except Exception as e:
            self.logger.error(f"Error initializing queue manager: {str(e)}")
            raise

    # def _mission_upload_dir(self, message: Dict[str, Any]) -> str: # TODO PATH
    #     """
    #     Returns:
    #         str: Upload dir for mission related data
    #     """
    #     return (
    #         f"{self.machine_config['organization_id']}/{message['project_id']}/{message['date']}/"
    #         f"{message['data_source']}/{self.machine_config['machine_id']}/{message['mission_id']}"
    #     )

    # def _data_upload_dir(self, filepath: Path) -> str: # TODO PATH
    #     """
    #     Returns:
    #         str: Upload dir for non-mission related data
    #     """
    #     now = datetime.now(timezone.utc)
    #     date = now.strftime("%Y-%m-%d")

    #     rel_path = filepath.relative_to(self.watch_dir)
    #     rel_path_str = str(rel_path)
    #     rel_path_dir = str(Path(rel_path_str).parent)
    #     if rel_path_dir == ".":
    #         rel_path_dir = ""
    #     elif rel_path_dir:
    #         rel_path_dir = "/" + rel_path_dir
    #     return f"{self.machine_config['organization_id']}/_uploads_/{self.machine_config['machine_id']}{rel_path_dir}"

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""

        def signal_handler(sig, frame):
            self.logger.info(f"Received signal {sig}, shutting down DirWatcher...")
            self.stop()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def _get_next_file(self) -> Optional[Path]:
        """
        Get the next file to process from the watch directory, including nested subdirectories.

        Returns:
            Optional[Path]: Path to the next file or None if no files are available
        """
        try:
            for root, _, files in os.walk(
                self.watch_dir
            ):  # Walk through all subdirectories
                root_path = Path(root)
                for filename in sorted(files):
                    try:
                        filepath = root_path / filename
                        if not filepath.is_file():
                            continue
                        rel_path = filepath.relative_to(self.watch_dir)
                        rel_path_str = str(rel_path)

                        if (
                            not self.file_status.get(rel_path_str, {}).get("status")
                            == "processing"
                        ):
                            return filepath
                    except Exception as e:
                        self.logger.error(
                            f"Error checking file status for {filepath}: {str(e)}"
                        )
                        continue
            return None
        except Exception as e:
            self.logger.error(f"Error getting next message: {str(e)}")
            return None

    def _update_message_status(self, filepath: Path, status: str) -> None:
        """
        Update the status of a message file

        Args:
            filepath (Path): Path to the file
            status (str): New status to set
        """
        if isinstance(self.file_status.get(filepath.name), dict):
            self.file_status[filepath.name]["status"] = status
        else:
            created_at = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            self.file_status[filepath.name] = {
                "status": status,
                "attempts": 0,
                "last_error": None,
                "created_at": created_at,
            }
        self.logger.debug(f"Updated status for {filepath.name} to {status}")

    def _proccess_file(
        self, queue_writer_client: QueueWriterFile, filepath: Path, destination_ids
    ) -> bool:
        """
        Process a single file from the watch directory.

        Args:
            queue_writer_client: The client used to process the message
            filepath (Path): Path to the file to be processed

        Returns:
            bool: True if processing was successful, False otherwise
        """
        # Get relative path for logging and status tracking
        rel_path = filepath.relative_to(self.watch_dir)
        rel_path_str = str(rel_path)
        path_parts = rel_path_str.split("/")
        self.logger.info(f"Starting to process file: {rel_path_str}")

        try:
            self._update_message_status(filepath, "processing")
            if self.is_mission_dir:
                if len(path_parts) == 5:  # fixed defined file path
                    date = path_parts[0]
                    project_id = path_parts[1]
                    mission_id = path_parts[2]
                    data_source = path_parts[3]
                    # mission_upload_dir = self._mission_upload_dir(properties)  # TODO PATH
                    mission_upload_dir: str = get_mission_upload_dir(
                        organization_id=self.organization_id,
                        machine_id=self.machine_id,
                        mission_id=mission_id,
                        data_source=data_source,
                        date=date,
                        project_id=project_id,
                    )
                    filename, file_extension, data_type, file_size = get_file_info(
                        str(filepath)
                    )
                    file_dir = mission_upload_dir
                    chunk_dir = mission_upload_dir + f"/chunk"
                    queue_writer_client.write_from_file(
                        str(filepath),
                        properties=None,
                        data_source=data_source,
                        file_dir=file_dir,
                        chunk_dir=chunk_dir,
                        merge_chunks=self.merge_chunks,
                        buffer_key=str(mission_id),
                        priority=self.priority,
                        destination_ids=destination_ids,
                        send_live=self.watching_live and self.send_live,
                    )
                    # collect mission related data listing
                    self.mission_stats.on_mission_data_arrive(
                        mission_id=mission_id,
                        size=file_size,
                        file_count=1,
                        data_type=data_type,
                        data_source=data_source,
                        s3_dir=file_dir,
                    )

                else:
                    self.logger.warning(f"Invalid path of file: {rel_path_str}")
            else:
                if len(path_parts) <= 3:
                    filename, file_extension, data_type, file_size = get_file_info(
                        str(filepath)
                    )
                    # data_upload_dir = self._data_upload_dir(filepath) # TODO PATH
                    rel_filepath = filepath.relative_to(self.watch_dir)
                    rel_filepath = str(rel_filepath)
                    rel_path_dir = str(Path(rel_filepath).parent)
                    data_upload_dir: str = get_data_upload_dir(
                        organization_id=self.machine_config["organization_id"],
                        machine_id=self.machine_config["machine_id"],
                        rel_path_dir=rel_path_dir,
                    )
                    file_dir: str = data_upload_dir
                    chunk_dir: str = data_upload_dir + f"/chunk"
                    queue_writer_client.write_from_file(
                        str(filepath),
                        properties=self.properties,
                        data_source=default_dir_data_source,
                        file_dir=file_dir,
                        chunk_dir=chunk_dir,
                        merge_chunks=self.merge_chunks,
                        buffer_key=data_buffer_key,
                        priority=self.priority,
                        destination_ids=destination_ids,
                        send_live=self.watching_live and self.send_live,
                    )
                else:
                    self.logger.warning(
                        f"Max 2 nested directory are supported, error in file: {rel_path_str}"
                    )

            filepath.unlink()
            self.logger.info(f"Successfully deleted file: {rel_path_str}")

            self._update_message_status(filepath, "completed")
            return True

        except Exception as e:
            self.logger.error(
                f"Error processing file {rel_path_str}: {str(e)}", exc_info=True
            )

            current_status = self.file_status.get(rel_path_str, {})
            attempts = current_status.get("attempts", 0) + 1

            self.file_status[rel_path_str] = {
                "status": "pending",
                "attempts": attempts,
                "last_error": str(e),
                "created_at": current_status.get(
                    "created_at", datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                ),
            }

            if attempts >= self.max_retries:
                self.file_status[rel_path_str]["status"] = "failed"
                self.logger.error(
                    f"Max retries reached for file {rel_path_str}. Marking as failed."
                )
                return False

            self.logger.error(
                f"Error processing file {rel_path_str} (Attempt {attempts}/{self.max_retries}): {str(e)}"
            )
            return False

    def start_proccessing(self, queue_writer_client: QueueWriterFile, destination_ids):
        """
        Start processing files in the watch directory.

        Args:
            queue_writer_client: Client for processing messages
        """
        self.logger.info("Starting the file processing loop")
        while self.is_running:
            with self.processing_lock:
                filepath = self._get_next_file()
                if filepath:
                    success = self._proccess_file(
                        queue_writer_client, filepath, destination_ids
                    )

                    if not success:
                        time.sleep(self.retry_delay)
                else:
                    time.sleep(self.empty_dir_delay)

    def cleanup_failed_messages(self, age_hours: int = 24):
        """
        Clean up failed messages older than specified hours.

        Args:
            age_hours (int): Age in hours after which to delete failed messages
        """
        self.logger.info(
            f"Starting cleanup of failed messages older than {age_hours} hours"
        )
        current_time = datetime.now()

        for filepath in self.watch_dir.glob("*.json"):
            try:
                file_status = self.file_status.get(filepath.name, {})
                if file_status.get("status") == "failed":
                    created_at = datetime.strptime(
                        file_status.get(
                            "created_at", current_time.strftime("%Y%m%d_%H%M%S_%f")
                        ),
                        "%Y%m%d_%H%M%S_%f",
                    )
                    age = current_time - created_at
                    if age.total_seconds() > age_hours * 3600:
                        filepath.unlink()
                        self.logger.info(
                            f"Cleaned up old failed message: {filepath.name}"
                        )
            except Exception as e:
                self.logger.error(f"Error cleaning up message {filepath}: {str(e)}")

    def start(self):
        """
        Initialize the IoT client and start processing threads.
        """
        self.logger.info("Starting DirWatcher service")
        try:
            try:
                self.logger.info("Initializing QueueWriterFile client...")
                self.queue_writer_client = QueueWriterFile(log_level=self.log_level)
                self.is_running = True
                self.logger.info("QueueWriterFile client initialized successfully")
            except Exception as e:
                self.logger.error(
                    f"Error in initializing IoT client: {str(e)}", exc_info=True
                )
                raise

            try:
                self.logger.info("File processing thread starting...")
                self.proccess_thread = threading.Thread(
                    target=self.start_proccessing,
                    args=(self.queue_writer_client, self.destination_ids),
                )
                # self.proccess_thread.daemon = True
                self.proccess_thread.start()
                self.logger.info("File processing thread started successfully")
            except Exception as e:
                self.logger.error(
                    f"Error in starting processing thread: {str(e)}", exc_info=True
                )
                raise

            if self.failed_cleanup_delay != 0:  # 0 cleanup_time means, don't clean
                try:

                    def cleanup_task():
                        while self.is_running:
                            self.cleanup_failed_messages()
                            time.sleep(self.failed_cleanup_delay)

                    self.failed_cleanup_thread = threading.Thread(target=cleanup_task)
                    self.failed_cleanup_thread.daemon = True
                    self.failed_cleanup_thread.start()
                except Exception as e:
                    self.logger.error(
                        f"Error in starting cleanup thread: {str(e)}", exc_info=True
                    )
                    raise

            self.logger.info("DirWatcher service started successfully")
        except Exception as e:
            self.logger.error(f"Error initializing service: {str(e)}", exc_info=True)
            raise

    def stop(self):
        """Cleanup function to stop all threads and disconnect client"""
        self.logger.info("Shutting down MQTT Queue service...")
        self.is_running = False

        if self.proccess_thread and self.proccess_thread.is_alive():
            self.logger.info("Stopping the file processing thread")
            self.is_running = False
            self.proccess_thread.join(timeout=5)
            self.logger.info("Processing thread stopped successfully")

        if self.failed_cleanup_thread and self.failed_cleanup_thread.is_alive():
            self.logger.info("Stopping the failed_file cleanup thread")
            self.is_running = False
            self.failed_cleanup_thread.join(timeout=5)
            self.logger.info("failed_file cleanup thread stopped successfully")

        if self.queue_writer_client:
            try:
                self.queue_writer_client.cleanup()
                self.logger.info("queue_writer_client cleaned up successfully")
            except Exception as e:
                self.logger.error(
                    f"Error cleaning queue_writer_client: {str(e)}", exc_info=True
                )
        if self.mission_stats:
            try:
                self.mission_stats.stop()
                self.logger.info("mission_stats cleaned up successfully")
            except Exception as e:
                self.logger.error(
                    f"Error cleaning mission_stats: {str(e)}", exc_info=True
                )

        self.logger.info("Service shutdown completed")

    def is_healthy(self):
        """
        Check if the service is healthy.

        Returns:
            bool: True if the service is running and RabbitMQ connection is healthy
        """
        return (
            self.is_running
            and self.queue_writer_client
            and self.queue_writer_client.is_healthy()
            and self.mission_stats.is_healthy()
        )

    def __del__(self):
        """Destructor called by garbage collector to ensure resources are cleaned up, when object is about to be destroyed"""
        try:
            self.logger.error(
                "Destructor called by garbage collector to cleanup DirWatcher"
            )
            self.stop()
        except Exception as e:
            pass


def main():
    mission_dir = "/Users/amardeepsaini/Documents/VYOM/vyom-cloud-bridge/vyomcloudbridge/_extra_capture"
    mission_dir = "/home/admin/Documents/mission_data"
    properties = {}
    dir_watcher = DirWatcher(True, mission_dir, properties)
    try:
        # for mission_dir, the should be in nested dir, /date/project_id/mission_id/data_source/
        dir_watcher.start()

        # Keep the main thread running
        while dir_watcher.is_running:
            try:
                time.sleep(10)  # Sleep to prevent high CPU usage
            except KeyboardInterrupt:
                print("\nInterrupted by user, shutting down...")
                break
    except Exception as e:
        print(f"Error in main thread: {str(e)}")
        traceback.print_exc()
    finally:
        print("Cleaning up resources")
        dir_watcher.stop()


if __name__ == "__main__":
    main()
