# vyomcloudbridge/setup.py
import os
import subprocess
import sys
import json
import configparser
import getpass
import requests
import time
import pwd
from urllib.parse import urlencode

from vyomcloudbridge.constants.constants import (
    log_dir,
    log_file,
    pid_file,
    vyom_root_dir,
    machine_config_file,
    machine_topics_file,
    start_script_file,
    start_script_root_file,
    service_file_name,
    service_file_path,
    service_root_file_name,
    service_root_file_path,
    ssh_service_file_name,
    ssh_service_file_path,
    cert_dir,
    cert_file_path,
    pri_key_file_path,
    pub_key_file_path,
    root_ca_file_path,
    vyom_variables_file,
    default_machine_type,
    DEFAULT_TIMEZONE,
    MACHINE_REGISTER_API_URL,
    MACHINE_MODELS_API_URL,
    MACHINE_TOPICS_API_URL,
)
from vyomcloudbridge.utils.configs import Configs
from vyomcloudbridge.utils.install_specs import InstallSpecs


install_specs = InstallSpecs()

# def setup_ros2_workspaces(): # Not in use
#     """
#     Writes AMENT_PREFIX_PATH and PYTHONPATH to a shell-compatible .env file for later sourcing.

#     Returns:
#         bool: True if environment file was written successfully, False otherwise
#         error: Error in string format occurs if registration is not successful.
#     """
#     print("\n--- STEP 0: Fetching ROS2 workspace environment variables ---")

#     python_path = os.environ.get("PYTHONPATH", "")
#     ament_prefix_path = os.environ.get("AMENT_PREFIX_PATH", "")
#     ld_library_path = os.environ.get("LD_LIBRARY_PATH", "")
#     rmw_implementation = os.environ.get("RMW_IMPLEMENTATION", "")
#     # print("After reading in setup, PYTHONPATH-", python_path)
#     # print("After reading in setup, AMENT_PREFIX_PATH-", ament_prefix_path)
#     # print("After reading in setup, LD_LIBRARY_PATH-", ld_library_path)
#     # print("After reading in setup, RMW_IMPLEMENTATION-", rmw_implementation)

#     if (
#         not ament_prefix_path
#         or not python_path
#         or not ld_library_path
#         or not rmw_implementation
#     ) and not os.path.exists(vyom_services_env_file):
#         missing_vars = []
#         if not python_path:
#             missing_vars.append("PYTHONPATH env variable")
#         if not ament_prefix_path:
#             missing_vars.append("Your ROS2 workspaces (AMENT_PREFIX_PATH env variable)")
#         if not ld_library_path:
#             missing_vars.append("LD_LIBRARY_PATH env variable")
#         if not rmw_implementation:
#             missing_vars.append("RMW_IMPLEMENTATION env variable")

#         error_message = "Missing environment variables:\n - " + "\n - ".join(
#             missing_vars
#         )
#         print(
#             "===> "
#             + error_message
#             + "\nPlease ensure you manually source them, before running `vyomcloudbridge setup`. <==="
#         )
#         return False, error_message
#     # else here either we have all three varibale or the file saved already
#     needs_sudo = os.geteuid() != 0
#     if needs_sudo:
#         print("Error - Root permission required.")
#         return False, "Root permission required."

#     try:
#         if (
#             ament_prefix_path and python_path and ld_library_path
#         ):  # we have all three varibale
#             os.makedirs(vyom_root_dir, exist_ok=True)

#             with open(vyom_services_env_file, "w") as f:
#                 f.write("#!/bin/bash\n")
#                 if python_path:
#                     f.write(f'export PYTHONPATH="{python_path.strip()}"\n')
#                 if ament_prefix_path:
#                     f.write(f'export AMENT_PREFIX_PATH="{ament_prefix_path.strip()}"\n')
#                 if ld_library_path:
#                     f.write(f'export LD_LIBRARY_PATH="{ld_library_path.strip()}"\n')
#                 if rmw_implementation:
#                     f.write(
#                         f'export RMW_IMPLEMENTATION="{rmw_implementation.strip()}"\n'
#                     )
#                 # f.write(f'export RMW_IMPLEMENTATION="rmw_cyclonedds_cpp"\n')

#             subprocess.run(["chmod", "+x", vyom_services_env_file], check=True)

#             print(f"✅ ROS2 environment variables saved to: {vyom_services_env_file}")
#         else:  # the file saved already before
#             print(
#                 f"✅ Using Exiting ROS2 env variables saved at: {vyom_services_env_file}"
#             )
#         return True, None

#     except Exception as e:
#         print(f"❌ Error saving ROS2 environment file: {str(e)}")
#         return False, f"Error saving ROS2 environment file: {str(e)}"


def install_rabbitmq():
    """
    Install and configure RabbitMQ server

    Returns:
        success: bool, True if installation was successful, False otherwise
        error: string, error if not successful.
    """
    print("\n--- STEP 1: Installing and configuring RabbitMQ server ---")

    try:
        # Update package lists
        # print("Updating package lists...")
        # subprocess.run(["apt", "update", "-y"], check=True)

        # Install RabbitMQ server
        print("Installing RabbitMQ server...")
        subprocess.run(["apt", "install", "rabbitmq-server", "-y"], check=True)

        # Start the RabbitMQ service
        print("Starting RabbitMQ service...")
        subprocess.run(["systemctl", "start", "rabbitmq-server"], check=True)

        # Enable RabbitMQ to start on boot
        print("Enabling RabbitMQ to start on boot...")
        subprocess.run(["systemctl", "enable", "rabbitmq-server"], check=True)

        # Enable the RabbitMQ management plugin
        print("Enabling RabbitMQ management plugin...")
        subprocess.run(
            ["rabbitmq-plugins", "enable", "rabbitmq_management"], check=True
        )

        print("RabbitMQ installation and configuration completed successfully.")
        return True, None
    except subprocess.CalledProcessError as e:
        print(f"Error during RabbitMQ installation: {str(e)}")
        return False, f"Error during RabbitMQ installation: {str(e)}"


