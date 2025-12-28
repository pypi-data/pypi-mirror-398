import pika
import pika.channel
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Union
import time
from vyomcloudbridge.utils.common import ServiceAbstract
from vyomcloudbridge.utils.configs import Configs
from vyomcloudbridge.utils.logger_setup import setup_logger
from vyomcloudbridge.constants.constants import RESERVED_KEYS, DEFAULT_RABBITMQ_URL


class RootStore(ServiceAbstract):  # Not in use
    """
    A service that maintains generic data using RabbitMQ as a persistent store.
    Each key has its own queue in RabbitMQ that stores the latest state of its data.
    """

    def __init__(self, log_level=None):
        """
        Initialize the generic data service with RabbitMQ connection.
        """
        super().__init__(log_level=log_level)
        self.host: str = "localhost"
        self.rabbitmq_url = DEFAULT_RABBITMQ_URL
        self.publish_interval = 5
        self.publish_error_delay = 10
        self.rmq_conn = None  # rabbit mq connection
        self.rmq_channel = None
        self.machine_config = Configs.get_machine_config()
        self.machine_id = self.machine_config.get("machine_id", "-") or "-"

    def _setup_connection(self):
        """Set up RabbitMQ connection and declare the exchange for data."""
        try:
            # Establish connection
            self.rmq_conn = pika.BlockingConnection(
                pika.URLParameters(self.rabbitmq_url)
            )
            self.rmq_channel = self.rmq_conn.channel()
            self.rmq_channel.exchange_declare(
                exchange="general_store_exchange", exchange_type="direct", durable=True
            )

            self.logger.info("RabbitMQ connection established successfully")
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
                    exchange="general_store_exchange",
                    exchange_type="direct",
                    durable=True,
                )
                self.logger.info("Channel re-established successfully")

            return True
        except Exception as e:
            self.logger.error(f"Failed to ensure connection: {e}")
            self.rmq_conn = None
            self.rmq_channel = None
            return False

    def _validate_key(self, key: str) -> bool:
        """
        Validate that the provided key is not in the reserved list.

        Args:
            key: The queue key to validate

        Returns:
            bool: True if valid, False if reserved

        Raises:
            ValueError: If the key is reserved
        """
        if key in RESERVED_KEYS:
            raise ValueError(f"Key '{key}' is reserved and cannot be used")
        return True

    def _ensure_queue(self, key: str):
        """
        Ensure that a queue exists for the given key.

        Args:
            key: The queue name to ensure exists
        """
        if not self._ensure_connection() or not self.rmq_channel:
            raise Exception("Could not establish connection")

        self._validate_key(key)

        queue_name = key
        self.rmq_channel.queue_declare(queue=queue_name, durable=True)

        # Create a dedicated exchange for this queue if needed
        exchange_name = f"{queue_name}_exchange"
        self.rmq_channel.exchange_declare(
            exchange=exchange_name, exchange_type="direct", durable=True
        )

        self.rmq_channel.queue_bind(
            exchange=exchange_name, queue=queue_name, routing_key=queue_name
        )

    def set_data(self, key: str, data: Any):
        """
        Set data in the specified queue without clearing existing data.
        This adds a new message to the queue without deleting previous messages.

        Args:
            key: The queue name to set data for
            data: Any JSON serializable data to store (dict, list, int, str, etc.)
        """
        try:
            if not self._ensure_connection() or not self.rmq_channel:
                raise Exception("Could not establish connection")

            self.logger.debug(f"Setting data for key {key}")

            self._validate_key(key)

            # Ensure queue exists
            self._ensure_queue(key)

            # Clear existing data
            self.delete_data(key)

            # Prepare data for storage
            # If it's a dict, add timestamp directly
            if isinstance(data, dict):
                data_with_metadata = data.copy()
                data_with_metadata["_timestamp"] = datetime.now(
                    timezone.utc
                ).isoformat()
                data_with_metadata["_machine_id"] = self.machine_id
            else:
                # For non-dict values, wrap them in a structure that preserves their type
                data_with_metadata = {
                    "_value_type": type(data).__name__,
                    "_value": data,
                    "_timestamp": datetime.now(timezone.utc).isoformat(),
                    "_machine_id": self.machine_id,
                }

            # Publish the new data without deleting existing data
            self.rmq_channel.basic_publish(
                exchange="",
                routing_key=key,
                body=json.dumps(data_with_metadata),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # make message persistent
                    content_type="application/json",
                ),
            )
            self.logger.debug(f"Set data for key: {key}")
        except ValueError as e:
            # Re-raise validation errors
            raise
        except Exception as e:
            self.logger.error(f"Error setting data in {key}: {str(e)}")

    def get_data(self, key: str) -> Optional[Any]:
        """
        Get data from the specified queue.

        Args:
            key: The queue name to get data from

        Returns:
            Data (any type) or None if not found
        """
        try:
            if not self._ensure_connection() or not self.rmq_channel:
                raise Exception("Could not establish connection")

            self._validate_key(key)

            # Ensure queue exists
            self._ensure_queue(key)

            method_frame, _, body = self.rmq_channel.basic_get(
                queue=key, auto_ack=False
            )

            data = None
            if method_frame:
                data = json.loads(body.decode("utf-8"))
                # If the data has the special _value_type field, extract the actual value
                if (
                    isinstance(data, dict)
                    and "_value_type" in data
                    and "_value" in data
                ):
                    data = data["_value"]
                # Put the message back in the queue since we're just reading
                self.rmq_channel.basic_nack(
                    delivery_tag=method_frame.delivery_tag, requeue=True
                )
                self.logger.debug(f"Retrieved data from queue: {key}")
            return data
        except ValueError as e:
            # Re-raise validation errors
            raise
        except Exception as e:
            self.logger.error(f"Error getting data from {key}: {str(e)}")
            return None

    def update_data(
        self, key: str, data: Any
    ):  # Depreciated, will not be removed in future
        """
        Update data in the specified queue.
        This first clears any existing data in the queue.
        Can store any type of data that is JSON serializable.

        Args:
            key: The queue name to update
            data: Any JSON serializable data to store (dict, list, int, str, etc.)
        """
        try:
            if not self._ensure_connection() or not self.rmq_channel:
                raise Exception("Could not establish connection")

            self.logger.info(f"updating data for key {key}")

            self._validate_key(key)

            # Ensure queue exists
            self._ensure_queue(key)

            # Clear existing data
            self.delete_data(key)

            # Prepare data for storage
            # If it's a dict, add timestamp directly
            if isinstance(data, dict):
                data_with_metadata = data.copy()
                data_with_metadata["_timestamp"] = datetime.now(
                    timezone.utc
                ).isoformat()
                data_with_metadata["_machine_id"] = self.machine_id
            else:
                # For non-dict values, wrap them in a structure that preserves their type
                data_with_metadata = {
                    "_value_type": type(data).__name__,
                    "_value": data,
                    "_timestamp": datetime.now(timezone.utc).isoformat(),
                    "_machine_id": self.machine_id,
                }

            # Publish the new data
            self.rmq_channel.basic_publish(
                exchange="",
                routing_key=key,
                body=json.dumps(data_with_metadata),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # make message persistent
                    content_type="application/json",
                ),
            )
            self.logger.info(f"Updated data for key: {key}")
        except ValueError as e:
            # Re-raise validation errors
            raise
        except Exception as e:
            self.logger.error(f"Error updating data in {key}: {str(e)}")

    def delete_data(self, key: str):
        """
        Delete all data from the specified queue.

        Args:
            key: The queue name to delete data from
        """
        try:
            if not self._ensure_connection() or not self.rmq_channel:
                raise Exception("Could not establish connection")

            self._validate_key(key)

            # Clear all messages from the queue
            while True:
                method_frame, _, _ = self.rmq_channel.basic_get(
                    queue=key, auto_ack=True
                )
                if not method_frame:
                    break

            self.logger.debug(f"Deleted all data from queue: {key}")
        except ValueError as e:
            # Re-raise validation errors
            raise
        except Exception as e:
            self.logger.error(f"Error deleting data from {key}: {str(e)}")

    def start(self):
        """
        Start the service and maintain connection.
        """
        try:
            self.logger.info("Starting general store service")
            self.is_running = True

            # Setup initial connection
            self._ensure_connection()

            # Keep the main thread alive to handle KeyboardInterrupt
            while self.is_running:
                time.sleep(10)
                # Periodically check connection
                if not self.rmq_conn or self.rmq_conn.is_closed:
                    self._setup_connection()

        except KeyboardInterrupt:
            self.is_running = False
            self.logger.info("Received keyboard interrupt, shutting down...")
        except Exception as e:
            self.logger.error(f"Error running service: {str(e)}", exc_info=True)
            raise

    def stop(self):
        """
        Close connections and stop the service.
        Should be called when shutting down the application.
        """
        self.is_running = False
        if self.rmq_conn and self.rmq_conn.is_open:
            try:
                self.rmq_conn.close()
                self.logger.info("General store service stopped")
            except Exception as e:
                self.logger.error(f"Error closing connection: {str(e)}")

    def cleanup(self):
        """
        Cleanup the service.
        """
        try:
            if self.rmq_conn and self.rmq_conn.is_open:
                self.rmq_conn.close()
                self.logger.info("General store service stopped")
            self.logger.info("General store service cleaned up")
        except Exception as e:
            self.logger.error(f"Error closing connection: {str(e)}")

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

    def __del__(self):
        """Destructor called by garbage collector to ensure resources are cleaned up, when object is about to be destroyed"""
        try:
            if self.is_healthy():
                self.logger.error(
                    "Destructor called by garbage collector to cleanup RootStore"
                )
                self.stop()
        except Exception as e:
            pass


