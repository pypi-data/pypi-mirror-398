#!/bin/bash
# This script will run during installation
# Get the API URL from Python module
MACHINE_REGISTER_API_URL=$(python3 -c "from vyomcloudbridge.constants.constants import MACHINE_REGISTER_API_URL; print(MACHINE_REGISTER_API_URL)")

echo "Running post-installation setup for vyomcloudbridge..."

# Echo "Hello VyomOS" five times
echo "Printing welcome message..."
for i in {1..5}; do
    echo "Hello VyomOS"
done

# Check if we're in an interactive environment
if [ -t 0 ]; then
    # Interactive mode - prompt for inputs
    echo "Please enter device registration information:"
    echo -n "Organization ID: "
    read organization_id
    echo -n "Machine UID: "
    read machine_uid
    echo -n "Device Name: "
    read device_name
    echo -n "Machine Model ID: "
    read machine_model_id
    
    # Only proceed with registration if we have all required values
    if [ -n "$organization_id" ] && [ -n "$machine_uid" ] && [ -n "$machine_model_id" ]; then
        register_device=true
    else
        echo "Missing required registration information. Registration skipped."
        register_device=false
    fi
else
    # Non-interactive mode - skip registration during package installation
    echo "Running in non-interactive mode. Device registration will be skipped."
    echo "Please run 'vyomcloudbridge setup' after installation to register your device."
    register_device=false
fi

