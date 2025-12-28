# vyomcloudbridge/dir_watcher.py
import json
import os
from platform import machine
import sys
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import threading
from pathlib import Path
import logging
from typing import Optional, Dict, Any, Union
from numbers import Number
from vyomcloudbridge.utils.common import get_file_info
import signal
from vyomcloudbridge.services.mission_stats import MissionStats
from vyomcloudbridge.services.stream_formatter import StreamFormatter
from vyomcloudbridge.utils.common import get_file_info, parse_bool
from vyomcloudbridge.utils.logger_setup import setup_logger
from vyomcloudbridge.utils.configs import Configs
from vyomcloudbridge.constants.constants import MAX_FILE_SIZE, DEFAULT_TIMEZONE
from vyomcloudbridge.utils.common import (
    get_mission_upload_dir,
    get_data_upload_dir,
    default_dir_data_source,
)
from vyomcloudbridge.constants.constants import data_buffer_key
import traceback


class StreamConsumer:
    def __init__(
        self,
        stream_dir: str,
        multi_machine: bool = False,  # True
        machine_key: Optional[str] = "agentId",  # None
        # low priority
        priority: int = 1,
        preserve_file: bool = False,  # this we will implement later, move it to <dir>_preserve
        log_level=None,
    ):
        """
        Initialize the StreamConsumer with the specified watch directory.

        Args:
            watch_dir (str): Path to the directory to watch
        """

        try:
            self.log_level = log_level
            self.logger = setup_logger(
                name=self.__class__.__module__ + "." + self.__class__.__name__,
                show_terminal=False,
                log_level=log_level,
            )

            self.watch_dir = Path(stream_dir)
            self.multi_machine: bool = parse_bool(multi_machine)
            self.machine_key: str = machine_key

            self.preserve_file: bool = parse_bool(preserve_file)
            self.destination_ids = ["s3"]
            self.priority = priority

            self.project_id = "_all_"
            self.mission_id = "_all_"

            self.watch_dir.mkdir(mode=0o755, exist_ok=True)
            self.processing_lock = threading.Lock()
            self.is_running = False

            self.max_retries = 3
            self.retry_delay = 5
            self.empty_dir_delay = 0.1
            self.stream_formatter_client = None

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
            self.machine_timezone = (
                self.machine_config.get("timezone", DEFAULT_TIMEZONE)
                or DEFAULT_TIMEZONE
            )
            self.machine_timezone_info = self._get_timezone_info()
            self.mission_stats = MissionStats()
            self._setup_signal_handlers()  # for graceful shutdown

            self.MIN_SECONDS = 946684800  # January 1, 2000 in seconds
            self.MIN_MILLISECONDS = 946684800000  # January 1, 2000 in milliseconds
            self.MIN_MICROSECONDS = 946684800000000  # January 1, 2000 in microseconds

            self.logger.info(f"Queue directory initialized at: {self.watch_dir}")

        except Exception as e:
            self.logger.error(f"Error initializing StreamConsumer: {str(e)}")
            raise

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""

        def signal_handler(sig, frame):
            self.logger.info(f"Received signal {sig}, shutting down StreamConsumer...")
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

    def _is_valid_filetime(self, filename: str) -> bool:
        """Check if filename (without extension) is a valid millisecond or microsecond epoch timestamp."""
        try:
            # Remove file extension if present
            name_without_ext = filename.split(".")[0]

            # Convert to integer
            timestamp = int(name_without_ext)

            # Current time + 1 minute buffer
            now_millis = int(time.time() * 1000) + 60_000
            now_micros = int(time.time() * 1_000_000) + 60_000_000

            # Validate range
            return (self.MIN_MILLISECONDS <= timestamp <= now_millis) or (
                self.MIN_MICROSECONDS <= timestamp <= now_micros
            )

        except (ValueError, IndexError):
            return False

    def get_file_date(self, filename: str) -> str:
        """
        Extract date from filename containing epoch timestamp.
        Automatically detects seconds, milliseconds, or microseconds.
        Uses machine timezone for date calculation.
        """
        try:
            # Remove file extension if present
            name_without_ext = filename.rsplit(".", 1)[0]
            timestamp = int(name_without_ext)

            if timestamp >= self.MIN_MICROSECONDS:
                timestamp_seconds = timestamp / 1000000
            elif timestamp >= self.MIN_MILLISECONDS:
                timestamp_seconds = timestamp / 1000
            elif timestamp >= self.MIN_SECONDS:
                timestamp_seconds = timestamp

            # Convert to datetime in UTC first, then convert to machine timezone
            dt_utc = datetime.fromtimestamp(timestamp_seconds, tz=timezone.utc)
            dt_local = dt_utc.astimezone(self.machine_timezone_info)
            return dt_local.strftime("%Y-%m-%d")
        except (ValueError, IndexError, OSError, OverflowError) as e:
            self.logger.error(f"Invalid date of file {filename} error: {str(e)}")
            return "YYYY-MM-DD"

    def get_timestamp_mili(self, filename: str) -> int:
        """
        Extract date from filename containing epoch timestamp.
        Automatically detects seconds, milliseconds, or microseconds.
        """
        try:
            # Remove file extension if present
            name_without_ext = filename.rsplit(".", 1)[0]
            timestamp = int(name_without_ext)

            if timestamp >= self.MIN_MICROSECONDS:
                timestamp_mili = int(timestamp / 1000)
            elif timestamp >= self.MIN_MILLISECONDS:
                timestamp_mili = timestamp
            elif timestamp >= self.MIN_SECONDS:
                timestamp_mili = int(timestamp * 1000)

            return timestamp_mili
        except (ValueError, IndexError, OSError, OverflowError) as e:
            self.logger.error(
                f"error in get_timestamp_mili for file {filename} error: {str(e)}"
            )
            # return current milisecond
            return int(time.time() * 1000)

    def _proccess_file(
        self, stream_formatter_client: StreamFormatter, filepath: Path, destination_ids
    ) -> bool:
        """
        Process a single file from the watch directory.

        Args:
            stream_formatter_client: The client used to process the message
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
            filename, file_extension, data_type, file_size = get_file_info(
                str(filepath)
            )
            if file_extension != "json":
                self.logger.error(
                    f"File format [{file_extension}] not suppoeted for {str(filepath)}"
                )
            elif not self._is_valid_filetime(filename):
                self.logger.error(
                    f"Invalid filename [{filename}], required epoch mili/mircrosecond"
                )
            elif (
                len(path_parts) == 2
            ):  # /dir_to_watch/<data_source>/<epoch_time_ms>.<ext>
                data_source = path_parts[0]
                file_date = self.get_file_date(filename)
                mission_upload_dir: str = get_mission_upload_dir(
                    organization_id=self.organization_id,
                    machine_id=self.machine_id,
                    mission_id=self.mission_id,
                    data_source=data_source,
                    date=file_date,
                    project_id=self.project_id,
                )
                stream_formatter_client.consume_file(
                    str(filepath),  # json
                    timestamp_epoch=self.get_timestamp_mili(filename),
                    data_source=data_source,
                    file_dir=mission_upload_dir,
                    buffer_key=str(self.mission_id),
                    priority=self.priority,
                    destination_ids=destination_ids,
                )

                # collect mission related data listing
                self.mission_stats.on_mission_data_arrive(
                    mission_id=self.mission_id,
                    size=file_size,
                    file_count=1,
                    data_type=data_type,
                    data_source=data_source,
                    s3_dir=mission_upload_dir,
                )
            else:
                self.logger.error(
                    f"Invalid path of file: {rel_path_str}, expected /dir_to_watch/<data_source>/<epoch_time_ms>.<ext>"
                )
                # TODO move it to come other directory

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

    def start_proccessing(self, stream_formatter_client: StreamFormatter, destination_ids):
        """
        Start processing files in the watch directory.

        Args:
            stream_formatter_client: Client for processing messages
        """
        self.logger.info("Starting file processing loop...")
        while self.is_running:
            with self.processing_lock:
                filepath = self._get_next_file()
                if filepath:
                    success = self._proccess_file(
                        stream_formatter_client, filepath, destination_ids
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
        self.logger.info("Starting StreamConsumer service")
        try:
            try:
                self.logger.info("Initializing StreamFormatter client...")
                self.stream_formatter_client = StreamFormatter(
                    multi_machine=self.multi_machine,
                    machine_key=self.machine_key,
                    log_level=self.log_level,
                )
                self.is_running = True
                self.logger.info("StreamFormatter client initialized successfully")
            except Exception as e:
                self.logger.error(
                    f"Error in initializing IoT client: {str(e)}", exc_info=True
                )
                raise

            try:
                self.logger.info("Starting file processing thread...")
                self.proccess_thread = threading.Thread(
                    target=self.start_proccessing,
                    args=(self.stream_formatter_client, self.destination_ids),
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

            self.logger.info("StreamConsumer service started successfully")
        except Exception as e:
            self.logger.error(f"Error initializing service: {str(e)}", exc_info=True)
            raise

    def stop(self):
        """Cleanup function to stop all threads and disconnect client"""
        self.logger.info("Shutting down StreamConsumer service...")
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

        if self.stream_formatter_client:
            try:
                self.stream_formatter_client.cleanup()
                self.logger.info("stream_formatter_client cleaned up successfully")
            except Exception as e:
                self.logger.error(
                    f"Error cleaning stream_formatter_client: {str(e)}", exc_info=True
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
            and self.stream_formatter_client
            and self.stream_formatter_client.is_healthy()
            and self.mission_stats.is_healthy()
        )

    def __del__(self):
        """Destructor called by garbage collector to ensure resources are cleaned up, when object is about to be destroyed"""
        try:
            self.logger.error(
                "Destructor called by garbage collector to cleanup StreamConsumer"
            )
            self.stop()
        except Exception as e:
            pass


def main():
    dir_to_watch = (
        "/Users/amardeepsaini/Documents/VYOM/vyom-cloud-bridge/extra/stream_dir"
    )
    dir_watcher = StreamConsumer(
        stream_dir=dir_to_watch, multi_machine=True, machine_key="agentId"
    )
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