def _get_machine_data_topic_list():
    # return machine_topics_list
    try:
        from vyomcloudbridge.utils.ros_topics import ROSTopic

        topics_discoverer = ROSTopic(discovery_timeout=5.0)
        topic_list = topics_discoverer.serialize_topic_list()

        # cleanup before exit
        try:
            topics_discoverer.cleanup()
        except:
            pass
        if len(topic_list):
            return topic_list, None
        else:
            return [], "Error - No ROS topics detected"
    except Exception as e:

        # cleanup before exit
        try:
            topics_discoverer.cleanup()
        except:
            pass

        error = f"Error - Failed to fetch ROS topics: {str(e)}"
        return [], error


def _fetch_organization_models(organization_id, otp):
    """
    Fetch machine models for an organization using API call
    Args:
        organization_id (str): The organization ID
        otp (str): One-time password for authentication

    Returns:
        dict: Response containing models and possibly new OTP
    """
    try:
        headers = {
            "Content-Type": "application/json",
        }
        payload = {"otp": otp, "organization_id": organization_id}

        response = requests.post(MACHINE_MODELS_API_URL, headers=headers, json=payload)
        data = response.json()
        if data.get("status") == 200:
            otp = str(data["data"].get("otp", ""))
            session_id = str(data["data"].get("session_id", ""))
            machine_models = data["data"].get("machine_models", [])
            return otp, session_id, machine_models
        else:
            error_message = data.get("error", {}).get(
                "message",
                "API failed due to an unknown error - please contact the support team.",
            )
            raise Exception(error_message)

    except Exception as e:
        raise


def setup_ssh_service(ssh_key, port, service_username):
    """
    Create and start the ssh service

    Returns:

    """
    print("\n--- Setting ssh service ---")

    # TODO
    # OPEN and save ssh_key in, in home directory of service_username, ~/.ssh/vyom_gcp_key

    needs_sudo = os.geteuid() != 0
    if needs_sudo:
        print("Error - Root permission required.")
        return False, "Root permission required."
    try:
        user_home = os.path.expanduser(f"~{service_username}")
        ssh_dir = os.path.join(user_home, ".ssh")
        key_file_path = os.path.join(ssh_dir, "vyom_gcp_key")

        # Ensure .ssh directory exists
        os.makedirs(ssh_dir, mode=0o700, exist_ok=True)

        # Write the ssh_key content to the key file, ensuring it ends with a newline
        if not ssh_key.endswith("\n"):
            ssh_key += "\n"
        with open(key_file_path, "w") as key_file:
            key_file.write(ssh_key)
        os.chmod(key_file_path, 0o600)

        # Set ownership to target user
        user_info = pwd.getpwnam(service_username)
        uid = user_info.pw_uid
        gid = user_info.pw_gid
        os.chown(ssh_dir, uid, gid)
        os.chown(key_file_path, uid, gid)

        print(f"SSH key has been saved to {key_file_path}")

        # TODO later we willl replace User=root with User={username}
        # ExecStart=/bin/bash {start_script_file}
        with open(ssh_service_file_path, "w") as f:
            f.write(
                f"""[Unit]
Description=Reverse SSH Tunnel
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User={service_username}
ExecStart=/usr/bin/ssh -N -R {port}:localhost:22 \
    -o ServerAliveInterval=60 \
    -o ServerAliveCountMax=3 \
    -o ExitOnForwardFailure=yes \
    -o StrictHostKeyChecking=no \
    -i {key_file_path} \
    jet@hq.vyomos.org
Restart=always
RestartSec=60

[Install]
WantedBy=multi-user.target
"""
            )
        print(f"Vyom ssh service has been created at {ssh_service_file_path}")

        print("Reloading systemd daemon...")
        subprocess.run(["systemctl", "daemon-reload"], check=True)

        # Enable and start the service
        print(f"Enabling and starting {ssh_service_file_name}...")
        subprocess.run(["systemctl", "enable", ssh_service_file_name], check=True)
        try:
            subprocess.run(["systemctl", "stop", ssh_service_file_name], check=False)
        except Exception as e:
            pass
        subprocess.run(["systemctl", "start", ssh_service_file_name], check=True)
        print(f"{ssh_service_file_name} Service has been installed and started.")
        print(
            f"=====> You can now SSH into this machine using: ssh -p {port} <username>@hq.vyomos.org <====== \n"
        )
    except Exception as e:
        print(f"Error creating or starting {service_file_name}: {str(e)}")
        return False, f"Error creating or starting {service_file_name}: {str(e)}"
    return True, None


