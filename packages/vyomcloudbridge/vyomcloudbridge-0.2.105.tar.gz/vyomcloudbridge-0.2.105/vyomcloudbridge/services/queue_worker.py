# vyomcloudbridge/queue_worker.py
import base64
import signal
import threading
import time
import copy
import pika
import pika.channel
from pika.spec import Basic
from pika.exceptions import (
    ConnectionClosedByBroker,
    AMQPChannelError,
    AMQPConnectionError,
)
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Dict, Any, Tuple
from vyomcloudbridge.services.vyom_sender import VyomSender
from vyomcloudbridge.utils.common import ServiceAbstract, parse_bool
from vyomcloudbridge.utils.configs import Configs
from vyomcloudbridge.services.mission_stats import MissionStats
from vyomcloudbridge.constants.constants import data_buffer_key, UPLOAD_THREADS
from vyomcloudbridge.utils.logger_setup import setup_logger
from vyomcloudbridge.constants.constants import main_data_queue


class QueueWorker(ServiceAbstract):
    """
    Worker class that handles rabbit_mq consumption and message publishing.
    Inherits from ServiceAbstract for consistent service management.
    """

    def __init__(
        self,
        multi_thread: bool = False,
        host: str = "localhost",
        num_threads: int = UPLOAD_THREADS,
        log_level=None,
    ):
        try:
            self.log_level = log_level
            super().__init__(multi_thread=multi_thread, log_level=log_level)
            self.logger.info("QueueWorker initializing...")
            self.mission_stats = MissionStats(log_level=log_level)
            self.vyom_sender = None
            self.fail_client_pausetime = 3
            self.logger.info("QueueWorker initialized successfully!")
            self.upload_stats = {}
            self._upload_stats_lock = threading.Lock()
            self.upload_stats_publish_interval = 10  # TODO is was 120 earlier
            self.upload_stats_error_delay = 300

            self.host = host
            self.queue_name = main_data_queue
            self.num_threads = num_threads if parse_bool(multi_thread) else 1
            self.is_running = False

        except Exception as e:
            self.logger.error(f"Error initializing QueueWorker: {str(e)}")
            raise

    def _get_vyom_sender(self):
        """Setup connection and channel with retry logic"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                vyom_sender = VyomSender(log_level=self.log_level)
                return vyom_sender
            except Exception as e:
                self.logger.error(f"Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(self.fail_client_pausetime)
                else:
                    self.logger.error(
                        "Failed to establish VyomSender connection after 3 attempts"
                    )
                    raise

    def proccess_deque_message(
        self, message: Dict[str, Any], vyom_sender_conn
    ) -> Tuple[bool, list[Any]]:
        """
        Args:
            message (Dict[str, Any]): The message to be processed.
                Expected keys:
                    - "data": Base64 encoded data if message_type is "binary"

                    - "message_type": Type of the message (e.g., "binary", "json")
                    - "topic": Topic to which the message should be published
                    - "data_source": Source of the data
                    - "destination_ids": List of destination IDs for the message
                    - "buffer_key": Optional key for tracking upload stats
                    - "buffer_size": Size of the buffer for upload stats
                    - "data_type": Type of data being uploaded
        Returns:
            bool: True if publishing successful, False otherwise
        """
        try:
            self.logger.debug("proccess_deque_message called")
            message_type = message.get("message_type", "json")
            topic = message.get("topic", None)
            data_source = message.get("data_source", None)
            destination_ids = message.get("destination_ids", [])
            if len(destination_ids) == 0:
                self.logger.warning(
                    f"No destination_ids found in message, skipping message..."
                )
                return True, []

            data = message.get("data", None)
            # data = base64.b64decode(data) if message_type == "binary" else data
            destination_ids_str = ",".join(destination_ids)
            self.logger.debug(
                f"found data-{topic}, destination_ids: [{destination_ids_str}]"
            )
            result, remaining_dest_ids = vyom_sender_conn.send_message(
                data, message_type, destination_ids, data_source, topic
            )
            if result:
                try:
                    buffer_key = message.get("buffer_key", None)
                    upload_size = message.get("buffer_size", 0)
                    data_type = message.get("data_type", 0)
                    if buffer_key and upload_size:
                        with self._upload_stats_lock:
                            if buffer_key not in self.upload_stats:
                                self.upload_stats[buffer_key] = {
                                    "size": upload_size,
                                    "file_count": 1,
                                    "data_type": data_type,
                                    "data_source": data_source,
                                }
                            else:
                                self.upload_stats[buffer_key]["size"] += upload_size
                                self.upload_stats[buffer_key]["file_count"] += 1
                                self.upload_stats[buffer_key]["data_type"] = data_type
                                self.upload_stats[buffer_key][
                                    "data_source"
                                ] = data_source

                except Exception as e:
                    self.logger.warning(f"Error updating upload stats: {e}")
                    pass
                # if message.get("buffer_key", None) != data_buffer_key:
                #     try:
                #         mission_id = int(message.get("buffer_key", None))
                #         buffer_size = message.get("buffer_size", 0)
                #         data_type = message.get("data_type", 0)
                #         if buffer_size:
                #             self.mission_stats.on_mission_data_publish(
                #                 mission_id=mission_id,
                #                 size=buffer_size,
                #                 file_count=1,
                #                 data_type=data_type,
                #                 data_source=data_source,
                #             )
                #     except Exception as e:
                #         pass
            else:
                remaining_dest_ids_str = ",".join(remaining_dest_ids)
                self.logger.debug(
                    f"Error: Message proccesing failed topic: {topic}, remaining_dest_ids: [{remaining_dest_ids_str}]"
                )
            return result, remaining_dest_ids

        except Exception as e:
            self.logger.error(f"error in publishing message: {e}")
            return False, destination_ids

    def _publish_upload_stats(self):
        """
        Publish upload stats to the vyom sender.
        """
        try:
            if not self.upload_stats:
                self.logger.debug("No upload stats to publish")
                return
            with self._upload_stats_lock:
                upload_stats_copy = copy.deepcopy(self.upload_stats)
                self.upload_stats.clear()

            self.logger.debug("Publishing upload stats to vyom sender")
            for buffer_key, stats in upload_stats_copy.items():
                size = stats["size"]
                file_count = stats["file_count"]
                data_type = stats["data_type"]
                data_source = stats["data_source"]
                self.mission_stats.on_mission_data_publish(
                    mission_id=buffer_key,
                    size=size,
                    file_count=file_count,
                    data_type=data_type,
                    data_source=data_source,
                )
        except Exception as e:
            self.logger.error(f"Error publishing upload stats: {e}")

    def _consume_queue_message(
        self,
        vyom_sender_conn,
        channel: pika.channel.Channel,
        method_frame: Basic.Deliver,
        properties: pika.BasicProperties,
        body,
    ):
        """Process a single message"""
        try:
            message = body
            headers = {}
            expiration = None
            start_time_ms = int(time.time() * 1000)  # Get current time in milliseconds
            if hasattr(properties, "expiration") and properties.expiration:
                expiration = properties.expiration

            if hasattr(properties, "headers") and properties.headers:
                headers = properties.headers
            else:
                channel.basic_ack(delivery_tag=method_frame.delivery_tag)
                self.logger.error(f"Headers not found in messase skipping message")
                return
            self.logger.debug(f"proccessing data having header={headers}")
            queue_name = method_frame.routing_key
            priority = properties.priority if properties.priority is not None else 0
            new_priority = max(priority - 1, 0) if priority < 3 else priority  # TODO

            expiry_info = ""
            if hasattr(properties, "expiration") and properties.expiration:
                expiry_info = f" with expiration {properties.expiration}ms"
            self.logger.debug(
                f"Processing message from {queue_name} with priority {priority}{expiry_info}"
            )

            result, remaining_dest_ids = self.proccess_deque_message(
                {"data": message, **headers}, vyom_sender_conn
            )

            if result:
                channel.basic_ack(delivery_tag=method_frame.delivery_tag)
                self.logger.debug(f"Message processed successfully in {queue_name}")
            else:
                # If processing failed, republish with mew priority, and update destination_ids
                self.logger.debug(
                    f"Error: Message processing failed in {queue_name}, requeuing with new priority {new_priority}"
                )
                # First ack the original message
                channel.basic_ack(delivery_tag=method_frame.delivery_tag)

                new_properties = {
                    "priority": new_priority,
                    "content_type": properties.content_type,
                    "delivery_mode": properties.delivery_mode,  # Preserve persistence setting
                }
                if expiration is not None:
                    curr_time_ms = int(time.time() * 1000)
                    # Calculate remaining time until expiration
                    remaining_time_ms = int(expiration) - (curr_time_ms - start_time_ms)
                    if remaining_time_ms > 0:
                        new_properties["expiration"] = str(remaining_time_ms)
                    else:
                        destination_ids = properties.headers.get("destination_ids", [])
                        destination_ids_str = (
                            ",".join(str(id) for id in destination_ids) or "-"
                        )
                        data_source = properties.headers.get("data_source", "-")
                        # new_properties["expiration"] = "0"
                        # Above does not worked, as immediate consumer is available,
                        self.logger.info(
                            f"Message got expired, removed, data_source='{data_source}', destination_ids=[{destination_ids_str}]"
                        )
                        return

                # if hasattr(properties, "expiration") and properties.expiration:
                #     new_properties["expiration"] = properties.expiration

                if hasattr(properties, "headers") and properties.headers:
                    headers = dict(copy.deepcopy(properties.headers))
                    headers["destination_ids"] = remaining_dest_ids
                    new_properties["headers"] = headers

                if (
                    hasattr(properties, "content_encoding")
                    and properties.content_encoding
                ):
                    new_properties["content_encoding"] = properties.content_encoding

                channel.basic_publish(
                    exchange="",
                    routing_key=queue_name,
                    body=body,
                    properties=pika.BasicProperties(**new_properties),
                )

        except Exception as e:
            self.logger.error(
                f"Error processing message _consume_queue_message in {queue_name} error: {e}"
            )
            # For exceptions, also republish with new priority
            try:
                priority = properties.priority if properties.priority is not None else 0
                self.logger.warning(
                    f"Error processing message, requeuing with new priority {new_priority}"
                )
                # First ack the original message
                channel.basic_ack(delivery_tag=method_frame.delivery_tag)

                new_properties = {
                    "priority": new_priority,
                    "content_type": properties.content_type,
                    "delivery_mode": properties.delivery_mode,  # Preserve persistence setting
                }

                if expiration is not None:
                    curr_time_ms = int(time.time() * 1000)
                    # Calculate remaining time until expiration
                    remaining_time_ms = int(expiration) - (curr_time_ms - start_time_ms)
                    if remaining_time_ms > 0:
                        new_properties["expiration"] = str(remaining_time_ms)
                    else:
                        destination_ids = properties.headers.get("destination_ids", [])
                        destination_ids_str = (
                            ",".join(str(id) for id in destination_ids) or "-"
                        )
                        data_source = properties.headers.get("data_source", "-")
                        # new_properties["expiration"] = "0"
                        # Above does not worked, as immediate consumer is available,
                        self.logger.info(
                            f"Message got expired, removed, data_source='{data_source}', destination_ids=[{destination_ids_str}]"
                        )  #
                        return

                # if hasattr(properties, "expiration") and properties.expiration:
                #     new_properties["expiration"] = properties.expiration

                if hasattr(properties, "headers") and properties.headers:
                    new_properties["headers"] = properties.headers

                if (
                    hasattr(properties, "content_encoding")
                    and properties.content_encoding
                ):
                    new_properties["content_encoding"] = properties.content_encoding

                channel.basic_publish(
                    exchange="",
                    routing_key=queue_name,
                    body=body,
                    properties=pika.BasicProperties(**new_properties),
                )
            except Exception as republish_error:
                self.logger.error(
                    f"Failed to republish message with new priority: {republish_error}"
                )
                channel.basic_nack(delivery_tag=method_frame.delivery_tag, requeue=True)

    def _worker(self):
        """Worker thread function to process messages"""
        # Create a dedicated connection for this worker
        rmq_conn = None
        rmq_channel = None
        vyom_sender_conn = self._get_vyom_sender()

        try:
            rmq_conn = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=self.host,
                    heartbeat=600,
                    blocked_connection_timeout=300,
                    socket_timeout=300,
                )
            )
            rmq_channel = rmq_conn.channel()
            rmq_channel.queue_declare(
                queue=self.queue_name,
                durable=True,
                arguments={
                    "x-message-ttl": 1000 * 60 * 60 * 24,
                    "x-max-priority": 10,
                },
            )

            # Set QoS
            rmq_channel.basic_qos(prefetch_count=1)

            # Setup consumer with the callback
            def callback_wrapper(ch, method, properties, body):
                self._consume_queue_message(
                    vyom_sender_conn, ch, method, properties, body
                )

            # Start consuming
            rmq_channel.basic_consume(
                queue=self.queue_name,
                on_message_callback=callback_wrapper,
                auto_ack=False,  # We'll handle acknowledgments manually
            )
            self.logger.info(f"Worker thread started for {self.queue_name}")
            while self.is_running:
                # Process messages for a short time before checking if we should stop
                rmq_conn.process_data_events(time_limit=1)
                # self.logger.debug(
                #     "Processed pending RabbitMQ events in queue '%s'", self.queue_name
                # )

        except (ConnectionClosedByBroker, AMQPChannelError) as e:
            self.logger.error(f"Connection error in worker: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error in worker: {e}")
        finally:
            if rmq_channel is not None and rmq_channel.is_open:
                try:
                    rmq_channel.close()
                except:
                    pass

            if vyom_sender_conn:
                try:
                    vyom_sender_conn.cleanup()
                except:
                    pass

            if rmq_conn is not None and rmq_conn.is_open:
                try:
                    rmq_conn.close()
                except:
                    pass

    def start_consume(self) -> None:
        """Start consuming messages with multiple worker threads"""
        self.logger.info(
            f"Starting consumption from {self.queue_name} with {self.num_threads} threads"
        )
        self.is_running = True

        # Create thread pool for workers
        with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            futures = [executor.submit(self._worker) for _ in range(self.num_threads)]

            # Setup signal handler for graceful shutdown
            def signal_handler(signum, frame):
                self.logger.info("Shutdown signal received, stopping workers...")
                self.is_running = False

            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)

            try:
                # Wait for all futures to complete
                for future in futures:
                    future.result()
            except KeyboardInterrupt:
                self.logger.info("Keyboard interrupt received, initiating shutdown...")
                self.is_running = False

    def start(self):
        """Start publishing messages from the rabbit_mq."""
        try:
            self.logger.info("Starting QueueWorker service...")
            self.is_running = True

            def upload_stats_loop():
                while self.is_running:
                    try:
                        self._publish_upload_stats()
                        time.sleep(self.upload_stats_publish_interval)
                        self.logger.debug(
                            "Upload stats published; sleeping for %s seconds",
                            self.upload_stats_publish_interval,
                        )
                    except Exception as e:
                        self.logger.error(f"Error in stats publisher loop: {str(e)}")
                        time.sleep(self.upload_stats_error_delay)

            self.data_listing_thread = threading.Thread(
                target=upload_stats_loop, daemon=True
            )
            self.data_listing_thread.start()

            self.logger.info("Started QueueWorker service!")
            self.start_consume()

            while self.is_running:
                self.logger.debug(
                    "QueueWorker is actively running for queue '%s'", self.queue_name
                )
                time.sleep(10)

        except Exception as e:
            self.logger.error(f"Error in starting QueueWorker: {e}")
            raise
        finally:
            self.stop()

    def stop(self):
        """Stop resources and connections."""
        try:
            self.logger.info("Stopping QueueWorker service...")
            if self.is_running:
                self.is_running = False
                if self.mission_stats:
                    self.mission_stats.cleanup()
                self.logger.info("Stopped QueueWorker service!")
            else:
                self.logger.info("QueueWorker service already stopped, skipped..")
        except Exception as e:
            self.logger.error(f"Error during stop: {e}")

    def cleanup(self):
        """cleaning resources and connections."""
        try:
            self.logger.info("cleaning QueueWorker service...")
            self.is_running = False
            if self.mission_stats:
                self.mission_stats.cleanup()
            self.logger.info("Cleaned QueueWorker service!")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

    def is_healthy(self):
        """
        Override health check to add additional service-specific checks.
        """
        return self.is_running

    def __del__(self):
        """Destructor called by garbage collector to ensure resources are cleaned up, when object is about to be destroyed"""
        try:
            self.logger.error(
                "Destructor called by garbage collector to cleanup QueueWorker"
            )
            self.cleanup()
        except Exception as e:
            pass


def main():
    """
    Main entry point for the queue worker service.
    """
    service = QueueWorker()
    try:
        service.start()

        # Keep the main thread running
        while service.is_running:
            time.sleep(10)
    except KeyboardInterrupt:
        pass
    finally:
        service.stop()


if __name__ == "__main__":
    main()
