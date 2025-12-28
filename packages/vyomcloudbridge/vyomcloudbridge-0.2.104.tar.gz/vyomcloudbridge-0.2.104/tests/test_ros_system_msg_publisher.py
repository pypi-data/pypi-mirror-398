import sys
import os
import random
import string
import json

# Add the directory containing ros_system_msg_publisher.py to the sys.path
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../vyomcloudbridge/utils"))
)

from vyomcloudbridge.utils.ros_system_msg_publisher import RosSystemMsgPublisher


def generate_random_data(msg_type):
    """
    Generates random data for each message type to facilitate testing.
    """
    data = {}

    if msg_type == "Access":
        data["encrypted"] = "".join(
            random.choices(string.ascii_letters + string.digits, k=16)
        )

    elif msg_type == "Accessinfo":
        data["end_time"] = random.randint(1600000000, 1700000000)  # Random timestamp
        data["current_date"] = random.randint(
            1600000000, 1700000000
        )  # Random timestamp
        data["user_id"] = random.randint(1000, 9999)

    elif msg_type == "Ack":
        data["msgid"] = "".join(
            random.choices(string.ascii_letters + string.digits, k=8)
        )
        data["chunk_id"] = random.randint(1, 100)

    elif msg_type == "Auth":
        data["auth_key"] = "".join(
            random.choices(string.ascii_letters + string.digits, k=32)
        )

    elif msg_type == "Dvid":
        data["device_id"] = random.randint(1000, 5000)

    return data


def get_input_data():
    """
    Prompts the user for input or generates random data for each message type.
    """
    # Define the possible message types
    message_types = ["Access", "Accessinfo", "Ack", "Auth", "Dvid"]
    input_data = []

    # Ask user if they want to enter values manually or use random values
    use_random = (
        input("Do you want to use random values for testing? [Y/n]: ").strip().lower()
        == "y"
    )

    # Loop through each message type and prompt the user for data or generate random data
    for msg_type in message_types:
        print(
            f"\nEnter data for message type: {msg_type}"
            if not use_random
            else f"\nGenerating random data for message type: {msg_type}"
        )

        # If using random values, generate the data
        if use_random:
            msg_data = generate_random_data(msg_type)
        else:
            msg_data = {}

            if msg_type == "Access":
                msg_data["encrypted"] = input("Encrypted text: ")

            elif msg_type == "Accessinfo":
                try:
                    msg_data["end_time"] = int(
                        input("End time (timestamp in seconds): ")
                    )
                    msg_data["current_date"] = int(
                        input("Current date (timestamp in seconds): ")
                    )
                    msg_data["user_id"] = int(input("User ID: "))
                except ValueError:
                    print(
                        "Invalid input for timestamps or user ID. Please enter integers."
                    )

            elif msg_type == "Ack":
                msg_data["msgid"] = input("Message ID: ")
                try:
                    msg_data["chunk_id"] = int(input("Chunk ID: "))
                except ValueError:
                    print("Invalid input for chunk ID. Please enter an integer.")

            elif msg_type == "Auth":
                msg_data["auth_key"] = input("Authentication key: ")

            elif msg_type == "Dvid":
                try:
                    msg_data["device_id"] = int(input("Device ID: "))
                except ValueError:
                    print("Invalid input for device ID. Please enter an integer.")

        input_data.append({"typ": msg_type, "msg": msg_data})

    return input_data


def main(args=None):
    # Create publisher instance
    ros_msg_publisher = RosSystemMsgPublisher()

    # Get input data from user or generate random data
    input_data = get_input_data()

    # Setup all publishers for the input data
    for item in input_data:
        ros_msg_publisher.setup_publisher(item["typ"], item["msg"])

    # Publish all the messages
    ros_msg_publisher.publish_all()
    # Spin the node
    ros_msg_publisher.spin_once(timeout_sec=1.0)
    ros_msg_publisher.cleanup()


if __name__ == "__main__":
    main()
