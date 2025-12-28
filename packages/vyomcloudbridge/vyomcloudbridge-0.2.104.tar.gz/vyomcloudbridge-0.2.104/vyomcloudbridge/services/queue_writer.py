# vyomcloudbridge/queue_writer.py
from concurrent.futures import ThreadPoolExecutor
import logging
import time
import random
from datetime import datetime, timezone
import configparser
import traceback
import os
import signal
import sys
import hashlib
import base64
from typing import Dict, Any, Optional
from queue import Queue, Empty
import json
from typing import Dict, Any, List, Tuple, Union
from pathlib import Path
import threading
from vyomcloudbridge.services.chunk_merger import ChunkMerger

# from vyomcloudbridge.services.mission_stats import MissionStats # TODO: remove later
from vyomcloudbridge.services.rabbit_queue.queue_main import RabbitMQ
from vyomcloudbridge.utils.logger_setup import setup_logger
from vyomcloudbridge.utils.configs import Configs
from vyomcloudbridge.constants.constants import MAX_FILE_SIZE, LIVE_FILE_SIZE
from vyomcloudbridge.utils.common import generate_unique_id, DATA_TYPE_MAPPING
from vyomcloudbridge.utils.common import get_mission_upload_dir
from vyomcloudbridge.constants.constants import (
    default_project_id,
    default_mission_id,
    MISSION_STATS_DT_SRC,
)


class ThreadSafeRabbitMQPool:  # use this QueueWriter, instead of QueueWriterJson from queue_write.py
    """Thread-safe RabbitMQ connection pool with actual connection reuse"""

    def __init__(self, max_pool_size: int = 8, log_level=None):
        self.log_level = log_level
        self._thread_local = threading.local()
        self._pool_lock = threading.Lock()
        self._connection_pool = Queue(maxsize=max_pool_size)
        self._active_connections: Dict[int, RabbitMQ] = {}  # thread_id -> connection
        self._max_pool_size = max_pool_size
        self._created_connections = 0

        self.logger = setup_logger(
            name=self.__class__.__module__ + "." + self.__class__.__name__,
            show_terminal=False,
            log_level=log_level,
        )

    def get_connection(self) -> RabbitMQ:
        """Get a RabbitMQ connection for the current thread"""
        thread_id = threading.current_thread().ident

        # Check if current thread already has an active connection
        with self._pool_lock:
            if thread_id in self._active_connections:
                connection = self._active_connections[thread_id]
                if connection.is_healthy():
                    return connection
                else:
                    # Connection is unhealthy, remove it
                    del self._active_connections[thread_id]
                    try:
                        connection.close()
                    except:
                        pass

        # Try to get a connection from the pool first
        connection = None
        try:
            connection = self._connection_pool.get_nowait()
            if connection.is_healthy():
                self.logger.debug(
                    f"Reused pooled connection for thread {threading.current_thread().name}"
                )
            else:
                # Connection from pool is unhealthy, discard it
                try:
                    connection.close()
                except:
                    pass
                connection = None
        except Empty:
            # Pool is empty, will create new connection
            pass

        # Create new connection if we don't have a healthy one
        if connection is None:
            with self._pool_lock:
                if self._created_connections < self._max_pool_size:
                    connection = RabbitMQ(log_level=self.log_level)
                    self._created_connections += 1
                    self.logger.debug(
                        f"Created new RabbitMQ connection for thread {threading.current_thread().name} "
                        f"({self._created_connections}/{self._max_pool_size})"
                    )
                else:
                    # Max connections reached, wait for one to become available
                    self.logger.warning(
                        f"Max connections ({self._max_pool_size}) reached, waiting for available connection"
                    )

            # If we couldn't create due to limit, wait for one from pool
            if connection is None:
                try:
                    connection = self._connection_pool.get(
                        timeout=10
                    )  # Wait up to 10 seconds
                    if not connection.is_healthy():
                        try:
                            connection.close()
                        except:
                            pass
                        raise Exception("Retrieved unhealthy connection from pool")
                except:
                    # Fallback: create connection anyway if we're stuck
                    self.logger.warning(
                        "Creating connection despite limit due to timeout"
                    )
                    connection = RabbitMQ(log_level=self.log_level)

        # Register the connection as active for this thread
        with self._pool_lock:
            self._active_connections[thread_id] = connection

        return connection

    def return_connection(self, connection: RabbitMQ):
        """Return a connection to the pool for reuse"""
        thread_id = threading.current_thread().ident

        # Remove from active connections
        with self._pool_lock:
            self._active_connections.pop(thread_id, None)

        # Only return healthy connections to the pool
        if connection and connection.is_healthy():
            try:
                self._connection_pool.put_nowait(connection)
                self.logger.debug("Returned healthy connection to pool")
                return
            except:
                # Pool is full, close the connection
                pass

        # Close unhealthy or excess connections
        try:
            connection.close()
            self.logger.debug("Closed connection (unhealthy or pool full)")
        except:
            pass

        # Decrement counter only if we're closing the connection
        with self._pool_lock:
            if self._created_connections > 0:
                self._created_connections -= 1

    def cleanup_thread_connection(self):
        """Clean up the current thread's connection by returning it to pool"""
        thread_id = threading.current_thread().ident

        with self._pool_lock:
            connection = self._active_connections.pop(thread_id, None)

        if connection:
            self.return_connection(connection)
            self.logger.debug(
                f"Returned connection to pool for thread {threading.current_thread().name}"
            )

    def cleanup(self):
        """Clean up all connections in the pool"""
        self.logger.info("ThreadSafeRabbitMQPool cleanup initiated")

        # Clean up all active connections
        with self._pool_lock:
            active_connections = list(self._active_connections.values())
            self._active_connections.clear()

        for connection in active_connections:
            try:
                connection.close()
            except:
                pass

        # Clean up pooled connections
        while True:
            try:
                connection = self._connection_pool.get_nowait()
                try:
                    connection.close()
                except:
                    pass
            except Empty:
                break

        with self._pool_lock:
            self._created_connections = 0

        self.logger.info("ThreadSafeRabbitMQPool cleanup completed")

    def get_pool_stats(self) -> Dict[str, int]:
        """Get statistics about the connection pool"""
        with self._pool_lock:
            return {
                "active_connections": len(self._active_connections),
                "pooled_connections": self._connection_pool.qsize(),
                "total_created": self._created_connections,
                "max_pool_size": self._max_pool_size,
            }