logger = setup_logger(name=__name__, show_terminal=False, log_level=logging.INFO)


def _get_machine_id() -> str:
    """Get the machine ID from config or return a default value."""
    try:
        machine_config = Configs.get_machine_config()
        return machine_config.get("machine_id", "-") or "-"
    except Exception as e:
        logger.error(f"Failed to get machine ID: {str(e)}")
        return "-"


def _validate_key(key: str) -> bool:
    """
    Validate that the provided key is not in the reserved list.

    Args:
        key: The queue key to validate

    Returns:
        bool: True if valid

    Raises:
        ValueError: If the key is reserved
    """
    if key in RESERVED_KEYS:
        raise ValueError(f"Key '{key}' is reserved and cannot be used")
    return True


def _setup_connection(rabbitmq_url: str = DEFAULT_RABBITMQ_URL):
    """
    Set up a new RabbitMQ connection and channel.

    Args:
        rabbitmq_url: The RabbitMQ connection URL

    Returns:
        tuple: (connection, channel) for RabbitMQ
    """
    try:
        rmq_conn = pika.BlockingConnection(pika.URLParameters(rabbitmq_url))
        rmq_channel = rmq_conn.channel()

        # Declare general exchange
        rmq_channel.exchange_declare(
            exchange="general_store_exchange", exchange_type="direct", durable=True
        )

        logger.debug("RabbitMQ connection established successfully")
        return rmq_conn, rmq_channel
    except Exception as e:
        logger.error(f"Failed to initialize RabbitMQ connection: {str(e)}")
        raise


