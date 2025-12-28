import pika
import json
import logging
from datetime import datetime, timezone
import threading
import time
from typing import Dict, Any, Optional
from vyomcloudbridge.services.rabbit_queue.queue_main import RabbitMQ
from vyomcloudbridge.services.root_store import RootStore
from vyomcloudbridge.utils.common import ServiceAbstract, get_mission_upload_dir
from vyomcloudbridge.constants.constants import (
    DEFAULT_RABBITMQ_URL,
    default_project_id,
    default_mission_id,
    data_buffer_key,
    main_data_queue,
    MACHINE_STATS_DT_SRC
)
from vyomcloudbridge.utils.configs import Configs
from vyomcloudbridge.services.rabbit_mq_utils import RabbitMQUtils


class MachineStats(ServiceAbstract):
    """
    A service that maintains machine buffer statistics using RabbitMQ as a persistent store.
    Stores the current buffer state in a dedicated queue and publishes stats to HQ.
    """

    def __init__(self, log_level=None):
        """
        Initialize the machine stats service with RabbitMQ connection.
        """
        super().__init__(log_level=log_level)
        self.host: str = "localhost"
        self.rabbitmq_url = DEFAULT_RABBITMQ_URL
        self.priority = 2  # live priority
        self.stats_publish_interval = 4  # Seconds between stats publication
        self.publish_error_delay = 20  # Delay after publish error
        self.buffer_process_interval = 5  # seconds

        self.connection_lock = threading.Lock()
        self._connection_in_progress = False
        self.rmq_conn = None
        self.rmq_channel = None
        self.rabbit_mq = RabbitMQ(log_level=log_level)
        self.machine_config = Configs.get_machine_config()
        self.machine_id = self.machine_config.get("machine_id", "-") or "-"
        self.organization_id = self.machine_config.get("organization_id", "-") or "-"
        self.data_source = MACHINE_STATS_DT_SRC
        self.buffer_update_lock = threading.Lock()
        self.expiration = "2000"  # milisecond
        self.root_store = RootStore(log_level=log_level)
        self.rabbit_mq_utils = RabbitMQUtils(log_level=log_level)
        self.rabbit_mq_api_sync_delay = 5  # seconds
        self.destination_ids = ["s3", "gcs_mqtt"]
        # Thread attributes
        self.stats_thread = None
        self.is_running = False

    def _setup_connection(self):
        """Set up RabbitMQ connection and declare the queue for machine buffer."""
        try:
            # Establish connection
            self.rmq_conn = pika.BlockingConnection(
                pika.URLParameters(self.rabbitmq_url)
            )
            self.rmq_channel = self.rmq_conn.channel()

            # Declare queue for machine buffer
            self.rmq_channel.queue_declare(queue="machine_buffer", durable=True)
            self.rmq_channel.queue_declare(queue="machine_buffer_array", durable=True)

            self.logger.debug("RabbitMQ connection established successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize RabbitMQ: {str(e)}")
            raise

    def _ensure_connection(self) -> bool:
        """Ensure connection and channel are active and working"""
        with self.connection_lock:
            try:
                self._connection_in_progress = True
                if not self.rmq_conn or self.rmq_conn.is_closed:
                    self._setup_connection()
                    self._connection_in_progress = False
                    return True

                if not self.rmq_channel or self.rmq_channel.is_closed:
                    self.logger.info("Closed channel found, re-establishing...")
                    self.rmq_channel = self.rmq_conn.channel()
                    self.rmq_channel.queue_declare(queue="machine_buffer", durable=True)
                    self.rmq_channel.queue_declare(
                        queue="machine_buffer_array", durable=True
                    )
                    self.logger.info("Channel re-established successfully")

                self._connection_in_progress = False
                return True
            except Exception as e:
                self.logger.error(f"Failed to ensure connection: {e}")
                self.rmq_conn = None
                self.rmq_channel = None
                self._connection_in_progress = False
                return False

    def _get_current_buffer(self):
        """
        Get the current data size and uploaded size from RabbitMQ.

        Returns:
            Tuple of (data_size, data_size_uploaded) or (0, 0) if not found.
        """
        try:
            if self._connection_in_progress:
                self.logger.info("Connection in progress, skipping _get_current_buffer")
                return None, None

            if not self._ensure_connection():
                raise Exception(
                    "Could not establish connection, in _get_current_buffer"
                )

            method_frame, _, body = self.rmq_channel.basic_get(
                queue="machine_buffer", auto_ack=False
            )

            if method_frame:
                data = json.loads(body.decode("utf-8"))
                self.rmq_channel.basic_nack(
                    delivery_tag=method_frame.delivery_tag, requeue=True
                )
                data_size = data.get("data_size", 0)
                data_size_uploaded = data.get("data_size_uploaded", 0)
                return data_size, data_size_uploaded
        except pika.exceptions.DuplicateGetOkCallback as e:
            self.logger.error(
                f"DuplicateGetOkCallback error in _get_current_buffer: {e}"
            )
            raise
        except Exception as e:
            self.logger.error(f"Warning getting current buffer: {str(e)}")
            raise
        return None, None

    def get_current_buffer(self):  # TODO: remove this
        return self._get_current_buffer()

    def _set_current_buffer(self, data_size: int, data_size_uploaded: int):
        try:
            if not self._ensure_connection():
                raise Exception("Could not establish connection")

            while True:
                method_frame, _, _ = self.rmq_channel.basic_get(
                    queue="machine_buffer", auto_ack=True
                )
                if not method_frame:
                    break

            body = json.dumps(
                {"data_size": data_size, "data_size_uploaded": data_size_uploaded}
            )

            self.rmq_channel.basic_publish(
                exchange="",
                routing_key="machine_buffer",
                body=body,
                properties=pika.BasicProperties(delivery_mode=2),
            )

            self.logger.debug(
                f"Set buffer: data_size={data_size}, data_size_uploaded={data_size_uploaded}"
            )
        except pika.exceptions.DuplicateGetOkCallback as e:
            self.logger.error(
                f"DuplicateGetOkCallback error in _set_current_buffer: {e}"
            )
            raise
        except Exception as e:
            self.logger.error(f"Error setting buffer state: {str(e)}")
            raise

    def on_data_arrive(self, size: int):
        try:
            self.logger.debug(
                f"Machine stats: on_data_arrive called with size {size} bytes"
            )
            if not self._ensure_connection():
                raise Exception("Could not establish connection")
            body = json.dumps({"size": int(size)})
            self.rmq_channel.basic_publish(
                exchange="",
                routing_key="machine_buffer_array",
                body=body,
                properties=pika.BasicProperties(delivery_mode=2),
            )
            self.logger.debug(f"Enqueued data arrival: {size} bytes")
        except Exception as e:
            self.logger.error(f"Error enqueuing on on_data_arrive: {str(e)}")

        # try:
        #     data_size, data_size_uploaded = self._get_current_buffer()
        #     new_data_size = data_size + int(size)
        #     self._set_current_buffer(new_data_size, data_size_uploaded)
        #     self.logger.info(
        #         f"Data arrived: +{size} bytes, new data_size={new_data_size}"
        #     )
        # except Exception as e:
        #     self.logger.error(f"Error handling data arrival: {str(e)}")

    def on_data_publish(self, size: int):
        try:
            self.logger.debug(
                f"Machine stats: on_data_publish called with size {size} bytes"
            )
            if not self._ensure_connection():
                raise Exception("Could not establish connection")
            body = json.dumps(
                {"size": -int(size)}
            )  # keeping it negative to indicate data publish
            self.rmq_channel.basic_publish(
                exchange="",
                routing_key="machine_buffer_array",
                body=body,
                properties=pika.BasicProperties(delivery_mode=2),
            )
            self.logger.debug(f"Enqueued data arrival: {size} bytes")
        except Exception as e:
            self.logger.error(f"Error enqueuing in on_data_publish: {str(e)}")

        # try:
        #     data_size, data_size_uploaded = self._get_current_buffer()
        #     new_uploaded = min(data_size_uploaded + int(size), data_size)
        #     self._set_current_buffer(data_size, new_uploaded)
        #     self.logger.info(
        #         f"Data published: +{size} bytes, total uploaded={new_uploaded}"
        #     )
        # except Exception as e:
        #     self.logger.error(f"Error handling data publish: {str(e)}")

    def _publish_stats_to_hq(self) -> bool:
        """
        Send buffer size to API endpoint with retry logic.

        Returns:
            True if report was successful, False otherwise
        """
        try:
            # Get current buffer
            data_size, data_size_uploaded = self._get_current_buffer()

            if data_size is None or data_size_uploaded is None:
                buffer_size_bytes = None
            else:
                buffer_size_bytes = data_size - data_size_uploaded

            try:
                location_data = self.root_store.get_data("location")
            except Exception as e:
                location_data = None

            try:
                health_data = self.root_store.get_data("health")
            except Exception as e:
                health_data = None

            epoch_ms = int(time.time() * 1000)
            # Prepare payload
            payload = {
                "machine_id": self.machine_id,
                "buffer": buffer_size_bytes,
                "data_size": data_size,
                "data_size_uploaded": data_size_uploaded,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "timestamp": epoch_ms,
                "location": location_data,
                "health": health_data,
            }

            # Log current state
            if buffer_size_bytes is not None:
                buffer_str = f"{buffer_size_bytes:.2f}"
            else:
                buffer_str = "N/A"
            self.logger.debug(f"Current buffer state: Total: {buffer_str} bytes")

            now = datetime.now(timezone.utc)
            date = now.strftime("%Y-%m-%d")
            # mission_upload_dir = f"{self.machine_config['organization_id']}/{default_project_id}/{date}/machine_stats/{self.machine_id}" # TODO
            mission_upload_dir: str = get_mission_upload_dir(
                organization_id=self.organization_id,
                machine_id=self.machine_id,
                mission_id=default_mission_id,
                data_source=self.data_source,
                date=date,
                project_id=default_project_id,
            )
            message_body = json.dumps(payload)
            headers = {
                "topic": f"{mission_upload_dir}/{epoch_ms}.json",
                "message_type": "json",
                "destination_ids": self.destination_ids,
                "data_source": self.data_source,
                # meta data
                "buffer_key": data_buffer_key,
                "buffer_size": 0,
                "data_type": "json",
            }
            self.rabbit_mq.enqueue_message(
                message=message_body,
                headers=headers,
                priority=self.priority,
                expiration=self.expiration,
            )

            self.logger.debug("HEARTBEAT")
            return True

        except Exception as e:
            self.logger.error(f"Machine stats publish: Unexpected error: {e}")
            return False

    def _update_buffer_untill_success(
        self, total_enqued_size: int, total_dequed_size: int
    ):
        """
        Continuously update the buffer until the RabbitMQ connection is healthy.
        """
        loopcount = 10
        while self.is_running and loopcount > 0:
            try:
                with self.buffer_update_lock:
                    data_size, data_size_uploaded = self._get_current_buffer()
                    # new stats
                    new_data_size = data_size if data_size is not None else 0
                    new_data_size_uploaded = (
                        data_size_uploaded if data_size_uploaded is not None else 0
                    )

                    new_data_size = new_data_size + total_enqued_size
                    new_data_size_uploaded = new_data_size_uploaded + total_dequed_size

                    if new_data_size_uploaded > new_data_size:
                        new_data_size = new_data_size_uploaded
                    self.logger.debug(f"On update_buffer...")
                    self._set_current_buffer(new_data_size, new_data_size_uploaded)
                    self.logger.debug(
                        f"On update_buffer, set data size: {new_data_size}, uploaded: {new_data_size_uploaded} bytes"
                    )
                    return
            except Exception as e:
                loopcount -= 1
                self.logger.error(f"Error updating buffer: {str(e)}")
                time.sleep(5)
        try:
            self.on_data_arrive(total_enqued_size)
            self.on_data_publish(total_dequed_size)
        except Exception as e:
            self.logger.error(f"Error re-enqueuing data after failure: {str(e)}")
            raise

    def _update_buffer_when_all_data_uploaded(self):
        """
        Set pameter when all data got uploaded.
        """
        loopcount = 10
        while self.is_running and loopcount > 0:
            try:
                with self.buffer_update_lock:
                    data_size, data_size_uploaded = (
                        self._get_current_buffer()
                    )  # these both might be null
                    # new stats
                    if data_size is None and data_size_uploaded is None:
                        return
                    elif data_size is None:
                        data_size = data_size_uploaded
                    elif data_size_uploaded is None:
                        data_size_uploaded = data_size

                    new_data_size = max(data_size, data_size_uploaded)
                    new_data_size_uploaded = new_data_size
                    self.logger.debug(f"On all_data_uploaded...")
                    self._set_current_buffer(new_data_size, new_data_size_uploaded)
                    self.logger.info("ZERO BUFFER")
                    return
            except Exception as e:
                loopcount -= 1
                self.logger.error(
                    f"Error updating buffer when all data uploaded: {str(e)}"
                )
                time.sleep(5)

    def _process_buffer_array(self):
        while self.is_running:
            try:
                if not self._ensure_connection():
                    self.logger.error(
                        "Could not ensure RabbitMQ connection, in process_buffer_array"
                    )
                    time.sleep(5)
                    continue
                total_size_enques = 0
                total_size_deques = 0
                for _ in range(10):
                    try:
                        method_frame, _, body = self.rmq_channel.basic_get(
                            queue="machine_buffer_array", auto_ack=True
                        )
                        if not method_frame:
                            break
                        json_data = json.loads(body.decode("utf-8"))
                        data_size = json_data.get("size", 0)
                        if data_size > 0:
                            total_size_enques += data_size
                        else:
                            total_size_deques += -data_size
                    except IndexError as ie:
                        self.logger.error(
                            f"IndexError in buffer array processing: {ie}"
                        )
                        break
                    except pika.exceptions.StreamLostError as sle:
                        self.logger.error(
                            f"StreamLostError in buffer array processing: {sle}"
                        )
                        self.rmq_conn = None
                        self.rmq_channel = None
                        break
                    except Exception as e:
                        self.logger.error(f"Error processing buffer array: {str(e)}")
                        self.rmq_conn = None
                        self.rmq_channel = None
                        break
                self.logger.debug(
                    f"Buffer array processed: {total_size_enques} enqueues, {total_size_deques} deques"
                )
                if total_size_enques > 0 or total_size_deques > 0:
                    self._update_buffer_untill_success(
                        total_size_enques, total_size_deques
                    )
                else:  # no changes in buffer, also check, message count in queue_main
                    self.logger.debug(
                        f"No changes in buffer, checking queue_main {main_data_queue} size, with sleep {self.rabbit_mq_api_sync_delay}"
                    )
                    time.sleep(
                        self.rabbit_mq_api_sync_delay
                    )  # lets wait till all message should refelected for now in API
                    queue_info, error = self.rabbit_mq_utils.get_queue_info(
                        main_data_queue
                    )
                    if error:
                        self.logger.error(f"Error getting queue info: {error}")
                    else:
                        if (
                            queue_info.get("messages") <= 1
                        ):  # assume that queue got empty
                            self._update_buffer_when_all_data_uploaded()
                    time.sleep(self.buffer_process_interval)
            except Exception as e:
                self.logger.error(f"Error processing buffer array: {str(e)}")

    def start(self):
        """
        Start the machine stats service, including the background publisher thread.
        """
        try:
            self.logger.info("Starting MachineStats service...")
            self.is_running = True

            # Process buffer array
            self.buffer_array_thread = threading.Thread(
                target=self._process_buffer_array, daemon=True
            )
            self.buffer_array_thread.start()

            # Define the stats publisher loop
            def stats_publisher_loop():
                while self.is_running:
                    try:
                        self._publish_stats_to_hq()
                        time.sleep(self.stats_publish_interval)
                    except Exception as e:
                        self.logger.error(f"Error in stats publisher loop: {str(e)}")
                        time.sleep(self.publish_error_delay)

            # Create and start the thread
            self.stats_thread = threading.Thread(
                target=stats_publisher_loop, daemon=True
            )
            self.stats_thread.start()

            self.logger.info("MachineStats service started!")

        except Exception as e:
            self.logger.error(f"Error starting MachineStats service: {str(e)}")
            self.stop()
            raise

    def stop(self):
        """
        Stop the machine stats service and clean up resources.
        """
        self.is_running = False

        # Wait for thread to finish
        if (
            hasattr(self, "stats_thread")
            and self.stats_thread
            and self.stats_thread.is_alive()
        ):
            self.stats_thread.join(timeout=5)

        # Clean up connection
        self.cleanup()

        self.logger.info("MachineStats service stopped")

    def cleanup(self):
        """
        Clean up resources, closing connections and channels.
        """
        try:
            if hasattr(self, "rmq_conn") and self.rmq_conn and self.rmq_conn.is_open:
                self.rmq_conn.close()
        except Exception as e:
            self.logger.error(f"Error closing RabbitMQ connection: {str(e)}")

        try:
            self.rabbit_mq.close()
        except Exception as e:
            self.logger.error(f"Error closing RabbitMQ connection: {str(e)}")

        try:
            self.root_store.cleanup()
        except Exception as e:
            self.logger.error(f"Error closing Root store connection: {str(e)}")

    def is_healthy(self):
        """
        Check if the service is healthy.
        """
        return (
            self.is_running
            and hasattr(self, "rmq_conn")
            and self.rmq_conn
            and self.rmq_conn.is_open
            and self.rabbit_mq.is_healthy()
        )

    def __del__(self):
        """Destructor called by garbage collector to ensure resources are cleaned up, when object is about to be destroyed"""
        try:
            if self.is_running:
                self.logger.error(
                    "Destructor called by garbage collector to cleanup MachineStats"
                )
                self.stop()
        except Exception as e:
            pass


