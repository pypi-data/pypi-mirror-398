import pika
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple, Union
import threading
import time

import requests
from vyomcloudbridge.services.machine_stats import MachineStats
from vyomcloudbridge.services.rabbit_queue.queue_main import RabbitMQ
from vyomcloudbridge.utils.common import ServiceAbstract
from vyomcloudbridge.constants.constants import (
    sample_mission_telemetry,
    sample_mission_summary,
    DEFAULT_RABBITMQ_URL,
    MISSION_STATS_DT_SRC,
)
from vyomcloudbridge.utils.configs import Configs
from vyomcloudbridge.utils.common import get_mission_upload_dir
from vyomcloudbridge.constants.constants import (
    default_upload_dir,
    default_project_id,
    default_mission_id,
    data_buffer_key,
    mission_buffer_key,
)


class MissionStats(ServiceAbstract):
    """
    A service that maintains mission data statistics using RabbitMQ as a persistent store.
    Each mission_id has its own queue in RabbitMQ that stores the latest state of its data.
    Also maintains current mission and current user data in dedicated queues.
    """

    def __init__(self, log_level=None):
        """
        Initialize the mission data service with RabbitMQ connection.

        Args:
            rabbitmq_url: Connection URL for RabbitMQ
            logger: Optional logger instance
        """
        super().__init__(log_level=log_level)
        self.host: str = "localhost"
        self.rabbitmq_url = DEFAULT_RABBITMQ_URL
        self.mission_stats_publish_interval = 30
        self.mission_stats_empty_delay = 60
        self.mission_stats_live_priority = 2

        self.mission_data_publish_interval = 2
        self.mission_data_empty_delay = 20
        self.mission_live_priority = 3

        self.publish_error_delay = 60

        self.rmq_conn = None
        self.rmq_channel = None
        self.rabbit_mq = RabbitMQ(log_level=log_level)
        self.machine_config = Configs.get_machine_config()
        self.machine_id = self.machine_config.get("machine_id", "-") or "-"
        self.organization_id = self.machine_config.get("organization_id", "-") or "-"
        self.data_source_stats = MISSION_STATS_DT_SRC

        self.machine_stats = MachineStats(log_level=log_level)
        # Thread attributes
        self.data_listing_thread = None
        self.mission_thread = None

    def generate_mission_id(self):
        try:
            epoch_ms = int(time.time() * 1000)
            mission_id = f"{epoch_ms}{self.machine_id}"
            return int(mission_id)
        except Exception as e:
            self.logger.error(f"Failed to generate unique mission_id: {str(e)}")
            raise

    def _setup_connection(self):
        """Set up RabbitMQ connection and declare the exchange for mission data."""
        try:
            # Establish connection
            self.rmq_conn = pika.BlockingConnection(
                pika.URLParameters(self.rabbitmq_url)
            )
            # self.rmq_conn = pika.BlockingConnection(
            #     pika.ConnectionParameters(
            #         host=self.host,
            #         heartbeat=600,
            #         blocked_connection_timeout=300,
            #         socket_timeout=300,
            #     )
            # )
            self.rmq_channel = self.rmq_conn.channel()
            self.rmq_channel.exchange_declare(
                exchange="mission_uploaded_exchange",
                exchange_type="direct",
                durable=True,
            )
            self.rmq_channel.queue_declare(queue="last_data_mission_id", durable=True)

            # Declare queues for current mission and current user
            self.rmq_channel.queue_declare(queue="current_mission", durable=True)
            self.rmq_channel.queue_declare(queue="current_user", durable=True)

            self.logger.debug("RabbitMQ connection established successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize RabbitMQ: {str(e)}")
            raise

    def _ensure_connection(self) -> bool:
        """Ensure connection and channel are active and working"""
        try:
            if not self.rmq_conn or self.rmq_conn.is_closed:
                self._setup_connection()
                return True

            if not self.rmq_channel or self.rmq_channel.is_closed:
                self.logger.info("Closed channel found, re-establishing...")
                self.rmq_channel = self.rmq_conn.channel()
                self.rmq_channel.exchange_declare(
                    exchange="mission_uploaded_exchange",
                    exchange_type="direct",
                    durable=True,
                )
                self.rmq_channel.queue_declare(
                    queue="last_data_mission_id", durable=True
                )
                self.rmq_channel.queue_declare(queue="current_mission", durable=True)
                self.rmq_channel.queue_declare(queue="current_user", durable=True)
                self.logger.info("Channel re-established successfully")

            return True
        except Exception as e:
            self.logger.error(f"Failed to ensure connection: {e}")
            self.rmq_conn = None
            self.rmq_channel = None
            return False

    def _set_last_data_mission(self, mission_id: Union[str, int]):
        """
        Store the last data mission ID in RabbitMQ.

        Args:
            mission_id: The ID of the mission to set as last data
        """
        try:
            if not self._ensure_connection() or not self.rmq_channel:
                raise Exception("Could not establish connection")

            # Clear the queue first (get all messages)
            while True:
                method_frame, _, _ = self.rmq_channel.basic_get(
                    queue="last_data_mission_id", auto_ack=True
                )
                if not method_frame:
                    break

            # Add the new mission_id (convert to string for storage)
            if isinstance(mission_id, int):
                mission_id = str(mission_id)
            self.rmq_channel.basic_publish(
                exchange="",
                routing_key="last_data_mission_id",
                body=mission_id,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # make message persistent
                ),
            )
            self.logger.info(f"Set last data mission to {mission_id}")
        except Exception as e:
            self.logger.error(f"Error setting last data mission: {str(e)}")

    def _get_last_data_mission_id(self) -> Optional[str]:
        """
        Get the last data mission ID from RabbitMQ and clear it from the queue.

        Returns:
            The mission ID string or None if not found
        """
        try:
            if not self._ensure_connection() or not self.rmq_channel:
                raise Exception("Could not establish connection")

            # Get the message but don't acknowledge it initially
            method_frame, _, body = self.rmq_channel.basic_get(
                queue="last_data_mission_id", auto_ack=False
            )

            mission_id = None
            if method_frame:
                mission_id = body.decode("utf-8")
                self.rmq_channel.basic_ack(delivery_tag=method_frame.delivery_tag)
                self.logger.info(
                    f"Retrieved and cleared last data mission: {mission_id}"
                )
            return mission_id
        except Exception as e:
            self.logger.warning(f"Warning getting last data mission: {str(e)}")
            return None

    def _ensure_mission_stats_queue(self, mission_id: Union[int, str]):
        """
        Ensure that a queue exists for the given mission_id.

        Args:
            mission_id: The ID of the mission to create a queue for
        """
        if not self._ensure_connection() or not self.rmq_channel:
            raise Exception("Could not establish connection")

        if isinstance(mission_id, int):
            mission_id = str(mission_id)

        queue_name = f"mission_stats_{mission_id}"
        self.rmq_channel.queue_declare(queue=queue_name, durable=True)
        self.rmq_channel.queue_bind(
            exchange="mission_uploaded_exchange",
            queue=queue_name,
            routing_key=mission_id,
        )

    def _get_mission_stats_from_rabbitmq(
        self, mission_id: Union[int, str]
    ) -> Dict[str, Any]:
        """
        Retrieve mission data from RabbitMQ.

        Args:
            mission_id: The ID of the mission

        Returns:
            List of data type statistics entries or empty list if no data exists
        """
        queue_name = f"mission_stats_{mission_id}"

        try:
            if not self._ensure_connection() or not self.rmq_channel:
                raise Exception("Could not establish connection")

            # Declare queue (will not do anything if it already exists)
            self._ensure_mission_stats_queue(mission_id)

            # Get the message (if any)
            method_frame, header_frame, body = self.rmq_channel.basic_get(
                queue=queue_name, auto_ack=False
            )

            if isinstance(mission_id, str):
                mission_id = int(mission_id)

            if method_frame:
                # Message exists, parse it
                mission_stats_body = json.loads(body)

                # Put message back into the queue (we're just reading)
                self.rmq_channel.basic_nack(
                    delivery_tag=method_frame.delivery_tag, requeue=True
                )

                return mission_stats_body
            else:
                # No message in queue
                return {
                    "mission_id": mission_id,
                    "file_count": 0,
                    "data_size": 0,
                    "file_count_uploaded": 0,
                    "data_size_uploaded": 0,
                    "updated_at": None,
                }

        except Exception as e:
            self.logger.error(
                f"Error retrieving mission data for {mission_id}: {str(e)}"
            )
            return {
                "mission_id": mission_id,
                "file_count": 0,
                "data_size": 0,
                "file_count_uploaded": 0,
                "data_size_uploaded": 0,
                "updated_at": None,
            }

    def _update_stats_in_rabbitmq(
        self,
        mission_id: int,
        new_mission_stats: Union[Dict[str, Any], List[Dict[str, Any]]],
    ):
        """
        Update mission data in RabbitMQ.

        Args:
            mission_id: The ID of the mission
            new_mission_stats: Updated list of data type statistics
        """
        queue_name = f"mission_stats_{mission_id}"

        try:
            if not self._ensure_connection() or not self.rmq_channel:
                raise Exception("Could not establish connection")

            if isinstance(mission_id, int):
                mission_id = str(mission_id)

            # Ensure queue exists
            self._ensure_mission_stats_queue(mission_id)

            # Get the current message (if any)
            method_frame, header_frame, body = self.rmq_channel.basic_get(
                queue=queue_name, auto_ack=True
            )

            # Publish new message with updated data
            self.rmq_channel.basic_publish(
                exchange="mission_uploaded_exchange",
                routing_key=mission_id,
                body=json.dumps(new_mission_stats),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # make message persistent
                    content_type="application/json",
                ),
            )

            self.logger.info(f"Updated mission data for {mission_id} in RabbitMQ")

        except Exception as e:
            self.logger.error(f"Error updating mission data for {mission_id}: {str(e)}")

    def delete_current_mission(self, mission_id: Union[str, int]):  # Note in use
        """
        Delete the current mission from RabbitMQ queue only if it matches the provided mission_id.

        Args:
            mission_id: The ID of the mission to delete
        """
        try:
            if not self._ensure_connection() or not self.rmq_channel:
                raise Exception("Could not establish connection")

            if isinstance(mission_id, int):
                mission_id = str(mission_id)

            method_frame, _, body = self.rmq_channel.basic_get(
                queue="current_mission", auto_ack=False
            )

            if method_frame:
                current_mission = json.loads(body.decode("utf-8"))
                current_mission_id = current_mission.get("id")

                if str(current_mission_id) == mission_id:
                    self.rmq_channel.basic_ack(delivery_tag=method_frame.delivery_tag)

                    while True:
                        method_frame, _, _ = self.rmq_channel.basic_get(
                            queue="current_mission", auto_ack=True
                        )
                        if not method_frame:
                            break

                    self.logger.info(f"Deleted current mission with ID: {mission_id}")
                else:
                    self.rmq_channel.basic_nack(
                        delivery_tag=method_frame.delivery_tag, requeue=True
                    )
                    self.logger.info(
                        f"Current mission ID {current_mission_id} doesn't match {mission_id}, not deleting"
                    )
        except Exception as e:
            self.logger.error(f"Error deleting current mission: {str(e)}")

    def update_current_mission(  # for interenal use only, will be depreciated in future
        self,
        id,
        name,
        description,
        creator_id,
        owner_id,
        mission_status,
        campaign_id,
        mission_date,
        start_time,
        end_time,
    ):
        """
        Update the current mission details in RabbitMQ.

        Args:
            mission_detail: Dictionary containing mission details
        """
        try:
            mission_detail = {
                "id": id,
                "name": name,
                "description": description,
                "creator_id": creator_id,
                "owner_id": owner_id,
                "mission_status": mission_status,
                "campaign_id": campaign_id,
                "mission_date": mission_date,
                "start_time": start_time,
                "end_time": end_time,
                "mission_type": "",
                "machine_id": self.machine_id,
                "json_data": {},
            }

            if not self._ensure_connection() or not self.rmq_channel:
                raise Exception("Could not establish connection")

            while True:
                method_frame, _, _ = self.rmq_channel.basic_get(
                    queue="current_mission", auto_ack=True
                )
                if not method_frame:
                    break

            self.rmq_channel.basic_publish(
                exchange="",
                routing_key="current_mission",
                body=json.dumps(mission_detail),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # make message persistent
                    content_type="application/json",
                ),
            )

            # Publish mission data in real time
            now = datetime.now(timezone.utc)
            date = now.strftime("%Y-%m-%d")
            filename = int(time.time() * 1000)
            mission_upload_dir: str = get_mission_upload_dir(
                organization_id=self.organization_id,
                machine_id=self.machine_id,
                mission_id=id,
                data_source=self.data_source_stats,
                date=date,
                project_id=default_project_id,
            )

            message_body = json.dumps({"mission": mission_detail, "data_stats": None})
            headers = {
                "topic": f"{mission_upload_dir}/{filename}.json",
                "message_type": "json",
                "destination_ids": ["s3"],
                "data_source": self.data_source_stats,
                # meta data
                "buffer_key": str(id),
                "buffer_size": 0,
                "data_type": "json",
            }
            self.rabbit_mq.enqueue_message(
                message=message_body,
                headers=headers,
                priority=self.mission_live_priority,
            )

            self.logger.info(
                f"Updated current mission to {mission_detail.get('id', 'unknown')}"
            )
        except Exception as e:
            self.logger.error(f"Error updating current mission: {str(e)}")

    def get_current_mission(self) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Retrieve the current mission details from RabbitMQ.

        Returns:
            Tuple:
                - dict or None: Current mission details if available, else None
                - str or None: Error message if any issue occurs, else None
        """
        try:
            if not self._ensure_connection() or not self.rmq_channel:
                error_message = "Could not establish connection"
                self.logger.error(error_message)
                return None, error_message

            method_frame, _, body = self.rmq_channel.basic_get(
                queue=self.current_mission_queue, auto_ack=False
            )

            mission_detail = None
            if method_frame:
                mission_detail = json.loads(body.decode("utf-8"))
                self.rmq_channel.basic_nack(
                    delivery_tag=method_frame.delivery_tag, requeue=True
                )
                self.logger.info(
                    f"Retrieved current mission: {mission_detail.get('id', 'unknown')}"
                )
            return mission_detail, None
        except Exception as e:
            error_message = f"Error getting current mission: {str(e)}"
            self.logger.error(error_message)
            return None, error_message

    def start_mission(
        self,
        id=None,  # Unique mission_id from Vyom services if available
        name=None,  # Human-readable name for the mission
        description=None,  # Description about the mission
        creator_id=None,  # User ID of the person initiating the mission
        owner_id=None,  # If someone else is the mission owner, provide their user ID
        project_id: Union[str, int] = None,  # Project ID if available
        mission_date: str = None,
        start_time: str = None,
    ):
        """
        Start a new mission and publish its details to RabbitMQ for VyomIQ.

        Args:
            id (integer, optional): Unique mission ID. Auto-generated if not provided.
            name (str, optional): Name of the mission. Defaults to timestamp-based string.
            description (str, optional): Description of the mission.
            creator_id (int, optional): ID of the user creating the mission. Defaults to 1.
            owner_id (int, optional): ID of the mission owner. Defaults to creator_id.

        Returns:
            Tuple:
                - dict or None: Mission details if mission is successfully started, else None
                - str or None: Error message if any issue occurs, else None
        """
        existing_mission, mission_read_error = self.get_current_mission()
        if mission_read_error is not None:
            self.logger.error(
                f"Error in checking existing mission -{mission_read_error}"
            )
            return None, mission_read_error

        if existing_mission is not None:
            if existing_mission.get("mission_status") == 1:
                existing_mission_id = existing_mission.get("id")
                error_message = f"Mission with id={existing_mission_id} is already in progress, please complete it OR mark complete before starting new mission"
                self.logger.error(error_message)
                return None, error_message
            else:
                pass  # Existing mission already completed, so start new one
        try:
            project_id = int(project_id)
        except Exception as e:
            project_id = None
            pass

        if id is None:
            id = self.generate_mission_id()

        if name is None:
            name = f"M_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f')[:-3]}_UTC"

        if mission_date is None:
            mission_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        try:
            if creator_id is None:
                creator_id = 1
            if owner_id is None:
                owner_id = creator_id

            mission_detail = {
                "id": id,
                "name": name,
                "description": description,
                "creator_id": creator_id,
                "owner_id": owner_id,
                "mission_status": 1,
                "campaign_id": project_id,  # campaign ID if available, else None
                "mission_date": mission_date,
                "start_time": start_time or datetime.now(timezone.utc).isoformat(),
                "end_time": None,
                "mission_type": "",
                "machine_id": self.machine_id,
                "json_data": {},
            }

            if not self._ensure_connection() or not self.rmq_channel:
                error_message = "Could not establish connections, please try again"
                return None, error_message

            while True:
                method_frame, _, _ = self.rmq_channel.basic_get(
                    queue="current_mission", auto_ack=True
                )
                if not method_frame:
                    break

            self.rmq_channel.basic_publish(
                exchange="",
                routing_key="current_mission",
                body=json.dumps(mission_detail),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # make message persistent
                    content_type="application/json",
                ),
            )
            self.logger.info(
                f"Updated current mission to {mission_detail.get('id', 'unknown')}"
            )

            # Publish mission data in real time
            now = datetime.now(timezone.utc)
            date = now.strftime("%Y-%m-%d")
            filename = int(time.time() * 1000)
            mission_upload_dir: str = get_mission_upload_dir(
                organization_id=self.organization_id,
                machine_id=self.machine_id,
                mission_id=id,
                data_source=self.data_source_stats,
                date=date,
                project_id=default_project_id,
            )

            message_body = json.dumps({"mission": mission_detail, "data_stats": None})
            headers = {
                "topic": f"{mission_upload_dir}/{filename}.json",
                "message_type": "json",
                "destination_ids": ["s3"],
                "data_source": self.data_source_stats,
                # meta data
                "buffer_key": str(id),
                "buffer_size": 0,
                "data_type": "json",
            }
            self.rabbit_mq.enqueue_message(
                message=message_body,
                headers=headers,
                priority=self.mission_live_priority,
            )

            return mission_detail, None
        except Exception as e:
            error_message = f"Error updating current mission: {str(e)}"
            self.logger.error(error_message)
            return None, error_message

    def end_current_mission(self):
        """
        Mark the current mission as completed and update RabbitMQ.

        Returns:
            Tuple:
                - success (bool): success, True if mission successfully marked as completed or no active mission found; False if error
                - error_message (str): error message if there is any error, else None in case of success
        """
        try:
            mission_detail, mission_read_error = self.get_current_mission()
            if mission_read_error is not None:
                return False, mission_read_error
            if mission_detail is not None:
                if mission_detail.get("mission_status") == 1:
                    existing_mission_id = mission_detail.get("id")
                    mission_detail["mission_status"] = 2
                    if not self._ensure_connection() or not self.rmq_channel:
                        error_message = "Could not establish connection"
                        return False, error_message

                    while True:
                        method_frame, _, _ = self.rmq_channel.basic_get(
                            queue="current_mission", auto_ack=True
                        )
                        if not method_frame:
                            break

                    self.rmq_channel.basic_publish(
                        exchange="",
                        routing_key="current_mission",
                        body=json.dumps(mission_detail),
                        properties=pika.BasicProperties(
                            delivery_mode=2,  # make message persistent
                            content_type="application/json",
                        ),
                    )

                    # Publish mission data in real time
                    now = datetime.now(timezone.utc)
                    date = now.strftime("%Y-%m-%d")
                    filename = int(time.time() * 1000)
                    mission_upload_dir: str = get_mission_upload_dir(
                        organization_id=self.organization_id,
                        machine_id=self.machine_id,
                        mission_id=existing_mission_id,
                        data_source=self.data_source_stats,
                        date=date,
                        project_id=default_project_id,
                    )

                    message_body = json.dumps(
                        {"mission": mission_detail, "data_stats": None}
                    )
                    headers = {
                        "topic": f"{mission_upload_dir}/{filename}.json",
                        "message_type": "json",
                        "destination_ids": ["s3"],
                        "data_source": self.data_source_stats,
                        # meta data
                        "buffer_key": str(existing_mission_id),
                        "buffer_size": 0,
                        "data_type": "json",
                    }
                    self.rabbit_mq.enqueue_message(
                        message=message_body,
                        headers=headers,
                        priority=self.mission_live_priority,
                    )

                    self.logger.info(
                        f"Current mission with id={existing_mission_id}, marked completed"
                    )
                    return True, None
                else:
                    self.logger.info(f"No active mission found to mark completed")
                    return True, None
            else:
                self.logger.info(f"No active mission found to mark completed")
                return True, None
        except Exception as e:
            error_message = f"Error updating current mission: {str(e)}"
            self.logger.error(error_message)
            return False, error_message

    # def publish_mission_telemetry(self, mission_id: int, mission_telemetry: Any): # NOT IN USE
    #     """
    #     Update the current mission_telemetry in RabbitMQ.

    #     Args:
    #         mission_id: The ID of the mission
    #         mission_telemetry: json containing mission_telemetry
    #     """
    #     try:
    #         self.logger.info(f"self.machine_id-{self.machine_id}")
    #         now = datetime.now(timezone.utc)
    #         date = now.strftime("%Y-%m-%d")
    #         filename = int(time.time() * 1000)
    #         # mission_upload_dir = f"{self.machine_config['organization_id']}/{date}/{default_project_id}/{self.data_source_stats}/{self.machine_id}/{mission_id}" # TODO
    #         mission_upload_dir: str = get_mission_upload_dir(
    #             organization_id=self.organization_id,
    #             machine_id=self.machine_id,
    #             mission_id=mission_id,
    #             data_source=self.data_source_stats,
    #             date=date,
    #             project_id={default_project_id},
    #         )

    #         message_body = json.dumps({"mission_telemetry": mission_telemetry})
    #         headers = {
    #             "topic": f"{mission_upload_dir}/{filename}.json",
    #             "message_type": "json",
    #             "destination_ids": ["s3"],
    #             "data_source": self.data_source_stats,
    #             # meta data
    #             "buffer_key": str(mission_id),
    #             "buffer_size": 0,  # TODO
    #             "data_type": "json",
    #         }
    #         self.rabbit_mq.enqueue_message(
    #             message=message_body, headers=headers, priority=1
    #         )

    #         self.logger.info(f"Updated mission_telemetry to mission_id: {mission_id}")
    #     except Exception as e:
    #         self.logger.error(f"Error updating mission_telemetry: {str(e)}")

    def publish_mission_summary(self, mission_id: int, mission_summary: Any):
        """
        Update the current mission_summary in RabbitMQ.

        Args:
            mission_id: The ID of the mission
            mission_summary: Dictionary containing mission_summary
        """
        try:
            now = datetime.now(timezone.utc)
            date = now.strftime("%Y-%m-%d")
            filename = int(time.time() * 1000)
            # mission_upload_dir = f"{self.machine_config['organization_id']}/{date}/{default_project_id}/{self.data_source_stats}/{self.machine_id}/{mission_id}" # TODO
            mission_upload_dir: str = get_mission_upload_dir(
                organization_id=self.organization_id,
                machine_id=self.machine_id,
                mission_id=mission_id,
                data_source=self.data_source_stats,
                date=date,
                project_id=default_project_id,
            )

            message_body = json.dumps({"mission_summary": mission_summary})
            headers = {
                "topic": f"{mission_upload_dir}/{filename}.json",
                "message_type": "json",
                "destination_ids": ["s3"],
                "data_source": self.data_source_stats,
                # meta data
                "buffer_key": str(mission_id),
                "buffer_size": 0,  # TODO
                "data_type": "json",
            }
            self.rabbit_mq.enqueue_message(
                message=message_body, headers=headers, priority=1
            )

            self.logger.info(f"Updated mission_summary to mission_id: {mission_id}")
        except Exception as e:
            self.logger.error(f"Error updating mission_summary: {str(e)}")

    def on_mission_data_arrive(
        self,
        mission_id: Union[int, str],
        size: int,
        file_count: int = 1,
        data_type: Optional[str] = None,  # Not in use
        data_source: Optional[str] = None,  # Not in use
        s3_dir: Optional[str] = None,  # Not in use
    ):
        """
        Args:
            mission_id: The ID of the mission
            data_type: Type of data (Video, Log, etc.)
            size: Size of the file in bytes
            s3_dir: S3 directory path where the file is stored
        """
        try:
            if not mission_id:
                self.logger.warning("Cannot add mission data: mission_id is empty")
                return
            if not self._ensure_connection() or not self.rmq_channel:
                self.logger.error("Could not establish connection")
                return

            if isinstance(mission_id, str):
                if mission_id != data_buffer_key and not mission_id.isdigit():
                    raise Exception(
                        "Invalid mission_id provided, it should be an integer or '_all_'"
                    )

                if mission_id == data_buffer_key:
                    self.machine_stats.on_data_arrive(size)
                    return
                else:
                    mission_id = int(mission_id)

            self.machine_stats.on_data_arrive(size)
            # new_mission_stats = self._get_mission_stats_from_rabbitmq(mission_id)

            # Update mission stats
            # updated_at = datetime.now(timezone.utc).isoformat()
            # try:
            #     new_mission_stats["file_count"] += int(file_count)
            #     new_mission_stats["data_size"] += int(size)
            #     new_mission_stats["updated_at"] = updated_at
            # except Exception as e:
            #     # Backword compatibility
            #     new_mission_stats = {
            #         "mission_id": mission_id,
            #         "file_count": 0,
            #         "data_size": 0,
            #         "file_count_uploaded": 0,
            #         "data_size_uploaded": 0,
            #         "updated_at": None,
            #     }
            #     new_mission_stats["file_count"] += int(file_count)
            #     new_mission_stats["data_size"] += int(size)
            #     new_mission_stats["updated_at"] = updated_at

            # # Check last data mission
            # last_data_mission_id = self._get_last_data_mission_id()
            # if last_data_mission_id and last_data_mission_id != str(mission_id):
            #     self._publish_stats_to_hq(last_data_mission_id)
            # self._set_last_data_mission(mission_id)
            # self._update_stats_in_rabbitmq(mission_id, new_mission_stats)

            # self.logger.info(
            #     f"Updated mission data for mission_id: {mission_id}, data_type: {data_type}, data_source: {data_source}"
            # )
        except Exception as e:
            self.logger.error(f"Error in on_mission_data_arrive: {str(e)}")

    def on_mission_data_publish(
        self,
        mission_id: Union[int, str],
        size: int,
        file_count: int = 1,
        data_type: Optional[str] = None,  # Not in use
        data_source: Optional[str] = None,  # Not in use
    ):
        """
        Update mission data statistics for a specific mission.

        Args:
            mission_id: The ID of the mission
            data_type: Type of data (Video, Log, etc.)
            # data_format: Format of the data (mp4, log, etc.)
            size: Size of the file in bytes
        """
        if not mission_id:
            self.logger.warning("Cannot add mission data: mission_id is empty")
            return
        if not self._ensure_connection() or not self.rmq_channel:
            raise Exception("Could not establish connection")

        if isinstance(mission_id, str):
            if mission_id != data_buffer_key and not mission_id.isdigit():
                raise Exception(
                    "Invalid mission_id provided, it should be an integer or '_all_'"
                )

            if mission_id == data_buffer_key:
                self.machine_stats.on_data_publish(size)
                return
            else:
                mission_id = int(mission_id)

        self.machine_stats.on_data_publish(size)
        new_mission_stats = self._get_mission_stats_from_rabbitmq(mission_id)

        new_mission_stats["file_count_uploaded"] += int(file_count)
        new_mission_stats["data_size_uploaded"] += int(size)
        new_mission_stats["updated_at"] = datetime.now(timezone.utc).isoformat()

        # If not found, new_mission created
        last_data_mission_id = self._get_last_data_mission_id()
        if last_data_mission_id and last_data_mission_id != mission_id:
            self._publish_stats_to_hq(last_data_mission_id)
        self._set_last_data_mission(mission_id)
        self._update_stats_in_rabbitmq(mission_id, new_mission_stats)

        self.logger.info(
            f"mission data updated for mission_id: {mission_id}, data_type: {data_type}, data_source: {data_source}"
        )

    def _publish_stats_to_hq(self, mission_id: Union[int, str]):  # PUBLISHER FUNCTION 1
        try:
            # Get the mission data for mission_id
            self.logger.info(
                f"publishing {self.data_source_stats}... for mission_id: {mission_id}"
            )
            if isinstance(mission_id, int):
                mission_id = str(mission_id)

            mission_data_stats = self._get_mission_stats_from_rabbitmq(mission_id)
            if not mission_data_stats:
                self.logger.warning(
                    f"No data found for mission {mission_id} to publish"
                )
                return False

            now = datetime.now(timezone.utc)
            date = now.strftime("%Y-%m-%d")
            filename = int(time.time() * 1000)
            # mission_upload_dir = f"{self.machine_config['organization_id']}/{date}/{default_project_id}/{self.data_source_stats}/{self.machine_id}/{mission_id}" # TODO
            mission_upload_dir: str = get_mission_upload_dir(
                organization_id=self.organization_id,
                machine_id=self.machine_id,
                mission_id=mission_id,
                data_source=self.data_source_stats,
                date=date,
                project_id=default_project_id,
            )

            message_body = json.dumps(
                {"mission": None, "data_stats": mission_data_stats}
            )
            headers = {
                "topic": f"{mission_upload_dir}/{filename}.json",
                "message_type": "json",
                "destination_ids": ["s3"],
                "data_source": self.data_source_stats,
                # meta data
                "buffer_key": mission_id,
                "buffer_size": 0,
                "data_type": "json",
            }
            self.rabbit_mq.enqueue_message(
                message=message_body,
                headers=headers,
                priority=self.mission_stats_live_priority,
            )

            self.logger.info(
                f"Successfully published data_listing for mission {mission_id}"
            )
            return True

        except Exception as e:
            self.logger.error(
                f"Error publishing mission data_listing for {mission_id}: {str(e)}"
            )
            return False

    # def _publish_mission_to_hq(  # NOT in use
    #     self, current_mission: Dict[str, Any]
    # ):  # CURRENTLY NOT in use
    #     try:
    #         # Get the mission data for mission_id
    #         mission_id = current_mission.get("id")
    #         now = datetime.now(timezone.utc)
    #         date = now.strftime("%Y-%m-%d")
    #         filename = int(time.time() * 1000)
    #         # mission_upload_dir = f"{self.machine_config['organization_id']}/{date}/{default_project_id}/{self.data_source_stats}/{self.machine_id}/{mission_id}" # TODO
    #         mission_upload_dir: str = get_mission_upload_dir(
    #             organization_id=self.organization_id,
    #             machine_id=self.machine_id,
    #             mission_id=mission_id,
    #             data_source=self.data_source_stats,
    #             date=current_mission.get("mission_date", date),
    #             project_id=current_mission.get("campaign_id", default_project_id),
    #         )

    #         message_body = json.dumps({"mission": current_mission, "data_list": None})
    #         headers = {
    #             "topic": f"{mission_upload_dir}/{filename}.json",
    #             "message_type": "json",
    #             "destination_ids": ["s3"],
    #             "data_source": self.data_source_stats,
    #             # meta data
    #             "buffer_key": str(mission_id),
    #             "buffer_size": 0,
    #             "data_type": "json",
    #         }
    #         self.rabbit_mq.enqueue_message(
    #             message=message_body, headers=headers, priority=self.mission_live_priority
    #         )

    #         # TODO Later
    #         # self.delete_current_mission(mission_id)
    #         self.logger.info(
    #             f"Successfully published data for current mission {mission_id}"
    #         )
    #         return True
    #     except Exception as e:
    #         self.logger.error(
    #             f"Error publishing mission data for {mission_id}: {str(e)}"
    #         )

    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """
        Get the current user details from RabbitMQ.

        Returns:
            Current user details as a dictionary or None if not found
        """
        try:
            if not self._ensure_connection() or not self.rmq_channel:
                raise Exception("Could not establish connection")

            method_frame, _, body = self.rmq_channel.basic_get(
                queue="current_user", auto_ack=False
            )

            user_detail = None
            if method_frame:
                user_detail = json.loads(body.decode("utf-8"))
                self.rmq_channel.basic_nack(
                    delivery_tag=method_frame.delivery_tag, requeue=True
                )
                self.logger.info(
                    f"Retrieved current user: {user_detail.get('id', 'unknown')}"
                )
            return user_detail
        except Exception as e:
            self.logger.error(f"Error getting current user: {str(e)}")
            return None

    def delete_current_user(self):
        """
        Delete the current user from RabbitMQ queue.
        """
        try:
            if not self._ensure_connection() or not self.rmq_channel:
                raise Exception("Could not establish connection")

            while True:
                method_frame, _, _ = self.rmq_channel.basic_get(
                    queue="current_user", auto_ack=True
                )
                if not method_frame:
                    break

            self.logger.info("Deleted current mission")
        except Exception as e:
            self.logger.error(f"Error deleting current mission: {str(e)}")

    def set_current_user(self, user_detail: Dict[str, Any]):
        """
        Update the current user details in RabbitMQ.

        Args:
            user_detail: Dictionary containing user details
        """
        try:
            if not self._ensure_connection() or not self.rmq_channel:
                raise Exception("Could not establish connection")

            self.delete_current_user()

            self.rmq_channel.basic_publish(
                exchange="",
                routing_key="current_user",
                body=json.dumps(user_detail),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # make message persistent
                    content_type="application/json",
                ),
            )
            self.logger.info(
                f"Updated current user to {user_detail.get('id', 'unknown')}"
            )
        except Exception as e:
            self.logger.error(f"Error updating current user: {str(e)}")

    def start(self):
        try:
            self.logger.info("Starting MssionStats publisher...")
            self.is_running = True

            # Define the two loop functions
            def stats_publisher_loop():
                while self.is_running:
                    try:
                        last_data_mission_id = self._get_last_data_mission_id()
                        if last_data_mission_id:
                            self.logger.info(
                                f"Action mission FOUND, {last_data_mission_id}"
                            )
                            self._publish_stats_to_hq(last_data_mission_id)
                            time.sleep(self.mission_stats_publish_interval)
                        else:
                            time.sleep(self.mission_stats_empty_delay)
                    except Exception as e:
                        self.logger.error(f"Error in stats publisher loop: {str(e)}")
                        time.sleep(self.publish_error_delay)

            # def mission_publisher_loop():
            #     while self.is_running:
            #         try:
            #             current_mission, mission_read_error = self.get_current_mission()
            #             if mission_read_error is not None:
            #                 self.logger.error(
            #                     f"Error reading current mission: {mission_read_error}"
            #                 )
            #                 time.sleep(self.publish_error_delay)
            #                 continue

            #             if current_mission:
            #                 current_mission_id = current_mission.get("id", None)
            #                 self.logger.info(
            #                     f"current mission FOUND current_mission_id-, {current_mission_id}"
            #                 )
            #                 self._publish_mission_to_hq(current_mission)
            #                 time.sleep(self.mission_data_publish_interval)
            #             else:
            #                 self.logger.info(f"not current mission FOUND")
            #                 time.sleep(self.mission_data_empty_delay)
            #         except Exception as e:
            #             self.logger.error(f"Error in mission publisher loop: {str(e)}")
            #             time.sleep(self.publish_error_delay)

            # Create and start the threads
            self.data_listing_thread = threading.Thread(
                target=stats_publisher_loop, daemon=True
            )
            # self.mission_thread = threading.Thread(
            #     target=mission_publisher_loop, daemon=True
            # )

            self.data_listing_thread.start()
            # self.mission_thread.start()  # TODO
            self.logger.info("MssionStats publisher started!")

            # Keep the main thread alive to handle KeyboardInterrupt
            while self.is_running:
                time.sleep(10)

        except KeyboardInterrupt:
            self.is_running = False
            self.logger.info("Received keyboard interrupt, shutting down...")
        except Exception as e:
            self.logger.error(f"Error initializing service: {str(e)}", exc_info=True)
            raise

    def stop(self):
        """
        Close connections and stop background threads.
        Should be called when shutting down the application.
        """
        self.is_running = False

        # Wait for threads to finish
        if (
            hasattr(self, "stats_thrdata_listing_threadead")
            and self.data_listing_thread
            and self.data_listing_thread.is_alive()
        ):
            self.data_listing_thread.join(timeout=5)

        if (
            hasattr(self, "mission_thread")
            and self.mission_thread
            and self.mission_thread.is_alive()
        ):
            self.mission_thread.join(timeout=5)

        if hasattr(self, "rmq_conn") and self.rmq_conn and self.rmq_conn.is_open:
            self.rmq_conn.close()
            self.logger.info("RabbitMQ connection closed")

    def is_healthy(self):
        """
        Check if the service is healthy.
        """
        return (
            self.is_running
            and hasattr(self, "rmq_conn")
            and self.rmq_conn
            and self.rmq_conn.is_open
        )

    def cleanup(self):
        """
        Clean up resources, closing connections and channels.
        """
        if hasattr(self, "rmq_conn") and self.rmq_conn and self.rmq_conn.is_open:
            self.rmq_conn.close()
            self.logger.info("RabbitMQ connection closed")
        self.rabbit_mq.close()
        self.machine_stats.cleanup()

    def __del__(self):
        """Destructor called by garbage collector to ensure resources are cleaned up, when object is about to be destroyed"""
        try:
            if self.is_running:
                self.logger.error(
                    "Destructor called by garbage collector to cleanup MissionStats"
                )
                self.stop()
        except Exception as e:
            pass