def _ensure_queue(channel: pika.channel.Channel, key: str):
    """
    Ensure that a queue exists for the given key.

    Args:
        channel: RabbitMQ channel
        key: The queue name to ensure exists
    """
    _validate_key(key)

    queue_name = key
    channel.queue_declare(queue=queue_name, durable=True)

    # Create a dedicated exchange for this queue
    exchange_name = f"{queue_name}_exchange"
    channel.exchange_declare(
        exchange=exchange_name, exchange_type="direct", durable=True
    )

    channel.queue_bind(exchange=exchange_name, queue=queue_name, routing_key=queue_name)


def get_data(key: str, rabbitmq_url: str = DEFAULT_RABBITMQ_URL) -> Optional[Any]:
    """
    Get data from the specified queue. Creates a new connection for this operation.

    Args:
        key: The queue name to get data from
        rabbitmq_url: The RabbitMQ connection URL

    Returns:
        Data (any type) or None if not found
    """
    rmq_conn = None
    try:
        logger.info(f"Getting data for key: {key}")
        _validate_key(key)

        # Setup connection
        rmq_conn, rmq_channel = _setup_connection(rabbitmq_url)

        # Ensure queue exists
        _ensure_queue(rmq_channel, key)

        # Get data from queue
        method_frame, _, body = rmq_channel.basic_get(queue=key, auto_ack=False)

        data = None
        if method_frame:
            data = json.loads(body.decode("utf-8"))
            # If the data has the special _value_type field, extract the actual value
            if isinstance(data, dict) and "_value_type" in data and "_value" in data:
                data = data["_value"]
            # Put the message back in the queue since we're just reading
            rmq_channel.basic_nack(delivery_tag=method_frame.delivery_tag, requeue=True)
            logger.info(f"Retrieved data from queue: {key}")
        else:
            logger.info(f"No data found in queue: {key}")

        return data
    except ValueError as e:
        # Re-raise validation errors
        logger.error(f"Validation error for key {key}: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error getting data from {key}: {str(e)}")
        return None
    finally:
        # Clean up connection
        if rmq_conn and rmq_conn.is_open:
            try:
                rmq_conn.close()
                logger.debug(f"Connection closed after get_data for key: {key}")
            except Exception as e:
                logger.error(f"Error closing connection: {str(e)}")