def register_machine(interactive=True):
    """
    Register the machine with VyomOS API or display existing configuration
    if already registered.

    Args:
        interactive (bool): Whether to run in interactive mode and prompt for input

    Returns:
        bool: True if registration was successful or config already exists,
              False otherwise
        error: Error in string format occurs if registration is not successful.
    """
    print("\n--- STEP 2: Machine Registration Check ---")

    # Check if config file already exists
    if os.path.exists(machine_config_file):
        print(f"Configuration file already exists at: {machine_config_file}")
        try:
            # Read existing configuration
            config = configparser.ConfigParser()
            config.read(machine_config_file)

            if "MACHINE" in config:
                machine_id = config["MACHINE"].get("machine_id", "Unknown")
                machine_uid = config["MACHINE"].get("machine_uid", "Unknown")
                organization_id = config["MACHINE"].get("organization_id", "Unknown")
                organization_name = config["MACHINE"].get(
                    "organization_name", "Unknown"
                )
                machine_name = config["MACHINE"].get("machine_name", "Unknown")

                print("\n--- Basic Machine Details ---")
                print(f"Machine ID: {machine_id}")
                print(f"Machine UID: {machine_uid}")
                print(f"Machine Name: {machine_name}")
                print(f"Organization ID: {organization_id}")
                print(f"Organization Name: {organization_name}")
                return True, ""
            else:
                print(
                    "Warning: Configuration file exists but appears to be invalid. Re-registering..."
                )
        except Exception as e:
            print(f"Error reading configuration file: {str(e)}")
            print(f"Re-registering..")

    print("\n--- STEP 2: Registering machine with VyomIQ ---")

    # Check if we're running with sufficient privileges
    needs_sudo = os.geteuid() != 0

    if not interactive:
        print("Error - Running in non-interactive mode. Machine registration failed.")
        return False, ""

    # Get machine registration information
    organization_id = input("Organization ID: ").strip()
    print("Fetching organization-related details...")
    otp = input("Enter the OTP: ").strip()

    # Fetch machine models from API
    machine_models = []
    session_id = ""
    try:
        # API call to fetch machine models
        try:
            new_otp, session_id, machine_models = _fetch_organization_models(
                organization_id, otp
            )
            otp = new_otp
        except Exception as e:
            print(f"Error fetching machine models: {str(e)}")
            return False, ""
    except Exception as e:
        print(f"Error fetching machine models: {str(e)}")
        return False, ""

    # Prompt for machine details

    # Display machine models in a table format
    print("\n--- Available Machine Models ---")

    print("| {:<10} | {:<20} | {:<30} |".format("Model ID", "Model UID", "Model Name"))
    print("|" + "-" * 12 + "|" + "-" * 22 + "|" + "-" * 32 + "|")

    for model in machine_models:
        model_id = model.get("id", "N/A")
        if model_id == 1 or model_id == "1":
            # Skip the demo device model
            continue
        print(
            "| {:<10} | {:<20} | {:<30} |".format(
                model.get("id", "N/A"),
                model.get("model_uid", "N/A"),
                model.get("name", "N/A"),
            )
        )
    print(
        "Choose a Machine Model ID from the list, or enter 'N' to create a new one..."
    )
    machine_model_id = input("Machine Model ID: ").strip().lower()
    if machine_model_id == "n" or machine_model_id == "'n'":
        machine_model_id = None
        machine_model_uid = input("Machine Model UID: ").strip()
        machine_model_name = input("Machine Model Name: ").strip()
        type = default_machine_type
        # TODO: If invalid, prompt the user multiple times to choose from the list.
    else:
        machine_model_id = int(machine_model_id)
        machine_model_uid = None
        machine_model_name = None
        type = None

    machine_uid = input("Machine UID: ").strip()
    machine_name = input("Machine Name: ").strip()

    # Timezone selection
    timezone = DEFAULT_TIMEZONE
    timezone_choices = {
        1: "UTC",
        2: "Asia/Kolkata",
        3: "America/New_York",
        4: "America/Los_Angeles",
        5: "Europe/London",
        6: "Europe/Paris",
        7: "Asia/Tokyo",
        8: "Asia/Shanghai",
        9: "Australia/Sydney",
    }

    print(
        f'\nDevice Timezone: {timezone}, type "y" if you want to change it [Y/n]: ',
        end="",
    )
    change_timezone = input().strip().lower()

    if change_timezone == "y":
        print("\nChoices:")
        print("1 - UTC")
        print("2 - Asia/Kolkata (IST)")
        print("3 - America/New_York (EST/EDT)")
        print("4 - America/Los_Angeles (PST/PDT)")
        print("5 - Europe/London (GMT/BST)")
        print("6 - Europe/Paris (CET/CEST)")
        print("7 - Asia/Tokyo (JST)")
        print("8 - Asia/Shanghai (CST)")
        print("9 - Australia/Sydney (AEST/AEDT)")

        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                choice_input = input(
                    "Type integer value corresponding to correct timezone, and enter: "
                ).strip()
                choice = int(choice_input)
                if choice in timezone_choices:
                    timezone = timezone_choices[choice]
                    print(f"Timezone set to: {timezone}")
                    break
                else:
                    remaining = max_attempts - attempt - 1
                    if remaining > 0:
                        print(
                            f"Invalid choice. Please enter a number between 1 and 9. ({remaining} attempts remaining)"
                        )
                    else:
                        print(f"Invalid choice. Using default timezone: {timezone}")
            except ValueError:
                remaining = max_attempts - attempt - 1
                if remaining > 0:
                    print(
                        f"Invalid input. Please enter a valid integer. ({remaining} attempts remaining)"
                    )
                else:
                    print(f"Invalid input. Using default timezone: {timezone}")

    ssh_enabled = False
    ssh_confirm = (
        input("Do you want to set up remote SSH, routed via VyomIQ domain? [Y/n]: ")
        .strip()
        .lower()
    )

    if ssh_confirm in ["y", "yes"]:
        ssh_enabled = True

    # Validate input
    is_valid_model = machine_model_id or (
        machine_model_uid and machine_model_name and type
    )
    if not organization_id or not machine_uid or not is_valid_model:
        print("Missing required registration information. Registration failed.")
        return False, ""

    if install_specs.is_full_install:
        machine_model_topics, error = _get_machine_data_topic_list()
    else:
        machine_model_topics = []
        error = None

    if error:
        print(error)
        return False, ""
    # Create payload JSON
    payload = {
        "organization_id": int(organization_id),
        "otp": otp,  # string
        "session_id": session_id,
        # model detail
        "machine_model_id": machine_model_id,  # TODO just check int of None will work here or not
        "machine_model_uid": machine_model_uid,
        "machine_model_name": machine_model_name,
        "type": type,
        # machine detail
        "machine_uid": machine_uid,
        "name": machine_name,
        "ssh_enabled": ssh_enabled,
        "timezone": timezone,
        # machine topic detail
        "machine_model_topics": machine_model_topics,
    }

    # Make API call to register machine
    print("Registering machine with VyomIQ...")
    try:

        response = requests.post(
            MACHINE_REGISTER_API_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
        )

        # Check response
        data = response.json()
        if data.get("status") == 200:
            print("Machine registration successful!")

            if needs_sudo:
                print("Error - Root permission required.")
                return False, "Root permission required."
            else:
                print(
                    "=====>  Your new Machine Model ID is -",
                    str(data["data"].get("machine_model", "")),
                    " <======",
                )
                os.makedirs(vyom_root_dir, exist_ok=True)
                # Extract data from response and save in INI format

                config = configparser.ConfigParser()
                # STEP 1 saving machine configuration
                try:
                    print("Saving machine configuration...")
                    config["MACHINE"] = {
                        "machine_id": str(data["data"].get("id", "")),
                        "machine_uid": data["data"].get("machine_uid", ""),
                        "machine_name": data["data"].get("name", ""),
                        "machine_model_id": str(data["data"].get("machine_model", "")),
                        "machine_model_name": data["data"].get(
                            "machine_model_name", ""
                        ),
                        "machine_model_type": data["data"].get(
                            "machine_model_type", ""
                        ),
                        "mfg_date": data["data"].get("mfg_date", ""),
                        "activation_date": str(data["data"].get("activation_date", "")),
                        "end_of_service_date": str(
                            data["data"].get("end_of_service_date", "")
                        ),
                        "organization_id": str(data["data"].get("current_owner", "")),
                        "organization_name": data["data"].get("current_owner_name", ""),
                        "usage_status": data["data"].get("usage_status", ""),
                        "camera_feed": data["data"].get("camera_feed", ""),
                        "ssh_port": str(data["data"].get("ssh_port", "")),
                        "ssh_enabled": str(data["data"].get("ssh_enabled", "")),
                        "ssh_key": data["data"].get("ssh_key", ""),
                        "timezone": data["data"].get("timezone", ""),
                        "created_at": data["data"].get("created_at", ""),
                        "updated_at": data["data"].get("updated_at", ""),
                        "session_id": data["data"].get("session_id", ""),
                        "access_public_key": data["data"].get("access_public_key", ""),
                        "access_private_key": data["data"].get(
                            "access_private_key", ""
                        ),
                    }
                    with open(machine_config_file, "w") as f:
                        config.write(f)
                    print(f"Configuration saved to {machine_config_file}")

                except Exception as e:
                    print(f"Error saving configuration: {str(e)}")
                    return False, f"Error saving configuration: {str(e)}"

                # STEP2 - Check if IoT data is present in the response
                try:
                    if "iot_data" in data["data"]:
                        iot_data = data["data"]["iot_data"]
                        machine_id = data["data"].get("id", "")

                        print("Saving IoT certificates...")
                        os.makedirs(cert_dir, exist_ok=True)
                        try:
                            # Save the certificate
                            with open(cert_file_path, "w") as f:
                                f.write(iot_data["certificate"]["certificatePem"])

                            # Save the private key
                            with open(pri_key_file_path, "w") as f:
                                f.write(
                                    iot_data["certificate"]["keyPair"]["PrivateKey"]
                                )

                            # Save the public key
                            with open(pub_key_file_path, "w") as f:
                                f.write(iot_data["certificate"]["keyPair"]["PublicKey"])

                            # Save the root CA
                            with open(root_ca_file_path, "w") as f:
                                f.write(iot_data["root_ca"])

                            print(f"IoT certificates saved to {cert_dir}")

                            # Update config with certificate paths
                            config["IOT"] = {
                                "thing_name": iot_data["thing_name"],
                                "thing_arn": iot_data["thing_arn"],
                                "policy_name": iot_data["policy_name"],
                                "certificate_path": cert_file_path,
                                "private_key_path": pri_key_file_path,
                                "public_key_path": pub_key_file_path,
                                "root_ca_path": root_ca_file_path,
                            }

                            # Update the config file with IoT information
                            with open(machine_config_file, "w") as f:
                                config.write(f)
                            print(f"Configuration updated with IoT information")

                        except Exception as e:
                            print(f"Error saving IOT certificates: {str(e)}")
                    else:
                        print("No IoT credentials found in response")
                except Exception as e:
                    print(f"Error in saving IOT certificates : {str(e)}")
                    return False, f"Error in saving IOT certificates : {str(e)}"
                return True, ""
        else:
            print(
                f"Error; Machine registration failed with status: {data.get('status')}"
            )
            print(f"Response: {data}")
            return (
                False,
                f"Machine registration failed with status: {data.get('status')}",
            )

    except Exception as e:
        print(f"Error during machine registration: {str(e)}")
        return False, f"Error during machine registration: {str(e)}"


