import requests
import json
from typing import Optional, Dict, Any
from vyomcloudbridge.constants.constants import (
    rabbit_mq_url,
    rabbit_mq_username,
    rabbit_mq_password,
    main_data_queue,
)


class RabbitMQUtils:
    def __init__(
        self,
        management_url: str = rabbit_mq_url,
        username: str = rabbit_mq_username,
        password: str = rabbit_mq_password,
        log_level=None,
    ):
        self.management_url = management_url.rstrip("/")
        self.auth = (username, password)

    def get_queue_stats(self, queue_name: str) -> Optional[Dict[str, Any]]:
        """Get complete queue statistics from RabbitMQ Management API"""
        try:
            # %2F is URL encoded forward slash for default vhost "/"
            url = f"{self.management_url}/api/queues/%2F/{queue_name}"
            response = requests.get(url, auth=self.auth, timeout=10)

            if response.status_code == 200:
                return response.json(), None
            elif response.status_code == 404:
                return None, f"Queue '{queue_name}' not found"
            else:
                return None, f"Error: HTTP {response.status_code} - {response.text}"

        except requests.exceptions.RequestException as e:
            return None, f"Error connecting to RabbitMQ Management API: {e}"
        except Exception as e:
            return None, f"Unexpected error: {e}"

    def get_queue_info(self, queue_name: str) -> Dict[str, Any]:
        """Get queue size and message count information"""
        stats, error = self.get_queue_stats(queue_name)
        if error:
            return {
                "queue_name": queue_name,
                "messages": 0,
                "memory": 0,
                "memory_mb": 0.0,
                "messages_ready": 0,
                "messages_unacknowledged": 0,
            }, error
        else:
            messages = stats.get("messages", 0)
            memory = stats.get("memory", 0)
            messages_ready = stats.get("messages_ready", 0)
            messages_unacknowledged = stats.get("messages_unacknowledged", 0)
            return {
                "queue_name": queue_name,
                "messages": messages,
                "memory": memory,
                "memory_mb": round(memory / (1024 * 1024), 2),
                "messages_ready": messages_ready,
                "messages_unacknowledged": messages_unacknowledged,
            }, None

    def get_all_queues(self) -> Optional[list]:
        """Get list of all queues"""
        try:
            url = f"{self.management_url}/api/queues"
            response = requests.get(url, auth=self.auth, timeout=10)

            if response.status_code == 200:
                return response.json(), None
            else:
                return None, f"Error getting queues: HTTP {response.status_code}"

        except Exception as e:
            return None, f"Error getting all queues: {e}"


if __name__ == "__main__":
    # Example 1: get queue stats
    rabbit_mq_utils = RabbitMQUtils()
    queue_name = main_data_queue
    print("\U0001f430 RabbitMQ Queue Size Checker")
    print(f"\n{'='*50}")
    print(f"Queue: {queue_name}")
    print(f"{'='*50}")
    info, error = rabbit_mq_utils.get_queue_info(queue_name)
    if error:
        print(f"Error: {error}")
        exit(1)
    else:
        print(f"\U0001f4ca Total Messages: {info['messages']:,}")
        print(f"\u2705 Ready Messages: {info['messages_ready']:,}")
        print(f"\u23f3 Unacked Messages: {info['messages_unacknowledged']:,}")
        print(
            f"\U0001f4be Memory Usage: {info['memory']:,} bytes ({info['memory_mb']} MB)"
        )
        if info["messages"] > 0:
            avg_size = info["memory"] / info["messages"]
            print(f"\U0001f4cf Average Message Size: {avg_size:.2f} bytes")

    # Example 2: get all queues
    all_queues, error = rabbit_mq_utils.get_all_queues()
    if error:
        print(f"Error: {error}")
        exit(1)
    else:
        all_queues_names = [queue.get("name") for queue in all_queues]
        print(f"All Queues: {all_queues_names}")
