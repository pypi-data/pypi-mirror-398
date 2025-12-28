import abc
from datetime import datetime, timezone
import signal
import sys
import logging
import time
from typing import Dict, Any, List, Tuple, Union
from vyomcloudbridge.constants.constants import SERVICE_ID
from vyomcloudbridge.utils.logger_setup import setup_logger
from vyomcloudbridge.constants.constants import (
    default_project_id,
    default_dir_data_source,
)
from pathlib import Path
import random
import string

DATA_TYPE_MAPPING = {
    # Images
    "jpg": "image",
    "jpeg": "image",
    "png": "image",
    "gif": "image",
    "bmp": "image",
    # Videos
    "mp4": "video",
    "avi": "video",
    "mov": "video",
    "wmv": "video",
    "flv": "video",
    # Documents
    "txt": "file",
    "pdf": "file",
    "doc": "file",
    "docx": "file",
    # Data files
    "json": "json",
    "csv": "file",
    "xml": "file",
    # Default
    "": "file",
}


class ServiceAbstract(abc.ABC):
    """
    Abstract base class for services that can be started, stopped, and monitored.
    All service implementations should inherit from this class.
    """

    def __init__(self, multi_thread: bool = False, log_level=None):
        self.is_running = False
        self.multi_thread = multi_thread
        self.logger = setup_logger(
            name=self.__class__.__module__ + "." + self.__class__.__name__,
            show_terminal=False,
            log_level=log_level,
        )
        self._setup_signal_handlers()

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""

        def signal_handler(sig, frame):
            self.logger.info(
                f"Received signal {sig}, shutting down {self.__class__.__name__}..."
            )
            self.stop()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    @abc.abstractmethod
    def start(self):
        """
        Start the service. Must be implemented by subclasses.
        This method should set is_running to True when the service is successfully started.
        """
        pass

    @abc.abstractmethod
    def stop(self):
        """
        Stop the service. Must be implemented by subclasses.
        This method should set is_running to False when the service is successfully stopped.
        """
        pass

    @abc.abstractmethod
    def cleanup(self):
        """
        Cleanup the open resources/connections. Must be implemented by subclasses.
        """
        pass

    def is_healthy(self):
        """
        Check if the service is healthy. Can be overridden by subclasses.
        """
        return self.is_running


def parse_bool(value):
    """Convert string representation of boolean to actual boolean."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "t", "yes", "y", "1")
    return bool(value)


def get_file_info(filepath: str) -> Tuple[str, str, str, int]:
    """
    Extract file information from filepath.
    Returns: (filename without extension, extension, detected data type, file size in bytes)
    """
    path = Path(filepath)
    filename = path.stem
    extension = path.suffix.lower().lstrip(".")

    # Get file size in bytes
    file_size = path.stat().st_size

    # Use mimetypes to help detect file type
    # mime_type, _ = mimetypes.guess_type(filepath)

    # Determine data type based on extension
    data_type = DATA_TYPE_MAPPING.get(extension, "file")

    return filename, extension, data_type, file_size


def get_service_id(service_name: str) -> str:
    """
    Get the service ID for a given service name.
    Returns '***_**' if the service name is not found.

    Args:
        service_name: The name of the service

    Returns:
        The service ID or '***_**' if not found
    """
    return SERVICE_ID.get(service_name, "***_**")


def generate_unique_id(length=10, chars=None):
    """Generate random unique ID for various models"""
    if chars is None:
        chars = string.digits
        # chars = string.ascii_lowercase + string.digits
    return "".join(random.choice(chars) for _ in range(length))


def get_mission_upload_dir(
    organization_id,
    machine_id,
    mission_id: Union[int, str],
    data_source,
    date=None,
    project_id=None,
) -> str:
    """
    Returns:
        str: Upload dir for mission related data
    """
    now = datetime.now(timezone.utc)
    default_date = now.strftime("%Y-%m-%d")

    date = date or default_date
    project_id = project_id or default_project_id
    return (
        f"{organization_id}/{project_id}/{date}/{machine_id}/{mission_id}/{data_source}"
    )


def get_data_upload_dir(organization_id, machine_id, rel_path_dir: str = "") -> str:
    """
    Returns:
        str: Upload dir for non-mission related data
    """
    now = datetime.now(timezone.utc)
    date = now.strftime("%Y-%m-%d")  # Not in use

    rel_path_dir = rel_path_dir.strip()

    if rel_path_dir in ["", ".", "./"]:
        rel_path_dir = ""
    else:
        # Remove leading ./, slashes, etc.
        while rel_path_dir.startswith((".", "/")):
            rel_path_dir = rel_path_dir[1:]

        # Remove trailing slash if any
        rel_path_dir = rel_path_dir.rstrip("/")

        # Add leading slash
        rel_path_dir = "/" + rel_path_dir

    return f"{organization_id}/{default_dir_data_source}/{machine_id}{rel_path_dir}"
