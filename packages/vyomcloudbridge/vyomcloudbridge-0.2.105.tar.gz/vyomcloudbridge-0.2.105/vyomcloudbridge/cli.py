# vyomcloudbridge/cli.py
import os
import subprocess
import sys
import json
import logging
from vyomcloudbridge.constants.constants import (
    vyom_variables_file,
)
from vyomcloudbridge.utils.install_specs import InstallSpecs

install_specs = InstallSpecs()


def format_duration(seconds):
    """Format duration in seconds to a human-readable string."""
    minutes, seconds = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)

    if days > 0:
        return f"{days}d {hours}h {minutes}m"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"


def display_system_health(library_health):
    try:
        # Check 1: Certificates
        print("\nCheck 1: Certificates and Security:\n------------------------------")
        cert_components = ["certificates_dir", "cert_file", "private_key", "root_ca"]
        for component in cert_components:
            if component in library_health:
                status_symbol = "✓" if library_health[component]["status"] else "✗"
                print(
                    f"{status_symbol} {component}: {library_health[component]['message']}"
                )

        # Check 2: Log directory
        print("\nCheck 2: Logging Configuration:\n---------------------------")
        if "log_directory" in library_health:
            status_symbol = "✓" if library_health["log_directory"]["status"] else "✗"
            print(f"{status_symbol} {library_health['log_directory']['message']}")

        # Check 3: Home directory and configs
        print(
            "\nCheck 3: Home Directory and Configuration:\n------------------------------------"
        )
        home_components = ["root_directory", "machine_config", "start_script"]
        for component in home_components:
            if component in library_health:
                status_symbol = "✓" if library_health[component]["status"] else "✗"
                print(
                    f"{status_symbol} {component}: {library_health[component]['message']}"
                )

        # Check 4: System service
        print(
            "\nCheck 4: System Service Configuration:\n---------------------------------"
        )
        service_components = ["service_dir", "service_file_path"]
        for component in service_components:
            if component in library_health:
                status_symbol = "✓" if library_health[component]["status"] else "✗"
                print(
                    f"{status_symbol} {component}: {library_health[component]['message']}"
                )

        # Check 5: RabbitMQ
        print("\nCheck 5: RabbitMQ and Dependencies:\n------------------------------")
        rabbitmq_components = ["rabbitmq", "pika_library"]
        for component in rabbitmq_components:
            if component in library_health:
                status_symbol = "✓" if library_health[component]["status"] else "✗"
                print(
                    f"{status_symbol} {component}: {library_health[component]['message']}"
                )

        # Overall status
        print("\nOverall Status:\n--------------")
        all_complete = all(status["status"] for status in library_health.values())
        if all_complete:
            print("✓ All system requirements are met. The system is ready to use.")
        else:
            incomplete_steps = []
            if not all(
                library_health[comp]["status"]
                for comp in cert_components
                if comp in library_health
            ):
                incomplete_steps.append("Check 1: Certificates")
            if (
                "log_directory" in library_health
                and not library_health["log_directory"]["status"]
            ):
                incomplete_steps.append("Check 2: Logging")
            if not all(
                library_health[comp]["status"]
                for comp in home_components
                if comp in library_health
            ):
                incomplete_steps.append("Check 3: Configuration")
            if not all(
                library_health[comp]["status"]
                for comp in service_components
                if comp in library_health
            ):
                incomplete_steps.append("Check 4: System Service")
            if not all(
                library_health[comp]["status"]
                for comp in rabbitmq_components
                if comp in library_health
            ):
                incomplete_steps.append("Check 5: RabbitMQ not installed/running")

            print("✗ The setup is incomplete. The following steps need attention:")
            for step in incomplete_steps:
                print(f"  - {step}")
            print("\nTo complete setup, run:")
            print("  vyomcloudbridge setup")
    except Exception as e:
        print("Error occurred in displaying system health")


