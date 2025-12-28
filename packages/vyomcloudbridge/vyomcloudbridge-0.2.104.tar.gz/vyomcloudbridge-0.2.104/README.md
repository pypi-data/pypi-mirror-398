### Install RabbitMQ server

sudo apt install rabbitmq-server -y

### Start the RabbitMQ service

sudo systemctl start rabbitmq-server

### Enable RabbitMQ to start on boot

sudo systemctl enable rabbitmq-server

### Enable the RabbitMQ management plugin

sudo rabbitmq-plugins enable rabbitmq_management

### Check RabbitMQ service status

### sudo systemctl status rabbitmq-server

### Check RabbitMQ version

### rabbitmqctl --version

### It will get started at below port

http://localhost:15672/
Default username: guest
Default password: guest

# For MAC

brew update
brew install rabbitmq
rabbitmqctl --version
brew services start rabbitmq

### Check if RabbitMQ is running

brew services list

### Start RabbitMQ

brew services start rabbitmq
http://localhost:15672/
Default username: guest
Default password: guest

### Stop RabbitMQ (if needed)

brew services stop rabbitmq

### Restart RabbitMQ (if needed)

brew services restart rabbitmq

vyomcloudbridge/
├── vyomcloudbridge/
│ ├── **init**.py
│ ├── services/
│ │ ├── **init**.py
│ │ ├── queue_worker.py
│ ├── utils/
│ │ ├── **init**.py
│ │ └── logger_setup.py
│ ├── cli.py
│ └── service_manager.py
├── setup.py
└── README.md

# Contents of setup.py

from setuptools import setup, find_packages

setup(
name="my-service-demo",
version="0.1.0",
packages=find_packages(),
install_requires=[
"argparse",
],
entry_points={
'console_scripts': [
'vyomcloudbridge=vyomcloudbridge.cli:main',
],
},
author="Vyom OS Admin",
author_email="amardeep@vyomos.org",
description="A communication service for vyom cloud",
long_description=open("README.md").read(),
long_description_content_type="text/markdown",
url="https://github.com/yourusername/my-service-demo",
classifiers=[
"Programming Language :: Python :: 3",
"License :: OSI Approved :: MIT License",
"Operating System :: OS Independent",
],
python_requires=">=3.6",
)

# Contents of requirements.txt

Python requirement:

```text
python=">=3.6"
```

argparse>=1.4.0

# Contents of README.md

# My Service Demo

A simple service management demonstration package that runs a "hello1" logging service.

# Installation from the cloned repository

```bash
pip install -e .
```

## Usage

Start any service using service_name:

# VyomCloudBridge Services Guide

## 📋 **Common Arguments for All Services**

| Flag               | Type    | Description                            | Example          |
| ------------------ | ------- | -------------------------------------- | ---------------- |
| `--name`           | String  | Custom instance name for the service   | `--name worker1` |
| `--system-default` | Boolean | Mark if a service is started by system |

# Without multi-thread/False:

```bash
vyomcloudbridge start queueworker
```

# With multi-thread/True:

```bash
vyomcloudbridge start queueworker --multi-thread
```

# 📂 **VyomCloudBridge Directory Watcher**

## 🚀 **Basic Command to Start Directory Watcher**

Use the following command to start monitoring a directory and manage file uploads with specified properties:

```bash
vyomcloudbridge start dirwatcher --dir /path/to/dir --dir-properties /path/to/properties.json
```

| Argument           | Type   | Description                                                                                                   |
| ------------------ | ------ | ------------------------------------------------------------------------------------------------------------- |
| `--dir-properties` | String | Path to the properties file (in JSON format) that will be saved to S3. You may include any additional information about the files in this directory |

| Flag              | Type    | Description                                                                                         |
| ----------------- | ------- | --------------------------------------------------------------------------------------------------- |
| `--mission-dir`   | Boolean | If included, the <dir> provided will be considered a mission data directory.                        |
| `--send-live`     | Boolean | If included (only along with --mission-dir), the device will send data for live, and with priroty.  | 
| `--merge-chunks`  | Boolean | If included, combines S3 chunks after all have been uploaded.                                       |
| `--preserve-file` | Boolean | If included, files will be moved to <dir>\_preserve instead of being deleted after uploading to S3. |
| `--priority`      | Number  | priority order in which the data will be uploaded, [0,3], higher is more                            |

## ✅ **Usage Examples**

1. **Basic Directory Watcher**

```bash
vyomcloudbridge start dirwatcher --dir /data/files --dir-properties /config/properties.json
```

2. **Mission Directory with Chunk Merging and Priority**

