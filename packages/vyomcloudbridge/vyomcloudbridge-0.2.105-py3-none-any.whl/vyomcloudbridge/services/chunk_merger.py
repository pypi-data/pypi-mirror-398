import json
from datetime import datetime, timezone
import time
from vyomcloudbridge.services.rabbit_queue.queue_main import RabbitMQ
from vyomcloudbridge.utils.common import ServiceAbstract
from vyomcloudbridge.utils.configs import Configs
from vyomcloudbridge.utils.common import get_mission_upload_dir
from vyomcloudbridge.constants.constants import (
    CHUNK_MERGER_DT_SRC,
    default_project_id,
    default_mission_id,
    data_buffer_key,
)


class ChunkMerger(ServiceAbstract):
    """
    Service that processes file chunks that have been uploaded to S3 storage.
    It publishes messages to a RabbitMQ queue to trigger the merging process
    for files that were uploaded in chunks.
    """

    def __init__(self, log_level=None):
        """
        Initialize the ChunkMerger service with RabbitMQ connection.
        """
        super().__init__(log_level=log_level)
        self.rabbit_mq = RabbitMQ(log_level=log_level)
        self.machine_config = Configs.get_machine_config()
        self.machine_id = self.machine_config.get("machine_id", "-") or "-"
        self.organization_id = self.machine_config.get("organization_id", "-") or "-"
        self.priority = 1  # Message priority level for RabbitMQ
        self.is_running = False

    def on_chunk_file_arrive(self, s3_key: str) -> bool:
        """
        Publish a message to the RabbitMQ queue when a new file chunk arrives.

        Args:
            s3_key: The S3 storage key of the uploaded property file of chunks

        Returns:
            bool: True if message was published successfully, False otherwise
        """
        try:
            self.logger.debug(f"Enqueueing chunk merging task key: {s3_key}")

            now = datetime.now(timezone.utc)
            date_str = now.strftime("%Y-%m-%d")
            timestamp = int(time.time() * 1000)
            # mission_upload_dir = f"{self.organization_id}/{default_project_id}/{date_str}/chunk_merger/{self.machine_id}" # TODO
            mission_upload_dir: str = get_mission_upload_dir(
                organization_id=self.organization_id,
                machine_id=self.machine_id,
                mission_id=default_mission_id,
                data_source=CHUNK_MERGER_DT_SRC,
                date=date_str,
                project_id=default_project_id,
            )
            data = json.dumps(
                {
                    "s3_key": s3_key,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            headers = {
                "topic": f"{mission_upload_dir}/{timestamp}.json",
                "message_type": "json",
                "destination_ids": ["s3"],
                "data_source": CHUNK_MERGER_DT_SRC,
                # meta data
                "buffer_key": data_buffer_key,
                "buffer_size": 0,  # Size is 0 as we're just sending a reference
                "data_type": "json",
            }

            # Publish the message with the specified priority
            self.rabbit_mq.enqueue_message(
                message=data, headers=headers, priority=self.priority
            )
            self.logger.info(f"Chunk merging task enqueued for: {s3_key}")
        except Exception as e:
            self.logger.error(
                f"Error publishing chunk merger notification: {str(e)}", exc_info=True
            )
            return False

    def start(self):
        """
        Start the ChunkMerger service and keep it running.
        The service primarily waits for on_chunk_file_arrive calls.
        """
        try:
            self.is_running = True
            self.logger.info("Starting ChunkMerger service")
            self.logger.info("Started ChunkMerger service!")
            while self.is_running:
                time.sleep(10)

        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt, shutting down...")
        except Exception as e:
            self.logger.error(f"Error in ChunkMerger service: {str(e)}", exc_info=True)
            raise
        finally:
            self.stop()

    def stop(self):
        """
        Close connections and stop the service.
        Should be called when shutting down the application.
        """
        self.is_running = False
        if hasattr(self, "rabbit_mq"):
            self.rabbit_mq.close()
        self.logger.info("ChunkMerger service stopped")

    def cleanup(self):
        pass

    def is_healthy(self):
        """
        Check if the service is healthy.

        Returns:
            bool: True if the service is running and RabbitMQ connection is healthy
        """
        return self.is_running and self.rabbit_mq.is_healthy()

    def __del__(self):
        """Destructor called by garbage collector to ensure resources are cleaned up, when object is about to be destroyed"""
        try:
            if self.is_healthy():
                self.logger.error(
                    "Destructor called by garbage collector to cleanup ChunkMerger"
                )
                self.stop()
        except Exception as e:
            pass


def main():
    """Example of how to use the ChunkMerger"""
    print("Starting ChunkMerger service example")
    chunk_merger = ChunkMerger()

    try:
        # Example S3 key for a json property_file that needs to be merged
        s3_key = "1/2025-03-21/all/camera1/12/301389/image/sample_image.json"
        chunk_merger.on_chunk_file_arrive(s3_key)
        print(f"Message published successfully")
    finally:
        # Ensure service is properly stopped
        chunk_merger.stop()

    print("Completed ChunkMerger service example")


if __name__ == "__main__":
    main()