def fetch_and_save_topics(interactive=True):
    """
    Fetch and save machine subscribed topics from the API

    Args:
        interactive (bool): Whether to run in interactive mode and prompt for input

    Returns:
        tuple: (success (bool), data (dict))
    """
    print("\n--- Fetching machine subscribed topic ---")

    # Prompt user for confirmation if already configured
    # if interactive:
    #     user_input = (
    #         input(
    #             "Have you already configured the subscribed topics for this machine model? [Y/n]: "
    #         )
    #         .strip()
    #         .lower()
    #     )
    #     if user_input not in ["y", "yes"]:
    #         print(
    #             "Skipping topic fetch as per user input. please run setup again once you are done"
    #         )
    #         return False, {}

    # Check if config file already exists
    if os.path.exists(machine_config_file):
        print(f"Configuration file reading from: {machine_config_file}")
        try:
            # Read existing configuration
            config = configparser.ConfigParser()
            config.read(machine_config_file)
            if "MACHINE" in config:
                machine_model_id = config["MACHINE"].get("machine_model_id", "")
                # BACKWARD COMPATIBILITY CODE START
                if not machine_model_id:
                    machine_section = config["MACHINE"]
                    if "machine_model" in machine_section:
                        machine_model_id = machine_section["machine_model"]
                        machine_section["machine_model_id"] = machine_section[
                            "machine_model"
                        ]
                        del machine_section["machine_model"]

                        # Write updated config back to file
                        with open(machine_config_file, "w") as configfile:
                            config.write(configfile)
                # BACKWARD COMPATIBILITY CODE END
                if not machine_model_id:
                    print("Error: Machine model ID not found in configuration file.")
                    print(
                        f"Please delete {machine_config_file} and again do `vyomcloudbridge setup` from root user."
                    )
                    return (
                        False,
                        "Error: Machine model ID not found in configuration file.",
                    )

                try:
                    url = MACHINE_TOPICS_API_URL
                    params = {"machine_model_id": machine_model_id}
                    full_url = f"{url}?{urlencode(params)}"
                    headers = {
                        "Content-Type": "application/json",
                    }
                    payload = {"machine_model_id": machine_model_id}
                    response = requests.get(full_url, headers=headers)

                    if response.status_code != 200:
                        print(
                            f"Error: API {url}, returned status code {response.status_code}"
                        )
                        return (
                            False,
                            f"Error: API {url}, returned status code {response.status_code}",
                        )

                    data = response.json()

                    # Save fetched topics to machine_topics_file
                    os.makedirs(os.path.dirname(machine_topics_file), exist_ok=True)
                    with open(machine_topics_file, "w") as f:
                        json.dump(data, f, indent=4)
                    print(f"Topics successfully saved to {machine_topics_file}")
                    return True, None

                except requests.RequestException as e:
                    print(f"Error: Failed to connect to API {url}: {str(e)}")
                    print(
                        f"Please re-run `vyomcloudbridge setup` again after some time"
                    )
                    return False, f"Failed to connect to API {url}: {str(e)}"
                except json.JSONDecodeError:
                    print("Error: Received invalid JSON response from API")
                    return False, "Received invalid JSON response from API"
                except Exception as e:
                    print(
                        f"Error: in fetching machine topics from API or saving to {machine_topics_file}: {str(e)}"
                    )
                    print("Please try setting up again.")
                    return (
                        False,
                        f"Error: in fetching machine topics from API or saving to {machine_topics_file}: {str(e)}",
                    )
            else:
                print(f"Error: Configuration file exists but appears to be invalid.")
                print(f"Please delete {machine_config_file} and set up again.")
                return False, f"Configuration file exists but appears to be invalid."
        except Exception as e:
            print(f"Error: Failed to read configuration file: {str(e)}")
            print(f"Please delete {machine_config_file} and set up again.")
            return False, f"Failed to read configuration file: {str(e)}"
    else:
        print(
            f"Error: Machine configuration file ({machine_config_file}) does not exist."
        )
        print("Please run the setup process first.")
        return (
            False,
            f"Error: Machine configuration file ({machine_config_file}) does not exist.",
        )


