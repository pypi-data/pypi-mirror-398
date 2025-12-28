# vyomcloudbridge/service_manager.py
import sys
import time
import signal
import os
import json
import subprocess
import shutil
import uuid
import random
import multiprocessing
from typing import Dict, Any, Type, TypeVar, List, Optional
import logging
from vyomcloudbridge.list_service import AVAILABLE_SERVICES
from vyomcloudbridge.utils.common import ServiceAbstract, get_service_id
from vyomcloudbridge.utils.logger_setup import setup_logger
from vyomcloudbridge.constants.constants import log_dir, pid_file
from vyomcloudbridge.constants.constants import (
    cert_dir,
    cert_file_path,
    pri_key_file_path,
    root_ca_file_path,
)
from vyomcloudbridge.constants.constants import log_dir
from vyomcloudbridge.constants.constants import (
    vyom_root_dir,
    machine_config_file,
    start_script_file,
)
from vyomcloudbridge.constants.constants import (
    service_dir,
    service_file_path,
    service_root_file_path,
    machine_topics_file,
    vyom_variables_file,
)


logger = setup_logger(name=__name__, show_terminal=False, log_level=logging.INFO)
T = TypeVar("T", bound=ServiceAbstract)


class ServiceManager:
    def __init__(self):
        os.makedirs(log_dir, exist_ok=True)
        self.services: Dict[str, Any] = {}
        self.pid_file = pid_file
        self.load_running_services()
        self.stop_wait_time = 2
        self.alive_wait_time = 10

        self._update_service_status()

    def load_running_services(self):
        """Load information about running services from the PID file."""
        try:
            if os.path.exists(self.pid_file):
                with open(self.pid_file, "r") as f:
                    self.services = json.load(f)

                if not isinstance(self.services, dict):
                    logger.error("Invalid service data format, resetting")
                    self.services = {}
        except Exception as e:
            logger.error(f"Error loading service information: {e}")
            self.services = {}

    def save_running_services(self):
        """Save information about running services to the PID file."""
        try:
            with open(self.pid_file, "w") as f:
                json.dump(self.services, f)
        except Exception as e:
            logger.error(f"Error saving service information: {e}")

    def generate_instance_id(self, service_name: str, system_default: bool) -> str:
        """Generate a unique instance ID for a service."""
        service_id = "system" if system_default else get_service_id(service_name)
        return f"{service_id}-{str(uuid.uuid4())[:8]}"

    def generate_container_name(self) -> str:
        """Generate a random instance name (adjective_noun format)."""
        adjectives = [
            "brave",
            "swift",
            "calm",
            "wise",
            "happy",
            "funny",
            "quick",
            "keen",
            "busy",
        ]
        nouns = [
            "tiger",
            "panda",
            "eagle",
            "shark",
            "dolphin",
            "wolf",
            "bear",
            "hawk",
            "lion",
        ]
        return f"{random.choice(adjectives)}_{random.choice(nouns)}"

    def _service_runner(service_instance, alive_wait_time):
        try:
            service_instance.start()
            while service_instance.is_running:
                time.sleep(alive_wait_time)
        except KeyboardInterrupt:
            pass
        finally:
            service_instance.stop()

    def start_service(
        self,
        service_name: str,
        service_class: Type[ServiceAbstract],
        name: Optional[str] = None,
        system_default: bool = False,
        debug_flags: Optional[Dict] = None,
        *args,
        **kwargs,
    ):
        """Start a service with the given name and parameters.

        Args:
            service_name: The type of service to start
            service_class: The class that implements the service
            name: Optional custom instance name (if None, a random name will be generated)
            system_default: Whether this is a system default service
            debug_flags: Internal flags for command display (_debug_flag, _verbose_count)
            *args, **kwargs: Arguments to pass to the service constructor (log_level, multi_thread, etc.)
        """
        try:
            # Generate instance ID and instance name
            instance_id = self.generate_instance_id(service_name, system_default)
            instance_name = name if name else self.generate_container_name()

            # Ensure the instance name is unique
            existing_names = [info.get("name") for info in self.services.values()]
            while instance_name in existing_names:
                instance_name = self.generate_container_name()

            # Merge debug_flags into kwargs for command display
            display_kwargs = dict(kwargs)
            if debug_flags:
                display_kwargs.update(debug_flags)

            pid = os.fork() if hasattr(os, "fork") else None
            # print("PIDDDDDDD-", pid)
            # Create the service instance
            if pid == 0:  # Child process
                service_instance = service_class(*args, **kwargs)
                try:
                    service_instance.start()
                    while service_instance.is_running:
                        time.sleep(self.alive_wait_time)
                except KeyboardInterrupt:
                    pass
                finally:
                    service_instance.stop()
                    sys.exit(0)
            else:  # Parent process
                self.services[instance_id] = {
                    "pid": pid,
                    "start_time": time.time(),
                    "status": "running",
                    "system_default": system_default,
                    "service_name": service_name,
                    "name": instance_name,
                    "command": self._format_command(
                        service_name, name, system_default, display_kwargs
                    ),
                    "args": args,
                    "kwargs": kwargs,
                    "created": time.time(),
                }
                self.save_running_services()
                logger.info(
                    f"Started service {service_name} ({instance_name}) with PID {pid}"
                )
                return True, instance_id, instance_name

        except Exception as e:
            logger.error(f"Error starting service {service_name}: {e}")
            return False, None, None

    def _format_command(
        self, service_name: str, name: Optional[str], system_default: bool, kwargs: Dict
    ) -> str:
        """Format the command string for display in listing."""
        # Base command with the service name
        command = service_name

        # Add service-specific parameters
        if service_name == "queueworker":
            multi_thread = "--multi-thread" if kwargs.get("multi_thread") else ""
            command = f"queueworker {multi_thread}".strip()
        elif service_name == "dirwatcher":
            dir_path = kwargs.get("dir", "unknown")
            mission_dir = "--mission-dir" if kwargs.get("mission_dir") else ""
            merge_chunks = "--merge-chunks" if kwargs.get("merge_chunks") else ""
            send_live = "--send-live" if kwargs.get("send_live") else ""
            preserve_file = "--preserve-file" if kwargs.get("preserve_file") else ""
            command = f"dirwatcher --dir {dir_path} {mission_dir} {merge_chunks} {send_live} {preserve_file}".strip()
        elif service_name == "streamconsumer":
            stream_dir_path = kwargs.get("stream_dir", "unknown")
            multi_machine = "--multi-machine" if kwargs.get("multi_machine") else ""
            machine_key = kwargs.get("machine_key", "unknown")
            command = f"streamconsumer --stream-dir {stream_dir_path} {multi_machine} --machine-key {machine_key}".strip()
        elif service_name == "missionstats":
            command = "missionstats"
        elif service_name == "machinestats":
            command = "machinestats"
        elif service_name == "mavproxyhq":
            command = "mavproxyhq"
        elif service_name == "robotstat":
            command = "robotstat"

        if name:
            command += f" --name {name}"
        if system_default:
            command += " --system-default"

        # Standard Linux pattern: -v or --debug both mean DEBUG level
        if kwargs.get("_debug_flag"):
            command += " --debug"
        elif kwargs.get("_verbose_count", 0) >= 1:
            # Show -v for single, -vv for double (both set DEBUG)
            if kwargs.get("_verbose_count", 0) >= 2:
                command += " -vv"
            else:
                command += " -v"

        return command

    def stop_service(self, identifier: str) -> bool:
        """Stop a running service by instance ID or instance name.

        Args:
            identifier: Either an instance ID or instance name
        """
        try:
            # Try by instance ID
            if identifier in self.services:
                return self._stop_by_instance_id(identifier)

            # Try by instance name
            for instance_id, info in list(self.services.items()):
                if info.get("name") == identifier:
                    return self._stop_by_instance_id(instance_id)

            # Try by service type (stop all)
            instances_to_stop = [
                instance_id
                for instance_id, info in list(self.services.items())
                if info.get("service_name") == identifier
            ]
            if instances_to_stop:
                success = True
                for instance_id in instances_to_stop:
                    success = self._stop_by_instance_id(instance_id) and success
                return success

            logger.warning(f"No service found with identifier: {identifier}")
            return False

        except Exception as e:
            logger.error(f"Error stopping service {identifier}: {e}")
            return False

    def _stop_by_instance_id(self, target_instance_id: str) -> bool:
        try:
            service_info = self.services.get(target_instance_id)
            if not service_info:
                logger.warning(f"No such instance: {target_instance_id}")
                return False

            service_pid = service_info.get("pid", "")
            is_running = self.is_pid_running(service_pid)
            if is_running:
                try:
                    os.kill(service_pid, signal.SIGTERM)
                    time.sleep(self.stop_wait_time)
                    if self.is_pid_running(service_pid):
                        os.kill(service_pid, signal.SIGKILL)
                except Exception as e:
                    logger.error(
                        f"Could not terminate the service instance instance_id-{target_instance_id}"
                    )
                    return False
            else:
                service_info["status"] = "stopped"
                logger.warning(
                    f"Process already terminated or not found for {target_instance_id}"
                )

            # del self.services[instance_id]
            updated_list = {}
            for instance_id, info in list(self.services.items()):
                if instance_id != target_instance_id:
                    updated_list[instance_id] = info
            self.services = updated_list
            self.save_running_services()
            return True
        except Exception as e:
            logger.error(f"Error stopping service instance {instance_id}: {e}")
            return False

    def is_service_running(self, instance_id: str) -> bool:
        """Check if a service instance is running."""
        if instance_id not in self.services:
            return False

        pid = self.services[instance_id]["pid"]
        return self.is_pid_running(pid)

    @staticmethod
    def is_pid_running(pid: int) -> bool:
        """Check if a process with the given PID is running."""
        try:
            os.kill(pid, 0)
            return True
        except (ProcessLookupError, PermissionError):
            return False

    def _update_service_status(self):
        """Update the status of all services in real-time."""
        for instance_id, info in list(self.services.items()):
            info: Dict
            pid = info.get("pid")
            # Skip if no PID (shouldn't happen, but as a safeguard)
            if not pid:
                continue

            is_running = self.is_pid_running(pid)
            current_status = info.get("status")

            # If status changed from running to not running
            if not is_running:
                self.services[instance_id]["status"] = "exited"
                self.services[instance_id]["exit_time"] = time.time()
                self.services[instance_id]["exit_code"] = 0  # Default exit code
                logger.info(
                    f"Service {instance_id} is no longer running, marking as exited"
                )
            else:
                self.services[instance_id]["status"] = "running"

        # Save updated statuses
        self.save_running_services()

    def list_services(self) -> Dict[str, Dict]:
        """List all services and their status in real-time."""
        # Update status before listing
        self._update_service_status()

        current_services = {}
        for instance_id, info in list(self.services.items()):
            status = info.get("status", "unknown")
            current_time = time.time()
            if status == "running":
                uptime = current_time - info.get("start_time", current_time)
            else:
                uptime = info.get("exit_time", current_time) - info.get(
                    "start_time", current_time
                )

            current_services[instance_id] = {
                **info,
                "uptime": uptime,
            }

        return current_services

    def check_library_status(self) -> Dict[str, Dict[str, Any]]:
        """Check overall system status and requirements."""
        status = {}

        # Step 1: Check certificate directory and files
        status["certificates_dir"] = {
            "status": os.path.exists(cert_dir),
            "message": f"Certificate directory at {cert_dir}",
        }

        status["cert_file"] = {
            "status": os.path.exists(cert_file_path),
            "message": f"Certificate file at {cert_file_path}",
        }

        status["private_key"] = {
            "status": os.path.exists(pri_key_file_path),
            "message": f"Private key file at {pri_key_file_path}",
        }

        status["root_ca"] = {
            "status": os.path.exists(root_ca_file_path),
            "message": f"Root CA file at {root_ca_file_path}",
        }

        # Step 2: Check log directory
        status["log_directory"] = {
            "status": os.path.exists(log_dir),
            "message": f"Log directory at {log_dir}",
        }

        # Step 3: Check home directory, machine config file, and start script file
        status["root_directory"] = {
            "status": os.path.exists(vyom_root_dir),
            "message": f"Root directory at {vyom_root_dir}",
        }

        status["machine_config"] = {
            "status": os.path.exists(machine_config_file),
            "message": f"Machine configuration file at {machine_config_file}",
        }

        status["start_script"] = {
            "status": os.path.exists(start_script_file)
            and os.access(start_script_file, os.X_OK),
            "message": f"Start script at {start_script_file}",
        }

        # Step 4: Check system service file
        status["service_dir"] = {
            "status": os.path.exists(service_dir),
            "message": f"Service directory at {service_dir}",
        }

        status["service_file_path"] = {
            "status": os.path.exists(service_file_path),
            "message": f"Service file at {service_file_path}",
        }

        status["service_root_file_path"] = {
            "status": os.path.exists(service_root_file_path),
            "message": f"Service file at {service_root_file_path}",
        }

        # Step 5: Check RabbitMQ installation and status
        rabbitmq_installed = shutil.which("rabbitmqctl") is not None

        if rabbitmq_installed:
            try:
                result = subprocess.run(
                    ["rabbitmqctl", "status"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=5,
                )
                rabbitmq_running = result.returncode == 0
                rabbitmq_msg = (
                    "Running" if rabbitmq_running else "Installed but not running"
                )
            except (subprocess.SubprocessError, subprocess.TimeoutExpired):
                rabbitmq_running = False
                rabbitmq_msg = "Installed but service status check failed"
        else:
            rabbitmq_running = False
            rabbitmq_msg = "Not installed"

        status["rabbitmq"] = {"status": rabbitmq_running, "message": rabbitmq_msg}

        # Check Python dependencies (RabbitMQ client)
        try:
            import pika  # For RabbitMQ

            pika_status = True
            pika_msg = f"Installed (version {pika.__version__})"
        except ImportError:
            pika_status = False
            pika_msg = "Not installed"

        status["pika_library"] = {"status": pika_status, "message": pika_msg}
        return status

    def stop_all_services(self):
        """
        Restart all services marked as system_default=True from the loaded services file.
        This function is meant to be called on system reboot.
        """
        logger.info("Stopping all system background services...")

        try:
            subprocess.run(
                ["systemctl", "stop", "vyomcloudbridge.service"], check=False
            )
        except Exception as e:
            pass

        # Load running services from the pid file
        self.load_running_services()

        services_to_delete = {k: v for k, v in self.services.items()}
        for instance_id, service_info in services_to_delete.items():
            old_pid = service_info.get("pid", "")
            del self.services[instance_id]
            try:
                os.kill(old_pid, signal.SIGTERM)
                time.sleep(self.stop_wait_time)
                if self.is_pid_running(old_pid):
                    os.kill(old_pid, signal.SIGKILL)
            except Exception as e:
                pass
        self.save_running_services()

        success = True
        try:
            subprocess.run(
                ["systemctl", "stop", "vyomcloudbridge.service"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            subprocess.run(
                ["systemctl", "disable", "vyomcloudbridge.service"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            success = True
        except Exception as e:
            success = False
            logger.error(f"Failed to stop/disable service: {str(e)}")

        logger.info(f"All background services of library stopped complete!")
        return success

    def restart_user_started_services(self):
        """
        Restart all services marked as system_default=True from the loaded services file.
        This function is meant to be called on system reboot.
        """
        logger.info("Restarting system default services...")

        # Load running services from the pid file
        self.load_running_services()

        # Counter for tracking restart results
        restarted = 0
        failed = 0

        # Go through each service in the loaded file
        # user_started_services = {
        #     k: v for k, v in self.services.items() if not v.get("system_default", False)
        # }

        services_to_delete = {
            k: v for k, v in self.services.items() if v.get("system_default", False)
        }
        for instance_id, service_info in services_to_delete.items():
            old_pid = service_info.get("pid", "")
            del self.services[instance_id]
            try:
                os.kill(old_pid, signal.SIGTERM)
                time.sleep(self.stop_wait_time)
                if self.is_pid_running(old_pid):
                    os.kill(old_pid, signal.SIGKILL)
            except Exception as e:
                pass
        self.save_running_services()

        for instance_id, service_info in self.services.items():
            instance_id: str
            service_info: Dict[str, Any]

            service_name = service_info.get("service_name")
            instance_name = service_info.get("name")

            logger.info(
                f"Restarting system default service: {service_name} ({instance_name})"
            )

            try:
                service_class: Type[ServiceAbstract] = AVAILABLE_SERVICES[service_name]

                if not service_class:
                    logger.error(f"Unknown service type: {service_name}")
                    failed += 1
                    continue

                kwargs = service_info.get("kwargs", {})
                args = service_info.get("args", [])

                old_pid = service_info.get("pid", "")
                # just stopping pid if already running
                try:
                    os.kill(old_pid, signal.SIGTERM)
                    time.sleep(self.stop_wait_time)
                    if self.is_pid_running(old_pid):
                        os.kill(old_pid, signal.SIGKILL)
                except Exception as e:
                    pass

                service_instance: ServiceAbstract = service_class(*args, **kwargs)

                pid = os.fork() if hasattr(os, "fork") else None

                if pid == 0:  # Child process
                    try:
                        service_instance.start()
                        while service_instance.is_running:
                            time.sleep(self.alive_wait_time)
                    except KeyboardInterrupt:
                        pass
                    finally:
                        service_instance.stop()
                        sys.exit(0)
                else:  # Parent process
                    # Preserve the original service_info and only update necessary fields
                    service_info["pid"] = pid
                    service_info["start_time"] = time.time()
                    service_info["status"] = "running"

                    # Keep the original instance_id and service_info structure
                    self.services[instance_id] = service_info

                    self.save_running_services()
                    logger.info(
                        f"Restarted service {service_name} ({instance_name}) with PID {pid}"
                    )
                    restarted += 1

            except Exception as e:
                logger.error(f"Error restarting service {service_name}: {e}")
                failed += 1

        logger.info(
            f"System default service restart complete. Restarted: {restarted}, Failed: {failed}"
        )
        return restarted, failed

    def cleanup_system(self) -> Dict[str, bool]:
        """Clean up all files and directories created by the vyomcloudbridge installation.

        Returns:
            Dict[str, bool]: Status of each cleanup operation
        """
        cleanup_results = {}

        # Define all paths that need to be cleaned up
        paths_to_remove = [
            # Certificates
            cert_dir,
            cert_file_path,
            pri_key_file_path,
            root_ca_file_path,
            # Home directory and config files
            vyom_root_dir,
            machine_config_file,
            start_script_file,
            # Service files
            service_file_path,
            service_root_file_path,
            machine_topics_file,
            vyom_variables_file,
        ]

        # Remove each path
        for path in paths_to_remove:
            try:
                if os.path.exists(path):
                    if os.path.isdir(path):
                        shutil.rmtree(path)
                    else:
                        os.remove(path)
                    cleanup_results[path] = True
                else:
                    cleanup_results[path] = True  # Path didn't exist
            except Exception as e:
                cleanup_results[path] = False
                logger.error(f"Failed to remove {path}: {str(e)}")

        # Note: We don't uninstall RabbitMQ or pika as they might be used by other applications

        return cleanup_results

    def display_cleanup_results(self, results: Dict[str, bool]) -> None:
        """Display the results of the cleanup operation.

        Args:
            results: Dictionary of cleanup operations and their status
        """
        print("\nVyomCloudBridge Cleanup Results:")
        print("=============================")

        # Group results by type
        sections = {
            "Certificates and Security": [
                cert_dir,
                cert_file_path,
                pri_key_file_path,
                root_ca_file_path,
            ],
            "Logging": [log_dir],
            "Configuration Files": [
                vyom_root_dir,
                machine_config_file,
                start_script_file,
            ],
            "System Service": [service_file_path, "service_stopped"],
            "System Root Service": [service_root_file_path, "service_stopped"],
        }

        all_success = True

        for section, paths in sections.items():
            print(f"\n{section}:")
            print("-" * len(section))

            for path in paths:
                if path in results:
                    status = results[path]
                    symbol = "✓" if status else "✗"
                    if path == "service_stopped":
                        print(
                            f"{symbol} Service {'stopped and disabled' if status else 'failed to stop'}"
                        )
                    else:
                        action = "Removed" if status else "Failed to remove"
                        print(f"{symbol} {action} {path}")

                    if not status:
                        all_success = False

        print("\nOverall Status:")
        print("--------------")
        if all_success:
            print("✓ All vyomcloudbridge files and directories successfully removed.")
        else:
            print("✗ Some cleanup operations failed. See details above.")
