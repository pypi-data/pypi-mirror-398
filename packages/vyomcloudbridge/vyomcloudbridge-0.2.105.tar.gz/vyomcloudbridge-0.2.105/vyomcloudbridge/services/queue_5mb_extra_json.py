from vyomcloudbridge.services.queue_writer_json import QueueWriterJson

writer = QueueWriterJson()
try:
    import time

    default_mission_id = "_all_"
    import requests
    from urllib.parse import urlparse

    loop_len = 100
    padding_length = len(str(loop_len))

    start_time_in_epoch = int(time.time() * 1000)
    print("Started")
    for i in range(loop_len):
        mission_id = default_mission_id  # "34556"
        formatted_index = str(i + 1).zfill(padding_length)
        print(f"i={i}, formatted_index={formatted_index}")
        epoch_ms = int(time.time() * 1000)
        message_data = {
            "data": f"Test message No {i}",
            "data_id": epoch_ms,
            "lat": 75.66666,
            "long": 73.0589455,
            "alt": 930,
        }

        filename = f"{epoch_ms}_{formatted_index}.json"
        writer.write_message(
            message_data=message_data,
            filename=filename,
            data_source="MACHINE_POSE",
            data_type="json",
            mission_id="111333",
            send_live=True,
            priority=1,
            destination_ids=["s3", "gcs_mqtt"],
            merge_chunks=True if i % 2 == 0 else False,
            background=True
        )

    end_time_in_epoch = int(time.time() * 1000)
    time_diff = end_time_in_epoch - start_time_in_epoch
    print(f"Time taken to write {loop_len} messages= {time_diff}")
    # time.sleep(30)
except Exception as e:
    print(f"Error writing test messages: {e}")
finally:
    pass
    # writer.cleanup()