def poll_for_topics(session_id, machine_model_id, timeout=900, interval=5):
    """
    Poll the machine-model/topic/list/ endpoint until topics are available or timeout.
    Args:
        session_id (str): Session ID for the request
        machine_model_id (str|int): Machine model ID
        timeout (int): Max seconds to poll
        interval (int): Seconds between polls
    Returns:
        bool: True if topics were fetched and saved, False otherwise
        error: string, error if not successful.
    """
    print(
        "\nPlease complete the setup on the Fleet manager to complete the setup of your new device."
    )
    print("Waiting for topics to be configured in the Fleet manager UI...")
    start_time = time.time()
    url = MACHINE_TOPICS_API_URL
    params = {"session_id": session_id, "machine_model_id": machine_model_id}
    full_url = f"{url}?{urlencode(params)}"
    headers = {"Content-Type": "application/json"}
    while time.time() - start_time < timeout:
        try:
            response = requests.get(full_url, headers=headers)
            if response.status_code == 200:
                topics = response.json()
                if topics and isinstance(topics, (list, dict)) and len(topics) > 0:
                    # Save topics to machine_topics_file
                    os.makedirs(os.path.dirname(machine_topics_file), exist_ok=True)
                    with open(machine_topics_file, "w") as f:
                        json.dump(topics, f, indent=4)
                    print(
                        f"\nTopics successfully fetched and saved to {machine_topics_file}"
                    )
                    return True
            else:
                print(f"Polling... (status: {response.status_code})")
        except Exception as e:
            print(f"Polling error: {str(e)}")
        time.sleep(interval)
    print(
        "\nTimeout: Topics were not configured in the Fleet manager within the expected time."
    )
    return False


def setup_shell_script():
    """
    Create the shell script for vyomcloudbridge and make it executable

    Returns:
        bool: True if shell script setup was successful, False otherwise
        error: string, error if not successful.
    """
    print("\n--- STEP 3: Setting up vyomcloudbridge shell script ---")

    import os
    import subprocess
    import getpass

    # Check if we're running with sufficient privileges
    needs_sudo = os.geteuid() != 0
    if needs_sudo:
        print("Error - Root permission required.")
        return False

    mavproxyhq_line = (
        "vvyomcloudbridge start mavproxyhq --system-default\n"
        if install_specs.is_full_install
        else ""
    )
    rospublisher_line = (
        "vyomcloudbridge start rospublisher --system-default\n"
        if install_specs.is_full_install
        else ""
    )
    robotstat_line = (
        "vyomcloudbridge start robotstat --system-default\n"
        if install_specs.is_full_install
        else ""
    )

    shell_script_content = f"""#!/bin/bash
# Wait for system to fully boot
sleep 10

export PYTHONUNBUFFERED=1

# Start all the services
echo "Starting vyomcloudbridge services..."
vyomcloudbridge restart
{mavproxyhq_line}
sleep 5
{rospublisher_line}
vyomcloudbridge start vyomlistener --system-default
{robotstat_line}
echo "All system default's services started successfully"

# This keeps the systemd service active/ running indefinitely with minimal resource usage
echo "Services are running, monitoring process active"
tail -f /dev/null

# The script will only reach this point if explicitly terminated
echo "vyomcloudbridge services shutting down.."
"""

    # We have sudo privileges, create the file directly
    try:
        os.makedirs(vyom_root_dir, exist_ok=True)

        with open(start_script_file, "w") as f:
            f.write(shell_script_content)

        # Make the script executable
        print("Setting execute permissions on shell script...")
        subprocess.run(["chmod", "+x", start_script_file], check=True)

        print(
            f"Shell script has been created at {start_script_file} and made executable."
        )
    except Exception as e:
        print(f"Error creating or setting permissions on {start_script_file}: {str(e)}")
        return False

    # Shell script content
    shell_script_root_content = """#!/bin/bash
# Wait for system to fully boot
sleep 30

export PYTHONUNBUFFERED=1

# Start all the services
echo "Starting vyomcloudbridge root services..."
vyomcloudbridge start queueworker --multi-thread --system-default
vyomcloudbridge start missionstats --system-default
vyomcloudbridge start machinestats --system-default

echo "All system default's services started successfully"

# This keeps the systemd service active/ running indefinitely with minimal resource usage
echo "Services are running, monitoring process active"
tail -f /dev/null

# The script will only reach this point if explicitly terminated
echo "vyomcloudbridge services shutting down.."
"""

    # We have sudo privileges, create the file directly
    try:
        with open(start_script_root_file, "w") as f:
            f.write(shell_script_root_content)

        # Make the script executable
        print("Setting execute permissions on shell script...")
        subprocess.run(["chmod", "+x", start_script_root_file], check=True)

        print(
            f"Shell script has been created at {start_script_root_file} and made executable."
        )
    except Exception as e:
        print(
            f"Error creating or setting permissions on {start_script_root_file}: {str(e)}"
        )
        return False

    return True


