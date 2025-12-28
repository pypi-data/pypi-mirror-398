from vyomcloudbridge.services.queue_writer_json import QueueWriterJson
import time

default_mission_id = "_all_"
writer = QueueWriterJson()
try:
    import requests
    from urllib.parse import urlparse

    loop_len = 2
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
                background=True,
            )
        else:
            print(
                f"Failed to download image from {current_url}. Status code: {response.status_code}"
            )
except Exception as e:
    print(f"Error writing test messages: {e}")
finally:
    writer.cleanup()
