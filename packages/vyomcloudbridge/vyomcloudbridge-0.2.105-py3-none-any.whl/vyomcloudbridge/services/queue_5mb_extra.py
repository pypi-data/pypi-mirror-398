from vyomcloudbridge.services.queue_writer_json import QueueWriterJson

writer = QueueWriterJson()
try:
    import time

    default_mission_id = "_all_"
    import requests
    from urllib.parse import urlparse

    loop_len = 100
    padding_length = len(str(loop_len))
    # URLs for the images
    image_urls = [
        # "https://www.sample-videos.com/video321/mp4/720/big_buck_bunny_720p_5mb.mp4",
        "https://www.sample-videos.com/img/Sample-jpg-image-5mb.jpg",
        "https://mirror.del.albony.in/videolan-ftp/vlc/3.0.21/macosx/vlc-3.0.21-intel64.dmg",
        "https://www.sample-videos.com/video321/flv/360/big_buck_bunny_360p_5mb.flv",
    ]
    current_url = image_urls[0 % len(image_urls)]
    # Get the file extension from the URL
    parsed_url = urlparse(current_url)
    file_extension = parsed_url.path.split(".")[-1]
    # Download the image binary data
    response = requests.get(current_url)

    start_time_in_epoch = int(time.time() * 1000)
    print("Started")
    for i in range(loop_len):
        epoch_ms = int(time.time() * 1000)
        data_source = "TEST_BINARY_FILE"  # event, warning, camera1, camera2
        data_type = "image"  # image, json, binary
        mission_id = default_mission_id  # "34556"
        formatted_index = str(i + 1).zfill(padding_length)
        print(f"i={i}, formatted_index={formatted_index}")
        # Alternate between the two URLs
        # current_url = image_urls[i % len(image_urls)]
        # # Get the file extension from the URL
        # parsed_url = urlparse(current_url)
        # file_extension = parsed_url.path.split(".")[-1]
        # # Download the image binary data
        # response = requests.get(current_url)
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
                background=True
            )
        else:
            print(
                f"Failed to download image from {current_url}. Status code: {response.status_code}"
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