def setup_service():
    """
    Create and start the systemd service for vyomcloudbridge

    Returns:
        bool: True if service setup was successful, False otherwise
        error: string, error if not successful.
    """
    print("\n--- STEP 4: Setting up vyomcloudbridge service ---")

    # Check if we're running with sufficient privileges
    needs_sudo = os.geteuid() != 0

    saved_data = {}
    vyom_env_file = None
    service_username = None

    if os.path.isfile(vyom_variables_file):
        try:
            with open(vyom_variables_file, "r") as f:
                saved_data = json.load(f)
                vyom_env_file = saved_data.get("vyom_env_file")
                try:
                    service_username = saved_data.get("service_username")
                except Exception as e:
                    print(
                        f"Error reading vyom_variables_file= {vyom_variables_file}: {str(e)}"
                    )

                if not service_username:
                    service_username = saved_data.get("ros_username")  # TODO
        except Exception as e:
            print(f"Error reading vyom_variables_file= {vyom_variables_file}: {str(e)}")
            vyom_env_file = None  # ensure fallback to prompting
            service_username = None

    # if os.path.isfile(vyom_variables_file):
    #     try:
    #         with open(vyom_variables_file, "r") as f:
    #             saved_data = json.load(f)
    #             vyom_env_file = saved_data.get("vyom_env_file")

    #             if vyom_env_file and os.path.isfile(vyom_env_file):
    #                 print(f"Saved environment file path found: {vyom_env_file}")
    #                 confirm = (
    #                     input("Do you want to continue using this path? [Y/n]: ")
    #                     .strip()
    #                     .lower()
    #                 )

    #                 if confirm in ["n", "no"]:
    #                     vyom_env_file = None

    #             else:
    #                 print(f"Saved path does not exist or is invalid: {vyom_env_file}")
    #                 vyom_env_file = None  # force re-prompt

    #     except Exception as e:
    #         print(f"Error reading vyom_variables_file= {vyom_variables_file}: {str(e)}")
    #         vyom_env_file = None  # ensure fallback to prompting

    if vyom_env_file and os.path.isfile(vyom_env_file):
        print(f"Saved environment file path found: {vyom_env_file}")
        confirm = (
            input("Do you want to continue using this path? [Y/n]: ").strip().lower()
        )
        if confirm in ["n", "no"]:
            vyom_env_file = None
    else:
        print(f"Saved path does not exist or is invalid: {vyom_env_file}")
        vyom_env_file = None

    if not vyom_env_file:
        MAX_PATH_ATTEMPTS = 3
        for attempt in range(MAX_PATH_ATTEMPTS):
            vyom_env_file = input(
                "Enter the full path of the script that sets up your environment variables: "
            ).strip()

            # Ensure the path starts with '/'
            if not vyom_env_file.startswith("/"):
                vyom_env_file = "/" + vyom_env_file

            # Check if the file exists
            if os.path.isfile(vyom_env_file):
                print(f"Valid path provided: {vyom_env_file}")
                # try:
                #     # Save the path to the file for future use
                #     with open(vyom_variables_file, "w") as f:
                #         json.dump({"vyom_env_file": vyom_env_file}, f)
                #     print(f"Path saved to: {vyom_variables_file}")
                # except Exception as e:
                #     print(f"Failed to save environment path: {str(e)}")
                break
            else:
                print(f"Invalid path: {vyom_env_file}. Please try again.")
        else:
            print("Maximum attempts reached. Exiting.")
            return False, "Maximum attempts to enter the full path for environment"
    saved_data["vyom_env_file"] = vyom_env_file
    if service_username and install_specs.is_full_install:
        try:
            pwd.getpwnam(service_username)
            print(
                f"Valid username already provided for ros related services: {service_username}"
            )
            confirm = (
                input(
                    "Do you want to continue using username for running ros related services? [Y/n]: "
                )
                .strip()
                .lower()
            )
            if confirm in ["n", "no"]:
                service_username = None
        except KeyError:
            print(f"Username '{service_username}' does not exist in the system.")
            service_username = None

    if not service_username and install_specs.is_lite_install:
        service_username = "root"

    if not service_username:
        MAX_USERNAME_ATTEMPTS = 3
        for attempt in range(MAX_USERNAME_ATTEMPTS):
            service_username = input(
                "Enter the username of the system which will be used to run the ros related services: "
            ).strip()
            try:
                pwd.getpwnam(service_username)
                print(f"Valid username provided: {service_username}")
                break
            except KeyError:
                print(
                    f"Username '{service_username}' does not exist in the system. Please try again."
                )
            except Exception as e:
                print(f"Error validating username: {str(e)}")
        else:
            print("Maximum attempts reached for username validation. Exiting.")
            return False, "Maximum attempts to enter a valid username"
    saved_data["service_username"] = service_username

    try:
        with open(vyom_variables_file, "w") as f:
            json.dump(saved_data, f)
        print(f"Configuration saved to: {vyom_variables_file}")
    except Exception as e:
        print(f"Failed to save configuration: {str(e)}")
        return False, f"Failed to save configuration: {str(e)}"

    if needs_sudo:
        print("Error - Root permission required.")
        return False, "Root permission required."

    # We have sudo privileges, create the file directly
    # Try to get the actual username even when running with sudo
    try:
        username = subprocess.check_output(["logname"], text=True).strip()
    except subprocess.CalledProcessError:
        username = getpass.getuser()

    try:
        # TODO later we willl replace User=root with User={username}
        # ExecStart=/bin/bash {start_script_file}
        with open(service_file_path, "w") as f:
            f.write(
                f"""[Unit]
Description=VyomCloudBridge Service
After=network.target rabbitmq-server.service
Wants=rabbitmq-server.service

[Service]
Type=simple
User={service_username}
Group={service_username}
WorkingDirectory={vyom_root_dir}
ExecStart=/bin/bash -lic 'source {vyom_env_file} && VYOM_ENV_READY=1 {start_script_file}'
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal
LogRateLimitIntervalSec=0
LogRateLimitBurst=0
KillMode=process
KillSignal=SIGTERM
TimeoutStartSec=60
TimeoutStopSec=30

[Install]
WantedBy=multi-user.target
"""
            )
        print(f"Vyomcloudbridge Service has been created at {service_file_path}")

        print("Reloading systemd daemon...")
        subprocess.run(["systemctl", "daemon-reload"], check=True)

        # Enable and start the service
        print(f"Enabling and starting {service_file_name}...")
        subprocess.run(["systemctl", "enable", service_file_name], check=True)
        try:
            subprocess.run(["systemctl", "stop", service_file_name], check=False)
        except Exception as e:
            pass
        # subprocess.run(
        #     ["systemctl", "start", service_file_name], check=True
        # )
        print(f"{service_file_name} Service has been installed.")
    except Exception as e:
        print(f"Error creating or starting {service_file_name}: {str(e)}")
        return False, f"Error creating or starting {service_file_name}: {str(e)}"

    try:
        # TODO later we willl replace User=root with User={username}
        # ExecStart=/bin/bash {start_script_root_file}
        with open(service_root_file_path, "w") as f:
            f.write(
                f"""[Unit]
Description=VyomCloudBridge Root Service
After=network.target rabbitmq-server.service
Wants=rabbitmq-server.service

[Service]
Type=simple
User=root
Group=root
WorkingDirectory={vyom_root_dir}
ExecStart=/bin/bash -lic 'source {vyom_env_file} && VYOM_ENV_READY=1 {start_script_root_file}'
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal
LogRateLimitIntervalSec=0
LogRateLimitBurst=0
KillMode=process
KillSignal=SIGTERM
TimeoutStartSec=60
TimeoutStopSec=30

[Install]
WantedBy=multi-user.target
"""
            )
        print(
            f"Vyomcloudbridge Root Service has been created at {service_root_file_path}"
        )

        print("Reloading systemd daemon...")
        subprocess.run(["systemctl", "daemon-reload"], check=True)

        # Enable and start the service
        print(f"Enabling and starting {service_root_file_name}...")
        subprocess.run(["systemctl", "enable", service_root_file_name], check=True)
        try:
            subprocess.run(["systemctl", "stop", service_root_file_name], check=False)
        except Exception as e:
            pass
        # subprocess.run(
        #     ["systemctl", "start", service_root_file_name], check=True
        # )
        print(f"{service_root_file_name} Service has been installed.")
    except Exception as e:
        print(f"Error creating or starting {service_root_file_name}: {str(e)}")
        return False, f"Error creating or starting {service_root_file_name}: {str(e)}"

    machine_config = Configs.get_machine_config()
    ssh_port = machine_config.get("ssh_port", 0) or 0
    ssh_enabled = machine_config.get("ssh_enabled", False) or False
    ssh_key = machine_config.get("ssh_key", None) or None

    # TODO remove later
    if ssh_enabled and ssh_port:
        if ssh_key:
            ssh_success, ssh_error = setup_ssh_service(
                ssh_key, ssh_port, service_username
            )
            if not ssh_success:
                return False, ssh_error
        else:
            print(f"Error: could not find ssh key in machine config")
    return True, None