class QueueWriter:  # use this QueueWriter, instead of QueueWriterJson from queue_write.py
    """Main class for handling message queue writing operations."""

    def __init__(self, log_level=None):
        self.rabbit_mq = RabbitMQ(log_level=log_level)  # Main thread connection
        self.rabbit_mq_pool = ThreadSafeRabbitMQPool(
            log_level=log_level
        )  # Thread pool for background threads
        self.machine_config = Configs.get_machine_config()
        self.machine_id = self.machine_config.get("machine_id", "-") or "-"
        self.organization_id = self.machine_config.get("organization_id", "-") or "-"
        self.logger = setup_logger(
            name=self.__class__.__module__ + "." + self.__class__.__name__,
            show_terminal=False,
            log_level=log_level,
        )
        self.chunk_merger = ChunkMerger(log_level=log_level)
        # self.mission_stats = MissionStats() # TODO: remove later
        self.watching_live = True  # if a watcher is available to watch live data
        self.live_priority = 2
        self.live_destinations = ["s3", "gcs_mqtt"]  # TODO real time later
        self.live_expiry_time = "2000"  # millisecond
        self.live_executor = ThreadPoolExecutor(
            max_workers=4, thread_name_prefix="live"
        )
        self.data_executor = ThreadPoolExecutor(
            max_workers=4, thread_name_prefix="data"
        )
        self._setup_signal_handlers()

    def _get_file_info(self, filename: str) -> Tuple[str, str, str]:
        """
        Extract file information from filepath.
        Returns: (filename without extension, extension, detected data type)
        """
        extension = filename.lower().lstrip(".")
        data_type = DATA_TYPE_MAPPING.get(extension, "file")
        return filename, extension, data_type

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""

        def signal_handler(signum, frame):
            self.logger.info("Shutting down...")
            self.cleanup()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def _get_data_chunks_md5(self, message_data, is_json_data, should_chunk):
        """Helper to split data into chunks and compute MD5 hash"""
        if not is_json_data:
            data = (
                message_data
                if isinstance(message_data, bytes)
                else message_data.encode("utf-8")
            )
        else:
            data = json.dumps(message_data).encode("utf-8")
        md5_hash = hashlib.md5(data).hexdigest()

        # Split data into chunks
        chunks = []
        if should_chunk:
            for i in range(0, len(data), MAX_FILE_SIZE):
                chunks.append(data[i : i + MAX_FILE_SIZE])

        return chunks, md5_hash

    def _get_live_first_chunks(self, message_data, is_json_data):
        """Helper to split data into chunks and compute MD5 hash"""
        if not is_json_data:
            data = (
                message_data
                if isinstance(message_data, bytes)
                else message_data.encode("utf-8")
            )
        else:
            data = json.dumps(message_data).encode("utf-8")

        return data[0:LIVE_FILE_SIZE]

    def _enqueue_live_data_sync(
        self,
        message_data,
        data_type,
        data_size,
        live_dir,
        filename,
        base_filename,
        buffer_key,
        data_source,
    ):
        """Synchronous version for main thread"""
        return self._enqueue_live_data_impl(
            self.rabbit_mq,  # Use main thread connection
            message_data,
            data_type,
            data_size,
            live_dir,
            filename,
            base_filename,
            buffer_key,
            data_source,
        )

    def _enqueue_live_data_async(
        self,
        message_data,
        data_type,
        data_size,
        live_dir,
        filename,
        base_filename,
        buffer_key,
        data_source,
    ):
        """Asynchronous version for background threads"""
        try:
            while True:
                try:
                    thread_rabbit_mq = self.rabbit_mq_pool.get_connection()
                    break
                except Exception as e:
                    self.logger.warning(f"Error in async live data enqueue: {str(e)}")
                    time.sleep(1)

            return self._enqueue_live_data_impl(
                thread_rabbit_mq,  # Use thread-specific connection
                message_data,
                data_type,
                data_size,
                live_dir,
                filename,
                base_filename,
                buffer_key,
                data_source,
            )
        except Exception as e:
            self.logger.error(f"Error in async live data enqueue: {str(e)}")
        finally:
            # Clean up thread connection when done
            self.rabbit_mq_pool.cleanup_thread_connection()

    def _enqueue_live_data_impl(
        self,
        rabbit_mq_conn,  # RabbitMQ connection to use
        message_data,
        data_type,
        data_size,
        live_dir,
        filename,
        base_filename,
        buffer_key,
        data_source,
    ):
        """Implementation that works with any RabbitMQ connection"""
        try:
            if data_size is None:
                data_size = (
                    len(json.dumps(message_data).encode("utf-8"))
                    if data_type == "json"
                    else (
                        len(message_data)
                        if isinstance(message_data, bytes)
                        else len(message_data.encode("utf-8"))
                    )
                )
            # LIVE DATA
            data_live = (
                self._get_live_first_chunks(
                    message_data, is_json_data=data_type == "json"
                )
                if data_size > LIVE_FILE_SIZE
                else message_data
            )
            data_type_live = "json" if data_type == "image" else data_type
            message_type_live = "json" if data_type_live == "json" else "binary"
            filename_live = (
                f"{base_filename}.json" if message_type_live == "json" else filename
            )
            if data_type == "image":  # for any binary, converting it to json TODO
                data_live = {
                    "image_base64": base64.b64encode(data_live).decode("utf-8"),
                    "type": "jpeg",
                }
            live_topic = f"{live_dir}/{filename_live}"
            message_body = (
                data_live if message_type_live == "binary" else json.dumps(data_live)
            )
            headers = {
                "message_type": message_type_live,
                "topic": live_topic,
                "destination_ids": self.live_destinations,  # LIVE
                "data_source": data_source,
                # meta info
                "buffer_key": buffer_key,
                "buffer_size": 0,
                "data_type": data_type_live,
            }
            rabbit_mq_conn.enqueue_message(
                message=message_body,
                headers=headers,
                priority=self.live_priority,
                expiration=self.live_expiry_time,
            )
            self.logger.info(
                f"Data enqueued to {live_topic}, with expiry time {self.live_expiry_time}"
            )
        except Exception as e:
            self.logger.error(f"Error in publishing live -{str(e)}")
            pass

    def _enqueue_all_data_sync(
        self,
        mission_id,
        message_data,
        data_type,
        data_size,
        chunk_dir,
        filename,
        mission_upload_dir,
        properties,
        merge_chunks,
        base_filename,
        buffer_key,
        data_source,
        destination_ids,
        priority,
        expiry_time_ms,
        background,
    ):
        """Synchronous version for main thread"""
        return self._enqueue_all_data_impl(
            self.rabbit_mq,  # Use main thread connection
            mission_id,
            message_data,
            data_type,
            data_size,
            chunk_dir,
            filename,
            mission_upload_dir,
            properties,
            merge_chunks,
            base_filename,
            buffer_key,
            data_source,
            destination_ids,
            priority,
            expiry_time_ms,
            background,
        )

    def _enqueue_all_data_async(
        self,
        mission_id,
        message_data,
        data_type,
        data_size,
        chunk_dir,
        filename,
        mission_upload_dir,
        properties,
        merge_chunks,
        base_filename,
        buffer_key,
        data_source,
        destination_ids,
        priority,
        expiry_time_ms,
        background,
    ):
        """Asynchronous version for background threads"""
        try:
            while True:
                try:
                    thread_rabbit_mq = self.rabbit_mq_pool.get_connection()
                    break
                except Exception as e:
                    self.logger.warning(f"Error in async all data enqueue: {str(e)}")
                    time.sleep(1)
            return self._enqueue_all_data_impl(
                thread_rabbit_mq,  # Use thread-specific connection
                mission_id,
                message_data,
                data_type,
                data_size,
                chunk_dir,
                filename,
                mission_upload_dir,
                properties,
                merge_chunks,
                base_filename,
                buffer_key,
                data_source,
                destination_ids,
                priority,
                expiry_time_ms,
                background,
            )
        except Exception as e:
            self.logger.error(f"Error in async all data enqueue: {str(e)}")
            return False, f"Error in async all data enqueue: {str(e)}"
        finally:
            # Clean up thread connection when done
            self.rabbit_mq_pool.cleanup_thread_connection()

    def _enqueue_all_data_impl(
        self,
        rabbit_mq_conn,  # RabbitMQ connection to use
        mission_id,
        message_data,
        data_type,
        data_size,
        chunk_dir,
        filename,
        mission_upload_dir,
        properties,
        merge_chunks,
        base_filename,
        buffer_key,
        data_source,
        destination_ids,
        priority,
        expiry_time_ms,
        background,
    ):
        """Implementation that works with any RabbitMQ connection"""
        try:
            destination_ids_str = ",".join(str(id) for id in destination_ids)
            if data_size is None:
                data_size = (
                    len(json.dumps(message_data).encode("utf-8"))
                    if data_type == "json"
                    else (
                        len(message_data)
                        if isinstance(message_data, bytes)
                        else len(message_data.encode("utf-8"))
                    )
                )
            should_chunk = data_size > MAX_FILE_SIZE
            file_property_size = 0
            # chunks_size = 0
            if should_chunk:
                # 1.1 getting chunks and md5
                data_chunks, data_md5 = self._get_data_chunks_md5(
                    message_data,
                    is_json_data=data_type == "json",
                    should_chunk=should_chunk,
                )
                # 1.2 properties for chunks, doing it inside chunking logic to optimize
                file_info_data = {
                    "filename": filename,
                    "data_type": data_type,
                    "file_md5": data_md5,
                    "total_size": data_size,
                    "file_dir": mission_upload_dir,
                    "properties": properties,
                    "is_chunked": should_chunk,
                    **(
                        {
                            "total_chunks": len(data_chunks),
                            "chunk_dir": chunk_dir,
                            "merge_chunks": merge_chunks,
                            "chunk_name": base_filename,
                        }
                        if should_chunk
                        else {}
                    ),
                }
                # 1.3 send file_properties for chunks
                chunk_info_topic = (
                    f"{mission_upload_dir}/file_properties/{base_filename}.json"
                )
                file_property_size = len(json.dumps(file_info_data).encode("utf-8"))
                message_body = json.dumps(file_info_data)
                headers = {
                    "topic": chunk_info_topic,
                    "message_type": "json",
                    "destination_ids": destination_ids,
                    "data_source": data_source,
                    # meta info
                    "buffer_key": buffer_key,
                    "buffer_size": file_property_size,
                    "data_type": data_type,
                }
                rabbit_mq_conn.enqueue_message(
                    message=message_body,
                    headers=headers,
                    priority=priority,
                    expiration=expiry_time_ms,
                )
                expiry_log = f", with expiry time {expiry_time_ms}ms" if expiry_time_ms is not None else ""
                self.logger.info(f"Data enqueued to {chunk_info_topic}, dst's=[{destination_ids_str}], {expiry_log}")
                # 1.4 send all chunks
                total_chunks = len(data_chunks)
                padding_length = len(str(total_chunks))
                for i, chunk in enumerate(data_chunks):
                    try:
                        formatted_index = str(i + 1).zfill(padding_length)
                        message_body = chunk
                        # chunks_size += len(chunk)
                        headers = {
                            "message_type": "binary",  # Always binary for chunks
                            "topic": f"{chunk_dir}/{base_filename}_{formatted_index}.bin",
                            "destination_ids": destination_ids,
                            "data_source": data_source,
                            # meta info
                            "buffer_key": buffer_key,
                            "buffer_size": len(chunk),
                            "data_type": data_type,
                        }
                        rabbit_mq_conn.enqueue_message(
                            message=message_body,
                            headers=headers,
                            priority=priority,
                            expiration=expiry_time_ms,
                        )
                    except Exception as e:
                        self.logger.error(f"Error in publishing chunk {i}: {str(e)}")
                self.logger.info(
                    f"Data enqueued to all {chunk_dir}/{base_filename}_*.bin"
                )
                # 1.5 send event for merging file
                if merge_chunks:
                    s3_prop_key = (
                        f"{mission_upload_dir}/file_properties/{base_filename}.json"
                    )
                    self.chunk_merger.on_chunk_file_arrive(s3_prop_key)
            else:
                try:
                    # 2.1 send file to s3, without chunking
                    file_name_topic = mission_upload_dir + "/" + filename
                    message_body = (
                        json.dumps(message_data)
                        if data_type == "json"
                        else message_data
                    )
                    headers = {
                        "message_type": "json" if data_type == "json" else "binary",
                        "topic": file_name_topic,
                        "destination_ids": destination_ids,
                        "data_source": data_source,
                        # meta data
                        "buffer_key": buffer_key,
                        "buffer_size": data_size,
                        "data_type": data_type,
                    }
                    rabbit_mq_conn.enqueue_message(
                        message=message_body,
                        headers=headers,
                        priority=priority,
                        expiration=expiry_time_ms,
                    )
                    expiry_log = f", with expiry time {expiry_time_ms}ms" if expiry_time_ms is not None else ""
                    self.logger.info(f"Data enqueued to {file_name_topic}, dst's=[{destination_ids_str}]{expiry_log}")
                except Exception as e:
                    self.logger.error(f"Error in publishing : {str(e)}")
            # metadata for machine buffer (in case of all success)
            if expiry_time_ms is None:
                self.logger.debug(
                    f"Enqueuing file info metadata to RabbitMQ, mission_id: {mission_id}, data_source: {data_source}, size: {data_size}"
                )
                rabbit_mq_conn.enqueue_message_size(
                    size=data_size + file_property_size,
                )
                # TODO: remove later
                # self.mission_stats.on_mission_data_arrive(
                #     mission_id=mission_id,
                #     size=data_size+file_property_size,
                #     file_count=1,
                #     data_type=data_type,
                #     data_source=data_source,
                #     s3_dir=mission_upload_dir,
                # )
                self.logger.debug(
                    f"Enqueued file info metadata to RabbitMQ, mission_id: {mission_id}, data_source: {data_source}, size: {data_size}"
                )
            return True, None
        except Exception as e:
            if background:
                self.logger.fatal(
                    f"Error in enqueueing all data, data lost for {mission_upload_dir}/file_properties/{base_filename}.json: {str(e)}"
                )
                return False, f"Error in enqueueing all data: {str(e)}"
            else:
                self.logger.error(f"Error in enqueueing all data: {str(e)}")
                return False, f"Error in enqueueing all data: {str(e)}"

    def write_message(
        self,
        message_data: Any,
        data_type: str,  # json, image, binary
        data_source: str,  # DRONE_STATE, camera1, camera2, machine_state, BATTERY_TOPIC
        destination_ids: List[Union[str, int]],  # array of destination_ids
        source_id: Optional[Union[str, int]] = None,
        filename: Optional[str] = None,
        mission_id: Optional[Union[str, int]] = default_mission_id,
        project_id: Optional[Union[str, int]] = default_project_id,
        priority: Optional[int] = 1,
        merge_chunks: Optional[bool] = False,
        send_persistent: Optional[bool] = True,
        send_live: Optional[bool] = False,
        expiry_time_ms: Optional[Union[int, str]] = None,
        background: bool = False,
        # Extra arguments, will be removed later
        expiry_time: Optional[
            Union[int, str]
        ] = None,  # THIS IS DEPRECATED, USE expiry_time_ms INSTEAD
    ) -> tuple[bool, Union[str, None]]:
        """
        Writes a message to the specified destinations.

        Args:
            message_data: The data to be sent
            data_type: Type of data (json, image, binary)
            data_source: Source of the data (telemetry, drone_state, mission_summary, camera1, camera2, machine_state)
            destination_ids: List of destination IDs to send the message to, for publishing it to server use ["s3"]
            filename: Optional filename for JSON data which be taken from timestamp, for rest give proper name i.e. 17460876104123343.jpeg
            mission_id: Optional mission ID for data generated by current device
            project_id: Optional project ID for data generated by current device
            priority: Optional, message priority to be published in priority order (1 for all, 3 for critical) 2 is reserved
            merge_chunks: Optional, Whether to merge message chunks after publishing it to server, default is False
            send_persistent: Optional, Whether to send persistent data (buffered for later delivery), default is True
            send_live: Optional, Whether to send live data or not, default is False
            expiry_time_ms: Optional, message expiry time in milliseconds, default is None, after that message will be deleted from queue
            background: Whether to execute in background thread (True) or synchronously (False)
        Returns:
            tuple[bool, str]: A tuple containing:
                - success: Boolean indicating whether the operation was successful
                - error: Error message if unsuccessful, empty string otherwise
        """
        try:
            expiry_time_ms = expiry_time_ms or expiry_time
            if expiry_time_ms is not None:
                try:
                    expiry_time_ms = str(expiry_time_ms)
                except Exception as e:
                    self.logger.error(
                        f"Error in converting expiry_time_ms to string: {str(e)}"
                    )
                    return (
                        False,
                        f"Error in converting expiry_time_ms to string: {str(e)}",
                    )

            if source_id is None:
                source_id = self.machine_id

            if destination_ids and (
                isinstance(destination_ids, str) or isinstance(destination_ids, int)
            ):
                destination_ids = [destination_ids]

            if data_source is None or data_source == "":
                data_source = "UNKNOWN_SOURCE"
                self.logger.warning(
                    "data_source is None or empty, using 'UNKNOWN_SOURCE' as default"
                )
            if not isinstance(data_source, str):
                return False, "data_source must be a of type string"

            if "/" in data_source:
                self.logger.error(
                    f"data_source '{data_source}' contains '/', which is not allowed"
                )
                return False, "data_source cannot contain '/'"

            if priority is None:
                error_msg = (
                    "'priority' cannot be None; must be an integer (1-4) if provided."
                )
                self.logger.error(error_msg)
                return False, f"[QueueWriter.write_message] {error_msg}"

            destination_ids_str = ",".join(str(id) for id in destination_ids)
            mrg_chunks_str = "T" if merge_chunks else "F"
            snd_persistent_str = "T" if send_persistent else "F"
            snd_live_str = "T" if send_live else "F"
            self.logger.info(
                f"Data enqueueing... src={source_id}, dst's=[{destination_ids_str}], dta_src={data_source}, dtatyp={data_type}, fil_nm={filename}, prio={priority}, msid={mission_id}, pid={project_id}, mrg_c={mrg_chunks_str}, persistent={snd_persistent_str}, live={snd_live_str}, exp={expiry_time or expiry_time_ms}, sz={len(message_data) if hasattr(message_data, '__len__') else 'N/A'}, msgdtatyp={type(message_data).__name__}, bg={background}"
            )
            # isinstance(message_data, bytes) is True when {type(message_data).__name__=="bytes"

            if not filename or filename is None:
                epoch_ms = int(time.time() * 1000)
                if data_type == "json":
                    filename = f"{epoch_ms}.json"
                    self.logger.debug(
                        f"No filename provided, using generated name epoch_ms: {filename}"
                    )
                else:
                    self.logger.error(
                        f"No filename provided, invalid filename for non string message_data, message skipped..."
                    )
                    return False, "No filename provided"

            # Extract filename and extension
            base_filename, file_extension = os.path.splitext(filename)
            file_extension = file_extension[1:]
            if not file_extension:
                file_extension = "json" if data_type == "json" else "bin"
                filename = f"{base_filename}.{file_extension}"

            # Get current time for metadata
            now = datetime.now(timezone.utc)
            properties = {
                "organization_id": self.organization_id,
                "data_source": data_source,
                "date": now.strftime("%Y-%m-%d"),
                "hour": str((now.hour + 1) % 24 or 24),
                "machine_id": source_id,
                "mission_id": mission_id,
                "project_id": project_id,
                "file_name": filename,
            }

            # Determine file paths
            mission_upload_dir: str = get_mission_upload_dir(
                organization_id=self.organization_id,
                machine_id=source_id,
                mission_id=mission_id,
                data_source=data_source,
                date=now.strftime("%Y-%m-%d"),
                project_id=project_id,
            )

            chunk_dir = f"{mission_upload_dir}/chunks"
            live_dir = f"{mission_upload_dir}/live"
            buffer_key = mission_id if isinstance(mission_id, str) else str(mission_id)

            if background:
                data_size = None  # will be calculated in _enqueue_all_data_impl
                if self.watching_live and send_live:
                    self.live_executor.submit(
                        self._enqueue_live_data_async,
                        message_data,
                        data_type,
                        data_size,
                        live_dir,
                        filename,
                        base_filename,
                        buffer_key,
                        data_source,
                    )
                if send_persistent:
                    self.data_executor.submit(
                        self._enqueue_all_data_async,
                        mission_id,
                        message_data,
                        data_type,
                        data_size,
                        chunk_dir,
                        filename,
                        mission_upload_dir,
                        properties,
                        merge_chunks,
                        base_filename,
                        buffer_key,
                        data_source,
                        destination_ids,
                        priority,
                        expiry_time_ms,
                        background,
                    )
                return True, None
            else:
                # Synchronous execution - use main thread connection
                data_size = (
                    len(json.dumps(message_data).encode("utf-8"))
                    if data_type == "json"
                    else (
                        len(message_data)
                        if isinstance(message_data, bytes)
                        else len(message_data.encode("utf-8"))
                    )
                )
                if self.watching_live and send_live:
                    self._enqueue_live_data_sync(
                        message_data,
                        data_type,
                        data_size,
                        live_dir,
                        filename,
                        base_filename,
                        buffer_key,
                        data_source,
                    )
                if send_persistent:
                    success, error = self._enqueue_all_data_sync(
                        mission_id,
                        message_data,
                        data_type,
                        data_size,
                        chunk_dir,
                        filename,
                        mission_upload_dir,
                        properties,
                        merge_chunks,
                        base_filename,
                        buffer_key,
                        data_source,
                        destination_ids,
                        priority,
                        expiry_time_ms,
                        background,
                    )
                    return success, error
                else:
                    # If only live data was sent (or no data sent), return success
                    return True, None

            # # LIVE DATA SENDING
            # if self.watching_live and send_live:
            #     data_size = (
            #         len(json.dumps(message_data).encode("utf-8"))
            #         if data_type == "json"
            #         else (
            #             len(message_data)
            #             if isinstance(message_data, bytes)
            #             else len(message_data.encode("utf-8"))
            #         )
            #     )
            #     self._enqueue_live_data(
            #         message_data,
            #         data_type,
            #         data_size,
            #         live_dir,
            #         filename,
            #         base_filename,
            #         buffer_key,
            #         data_source,
            #     )

            # # ALL DATA SENDING
            # data_size = (
            #     len(json.dumps(message_data).encode("utf-8"))
            #     if data_type == "json"
            #     else (
            #         len(message_data)
            #         if isinstance(message_data, bytes)
            #         else len(message_data.encode("utf-8"))
            #     )
            # )
            # success, error = self._enqueue_all_data(
            #     mission_id,
            #     message_data,
            #     data_type,
            #     data_size,
            #     chunk_dir,
            #     filename,
            #     mission_upload_dir,
            #     properties,
            #     merge_chunks,
            #     base_filename,
            #     buffer_key,
            #     data_source,
            #     destination_ids,
            #     priority,
            #     expiry_time_ms,
            # )
            # return success, error
        except Exception as e:
            self.logger.error(f"Error in write_message: {traceback.format_exc()}")
            return False, f"Error in write_message: {str(e)}"

    def cleanup(self):
        """Clean up resources."""
        if self.chunk_merger:
            try:
                self.chunk_merger.stop()
                self.logger.info("chunk_merger cleaned up successfully")
            except Exception as e:
                self.logger.error(
                    f"Error cleaning chunk_merger: {str(e)}", exc_info=True
                )

        # TODO: remove later
        # if self.mission_stats:
        #     try:
        #         self.mission_stats.stop()
        #         self.logger.info("mission_stats cleaned up successfully")
        #     except Exception as e:
        #         self.logger.error(
        #             f"Error cleaning mission_stats: {str(e)}", exc_info=True
        #         )

        try:
            self.rabbit_mq.close()
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

            # Clean up thread pool
        if hasattr(self, "live_executor"):
            try:
                self.live_executor.shutdown(wait=True, timeout=5)
                self.logger.info("Live executor cleaned up successfully")
            except Exception as e:
                self.logger.error(f"Error cleaning live executor: {str(e)}")

        if hasattr(self, "data_executor"):
            try:
                self.data_executor.shutdown(wait=True, timeout=5)
                self.logger.info("Data executor cleaned up successfully")
            except Exception as e:
                self.logger.error(f"Error cleaning data executor: {str(e)}")

        # Clean up RabbitMQ pool
        if hasattr(self, "rabbit_mq_pool"):
            try:
                self.rabbit_mq_pool.cleanup()
                self.logger.info("RabbitMQ pool cleaned up successfully")
            except Exception as e:
                self.logger.error(f"Error cleaning RabbitMQ pool: {str(e)}")

    def is_healthy(self):
        """
        Override health check to add additional service-specific checks.
        """
        # TODO: remove later
        # return self.rabbit_mq.is_healthy() and self.mission_stats.is_healthy()
        return self.rabbit_mq.is_healthy()

    def __del__(self):
        """Destructor called by garbage collector to ensure resources are cleaned up, when object is about to be destroyed"""
        try:
            if self.is_healthy():
                self.logger.error(
                    "Destructor called by garbage collector to cleanup QueueWriter"
                )
                self.cleanup()
        except Exception as e:
            pass