def main():
    """Example of how to use the MachineStats service"""
    print("Starting machine stats service example")

    # # Example 1: Simulate data arrival and publish
    # machine_stats = MachineStats()
    # machine_stats.on_data_arrive(1024)  # 1 MB
    # machine_stats.on_data_publish(500)
    # machine_stats.cleanup()

    # # Example 2: Simulate data arrival and publish
    # try:
    #     machine_stats = MachineStats()
    #     # Simulate data arriving
    #     machine_stats.on_data_arrive(1024)  # 1 MB
    #     print(
    #         f"Current buffer after data arrival: {machine_stats.get_current_buffer()} bytes"
    #     )

    #     # Simulate publishing some data
    #     machine_stats.on_data_publish(500)  # 512 KB
    #     print(
    #         f"Current buffer after publishing: {machine_stats.get_current_buffer()} bytes"
    #     )
    #     # Let it run for a short while
    # finally:
    #     # Clean up
    #     machine_stats.cleanup()

    # Example 3: Service monitoring
    machine_stats = MachineStats()
    try:
        machine_stats.is_running = True
        machine_stats.start()
        while machine_stats.is_running:
            try:
                time.sleep(10)  # Sleep to prevent high CPU usage
            except KeyboardInterrupt:
                print("\nInterrupted by user, shutting down...")
                break
    finally:
        machine_stats.stop()


if __name__ == "__main__":
    main()
