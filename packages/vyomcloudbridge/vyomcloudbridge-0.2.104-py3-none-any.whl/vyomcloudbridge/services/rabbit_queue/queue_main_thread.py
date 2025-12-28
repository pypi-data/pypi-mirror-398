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
from vyomcloudbridge.constants.constants import main_data_queue


class ThreadedRabbitMQ:  # Note in use
    def __init__(
        self,
        host: str = "localhost",
        queue_name: str = main_data_queue,
        num_threads: int = 10,
        log_level=None,
    ):
        self.logger = setup_logger(name=__name__, show_terminal=False, log_level=log_level)
        self.host = host
        self.queue_name = queue_name
        self.num_threads = num_threads
        self.is_consuming = False

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

    def _worker(self, callback: Callable):  # Note in use
        """Worker thread function to process messages"""
        # Create a dedicated connection for this worker
        rmq_conn = None
        rmq_channel = None

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
                self._consume_queue_message(callback, ch, method, properties, body)

            # Start consuming
            rmq_channel.basic_consume(
                queue=self.queue_name,
                on_message_callback=callback_wrapper,
                auto_ack=False,  # We'll handle acknowledgments manually
            )
            self.logger.info(f"Worker thread started for {self.queue_name}")
            while self.is_consuming:
                # Process messages for a short time before checking if we should stop
                rmq_conn.process_data_events(time_limit=1.0)

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

            if rmq_conn is not None and rmq_conn.is_open:
                try:
                    rmq_conn.close()
                except:
                    pass

    def start_consume(self, callback: Callable) -> None:  # Note in use
        """Start consuming messages with multiple worker threads

        Args:
            callback: Function to process messages (should return True for success, False for failure)
        """
        self.logger.info(
            f"Starting consumption from {self.queue_name} with {self.num_threads} threads"
        )
        self.is_consuming = True

        # Create thread pool for workers
        with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            futures = [
                executor.submit(self._worker, callback) for _ in range(self.num_threads)
            ]

            # Setup signal handler for graceful shutdown
            def signal_handler(signum, frame):
                self.logger.info("Shutdown signal received, stopping workers...")
                self.is_consuming = False

            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)

            try:
                # Wait for all futures to complete
                for future in futures:
                    future.result()
            except KeyboardInterrupt:
                self.logger.info("Keyboard interrupt received, initiating shutdown...")
                self.is_consuming = False

    def stop_consume(self) -> None:  # Note in use
        """Close connection"""
        self.is_consuming = False

    def close(self) -> None:
        """Close connection"""
        self.is_consuming = False
        pass

    def is_healthy(self):
        """
        Check if the service is healthy.
        """
        return True
        # return (
        #     hasattr(self, "rmq_conn") and self.rmq_conn and self.rmq_conn.is_open
        # )

    def __del__(self):
        """Destructor called by garbage collector to ensure resources are cleaned up, when object is about to be destroyed"""
        try:
            self.logger.error(
                "Destructor called by garbage collector to cleanup ThreadedRabbitMQ"
            )
            self.close()
        except Exception as e:
            pass
