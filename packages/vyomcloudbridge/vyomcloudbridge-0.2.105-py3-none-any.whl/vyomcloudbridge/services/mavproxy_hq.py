# === Standard Library Imports ===
import glob
import os
import shutil
import subprocess
import threading
import time
from datetime import datetime
from serial import PortNotOpenError, SerialException
import serial.tools.list_ports
import re

# === Third-Party Imports ===
import psutil
from pymavlink import mavutil

# === Application-Specific Imports ===
from vyomcloudbridge.utils.common import ServiceAbstract
from vyomcloudbridge.utils.configs import Configs


class MavproxyHq(ServiceAbstract):
    def __init__(self, daemon: bool = False, log_level=None):
        try:
            super().__init__(log_level=log_level)
            # machine configs
            self.machine_config = Configs.get_machine_config()
            self.machine_id = self.machine_config.get("machine_id", "-") or "-"
            self.logger.debug(f"Machine ID: {self.machine_id}")

            # service parameter
            self.is_running = False
            self.daemon = daemon

            # Mav proxy
            self.mavproxy_proc = None
            self.serial_port_path = None
            self.uart_baud = 57600  # Recommended are 57600, 921600 ... from list [9600, 57600, 921600, 115200] TODO Deepak
            self.sysid_thismav = 156  # system ID
            self.compid_thismav = 191  # component ID
            self.is_connected = False
            self.connection_lock = threading.Lock()
            self._connection_in_progress = False
            self.max_reconnect_attempts = 3
            self.base_reconnect_delay = 2  # Base delay in seconds
            self.max_reconnect_delay = 60
            self.conn_health_check_delay = 30
            self.udp_heartbeat_timeout = 5
            self.test_connection = None

            # TODO, Param PART

            # Log file details
            self.base_log_dir = "/var/log/vyomcloudbridge/mavlogs"
            self.log_dir = f"{self.base_log_dir}/{self.machine_id}/"
            self.log_filepath = None
            self._setup_log_directories()

            # Deepak's Variable TODO Deepak
            self.mavproxy_hq_thread = None
            self.prev_armed = None
            self.curr_armed = None

            self.logger.info("MavproxyHq service initialized")
        except Exception as e:
            self.logger.error(f"Error initializing MavproxyHq service: {str(e)}")

    def _setup_log_directories(self):
        try:
            # create dir if not there
            if not os.path.exists(self.log_dir):
                self.logger.info(f"Creating log directory: {self.log_dir}")
                os.makedirs(self.log_dir, exist_ok=True)
            else:
                self.logger.debug(f"Log directory exists: {self.log_dir}")

            # get new file name on reboot
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_filename = f"mavlog_{timestamp}.tlog"
            self.log_filepath = os.path.join(self.log_dir, log_filename)

            # Ensure log directory exists
            # self.logger.info("MAVProxy log files:")
            # subprocess.run(["ls", "-lh", self.log_dir])
        except Exception as e:
            self.logger.error(f"Error in _setup_log_directories: {str(e)}")
            raise

    def create_copy_data_logger(self):
        try:
            dest_log_dir_base = f"{self.base_log_dir}/dir_watch_data_logs/logs/"

            if not os.path.isdir(self.log_dir):
                self.logger.info(f"Directory not found: {self.log_dir}")
                return

            # Find all .BIN files
            bin_files = glob.glob(os.path.join(self.log_dir, "*.BIN"))

            if not bin_files:
                self.logger.info("No numbered .BIN files found.")
            else:
                # Sort by numeric filename (e.g., 1.BIN → 1)
                bin_files.sort(key=lambda f: int(os.path.basename(f).split(".")[0]))
                latest_bin = bin_files[-1]
                self.logger.info(f"Copying latest BIN file: {latest_bin}")

                now = time.time()
                timestamp = int(now * 1000)

                date_folder = datetime.fromtimestamp(now).strftime("%Y_%m_%d")
                dest_log_dir = os.path.join(dest_log_dir_base, date_folder)

                os.makedirs(dest_log_dir, exist_ok=True)

                # Rename while copying to destination
                original_name = os.path.basename(latest_bin)
                new_name = f"{os.path.splitext(original_name)[0]}_{timestamp}.BIN"
                renamed_path = os.path.join(dest_log_dir, new_name)

                # Copy with new name only
                shutil.copyfile(latest_bin, renamed_path)
                self.logger.info(f"Copied and renamed to: {renamed_path}")

        except Exception as e:
            self.logger.error(f"Error copying data logger: {str(e)}")

    def get_working_port(self):
        """
        Lists all available serial ports, and return working if available.
        """
        try:
            ports = serial.tools.list_ports.comports()
            if not ports:
                self.logger.error("No serial ports found.")
                return

            working_path = []
            for port in sorted(ports):
                if port.serial_number and (
                    port.serial_number == "420033000C51333130373938"
                    or port.serial_number == "20002C001251303437363830"
                    or port.serial_number == "0001"
                ):  # TODO, Deepak move this list in init
                    working_path.append(port.device)

            if len(working_path) > 1:
                working_path.sort(key=lambda x: int(re.search(r"\d+$", x).group()))
                return working_path[0]
            elif len(working_path) == 1:
                return working_path[0]
            else:
                return None
        except Exception as e:
            self.logger.error(f"Error getting working port: {str(e)}")
            return None

    def _is_connection_healthy(self):
        """Check if CubeOrange is sending MAVLink heartbeat on the serial connection"""
        try:
            if not self.serial_port_path:
                return False

            if not self.test_connection:
                self.test_connection = mavutil.mavlink_connection(
                    "udp:127.0.0.1:14700",
                    source_system=self.sysid_thismav,
                    source_component=self.compid_thismav,
                )

            self.test_connection.wait_heartbeat(timeout=self.udp_heartbeat_timeout)
            return True

        except Exception as e:
            self.test_connection = None
            self.logger.error(f"Error receiving heartbeat: {str(e)}")
            return False

    def _create_mavproxy_conn(self):
        """Create a new Mavproxy connection with exponential backoff"""
        with self.connection_lock:  # Acquire lock to prevent concurrent attempts
            if self.is_connected and self._is_connection_healthy():
                self._connection_in_progress = False
                self.logger.info(
                    "Connection already established, skipping reconnection"
                )
                return

            self._connection_in_progress = True
            try:
                error = ""
                for attempt in range(self.max_reconnect_attempts):
                    try:
                        # Use exponential backoff for reconnection attempts

                        # Step 1: get fresh port for creating connection
                        self.serial_port_path = self.get_working_port()
                        if not self.serial_port_path:
                            raise SerialException(
                                "No working serial connection found for CubeOrange."
                            )
                        self.logger.info(
                            f"Detected serial_port_path: {self.serial_port_path}"
                        )

                        # Step 2: Build MAVProxy command
                        mavproxy_cmd = [
                            "/vyomos/venv/bin/mavproxy.py",
                            f"--master={self.serial_port_path},{self.uart_baud}",
                            "--daemon",
                            "--out=udp:127.0.0.1:14550",
                            "--out=udp:127.0.0.1:14555",
                            "--out=udp:127.0.0.1:14556",
                            "--out=udp:127.0.0.1:14557",
                            "--out=udp:127.0.0.1:14560",
                            "--out=udp:127.0.0.1:14565",
                            "--out=udp:127.0.0.1:14600",
                            "--out=udp:127.0.0.1:14700",
                            f"--source-system={self.sysid_thismav}",
                            f"--source-component={self.compid_thismav}",
                            f"--logfile={self.log_filepath}",
                            "--load-module=dataflash_logger",
                        ]

                        # Step 3: Launch MAVProxy
                        with open("/tmp/mavproxy.log", "w") as log_out:
                            self.mavproxy_proc = subprocess.Popen(
                                mavproxy_cmd, stdout=log_out, stderr=subprocess.STDOUT
                            )
                            self.logger.debug(
                                f"MAVProxy started in background (PID: {self.mavproxy_proc.pid})"
                            )

                        if not self._is_connection_healthy():
                            raise ConnectionError("Unhealthy connected detected.")
                        self.logger.info(
                            "Heart beat received. MavProxy initialized successfully!"
                        )
                        self.is_connected = True
                        return

                    except Exception as e:
                        error = str(e)
                        self.logger.debug(
                            f"MavProxy connection attempt {attempt + 1} failed: {str(e)}"
                        )
                        delay = min(
                            self.base_reconnect_delay * (2**attempt),
                            self.max_reconnect_delay,
                        )
                        if attempt < self.max_reconnect_attempts - 1:
                            time.sleep(delay)

                # If all attempts fails
                raise ConnectionError(
                    f"MavProxy conn failed in {self.max_reconnect_attempts} attempts: {error}"
                )
            finally:
                self._connection_in_progress = False

    def _start_mavproxy_conn_monitor(self):
        """
        Start a background thread to monitor connection health
        Uses built-in AWS IoT SDK reconnection mechanisms
        """

        def monitor_connection():
            while self.is_running:  # as long as service is running
                try:
                    if not self.is_connected:  # case: when not_connected is known
                        self._kill_a_subprocess(self.mavproxy_proc)
                        self._create_mavproxy_conn()
                    elif (
                        not self.get_working_port()
                    ):  # case: serial_port_path disconnect check
                        self.is_connected = False
                        self.serial_port_path = None

                        retries = 0  # retrying port check 5 times
                        while retries < 5 and not self.get_working_port():
                            time.sleep(self.conn_health_check_delay)
                            retries += 1
                        self._kill_a_subprocess(self.mavproxy_proc)
                        self._create_mavproxy_conn()
                    elif self.is_connected:  # case: revalidate connection
                        try:
                            if not self._is_connection_healthy():
                                raise ConnectionError("Unhealthy connected detected.")
                        except Exception as e:
                            self.logger.error(
                                f"Connection monitoring, heartbeat failed: {str(e)}, reconnecting..."
                            )
                            self.is_connected = False
                            self._kill_a_subprocess(self.mavproxy_proc)
                            self._create_mavproxy_conn()
                    time.sleep(self.conn_health_check_delay)
                except Exception as e:
                    self.is_connected = False
                    self.logger.error(
                        f"mavproxy_hq connection monitoring failed: {str(e)}"
                    )
                    time.sleep(self.conn_health_check_delay)

        # Start monitoring in a daemon thread
        monitor_thread = threading.Thread(target=monitor_connection, daemon=True)
        monitor_thread.start()

    def start(self):
        try:
            self.is_running = True

            # Mavproxy connection and monitoring
            if self.daemon:
                self._start_mavproxy_conn_monitor()
                self.logger.info(
                    "MavProxy connection init and background monitoring thread started..."
                )
            else:
                try:
                    self._create_mavproxy_conn()
                except Exception as e:
                    self.logger.error(
                        f"Error initializing mavproxy connection: {str(e)}"
                    )
                    #
                    self._start_mavproxy_conn_monitor()
                    self.logger.info(
                        "MavProxy connection init and monitoring thread started in background..."
                    )
                if self.is_connected:
                    self._start_mavproxy_conn_monitor()
                    self.logger.info("MavProxy background monitoring thread started...")

            # TODO, Mavros PART

            # TODO, Deepak what is this for??
            def arm_state_monitor_loop():
                master = mavutil.mavlink_connection("udp:127.0.0.1:14700")
                master.wait_heartbeat()
                self.logger.debug(
                    "Heart beat received from system (system %u component %u)"
                    % (master.target_system, master.target_component)
                )

                def is_armed(base_mode):
                    return (base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED) != 0

                while self.is_running:
                    try:
                        msg = master.recv_match(type="HEARTBEAT", blocking=True)
                        if not msg:
                            continue

                        if msg.get_srcComponent() != 1:
                            continue

                        self.curr_armed = is_armed(msg.base_mode)
                        self.logger.debug(
                            f"[DEBUG] base_mode: {msg.base_mode}, prev_armed: {self.prev_armed}, curr_armed: {self.curr_armed}"
                        )

                        if self.prev_armed is not None:
                            if self.prev_armed is True and self.curr_armed is False:
                                self.logger.info("Transition: ARMED → DISARMED")
                                self.create_copy_data_logger()

                            elif self.prev_armed is False and self.curr_armed is True:
                                self.logger.info("Transition: DISARMED → ARMED")

                        self.prev_armed = self.curr_armed

                    except Exception as e:
                        self.logger.error(f"Error in arm state monitor loop: {str(e)}")
                        time.sleep(1)

            # Create and start the thread
            self.mavproxy_hq_thread = threading.Thread(
                target=arm_state_monitor_loop, daemon=True
            )
            self.mavproxy_hq_thread.start()

            self.logger.info("MavproxyHq service started!")

        except Exception as e:
            self.logger.error(f"Error starting Mavproxy service: {str(e)}")
            self.stop()
            raise

    def _kill_a_subprocess(self, proc):
        try:
            if proc:
                parent = psutil.Process(proc.pid)
                children = parent.children(recursive=True)
                for child in children:
                    self.logger.debug(f"Killing child process: {child.pid}")
                    child.kill()
                self.logger.debug(f"Killing a process: {proc.pid}")
                parent.kill()
                self.logger.debug("process terminated.")
        except Exception as e:
            self.logger.error(f"Error stopping a proccess: {str(e)}")

    def stop(self):
        self.is_running = False
        # Wait for thread to finish
        if (
            hasattr(self, "mavproxy_hq_thread")
            and self.mavproxy_hq_thread
            and self.mavproxy_hq_thread.is_alive()
        ):
            self.mavproxy_hq_thread.join(timeout=5)

        if self.mavproxy_proc:
            self.logger.info("Attempting to stop MAVProxy process...")

            # Get all children and kill them too
            try:
                parent = psutil.Process(self.mavproxy_proc.pid)
                children = parent.children(recursive=True)
                for child in children:
                    self.logger.info(f"Killing child process: {child.pid}")
                    child.kill()
                self.logger.info(f"Killing MAVProxy process: {self.mavproxy_proc.pid}")
                parent.kill()
                self.logger.info("MAVProxy process terminated.")
            except Exception as e:
                self.logger.error(f"Error stopping MAVProxy: {str(e)}")
        else:
            self.logger.warning("No MAVProxy process to stop.")

    def cleanup(self):
        pass

    def is_healthy(self):
        return self.is_running

    def __del__(self):
        """Destructor called by garbage collector to ensure resources are cleaned up, when object is about to be destroyed"""
        try:
            self.logger.error(
                "Destructor called by garbage collector to cleanup MavproxyHQ service"
            )
            self.stop()
        except Exception as e:
            pass


def main():
    """Mavproxy service"""
    print("Starting Mavproxy service")

    mavproxy_service = MavproxyHq()

    try:
        # Simulate data arriving
        mavproxy_service.start()
        # Let it run for a short while
        time.sleep(200)

    finally:
        # Clean up
        mavproxy_service.stop()

    print("Completed Mavproxy service")


if __name__ == "__main__":
    main()
