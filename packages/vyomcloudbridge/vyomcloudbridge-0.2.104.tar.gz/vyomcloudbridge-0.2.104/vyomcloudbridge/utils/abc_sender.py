import abc
import signal
import sys
from vyomcloudbridge.utils.logger_setup import setup_logger


class AbcSender(abc.ABC):
    """
    Abstract base class for services that can send messages to specific destinations.
    All sender implementations should inherit from this class.
    """

    def __init__(self, daemon: bool = False, log_level=None):
        # compulsory fields
        self.name = ""
        self.combine_by_target_id = False

        # class specific
        self.logger = setup_logger(
            name=self.__class__.__module__ + "." + self.__class__.__name__,
            show_terminal=False,
            log_level=log_level,
        )

    @abc.abstractmethod
    def send_message(
        self,
        message,
        message_type,
        data_source,
        target_des_id,
        destination_id,
        source_id,
        topic,
    ):
        """
        Send a message to a specific destination.

        Args:
            destination_id: The identifier of the destination to send the message to
            message: The message content to be sent (can be ROS message, dictionary, or any object)
            message_type: The type of the message being sent

        Returns:
            Implementation-specific result of the send operation
        """
        pass

    def is_healthy(self):
        """
        Check if the sender service is healthy.
        Can be overridden by subclasses to implement specific health checks.

        Returns:
            bool: True if like if all connection and other things are healthy
        """
        return True

    @abc.abstractmethod
    def cleanup(self):
        """
        Clean up resources used by the sender.
        Must be implemented by subclasses.
        This method should handle stopping any background processes,
        closing connections, and releasing any resources.
        """
        pass

    def __del__(self):
        """
        Destructor called by garbage collector to ensure resources are cleaned up
        when the object is about to be destroyed., will just call cleanup
        """
        try:
            self.logger.error(
                "Destructor called by garbage collector to cleanup AbcSender"
            )
            self.cleanup()
        except Exception as e:
            # Cannot log here as logger might be destroyed already
            pass
