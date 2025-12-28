# In a new shared file (e.g., shared_memory_utils.py)
import json
import pickle
from multiprocessing import shared_memory
import threading


class SharedMemoryUtil:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(SharedMemoryUtil, cls).__new__(cls)
                    cls._instance._init_shared_memory()
        return cls._instance

    def _init_shared_memory(self):
        # Define initial empty dict
        init_data = {}
        serialized_data = pickle.dumps(init_data)

        # Size with some buffer for growth
        buffer_size = max(len(serialized_data) * 10, 10240)  # At least 10KB

        try:
            # Try to attach to existing shared memory
            self.shm = shared_memory.SharedMemory(name="mavlink_ack_data")
            # If it exists, don't initialize it
        except FileNotFoundError:

            # Create new shared memory if it doesn't exist
            self.shm = shared_memory.SharedMemory(
                name="mavlink_ack_data", create=True, size=buffer_size
            )
            # Initialize with empty dict
            self.shm.buf[: len(serialized_data)] = serialized_data
            # Store the length
            length_bytes = len(serialized_data).to_bytes(4, byteorder="little")
            self.shm.buf[buffer_size - 4 : buffer_size] = length_bytes

    def get_data(self, data_name):
        try:
            # Attach to existing shared memory
            return shared_memory.SharedMemory(name=data_name)
        except FileNotFoundError:
            # If it doesn't exist, return None or raise an error
            return None

    def set_data(self, data_name, data):
        with self._lock:
            # shared_memory.SharedMemory(
            #     name=data_name, create=False, size=1
            # )

            try:
                # Try to create new shared memory
                shared_memory.SharedMemory(name=data_name, create=True, size=1)
            except FileExistsError:
                return

    def cleanup(self):
        self.shm.close()
        # Unlink only when the application is shutting down
        # to avoid removing shared memory while other processes are using it
        self.shm.unlink()