def setup_log_directories():
    """
    Create necessary log directories and files with 777 permissions

    Returns:
        bool: True if setup was successful, False otherwise
        error: string, error if not successful.
    """
    print("\n--- STEP 5: Setting up log directories and files ---")

    # Check if we're running with sufficient privileges
    needs_sudo = os.geteuid() != 0

    try:
        if needs_sudo:
            print("Error - Root permission required.")
            return False

        print(f"Creating log directory: {log_dir}")
        os.makedirs(log_dir, exist_ok=True)

        print(f"Setting up log file: {log_file}")
        if not os.path.exists(log_file):
            with open(log_file, "w") as f:
                pass  # Just create an empty file

        print(f"Setting up PID file: {pid_file}")
        if not os.path.exists(pid_file):
            with open(pid_file, "w") as f:
                f.write("{}")  # Initialize with empty JSON object

        print("Setting full permissions (777/666)...")
        # Set 777 permissions for directory (rwxrwxrwx)
        os.chmod(log_dir, 0o777)
        # Set 777 permissions for files (rwxrwxrwx)
        os.chmod(log_file, 0o777)
        os.chmod(pid_file, 0o777)
        #

        # Files that need to be readable/writable by all
        for filepath in [machine_topics_file]:
            dirpath = os.path.dirname(filepath)
            print(f"Ensuring file exists and setting permissions: {filepath}")
            os.makedirs(dirpath, exist_ok=True)
            os.chmod(dirpath, 0o755)
            if not os.path.exists(filepath):
                open(filepath, "w").close()
            os.chmod(filepath, 0o666)  # Read/write by all

        # Other files (readable by all, writable by owner)
        for filepath in [machine_config_file, vyom_variables_file]:
            dirpath = os.path.dirname(filepath)
            print(f"Ensuring file exists and setting permissions: {filepath}")
            os.makedirs(dirpath, exist_ok=True)
            os.chmod(dirpath, 0o755)  # Allow read/traverse by all users

            if not os.path.exists(filepath):
                open(filepath, "w").close()

            os.chmod(filepath, 0o644)  # Readable by all

        # making non root sh file, executable by all
        os.chmod(vyom_root_dir, 0o755)
        if not os.path.exists(start_script_root_file):
            with open(start_script_root_file, "w") as f:
                f.write("#!/bin/bash\n")  # starter content
        os.chmod(
            start_script_root_file, 0o755
        )  # Set read & execute permissions for all users

        # try:
        #     username = subprocess.check_output(["logname"], text=True).strip()
        # except subprocess.CalledProcessError:
        #     username = getpass.getuser()

        # # Only change owner (not group) to avoid issues with mismatched group names
        # try:
        #     subprocess.run(["chown", username, log_dir], check=True)
        #     subprocess.run(["chown", username, log_file], check=True)
        #     subprocess.run(["chown", username, pid_file], check=True)
        # except subprocess.CalledProcessError as e:
        #     print(f"Warning: Could not change ownership: {str(e)}")
        # Already set to 777, so no need for fallback permissions

        print(
            f"Log directories and files setup completed successfully with full permissions (777)."
        )
        return True

    except Exception as e:
        print(f"Error setting up log directories and files: {str(e)}")
        return False