def set_data(key: str, data: Any, rabbitmq_url: str = DEFAULT_RABBITMQ_URL) -> bool:
    """
    Set data in the specified queue without clearing existing data.
    This adds a new message to the queue without deleting previous messages.
    Creates a new connection for this operation.

    Args:
        key: The queue name to set data for
        data: Any JSON serializable data to store (dict, list, int, str, etc.)
        rabbitmq_url: The RabbitMQ connection URL

    Returns:
        bool: True if successful, False otherwise
    """
    rmq_conn = None
    try:
        logger.debug(f"Setting data for key: {key}")
        _validate_key(key)

        # Setup connection
        rmq_conn, rmq_channel = _setup_connection(rabbitmq_url)

        # Ensure queue exists
        _ensure_queue(rmq_channel, key)

        # Clear existing data
        delete_queue_data(rmq_channel, key)

        # Get machine ID
        machine_id = _get_machine_id()

        # Prepare data for storage
        if isinstance(data, dict):
            data_with_metadata = data.copy()
            data_with_metadata["_timestamp"] = datetime.now(timezone.utc).isoformat()
            data_with_metadata["_machine_id"] = machine_id
        else:
            # For non-dict values, wrap them in a structure that preserves their type
            data_with_metadata = {
                "_value_type": type(data).__name__,
                "_value": data,
                "_timestamp": datetime.now(timezone.utc).isoformat(),
                "_machine_id": machine_id,
            }

        # Publish the new data without deleting existing data
        rmq_channel.basic_publish(
            exchange="",
            routing_key=key,
            body=json.dumps(data_with_metadata),
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
                content_type="application/json",
            ),
        )
        logger.debug(f"Set data for key: {key}")
        return True
    except ValueError as e:
        # Re-raise validation errors
        logger.error(f"Validation error for key {key}: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error setting data in {key}: {str(e)}")
        return False
    finally:
        # Clean up connection
        if rmq_conn and rmq_conn.is_open:
            try:
                rmq_conn.close()
                logger.debug(f"Connection closed after set_data for key: {key}")
            except Exception as e:
                logger.error(f"Error closing connection: {str(e)}")


def update_data(key: str, data: Any, rabbitmq_url: str = DEFAULT_RABBITMQ_URL) -> bool:
    """
    Update data in the specified queue.
    This first clears any existing data in the queue.
    Creates a new connection for this operation.

    Args:
        key: The queue name to update
        data: Any JSON serializable data to store (dict, list, int, str, etc.)
        rabbitmq_url: The RabbitMQ connection URL

    Returns:
        bool: True if successful, False otherwise
    """
    rmq_conn = None
    try:
        logger.info(f"Updating data for key: {key}")
        _validate_key(key)

        # Setup connection
        rmq_conn, rmq_channel = _setup_connection(rabbitmq_url)

        # Ensure queue exists
        _ensure_queue(rmq_channel, key)

        # Clear existing data
        delete_queue_data(rmq_channel, key)

        # Get machine ID
        machine_id = _get_machine_id()

        # Prepare data for storage
        if isinstance(data, dict):
            data_with_metadata = data.copy()
            data_with_metadata["_timestamp"] = datetime.now(timezone.utc).isoformat()
            data_with_metadata["_machine_id"] = machine_id
        else:
            # For non-dict values, wrap them in a structure that preserves their type
            data_with_metadata = {
                "_value_type": type(data).__name__,
                "_value": data,
                "_timestamp": datetime.now(timezone.utc).isoformat(),
                "_machine_id": machine_id,
            }

        # Publish the new data
        rmq_channel.basic_publish(
            exchange="",
            routing_key=key,
            body=json.dumps(data_with_metadata),
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
                content_type="application/json",
            ),
        )
        logger.info(f"Updated data for key: {key}")
        return True
    except ValueError as e:
        # Re-raise validation errors
        logger.error(f"Validation error for key {key}: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error updating data in {key}: {str(e)}")
        return False
    finally:
        # Clean up connection
        if rmq_conn and rmq_conn.is_open:
            try:
                rmq_conn.close()
                logger.debug(f"Connection closed after update_data for key: {key}")
            except Exception as e:
                logger.error(f"Error closing connection: {str(e)}")


def delete_queue_data(channel: pika.channel.Channel, key: str):
    """
    Internal function to delete all data from a queue using an existing channel.

    Args:
        channel: RabbitMQ channel
        key: The queue name to delete data from
    """
    _validate_key(key)

    # Clear all messages from the queue
    message_count = 0
    while True:
        method_frame, _, _ = channel.basic_get(queue=key, auto_ack=True)
        if not method_frame:
            break
        message_count += 1

    if message_count > 0:
        logger.info(f"Cleared {message_count} messages from queue: {key}")
    else:
        logger.info(f"Queue {key} was already empty")


