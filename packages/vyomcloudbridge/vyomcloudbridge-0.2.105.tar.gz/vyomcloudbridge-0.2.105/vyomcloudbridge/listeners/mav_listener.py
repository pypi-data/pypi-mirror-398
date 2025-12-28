# /vyomcloudbridge/listeners/mav_listener.py
import json
import threading
import time
import uuid

# Third-party imports
from pymavlink import mavutil

# Local application imports
from vyomcloudbridge.utils.abc_listener import AbcListener
from vyomcloudbridge.utils.configs import Configs
from vyomcloudbridge.utils.logger_setup import setup_logger
from rclpy_message_converter import message_converter
from vyomcloudbridge.utils.shared_memory import SharedMemoryUtil


class MavListener(AbcListener):
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, daemon: bool = False, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(MavListener, cls).__new__(cls)
                    print("MavListener singleton initialized")
        print("MavListener client service started")
        return cls._instance

    def __init__(self, daemon: bool = False, log_level=None):
        try:
            super().__init__(
                multi_thread=False, daemon=False, log_level=log_level
            )  # TODO: we can remove multi_thread, daemon later
            self.logger.info("MavListener initializing...")

            # compulsory
            self.channel = "mavlink"
            # machine configs
            self.machine_config = Configs.get_machine_config()
            self.machine_id = self.machine_config.get("machine_id", "-") or "-"

            # shared memory
            self.shared_mem = SharedMemoryUtil(log_level=log_level)

            self.mission_id = 0
            self.user_id = 1
            self.mission_status = 2
            self.chunk_retry_count = 3
            self.chunk_retry_timeout = 5
            self.chunk_result_recheck_delay = 0.1
            self.udp_connection_timeout = 5
            self.udp_heartbeat_timeout = 5

            self.ack_data_received = {}
            self.data_received = {}

            # connection
            self.daemon = daemon
            self.master = None
            self.is_connected = False
            self.connection_lock = threading.Lock()
            self._connection_in_progress = False

            self.max_reconnect_attempts = 3
            self.base_reconnect_delay = 2  # Base delay in seconds
            self.max_reconnect_delay = 60
            self.conn_health_check_delay = 30

            self.connection_wait_time_sleep = 5

            if self.daemon:
                self._start_backgd_conn_monitor()
                self.logger.info(
                    "MavListener initialization in background thread started..."
                )
            else:
                self._create_mav_connection()
                self._start_backgd_conn_monitor()
                self.logger.info(
                    "MavListener initialized successfully, with health monitoring!"
                )
        except Exception as e:
            self.logger.error(f"Error init MavListener: {str(e)}")
            raise

    def _is_connection_healthy(self):
        """Get the latest heartbeat message from the MAVLink connection"""
        try:
            if self.master:
                self.master.wait_heartbeat(timeout=self.udp_heartbeat_timeout)
                return True
            else:
                self.logger.error("MAVLink master connection not initiated")
                return False
        except Exception as e:
            self.logger.error(f"Error receiving heartbeat: {str(e)}")
            return False

    def _create_mav_connection(self):
        """Create a new Mav connection with exponential backoff"""
        with self.connection_lock:  # Acquire lock to prevent concurrent attempts
            if self.is_connected:
                self._connection_in_progress = False
                self.logger.info(
                    "Connection already established, skipping reconnection"
                )
                return

            self._connection_in_progress = True
            try:
                for attempt in range(self.max_reconnect_attempts):
                    try:
                        # Use exponential backoff for reconnection attempts
                        self.master = mavutil.mavlink_connection(
                            "udp:127.0.0.1:14557",
                            source_system=101,
                            source_component=191,
                        )
                        if not self._is_connection_healthy():
                            raise ConnectionError("Heartbeat not received")
                        self.logger.info(
                            "Heart beat received. MavListener initialized successfully!"
                        )
                        self.is_connected = True
                        return

                    except Exception as e:
                        self.logger.debug(
                            f"Warning: MavListener connection attempt {attempt + 1} failed: {str(e)}"
                        )
                        delay = min(
                            self.base_reconnect_delay * (2**attempt),
                            self.max_reconnect_delay,
                        )
                        if attempt < self.max_reconnect_attempts - 1:
                            time.sleep(delay)

                # If all attempts fail
                raise ConnectionError(
                    f"Could not connect to MavLink after {self.max_reconnect_attempts} attempts"
                )
            finally:
                self._connection_in_progress = False

    def _start_backgd_conn_monitor(self):
        """
        Start a background thread to monitor connection health
        Uses built-in AWS IoT SDK reconnection mechanisms
        """

        def monitor_connection():
            while True:
                try:
                    if not self.is_connected:
                        self._create_mav_connection()
                    elif self.is_connected:  # revalidate connection
                        try:
                            if not self._is_connection_healthy():
                                raise ConnectionError("Heartbeat not received")
                        except Exception as e:
                            self.logger.error(
                                f"Connection monitoring, heartbeat failed: {str(e)}, reconnecting..."
                            )
                            self.is_connected = False
                            self._create_mav_connection()
                    time.sleep(self.conn_health_check_delay)
                except Exception as e:
                    self.is_connected = False
                    self.logger.error(
                        f"mav_listener connection monitoring failed: {str(e)}"
                    )
                    time.sleep(self.conn_health_check_delay)

        # Start monitoring in a daemon thread
        monitor_thread = threading.Thread(target=monitor_connection, daemon=True)
        monitor_thread.start()

    def set_ack_data_received(self, data_name):  # AMAR
        """
        Update acknowledgment data in shared memory
        """
        self.shared_mem.cleanup_old_shared_memory()  
        self.shared_mem.set_data(data_name, True)

    def serialise_msg(self, message):
        # If it's a string or dict, treat accordingly
        if isinstance(message, str):
            return json.dumps(dict(typ="string", msg=message))

        elif isinstance(message, dict):
            return json.dumps(dict(typ="dict", msg=message))

        else:
            msg_type = type(message).__name__
            msg_to_sent = message_converter.convert_ros_message_to_dictionary(message)
            return json.dumps(dict(typ=msg_type, msg=msg_to_sent))

    def send_mav_msg(self, msgid, ack_msg):  # TODO, Deepak remove is not of use
        try:
            if self.is_connected:
                self.master.mav.vyom_message_send(
                    0,  # target_system
                    0,  # target_component
                    msgid.encode("utf-8"),  # 6-byte message_id
                    self.serialise_msg(ack_msg).encode(
                        "utf-8"
                    ),  # The 233-byte msg_text
                    1,  # Total number of chunks
                    0,  # Current chunk index
                    int(time.time()),  # Unix timestamp
                )
                self.logger.info(f"Sent MAV message with msgid: {msgid}")
            else:
                self.logger.error(
                    f"error sending mav_msg, mavlink connection is not connected"
                )
        except Exception as e:
            self.logger.error(
                f"Failed to send MAV message with msgid: {msgid}. Error: {e}"
            )

    def update_data_received(self, msgid, total_chunks, chunk_id, msg_text):
        self.logger.debug(f"Received msg_text {msg_text}")
        if self.data_received[msgid][chunk_id] == -1:
            self.data_received[msgid][chunk_id] = msg_text
            self.data_received[msgid][total_chunks] += 1
        else:
            self.logger.debug(f"Duplicate chunk {chunk_id} for msgid {msgid}")

        self.logger.debug(
            f"Received chunk_id {chunk_id}. Number of chunks recieved {self.data_received[msgid][total_chunks]} of {total_chunks} total chunks"
        )

        self.logger.debug("New chunks received and sent ack")

        # check if entire msg is receieved
        if self.data_received[msgid][total_chunks] == total_chunks:
            full_message = "".join(self.data_received[msgid][:total_chunks])
            self.logger.info(
                f"All chunks received for msgid: {msgid}. Receieved full message"
            )
            self.logger.debug(f"Full message: {full_message}")

            try:
                message_dict = json.loads(full_message)
                self.logger.debug(
                    f"messages: {message_dict} type: {type(message_dict)}"
                )

                self.logger.debug(
                    f"typ: {message_dict.get('typ')} id = {self.machine_id}"
                )

                self.handle_message("gcs_data", message_dict, self.machine_id, 0)
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse full_message as JSON: {e}")

            # TODO: if all msg received push to ros
            # self.handle_message()
            # def handle_message(self, typ, full_message, self.machine_id, source_id)

            message = json.loads(full_message)

            # remove the msgid from the dictionary
            self.handle_msg(message)
            self.data_received.pop(msgid)
            self.data_received[msgid] = 1

    def handle_msg(self, message):
        pass

    def msg_acknowledged(self, msgid, chunk_index):  # AMAR
        """Record ACK only if not already recorded"""
        data_name = f"mavlink_ack_data-{msgid}-{chunk_index}"
        
        # Check if already acknowledged
        # if self.shared_mem.get_data(data_name) is not None:
        #     self.logger.debug(f"ACK already recorded for {msgid}-{chunk_index}, skipping")
        #     return
        
        ack = self.set_ack_data_received(f"mavlink_ack_data-{msgid}-{chunk_index}")

    # def msg_acknowledged(self, msgid, chunk_index): # AMAR
    #     ack = self.ack_data_received.get(msgid)
    #     if not ack:
    #         self.ack_data_received.update({msgid: {str(chunk_index): 1}})

    #         self.logger.info(f"Updating ack_data_received {self.ack_data_received}")
    #     else:
    #         ack.update({str(chunk_index): 1})

    def acknowledge_msg(self, msgid, chunk_index):
        try:
            if self.is_connected:
                self.master.mav.vyom_message_send(
                    0,  # target_system
                    0,  # target_component
                    msgid.encode("ascii"),  # 6-byte message_id
                    "ACK".encode("ascii"),  # The 233-byte msg_text
                    1,  # Total number of chunks
                    chunk_index,  # Current chunk index
                    int(time.time()),  # Unix timestamp
                )
                self.logger.debug(
                    f"Acknowledged chunk {chunk_index} for msgid: {msgid}"
                )
            else:
                self.logger.error(
                    f"error sending ack, mavlink connection is not connected"
                )
        except Exception as e:
            self.logger.error(
                f"Failed to acknowledge chunk {chunk_index} for msgid: {msgid}. Error: {e}"
            )

    def receive_mav_message(self):
        self.logger.debug(
            f"Receiveing mav_messages background proccess started - is_running={self.is_running}"
        )
        while self.is_running:
            if self.is_connected:
                msg = self.master.recv_match(type="VYOM_MESSAGE", blocking=True)
                if msg:
                    self.logger.debug(f"Received mav_messages msg {msg}")
                    # extract the data
                    msgid = msg.message_id
                    chunk_id = msg.chunk_index
                    msg_text = msg.msg_text
                    total_chunks = msg.total_chunks

                    if msg_text == "ACK":
                        self.msg_acknowledged(msgid, chunk_id)
                        continue
                    else:
                        self.acknowledge_msg(msgid, chunk_id)

                        self.logger.debug(
                            f"Received chunk_id {chunk_id} total chunks {total_chunks}"
                        )

                        # Update the dictionary for new msg
                        # if the msgid is not existing in the dictionary
                        if msgid not in self.data_received:
                            self.data_received[msgid] = [-1] * (total_chunks + 1)

                            # last value is used as counter number of chunks received
                            self.data_received[msgid][total_chunks] = 0

                        # If msgid was already received and all chunks are joined
                        if self.data_received[msgid] == 1:
                            self.logger.debug("all chunks already added")
                        else:
                            self.logger.debug("Receiving chunks for the msgid")
                            self.update_data_received(
                                msgid, total_chunks, chunk_id, msg_text
                            )
            else:
                self.logger.warning(
                    f"Waiting for mavlink connection to get estalished, {self.connection_wait_time_sleep} sec sleeping..."
                )
                time.sleep(self.connection_wait_time_sleep)

    def start(self):
        try:
            self.logger.debug("MAVLink message listener thread starting...")
            self.is_running = True
            self._listener_thread = threading.Thread(
                target=self.receive_mav_message, daemon=True
            )

            self._listener_thread.start()
            self.logger.info("Started MAVLink message listener thread.")
        except Exception as e:
            self.logger.error(f"Failed to start listener thread: {str(e)}")

    def stop(self):
        self.logger.info("Stopping MavListener...")
        self.is_running = False
        self.cleanup()
        self.logger.info("Stoped MavListener successfully!")

    def cleanup(self):
        # TODO: Implement connection cleanup: TO check if this works
        self.logger.info("Cleaning up MAVLink connection...")
        try:
            if self.master:
                self.master.close()
            self.logger.info("MAVLink cleanup successful!")
        except Exception as e:
            self.logger.error(f"MAVLink cleanup failed error: {str(e)}")
        super().cleanup()

    def is_healthy(self):
        # TODO Implement if connection is working
        # return true
        # else false
        pass


def main():
    listener = MavListener()
    listener.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[INFO] Interrupted. Cleaning up...")
    listener.stop()


if __name__ == "__main__":
    main()
