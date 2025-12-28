import logging
from awscrt import io, mqtt
from awsiot import mqtt_connection_builder
import time
import os
from vyomcloudbridge.services.mqtt.machine_client import MqttMachineClient
from vyomcloudbridge.utils.logger_setup import setup_logger
from vyomcloudbridge.utils.configs import Configs
import json
import threading

log_dir = os.path.expanduser("/var/log/vyomcloudbridge")
logger = setup_logger(log_dir, __name__, show_terminal=False, log_level=logging.INFO)


def message_callback(topic, payload):
    try:
        logger.info(f"Received message in callback '{topic}': {json.loads(payload)}")
    except Exception as e:
        logger.error("Error in calling callback")


def publish_message_async(callback, topic, message):
    threading.Thread(
        target=callback, args=(topic, json.dumps(message), False), daemon=True
    ).start()


def main():
    try:
        # Connect to AWS IoT Core
        client = MqttMachineClient(message_callback = message_callback)
        machine_config = Configs.get_machine_config()
        machine_id = machine_config.get("machine_id", "-") or "-"

        # Subscribe to a test topic
        subscribe_topic_1 = f"vyom-mqtt-msg/{machine_id}/#"
        # subscribe_topic_2 = f"vyom-mqtt-msg/{machine_id}/#"
        client.subscribe_to_topic(subscribe_topic_1)
        logger.info("Listening for messages... Press Ctrl+C to exit")

        # Publish a test message
        publish_topic_1 = f"1/2025-02-11/33/44/{machine_id}/99/10/hello.json"
        # publish_topic_2 = (
        #     f"1/_uploads_/12/camera1/2/3/JPEG_example_JPG_RIP_001.json"
        # )
        message_connect = {
            "type": "CONNECT_DRONE",
            "data": {"droneId": machine_id, "timestamp": "number", "parameters": {}},
        }

        while True:
            # logger.info("publishing messages...")
            # publish_message_async(client.publish_message, publish_topic_1, message_connect)
            # client.publish_message(publish_topic_1, json.dumps(message_connect), False)
            time.sleep(10)

    except KeyboardInterrupt:
        logger.info("\nExiting...")
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        import traceback

        traceback.print_exc()
    finally:
        client.close_connection()


if __name__ == "__main__":
    main()