# def load_env_from_file(vyom_services_env_file):
#     if not os.path.exists(vyom_services_env_file):
#         return
#     with open(vyom_services_env_file) as f:
#         for line in f:
#             if line.strip().startswith("export"):
#                 # parse lines like: export VAR=value
#                 parts = line.strip().replace("export", "", 1).strip().split("=", 1)
#                 if len(parts) == 2:
#                     key, val = parts
#                     val = val.strip()
#                     val = val.replace('"', "")
#                     os.environ[key.strip()] = val
#                     if key.strip() == "PYTHONPATH":
#                         for p in val.split(":"):
#                             if p not in sys.path:
#                                 sys.path.insert(0, p)


def get_vyom_env_file():
    vyom_env_file = None
    if os.path.isfile(vyom_variables_file):
        try:
            with open(vyom_variables_file, "r") as f:
                saved_data = json.load(f)
                vyom_env_file = saved_data.get("vyom_env_file")
                if vyom_env_file:
                    if os.path.isfile(vyom_env_file):
                        print(f"Using saved environment file path: {vyom_env_file}")
                        return vyom_env_file
                    else:
                        print(
                            f"Saved environment file path is invalid: {vyom_env_file}"
                        )
                        return None
                else:
                    print(f"Saved environment file path not found")
                    return None
        except Exception as e:
            print(f"Error reading saved env path from {vyom_variables_file}: {e}")
            return None
    return None


