from vyomcloudbridge import QueueWriterJson
import time
import json

if __name__ == "__main__":
    writer = QueueWriterJson()
    try:
        loop_len = 20
        padding_length = len(str(loop_len))

        for i in range(loop_len):
            priority = 1
            message_data = {
                "data": f"Test message (P{priority})",
                "data_id": f"data_id_{i}",
            }
            epoch_ms = int(time.time() * 1000)
            data_source = "camera1"  # event, warning, camera1, camera2,
            data_type = "image"  # image, json, file, video
            mission_id = "34556"

            formatted_index = str(i + 1).zfill(padding_length)

            writer.write_message(
                message_data=json.dumps(message_data),
                filename=f"{epoch_ms}_{formatted_index}.json",
                data_source=data_source,
                data_type=data_type,
                mission_id=mission_id,
                priority=priority,
            )
    except Exception as e:
        pass
