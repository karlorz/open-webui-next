#!/bin/bash

# Define variables
SERVICE_FILE="jupyter_enterprise_gateway.service"
SERVICE_PATH="/etc/systemd/system/"
DESTINATION_PATH="/opt/open-webui/backend/"
APP_USERNAME="root"

# Stop the service if it's already running
echo "Stopping the service"
sudo systemctl stop "$SERVICE_FILE"

# Copy the service file to the systemd directory, force overwrite
echo "Copying service file to $SERVICE_PATH"
sudo cp -f "$SERVICE_FILE" "$SERVICE_PATH"

# Reload systemd to recognize the new service
echo "Reloading systemd daemon"
sudo systemctl daemon-reload

# Enable the service to start on boot
echo "Enabling the service"
sudo systemctl enable "$SERVICE_FILE"

# Start the service
echo "Starting the service"
sudo systemctl start "$SERVICE_FILE"

sleep 1

# Check the status of the service
echo "Checking the status of the service"
sudo systemctl status "$SERVICE_FILE"