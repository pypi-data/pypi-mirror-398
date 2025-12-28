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
from typing import Any, Callable
import time
import threading
from queue import Queue
import signal
import os
from concurrent.futures import ThreadPoolExecutor
from vyomcloudbridge.utils.logger_setup import setup_logger


logger = setup_logger(name=__name__, show_terminal=False)


class ThreadedRabbitMQ:
    def __init__(
        self,
        host: str = "localhost",
        queue_name: str = "data_queue",
        num_threads: int = 10,
    ):
        self.host = host
        self.queue_name = queue_name
        self.num_threads = num_threads
        self.rmq_conn = None
        self.rmq_channel = None
        self.is_consuming = True
        # self._setup_connection()  # Don't set up connection in __init__ when running as service
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
                        heartbeat=600,
                        blocked_connection_timeout=300,
                        socket_timeout=300,
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
                logger.info("ThreadedRabbitMQ connection established")
                return

            except AMQPConnectionError as e:
                if attempt == max_retries - 1:
                    logger.error(
                        f"Failed to connect to ThreadedRabbitMQ after {max_retries} attempts"
                    )
                    raise
                logger.warning(
                    f"ThreadedRabbitMQ connection attempt {attempt + 1} failed, retrying..."
                )
                time.sleep(2**attempt)
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(
                        f"Failed to connect to ThreadedRabbitMQ after {max_retries} attempts"
                    )
                    raise
                logger.warning(
                    f"ThreadedRabbitMQ connection attempt {attempt + 1} failed, retrying..."
                )
                time.sleep(2**attempt)

    def _ensure_connection(self) -> bool:
        """Ensure connection and channel are active and working"""
        try:
            if not self.rmq_conn or self.rmq_conn.is_closed:
                self._setup_connection()
                return True

            if not self.rmq_channel or self.rmq_channel.is_closed:
                logger.info("Closed channel found, re-establishing...")
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
                self.rmq_channel.basic_qos(prefetch_count=1)
                logger.info("Channel re-established successfully")

            return True
        except Exception as e:
            logger.error(f"Failed to ensure connection: {e}")
            self.rmq_conn = None
            self.rmq_channel = None
            return False

    def enqueue_message(self, message: Any, priority: int = 0, expiration: str = None) -> None:
        """Publish message to queue with specified priority (0-10, higher is more priority)"""
        """ expiration is milisecond in string """
        if not self._ensure_connection():
            raise Exception("Could not establish connection")

        # Ensure priority is within bounds
        if priority < 0:
            priority = 0
        elif priority > 10:
            priority = 10
        properties = {
            "delivery_mode": 2,
            "content_type": "application/json",
        }
        if expiration is not None:
            properties["expiration"] = expiration  # 60 seconds TTL
        try:
            self.rmq_channel.basic_publish(
                exchange="",
                routing_key=self.queue_name,
                body=json.dumps(message),
                properties=pika.BasicProperties(**properties),
            )
            message_str = (
                json.dumps(message) if not isinstance(message, str) else message
            )
            truncated_message = (
                (message_str[:100] + "...") if len(message_str) > 100 else message_str
            )
            logger.info(
                f"Published message to queue {self.queue_name} with priority {priority}: {truncated_message}"
            )
        except (
            pika.exceptions.AMQPConnectionError,
            pika.exceptions.AMQPChannelError,
        ) as e:
            logger.error(f"Error publishing message: {e}")
            self._setup_connection()
            self.enqueue_message(message, priority)
        except Exception as e:
            logger.error(f"Error publishing message: {e}")
            self._setup_connection()
            self.enqueue_message(message, priority)

    def _process_message(
        self,
        callback: Callable,
        channel: pika.channel.Channel,
        method_frame: Basic.Deliver,
        properties: pika.BasicProperties,
        body,
    ):
        """Process a single message"""
        try:
            message = json.loads(body)
            queue_name = method_frame.routing_key
            priority = properties.priority if properties.priority is not None else 0
            new_priority = max(priority - 1, 0) if priority < 3 else priority  # TODO

            expiry_info = ""
            if hasattr(properties, "expiration") and properties.expiration:
                expiry_info = f" with expiration {properties.expiration}ms"
            logger.debug(
                f"Processing message from {queue_name} with priority {priority}{expiry_info}"
            )
            result = callback(message)

            if result:
                channel.basic_ack(delivery_tag=method_frame.delivery_tag)
                logger.debug(f"Message processed successfully in {queue_name}")
            else:
                # If processing failed, republish with new priority instead of just nacking
                logger.warning(
                    f"Message processing failed in {queue_name}, requeuing with new priority {new_priority}"
                )
                # First ack the original message
                channel.basic_ack(delivery_tag=method_frame.delivery_tag)

                new_properties = {
                    "priority": new_priority,
                    "content_type": properties.content_type,
                    "delivery_mode": properties.delivery_mode,  # Preserve persistence setting
                }

                if hasattr(properties, "expiration") and properties.expiration:
                    new_properties["expiration"] = properties.expiration

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

        except Exception as e:
            logger.error(f"Error processing message in {queue_name}: {e}")
            try:
                priority = properties.priority if properties.priority is not None else 0
                logger.warning(
                    f"Error processing message, requeuing with new priority {new_priority}"
                )
                # First ack the original message
                channel.basic_ack(delivery_tag=method_frame.delivery_tag)

                new_properties = {
                    "priority": new_priority,
                    "content_type": properties.content_type,
                    "delivery_mode": properties.delivery_mode,  # Preserve persistence setting
                }

                if hasattr(properties, "expiration") and properties.expiration:
                    new_properties["expiration"] = properties.expiration

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
                logger.error(
                    f"Failed to republish message with new priority: {republish_error}"
                )
                channel.basic_nack(delivery_tag=method_frame.delivery_tag, requeue=True)

    def _worker(self, callback: Callable):
        """Worker thread function to process messages"""
        # Create a dedicated connection for this worker
        connection = None
        channel = None

        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=self.host)
            )
            channel = connection.channel()

            # Set QoS
            channel.basic_qos(prefetch_count=1)

            # Setup consumer with the callback
            def callback_wrapper(ch, method, properties, body):
                self._process_message(callback, ch, method, properties, body)

            # Start consuming
            channel.basic_consume(
                queue=self.queue_name,
                on_message_callback=callback_wrapper,
                auto_ack=False,  # We'll handle acknowledgments manually
            )
            logger.info(f"Worker thread started for {self.queue_name}")
            while self.is_consuming:
                # Process messages for a short time before checking if we should stop
                connection.process_data_events(time_limit=1.0)

        except (ConnectionClosedByBroker, AMQPChannelError) as e:
            logger.error(f"Connection error in worker: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in worker: {e}")
        finally:
            if channel is not None and channel.is_open:
                try:
                    channel.close()
                except:
                    pass

            if connection is not None and connection.is_open:
                try:
                    connection.close()
                except:
                    pass

    def consume(self, callback: Callable) -> None:
        """Start consuming messages with multiple worker threads

        Args:
            callback: Function to process messages (should return True for success, False for failure)
        """
        logger.info(
            f"Starting consumption from {self.queue_name} with {self.num_threads} threads"
        )

        # Create thread pool for workers
        with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            futures = [
                executor.submit(self._worker, callback) for _ in range(self.num_threads)
            ]

            # Setup signal handler for graceful shutdown
            def signal_handler(signum, frame):
                logger.info("Shutdown signal received, stopping workers...")
                self.is_consuming = False

            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)

            try:
                # Wait for all futures to complete
                for future in futures:
                    future.result()
            except KeyboardInterrupt:
                logger.info("Keyboard interrupt received, initiating shutdown...")
                self.is_consuming = False

    def close(self) -> None:
        """Close connection"""
        if self.rmq_conn and not self.rmq_conn.is_closed:
            try:
                logger.info("sevice RbiitMQ shutdown signal, connection closing...")
                self.rmq_conn.close()
                logger.info("Connection closed")
            except Exception as e:
                logger.error(f"Error closing connection: {e}")
        else:
            ("ThreadedRabbitMQ already cleaned, no active connection")

    def is_healthy(self):
        """
        Check if the service is healthy.
        """
        return (
            hasattr(self, "rmq_conn") and self.rmq_conn and self.rmq_conn.is_open
        )

    def __del__(self):
        """Destructor called by garbage collector to ensure resources are cleaned up, when object is about to be destroyed"""
        try:
            logger.error(
                "Destructor called by garbage collector to cleanup ThreadedRabbitMQ"
            )
            self.close()
        except Exception as e:
            pass
