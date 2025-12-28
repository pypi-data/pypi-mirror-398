import configparser
import os
import signal
import sys
from typing import Dict, Any
import json
from zoneinfo import ZoneInfo
from vyomcloudbridge.utils.logger_setup import setup_logger
from vyomcloudbridge.constants.constants import DEFAULT_TIMEZONE, machine_config_file

logger = setup_logger(name=__name__, show_terminal=False)


class Configs:
    @staticmethod
    def _validate_timezone(timezone_str: str) -> str:
        """
        Validate timezone string and return DEFAULT_TIMEZONE if invalid.

        Args:
            timezone_str: Timezone string to validate

        Returns:
            Valid timezone string or DEFAULT_TIMEZONE as fallback
        """
        if not timezone_str:
            return DEFAULT_TIMEZONE

        try:
            # Test if the timezone is valid by creating a ZoneInfo object
            ZoneInfo(timezone_str)
            return timezone_str
        except Exception as e:
            logger.warning(
                f"Invalid timezone '{timezone_str}', falling back to default: {e}"
            )
            return DEFAULT_TIMEZONE

    @staticmethod
    def get_machine_config() -> Dict[str, Any]:
        config = configparser.ConfigParser()
        if os.path.exists(machine_config_file):
            config.read(machine_config_file)
            machine_detail = {}
            try:
                machine_detail = {
                    "machine_id": int(config["MACHINE"]["machine_id"]),  # in use
                    "machine_uid": config["MACHINE"]["machine_uid"],  # in use
                    "machine_name": config["MACHINE"]["machine_name"],
                    "machine_model_id": int(config["MACHINE"]["machine_model_id"]),
                    "machine_model_name": config["MACHINE"]["machine_model_name"],
                    "machine_model_type": config["MACHINE"]["machine_model_type"],
                    "organization_id": int(
                        config["MACHINE"]["organization_id"]
                    ),  # in use
                    "organization_name": config["MACHINE"]["organization_name"],
                }

                # return {
                #     "machine_id": int(config["MACHINE"]["machine_id"]),  # in use
                #     "machine_uid": config["MACHINE"]["machine_uid"],  # in use
                #     "machine_name": config["MACHINE"]["machine_name"],
                #     "machine_model_id": int(config["MACHINE"]["machine_model_id"]),
                #     "machine_model_name": config["MACHINE"]["machine_model_name"],
                #     "machine_model_type": config["MACHINE"]["machine_model_type"],
                #     "organization_id": int(
                #         config["MACHINE"]["organization_id"]
                #     ),  # in use
                #     "organization_name": config["MACHINE"]["organization_name"],
                #     "ssh_port": int(config["MACHINE"]["ssh_port"]),  # in use
                #     "access_public_key": config["MACHINE"][
                #         "access_public_key"
                #     ],  # in use
                #     "access_private_key": config["MACHINE"][
                #         "access_private_key"
                #     ],  # in use
                # }
            except (KeyError, ValueError):
                logger.error(
                    f"Failed to parse configuration from {machine_config_file}"
                )
                return {
                    "machine_id": None,  # in use
                    "machine_uid": "",  # in use
                    "machine_name": "",
                    "machine_model_id": None,
                    "machine_model_name": "",
                    "machine_model_type": "",
                    "organization_id": None,  # in use
                    "organization_name": "",
                    "ssh_port": None,  # in use
                    "access_public_key": "",  # in use
                    "access_private_key": "",  # in use
                }

            # BACKWARD COMPATIBILITY
            try:
                ssh_port = int(config["MACHINE"]["ssh_port"])
                if ssh_port:
                    machine_detail["ssh_port"] = ssh_port
                else:
                    machine_detail["ssh_port"] = 0
            except (KeyError, ValueError):
                logger.debug(f"Failed to get ssh_port from {machine_config_file}")
            except Exception as e:
                machine_detail["ssh_port"] = 0

            # TODO
            try:
                ssh_enabled = config["MACHINE"]["ssh_enabled"]
                if ssh_enabled:
                    if ssh_enabled in ["true", "True"]:
                        machine_detail["ssh_enabled"] = True
                    else:
                        machine_detail["ssh_enabled"] = False
                else:
                    machine_detail["ssh_enabled"] = False
            except (KeyError, ValueError):
                machine_detail["ssh_enabled"] = False
                logger.debug(f"Failed to get ssh_enabled from {machine_config_file}")
            except Exception as e:
                machine_detail["ssh_enabled"] = False

            try:
                ssh_key = config["MACHINE"]["ssh_key"]
                if ssh_key:
                    machine_detail["ssh_key"] = ssh_key
                else:
                    machine_detail["ssh_key"] = None
            except (KeyError, ValueError):
                machine_detail["ssh_key"] = None
                logger.debug(f"Failed to get ssh_key from {machine_config_file}")
            except Exception as e:
                machine_detail["ssh_key"] = None

            try:
                access_public_key = config["MACHINE"]["access_public_key"]
                if access_public_key:
                    machine_detail["access_public_key"] = access_public_key
                else:
                    machine_detail["access_public_key"] = None
            except (KeyError, ValueError):
                machine_detail["access_public_key"] = None
                logger.debug(
                    f"Failed to get access_public_key from {machine_config_file}"
                )
            except Exception as e:
                machine_detail["access_public_key"] = None

            try:
                access_private_key = config["MACHINE"]["access_private_key"]
                if access_private_key:
                    machine_detail["access_private_key"] = access_private_key
                else:
                    machine_detail["access_private_key"] = None
            except (KeyError, ValueError):
                machine_detail["access_private_key"] = None
                logger.debug(
                    f"Failed to get access_private_key from {machine_config_file}"
                )
            except Exception as e:
                machine_detail["access_private_key"] = None

            try:
                mqtt_primary_channel = config["MACHINE"]["mqtt_primary_channel"]
                if mqtt_primary_channel:
                    machine_detail["mqtt_primary_channel"] = mqtt_primary_channel
                else:
                    machine_detail["mqtt_primary_channel"] = [
                        "awsiot"
                    ]  #     awsiot, azureiot mosquitto
            except (KeyError, ValueError):
                machine_detail["mqtt_primary_channel"] = ["awsiot"]
                logger.debug(
                    f"Failed to get mqtt_primary_channel from {machine_config_file}"
                )
            except Exception as e:
                machine_detail["mqtt_primary_channel"] = ["awsiot"]

            # Timezone support - validate timezone and fallback to default if invalid
            try:
                timezone = config["MACHINE"]["timezone"]
                machine_detail["timezone"] = Configs._validate_timezone(timezone)
            except (KeyError, ValueError):
                machine_detail["timezone"] = DEFAULT_TIMEZONE
                logger.debug(f"Failed to get timezone from {machine_config_file}")
            except Exception as e:
                machine_detail["timezone"] = DEFAULT_TIMEZONE

            # from datetime import datetime
            # from zoneinfo import ZoneInfo # Python 3.9+ buil-in

            # tz_str = "Asia/Kolkata"
            # now_local = datetime.now(ZoneInfo(tz_str))
            # print(now_local)

            try:
                destination_ids = config["MACHINE"][
                    "destination_ids"
                ]  # this are destination
                if destination_ids:
                    machine_detail["destination_ids"] = destination_ids
                else:
                    machine_detail["destination_ids"] = ["awsiot_s3"]
            except (KeyError, ValueError):
                machine_detail["destination_ids"] = ["awsiot_s3"]
                logger.debug(
                    f"Failed to get destination_ids from {machine_config_file}"
                )
            except Exception as e:
                machine_detail["destination_ids"] = ["awsiot_s3"]

            # return the final details
            return machine_detail
        else:
            logger.error(
                f"Using default empty values because config file {machine_config_file} was not found"
            )
            return {
                "machine_id": None,  # in use
                "machine_uid": "",  # in use
                "machine_name": "",
                "machine_model_id": None,
                "machine_model_name": "",
                "machine_model_type": "",
                "organization_id": None,  # in use
                "organization_name": "",
                "ssh_port": 0,  # in use
                "ssh_enabled": False,
                "ssh_key": "",
                "access_public_key": "",  # in use
                "access_private_key": "",  # in use
                "timezone": DEFAULT_TIMEZONE,
            }


