import shutil
from datetime import datetime
import os
import glob

from vyomcloudbridge.utils.configs import Configs

def create_copy_data_logger(f_machine_id):
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_log_dir = f"/var/log/vyomcloudbridge/mavlogs"
        log_dir = f"{base_log_dir}/{f_machine_id}/"
        
        dest_log_dir = f"{base_log_dir}/dir_watch_data_logs/{f_machine_id}/"
        
        if not os.path.isdir(log_dir):
            print(f"Directory not found: {log_dir}")
            return
            

        
        print("Contents of log dir:", os.listdir(log_dir))

        # Find all .BIN files
        bin_files = glob.glob(os.path.join(log_dir, "*.BIN"))


        if not bin_files:
            print("No numbered .BIN files found.")
        else:
            # Sort by numeric filename (e.g., 1.BIN → 1)
            bin_files.sort(key=lambda f: int(os.path.basename(f).split('.')[0]))
            latest_bin = bin_files[-1]
            print(f"Copying latest BIN file: {latest_bin}")
            
            os.makedirs(dest_log_dir, exist_ok=True)

            dest_file = os.path.join(dest_log_dir, os.path.basename(latest_bin))
            shutil.copyfile(latest_bin, dest_file)
            print(f"Copied to: {dest_file}")


    except Exception as e:
        print(f"Error copying data logger: {str(e)}")
        
        
def main():
    """Main function to copy data logger file."""
    machine_config = Configs.get_machine_config()
    machine_id = machine_config.get("machine_id", "-") or "-"
            

    create_copy_data_logger(machine_id)

if __name__ == "__main__":
    main()
    