import pika
import pika.channel
from pika.spec import Basic
from pika.exceptions import (
    ConnectionClosedByBroker,
    AMQPChannelError,
    AMQPConnectionError,
)
import json
import logging
from typing import Any, Callable, Dict, Optional
import time
import os
from vyomcloudbridge.utils.logger_setup import setup_logger
from vyomcloudbridge.constants.constants import main_data_queue

class RabbitMQ:
    def __init__(self, host: str = "localhost", queue_name: str = main_data_queue, log_level=None):
        self.host = host
        self.queue_name = queue_name
        self.rmq_conn = None
        self.rmq_channel = None
        self.is_consuming = False
        self.max_enqueue_retries = 5
        self.logger = setup_logger(name=__name__, show_terminal=False, log_level=log_level)
        # Don't set up connection in __init__ when running as service
        # It will be set up in consume() instead

    def _setup_connection(self) -> None:
        """Setup connection and channel with retry logic"""
        if self.rmq_conn and not self.rmq_conn.is_closed:
            try:
                self.rmq_conn.close()
            except:
                pass

        max_retries = 5
        for attempt in range(max_retries):
            try:
                self.rmq_conn = pika.BlockingConnection(
                    pika.ConnectionParameters(
                        host=self.host,
                        heartbeat=300,  # Reduced from 600 to 300 seconds
                        blocked_connection_timeout=120,  # Reduced from 300 to 120
                        socket_timeout=120,  # Reduced from 300 to 120
                    )
                )
                self.rmq_channel = self.rmq_conn.channel()
                # Declare queue with priority support
                self.rmq_channel.queue_declare(
                    queue=self.queue_name,
                    durable=True,
                    arguments={
                        "x-message-ttl": 1000 * 60 * 60 * 24,  # 24 hour TTL
                        "x-max-priority": 10,  # Enable priorities from 0-10
                    },
                )

                # Set QoS
                self.rmq_channel.basic_qos(prefetch_count=1)
                self.logger.debug("RabbitMQ connection established")
                return

            except AMQPConnectionError as e:
                if attempt == max_retries - 1:
                    self.logger.error(
                        f"Failed to connect to RabbitMQ after {max_retries} attempts"
                    )
                    raise
                self.logger.warning(
                    f"RabbitMQ connection attempt {attempt + 1} failed AMQPConnectionError, retrying..."
                )
                time.sleep(2**attempt)
            except Exception as e:
                if attempt == max_retries - 1:
                    self.logger.error(
                        f"Failed to connect to RabbitMQ after {max_retries} attempts"
                    )
                    raise
                self.logger.warning(
                    f"RabbitMQ connection attempt {attempt + 1} failed, retrying..."
                )
                time.sleep(2**attempt)

    def _ensure_connection(self) -> bool:
        """Ensure connection and channel are active and working"""
        try:
            if not self.rmq_conn or self.rmq_conn.is_closed:
                self._setup_connection()
                return True

            if not self.rmq_channel or self.rmq_channel.is_closed:
                self.logger.info("Closed channel found, re-establishing...")
                self.rmq_channel = self.rmq_conn.channel()
                # Declare queue with priority support
                self.rmq_channel.queue_declare(
                    queue=self.queue_name,
                    durable=True,
                    arguments={
                        "x-message-ttl": 1000 * 60 * 60 * 24,  # 24 hour TTL
                        "x-max-priority": 10,  # Enable priorities from 0-10
                    },
                )

                # Set QoS
                self.rmq_channel.basic_qos(prefetch_count=1)
                self.logger.info("Channel re-established successfully")

            return True
        except Exception as e:
            self.logger.error(f"Failed to ensure connection: {e}")
            self.rmq_conn = None
            self.rmq_channel = None
            return False

    def enqueue_message_size(
        self,
        size: int,  # int, string
        queue_name: Optional[str] = None,
        retry_count: int = 1,
    ) -> None:
        if not self._ensure_connection():
            raise Exception("Could not establish connection")

        if queue_name is None:
            queue_name = "machine_buffer_array"

        message = json.dumps({"size": int(size)})

        try:
            self.rmq_channel.basic_publish(
                exchange="",
                routing_key=queue_name,
                body=message,
                properties=pika.BasicProperties(delivery_mode=2),
            )
        except Exception as e:
            self.logger.error(f"Error publishing enqueue_message_size : {e}")
            if retry_count > self.max_enqueue_retries:
                self.logger.error(
                    f"Failed to publish enqueue_message_size after {retry_count} retries, ignoring message"
                )
                return

            self._setup_connection()
            self.enqueue_message_size(
                size=size,
                retry_count=retry_count + 1,
            )

    def enqueue_message(
        self,
        message: Any,  # bytes, string, empty string
        headers: Dict[str, Any] = {},
        priority: int = 0,
        expiration: Optional[str] = None,
        queue_name: Optional[str] = None,
        retry_count: int = 1,
    ) -> None:
        """Publish message to queue with specified priority (0-10, higher is more priority)"""
        """ expiration is millisecond in string """
        if not self._ensure_connection():
            raise Exception("Could not establish connection")

        # Ensure priority is within bounds
        if priority < 0:
            priority = 0
        elif priority > 10:
            priority = 10
        properties = {
            "delivery_mode": 2,  # Make message persistent
            "content_type": "application/json",
            "priority": priority,  # Always set priority
            "headers": headers,
        }
        if expiration is not None:
            properties["expiration"] = expiration  # 60 seconds TTL

        if queue_name is None:
            queue_name = self.queue_name

        try:
            self.rmq_channel.basic_publish(
                exchange="",
                routing_key=queue_name,
                body=message,
                properties=pika.BasicProperties(**properties),
            )
            # message_str = (
            #     json.dumps(message) if not isinstance(message, str) else message
            # )
            # truncated_message = (
            #     (message_str[:100] + "...") if len(message_str) > 100 else message_str
            # )

            expiry_log = f" with expiration {expiration}ms" if expiration else ""
            self.logger.debug(
                f"Enqueued message to queue {queue_name} with priority {priority}{expiry_log}"
            )
        except Exception as e:
            import traceback

            self.logger.error(
                f"Error publishing message: {e}\n{traceback.format_exc()}, headers={headers}"
            )
            if retry_count > self.max_enqueue_retries:
                self.logger.error(
                    f"Failed to publish message after {retry_count} retries, ignoring message"
                )
                return

            self._setup_connection()
            self.enqueue_message(
                message=message,
                headers=headers,
                priority=priority,
                expiration=expiration,
                queue_name=queue_name,
                retry_count=retry_count + 1,
            )

    def _consume_queue_message(  # Note in use
        self,
        callback: Callable,
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
            # pass data to callback in format
            #         - "data": message
            #         # rest all take from header

            #         - "message_type": Type of the message (e.g., "binary", "json")
            #         - "topic": Topic to which the message should be published
            #         - "data_source": Source of the data
            #         - "destination_ids": List of destination IDs for the message
            #         - "buffer_key": Optional key for tracking upload stats
            #         - "buffer_size": Size of the buffer for upload stats
            #         - "data_type": Type of data being uploaded
            result = callback({"data": message, **headers})

            if result:
                channel.basic_ack(delivery_tag=method_frame.delivery_tag)
                self.logger.debug(f"Message processed successfully in {queue_name}")
            else:
                # If processing failed, republish with mew priority instead of just nacking
                self.logger.warning(
                    f"Message processing failed in {queue_name}, requeuing with new priority {new_priority}"
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
                        # new_properties["expiration"] = "0"
                        # Above does not worked, as immediate consumer is available,
                        self.logger.info(
                            f"Message expiration time reached, marked as expired {queue_name}"
                        )
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
                    exchange="",  # Use default exchange
                    routing_key=queue_name,
                    body=body,
                    properties=pika.BasicProperties(**new_properties),
                )

        except Exception as e:
            self.logger.error(f"Error processing message in {queue_name}: {e}")
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
                        # new_properties["expiration"] = "0"
                        # Above does not worked, as immediate consumer is available,
                        self.logger.info(
                            f"Message expiration time reached, marked as expired {queue_name}"
                        )
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

    def start_consume(self, callback: Callable) -> None:  # Note in use
        """Start consuming messages with priority handling by RabbitMQ"""
        # Establish initial connection
        if not self._ensure_connection() or not self.rmq_channel:
            raise Exception("Could not establish initial connection")

        self.logger.info(f"Started consuming messages from {self.queue_name}...")

        self.is_consuming = True

        while self.is_consuming:
            try:
                if not self._ensure_connection() or not self.rmq_channel:
                    self.logger.warning("Connection lost, waiting before retry...")
                    time.sleep(1)
                    continue

                # Setup consumer with the callback
                def callback_wrapper(channel, method, properties, body):
                    self._consume_queue_message(
                        callback, channel, method, properties, body
                    )

                self.rmq_channel.basic_consume(
                    queue=self.queue_name,
                    on_message_callback=callback_wrapper,
                    auto_ack=False,  # We'll handle acknowledgments manually
                )

                # Start consuming - this will block until channel or connection is closed
                self.rmq_channel.start_consuming()

            except ConnectionClosedByBroker:
                self.logger.warning("Connection closed by broker, reconnecting...")
                time.sleep(1)
            except AMQPChannelError as e:
                self.logger.error(f"Channel error: {e}")
                time.sleep(1)
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
                time.sleep(1)
                self._setup_connection()

    def stop_consume(self) -> None:  # Note in use
        """Stop consuming messages"""
        self.is_consuming = False

    def close(self) -> None:
        """Close connection"""
        if self.rmq_conn and not self.rmq_conn.is_closed:
            try:
                self.logger.info("Service RabbitMQ shutdown signal, connection closing...")
                self.rmq_conn.close()
                self.logger.info("Connection closed")
            except Exception as e:
                self.logger.error(f"Error closing connection: {e}")
        else:
            self.logger.info("RabbitMQ already cleaned, no active connection")

    def is_healthy(self):
        """
        Check if the service is healthy.
        """
        return hasattr(self, "rmq_conn") and self.rmq_conn and self.rmq_conn.is_open

    def __del__(self):
        """Destructor called by garbage collector to ensure resources are cleaned up, when object is about to be destroyed"""
        try:
            if self.is_healthy():
                self.logger.error(
                    "Destructor called by garbage collector to cleanup RabbitMQ"
                )
                self.close()
        except Exception as e:
            pass