```bash
vyomcloudbridge start dirwatcher --dir /data/mission --dir-properties /config/mission.json --mission-dir --merge-chunks --priority 2
```

3. **Directory with File Preservation After Upload**

```bash
vyomcloudbridge start dirwatcher --dir /backup/logs --dir-properties /config/logs.json --preserve-file
```

# Start Mission Stats Monitor:

```bash
vyomcloudbridge start missionstats
```

# Start Machine Stats Service:

```bash
vyomcloudbridge start machinestats
```

Stop the any service using <service_name>:

```bash
vyomcloudbridge stop <service_name>
```

List running services:

```bash
vyomcloudbridge list
```

List all services (running/stopped):

```bash
vyomcloudbridge list -a
```

Check library setup/health status:

```bash
vyomcloudbridge status
```

OR

```bash
vyomcloudbridge status <service_name>
```

## License

MIT License - see LICENSE file for details.

Pypi

# install

```bash
python -m pip install --upgrade build
```

```bash
python -m pip install --upgrade twine
```

# cleanup

```bash
rm -rf dist/ build/ *.egg-info/
```

# Build distribution packages

```bash
python -m build
```

# Pubblish to Prod

```bash
python -m twine upload dist/*
```

# Pubblish to test

```bash
python -m twine upload --repository-url https://test.pypi.org/legacy/ dist/*
```

# Installing from TEST PyPI

# If development dependencies are installed separately:

```bash
sudo pip install --index-url https://test.pypi.org/simple/ vyomcloudbridge
```

```bash
sudo pip install --index-url https://test.pypi.org/simple/ vyomcloudbridge==0.1.0
```

## If development dependencies are not installed:

```bash
sudo pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ vyomcloudbridge
```

```bash
sudo pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ vyomcloudbridge==0.1.4
```

# Make setup

```bash
sudo vyomcloudbridge setup
```

# After installation, here are the detail that you can use

# certificates

/etc/vyomcloudbridge/certs/

# logs

/var/log/vyomcloudbridge/
tail -f -n 1000 /var/log/vyomcloudbridge/vyomcloudbridge.log

# config

/etc/vyomcloudbridge/machine.conf

# service_unit_file (For Systemd)

/etc/systemd/system/vyomcloudbridge.service

```bash
sudo systemctl status vyomcloudbridge.service
```

```bash
sudo systemctl restart vyomcloudbridge.service
```

```bash
sudo journalctl -u vyomcloudbridge.service
```

# config

/etc/vyomcloudbridge/vyomcloudbridge.sh

# Directory Structure Guidelines

## Mission Related Data

All mission related data should be stored under:
Base directory: MISSION_DIR=/home/admin/Documents/mission_data

### Mission Directory Structure

Mission data follows a nested directory structure in this format:
/home/admin/Documents/mission_data/<date>/<project_id>/<mission_id>/<data_source>/<file_name>
Where:

- `<date>`: Date in YYYY-MM-DD format
- `<project_id>`: Project identifier (or "_all_" for general mission data)
- `<mission_id>`: Mission identifier
- `<data_source>`: Source of the data (e.g., camera1, camera2)
- `<file_name>`: Name of the data file

### the s3 data path will look like this

### Property File Path S3

<organization_id>/<project_id>/<date>/<machine_id>/<mission_id>/<data_source>/<file_name>

### File Chunks Path S3

<organization_id>/<project_id>/<date>/<machine_id>/<mission_id>/<data_source>/chunk/<chunk_name.bin>

### For general mission data, when to project linked

<organization_id>/_all_/<date>/<machine_id>/<mission_id>/<data_source>/<file_name>


#### Valid Examples

/home/admin/Documents/mission*data/1997-02-28/\_all*/m-2344/camera1/imaage_2023_12_23.jpg
/home/admin/Documents/mission_data/1997-02-28/p_46/m-2344/camera2/imaage_2025_02_11.jpg

## Non-Mission Related Data

All non-mission related data should be stored under:
Base directory: UPLOAD_DIR=/home/admin/Documents/upload_data

### Upload Directory Structure

Files can be placed directly in the upload directory or within up to two nested subdirectories:
/home/admin/Documents/upload_data/[folder1]/[folder2]/<file_name>
Maximum nesting level: 2 directories deep

#### Valid Examples

/home/admin/Documents/upload_data/debug.log
/home/admin/Documents/upload_data/folder1/folder2/debug.log

#### Invalid Example

/home/admin/Documents/upload_data/folder1/folder2/folder3/debug.log # Too many nested directories

### the s3 data path will look like this