def delete_data(key: str, rabbitmq_url: str = DEFAULT_RABBITMQ_URL) -> bool:
    """
    Delete all data from the specified queue.
    Creates a new connection for this operation.

    Args:
        key: The queue name to delete data from
        rabbitmq_url: The RabbitMQ connection URL

    Returns:
        bool: True if successful, False otherwise
    """
    rmq_conn = None
    try:
        logger.info(f"Deleting data from key: {key}")
        _validate_key(key)

        # Setup connection
        rmq_conn, rmq_channel = _setup_connection(rabbitmq_url)

        # Ensure queue exists
        _ensure_queue(rmq_channel, key)

        # Delete data from queue
        delete_queue_data(rmq_channel, key)

        logger.info(f"Deleted all data from queue: {key}")
        return True
    except ValueError as e:
        # Re-raise validation errors
        logger.error(f"Validation error for key {key}: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error deleting data from {key}: {str(e)}")
        return False
    finally:
        # Clean up connection
        if rmq_conn and rmq_conn.is_open:
            try:
                rmq_conn.close()
                logger.debug(f"Connection closed after delete_data for key: {key}")
            except Exception as e:
                logger.error(f"Error closing connection: {str(e)}")


def main():
    """Example of how to use the RootStore"""
    print("Starting general root store service example")
    # from vyomcloudbridge.services.root_store import RootStore
    root_store = RootStore()

    try:
        # Example: Store user details
        unset_key_example = root_store.get_data("unset_key_example")
        print(f"Retrieved user: {unset_key_example}")

        user_data = {
            "id": 1,
            "name": "Test User",
            "email": "testuser@example.com",
            "role": "operator",
        }
        root_store.set_data("user_details", user_data)

        # Retrieve the stored data
        retrieved_user = root_store.get_data("user_details")
        print(f"Retrieved user: {retrieved_user}")

        # Update with new data
        new_user_data = {
            "id": 2,
            "name": "Another User",
            "email": "another@example.com",
            "role": "admin",
        }
        root_store.set_data("user_details", new_user_data)

        # Retrieve the updated data
        updated_user = root_store.get_data("user_details")
        print(f"Updated user: {updated_user}")

        # Delete the data
        root_store.delete_data("user_details")

        # Verify deletion
        after_delete = root_store.get_data("user_details")
        print(f"After delete: {after_delete}")

        # Try to use a reserved key (should raise ValueError)
        try:
            print(f"Try to use a reserved key (should expect ValueError).....")
            root_store.set_data("current_user", user_data)
        except ValueError as e:
            print(f"Expected error: {e}")

        # Store different types of data
        config_data = {"theme": "dark", "notifications": True, "auto_update": False}
        root_store.set_data("app_config", config_data)

        # Retrieve the config data
        retrieved_config = root_store.get_data("app_config")
        print(f"Retrieved config: {retrieved_config}")

        # Store an integer value
        root_store.set_data("temp_id", 2)
        temp_data = root_store.get_data("temp_id")
        print(f"Retrieved temp_data: {temp_data}")

        # Store a string
        root_store.set_data("message", "Hello, RabbitMQ!")
        message = root_store.get_data("message")
        print(f"Retrieved message: {message}")

        # Store a list
        root_store.set_data("colors", ["red", "green", "blue"])
        colors = root_store.get_data("colors")
        print(f"Retrieved colors: {colors}")

        location = {
            "lat": 76.987934,
            "long": 76.937954,
            "alt": 930,
            "timestamp": "93u4983",
        }
        health = {"status": 1, "message": ""}
        root_store.set_data("location", location)
        root_store.set_data("health", health)
    except Exception as e:
        print("Error occured -", {str(e)})
    finally:
        # Clean up
        root_store.cleanup()

    # try:
    #     user_key = "user_data"
    #     # First data
    #     user_data = "Akash"
    #     update_data(user_key, user_data)  # Use update_data instead of set_data
    #     retrieved_user = get_data(user_key)
    #     print(f"Retrieved user_data 1: {retrieved_user}")

    #     # Second data
    #     user_data = {"id": 3, "name": "Akash", "age": 25}
    #     update_data(user_key, user_data)  # Use update_data instead of set_data
    #     retrieved_user = get_data(user_key)
    #     print(f"Retrieved user_data 2: {retrieved_user}")

    #     # Third data
    #     user_data = 3
    #     update_data(user_key, user_data)  # Use update_data instead of set_data
    #     retrieved_user = get_data(user_key)
    #     print(f"Retrieved user_data 3: {retrieved_user}")
    # except Exception as e:
    #     print("Error occured -", {str(e)})
    #     pass


if __name__ == "__main__":
    main()
