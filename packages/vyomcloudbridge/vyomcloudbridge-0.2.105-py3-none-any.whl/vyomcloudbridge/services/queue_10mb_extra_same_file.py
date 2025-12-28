from vyomcloudbridge.services.queue_writer import QueueWriter
import time
import os

default_mission_id = "_all_"
data_type = "binary"
data_source = "TEST_FILE"
target_upload_size = 1000 #
writer = QueueWriter()

try:
    
    
    
    # Resolve local sample file path in constants directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    constants_dir = os.path.normpath(os.path.join(current_dir, "..", "constants"))
    sample_file_path = os.path.join(constants_dir, "sample_image.jpg")
    
    if not os.path.exists(sample_file_path):
        print(f"Sample file not found at {sample_file_path}")
    else:
        print(f"Reading image from {sample_file_path}")
        with open(sample_file_path, "rb") as f:
            file_data = f.read()
        print(f"File read complete, data size: {len(file_data)} bytes")
        
        file_size = len(file_data) / (1024 * 1024) # MB
        loop_len = int(target_upload_size/file_size)
        if(target_upload_size%file_size):
            loop_len = loop_len +1 # 1 more increment
        padding_length = len(str(loop_len))
        
        # Get file extension from the file path
        file_extension = os.path.splitext(sample_file_path)[1].lstrip(".")
        epoch_ms = int(time.time() * 1000)
        
        for i in range(loop_len):
            formatted_index = str(i + 1).zfill(padding_length)
            filename = f"{epoch_ms}_{formatted_index}.{file_extension}"
            writer.write_message(
                message_data=file_data,
                filename=filename,
                data_source=data_source,
                data_type=data_type,
                mission_id=default_mission_id,
                priority=2,
                destination_ids=["s3"],
                merge_chunks=True,
                background=False,
            )
            print(f"Loop {i+1} of {loop_len} completed")
        print(f"Successfully wrote {loop_len} messages")
except Exception as e:
    print(f"Error writing test messages: {e}")
finally:
    writer.cleanup()