def main():
    machine_config = Configs.get_machine_config()
    machine_id = machine_config.get("machine_id", "-") or "-"
    machine_uid = machine_config.get("machine_uid", "-") or "-"
    machine_name = machine_config.get("machine_name", "-") or "-"
    machine_model_id = machine_config.get("machine_model_id", "-") or "-"
    machine_model_name = machine_config.get("machine_model_name", "-") or "-"
    machine_model_type = machine_config.get("machine_model_type", "-") or "-"
    organization_id = machine_config.get("organization_id", "-") or "-"
    organization_name = machine_config.get("organization_name", "-") or "-"
    ssh_port = machine_config.get("ssh_port", 0) or 0
    ssh_enabled = machine_config.get("ssh_enabled", False) or False
    ssh_key = machine_config.get("ssh_key", "-") or "-"
    access_public_key = machine_config.get("access_public_key", "-") or "-"
    access_private_key = machine_config.get("access_private_key", "-") or "-"
    timezone = machine_config.get("timezone", "-") or "-"

    print("machine_id:", machine_id)
    print("machine_uid:", machine_uid)
    print("machine_name:", machine_name)
    print("machine_model_id:", machine_model_id)
    print("machine_model_name:", machine_model_name)
    print("machine_model_type:", machine_model_type)
    print("organization_id:", organization_id)
    print("organization_name:", organization_name)
    print("ssh_port:", ssh_port)
    print("ssh_enabled:", ssh_enabled)
    print("ssh_key:", ssh_key)
    print("access_public_key:", access_public_key)
    print("access_private_key:", access_private_key)
    print("timezone:", timezone)


if __name__ == "__main__":
    main()