### Property File Path S3p

<organization_id>/_uploads_/<machine_id>/<relative_dir_wrt_UPLOAD_DIR>/<file_name>

### File Chunks Path S3

<organization_id>/_uploads_/<machine_id>/<relative_dir_wrt_UPLOAD_DIR>/chunk/<chunk_name.bin>


## ROS 2 System Message Publisher

This repository provides a ROS 2 publisher setup for testing and publishing messages to various topics. The messages can either be entered manually or generated randomly for testing. The code is modular and can be easily integrated into other projects.

### Prerequisites

Ensure you have the following prerequisites installed:

- **ROS 2**: A ROS 2 installation (Humble or later).
- **Python 3**: Python 3.6 or later.
- **vyom_common**: Ensure the `vyom_common` package is built and sourced before using the publisher.

### Setup

#### 1. Source the ROS 2 Workspace

Before running any scripts, source the ROS 2 workspace, including the `vyom_common` package:

```bash
source ~/vyom_workspace/vyom_common/install/setup.bash
```

#### 2. Build the Workspace (if needed)

If you haven't already built your workspace, navigate to the workspace directory and build it:

```bash
cd ~/vyom_workspace/
colcon build --symlink-install
```

# API writer
### Here is the default path of data being taken from device
### For general, when there is mission
<organization_id>/_all_/<date>/<machine_id>/<mission_id>/<data_source>/<file_name>
### For general, when there is no mission
<organization_id>/_all_/<date>/<machine_id>/_all_/<data_source>/<file_name>


#### 3. Run the ROS System Message Publisher

Run the publisher node to send messages to various topics. The publisher can accept either random or user-provided data.

**Run the Publisher:**

```bash
python3 test_ros_system_msg_publisher.py
```

**Input Options:**

When running the publisher, you'll be prompted to choose whether to use random values for testing:

```text
Do you want to use random values for testing? [Y/n]: y
```

- If you choose `y`, the publisher will generate random values for each message type.
- If you choose `n`, you'll be asked to enter your own data for each message type.

#### 4. Run the ROS System Message Subscriber

Run the subscriber node to receive messages from the publisher. The subscriber listens to the topics and logs the received messages.

**Run the Subscriber:**

```bash
python3 test_ros_system_msg_subscriber.py
```

**Output Example:**

```text
[INFO] [1745841738.356770665] [ros_system_msg_subscriber]: Received on 'access': vyom_msg.msg.Access(encrypted='NJAhX6NQy4lHN3E9')
```

#### 5. Integration with Other Projects

You can import the `RosSystemMsgPublisher` class into your Python scripts to programmatically publish messages.

**Example:**

```python
import rclpy
from ros_system_msg_publisher import RosSystemMsgPublisher

def main(args=None):
    ros_msg_publisher = RosSystemMsgPublisher()

    input_data = [
        {"typ": "Access", "msg": {"encrypted": "new_encrypted_text"}},
        {"typ": "Accessinfo", "msg": {"end_time": 1714322230, "current_date": 1714321220, "user_id": 2001}},
        {"typ": "Ack", "msg": {"msgid": "msg002", "chunk_id": 20}},
        {"typ": "Auth", "msg": {"auth_key": "new_auth_key"}},
        {"typ": "Dvid", "msg": {"device_id": 1005}}
    ]

    # Setup all publishers for the input data
    for item in input_data:
        ros_msg_publisher.setup_publisher(item["typ"], item["msg"])

    # Publish all the messages
    ros_msg_publisher.publish_all()

    # Spin the node
    ros_msg_publisher.spin_once(timeout_sec=1.0)

    # Graceful shutdown
    ros_msg_publisher.cleanup() # pass .cleanup(shutdown_ros=True) for graceful shutdown

if __name__ == "__main__":
    main()
```

#### 6. Testing the Publisher & Subscriber with Random Values

You can test the interaction between the publisher and subscriber using randomly generated data.

1. **Run the Publisher:**

   ```bash
   python3 test_ros_system_msg_publisher.py
   ```

   When prompted, choose `y` to use random values for testing.

2. **Run the Subscriber:**

   ```bash
   python3 test_ros_system_msg_subscriber.py
   ```

   The subscriber will log the messages it receives, as shown in the example output above.

### File Structure

The package structure is as follows:

```plaintext
.
├── README.md                   # This file
├── vyom-cloud-bridge/vyomcloudbridge/utils/ros_system_msg_publisher.py # Publisher script
└── tests/
    ├── test_ros_system_msg_publisher.py
    └── test_ros_system_msg_subscriber.py
```