def main():
    """Example of how to use the PersistentMissionStats"""
    print("Starting persistent mission data service example")

    # Create the service (replace with your actual RabbitMQ connection string)
    # from vyomcloudbridge.services.mission_stats import MissionStats

    mission_stats_service = MissionStats()

    try:
        # Set current mission and user for testing

        mission_id = 301393
        machine_id = 42
        # mission_stats_service.update_current_mission(
        #     id=mission_id,
        #     name="Navigation Test Mission",
        #     description="Testing mission navigation features",
        #     creator_id=1,
        #     owner_id=1,
        #     mission_status=1,
        #     campaign_id=1,
        #     mission_date="2025-03-21",
        #     start_time="2025-03-21T10:00:00Z",
        #     end_time=None,
        # )

        # user_detail = {
        #     "id": 42,
        #     "name": "Test User",
        #     "email": "testuser@example.com",
        #     "role": "operator",
        # }
        # mission_stats_service.set_current_user(user_detail)

        # # Test mission and user retrieval
        # current_mission, mission_read_error = mission_stats_service.get_current_mission()
        # print(f"Current mission: {current_mission}")

        # current_user = mission_stats_service.get_current_user()
        # print(f"Current user: {current_user}")

        # # Add data for multiple file formats
        # s3_dir_video = (
        #     f"1/{default_project_id}/2025-02-11/{machine_id}/{mission_id}/99/video/"
        # )
        # s3_dir_file = (
        #     f"1/{default_project_id}/2025-02-11/{machine_id}/{mission_id}/99/file/"
        # )
        # data_source = "camera1"

        # # # Process video files
        # mission_stats_service.on_mission_data_arrive(
        #     mission_id, 125000, 1, "mp4", data_source, s3_dir_video
        # )

        # mission_stats_service.on_mission_data_arrive(
        #     mission_id, 130000, 1, "mp4", data_source, s3_dir_video
        # )
        # mission_stats_service.on_mission_data_arrive(
        #     mission_id, 200000, 1, "mkv", data_source, s3_dir_video
        # )

        # mission_stats_service.on_mission_data_publish(
        #     mission_id,
        #     125000,
        #     "mp4",
        #     data_source,
        # )

        # # Process log files
        # mission_stats_service.on_mission_data_arrive(
        #     mission_id,, 500, 1, "log" data_source, s3_dir_file
        # )
        # mission_stats_service.on_mission_data_arrive(
        #     mission_id, 600, 1, "log", data_source, s3_dir_file
        # )

        # # Process telemetry files
        # mission_stats_service.on_mission_data_arrive(
        #     mission_id, 2500, 1, "json", data_source, s3_dir_file
        # )

        # # Get mission data (should be retrieved from RabbitMQ)
        # mission_stats_data = mission_stats_service.get_stats_from_rabbitmq(mission_id)
        # print("mission_stats_data-", mission_stats_data)

        # for entry in mission_stats_data:
        #     print(
        #         f"  {entry['data_type']} ({entry['data_source']}): {entry['file_count']} files, {entry['data_size']} bytes, last updated {entry['updated_at']}"
        #     )

        # mission_stats_service.start()
        # while mission_stats_service.is_running:
        #     time.sleep(5)

        # mission_stats_service.publish_mission_telemetry(
        #     mission_id, sample_mission_telemetry
        # )
        # mission_stats_service.publish_mission_summary(
        #     mission_id, sample_mission_summary
        # )

    finally:
        # Clean up
        mission_stats_service.stop()

    mission_stats_service = MissionStats()
    try:
        mission_stats_service.start()
        while mission_stats_service.is_running:
            try:
                time.sleep(10)  # Sleep to prevent high CPU usage
            except KeyboardInterrupt:
                print("\nInterrupted by user, shutting down...")
                break
    finally:
        # Clean up
        mission_stats_service.stop()

    print("Completed persistent mission data service example")


if __name__ == "__main__":
    main()