# Only perform registration if we have the necessary information
if [ "$register_device" = true ]; then
    # Create payload JSON
    payload="{\"organization_id\": $organization_id, \"machine_uid\": \"$machine_uid\", \"name\": \"$device_name\", \"machine_model_id\": $machine_model_id}"
    echo "Registration payload: $payload"

    # Make API call to register device
    echo "Registering device with VyomIO API..., using API URL: $MACHINE_REGISTER_API_URL"
    
    response=$(curl -s -X POST -H "Content-Type: application/json" -d "$payload" "$MACHINE_REGISTER_API_URL")

    # Check if curl command was successful
    if [ $? -ne 0 ]; then
        echo "Error: Failed to connect to the API server"
        exit 1
    fi

    # Extract status from response
    status=$(echo $response | grep -o '"status":[0-9]*' | cut -d':' -f2)

    if [ "$status" == "200" ]; then
        echo "Device registration successful!"
        
        # Create config directory if it doesn't exist
        CONFIG_DIR="/etc/vyomcloudbridge"
        if [ ! -d "$CONFIG_DIR" ]; then
            if [ "$EUID" -ne 0 ]; then
                echo "Creating config directory requires root privileges."
                echo "Please run: sudo mkdir -p $CONFIG_DIR"
                exit 0
            fi
            mkdir -p "$CONFIG_DIR"
        fi
        
        # Extract data from response and save in INI format
        echo "Saving device configuration..."
        
        # Convert JSON to INI format
        machine_config_file="$CONFIG_DIR/machine.conf"
        
        if [ "$EUID" -ne 0 ]; then
            echo "Writing to $machine_config_file requires root privileges."
            echo "Response data: $response"
            echo "Please manually create the configuration file."
            exit 0
        fi
        
        # Extract data section from the response
        data=$(echo $response | sed -n 's/.*"data":\([^}]*}\).*/\1/p')
        
        # Create INI file
        echo "[MACHINE]" > "$machine_config_file"
        echo "machine_id=$(echo $data | grep -o '"id":[0-9]*' | cut -d':' -f2)" >> "$machine_config_file"
        echo "machine_uid=$(echo $data | grep -o '"machine_uid":"[^"]*"' | sed 's/"machine_uid":"//;s/"//')" >> "$machine_config_file"
        echo "machine_name=$(echo $data | grep -o '"name":"[^"]*"' | sed 's/"name":"//;s/"//')" >> "$machine_config_file"
        echo "machine_model=$(echo $data | grep -o '"machine_model":[0-9]*' | cut -d':' -f2)" >> "$machine_config_file"
        echo "machine_model_name=$(echo $data | grep -o '"machine_model_name":"[^"]*"' | sed 's/"machine_model_name":"//;s/"//')" >> "$machine_config_file"
        echo "machine_model_type=$(echo $data | grep -o '"machine_model_type":"[^"]*"' | sed 's/"machine_model_type":"//;s/"//')" >> "$machine_config_file"
        echo "mfg_date=$(echo $data | grep -o '"mfg_date":"[^"]*"' | sed 's/"mfg_date":"//;s/"//')" >> "$machine_config_file"
        echo "activation_date=$(echo $data | grep -o '"activation_date":[^,]*' | cut -d':' -f2)" >> "$machine_config_file"
        echo "end_of_service_date=$(echo $data | grep -o '"end_of_service_date":[^,]*' | cut -d':' -f2)" >> "$machine_config_file"
        echo "organization_id=$(echo $data | grep -o '"current_owner":[0-9]*' | cut -d':' -f2)" >> "$machine_config_file"
        echo "organization_name=$(echo $data | grep -o '"current_owner_name":"[^"]*"' | sed 's/"current_owner_name":"//;s/"//')" >> "$machine_config_file"
        echo "usage_status=$(echo $data | grep -o '"usage_status":"[^"]*"' | sed 's/"usage_status":"//;s/"//')" >> "$machine_config_file"
        echo "camera_feed=$(echo $data | grep -o '"camera_feed":"[^"]*"' | sed 's/"camera_feed":"//;s/"//')" >> "$machine_config_file"
        echo "created_at=$(echo $data | grep -o '"created_at":"[^"]*"' | sed 's/"created_at":"//;s/"//')" >> "$machine_config_file"
        echo "updated_at=$(echo $data | grep -o '"updated_at":"[^"]*"' | sed 's/"updated_at":"//;s/"//')" >> "$machine_config_file"
        
        echo "Configuration saved to $machine_config_file"
    else
        echo "Device registration failed with status: $status"
        echo "Response: $response"
        # Don't exit with error here, allow installation to continue
    fi
fi

# Create systemd service file if root
SERVICE_FILE="/etc/systemd/system/vyomcloudbridge.service"
if [ "$EUID" -eq 0 ]; then
    echo "Creating systemd service file at $SERVICE_FILE"
    
    # Get username (try to get actual user even when running with sudo)
    username=$(logname || whoami)
    cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Camera Capture Service
After=network.target rabbitmq-server.service
Wants=rabbitmq-server.service

[Service]
Type=simple
User=$username
WorkingDirectory=/home/$username/Documents/arducam
ExecStart=/bin/bash /home/$username/Documents/arducam/start_capture.sh
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal
LogRateLimitIntervalSec=0
LogRateLimitBurst=0
KillMode=process
KillSignal=SIGTERM
TimeoutStartSec=60
TimeoutStopSec=30

[Install]
WantedBy=multi-user.target
EOF

    # Enable and start the service
    echo "Enabling and starting vyomcloudbridge service..."
    systemctl enable vyomcloudbridge.service
    systemctl start vyomcloudbridge.service
    echo "Service has been installed and started."
else
    # Create template for manual installation
    username=$(whoami)
    temp_service_file="$HOME/vyomcloudbridge.service"
    cat > "$temp_service_file" << EOF
[Unit]
Description=Camera Capture Service
After=network.target rabbitmq-server.service
Wants=rabbitmq-server.service

[Service]
Type=simple
User=$username
WorkingDirectory=/home/$username/Documents/arducam
ExecStart=/bin/bash /home/$username/Documents/arducam/start_capture.sh
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal
LogRateLimitIntervalSec=0
LogRateLimitBurst=0
KillMode=process
KillSignal=SIGTERM
TimeoutStartSec=60
TimeoutStopSec=30

[Install]
WantedBy=multi-user.target
EOF
    
    echo "Service file template created at: $temp_service_file"
    echo "Run the following commands to install and enable the service:"
    echo "sudo cp $temp_service_file /etc/systemd/system/vyomcloudbridge.service"
    echo "sudo systemctl daemon-reload"
    echo "sudo systemctl enable vyomcloudbridge.service"
    echo "sudo systemctl start vyomcloudbridge.service"
fi

echo "Post-installation setup completed successfully."
exit 0  # Always exit with success code to avoid failing the package installation