def setup(interactive=True):
    """
    Perform the VyomCloudBridge setup process.
    This is a Python implementation of the install_script.sh functionality.

    Args:
        interactive (bool): Whether to run in interactive mode and prompt for input

    Returns:
        bool: True if setup completed successfully, False otherwise
        error: string, error if not successful.
    """
    print("\n=== Starting VyomCloudBridge Setup ===\n")

    # Print welcome message
    print("Running post-installation setup for vyomcloudbridge...")
    success = True

    # Check if we're running with sufficient privileges
    needs_sudo = os.geteuid() != 0
    if needs_sudo:
        print("Note: Some operations may require administrative privileges.")
        print("Setup failed, Root permission required!")
        return False

    # rosenv_success = True
    # rosenv_success = setup_ros2_workspaces()
    # if not rosenv_success:
    #     print("Ros environment fetch unsuccessful!, Exiting...")
    #     success = False
    #     return False

    # STEP 1: Install RabbitMQ (only if we have root privileges)
    rabbitmq_success = True
    rabbitmq_success = install_rabbitmq()
    if not rabbitmq_success:
        print("RabbitMQ installation failed!, Exiting...")
        success = False
        return False

    # STEP 2: Register machine
    new_registration = True
    if os.path.exists(machine_config_file):
        new_registration = False

    registration_success, _ = register_machine(interactive=interactive)
    if not registration_success and interactive:
        print("Machine registration failed!, Exiting...")
        success = False
        return False

    # STEP 2.1: fetch machine subscribe topic
    session_id = None
    machine_model_id = None
    if registration_success:
        max_retries = 3
        retry_count = 0
        topic_fetch_success = False
        # Try to get session_id and machine_model_id from config or registration
        try:
            if os.path.exists(machine_config_file):
                config = configparser.ConfigParser()
                config.read(machine_config_file)
                if "MACHINE" in config:
                    machine_model_id = config["MACHINE"].get("machine_model_id", None)
                    session_id = config["MACHINE"].get("session_id", None)
        except Exception:
            pass
        while retry_count < max_retries and not topic_fetch_success:
            try:
                topic_fetch_success, topic_fetch_error = fetch_and_save_topics(
                    interactive=interactive
                )
                if not topic_fetch_success and interactive:
                    retry_count += 1
                    if retry_count < max_retries:
                        print(
                            f"Machine topics fetch failed! Retrying... (Attempt {retry_count + 1}/{max_retries})"
                        )
                    else:
                        print(
                            "Machine topics fetch failed after maximum retries! Exiting..."
                        )
                        success = False
                        return False
            except Exception as e:
                retry_count += 1
                if retry_count < max_retries:
                    print(
                        f"Error fetching topics: {str(e)}. Retrying... (Attempt {retry_count + 1}/{max_retries})"
                    )
                else:
                    print(
                        f"Failed to fetch topics after {max_retries} attempts. Error: {str(e)}"
                    )
                    success = False
                    return False
    # STEP 3: Setup shell script
    script_success = setup_shell_script()
    if not script_success:
        print("Shell script setup failed!, Exiting...")
        success = False
        return False

    # STEP 4: Setup service
    setup_service_success, setup_service_error = setup_service()
    if not setup_service_success:
        print("Service setup failed!, Exiting...")
        success = False
        return False

    # STEP 5: logs file and permission
    files_setup_success = setup_log_directories()
    if not files_setup_success:
        print("Script log directories failed!, Exiting...")
        success = False
        return False

    # Print message for Fleet manager step
    if install_specs.is_full_install:
        print(
            "\nPlease complete setup on your fleet manager to finish the device registration."
        )
        # STEP 6: Poll for topics after Fleet manager setup
        if new_registration and session_id and machine_model_id:
            poll_success = poll_for_topics(session_id, machine_model_id)
            if not poll_success:
                print(
                    "Setup could not complete because topics were not configured in time."
                )
                return False
        else:
            print(
                "Missing session_id or machine_model_id for polling topics. Skipping STEP 6."
            )
            return False

    # Final status
    if success:
        # non root service
        subprocess.run(["systemctl", "start", service_file_name], check=True)
        print(f"{service_file_name} background service started.")

        # root service
        subprocess.run(["systemctl", "start", service_root_file_name], check=True)
        print(f"{service_root_file_name} background service started.")

        print("\n=== VyomIQ setup finished. ===")
    else:
        print("\n=== VyomCloudBridge setup encountered errors ===")
        print("Please resolve the issues and try again.")

    return success


if __name__ == "__main__":
    # Check if script is run with --non-interactive flag
    is_interactive = "--non-interactive" not in sys.argv
    success = setup(interactive=is_interactive)

    # Exit with appropriate status code
    if not success:
        sys.exit(1)