def main():
    # print("======= sys.path inspection before update =======")
    # for i, path in enumerate(sys.path):
    #     print(f"{i}: {path}")
    # print("===================================")

    # python_path = os.environ.get("PYTHONPATH", "")
    # ament_prefix_path = os.environ.get("AMENT_PREFIX_PATH", "")
    # ld_library_path = os.environ.get("LD_LIBRARY_PATH", "")
    # rmw_implementation = os.environ.get("RMW_IMPLEMENTATION", "")

    # print("In main before update, PYTHONPATH-", python_path)
    # print("In main before update, AMENT_PREFIX_PATH-", ament_prefix_path)
    # print("In main before update, LD_LIBRARY_PATH-", ld_library_path)
    # print("In main before update, RMW_IMPLEMENTATION-", rmw_implementation)

    # if not os.path.exists(vyom_services_env_file):
    #     python_path = os.environ.get("PYTHONPATH", "")
    #     ament_prefix_path = os.environ.get("AMENT_PREFIX_PATH", "")
    #     ld_library_path = os.environ.get("LD_LIBRARY_PATH", "")
    #     rmw_implementation = os.environ.get("RMW_IMPLEMENTATION", "")

    #     if (
    #         not python_path
    #         or not ament_prefix_path
    #         or not ld_library_path
    #         or not rmw_implementation
    #     ):
    #         missing_vars = []
    #         if not python_path:
    #             missing_vars.append("PYTHONPATH env variable")
    #         if not ament_prefix_path:
    #             missing_vars.append(
    #                 "Your ROS2 workspaces (AMENT_PREFIX_PATH env variable)"
    #             )
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
    #             + "\nPlease ensure you manually source them and then run `vyomcloudbridge setup` for the first time. <==="
    #         )
    #         sys.exit(0)
    # else:
    #     load_env_from_file(vyom_services_env_file)

    # python_path = os.environ.get("PYTHONPATH", "")
    # ament_prefix_path = os.environ.get("AMENT_PREFIX_PATH", "")
    # ld_library_path = os.environ.get("LD_LIBRARY_PATH", "")
    # rmw_implementation = os.environ.get("RMW_IMPLEMENTATION", "")
    # print("In main after reading, PYTHONPATH-", python_path)
    # print("In main after reading, AMENT_PREFIX_PATH-", ament_prefix_path)
    # print("In main after reading, LD_LIBRARY_PATH-", ld_library_path)
    # print("In main after reading, RMW_IMPLEMENTATION-", rmw_implementation)

    # # <TODO> Check whether sys.path was updated
    # print("======= sys.path inspection after update =======")
    # for i, path in enumerate(sys.path):
    #     print(f"{i}: {path}")
    # print("===================================")

    # # expected_paths = python_path.split(":")
    # # missing = [p for p in expected_paths if p not in sys.path]
    # # if missing:
    # #     print("Warning: These PYTHONPATH entries are missing in sys.path:")
    # #     for m in missing:
    # #         print("  -", m)

    # print("INSIDE MAIN-", os.environ.get("VYOM_ENV_READY"))
    if not os.environ.get("VYOM_ENV_READY"):
        vyom_env_file = get_vyom_env_file()
        if not vyom_env_file or not os.path.exists(vyom_env_file):
            # we have to varibale all variables, path and libray can be imported or not
            python_path = os.environ.get("PYTHONPATH", "")
            ament_prefix_path = os.environ.get("AMENT_PREFIX_PATH", "")
            ld_library_path = os.environ.get("LD_LIBRARY_PATH", "")

            if install_specs.is_full_install:
                if (
                    not python_path
                    or not ament_prefix_path
                    or not ld_library_path
                    # or not rmw_implementation
                ):
                    missing_vars = []
                    if not python_path:
                        missing_vars.append("PYTHONPATH env variable")
                    if not ament_prefix_path:
                        missing_vars.append(
                            "Your ROS2 workspaces (AMENT_PREFIX_PATH env variable)"
                        )
                    if not ld_library_path:
                        missing_vars.append("LD_LIBRARY_PATH env variable")
                    error_message = (
                        "Missing environment variables:\n - "
                        + "\n - ".join(missing_vars)
                    )
                    print(
                        "===> "
                        + error_message
                        + "\nPlease ensure you manually source them and then run `vyomcloudbridge setup` for the first time. <==="
                    )
                    sys.exit(0)
                else:
                    pass
            elif not python_path:
                missing_vars = []
                if not python_path:
                    missing_vars.append("PYTHONPATH env variable")
                error_message = "Missing environment variables:\n - " + "\n - ".join(
                    missing_vars
                )
                print(
                    "===> "
                    + error_message
                    + "\nPlease ensure you manually source them and then run `vyomcloudbridge setup` for the first time. <==="
                )
                sys.exit(0)
            else:
                # Everthing is working in this case, user has already sourced the environments
                pass
        else:
            # Compose the command to re-run the CLI inside a shell with ROS sourced
            command = f"source {vyom_env_file} && VYOM_ENV_READY=1 vyomcloudbridge {' '.join(sys.argv[1:])}"
            subprocess.run(["bash", "-lic", command])
            # -l = makes the shell act as a login shell, sourcing .bash_profile or .profile
            # -i = makes it interactive, any file like .bashrc will behave as if it’s a terminal shell.
            # -c = lets you run a command string.

            # shell_command = f"bash -lic \"{command}\""
            # subprocess.run(shell_command, shell=True)
            sys.exit(
                0
            )  # Exit the original process after spawning the ROS-enabled process

    # Only the ROS-enabled process continues from here
    import argparse
    import time
    from typing import Dict, Type
    from vyomcloudbridge.list_service import AVAILABLE_SERVICES
    from vyomcloudbridge.service_manager import ServiceManager
    from vyomcloudbridge.setup import setup

    parser = argparse.ArgumentParser(description="Service Manager CLI")
    manager = ServiceManager()

    subparsers = parser.add_subparsers(dest="action")

    # General Commands
    subparsers.add_parser("setup", help="Setup the service environment")
    subparsers.add_parser("restart", help="Restart all instances started by users")

    # list of running/all services
    list_parser = subparsers.add_parser("list", help="List running services")
    list_parser.add_argument(
        "--all", "-a", action="store_true", help="Show all services (including stopped)"
    )

    # library status, health
    subparsers.add_parser(
        "status",
        help="Check library installation/setup status, configurations, and requirements",
    )
    subparsers.add_parser(
        "health",
        help="Check library installation/setup health, configurations, and requirements",
    )

    subparsers.add_parser(
        "cleanup",
        help="Remove all files, directories, and services created by the library installation",
    )

    # Stop Command
    stop_parser = subparsers.add_parser("stop", help="Stop a running service")
    stop_parser.add_argument(
        "service",
        help="Service name (identifier of service)",
    )

    # Start Command (with service-specific arguments)
    start_parser = subparsers.add_parser("start", help="Start a service")
    start_parser.add_argument(
        "service", choices=AVAILABLE_SERVICES.keys(), help="Service name to start"
    )
    start_parser.add_argument(
        "--name", help="Custom instance name for the service instance"
    )
    start_parser.add_argument(
        "--system-default",
        action="store_true",
        help="Mark if the service is started by the system",
    )
    # Verbose/debug flags (standard Linux pattern)
    start_parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Enable verbose/debug mode: -v or --verbose sets DEBUG level logging",
    )
    start_parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode (equivalent to -v, sets logging to DEBUG level)",
    )

    # Service-specific arguments
    service_parsers = {
        "dirwatcher": start_parser.add_argument_group("Directory Watcher"),
        "streamconsumer": start_parser.add_argument_group("Stream Consumer"),
        "machinestats": start_parser.add_argument_group("Machine Stats Service"),
        "mavproxyhq": start_parser.add_argument_group("Mavproxyhq Service"),
        "missionstats": start_parser.add_argument_group("Mission Stats Monitor"),
        "queueworker": start_parser.add_argument_group("Queue Worker"),
        "robotstat": start_parser.add_argument_group("Robot Stats"),
        "rospublisher": start_parser.add_argument_group("Ros Publisher"),
        "vyomlistener": start_parser.add_argument_group("Vyom Listener"),
    }

    # Arguments for queueworker
    service_parsers["queueworker"].add_argument(
        "--multi-thread",
        action="store_true",
        help="Enable multi-threading for queueworker",
    )

    # Arguments for dirwatcher
    service_parsers["dirwatcher"].add_argument(
        "--mission-dir",
        action="store_true",
        help="If included, the <dir> provided will be considered a mission data directory.",
    )

    service_parsers["dirwatcher"].add_argument(
        "--send-live",
        action="store_true",
        help="If included (only along with --mission-dir), the device will send data for live, and with priroty.",
    )

    service_parsers["dirwatcher"].add_argument(
        "--merge-chunks",
        action="store_true",
        help="If included, combines S3 chunks after all have been uploaded.",
    )

    service_parsers["dirwatcher"].add_argument(
        "--preserve-file",
        action="store_true",
        help="If included, files will be moved to <dir>_preserve instead of being deleted after uploading to S3.",
    )

    service_parsers["dirwatcher"].add_argument(
        "--dir",
        required=False,
        help="Directory to watch.",
    )

    service_parsers["dirwatcher"].add_argument(
        "--dir-properties",
        required=False,
        help="Path to a directory properties JSON file or an inline JSON object.",
    )

    service_parsers["dirwatcher"].add_argument(
        "--priority",
        required=False,
        help="Priority order of files in this directory to be pushed.",
    )

    # Arguments for streamconsumer
    service_parsers["streamconsumer"].add_argument(
        "--stream-dir",
        required=False,
        help="Directory to watch for streamconsumer.",
    )

    service_parsers["streamconsumer"].add_argument(
        "--multi-machine",
        action="store_true",
        help="If included, the data in '--dir' will be considered for multiple devices, based on '--machine-key'",
    )

    service_parsers["streamconsumer"].add_argument(
        "--machine-key",
        required=False,
        help="Key for different machine, on basis of which we will decide different machines",
    )

    # service_parsers["streamconsumer"].add_argument(
    #     "--preserve-file",
    #     action="store_true",
    #     help="If included, files will be moved to <dir>_preserve instead of being deleted after uploading to S3.",
    # )

    # service_parsers["streamconsumer"].add_argument(
    #     "--priority",
    #     required=False,
    #     help="Priority order of files in this directory to be pushed.",
    # )

    args = parser.parse_args()
    # Check manually if action is missing
    if args.action is None:
        parser.print_help()
        sys.exit(1)

    if args.action == "setup":
        success = setup()
        sys.exit(0 if success else 1)

    if args.action == "restart":
        success = manager.restart_user_started_services()
        sys.exit(0 if success else 1)

    # Handle stopping a service
    if args.action == "stop":
        success = manager.stop_service(args.service)
        if success:
            print(f"Successfully stopped service: {args.service}")
        else:
            print(f"Failed to stop service: {args.service}")
        sys.exit(0 if success else 1)

    # Handle listing services
    if args.action == "list":
        services = manager.list_services()

        if not services:
            print("No services running OR started.")
            sys.exit(0)

        # Filter stopped services unless --all/-a is specified
        if not args.all:
            services = {
                key: val
                for key, val in services.items()
                if val.get("status") == "running"
            }
            if not services:
                print("No running services found. Use --all or -a to see all services.")
                sys.exit(0)

        print(
            "\nINSTANCE ID       SERVICE NAME     INSTANCE NAME    CREATED      STATUS       PID        COMMAND"
        )
        print("-" * 100)
        now = time.time()
        for instance_id, info in services.items():
            service_name = info.get("service_name", "unknown")
            command = f"\"{info.get('command', '')}\""
            pid = info.get("pid", "")
            name = info.get("name", "")

            # Format created time
            created_ago = format_duration(now - info.get("created", now))

            # Format status
            status = info.get("status", "unknown")
            if status == "running":
                status = f"Up {format_duration(info.get('uptime', 0))}"
            elif status == "exited":
                exit_code = info.get("exit_code", 0)
                exit_time = format_duration(now - info.get("exit_time", now))
                status = f"Exited ({exit_code}) {exit_time} ago"
            print(
                f"{instance_id:<17} {service_name:<16} {name:<16} {created_ago:<12} {status:<12} {pid:<10} {command}"
            )
        sys.exit(0)

    if args.action == "status":
        # Check overall system status
        library_health = manager.check_library_status()
        display_system_health(library_health)
        sys.exit(0)

    if args.action == "health":
        # Check overall system health
        library_health = manager.check_library_status()
        display_system_health(library_health)
        sys.exit(0)

    if args.action == "cleanup":
        confirm = (
            input(
                "WARNING: This will remove all vyomcloudbridge files and directories. Continue? [Y/n]: "
            )
            .strip()
            .lower()
        )

        if confirm not in ["y", "yes"]:
            print("Cleanup aborted.")
            sys.exit(0)
        print("Stopping all system background services...")
        stop_success = manager.stop_all_services()
        if stop_success:
            print(f"All background services of library have been stopped completely!")
        else:
            print(f"All background services stopping failed!")

        cleanup_results = manager.cleanup_system()
        manager.display_cleanup_results(cleanup_results)
        sys.exit(0)

    # Handle starting a service with proper argument validation
    if args.action == "start":
        service_args = {}
        debug_flags = {}  # Track flags separately for command display only
        if args.debug or args.verbose >= 1:
            log_level = logging.DEBUG
            service_args["log_level"] = log_level
            # Track which flag was used for command display (for service_manager only)
            if args.debug:
                debug_flags["_debug_flag"] = True
            else:
                debug_flags["_verbose_count"] = args.verbose

        if args.service == "queueworker":
            service_args["multi_thread"] = args.multi_thread

        if args.service == "dirwatcher":
            if not args.dir:
                print("Error: --dir is required for dirwatcher service")
                sys.exit(1)
            service_args["mission_dir"] = args.mission_dir
            service_args["send_live"] = args.send_live
            service_args["merge_chunks"] = args.merge_chunks
            service_args["preserve_file"] = args.preserve_file
            service_args["dir"] = args.dir
            if args.dir_properties:
                service_args["dir_properties"] = args.dir_properties
            if args.priority:
                service_args["priority"] = args.priority

        if args.service == "streamconsumer":
            if not args.stream_dir:
                print("Error: --stream-dir is required for streamconsumer service")
                sys.exit(1)
            service_args["stream_dir"] = args.stream_dir
            service_args["multi_machine"] = args.multi_machine
            service_args["machine_key"] = args.machine_key
            # service_args["preserve_file"] = args.preserve_file
            # if args.priority:
            #     service_args["priority"] = args.priority

        if args.service == "missionstats":
            pass

        if args.service == "machinestats":
            pass

        if args.service == "mavproxyhq":
            pass

        if args.service == "rospublisher":
            pass
        if args.service == "robotstat":
            pass

        service_class = AVAILABLE_SERVICES[args.service]
        success, instance_id, instance_name = manager.start_service(
            args.service,
            service_class,
            name=args.name,
            system_default=args.system_default,
            debug_flags=debug_flags,  # For command display only
            **service_args,
        )

        if success:
            print(f"Successfully started {args.service} service")
            print(f"Instance ID: {instance_id}")
            print(f"Instance Name: {instance_name}")
        else:
            print(f"Failed to start {args.service} service")

        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
