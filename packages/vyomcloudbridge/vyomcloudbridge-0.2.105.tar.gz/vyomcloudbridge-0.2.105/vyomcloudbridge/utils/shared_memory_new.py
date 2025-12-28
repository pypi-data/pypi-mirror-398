import pickle
import time
from typing import Any
from multiprocessing import shared_memory, Lock
import threading
from vyomcloudbridge.utils.logger_setup import setup_logger


class SharedMemoryUtil:
    _instance = None
    _global_lock = threading.Lock()
    _key_locks = {}

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._global_lock:
                if cls._instance is None:
                    cls._instance = super(SharedMemoryUtil, cls).__new__(cls)
                    cls._instance._key_locks = {}
        return cls._instance

    def __init__(self, log_level=None):
        self.logger = setup_logger(
            name=self.__class__.__module__ + "." + self.__class__.__name__,
            show_terminal=False,
            log_level=log_level,
        )
        init_data = {}
        serialized_data = pickle.dumps(init_data)
        self.buffer_size = max(len(serialized_data) * 10, 10240)
        pass

    def _get_lock(self, key):  # private method
        if key not in self._key_locks:
            with self._global_lock:
                if key not in self._key_locks:
                    self._key_locks[key] = Lock()
        return self._key_locks[key]

    def get_lock(self, key):  # public method
        """Get a lock for a given key, create if it doesn't exist."""
        if not key or not isinstance(key, str):
            raise ValueError("Key must be non empty string")
        if not key.startswith("vyomcloudbridge_"):
            key = f"vyomcloudbridge_{key}"

        if key not in self._key_locks:
            with self._global_lock:
                if key not in self._key_locks:
                    self._key_locks[key] = Lock()
        return self._key_locks[key]

    def _get_shm(self, key, size=None):
        """Get shared memory by key, create if it doesn't exist."""
        try:
            return shared_memory.SharedMemory(name=key)
        except FileNotFoundError:
            if size is not None:
                return shared_memory.SharedMemory(name=key, create=True, size=size)
            else:
                return shared_memory.SharedMemory(
                    name=key, create=True, size=self.buffer_size
                )

    def set_data(self, key: str, value: Any):
        """Set data in shared memory with a given key."""
        if not key or not isinstance(key, str):
            raise ValueError("Key must be non empty string")
        if not key.startswith("vyomcloudbridge_"):
            key = f"vyomcloudbridge_{key}"

        data_bytes = pickle.dumps(value)
        shm = self._get_shm(key, size=len(data_bytes))
        if shm.size < len(data_bytes):
            shm.close()
            shm.unlink()
            shm = shared_memory.SharedMemory(
                name=key, create=True, size=len(data_bytes)
            )
        shm.buf[: len(data_bytes)] = data_bytes
        shm.close()
        return True

    def get_data(self, key: str):
        """Get data from shared memory by key."""
        if not key or not isinstance(key, str):
            raise ValueError("Key must be non empty string")
        if not key.startswith("vyomcloudbridge_"):
            key = f"vyomcloudbridge_{key}"

        shm = self._get_shm(key)
        if shm is None:
            return None
        try:
            data = bytes(shm.buf[:])
            return pickle.loads(data)
        except pickle.UnpicklingError as e:
            self.logger.error(f"Failed to unpickle data for key '{key}': {e}")
            self.delete_data(key)
            return None
        finally:
            shm.close()

    def delete_data(self, key: str):
        """Delete data from shared memory by key."""
        if not key or not isinstance(key, str):
            raise ValueError("Key must be non empty string")
        if not key.startswith("vyomcloudbridge_"):
            key = f"vyomcloudbridge_{key}"

        shm = self._get_shm(key)
        if shm:
            shm.close()
            shm.unlink()
            return True
        return False

    def cleanup(self):
        """Cleanup all shared memory segments."""
        for key in list(self._key_locks.keys()):
            try:
                shm = self._get_shm(key)
                shm.close()
                shm.unlink()  # this will delete the shared memory segment
            except FileNotFoundError:
                pass
            finally:
                del self._key_locks[key]
        self._key_locks.clear()

    def __del__(self):
        """Ensure cleanup on deletion."""
        try:
            self.logger.error(
                "Destructor called by garbage collector to cleanup SharedMemoryUtil"
            )
            self.cleanup()
        except Exception as e:
            pass


if __name__ == "__main__":
    # Example 1, set only
    data_key = "vyomcloudbridge_example_key"
    start_time_in_epoch = int(time.time() * 1000)
    print("\nStart Time:", threading.current_thread().name)

    print("\nExample 0: get only")
    sm_util = SharedMemoryUtil()
    data = sm_util.get_data(data_key)
    print("Retrieved data:", data)

    print("\nExample 1: Set only")
    sm_util = SharedMemoryUtil()
    success = sm_util.set_data(data_key, {"count": 42, "status": "active"})
    print("Set success:", success)

    # Example 2, set and get
    print("\nExample 2: Get, Set and Get")
    sm_util = SharedMemoryUtil()
    data = sm_util.get_data(data_key)
    print("Retrieved data:", data)
    success = sm_util.set_data(data_key, {"count": 42, "status": "active"})
    print("Set success:", success)
    data = sm_util.get_data(data_key)
    print("Retrieved data:", data)

    # Example 3, set and update existing data
    print("\nExample 3: Set and Update Existing Data")
    sm_util = SharedMemoryUtil()
    success = sm_util.set_data(data_key, {"count": 42, "status": "active"})
    print("Set success:", success)
    data = sm_util.get_data(data_key)
    print("Retrieved data:", data)

    lock = sm_util.get_lock(data_key)
    with lock:
        data = sm_util.get_data(data_key)
        if data:
            data["count"] += 1
        sm_util.set_data(data_key, data)
        print("Updated data:", data)
    print("Data updated successfully.")

    time.sleep(15)
    print("\nExample 4: get only")
    sm_util = SharedMemoryUtil()
    data = sm_util.get_data(data_key)
    print("Retrieved data:", data)

    sm_util = SharedMemoryUtil()
    start_time_in_epoch2 = int(time.time() * 1000)
    print(
        "Time taken after example 3:", start_time_in_epoch2 - start_time_in_epoch, "ms"
    )