def main():
    # # Example 1, send data, without live
    from vyomcloudbridge.services.queue_writer import QueueWriter
    import time

    default_mission_id = "_all_"

    try:
        writer = QueueWriter(log_level=logging.INFO)
        message_data = {"lat": 75.66666, "long": 73.0589455, "alt": 930}
        data_source = "MACHINE_POSE"  # event, warning, camera1, camera2,
        data_type = "json"  # image, binary, json
        mission_id = "111333"

        epoch_ms = int(time.time() * 1000)
        uuid_padding = generate_unique_id(4)
        filename = f"{epoch_ms}_{uuid_padding}.json"

        writer.write_message(
            message_data=message_data,  # json or binary data
            filename=filename,  # 293749834.json, 93484934.jpg
            data_source=data_source,  # machine_pose camera1, machine_state
            data_type=data_type,  # json, binary, ros
            mission_id=mission_id,  # mission_id
            priority=1,  # 1, 2
            destination_ids=["s3"],  # ["s3"]
        )
    except Exception as e:
        print(f"Error writing test messages: {e}")
    finally:
        writer.cleanup()

    # # Example 2, send data, live
    from vyomcloudbridge.services.queue_writer import QueueWriter

    try:
        writer = QueueWriter()
        message_data = {"lat": 75.66666, "long": 73.0589455, "alt": 930}
        data_source = "MACHINE_POSE"  # event, warning, camera1, camera2,
        data_type = "json"  # image, binary, json
        mission_id = "111333"

        epoch_ms = int(time.time() * 1000)
        uuid_padding = generate_unique_id(4)
        filename = f"{epoch_ms}_{uuid_padding}.json"

        writer.write_message(
            message_data=message_data,  # json or binary data
            filename=filename,  # 293749834.json, 93484934.jpg
            data_source=data_source,  # machine_pose camera1, machine_state
            data_type=data_type,  # json, binary, ros
            mission_id=mission_id,  # mission_id
            priority=1,  # 1, 2
            destination_ids=["s3"],  # ["s3"]
            send_live=True,
        )
    except Exception as e:
        print(f"Error writing test messages: {e}")
    finally:
        writer.cleanup()

    # # Example 3
    from vyomcloudbridge.services.queue_writer import QueueWriter

    writer = QueueWriter()
    try:
        loop_len = 10
        padding_length = len(str(loop_len))

        for i in range(loop_len):
            epoch_ms = int(time.time() * 1000)
            message_data = {
                "data": f"Test message No {i}",
                "data_id": epoch_ms,
                "lat": 75.66666,
                "long": 73.0589455,
                "alt": 930,
            }

            data_source = "MACHINE_POSE"  # event, warning, camera1, camera2,
            data_type = "json"  # image, binary, json
            mission_id = "111333"
            formatted_index = str(i + 1).zfill(padding_length)
            filename = f"{epoch_ms}_{formatted_index}.json"

            writer.write_message(
                message_data=message_data,
                filename=filename,
                data_source=data_source,
                data_type=data_type,
                mission_id=mission_id,
                priority=1,
                destination_ids=["s3", "gcs"],
            )
    except Exception as e:
        print(f"Error writing test messages: {e}")
    finally:
        writer.cleanup()

    # # Example 4
    from vyomcloudbridge.services.queue_writer import QueueWriter

    writer = QueueWriter()
    try:
        import requests
        from urllib.parse import urlparse

        loop_len = 10
        padding_length = len(str(loop_len))

        # URLs for the images
        image_urls = [
            "https://sample-videos.com/img/Sample-jpg-image-50kb.jpg",
            # "https://sample-videos.com/img/Sample-png-image-100kb.png",
            # "https://sample-videos.com/img/Sample-jpg-image-100kb.jpg",
            "https://sample-videos.com/img/Sample-jpg-image-200kb.jpg",
            "https://sample-videos.com/img/Sample-jpg-image-500kb.jpg",
            "https://www.sample-videos.com/video321/mp4/720/big_buck_bunny_720p_5mb.mp4",
            "https://www.sample-videos.com/img/Sample-jpg-image-5mb.jpg",
            "https://mirror.del.albony.in/videolan-ftp/vlc/3.0.21/macosx/vlc-3.0.21-intel64.dmg",
            "https://www.sample-videos.com/video321/flv/360/big_buck_bunny_360p_5mb.flv",
        ]

        for i in range(loop_len):
            epoch_ms = int(time.time() * 1000)
            data_source = "TEST_BINARY_FILE"  # event, warning, camera1, camera2
            data_type = "image"  # image, json, binary
            mission_id = default_mission_id  # "34556"
            formatted_index = str(i + 1).zfill(padding_length)

            # Alternate between the two URLs
            current_url = image_urls[i % len(image_urls)]

            # Get the file extension from the URL
            parsed_url = urlparse(current_url)
            file_extension = parsed_url.path.split(".")[-1]

            # Download the image binary data
            response = requests.get(current_url)
            if response.status_code == 200:
                file_data = response.content  # This is binary data (bytes)

                # Create filename with proper extension
                filename = f"{epoch_ms}_{formatted_index}.{file_extension}"

                writer.write_message(
                    message_data=file_data,
                    filename=filename,
                    data_source=data_source,
                    data_type=data_type,
                    mission_id=mission_id,
                    priority=1,
                    destination_ids=["s3"],
                    merge_chunks=True if i % 2 == 0 else False,
                )
            else:
                print(
                    f"Failed to download image from {current_url}. Status code: {response.status_code}"
                )

    except Exception as e:
        print(f"Error writing test messages: {e}")
    finally:
        writer.cleanup()

    # # Example 4.1 (5mb files)
    from vyomcloudbridge.services.queue_writer import QueueWriter
    import time

    writer = QueueWriter()
    default_mission_id = "_all_"
    try:
        import requests
        from urllib.parse import urlparse

        loop_len = 10
        padding_length = len(str(loop_len))
        # URLs for the images
        image_urls = [
            "https://www.sample-videos.com/video321/mp4/720/big_buck_bunny_720p_5mb.mp4",
            "https://www.sample-videos.com/img/Sample-jpg-image-5mb.jpg",
            "https://mirror.del.albony.in/videolan-ftp/vlc/3.0.21/macosx/vlc-3.0.21-intel64.dmg",
            "https://www.sample-videos.com/video321/flv/360/big_buck_bunny_360p_5mb.flv",
        ]
        for i in range(loop_len):
            epoch_ms = int(time.time() * 1000)
            data_source = "TEST_BINARY_FILE"  # event, warning, camera1, camera2
            data_type = "binary"  # image, json, binary
            mission_id = default_mission_id  # "34556"
            formatted_index = str(i + 1).zfill(padding_length)
            # Alternate between the two URLs
            current_url = image_urls[i % len(image_urls)]
            # Get the file extension from the URL
            parsed_url = urlparse(current_url)
            file_extension = parsed_url.path.split(".")[-1]
            # Download the image binary data
            response = requests.get(current_url)
            if response.status_code == 200:
                file_data = response.content  # This is binary data (bytes)
                # Create filename with proper extension
                filename = f"{epoch_ms}_{formatted_index}.{file_extension}"
                writer.write_message(
                    message_data=file_data,
                    filename=filename,
                    data_source=data_source,
                    data_type=data_type,
                    mission_id=mission_id,
                    priority=1,
                    destination_ids=["s3"],
                    merge_chunks=True if i % 2 == 0 else False,
                )
            else:
                print(
                    f"Failed to download image from {current_url}. Status code: {response.status_code}"
                )
    except Exception as e:
        print(f"Error writing test messages: {e}")
    finally:
        writer.cleanup()

    # # Example 4.2 (10mb files)
    from vyomcloudbridge.services.queue_writer import QueueWriter
    import time

    default_mission_id = "_all_"
    writer = QueueWriter()
    try:
        import requests
        from urllib.parse import urlparse

        loop_len = 10
        padding_length = len(str(loop_len))
        # URLs for the images
        image_urls = [
            "https://www.sample-videos.com/img/Sample-jpg-image-10mb.jpg",
            "https://www.sample-videos.com/video321/3gp/144/big_buck_bunny_144p_10mb.3gp",
            "https://www.sample-videos.com/video321/mkv/480/big_buck_bunny_480p_10mb.mkv",
            "https://www.sample-videos.com/video321/mp4/720/big_buck_bunny_720p_10mb.mp4",
        ]
        for i in range(loop_len):
            epoch_ms = int(time.time() * 1000)
            data_source = "TEST_BINARY_FILE"  # event, warning, camera1, camera2
            data_type = "binary"  # image, json, binary
            mission_id = default_mission_id  # "34556"
            formatted_index = str(i + 1).zfill(padding_length)
            # Alternate between the two URLs
            current_url = image_urls[i % len(image_urls)]
            # Get the file extension from the URL
            parsed_url = urlparse(current_url)
            file_extension = parsed_url.path.split(".")[-1]
            # Download the image binary data
            response = requests.get(current_url)
            if response.status_code == 200:
                file_data = response.content  # This is binary data (bytes)
                # Create filename with proper extension
                filename = f"{epoch_ms}_{formatted_index}.{file_extension}"
                writer.write_message(
                    message_data=file_data,
                    filename=filename,
                    data_source=data_source,
                    data_type=data_type,
                    mission_id=mission_id,
                    priority=1,
                    destination_ids=["s3"],
                    merge_chunks=True if i % 2 == 0 else False,
                )
            else:
                print(
                    f"Failed to download image from {current_url}. Status code: {response.status_code}"
                )
    except Exception as e:
        print(f"Error writing test messages: {e}")
    finally:
        writer.cleanup()

    # Example 5 - send mission detail
    from vyomcloudbridge.services.queue_writer import QueueWriter

    writer = QueueWriter()
    try:
        mission_id = "301394"
        machine_id = 60
        epoch_ms = int(time.time() * 1000)
        filename = f"{epoch_ms}.json"

        mission_stats = {
            "mission": {
                "id": mission_id,
                "name": f"Test Mission {mission_id}",
                "creator_id": 1,
                "owner_id": 1,
                "mission_status": 1,
                "machine_id": machine_id,
                "mission_date": "2025-03-21",  # datetime.now(timezone.utc).strftime("%Y-%m-%d")
                "start_time": "2025-03-21T10:00:00Z",  # datetime.now(timezone.utc).isoformat()
                "end_time": None,  # datetime.now(timezone.utc).strftime("%Y-%m-%d")
                # less important field
                "description": "Testing mission navigation features",
                "campaign_id": 1,
                "mission_type": "",
                "json_data": {},
            }
        }
        writer.write_message(
            message_data=mission_stats,  # json or binary data
            filename=filename,  # 293749834.json, 93484934.jpg
            data_source=MISSION_STATS_DT_SRC,  # machine_pose camera1, machine_state
            data_type="json",  # image, binary, json
            mission_id=mission_id,  # mission_id
            priority=1,  # important send with priority 1
            destination_ids=["s3"],  # ["s3"]
        )
    except Exception as e:
        print(f"Error writing test messages: {e}")
    finally:
        writer.cleanup()

    # Example 6 - send mission topics list
    from vyomcloudbridge.services.queue_writer import QueueWriter

    writer = QueueWriter()
    try:
        mission_id = "301394"
        epoch_ms = int(time.time() * 1000)
        filename = f"{epoch_ms}.json"

        mission_stats = {
            "mission_topics": {} or []  # here you have to add, mission topics object
        }
        writer.write_message(
            message_data=mission_stats,  # json or binary data
            filename=filename,  # 293749834.json, 93484934.jpg
            data_source=MISSION_STATS_DT_SRC,  # machine_pose camera1, machine_state
            data_type="json",  # image, binary, json
            mission_id=mission_id,  # mission_id
            priority=1,  # important send with priority 1
            destination_ids=["s3"],  # ["s3"]
        )
    except Exception as e:
        print(f"Error writing test messages: {e}")
    finally:
        writer.cleanup()


if __name__ == "__main__":
    main()
